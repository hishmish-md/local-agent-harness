"""Recorder-to-editable declarative skill compiler for F-NEON-01.

Produces versioned, declarative skill definitions (never executable scripts)
with bounded wait editing (including 30s) and mandatory submit confirmation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal

from recorder import ALLOWED_EVENT_KINDS, REDACTED_TOKEN, EventKind, RecordedEvent

SCHEMA_VERSION: Literal["skill.v1"] = "skill.v1"
MIN_WAIT_SECONDS = 0.0
MIN_POSITIVE_WAIT_SECONDS = 1e-6
MAX_WAIT_SECONDS = 120.0


class CompileError(ValueError):
    """Raised when a draft or skill edit violates declarative invariants."""


def validate_wait_seconds(wait_seconds: float) -> float:
    if isinstance(wait_seconds, bool) or not isinstance(wait_seconds, (int, float)):
        raise CompileError("wait_seconds must be a real number")
    val = float(wait_seconds)
    if not math.isfinite(val) or val < MIN_WAIT_SECONDS or val > MAX_WAIT_SECONDS:
        raise CompileError(f"wait_seconds must be in [{MIN_WAIT_SECONDS}, {MAX_WAIT_SECONDS}]")
    if 0.0 < val < MIN_POSITIVE_WAIT_SECONDS:
        raise CompileError(f"positive wait_seconds must be >= {MIN_POSITIVE_WAIT_SECONDS}")
    return val


@dataclass(frozen=True)
class SkillStep:
    step_id: str
    kind: EventKind
    target_id: str
    value: str | None = None
    wait_seconds: float = 0.0
    redacted: bool = False
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_EVENT_KINDS:
            raise CompileError(f"unsupported step kind: {self.kind}")
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise CompileError("step_id must be non-empty")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise CompileError("target_id must be non-empty")
        validate_wait_seconds(self.wait_seconds)
        if self.redacted and self.value not in (None, REDACTED_TOKEN):
            raise CompileError("redacted step cannot carry unredacted value")


@dataclass(frozen=True)
class DeclarativeSkill:
    skill_id: str
    app_id: str
    steps: tuple[SkillStep, ...]
    version: int = 1
    schema_version: Literal["skill.v1"] = SCHEMA_VERSION
    approved: bool = False
    dry_run_passed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise CompileError("skill_id must be non-empty")
        if not isinstance(self.app_id, str) or not self.app_id.strip():
            raise CompileError("app_id must be non-empty")
        if not self.steps:
            raise CompileError("declarative skill must contain at least one step")
        if self.version < 1:
            raise CompileError("version must be >= 1")

    def get_step(self, step_id: str) -> SkillStep:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        raise CompileError(f"unknown step_id: {step_id}")


def compile_draft(
    skill_id: str,
    app_id: str,
    events: list[RecordedEvent],
) -> DeclarativeSkill:
    if not events:
        raise CompileError("cannot compile empty draft; consent-gated events required")
    compiled: list[SkillStep] = []
    for idx, ev in enumerate(events, start=1):
        if ev.app_id != app_id:
            raise CompileError("draft contains event outside skill app_id")
        step = SkillStep(
            step_id=f"step_{idx:02d}",
            kind=ev.kind,
            target_id=ev.target_id,
            value=REDACTED_TOKEN if ev.redacted and ev.value is not None else ev.value,
            wait_seconds=validate_wait_seconds(ev.wait_seconds),
            redacted=ev.redacted,
            requires_confirmation=(ev.kind == "submit"),
        )
        compiled.append(step)
    return DeclarativeSkill(
        skill_id=skill_id.strip(),
        app_id=app_id.strip(),
        steps=tuple(compiled),
        version=1,
        approved=False,
        dry_run_passed=False,
    )


def edit_wait_seconds(
    skill: DeclarativeSkill,
    step_id: str,
    wait_seconds: float,
) -> DeclarativeSkill:
    new_wait = validate_wait_seconds(wait_seconds)
    found = False
    updated: list[SkillStep] = []
    for step in skill.steps:
        if step.step_id == step_id:
            found = True
            updated.append(replace(step, wait_seconds=new_wait))
        else:
            updated.append(step)
    if not found:
        raise CompileError(f"unknown step_id: {step_id}")
    return replace(
        skill,
        steps=tuple(updated),
        version=skill.version + 1,
        approved=False,
        dry_run_passed=False,
    )


def edit_target_id(
    skill: DeclarativeSkill,
    step_id: str,
    target_id: str,
) -> DeclarativeSkill:
    if not isinstance(target_id, str) or not target_id.strip():
        raise CompileError("target_id must be non-empty")
    found = False
    updated: list[SkillStep] = []
    for step in skill.steps:
        if step.step_id == step_id:
            found = True
            updated.append(replace(step, target_id=target_id.strip()))
        else:
            updated.append(step)
    if not found:
        raise CompileError(f"unknown step_id: {step_id}")
    return replace(
        skill,
        steps=tuple(updated),
        version=skill.version + 1,
        approved=False,
        dry_run_passed=False,
    )


def mark_dry_run_passed(skill: DeclarativeSkill) -> DeclarativeSkill:
    return replace(skill, dry_run_passed=True)


def approve_skill(skill: DeclarativeSkill) -> DeclarativeSkill:
    if not skill.dry_run_passed:
        raise CompileError("dry run must pass before approving skill")
    return replace(skill, approved=True)
