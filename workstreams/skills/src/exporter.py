"""Offline exporter for an already-edited synthetic DeclarativeSkill (F-NEON-01).

Produces deterministic, redacted JSON artifacts from an edited declarative
skill. Replaces any sensitive or redacted field values with REDACTED_TOKEN.
Contains no recording, replay, or network functionality.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from compiler import CompileError, DeclarativeSkill, SkillStep, validate_wait_seconds
from recorder import REDACTED_TOKEN, SECRET_KEYWORDS

EXPORT_SCHEMA_VERSION: Literal["skill.export.v1"] = "skill.export.v1"
EXPORT_NOTICE = (
    "Offline synthetic skill export: sensitive values are replaced with "
    f"{REDACTED_TOKEN}; no recording, replay, or network access."
)
_SENSITIVE_VALUE_MARKERS: tuple[str, ...] = (
    "bearer ",
    "sk-",
    "ghp_",
    "-----begin ",
)


class ExportError(ValueError):
    """Raised when an edited skill or export target fails validation."""


@dataclass(frozen=True)
class ExportedStep:
    step_id: str
    kind: str
    target_id: str
    value: str | None
    wait_seconds: float
    redacted: bool
    requires_confirmation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "kind": self.kind,
            "target_id": self.target_id,
            "value": self.value,
            "wait_seconds": self.wait_seconds,
            "redacted": self.redacted,
            "requires_confirmation": self.requires_confirmation,
        }


@dataclass(frozen=True)
class ExportedSkill:
    export_schema_version: Literal["skill.export.v1"]
    source_schema_version: str
    skill_id: str
    app_id: str
    skill_version: int
    approved: bool
    dry_run_passed: bool
    offline_only: bool
    redacted_step_count: int
    notice: str
    steps: tuple[ExportedStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_schema_version": self.export_schema_version,
            "source_schema_version": self.source_schema_version,
            "skill_id": self.skill_id,
            "app_id": self.app_id,
            "skill_version": self.skill_version,
            "approved": self.approved,
            "dry_run_passed": self.dry_run_passed,
            "offline_only": self.offline_only,
            "redacted_step_count": self.redacted_step_count,
            "notice": self.notice,
            "steps": [step.to_dict() for step in self.steps],
        }


def _is_sensitive_step(step: SkillStep) -> bool:
    if step.redacted:
        return True
    target_lower = step.target_id.lower()
    if any(keyword in target_lower for keyword in SECRET_KEYWORDS):
        return True
    if isinstance(step.value, str):
        value_lower = step.value.lower()
        if any(marker in value_lower for marker in _SENSITIVE_VALUE_MARKERS):
            return True
    return False


def export_edited_skill(
    skill: DeclarativeSkill,
    *,
    require_edited: bool = True,
) -> ExportedSkill:
    """Convert an already-edited DeclarativeSkill into a redacted export model."""
    if not isinstance(skill, DeclarativeSkill):
        raise ExportError("skill must be a DeclarativeSkill instance")
    if require_edited and skill.version < 2:
        raise ExportError("expected an already-edited skill (version >= 2)")

    exported_steps: list[ExportedStep] = []
    redacted_count = 0
    for step in skill.steps:
        try:
            wait_s = validate_wait_seconds(step.wait_seconds)
        except CompileError as exc:
            raise ExportError(str(exc)) from exc

        sensitive = _is_sensitive_step(step)
        if sensitive:
            redacted_count += 1
            safe_value: str | None = REDACTED_TOKEN
        else:
            safe_value = step.value

        exported_steps.append(
            ExportedStep(
                step_id=step.step_id,
                kind=step.kind,
                target_id=step.target_id,
                value=safe_value,
                wait_seconds=wait_s,
                redacted=sensitive,
                requires_confirmation=step.requires_confirmation,
            )
        )

    return ExportedSkill(
        export_schema_version=EXPORT_SCHEMA_VERSION,
        source_schema_version=skill.schema_version,
        skill_id=skill.skill_id,
        app_id=skill.app_id,
        skill_version=skill.version,
        approved=skill.approved,
        dry_run_passed=skill.dry_run_passed,
        offline_only=True,
        redacted_step_count=redacted_count,
        notice=EXPORT_NOTICE,
        steps=tuple(exported_steps),
    )


def serialize_exported_skill(exported: ExportedSkill) -> str:
    """Serialize an ExportedSkill to canonical deterministic JSON."""
    if not isinstance(exported, ExportedSkill):
        raise ExportError("exported must be an ExportedSkill instance")
    return json.dumps(exported.to_dict(), indent=2, sort_keys=True) + "\n"


def write_exported_skill(
    skill: DeclarativeSkill,
    output_path: str | Path,
    *,
    require_edited: bool = True,
) -> Path:
    """Write a redacted edited skill export to a local path offline."""
    raw_target = str(output_path).strip()
    if not raw_target or "://" in raw_target:
        raise ExportError("output_path must be a non-empty local filesystem path")
    target = Path(raw_target)
    payload = serialize_exported_skill(
        export_edited_skill(skill, require_edited=require_edited)
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f".{target.name}.tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, target)
    return target.resolve()


def build_synthetic_edited_skill() -> DeclarativeSkill:
    """Build an already-edited synthetic skill directly (no recorder/replay)."""
    return DeclarativeSkill(
        skill_id="skill.synthetic.expense_submit",
        app_id="app.synthetic.expense_form",
        version=2,
        approved=False,
        dry_run_passed=False,
        steps=(
            SkillStep("step_01", "fill", "field_vendor_name", value="Synthetic Supplies Co"),
            SkillStep("step_02", "fill", "field_api_secret", value=REDACTED_TOKEN, redacted=True),
            SkillStep("step_03", "wait", "btn_submit_expense", wait_seconds=30.0),
            SkillStep(
                "step_04",
                "submit",
                "btn_submit_expense",
                value="submit_synthetic_form",
                requires_confirmation=True,
            ),
        ),
    )
