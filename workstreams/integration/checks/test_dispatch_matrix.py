"""Black-box checks for the offline validator; run directly or via unittest discovery."""

import unittest
from pathlib import Path
from runpy import run_path


# Resolve the lane under test without relying on the caller's cwd or PYTHONPATH.
_lane = run_path(str(Path(__file__).resolve().parents[1] / 'validator.py'))
validate = _lane['validate']
PendingSelection = _lane['PendingSelection']


class DerivedText(str):
    pass


class DerivedList(list):
    pass


BUTTON = 'fixture:button'
# (case, action, candidates, decision with explicit consent)
CASES = (
    ('exact match', 'select', [BUTTON], 'allow'),
    ('empty', 'select', [], 'clarify'),
    ('duplicate match', 'select', [BUTTON, BUTTON], 'clarify'),
    ('mixed targets', 'select', ['other', BUTTON], 'clarify'),
    ('multiple unknown targets', 'select', ['other', 'third'], 'clarify'),
    ('unknown target', 'select', ['other'], 'deny'),
    ('near match', 'select', [BUTTON + ' '], 'deny'),
    ('unknown action', 'open', [BUTTON], 'deny'),
    ('wrong action with ambiguous targets', 'open', [], 'deny'),
    ('null action', None, [BUTTON], 'deny'),
    ('action subclass', DerivedText('select'), [BUTTON], 'deny'),
    ('null candidates', 'select', None, 'deny'),
    ('bare target', 'select', BUTTON, 'deny'),
    ('tuple', 'select', (BUTTON,), 'deny'),
    ('mapping', 'select', {BUTTON: True}, 'deny'),
    ('list subclass', 'select', DerivedList([BUTTON]), 'deny'),
    ('numeric member', 'select', [1], 'deny'),
    ('target subclass', 'select', [DerivedText(BUTTON)], 'deny'),
    ('malformed before valid', 'select', [None, BUTTON], 'deny'),
    ('malformed after valid', 'select', [BUTTON, [BUTTON]], 'deny'),
)
NON_CONSENTS = (False, None, 0, 1, 1.0, '', 'yes', [], [True], {'consent': True})


class DispatchMatrixTests(unittest.TestCase):
    def test_decisions_with_explicit_consent(self):
        for case, action, candidates, expected in CASES:
            with self.subTest(case=case):
                self.assertEqual(validate(action, candidates, True), expected)

    def test_non_consent_overrides_every_decision(self):
        for case, action, candidates, _ in CASES:
            for consent in NON_CONSENTS:
                with self.subTest(case=case, consent=consent):
                    self.assertEqual(validate(action, candidates, consent), 'stop')

    def test_initial_refusal_cannot_become_a_dispatch(self):
        for case, action, candidates, decision in CASES:
            for initial, expected in ((True, decision), (False, 'stop')):
                if expected == 'allow':
                    continue  # Successful selections are exercised at the deadline below.
                with self.subTest(case=case, initial=initial):
                    consent = initial
                    pending = PendingSelection(action, candidates, lambda: consent,
                                               clock=lambda: 0, wait=0)
                    consent = True
                    self.assertEqual(pending.poll(), expected)
                    self.assertEqual(pending.events, ())

    def test_final_consent_controls_the_single_dispatch(self):
        for final in (True, *NON_CONSENTS):
            with self.subTest(final=final):
                tick, consent = 10, True
                pending = PendingSelection('select', [BUTTON], lambda: consent,
                                           clock=lambda: tick, wait=3)
                tick = 12
                self.assertEqual(pending.poll(), 'waiting')
                self.assertEqual(pending.events, ())
                tick, consent = 13, final
                expected = 'dispatched' if final is True else 'stop'
                events = (('select', BUTTON),) if final is True else ()
                self.assertEqual(pending.poll(), expected)
                self.assertEqual(pending.events, events)
                tick, consent = 20, not (final is True)
                self.assertEqual(pending.poll(), expected)
                self.assertEqual(pending.events, events)

    def test_cancel_at_deadline_before_poll_suppresses_dispatch(self):
        tick = 0
        pending = PendingSelection('select', [BUTTON], lambda: True, clock=lambda: tick, wait=2)
        tick = 2
        pending.cancel()
        pending.edit_wait(0)
        self.assertEqual(pending.poll(), 'cancelled')
        self.assertEqual(pending.events, ())


if __name__ == '__main__':
    unittest.main()
