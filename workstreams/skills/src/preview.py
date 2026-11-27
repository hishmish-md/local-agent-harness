"""Edit/preview interface contract for Friend Sol (workstreams/experience/).

Exposes a pure-data preview of a compiled DeclarativeSkill and a bounded
edit entrypoint that never leaks redacted secrets or bypasses re-approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from compiler import (
    CompileError,
    DeclarativeSkill,
    edit_target_id,
    edit_wait_seconds,
)
from recorder import REDACTED_TOKEN

PREVIEW_CONTRACT_VERSION: Literal["preview.v1"] = "preview.v1"
CONSENT_NOTICE = (
    "Synthetic declarative skill preview: redacted fields are never stored; "
    "editing resets approval; submission requires explicit confirmation."
)


class PreviewEditError(ValueError):
    """Raised when an edit request from the UI layer is invalid."""


@dataclass(frozen=True)
class PreviewStep:
    step_id: str
    kind: str
    target_id: str
    display_value: str | None
    wait_seconds: float
    redacted: bool
    requires_confirmation: bool
    editable_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "kind": self.kind,
            "target_id": self.target_id,
            "display_value": self.display_value,
            "wait_seconds": self.wait_seconds,
            "redacted": self.redacted,
            "requires_confirmation": self.requires_confirmation,
            "editable_fields": list(self.editable_fields),
        }


@dataclass(frozen=True)
class SkillPreview:
    contract_version: Literal["preview.v1"]
    skill_id: str
    app_id: str
    skill_version: int
    approved: bool
    dry_run_passed: bool
    consent_notice: str
    steps: tuple[PreviewStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "skill_id": self.skill_id,
            "app_id": self.app_id,
            "skill_version": self.skill_version,
            "approved": self.approved,
            "dry_run_passed": self.dry_run_passed,
            "consent_notice": self.consent_notice,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass(frozen=True)
class PreviewEditRequest:
    step_id: str
    wait_seconds: float | None = None
    target_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise PreviewEditError("step_id must be non-empty")
        if self.wait_seconds is None and self.target_id is None:
            raise PreviewEditError("edit must specify wait_seconds or target_id")


def build_preview(skill: DeclarativeSkill) -> SkillPreview:
    preview_steps: list[PreviewStep] = []
    for step in skill.steps:
        display_val = REDACTED_TOKEN if step.redacted else step.value
        editable = ("wait_seconds", "target_id")
        preview_steps.append(
            PreviewStep(
                step_id=step.step_id,
                kind=step.kind,
                target_id=step.target_id,
                display_value=display_val,
                wait_seconds=step.wait_seconds,
                redacted=step.redacted,
                requires_confirmation=step.requires_confirmation,
                editable_fields=editable,
            )
        )
    return SkillPreview(
        contract_version=PREVIEW_CONTRACT_VERSION,
        skill_id=skill.skill_id,
        app_id=skill.app_id,
        skill_version=skill.version,
        approved=skill.approved,
        dry_run_passed=skill.dry_run_passed,
        consent_notice=CONSENT_NOTICE,
        steps=tuple(preview_steps),
    )


def apply_preview_edit(
    skill: DeclarativeSkill,
    request: PreviewEditRequest,
) -> tuple[DeclarativeSkill, SkillPreview]:
    updated = skill
    try:
        if request.wait_seconds is not None:
            updated = edit_wait_seconds(updated, request.step_id, request.wait_seconds)
        if request.target_id is not None:
            updated = edit_target_id(updated, request.step_id, request.target_id)
    except CompileError as exc:
        raise PreviewEditError(str(exc)) from exc
    return updated, build_preview(updated)
