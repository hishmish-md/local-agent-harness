"""Consent-gated synthetic event recorder with secret redaction (F-NEON-01)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from clock import FakeClock
from consent import ConsentMachine

EventKind = Literal["fill", "click", "wait", "submit"]
ALLOWED_EVENT_KINDS: frozenset[str] = frozenset({"fill", "click", "wait", "submit"})
REDACTED_TOKEN = "[REDACTED]"
MIN_POSITIVE_WAIT_S = 1e-6
MAX_RECORDED_WAIT_S = 120.0
SECRET_KEYWORDS: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "ssn",
    "pin",
)


@dataclass(frozen=True)
class RawEvent:
    kind: EventKind
    target_id: str
    app_id: str
    value: str | None = None
    wait_seconds: float = 0.0
    is_secret: bool = False
    field_name: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_EVENT_KINDS:
            raise ValueError(f"unsupported event kind: {self.kind}")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id must be a non-empty string")
        if not isinstance(self.app_id, str) or not self.app_id.strip():
            raise ValueError("app_id must be a non-empty string")
        if (
            isinstance(self.wait_seconds, bool)
            or not isinstance(self.wait_seconds, (int, float))
            or not math.isfinite(self.wait_seconds)
            or self.wait_seconds < 0.0
            or (0.0 < self.wait_seconds < MIN_POSITIVE_WAIT_S)
            or self.wait_seconds > MAX_RECORDED_WAIT_S
        ):
            raise ValueError("wait_seconds must be 0 or in [1e-6, 120]")


@dataclass(frozen=True)
class RecordedEvent:
    seq: int
    timestamp_s: float
    kind: EventKind
    target_id: str
    app_id: str
    value: str | None
    wait_seconds: float
    redacted: bool


class SecretRedactor:
    """Redacts declared or keyword-matched secret fields prior to storage."""

    @staticmethod
    def is_secret_event(event: RawEvent) -> bool:
        if event.is_secret:
            return True
        haystack = f"{event.field_name} {event.target_id}".lower()
        return any(keyword in haystack for keyword in SECRET_KEYWORDS)

    @classmethod
    def redact_value(cls, event: RawEvent) -> tuple[str | None, bool]:
        if cls.is_secret_event(event):
            return (REDACTED_TOKEN if event.value is not None else None), True
        return event.value, False


class SkillRecorder:
    """Records redacted synthetic events only while scoped consent is active."""

    def __init__(self, consent: ConsentMachine, clock: FakeClock) -> None:
        self._consent = consent
        self._clock = clock
        self._draft: list[RecordedEvent] = []
        self._dropped_count: int = 0

    @property
    def dropped_count(self) -> int:
        return self._dropped_count

    def snapshot_draft(self) -> list[RecordedEvent]:
        return list(self._draft)

    def record(self, event: RawEvent) -> RecordedEvent | None:
        if not self._consent.can_record():
            self._dropped_count += 1
            return None
        scope = self._consent.scope
        if scope is None or event.app_id.strip() != scope.app_id:
            self._dropped_count += 1
            return None

        safe_value, was_redacted = SecretRedactor.redact_value(event)
        recorded = RecordedEvent(
            seq=len(self._draft) + 1,
            timestamp_s=self._clock.now(),
            kind=event.kind,
            target_id=event.target_id.strip(),
            app_id=event.app_id.strip(),
            value=safe_value,
            wait_seconds=float(event.wait_seconds),
            redacted=was_redacted,
        )
        self._draft.append(recorded)
        return recorded

    def discard_draft(self) -> int:
        removed = len(self._draft)
        self._draft.clear()
        return removed

    def revoke_and_discard(self, reason: str = "employee_revoked") -> int:
        self._consent.revoke(reason)
        return self.discard_draft()

    def crash_and_discard(self, reason: str = "process_crash_reset") -> int:
        self._consent.simulate_crash(reason)
        return self.discard_draft()
