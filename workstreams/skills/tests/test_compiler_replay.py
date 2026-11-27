"""Compiler, Sol preview contract, and replay acceptance tests for F-NEON-01."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

_SKILLS_DIR = Path(__file__).resolve().parent.parent
for _sub in ("src", "fixtures"):
    _path = str(_SKILLS_DIR / _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from clock import FakeClock
from compiler import (
    CompileError,
    approve_skill,
    compile_draft,
    edit_wait_seconds,
)
from consent import ConsentMachine
from preview import (
    PREVIEW_CONTRACT_VERSION,
    PreviewEditError,
    PreviewEditRequest,
    apply_preview_edit,
    build_preview,
)
from recorder import REDACTED_TOKEN, RawEvent, SkillRecorder
from replay import ReplayEngine
from synthetic_form import (
    EDITED_WAIT_SECONDS,
    FAKE_SECRET_VALUE,
    SYNTHETIC_APP_ID,
    SYNTHETIC_PURPOSE,
    SYNTHETIC_SKILL_ID,
    build_revoke_during_wait_case,
    build_synthetic_form_events,
    run_synthetic_pipeline,
)


def _record_synthetic_skill():
    clock = FakeClock()
    consent = ConsentMachine(clock)
    consent.grant(SYNTHETIC_APP_ID, SYNTHETIC_PURPOSE, max_duration_s=600.0)
    recorder = SkillRecorder(consent, clock)
    for ev in build_synthetic_form_events():
        recorder.record(ev)
    skill = compile_draft(SYNTHETIC_SKILL_ID, SYNTHETIC_APP_ID, recorder.snapshot_draft())
    return clock, consent, skill


def test_compile_rejects_empty_and_requires_dry_run_before_approval() -> None:
    with pytest.raises(CompileError):
        compile_draft(SYNTHETIC_SKILL_ID, SYNTHETIC_APP_ID, [])

    _, _, skill = _record_synthetic_skill()
    assert skill.schema_version == "skill.v1"
    assert skill.approved is False
    assert skill.get_step("step_02").value == REDACTED_TOKEN
    assert skill.get_step("step_04").requires_confirmation is True
    with pytest.raises(CompileError):
        approve_skill(skill)


@pytest.mark.parametrize("wait_s", [0.0, 1e-6, 30.0, 120.0])
def test_edit_wait_seconds_valid_boundaries(wait_s: float) -> None:
    _, _, skill = _record_synthetic_skill()
    edited = edit_wait_seconds(skill, "step_03", wait_s)
    assert edited.get_step("step_03").wait_seconds == wait_s
    assert edited.version == skill.version + 1
    assert edited.approved is False
    assert edited.dry_run_passed is False


@pytest.mark.parametrize("bad_wait", [-0.01, 1e-7, 4e-7, 120.01, math.nan, math.inf, True, "30"])
def test_edit_wait_seconds_rejects_out_of_bounds(bad_wait: object) -> None:
    _, _, skill = _record_synthetic_skill()
    with pytest.raises(CompileError):
        edit_wait_seconds(skill, "step_03", bad_wait)  # type: ignore[arg-type]


def test_sol_preview_contract_redacts_secret_and_supports_30s_wait_edit() -> None:
    _, _, skill = _record_synthetic_skill()
    initial = build_preview(skill).to_dict()
    assert initial["contract_version"] == PREVIEW_CONTRACT_VERSION
    assert FAKE_SECRET_VALUE not in json.dumps(initial)
    assert initial["steps"][1]["display_value"] == REDACTED_TOKEN
    assert initial["steps"][2]["editable_fields"] == ["wait_seconds", "target_id"]

    updated_skill, updated_preview = apply_preview_edit(
        skill,
        PreviewEditRequest(step_id="step_03", wait_seconds=EDITED_WAIT_SECONDS),
    )
    payload = updated_preview.to_dict()
    assert updated_skill.get_step("step_03").wait_seconds == 30.0
    assert payload["skill_version"] == 2
    assert payload["approved"] is False
    assert FAKE_SECRET_VALUE not in json.dumps(payload)

    with pytest.raises(PreviewEditError):
        PreviewEditRequest(step_id="step_03")
    with pytest.raises(PreviewEditError):
        apply_preview_edit(skill, PreviewEditRequest(step_id="step_03", wait_seconds=999.0))


def test_replay_blocks_unapproved_and_requires_submit_confirmation() -> None:
    clock, consent, skill = _record_synthetic_skill()
    engine = ReplayEngine(consent, clock)

    unapproved = engine.replay(skill, confirm_submit=lambda _s: True)
    assert unapproved.status == "blocked_unapproved"
    assert unapproved.dispatched_steps == ()

    _, _, denied = run_synthetic_pipeline(edit_wait_to_s=30.0, confirm_submission=False)
    assert denied.status == "blocked_confirmation_required"
    assert denied.completed is False
    assert denied.submitted is False
    assert denied.halted_at_step_id == "step_04"
    assert denied.elapsed_s == 30.0


def test_synthetic_pipeline_happy_path_30s_wait_and_confirmed_submit() -> None:
    skill, preview_dict, result = run_synthetic_pipeline(
        edit_wait_to_s=30.0,
        confirm_submission=True,
    )
    assert result.status == "completed"
    assert result.completed is True
    assert result.submitted is True
    assert result.elapsed_s == 30.0
    assert len(result.dispatched_steps) == 4
    assert FAKE_SECRET_VALUE not in json.dumps(preview_dict)
    assert FAKE_SECRET_VALUE not in str(skill)
    assert FAKE_SECRET_VALUE not in str(result)


def test_gpt_oss_revoke_during_wait_case_halts_immediately() -> None:
    case = build_revoke_during_wait_case()
    _, _, result = run_synthetic_pipeline(
        edit_wait_to_s=case["edited_wait_seconds"],
        confirm_submission=True,
        revoke_at_elapsed_s=case["revoke_at_elapsed_s"],
    )
    assert result.status == case["expected_status"]
    assert result.completed is False
    assert result.submitted is case["expected_submitted"]
    assert result.halted_at_step_id == case["expected_halted_step_id"]
    assert len(result.dispatched_steps) == case["expected_dispatched_count"]
    assert result.elapsed_s == case["revoke_at_elapsed_s"]


def test_crash_during_wait_halts_and_blocks_subsequent_replay() -> None:
    clock, consent, skill = _record_synthetic_skill()
    skill = edit_wait_seconds(skill, "step_03", 30.0)
    engine = ReplayEngine(consent, clock, poll_step_s=1.0)
    skill, dry_res = engine.dry_run(skill)
    assert dry_res.completed is True
    skill = approve_skill(skill)

    def _crash_at_5s(elapsed_s: float, _step: object) -> None:
        if elapsed_s >= 5.0:
            consent.simulate_crash("simulated_worker_crash")

    halted = engine.replay(skill, confirm_submit=lambda _s: True, on_wait_tick=_crash_at_5s)
    assert halted.status == "halted_crashed"
    assert halted.submitted is False
    assert halted.halted_at_step_id == "step_03"
    assert halted.elapsed_s == 5.0

    retry = engine.replay(skill, confirm_submit=lambda _s: True)
    assert retry.status == "halted_crashed"
    assert retry.dispatched_steps == ()


def test_tiny_wait_precision_regression() -> None:
    with pytest.raises(ValueError):
        RawEvent(kind="wait", target_id="btn", app_id=SYNTHETIC_APP_ID, wait_seconds=1e-7)
    clock, consent, skill = _record_synthetic_skill()
    with pytest.raises(PreviewEditError):
        apply_preview_edit(skill, PreviewEditRequest(step_id="step_03", wait_seconds=4e-7))
    with pytest.raises(ValueError):
        ReplayEngine(consent, clock, poll_step_s=1e-7)

    _, _, min_res = run_synthetic_pipeline(edit_wait_to_s=1e-6, confirm_submission=True)
    assert min_res.completed is True
    assert min_res.elapsed_s == 1e-6

    _, _, rem_res = run_synthetic_pipeline(edit_wait_to_s=1.0000004, confirm_submission=True)
    assert rem_res.completed is True
    assert rem_res.submitted is True
    assert rem_res.elapsed_s >= 1.0
