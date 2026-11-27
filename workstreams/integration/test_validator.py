import unittest
from importlib.util import find_spec


class ValidatorTests(unittest.TestCase):
    def test_exact_synthetic_selection(self):
        self.assertIsNotNone(find_spec('validator'), 'missing lane validator')
        from validator import validate
        self.assertEqual(validate('select', ['fixture:button'], True), 'allow')

    def test_revocation_overrides_all_decisions(self):
        from validator import validate
        for consent in [False, None, 1, 'granted']:
            for action, targets in [('select', ['fixture:button']), ('select', []), ('open', None)]:
                self.assertEqual(validate(action, targets, consent), 'stop')

    def test_ambiguous_candidates(self):
        from validator import validate
        for targets in [[], ['fixture:button', 'other'], ['fixture:button'] * 2]:
            self.assertEqual(validate('select', targets, True), 'clarify')

    def test_allowlist(self):
        from validator import validate
        for action, targets in [('open', ['fixture:button']), ('select', ['other']), ('select', 'fixture:button'), ('select', [42])]:
            self.assertEqual(validate(action, targets, True), 'deny')
