"""In-memory undo/redo editor history (history_v1) for synthetic skill drafts (F-NEON-01)."""
from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import Any, Literal

HISTORY_VERSION = "history_v1"
MAX_STEPS, MAX_SLOTS, MAX_WAIT_MS = 64, 64, 60_000
MAX_HISTORY_SNAPSHOTS = 32
MAX_RETAINED_STEPS = (MAX_HISTORY_SNAPSHOTS + 1) * MAX_STEPS
_DRAFT_KEYS = frozenset({"version", "steps"})
_WAIT_KEYS = frozenset({"op", "ms"})
_SET_FIELD_KEYS = frozenset({"op", "target", "value"})
_PLACEHOLDER_KEYS = frozenset({"type", "slot"})
_TARGET_TYPES = frozenset({"field"})
_VALUE_TYPES = frozenset({"text", "number", "boolean"})

StatusCode = Literal[
    "opened", "applied", "noop", "rejected", "undone",
    "redone", "empty_undo", "empty_redo", "open", "closed",
]


class HistoryValidationError(ValueError):
    def __init__(self) -> None:
        super().__init__("invalid history_v1 draft")

@dataclass(frozen=True, slots=True)
class _Placeholder:
    kind: str
    slot: int

@dataclass(frozen=True, slots=True)
class _WaitStep:
    ms: int

@dataclass(frozen=True, slots=True)
class _SetFieldStep:
    target: _Placeholder
    value: _Placeholder

@dataclass(frozen=True, slots=True)
class _NormalizedDraft:
    version: str
    steps: tuple[_WaitStep | _SetFieldStep, ...]

@dataclass(frozen=True, slots=True)
class HistoryResult:
    status: StatusCode
    undo_count: int
    redo_count: int
    is_open: bool

@dataclass(frozen=True, slots=True)
class HistoryView:
    status: StatusCode
    is_open: bool
    undo_count: int
    redo_count: int
    current: dict[str, Any] | None


def _strict_int(value: Any, low: int, high: int) -> int:
    if type(value) is not int or value < low or value > high:
        raise HistoryValidationError()
    return value


def _parse_placeholder(raw: Any, allowed: frozenset[str], slots: dict[int, str]) -> _Placeholder:
    if type(raw) is not dict or raw.keys() != _PLACEHOLDER_KEYS:
        raise HistoryValidationError()
    kind = raw["type"]
    if type(kind) is not str or kind not in allowed:
        raise HistoryValidationError()
    slot = _strict_int(raw["slot"], 1, MAX_SLOTS)
    prev = slots.get(slot)
    if prev is not None and prev != kind:
        raise HistoryValidationError()
    slots[slot] = kind
    if len(slots) > MAX_SLOTS:
        raise HistoryValidationError()
    return _Placeholder(kind=kind, slot=slot)


def _normalize_draft(raw: Any) -> _NormalizedDraft:
    if type(raw) is not dict or raw.keys() != _DRAFT_KEYS:
        raise HistoryValidationError()
    if type(raw["version"]) is not str or raw["version"] != HISTORY_VERSION:
        raise HistoryValidationError()
    raw_steps = raw["steps"]
    if type(raw_steps) not in (list, tuple) or len(raw_steps) > MAX_STEPS:
        raise HistoryValidationError()
    normalized: list[_WaitStep | _SetFieldStep] = []
    slots: dict[int, str] = {}
    for step in raw_steps:
        if type(step) is not dict or type(step.get("op")) is not str:
            raise HistoryValidationError()
        op = step["op"]
        if op == "wait" and step.keys() == _WAIT_KEYS:
            normalized.append(_WaitStep(ms=_strict_int(step["ms"], 0, MAX_WAIT_MS)))
        elif op == "set_field" and step.keys() == _SET_FIELD_KEYS:
            target = _parse_placeholder(step["target"], _TARGET_TYPES, slots)
            value = _parse_placeholder(step["value"], _VALUE_TYPES, slots)
            normalized.append(_SetFieldStep(target=target, value=value))
        else:
            raise HistoryValidationError()
    return _NormalizedDraft(version=HISTORY_VERSION, steps=tuple(normalized))


def _materialize_draft(snap: _NormalizedDraft) -> dict[str, Any]:
    steps_out: list[dict[str, Any]] = [
        {"op": "wait", "ms": s.ms} if isinstance(s, _WaitStep) else {
            "op": "set_field",
            "target": {"type": s.target.kind, "slot": s.target.slot},
            "value": {"type": s.value.kind, "slot": s.value.slot},
        }
        for s in snap.steps
    ]
    return {"version": snap.version, "steps": steps_out}


def validate_draft(raw: Any) -> dict[str, Any]:
    return _materialize_draft(_normalize_draft(raw))


class SkillEditHistory:
    __slots__ = ("_current", "_undo", "_redo", "_open")

    def __init__(self, initial_draft: dict[str, Any]) -> None:
        self._current: _NormalizedDraft | None = _normalize_draft(initial_draft)
        self._undo: list[_NormalizedDraft] = []
        self._redo: list[_NormalizedDraft] = []
        self._open: bool = True

    def _result(self, status: StatusCode) -> HistoryResult:
        return HistoryResult(status, len(self._undo), len(self._redo), self._open)

    def apply_edit(self, draft: Any) -> HistoryResult:
        if not self._open or self._current is None:
            return HistoryResult("closed", 0, 0, False)
        try:
            candidate = _normalize_draft(draft)
        except HistoryValidationError:
            return self._result("rejected")
        if candidate == self._current:
            return self._result("noop")
        self._redo.clear()
        if len(self._undo) >= MAX_HISTORY_SNAPSHOTS:
            del self._undo[0]
        self._undo.append(self._current)
        self._current = candidate
        return self._result("applied")

    def undo(self) -> HistoryResult:
        if not self._open or self._current is None:
            return HistoryResult("closed", 0, 0, False)
        if not self._undo:
            return self._result("empty_undo")
        self._redo.append(self._current)
        self._current = self._undo.pop()
        return self._result("undone")

    def redo(self) -> HistoryResult:
        if not self._open or self._current is None:
            return HistoryResult("closed", 0, 0, False)
        if not self._redo:
            return self._result("empty_redo")
        self._undo.append(self._current)
        self._current = self._redo.pop()
        return self._result("redone")

    def inspect(self) -> HistoryView:
        if not self._open or self._current is None:
            return HistoryView("closed", False, 0, 0, None)
        return HistoryView("open", True, len(self._undo), len(self._redo), _materialize_draft(self._current))

    def close(self) -> HistoryResult:
        self._undo.clear()
        self._redo.clear()
        self._current = None
        self._open = False
        return HistoryResult("closed", 0, 0, False)


def open_history(initial_draft: dict[str, Any]) -> SkillEditHistory:
    return SkillEditHistory(initial_draft)


def _demo_wait(ms: int) -> dict[str, Any]:
    return {"version": HISTORY_VERSION, "steps": [{"op": "wait", "ms": ms}]}


def _run_demo_undo_redo() -> int:
    h = open_history(_demo_wait(100))
    steps = [
        ("open", HistoryResult("opened", 0, 0, True)), ("edit_1", h.apply_edit(_demo_wait(250))),
        ("edit_2", h.apply_edit(_demo_wait(500))), ("undo_1", h.undo()), ("redo_1", h.redo()),
        ("undo_2", h.undo()), ("invalid_edit", h.apply_edit(_demo_wait(-1))),
        ("edit_3", h.apply_edit(_demo_wait(750))), ("redo_2", h.redo()),
        ("undo_3", h.undo()), ("close", h.close()),
    ]
    for label, res in steps:
        sys.stdout.write(f"{label} status={res.status} undo={res.undo_count} redo={res.redo_count}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    if (sys.argv[1:] if argv is None else argv) == ["--demo", "undo-redo"]:
        return _run_demo_undo_redo()
    sys.stderr.write("usage_error\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
