"""Pure synthetic form fixture for F-NEON-01 (workstreams/skills/).

Contains only invented data, one clearly fake secret field, a configurable
wait step (editable to 30s), and a submit step requiring confirmation.
No real employee recordings, no secrets, and no network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from clock import FakeClock
from compiler import DeclarativeSkill, approve_skill, compile_draft
from consent import ConsentMachine
from preview import PreviewEditRequest, apply_preview_edit, build_preview
from recorder import RawEvent, SkillRecorder
from replay import ReplayEngine, ReplayResult

SYNTHETIC_APP_ID = "app.synthetic.expense_form"
SYNTHETIC_SKILL_ID = "skill.synthetic.expense_submit"
SYNTHETIC_PURPOSE = "synthetic_consent_to_replay_demo"
FAKE_SECRET_VALUE = "FAKE_SECRET_DO_NOT_USE_9911"
DEFAULT_WAIT_SECONDS = 5.0
EDITED_WAIT_SECONDS = 30.0
REVOKE_CASE_SEED = 4201


def build_synthetic_form_events(wait_seconds: float = DEFAULT_WAIT_SECONDS) -> list[RawEvent]:
    """Return invented form events: vendor fill, fake secret, wait, submit."""
    return [
        RawEvent(
            kind="fill",
            target_id="field_vendor_name",
            app_id=SYNTHETIC_APP_ID,
            value="Synthetic Supplies Co",
            field_name="vendor_name",
        ),
        RawEvent(
            kind="fill",
            target_id="field_api_secret",
            app_id=SYNTHETIC_APP_ID,
            value=FAKE_SECRET_VALUE,
            is_secret=True,
            field_name="api_secret",
        ),
        RawEvent(
            kind="wait",
            target_id="btn_submit_expense",
            app_id=SYNTHETIC_APP_ID,
            wait_seconds=wait_seconds,
            field_name="submit_ready_wait",
        ),
        RawEvent(
            kind="submit",
            target_id="btn_submit_expense",
            app_id=SYNTHETIC_APP_ID,
            value="submit_synthetic_form",
            field_name="submit_button",
        ),
    ]


def build_revoke_during_wait_case() -> dict[str, Any]:
    """Package the deterministic revoke-during-wait case for independent review."""
    return {
        "case_id": "F-NEON-01-REVOKE-DURING-WAIT",
        "seed": REVOKE_CASE_SEED,
        "app_id": SYNTHETIC_APP_ID,
        "skill_id": SYNTHETIC_SKILL_ID,
        "edited_wait_seconds": EDITED_WAIT_SECONDS,
        "revoke_at_elapsed_s": 10.0,
        "expected_status": "halted_revoked",
        "expected_halted_step_id": "step_03",
        "expected_submitted": False,
        "expected_dispatched_count": 2,
    }


def run_synthetic_pipeline(
    *,
    edit_wait_to_s: float = EDITED_WAIT_SECONDS,
    confirm_submission: bool = True,
    revoke_at_elapsed_s: float | None = None,
) -> tuple[DeclarativeSkill, dict[str, Any], ReplayResult]:
    """Execute the full offline consent -> record -> edit -> replay scenario."""
    clock = FakeClock()
    consent = ConsentMachine(clock)
    recorder = SkillRecorder(consent, clock)

    # Pre-consent attempt must record 0 events.
    events = build_synthetic_form_events()
    recorder.record(events[0])

    consent.grant(SYNTHETIC_APP_ID, SYNTHETIC_PURPOSE, max_duration_s=600.0)
    for event in events:
        recorder.record(event)
        clock.advance(1.0)

    skill = compile_draft(SYNTHETIC_SKILL_ID, SYNTHETIC_APP_ID, recorder.snapshot_draft())
    skill, preview = apply_preview_edit(
        skill,
        PreviewEditRequest(step_id="step_03", wait_seconds=edit_wait_to_s),
    )
    engine = ReplayEngine(consent, clock, poll_step_s=1.0)
    skill, dry_result = engine.dry_run(skill)
    if not dry_result.completed:
        return skill, build_preview(skill).to_dict(), dry_result
    skill = approve_skill(skill)

    def _on_wait_tick(elapsed_s: float, _step: Any) -> None:
        if revoke_at_elapsed_s is not None and elapsed_s >= revoke_at_elapsed_s:
            consent.revoke("employee_revoked_during_wait")

    result = engine.replay(
        skill,
        confirm_submit=(lambda _step: confirm_submission),
        on_wait_tick=_on_wait_tick,
    )
    return skill, preview.to_dict(), result
