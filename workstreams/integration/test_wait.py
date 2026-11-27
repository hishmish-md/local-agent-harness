import unittest
import validator


class WaitTests(unittest.TestCase):
    def pending(self, consent=lambda: True):
        self.assertTrue(hasattr(validator, 'PendingSelection'), 'missing offline wait')
        now = [100]
        pending = validator.PendingSelection('select', ['fixture:button'], consent,
                                             clock=lambda: now[0], wait=5)
        return now, pending

    def test_cancel_during_wait_is_terminal(self):
        now, pending = self.pending()
        now[0] += 2
        self.assertEqual(pending.poll(), 'waiting')
        self.assertTrue(hasattr(pending, 'cancel'), 'missing cancellation')
        pending.cancel()
        pending.edit_wait(0)
        now[0] += 10
        self.assertEqual(pending.poll(), 'cancelled')
        self.assertEqual(pending.events, ())

    def test_recheck_consent_at_dispatch_boundary(self):
        for revoked in (False, None, 1):
            with self.subTest(revoked=revoked):
                replies = iter((True, revoked))
                now, pending = self.pending(lambda: next(replies))
                self.assertEqual(pending.poll(), 'waiting')
                now[0] += 5
                self.assertEqual(pending.poll(), 'stop')
                self.assertEqual(pending.poll(), 'stop')
                self.assertEqual(pending.events, ())

    def test_edit_wait_relative_to_start_and_dispatch_once(self):
        now, pending = self.pending()
        now[0] = 104
        self.assertEqual(pending.poll(), 'waiting')
        pending.edit_wait(8)
        now[0] = 107
        self.assertEqual(pending.poll(), 'waiting')
        self.assertEqual(pending.events, ())
        now[0] = 108
        self.assertEqual(pending.poll(), 'dispatched')
        self.assertEqual(pending.poll(), 'dispatched')
        self.assertEqual(pending.events, (('select', 'fixture:button'),))
