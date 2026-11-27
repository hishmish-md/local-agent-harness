"""Synthetic offline calibration harness for Friend / Neon (F-NEON-01).

Covers the three calibration invariants with a deterministic FakeClock and
zero network or host side effects:
  1. Delayed step (bounded wait, act exactly once after readiness, timeout).
  2. Malformed action (strict schema validation, fail closed, zero dispatch).
  3. Consent withdrawn before dispatch (revoke before/during wait -> no action).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_ACTIONS = frozenset({"click", "fill", "wait", "submit"})
MAX_WAIT_SECONDS = 60.0


class ConsentState(Enum):
    IDLE = "idle"
    GRANTED = "granted"
    REVOKED = "revoked"


@dataclass
class FakeClock:
    now: float = 0.0
    ticks: list[float] = field(default_factory=list)

    def advance(self, seconds: float) -> float:
        if seconds < 0:
            raise ValueError("cannot advance clock backwards")
        self.now += seconds
        self.ticks.append(self.now)
        return self.now


@dataclass(frozen=True)
class CalibrationResult:
    status: str
    dispatched: bool
    dispatch_count: int
    elapsed_s: float
    reason: str
    seed: int


class SyntheticBroker:
    """Minimal offline broker used only for synthetic calibration."""

    def __init__(self, clock: FakeClock, seed: int) -> None:
        self.clock = clock
        self.seed = seed
        self.consent = ConsentState.IDLE
        self.dispatched_actions: list[dict[str, Any]] = []

    def grant_consent(self) -> None:
        self.consent = ConsentState.GRANTED

    def revoke_consent(self) -> None:
        self.consent = ConsentState.REVOKED

    def validate_action(self, action: dict[str, Any]) -> tuple[bool, str]:
        if not isinstance(action, dict):
            return False, "action_not_dict"
        kind = action.get("type")
        if not isinstance(kind, str) or kind not in ALLOWED_ACTIONS:
            return False, "invalid_action_type"
        target = action.get("target_id")
        if not isinstance(target, str) or not target.strip():
            return False, "missing_target_id"
        wait_s = action.get("wait_seconds", 0.0)
        if (
            isinstance(wait_s, bool)
            or not isinstance(wait_s, (int, float))
            or wait_s < 0
            or wait_s > MAX_WAIT_SECONDS
        ):
            return False, "invalid_wait_seconds"
        extra_keys = set(action.keys()) - {
            "type",
            "target_id",
            "wait_seconds",
            "value",
        }
        if extra_keys:
            return False, f"unexpected_fields:{','.join(sorted(extra_keys))}"
        return True, "ok"

    def execute_delayed_step(
        self,
        action: dict[str, Any],
        ready_at_s: float | None,
        timeout_s: float,
        poll_step_s: float = 1.0,
        revoke_at_s: float | None = None,
    ) -> CalibrationResult:
        start = self.clock.now
        valid, reason = self.validate_action(action)
        if not valid:
            return CalibrationResult(
                status="rejected_schema",
                dispatched=False,
                dispatch_count=len(self.dispatched_actions),
                elapsed_s=self.clock.now - start,
                reason=reason,
                seed=self.seed,
            )

        if self.consent != ConsentState.GRANTED:
            return CalibrationResult(
                status="blocked_no_consent",
                dispatched=False,
                dispatch_count=len(self.dispatched_actions),
                elapsed_s=self.clock.now - start,
                reason=f"consent_state:{self.consent.value}",
                seed=self.seed,
            )

        while True:
            elapsed = self.clock.now - start
            if revoke_at_s is not None and elapsed >= revoke_at_s:
                self.revoke_consent()
            if self.consent != ConsentState.GRANTED:
                return CalibrationResult(
                    status="halted_revoked",
                    dispatched=False,
                    dispatch_count=len(self.dispatched_actions),
                    elapsed_s=elapsed,
                    reason="consent_withdrawn_before_dispatch",
                    seed=self.seed,
                )
            if ready_at_s is not None and elapsed >= ready_at_s:
                self.dispatched_actions.append(dict(action))
                return CalibrationResult(
                    status="dispatched",
                    dispatched=True,
                    dispatch_count=len(self.dispatched_actions),
                    elapsed_s=elapsed,
                    reason="ready_and_dispatched_once",
                    seed=self.seed,
                )
            if elapsed >= timeout_s:
                return CalibrationResult(
                    status="timed_out",
                    dispatched=False,
                    dispatch_count=len(self.dispatched_actions),
                    elapsed_s=elapsed,
                    reason="bounded_timeout_exceeded",
                    seed=self.seed,
                )
            step = min(poll_step_s, timeout_s - elapsed)
            self.clock.advance(step)
