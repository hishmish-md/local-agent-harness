"""Unit and boundary-matrix tests for FakeClock, ConsentMachine, and SkillRecorder."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from clock import FakeClock
from consent import MAX_CONSENT_DURATION_S, ConsentError, ConsentMachine, ConsentState
from recorder import REDACTED_TOKEN, RawEvent, SkillRecorder


@pytest.mark.parametrize("delta,expected", [(0.0, 0.0), (1.5, 1.5), (30.0, 30.0)])
def test_fake_clock_valid_advances(delta: float, expected: float) -> None:
    clock = FakeClock()
    assert clock.advance(delta) == expected
    assert clock.now() == expected
    assert clock.ticks == [expected]


@pytest.mark.parametrize(
    "bad_value,exc_type",
    [(-0.1, ValueError), (math.nan, ValueError), (math.inf, ValueError), (True, TypeError)],
)
def test_fake_clock_rejects_invalid_deltas(bad_value: object, exc_type: type[Exception]) -> None:
    clock = FakeClock()
    with pytest.raises(exc_type):
        clock.advance(bad_value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "app_id,purpose,duration",
    [
        ("", "demo", 60.0),
        ("   ", "demo", 60.0),
        ("app.demo", "", 60.0),
        ("app.demo", "demo", 0.0),
        ("app.demo", "demo", -5.0),
        ("app.demo", "demo", MAX_CONSENT_DURATION_S + 0.1),
        ("app.demo", "demo", math.inf),
        ("app.demo", "demo", True),
    ],
)
def test_consent_grant_rejects_invalid_boundaries(
    app_id: str, purpose: str, duration: object
) -> None:
    machine = ConsentMachine(FakeClock())
    with pytest.raises(ConsentError):
        machine.grant(app_id, purpose, duration)  # type: ignore[arg-type]
    assert machine.state == ConsentState.IDLE
    assert machine.can_record() is False


def test_consent_expiry_exact_boundary_and_pause_resume() -> None:
    clock = FakeClock()
    machine = ConsentMachine(clock)
    scope = machine.grant("app.demo", "record_form", max_duration_s=10.0)
    assert scope.expires_at_s == 10.0

    machine.pause()
    assert machine.state == ConsentState.PAUSED
    assert machine.can_record() is False

    clock.advance(10.0)
    machine.resume()
    assert machine.state == ConsentState.GRANTED
    assert machine.can_record() is True  # exact boundary <= expires_at_s

    clock.advance(0.001)
    assert machine.can_record() is False
    assert machine.state == ConsentState.STOPPED
    assert machine.scope is None


def test_consent_revoke_and_crash_prevent_auto_resume() -> None:
    clock = FakeClock()
    machine = ConsentMachine(clock)
    machine.grant("app.demo", "record_form", max_duration_s=60.0)

    machine.revoke("employee_clicked_revoke")
    assert machine.state == ConsentState.REVOKED
    assert machine.can_record() is False
    with pytest.raises(ConsentError):
        machine.resume()

    machine.grant("app.demo", "regranted", max_duration_s=60.0)
    machine.simulate_crash("unexpected_exit")
    assert machine.state == ConsentState.CRASHED
    assert machine.can_record() is False
    with pytest.raises(ConsentError):
        machine.resume()


def test_recorder_blocks_pre_consent_and_out_of_scope_app() -> None:
    clock = FakeClock()
    consent = ConsentMachine(clock)
    recorder = SkillRecorder(consent, clock)

    pre_ev = RawEvent(kind="fill", target_id="vendor", app_id="app.demo", value="Acme")
    assert recorder.record(pre_ev) is None
    assert recorder.snapshot_draft() == []
    assert recorder.dropped_count == 1

    consent.grant("app.demo", "demo", max_duration_s=60.0)
    other_app = RawEvent(kind="fill", target_id="vendor", app_id="app.other", value="Acme")
    assert recorder.record(other_app) is None
    assert recorder.snapshot_draft() == []
    assert recorder.dropped_count == 2


@pytest.mark.parametrize(
    "target_id,field_name,is_secret,raw_val,expected_val,expected_redacted",
    [
        ("field_vendor", "vendor_name", False, "Synthetic Co", "Synthetic Co", False),
        ("field_custom", "custom", True, "FAKE_SECRET_1", REDACTED_TOKEN, True),
        ("field_box", "user_password", False, "FAKE_SECRET_2", REDACTED_TOKEN, True),
        ("api_key_input", "box", False, "FAKE_SECRET_3", REDACTED_TOKEN, True),
        ("field_token", "auth_token", False, "FAKE_SECRET_4", REDACTED_TOKEN, True),
        ("field_ssn", "tax_ssn", False, "FAKE_SECRET_5", REDACTED_TOKEN, True),
    ],
)
def test_secret_redaction_matrix(
    target_id: str,
    field_name: str,
    is_secret: bool,
    raw_val: str,
    expected_val: str,
    expected_redacted: bool,
) -> None:
    clock = FakeClock()
    consent = ConsentMachine(clock)
    consent.grant("app.demo", "demo", max_duration_s=60.0)
    recorder = SkillRecorder(consent, clock)

    rec = recorder.record(
        RawEvent(
            kind="fill",
            target_id=target_id,
            app_id="app.demo",
            value=raw_val,
            is_secret=is_secret,
            field_name=field_name,
        )
    )
    assert rec is not None
    assert rec.value == expected_val
    assert rec.redacted is expected_redacted
    if expected_redacted:
        assert raw_val not in str(recorder.snapshot_draft())


@pytest.mark.parametrize(
    "kind,wait_s",
    [("eval", 0.0), ("fill", -1.0), ("wait", 120.1), ("wait", True)],
)
def test_raw_event_rejects_invalid_kind_or_wait(kind: str, wait_s: object) -> None:
    with pytest.raises(ValueError):
        RawEvent(
            kind=kind,  # type: ignore[arg-type]
            target_id="btn",
            app_id="app.demo",
            wait_seconds=wait_s,  # type: ignore[arg-type]
        )


def test_revoke_and_crash_discard_unapproved_drafts() -> None:
    clock = FakeClock()
    consent = ConsentMachine(clock)
    consent.grant("app.demo", "demo", max_duration_s=60.0)
    recorder = SkillRecorder(consent, clock)

    ev = RawEvent(kind="click", target_id="btn_next", app_id="app.demo")
    assert recorder.record(ev) is not None
    assert recorder.revoke_and_discard() == 1
    assert recorder.snapshot_draft() == []
    assert recorder.record(ev) is None

    consent.grant("app.demo", "demo2", max_duration_s=60.0)
    assert recorder.record(ev) is not None
    assert recorder.crash_and_discard() == 1
    assert recorder.snapshot_draft() == []
    assert recorder.record(ev) is None
