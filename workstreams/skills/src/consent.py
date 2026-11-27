"""Scoped employee consent state machine for F-NEON-01 (workstreams/skills/)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from clock import FakeClock

MAX_CONSENT_DURATION_S = 3600.0


class ConsentError(RuntimeError):
    """Raised on invalid consent state transitions or boundary violations."""


class ConsentState(Enum):
    IDLE = "idle"
    GRANTED = "granted"
    PAUSED = "paused"
    STOPPED = "stopped"
    REVOKED = "revoked"
    CRASHED = "crashed"


@dataclass(frozen=True)
class ConsentScope:
    app_id: str
    purpose: str
    max_duration_s: float
    granted_at_s: float
    consent_version: str = "v1"

    def __post_init__(self) -> None:
        if not isinstance(self.app_id, str) or not self.app_id.strip():
            raise ConsentError("app_id must be a non-empty string")
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise ConsentError("purpose must be a non-empty string")
        if (
            isinstance(self.max_duration_s, bool)
            or not isinstance(self.max_duration_s, (int, float))
            or not math.isfinite(self.max_duration_s)
            or self.max_duration_s <= 0.0
            or self.max_duration_s > MAX_CONSENT_DURATION_S
        ):
            raise ConsentError("max_duration_s must be in (0, 3600]")

    @property
    def expires_at_s(self) -> float:
        return round(self.granted_at_s + self.max_duration_s, 6)


@dataclass(frozen=True)
class ConsentTransition:
    timestamp_s: float
    previous: ConsentState
    current: ConsentState
    reason: str


class ConsentMachine:
    """Fail-closed consent state machine; never auto-resumes after revoke/crash."""

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self._state: ConsentState = ConsentState.IDLE
        self._scope: ConsentScope | None = None
        self._audit: list[ConsentTransition] = []

    @property
    def state(self) -> ConsentState:
        return self._state

    @property
    def scope(self) -> ConsentScope | None:
        return self._scope

    @property
    def audit_log(self) -> list[ConsentTransition]:
        return list(self._audit)

    def _transition(self, target: ConsentState, reason: str) -> None:
        entry = ConsentTransition(
            timestamp_s=self._clock.now(),
            previous=self._state,
            current=target,
            reason=reason,
        )
        self._state = target
        self._audit.append(entry)

    def grant(self, app_id: str, purpose: str, max_duration_s: float) -> ConsentScope:
        if self._state in (ConsentState.GRANTED, ConsentState.PAUSED):
            raise ConsentError(f"cannot grant while state is {self._state.value}")
        if isinstance(max_duration_s, bool) or not isinstance(max_duration_s, (int, float)):
            raise ConsentError("max_duration_s must be in (0, 3600]")
        scope = ConsentScope(
            app_id=app_id.strip() if isinstance(app_id, str) else app_id,
            purpose=purpose.strip() if isinstance(purpose, str) else purpose,
            max_duration_s=float(max_duration_s),
            granted_at_s=self._clock.now(),
        )
        self._scope = scope
        self._transition(ConsentState.GRANTED, "explicit_employee_consent")
        return scope

    def can_record(self) -> bool:
        if self._state != ConsentState.GRANTED or self._scope is None:
            return False
        if self._clock.now() > self._scope.expires_at_s:
            self._scope = None
            self._transition(ConsentState.STOPPED, "consent_window_expired")
            return False
        return True

    def pause(self, reason: str = "employee_paused") -> None:
        if self._state != ConsentState.GRANTED:
            raise ConsentError(f"cannot pause from {self._state.value}")
        self._transition(ConsentState.PAUSED, reason)

    def resume(self, reason: str = "employee_resumed") -> None:
        if self._state != ConsentState.PAUSED or self._scope is None:
            raise ConsentError(f"cannot resume from {self._state.value}")
        if self._clock.now() > self._scope.expires_at_s:
            self._scope = None
            self._transition(ConsentState.STOPPED, "consent_window_expired")
            raise ConsentError("consent window expired; re-grant required")
        self._transition(ConsentState.GRANTED, reason)

    def stop(self, reason: str = "employee_stopped") -> None:
        if self._state not in (ConsentState.GRANTED, ConsentState.PAUSED):
            raise ConsentError(f"cannot stop from {self._state.value}")
        self._scope = None
        self._transition(ConsentState.STOPPED, reason)

    def revoke(self, reason: str = "employee_revoked") -> None:
        self._scope = None
        self._transition(ConsentState.REVOKED, reason)

    def simulate_crash(self, reason: str = "process_crash_reset") -> None:
        self._scope = None
        self._transition(ConsentState.CRASHED, reason)
