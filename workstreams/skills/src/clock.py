"""Deterministic offline fake clock for F-NEON-01 (workstreams/skills/)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def _validate_non_negative_seconds(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and >= 0")
    return result


@dataclass
class FakeClock:
    """Monotonic deterministic clock; never reads wall time or sleeps."""

    _now_s: float = 0.0
    ticks: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._now_s = _validate_non_negative_seconds(self._now_s, "initial time")

    def now(self) -> float:
        return self._now_s

    def advance(self, seconds: float) -> float:
        delta = _validate_non_negative_seconds(seconds, "advance seconds")
        self._now_s = round(self._now_s + delta, 6)
        self.ticks.append(self._now_s)
        return self._now_s

    def reset(self, start_s: float = 0.0) -> None:
        self._now_s = _validate_non_negative_seconds(start_s, "start_s")
        self.ticks.clear()
