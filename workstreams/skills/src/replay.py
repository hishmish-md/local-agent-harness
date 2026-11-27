"""Confirmation-gated declarative skill replay engine for F-NEON-01.

Uses FakeClock deterministically, requires dry-run + approval before replay,
requires explicit confirmation before submit steps, and halts immediately on
consent revocation or crash (including mid-wait).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from clock import FakeClock
from compiler import DeclarativeSkill, SkillStep, mark_dry_run_passed
from consent import ConsentMachine, ConsentState
from recorder import REDACTED_TOKEN

ConfirmFn = Callable[[SkillStep], bool]
WaitTickHook = Callable[[float, SkillStep], None]


@dataclass(frozen=True)
class StepExecution:
    step_id: str
    kind: str
    target_id: str
    dispatched: bool
    elapsed_s: float
    note: str


@dataclass(frozen=True)
class ReplayResult:
    status: str
    dry_run: bool
    completed: bool
    dispatched_steps: tuple[StepExecution, ...]
    halted_at_step_id: str | None
    submitted: bool
    elapsed_s: float
    reason: str


class ReplayEngine:
    """Offline, deterministic replay engine gated by consent and confirmation."""

    def __init__(self, consent: ConsentMachine, clock: FakeClock, poll_step_s: float = 1.0) -> None:
        if isinstance(poll_step_s, bool) or not isinstance(poll_step_s, (int, float)) or not math.isfinite(poll_step_s) or poll_step_s < 1e-6:
            raise ValueError("poll_step_s must be finite and >= 1e-6")
        self._consent = consent
        self._clock = clock
        self._poll_step_s = float(poll_step_s)
        self._dispatched_log: list[StepExecution] = []

    @property
    def dispatched_log(self) -> list[StepExecution]:
        return list(self._dispatched_log)

    def _consent_halt_reason(self) -> tuple[str, str] | None:
        state = self._consent.state
        if state == ConsentState.REVOKED:
            return "halted_revoked", "consent_revoked"
        if state == ConsentState.CRASHED:
            return "halted_crashed", "consent_crashed"
        if not self._consent.can_record():
            return "blocked_no_consent", f"consent_state:{self._consent.state.value}"
        return None

    def _halt(
        self,
        status: str,
        reason: str,
        start_s: float,
        dispatched: list[StepExecution],
        step_id: str | None,
        dry_run: bool = False,
    ) -> ReplayResult:
        return ReplayResult(
            status=status,
            dry_run=dry_run,
            completed=False,
            dispatched_steps=tuple(dispatched),
            halted_at_step_id=step_id,
            submitted=False,
            elapsed_s=round(self._clock.now() - start_s, 6),
            reason=reason,
        )

    def dry_run(self, skill: DeclarativeSkill) -> tuple[DeclarativeSkill, ReplayResult]:
        start_s = self._clock.now()
        halt = self._consent_halt_reason()
        if halt is not None:
            status, reason = halt
            return skill, self._halt(status, reason, start_s, [], None, dry_run=True)

        simulated: list[StepExecution] = []
        for step in skill.steps:
            if step.redacted and step.value not in (None, REDACTED_TOKEN):
                return skill, self._halt(
                    "blocked_unredacted_secret",
                    "redacted_step_has_raw_value",
                    start_s,
                    simulated,
                    step.step_id,
                    dry_run=True,
                )
            simulated.append(
                StepExecution(
                    step_id=step.step_id,
                    kind=step.kind,
                    target_id=step.target_id,
                    dispatched=False,
                    elapsed_s=round(self._clock.now() - start_s, 6),
                    note="dry_run_ok",
                )
            )
        passed = mark_dry_run_passed(skill)
        return passed, ReplayResult(
            status="dry_run_passed",
            dry_run=True,
            completed=True,
            dispatched_steps=tuple(simulated),
            halted_at_step_id=None,
            submitted=False,
            elapsed_s=round(self._clock.now() - start_s, 6),
            reason="dry_run_verified",
        )

    def _wait_step(
        self,
        step: SkillStep,
        start_s: float,
        on_wait_tick: WaitTickHook | None,
    ) -> tuple[str, str] | None:
        waited = 0.0
        while waited < step.wait_seconds:
            halt = self._consent_halt_reason()
            if halt is not None:
                return halt
            if on_wait_tick is not None:
                on_wait_tick(round(self._clock.now() - start_s, 6), step)
                halt = self._consent_halt_reason()
                if halt is not None:
                    return halt
            delta = min(self._poll_step_s, step.wait_seconds - waited)
            if delta <= 0.0:
                break
            self._clock.advance(delta)
            waited += delta
        if on_wait_tick is not None:
            on_wait_tick(round(self._clock.now() - start_s, 6), step)
        return self._consent_halt_reason()

    def replay(
        self,
        skill: DeclarativeSkill,
        *,
        confirm_submit: ConfirmFn | None = None,
        on_wait_tick: WaitTickHook | None = None,
    ) -> ReplayResult:
        start_s = self._clock.now()
        if not skill.approved or not skill.dry_run_passed:
            return self._halt(
                "blocked_unapproved", "skill_requires_dry_run_and_approval", start_s, [], None
            )
        halt = self._consent_halt_reason()
        if halt is not None:
            return self._halt(halt[0], halt[1], start_s, [], None)

        dispatched: list[StepExecution] = []
        submitted = False
        for step in skill.steps:
            halt = self._consent_halt_reason()
            if halt is not None:
                return self._halt(halt[0], halt[1], start_s, dispatched, step.step_id)
            if step.wait_seconds > 0.0:
                wait_halt = self._wait_step(step, start_s, on_wait_tick)
                if wait_halt is not None:
                    return self._halt(wait_halt[0], wait_halt[1], start_s, dispatched, step.step_id)
            if step.requires_confirmation or step.kind == "submit":
                if confirm_submit is None or not confirm_submit(step):
                    return self._halt(
                        "blocked_confirmation_required",
                        "explicit_submit_confirmation_denied_or_missing",
                        start_s,
                        dispatched,
                        step.step_id,
                    )
                halt = self._consent_halt_reason()
                if halt is not None:
                    return self._halt(halt[0], halt[1], start_s, dispatched, step.step_id)
            entry = StepExecution(
                step_id=step.step_id,
                kind=step.kind,
                target_id=step.target_id,
                dispatched=True,
                elapsed_s=round(self._clock.now() - start_s, 6),
                note="dispatched",
            )
            dispatched.append(entry)
            self._dispatched_log.append(entry)
            if step.kind == "submit":
                submitted = True

        return ReplayResult(
            status="completed",
            dry_run=False,
            completed=True,
            dispatched_steps=tuple(dispatched),
            halted_at_step_id=None,
            submitted=submitted,
            elapsed_s=round(self._clock.now() - start_s, 6),
            reason="all_steps_dispatched",
        )
