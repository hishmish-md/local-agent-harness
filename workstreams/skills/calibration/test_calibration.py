"""Synthetic calibration tests for Friend / Neon (F-NEON-01).

Run offline with either:
    pytest -v workstreams/skills/calibration/test_calibration.py
    python -m unittest discover -s workstreams/skills/calibration -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_DIR = str(Path(__file__).resolve().parent)
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from synthetic_calibration import ConsentState, FakeClock, SyntheticBroker

SEEDS = (101, 202)


class SyntheticCalibrationTests(unittest.TestCase):
    def test_delayed_step_dispatches_once_after_readiness(self) -> None:
        for seed in SEEDS:
            for ready_at_s in (0.0, 2.0, 8.0):
                with self.subTest(seed=seed, ready_at_s=ready_at_s):
                    clock = FakeClock()
                    broker = SyntheticBroker(clock=clock, seed=seed)
                    broker.grant_consent()

                    action = {
                        "type": "click",
                        "target_id": f"btn_ready_{seed}",
                        "wait_seconds": 10.0,
                    }
                    res = broker.execute_delayed_step(
                        action=action,
                        ready_at_s=ready_at_s,
                        timeout_s=10.0,
                        poll_step_s=1.0,
                    )
                    self.assertEqual(res.status, "dispatched")
                    self.assertTrue(res.dispatched)
                    self.assertEqual(res.dispatch_count, 1)
                    self.assertEqual(res.elapsed_s, ready_at_s)
                    self.assertEqual(len(broker.dispatched_actions), 1)

    def test_delayed_step_never_ready_times_out_without_action(self) -> None:
        for seed in SEEDS:
            with self.subTest(seed=seed):
                clock = FakeClock()
                broker = SyntheticBroker(clock=clock, seed=seed)
                broker.grant_consent()

                action = {
                    "type": "click",
                    "target_id": f"btn_never_{seed}",
                    "wait_seconds": 5.0,
                }
                res = broker.execute_delayed_step(
                    action=action, ready_at_s=None, timeout_s=5.0, poll_step_s=1.0
                )
                self.assertEqual(res.status, "timed_out")
                self.assertFalse(res.dispatched)
                self.assertEqual(res.dispatch_count, 0)
                self.assertEqual(res.elapsed_s, 5.0)
                self.assertEqual(broker.dispatched_actions, [])

    def test_malformed_action_rejected_before_dispatch(self) -> None:
        cases = [
            ({"type": "shell_exec", "target_id": "btn_1"}, "invalid_action_type"),
            ({"type": "click", "target_id": "   "}, "missing_target_id"),
            ({"type": "wait", "target_id": "form_1", "wait_seconds": -1}, "invalid_wait_seconds"),
            ({"type": "wait", "target_id": "form_1", "wait_seconds": 999}, "invalid_wait_seconds"),
            ({"type": "click", "target_id": "btn_1", "raw_secret": "fake-123"}, "unexpected_fields:raw_secret"),
        ]
        for seed in SEEDS:
            for bad_action, expected_reason in cases:
                with self.subTest(seed=seed, expected_reason=expected_reason):
                    clock = FakeClock()
                    broker = SyntheticBroker(clock=clock, seed=seed)
                    broker.grant_consent()

                    res = broker.execute_delayed_step(
                        action=bad_action, ready_at_s=0.0, timeout_s=5.0
                    )
                    self.assertEqual(res.status, "rejected_schema")
                    self.assertFalse(res.dispatched)
                    self.assertEqual(res.dispatch_count, 0)
                    self.assertEqual(res.reason, expected_reason)
                    self.assertEqual(clock.now, 0.0)
                    self.assertEqual(broker.dispatched_actions, [])

    def test_consent_never_granted_blocks_dispatch(self) -> None:
        for seed in SEEDS:
            with self.subTest(seed=seed):
                clock = FakeClock()
                broker = SyntheticBroker(clock=clock, seed=seed)

                action = {"type": "submit", "target_id": f"form_{seed}"}
                res = broker.execute_delayed_step(
                    action=action, ready_at_s=0.0, timeout_s=5.0
                )
                self.assertEqual(res.status, "blocked_no_consent")
                self.assertFalse(res.dispatched)
                self.assertEqual(res.dispatch_count, 0)
                self.assertEqual(broker.consent, ConsentState.IDLE)
                self.assertEqual(broker.dispatched_actions, [])

    def test_consent_withdrawn_before_dispatch_halts_mid_wait(self) -> None:
        for seed in SEEDS:
            with self.subTest(seed=seed):
                clock = FakeClock()
                broker = SyntheticBroker(clock=clock, seed=seed)
                broker.grant_consent()

                action = {
                    "type": "submit",
                    "target_id": f"form_{seed}",
                    "wait_seconds": 8.0,
                }
                res = broker.execute_delayed_step(
                    action=action,
                    ready_at_s=8.0,
                    timeout_s=10.0,
                    poll_step_s=1.0,
                    revoke_at_s=3.0,
                )
                self.assertEqual(res.status, "halted_revoked")
                self.assertFalse(res.dispatched)
                self.assertEqual(res.dispatch_count, 0)
                self.assertEqual(res.elapsed_s, 3.0)
                self.assertEqual(broker.consent, ConsentState.REVOKED)
                self.assertEqual(broker.dispatched_actions, [])

                res2 = broker.execute_delayed_step(
                    action=action, ready_at_s=0.0, timeout_s=5.0
                )
                self.assertEqual(res2.status, "blocked_no_consent")
                self.assertFalse(res2.dispatched)
                self.assertEqual(broker.dispatched_actions, [])


if __name__ == "__main__":
    unittest.main()
