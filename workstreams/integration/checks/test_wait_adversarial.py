"""Offline wait contract checks. Run from the repository root with unittest."""

import unittest
from unittest.mock import Mock

from workstreams.integration.validator import PendingSelection


INVALID_WAITS = (-1, False, True, 0.5, 5.0, '5', None)
SELECTION = (('select', 'fixture:button'),)


class WaitAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tick = 100
        self.consent = Mock(return_value=True)

    def pending(self, wait: object = 5):
        return PendingSelection('select', ['fixture:button'], self.consent,
                                clock=lambda: self.tick, wait=wait)

    def test_zero_wait_dispatches_once_despite_repeated_operations(self):
        pending = self.pending(0)
        self.assertEqual(pending.events, ())
        self.assertEqual(pending.poll(), 'dispatched')
        for tick in (100, 101, 200):
            self.tick = tick
            pending.edit_wait(99)
            pending.cancel()
            self.assertEqual(pending.poll(), 'dispatched')
            self.assertEqual(pending.events, SELECTION)
        self.assertEqual(self.consent.call_count, 2)  # creation and dispatch

    def test_cancel_at_deadline_before_poll_is_terminal(self):
        pending = self.pending()
        self.tick = 104
        self.assertEqual(pending.poll(), 'waiting')
        self.tick = 105
        pending.cancel()
        for tick in (105, 106, 200):
            self.tick = tick
            pending.cancel()
            pending.edit_wait(0)
            self.assertEqual(pending.poll(), 'cancelled')
            self.assertEqual(pending.events, ())
        self.assertEqual(self.consent.call_count, 1)

    def test_cancel_during_deadline_consent_check_is_terminal(self):
        pending = self.pending()

        def consent_while_cancelling():
            pending.cancel()  # same thread, before the simulated event is recorded
            return True

        self.consent.side_effect = consent_while_cancelling
        self.tick = 105
        self.assertEqual((pending.poll(), pending.events), ('cancelled', ()))

    def test_invalid_initial_wait_is_rejected(self):
        for value in INVALID_WAITS:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.pending(value)

    def test_invalid_edit_leaves_original_deadline_intact(self):
        for value in INVALID_WAITS:
            with self.subTest(value=value):
                self.tick = 100
                pending = self.pending()
                self.tick = 104
                with self.assertRaises(ValueError):
                    pending.edit_wait(value)
                self.assertEqual(pending.poll(), 'waiting')
                self.assertEqual(pending.events, ())
                self.tick = 105
                self.assertEqual(pending.poll(), 'dispatched')
                self.assertEqual(pending.events, SELECTION)


if __name__ == '__main__':
    unittest.main()
