"""One app-visible run, driven only by an integer clock and synthetic inputs."""
import unittest

from workstreams.integration import validator


class SelectionRunTests(unittest.TestCase):
    def setUp(self):
        self.tick = 10

    def start(self, wait=3, consent=lambda: True, candidates=('fixture:button',)):
        self.assertTrue(callable(getattr(validator, 'start_selection', None)),
                        'missing app-facing start_selection')
        return validator.start_selection('select', list(candidates), consent,
                                         clock=lambda: self.tick, wait=wait)

    def test_immediate_stop_beats_even_a_zero_wait(self):
        run = self.start(wait=0)
        self.assertEqual(run.status, 'waiting')
        self.assertEqual(run.stop(), 'stop_requested')
        self.assertEqual(run.poll(), 'stop_requested')
        self.assertEqual(run.events, ())

    def test_only_a_distinct_ack_confirms_the_requested_stop(self):
        run = self.start()
        self.assertEqual(run.acknowledge_stop(), 'waiting')
        self.assertEqual(run.stop(), 'stop_requested')
        self.assertEqual(run.status, 'stop_requested')
        self.assertEqual(run.acknowledge_stop(), 'stopped')
        self.tick += 3
        self.assertEqual(run.poll(), 'stopped')
        self.assertEqual(run.events, ())

    def test_repeated_stops_do_not_ack_or_reopen_the_request(self):
        run = self.start()
        self.assertEqual(run.stop(), 'stop_requested')
        self.assertEqual(run.stop(), 'stop_requested')
        self.assertEqual(run.acknowledge_stop(), 'stopped')
        self.assertEqual(run.stop(), 'stopped')
        self.assertEqual(run.acknowledge_stop(), 'stopped')
        self.assertEqual(run.events, ())

    def test_missing_ack_keeps_work_blocked_past_the_deadline(self):
        run = self.start()
        run.stop()
        for self.tick in (12, 13, 1000):
            run.edit_wait(0)
            self.assertEqual(run.poll(), 'stop_requested')
            self.assertEqual(run.events, ())

    def test_wait_edits_and_polls_dispatch_one_fixture_event(self):
        run = self.start()
        self.tick = 12
        run.edit_wait(5)
        self.tick = 13
        self.assertEqual(run.poll(), 'waiting')
        self.tick = 15
        self.assertEqual((run.status, run.events), ('waiting', ()))
        self.assertEqual(run.poll(), 'dispatched')
        self.assertEqual(run.stop(), 'dispatched')
        self.assertEqual(run.poll(), 'dispatched')
        self.assertEqual(run.events, (('select', 'fixture:button'),))

    def test_refusals_are_not_reported_as_confirmed_stops(self):
        for targets, consent, decision in (([], True, 'clarify'), (['real'], True, 'deny'),
                                           (['fixture:button'], False, 'stop')):
            with self.subTest(decision=decision):
                run = self.start(candidates=targets, consent=lambda: consent)
                self.assertEqual(run.status, decision)
                self.assertEqual(run.stop(), decision)
                self.assertEqual(run.acknowledge_stop(), decision)
                self.assertEqual(run.events, ())

    def test_stop_from_dispatch_consent_callback_wins(self):
        def consent():
            if self.tick == 13:
                run.stop()
            return True

        run = self.start(consent=consent)
        self.tick = 13
        self.assertEqual(run.poll(), 'stop_requested')
        self.assertEqual(run.events, ())
