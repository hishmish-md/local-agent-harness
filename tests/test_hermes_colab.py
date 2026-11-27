"""Offline only: synthetic HTTP, no Colab/vLLM/model downloads."""
import json
import hashlib
import importlib
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'notebooks'))
h = importlib.import_module('hermes_colab')


@contextmanager
def fixture(handler):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown(); thread.join(); server.server_close()


class Models(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def reply(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path != '/v1/models':
            return self.reply(404, {})
        if not self.headers.get('Authorization') and not getattr(self.server, 'open_access', False):
            return self.reply(401, {})
        if self.headers.get('Authorization') not in {None, 'Bearer synthetic-only'}:
            return self.reply(403, {})
        self.reply(200, {'data': getattr(self.server, 'rows', [{'id': h.MODEL, 'max_model_len': 64000}])})


class Bootstrap(unittest.TestCase):
    def test_pinned_runtime_inputs_reject_changed_bytes(self):

        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'config.json').write_bytes(b'{}'); shard = root/'model.safetensors'; shard.write_bytes(b'payload')
            manifest = {'config.json':hashlib.sha1(b'blob 2\0{}').hexdigest(), 'model.safetensors':hashlib.sha256(b'payload').hexdigest()}
            expected = hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            self.assertEqual(h.snapshot_digest(root), expected)
            shard.write_bytes(b'tampered'); self.assertNotEqual(h.snapshot_digest(root), expected)

    def test_no_launch_without_interactive_authorization(self):
        with patch('subprocess.Popen', side_effect=AssertionError('should not start')), self.assertRaises(RuntimeError):
            h.run_notebook()
        shell = type('Shell', (), {'__module__':'google.colab._shell'})()
        with (patch('builtins.get_ipython', return_value=shell, create=True), patch('sys.platform','linux'),
              patch('builtins.input', return_value='no'), patch('subprocess.Popen', side_effect=AssertionError('started')),
              self.assertRaisesRegex(RuntimeError,'Not confirmed')):
            h.run_notebook()

    def test_terminate_owned_child(self):
        proc = subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(60)'], start_new_session=os.name!='nt')
        try: h.terminate(proc); self.assertIsNotNone(proc.poll())
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()

    def test_documented_cell_fails_closed_without_colab(self):
        import re
        doc = (ROOT/'notebooks/hermes-colab.md').read_text(encoding='utf8')
        cells = re.findall(r'```python\n(.*?)```', doc, re.S); self.assertEqual(len(cells), 1)
        src = cells[0].replace("'/content/hermes_colab.py'", repr(str(ROOT/'notebooks/hermes_colab.py')))
        with self.assertRaisesRegex(RuntimeError, 'interactive Colab'): exec(compile(src, 'cell', 'exec'), {})

    def test_launch_shape_and_resource_gate(self):
        args = h.server_args(Path('/fixture/bin/vllm'), Path('/fixture/weights'), 8234)
        for flag, value in [('--host','127.0.0.1'),('--port','8234'),('--max-model-len','64000'),
                            ('--max-num-seqs','1'),('--tool-call-parser','openai')]:
            self.assertEqual(args[args.index(flag)+1],value)
        self.assertNotIn('--api-key', args)
        h.gpu_check('NVIDIA RTX PRO 6000 Blackwell, 97800, 96100, 12.0')
        for bad in ('', 'NVIDIA RTX 4090, 24576, 23500, 8.9', 'NVIDIA RTX PRO 6000 Blackwell, 97800, 16200, 12.0'):
            with self.assertRaises(RuntimeError): h.gpu_check(bad)

    def test_runtime_assets_cannot_escape_to_other_storage(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle = root / 'assets'; bundle.mkdir(); f = bundle / 'file'; f.touch()
            self.assertEqual(h.local_asset(root,bundle,f), f.resolve())
            for path in (bundle / 'missing', root / 'outside', bundle / '..' / 'elsewhere'):
                with self.assertRaises((RuntimeError, FileNotFoundError)):
                    h.local_asset(root,bundle,path)

    def test_worker_environment_does_not_inherit_credentials(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'OPENAI_API_KEY':'synthetic-canary','HTTP_PROXY':'http://invalid.invalid'}):
            env = h.child_env(Path(d))
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('HTTP_PROXY', env)
            self.assertEqual(env['HOME'], d)
            self.assertTrue(Path(env['HERMES_HOME']).is_relative_to(d))

    @unittest.skipUnless(os.environ.get('SYNTHETIC_HERMES_SRC'), 'set SYNTHETIC_HERMES_SRC for pinned-core fixture')
    def test_real_core_synthetic_endpoint(self):
        seen = []
        class Chat(Models):
            def do_POST(self):
                if self.path != '/v1/chat/completions' or self.headers.get('Authorization') != 'Bearer synthetic-only':
                    return self.reply(403, {})
                req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                seen.append((req['model'], [t['function']['name'] for t in req.get('tools', [])],
                             req.get('max_tokens', req.get('max_completion_tokens'))))
                msg = req['messages'][-1]
                if msg['role'] == 'tool':
                    word = 'unverified' if self.reject else json.loads(msg['content'])['name']
                    answer = {'role':'assistant', 'content':word}; reason = 'stop'
                else:
                    call = {'id':'call_fixture', 'type':'function', 'function':{'name':'lookup_item', 'arguments':'{"id":"A17"}'}}
                    answer = {'role':'assistant','content':None,'tool_calls':[call]}; reason = 'tool_calls'
                result = {'id':'synthetic', 'object':'chat.completion', 'created':1, 'model':h.MODEL,
                          'choices':[{'index':0,'message':answer,'finish_reason':reason}],
                          'usage':{'prompt_tokens':256,'completion_tokens':20,'total_tokens':276}}
                if not req.get('stream'): return self.reply(200, result)
                self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
                if 'tool_calls' in answer: answer['tool_calls'][0]['index'] = 0
                for delta, finish in ((answer,None), ({},reason)):
                    result.update(object='chat.completion.chunk', choices=[{'index':0,'delta':delta,'finish_reason':finish}])
                    self.wfile.write(('data: '+json.dumps(result)+'\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            reject = False
        with fixture(Chat) as port, tempfile.TemporaryDirectory() as d:
            result = h.run_worker(Path(sys.executable), Path(os.environ['SYNTHETIC_HERMES_SRC']), Path(d), port, 'synthetic-only')
        self.assertEqual(result, 'verified lookup')
        self.assertEqual(seen, [(h.MODEL,['lookup_item'],h.OUTPUT)]*2)
        Chat.reject = True
        with fixture(Chat) as port, tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(RuntimeError, 'did not verify'):
            h.run_worker(Path(sys.executable), Path(os.environ['SYNTHETIC_HERMES_SRC']), Path(d), port, 'synthetic-only')

    def test_exact_runtime_window(self):

        with fixture(Models) as port:
            self.assertEqual(h.probe(port, 'synthetic-only'), 64000)
            with self.assertRaises(RuntimeError):
                h.probe(port, 'invalid')
        for bad in (8192, None, True, '64000', 131072):
            with self.subTest(value=bad), self.assertRaises(RuntimeError):
                h.verified_window([{'id': h.MODEL, 'max_model_len': bad}])
        for rows in ([], [{'id':'wrong', 'max_model_len':64000}], [{'id':h.MODEL}]*2):
            with self.assertRaises(RuntimeError): h.verified_window(rows)

    def test_open_or_redirect_endpoint_denied(self):
        class Open(Models):
            def do_GET(self): self.reply(200, {})
        class Redirect(Models):
            def do_GET(self):
                self.send_response(302); self.send_header('Location', 'http://invalid.invalid'); self.end_headers()
        for cls in (Open, Redirect):
            with fixture(cls) as port, self.assertRaises(RuntimeError): h.probe(port, 'synthetic-only')
