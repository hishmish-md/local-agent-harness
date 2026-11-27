import json, unittest
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / 'notebooks/gpt-oss-120b.ipynb'

class Notebook(unittest.TestCase):
    def test_preflight(self):
        self.assertTrue(NB.is_file(), 'missing Colab notebook')
        cells = json.loads(NB.read_text())['cells']
        ns = {}
        for c in cells:
            if c['cell_type'] == 'code':
                src = ''.join(c['source']); compile(src, c['id'], 'exec')
                if c['id'] == 'settings': exec(src, ns)
        row = 'NVIDIA RTX PRO 6000 Blackwell, 97800, 96100, 12.0, 580.0'
        ns['check_gpu'](row)
        for bad in (row.replace('PRO 6000','4090'), row.replace('96100','30000'), row+'\n'+row, row.replace('12.0','9.0')):
            with self.assertRaises(RuntimeError): ns['check_gpu'](bad)
