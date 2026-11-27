"""Offline edited-skill v1 exporter and CLI (F-NEON-01 / source 7221971766).

Exports an already-edited, in-memory synthetic skill into a deterministic,
redacted UTF-8 JSON document conforming to `edited_skill_v1.md`.
No recording, replay, importer, shell, plugin loading, network, or telemetry.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

_SRC_DIR = str(Path(__file__).resolve().parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from compiler import DeclarativeSkill, SkillStep

EXPORT_FORMAT = "edited-skill"
EXPORT_VERSION = 1
MAX_BYTES_UTF8 = 65536
MAX_STEPS = 64
MAX_SLOTS = 64
MAX_DEPTH = 4
MAX_TOKEN_LEN = 32
MIN_WAIT_MS = 0
MAX_WAIT_MS = 60000

_GENERIC_ERROR = "invalid edited-skill v1 format"
_ROOT_KEYS = frozenset({"format", "version", "steps"})
_WAIT_KEYS = frozenset({"op", "ms"})
_SET_FIELD_KEYS = frozenset({"op", "target", "value"})
_PLACEHOLDER_KEYS = frozenset({"type", "slot"})
_TARGET_TYPES = frozenset({"field"})
_VALUE_TYPES = frozenset({"text", "number", "boolean"})
_ALLOWED_TOKENS = frozenset({
    "format", "version", "steps", EXPORT_FORMAT, "op", "wait", "ms",
    "set_field", "target", "value", "type", "slot", "field",
    "text", "number", "boolean",
})


class InvalidEditedSkillFormatError(ValueError):
    """Generic error raised on any v1 format violation without echoing input."""
    def __init__(self) -> None:
        super().__init__(_GENERIC_ERROR)


def _is_strict_int(val: Any) -> bool:
    return type(val) is int


def _seconds_to_exact_ms(seconds: Any) -> int:
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not (0.0 <= seconds <= 60.0):
        raise InvalidEditedSkillFormatError()
    scaled = float(seconds) * 1000.0
    rounded = int(round(scaled))
    if abs(scaled - rounded) > 1e-9 or not (MIN_WAIT_MS <= rounded <= MAX_WAIT_MS):
        raise InvalidEditedSkillFormatError()
    return rounded


def _from_declarative_skill(skill: DeclarativeSkill, *, require_edited: bool) -> dict[str, Any]:
    if require_edited and (not _is_strict_int(skill.version) or skill.version < 2):
        raise InvalidEditedSkillFormatError()
    if len(skill.steps) > MAX_STEPS:
        raise InvalidEditedSkillFormatError()
    steps: list[dict[str, Any]] = []
    next_slot = 1
    for step in skill.steps:
        if not isinstance(step, SkillStep):
            raise InvalidEditedSkillFormatError()
        if step.kind == "fill":
            target_slot, value_slot = next_slot, next_slot + 1
            next_slot += 2
            if value_slot > MAX_SLOTS:
                raise InvalidEditedSkillFormatError()
            steps.append({
                "op": "set_field",
                "target": {"type": "field", "slot": target_slot},
                "value": {"type": "text", "slot": value_slot},
            })
        elif step.kind == "wait":
            steps.append({"op": "wait", "ms": _seconds_to_exact_ms(step.wait_seconds)})
        else:
            raise InvalidEditedSkillFormatError()
    return {"format": EXPORT_FORMAT, "version": EXPORT_VERSION, "steps": steps}


def _validate_placeholder(raw: Any, allowed_types: frozenset[str], slot_types: dict[int, str]) -> dict[str, Any]:
    if type(raw) is not dict or set(raw.keys()) != _PLACEHOLDER_KEYS:
        raise InvalidEditedSkillFormatError()
    ptype, slot = raw["type"], raw["slot"]
    if type(ptype) is not str or len(ptype) > MAX_TOKEN_LEN or ptype not in allowed_types:
        raise InvalidEditedSkillFormatError()
    if not _is_strict_int(slot) or not (1 <= slot <= MAX_SLOTS):
        raise InvalidEditedSkillFormatError()
    prev = slot_types.get(slot)
    if prev is not None and prev != ptype:
        raise InvalidEditedSkillFormatError()
    slot_types[slot] = ptype
    if len(slot_types) > MAX_SLOTS:
        raise InvalidEditedSkillFormatError()
    return {"slot": slot, "type": ptype}


def _check_depth_and_tokens(node: Any, depth: int = 1) -> None:
    if depth > MAX_DEPTH:
        raise InvalidEditedSkillFormatError()
    if type(node) is dict:
        for key, val in node.items():
            if type(key) is not str or len(key) > MAX_TOKEN_LEN or key not in _ALLOWED_TOKENS:
                raise InvalidEditedSkillFormatError()
            if isinstance(val, (dict, list)):
                _check_depth_and_tokens(val, depth + 1)
            elif type(val) is str:
                if len(val) > MAX_TOKEN_LEN or val not in _ALLOWED_TOKENS:
                    raise InvalidEditedSkillFormatError()
            elif not _is_strict_int(val):
                raise InvalidEditedSkillFormatError()
    elif type(node) is list:
        for item in node:
            if not isinstance(item, (dict, list)):
                raise InvalidEditedSkillFormatError()
            _check_depth_and_tokens(item, depth + 1)
    else:
        raise InvalidEditedSkillFormatError()


def _validate_v1_document(doc: Any) -> dict[str, Any]:
    if (type(doc) is not dict or set(doc.keys()) != _ROOT_KEYS
            or type(doc["format"]) is not str or doc["format"] != EXPORT_FORMAT
            or not _is_strict_int(doc["version"]) or doc["version"] != EXPORT_VERSION):
        raise InvalidEditedSkillFormatError()
    raw_steps = doc["steps"]
    if type(raw_steps) is not list or len(raw_steps) > MAX_STEPS:
        raise InvalidEditedSkillFormatError()

    slot_types: dict[int, str] = {}
    clean_steps: list[dict[str, Any]] = []
    for raw_step in raw_steps:
        if type(raw_step) is not dict or "op" not in raw_step:
            raise InvalidEditedSkillFormatError()
        op = raw_step["op"]
        if op == "wait":
            if set(raw_step.keys()) != _WAIT_KEYS:
                raise InvalidEditedSkillFormatError()
            ms = raw_step["ms"]
            if not _is_strict_int(ms) or ms < MIN_WAIT_MS or ms > MAX_WAIT_MS:
                raise InvalidEditedSkillFormatError()
            clean_steps.append({"ms": ms, "op": "wait"})
        elif op == "set_field":
            if set(raw_step.keys()) != _SET_FIELD_KEYS:
                raise InvalidEditedSkillFormatError()
            target = _validate_placeholder(raw_step["target"], _TARGET_TYPES, slot_types)
            value = _validate_placeholder(raw_step["value"], _VALUE_TYPES, slot_types)
            clean_steps.append({"op": "set_field", "target": target, "value": value})
        else:
            raise InvalidEditedSkillFormatError()

    clean_doc = {"format": EXPORT_FORMAT, "steps": clean_steps, "version": EXPORT_VERSION}
    _check_depth_and_tokens(clean_doc, depth=1)
    return clean_doc


def export_edited_skill_v1(source: DeclarativeSkill | dict[str, Any], *, require_edited: bool = True) -> dict[str, Any]:
    """Validate and return a canonical edited-skill v1 document dict."""
    if isinstance(source, DeclarativeSkill):
        candidate = _from_declarative_skill(source, require_edited=require_edited)
    elif type(source) is dict:
        candidate = source
    else:
        raise InvalidEditedSkillFormatError()
    return _validate_v1_document(candidate)


def serialize_edited_skill_v1(source: DeclarativeSkill | dict[str, Any], *, require_edited: bool = True) -> bytes:
    """Validate and serialize an edited skill to canonical UTF-8 JSON bytes."""
    doc = export_edited_skill_v1(source, require_edited=require_edited)
    encoded = (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if len(encoded) > MAX_BYTES_UTF8:
        raise InvalidEditedSkillFormatError()
    return encoded


def build_demo_edited_skill() -> DeclarativeSkill:
    """Build an offline synthetic edited skill (1 field edit + 500 ms wait)."""
    return DeclarativeSkill(
        skill_id="skill.synthetic.edited_demo", app_id="app.synthetic.form",
        version=2, approved=False, dry_run_passed=False,
        steps=(
            SkillStep("step_01", "fill", "synthetic_field_name", value="synthetic_value"),
            SkillStep("step_02", "wait", "synthetic_wait_target", wait_seconds=0.5),
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args != ["--demo"]:
        sys.stderr.write(_GENERIC_ERROR + "\n")
        return 2
    try:
        payload = serialize_edited_skill_v1(build_demo_edited_skill())
    except InvalidEditedSkillFormatError:
        sys.stderr.write(_GENERIC_ERROR + "\n")
        return 1
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
