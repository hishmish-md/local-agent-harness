"""Pure in-memory skill draft change summary (change_summary_v1, F-NEON-01)."""
from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import Any, Literal

SUMMARY_VERSION = "change_summary_v1"
WAIT_UNIT: Literal["ms"] = "ms"
MAX_STEPS, MAX_SLOTS, MAX_WAIT_MS = 64, 64, 60_000
MAX_TOTAL_WAIT_MS, MAX_REVISION, MAX_SCOPE_LEN = 300_000, 1_000_000, 32
_SCOPE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_-")
_SNAPSHOT_KEYS = frozenset({"version", "draft_scope", "revision", "steps"})
_WAIT_KEYS = frozenset({"op", "ms"})
_SET_FIELD_KEYS = frozenset({"op", "target", "value"})
_PLACEHOLDER_KEYS = frozenset({"type", "slot"})
_TARGET_TYPES = frozenset({"field"})
_VALUE_TYPES = frozenset({"text", "number", "boolean"})

ReasonCode = Literal[
    "ok", "invalid_version", "invalid_shape", "invalid_scope", "invalid_revision",
    "cross_draft", "stale_revision", "step_limit_exceeded", "invalid_step",
    "missing_wait_duration", "invalid_wait_duration", "wait_total_overflow",
    "invalid_placeholder",
]

@dataclass(frozen=True, slots=True)
class ChangeSummaryResult:
    status: Literal["ok", "rejected"]
    reason: ReasonCode
    unit: Literal["ms"] | None
    before_steps: int | None
    after_steps: int | None
    delta_steps: int | None
    before_wait_ms: int | None
    after_wait_ms: int | None
    delta_wait_ms: int | None


def _reject(reason: ReasonCode) -> ChangeSummaryResult:
    return ChangeSummaryResult("rejected", reason, None, None, None, None, None, None, None)


def _valid_int(value: Any, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _valid_scope(value: Any) -> bool:
    return type(value) is str and 1 <= len(value) <= MAX_SCOPE_LEN and all(c in _SCOPE_CHARS for c in value)


def _validate_placeholder(raw: Any, allowed: frozenset[str], slots: dict[int, str]) -> bool:
    if type(raw) is not dict or raw.keys() != _PLACEHOLDER_KEYS:
        return False
    kind, slot = raw["type"], raw["slot"]
    if type(kind) is not str or kind not in allowed or not _valid_int(slot, 1, MAX_SLOTS):
        return False
    prev = slots.get(slot)
    if prev is not None and prev != kind:
        return False
    slots[slot] = kind
    return len(slots) <= MAX_SLOTS


def _validate_snapshot(raw: Any) -> tuple[str, int, int, int] | ReasonCode:
    if type(raw) is not dict:
        return "invalid_shape"
    if "version" in raw and (type(raw["version"]) is not str or raw["version"] != SUMMARY_VERSION):
        return "invalid_version"
    if raw.keys() != _SNAPSHOT_KEYS:
        return "invalid_shape"
    scope, rev, steps = raw["draft_scope"], raw["revision"], raw["steps"]
    if not _valid_scope(scope):
        return "invalid_scope"
    if not _valid_int(rev, 1, MAX_REVISION):
        return "invalid_revision"
    if type(steps) not in (list, tuple):
        return "invalid_shape"
    if len(steps) > MAX_STEPS:
        return "step_limit_exceeded"
    total_wait_ms = 0
    slots: dict[int, str] = {}
    for step in steps:
        if type(step) is not dict or type(step.get("op")) is not str:
            return "invalid_step"
        op = step["op"]
        if op == "wait":
            if "ms" not in step:
                return "missing_wait_duration"
            if step.keys() != _WAIT_KEYS:
                return "invalid_step"
            ms = step["ms"]
            if not _valid_int(ms, 0, MAX_WAIT_MS):
                return "invalid_wait_duration"
            total_wait_ms += ms
            if total_wait_ms > MAX_TOTAL_WAIT_MS:
                return "wait_total_overflow"
        elif op == "set_field":
            if step.keys() != _SET_FIELD_KEYS:
                return "invalid_step"
            if not _validate_placeholder(step["target"], _TARGET_TYPES, slots):
                return "invalid_placeholder"
            if not _validate_placeholder(step["value"], _VALUE_TYPES, slots):
                return "invalid_placeholder"
        else:
            return "invalid_step"
    return (scope, rev, len(steps), total_wait_ms)


def summarize_draft_change(
    before: Any,
    after: Any,
    *,
    expected_scope: Any,
    expected_before_rev: Any,
    expected_after_rev: Any,
) -> ChangeSummaryResult:
    if not _valid_scope(expected_scope):
        return _reject("invalid_scope")
    if not (_valid_int(expected_before_rev, 1, MAX_REVISION) and _valid_int(expected_after_rev, 1, MAX_REVISION)):
        return _reject("invalid_revision")
    if expected_before_rev >= expected_after_rev:
        return _reject("invalid_revision")
    b_res = _validate_snapshot(before)
    if isinstance(b_res, str):
        return _reject(b_res)
    a_res = _validate_snapshot(after)
    if isinstance(a_res, str):
        return _reject(a_res)
    b_scope, b_rev, b_steps, b_wait = b_res
    a_scope, a_rev, a_steps, a_wait = a_res
    if b_scope != expected_scope or a_scope != expected_scope:
        return _reject("cross_draft")
    if b_rev != expected_before_rev or a_rev != expected_after_rev:
        return _reject("stale_revision")
    return ChangeSummaryResult(
        "ok", "ok", WAIT_UNIT, b_steps, a_steps, a_steps - b_steps, b_wait, a_wait, a_wait - b_wait
    )


def _snap(scope: str, rev: int, steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {"version": SUMMARY_VERSION, "draft_scope": scope, "revision": rev, "steps": steps}


def _fmt(label: str, r: ChangeSummaryResult) -> str:
    if r.status != "ok":
        return f"{label} status={r.status} reason={r.reason}\n"
    ds = f"{r.delta_steps:+d}" if r.delta_steps else "0"
    dw = f"{r.delta_wait_ms:+d}" if r.delta_wait_ms else "0"
    return (
        f"{label} status=ok before_steps={r.before_steps} after_steps={r.after_steps} "
        f"delta_steps={ds} before_wait_ms={r.before_wait_ms} after_wait_ms={r.after_wait_ms} "
        f"delta_wait_ms={dw} unit={r.unit}\n"
    )


def _run_demo(mode: str) -> int:
    w = lambda ms: {"op": "wait", "ms": ms}
    sf = {"op": "set_field", "target": {"type": "field", "slot": 1}, "value": {"type": "text", "slot": 2}}
    if mode == "net-counts":
        s2, s3 = [w(1000), w(2000)], [w(2000), w(3000), sf]
        cases = [
            ("forward", summarize_draft_change(_snap("draft_a", 1, s2), _snap("draft_a", 2, s3), expected_scope="draft_a", expected_before_rev=1, expected_after_rev=2)),
            ("reverse", summarize_draft_change(_snap("draft_a", 2, s3), _snap("draft_a", 3, s2), expected_scope="draft_a", expected_before_rev=2, expected_after_rev=3)),
            ("empty", summarize_draft_change(_snap("draft_a", 3, []), _snap("draft_a", 4, []), expected_scope="draft_a", expected_before_rev=3, expected_after_rev=4)),
        ]
    elif mode == "reorder":
        cases = [
            ("reordered", summarize_draft_change(_snap("draft_b", 1, [w(1500), sf]), _snap("draft_b", 2, [sf, w(1500)]), expected_scope="draft_b", expected_before_rev=1, expected_after_rev=2)),
        ]
    elif mode == "invalid":
        cases = [
            ("stale_pair", summarize_draft_change(_snap("draft_c", 1, [w(1000)]), _snap("draft_c", 2, [w(2000)]), expected_scope="draft_c", expected_before_rev=2, expected_after_rev=3)),
            ("missing_wait", summarize_draft_change(_snap("draft_c", 1, [{"op": "wait"}]), _snap("draft_c", 2, [w(1000)]), expected_scope="draft_c", expected_before_rev=1, expected_after_rev=2)),
            ("wait_overflow", summarize_draft_change(_snap("draft_c", 1, [w(60_000)] * 6), _snap("draft_c", 2, [w(1000)]), expected_scope="draft_c", expected_before_rev=1, expected_after_rev=2)),
        ]
    else:
        sys.stderr.write("usage_error\n")
        return 2
    for label, res in cases:
        sys.stdout.write(_fmt(label, res))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 2 and args[0] == "--demo":
        return _run_demo(args[1])
    sys.stderr.write("usage_error\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
