import json, unittest
from pathlib import Path
R = Path(__file__).resolve().parent
class Fixtures(unittest.TestCase):
    def test_two_seeds(self):
        paths = sorted(R.glob('seed-*.json'))
        self.assertEqual(len(paths), 2)
        cases = [json.loads(p.read_text()) for p in paths]
        self.assertEqual([c['mask'] for c in cases], ['A','B'])
        for c in cases:
            self.assertNotEqual(type(c['draft']['count']), int)
            self.assertIs(type(c['source']['count']), int)
            self.assertTrue(0 < c['ready_tick'] < c['deadline'])
            self.assertIn('emit', c['review_only'])
        self.assertNotEqual(cases[0]['review_only'], cases[1]['review_only'])
if __name__ == '__main__': unittest.main()
