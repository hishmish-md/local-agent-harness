"""One foreground synthetic Hermes exercise. See hermes-colab.md for notebook cells."""
import http.client
import hashlib
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MODEL = 'openai/gpt-oss-120b'
REV = 'b5c939de8f754692c1647ca79fbf85e8c1e70f8a'
HERMES_REV = 'caafe5389ae585ef77387a962aee05b1bcf17029'
WINDOW, OUTPUT = 64_000, 1024
HOST = '127.0.0.1'
SNAPSHOT_DIGEST = 'c5b938140f082b6501f86c673fd0015d3367b8438493e847d63cf984f261949d'
VOCABS = {'cl100k_base.tiktoken':'223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7',
          'o200k_base.tiktoken':'446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d'}


def verified_window(rows):
    if (not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict)
            or rows[0].get('id') != MODEL or type(rows[0].get('max_model_len')) is not int
            or rows[0]['max_model_len'] != WINDOW):
        raise RuntimeError('Expected exactly the pinned model serving the requested 64000-token window')
    return WINDOW


def probe(port, key):
    # http.client uses the literal destination; never follows redirects or reads env proxies.
    for token, expected in ((None, 401), (key, 200)):
        connection = http.client.HTTPConnection(HOST, port, timeout=4)
        try:
            connection.request('GET', '/v1/models', headers={'Authorization': 'Bearer '+token} if token else {})
            response = connection.getresponse()
            if response.status != expected:
                raise RuntimeError(f'Model-list access check: expected HTTP {expected}, got {response.status}')
            if token:
                return verified_window(json.loads(response.read(65536))['data'])
        finally:
            connection.close()
    raise RuntimeError('Missing notebook-local key')


def child_env(home):
    # Construct (don't filter) the environment. No ADC, notebook tokens, proxies or API keys.
    profile = home / 'profile'
    profile.mkdir(mode=0o700, exist_ok=True)
    env = dict(HOME=str(home), USERPROFILE=str(home), HERMES_HOME=str(profile), PATH=os.defpath,
               TMPDIR=str(home), TEMP=str(home), TMP=str(home), LANG='C.UTF-8',
               HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1',
               UV_OFFLINE='1', HERMES_DISABLE_LAZY_INSTALLS='1', VLLM_NO_USAGE_STATS='1', NO_PROXY=HOST)
    if os.name == 'nt':  # offline fixture only; live notebook must be Linux
        env.update(SystemRoot=os.environ['SystemRoot'], APPDATA=str(home), LOCALAPPDATA=str(home))
    return env


def checkout(src):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(src), *args], text=True, timeout=30).strip()
    if git('rev-parse', 'HEAD') != HERMES_REV or git('status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('Expected clean, pinned Hermes checkout')
    if (src / '.env').exists():
        raise RuntimeError('Do not import a credential-bearing source tree')


def _worker_guard(port):
    # A tripwire for trusted Python code, NOT a sandbox for arbitrary native extensions.
    def guard(event, args):
        if event == 'socket.getaddrinfo' and args[0] != HOST:
            raise PermissionError('Non-local DNS disabled')
        if event == 'socket.connect' and args[1] != (HOST, port):
            raise PermissionError('Only the notebook model endpoint is allowed')
        if event in {'socket.sendto', 'socket.sendmsg', 'socket.bind', 'os.system', 'os.exec',
                     'os.spawn', 'os.posix_spawn', 'subprocess.Popen'}:
            raise PermissionError('Worker may not launch other processes or network services')
    sys.addaudithook(guard)


def worker(src, port):
    key = json.loads(sys.stdin.readline())
    _worker_guard(port)
    sys.path.insert(0, str(src))
    from agent.model_metadata import MINIMUM_CONTEXT_LENGTH
    from hermes_cli.config import set_config_value
    from run_agent import AIAgent
    from tools.registry import registry

    if MINIMUM_CONTEXT_LENGTH != WINDOW or probe(port, key) != WINDOW:
        raise RuntimeError('Context floor or endpoint changed; requalify first')
    set_config_value('tools.tool_search.enabled', 'off')  # expose the single fixture, not the discovery bridge
    answer = 'Orchid-' + secrets.token_hex(10)
    calls = []
    def lookup(args, **kwargs):
        calls.append(args)
        if args != {'id':'A17'} or len(calls) != 1: return json.dumps({'error':'Invalid synthetic lookup'})
        return json.dumps({'name':answer})
    registry.register(name='lookup_item', toolset='synthetic_inventory', handler=lookup,
        schema={'name':'lookup_item', 'description':'Return the synthetic inventory name for the supplied ID.',
                'parameters':{'type':'object', 'properties':{'id':{'type':'string'}}, 'required':['id'],
                              'additionalProperties':False}})
    agent = AIAgent(model=MODEL, base_url=f'http://{HOST}:{port}/v1', api_key=key,
                    provider='custom', api_mode='chat_completions', enabled_toolsets=['synthetic_inventory'],
                    max_tokens=OUTPUT, max_iterations=3, run_budget_seconds=120, quiet_mode=True,
                    skip_memory=True, skip_context_files=True, skip_background_review=True)
    try:
        if (agent.valid_tool_names != {'lookup_item'} or agent.context_compressor.context_length != WINDOW
                or agent.provider != 'custom' or agent.base_url.rstrip('/') != f'http://{HOST}:{port}/v1'):
            raise RuntimeError(f'Effective worker mismatch: {agent.valid_tool_names!r}, {agent.context_compressor.context_length}, {agent.provider!r}, {agent.base_url!r}')
        result = agent.run_conversation('Call lookup_item with id A17 exactly once. Reply with only its returned name.')
        if (result.get('completed') is not True or result.get('failed') or result.get('error')
                or calls != [{'id':'A17'}] or result.get('final_response', '').strip() != answer):
            raise RuntimeError('No verified worker tool-result round trip')
    finally:
        agent.close()
    # Only the supervising process reads this. No log/assistant/key enters cell output.
    print('VERIFIED_SYNTHETIC_HERMES_LOOKUP', flush=True)


def terminate(proc):
    if os.name == 'nt':
        if proc.poll() is None: proc.kill()
    else:
        try: os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: pass
    if os.name != 'nt':
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    proc.wait(timeout=5)


def run_worker(python, src, home, port, key):
    checkout(src)
    proc = subprocess.Popen([str(python), '-I', '-B', str(Path(__file__).resolve()), 'worker', str(src), str(port)],
        env=child_env(home), cwd=home, text=True, encoding='utf-8', errors='replace',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name!='nt')
    try:
        out, err = proc.communicate(json.dumps(key)+'\n', timeout=180)
        if proc.returncode or 'VERIFIED_SYNTHETIC_HERMES_LOOKUP' not in out.splitlines():
            # No raw model output, exception details, environment or token leaked to the notebook.
            raise RuntimeError(f'Hermes worker did not verify lookup (exit {proc.returncode})')
        return 'verified lookup'
    finally:
        terminate(proc)


def local_asset(root, bundle, path):
    root = root.resolve(strict=True)
    bundle = bundle.resolve(strict=True)
    target = path.resolve(strict=True)
    if (not bundle.is_relative_to(root) or not target.is_relative_to(bundle)
            or target.stat().st_dev != root.stat().st_dev or bundle.stat().st_dev != root.stat().st_dev):
        raise RuntimeError('Use trusted assets on ephemeral notebook storage only')
    return target


def gpu_check(csv):
    fields = [f.strip() for f in csv.strip().split(',')]
    if (len(fields) != 4 or '\n' in csv.strip() or 'RTX PRO 6000' not in fields[0] or 'Blackwell' not in fields[0]
            or fields[3] != '12.0' or int(fields[1]) < 90000 or int(fields[2]) < 88000):
        raise RuntimeError('Missing or busy project GPU; stop, do not allocate another runtime')


def server_args(cli, weights, port):
    return [str(cli), 'serve', str(weights), '--served-model-name', MODEL, '--host', HOST, '--port', str(port),
            '--tensor-parallel-size', '1', '--max-model-len', str(WINDOW), '--max-num-seqs', '1',
            '--tool-call-parser', 'openai', '--enable-auto-tool-choice']


def snapshot_digest(weights):
    # The Hub tree uses SHA-256 for LFS files and Git blob IDs for normal files.
    files = {}
    for p in weights.iterdir():
        if p.suffix not in {'.safetensors','.json','.jinja'}: continue
        lfs = p.suffix == '.safetensors' or p.name == 'tokenizer.json'
        digest = hashlib.sha256() if lfs else hashlib.sha1(f'blob {p.stat().st_size}\0'.encode())
        with p.open('rb') as f:
            for block in iter(lambda:f.read(4*1024*1024), b''): digest.update(block)
        files[p.name] = digest.hexdigest()
    return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run_notebook():
    """Interactive only. No fallback, connection to Colab control APIs, downloads, mounts or schedulers."""
    from builtins import __dict__ as builtins
    shell = builtins.get('get_ipython', lambda: None)()
    if sys.platform != 'linux' or not type(shell).__module__.startswith('google.colab.'):
        raise RuntimeError('This entry point is only for an already attached, interactive Colab notebook')
    if input('Only on your authorized private, already assigned runtime, if this adds no cost and uses '
             'synthetic data only. If unsure, stop. Type RUN ONE FIXTURE: ') != 'RUN ONE FIXTURE':
        raise RuntimeError('Not confirmed; nothing started')
    root = Path('/content'); bundle = root / 'synthetic-assets'
    def asset(*parts): return local_asset(root, bundle, bundle.joinpath(*parts))
    if (root / 'drive').is_mount() or bundle.is_symlink() or bundle.is_mount():
        raise RuntimeError('Use a fresh runtime without mounted user storage')
    src = asset('hermes-agent'); checkout(src)
    # A venv interpreter may symlink to the trusted system interpreter. Keep the venv entry path.
    hp = asset('hermes-env', 'bin') / 'python'; vp = asset('vllm-env', 'bin') / 'python'
    cli = asset('vllm-env','bin','vllm'); weights = asset('snapshots', REV); enc = asset('encodings')
    for name, expected in VOCABS.items():
        if hashlib.sha256(asset('encodings',name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Wrong Harmony encoding; no download attempted')
    for file in weights.iterdir(): local_asset(root, bundle, file)
    config = json.loads((weights/'config.json').read_text())
    if (config.get('model_type') != 'gpt_oss' or config.get('quantization_config', {}).get('quant_method') != 'mxfp4'
            or config.get('max_position_embeddings', 0) < WINDOW):
        raise RuntimeError('Wrong model, quantization or model context capacity')
    shards = set(json.loads((weights/'model.safetensors.index.json').read_text())['weight_map'].values())
    if not shards or not all(Path(s).name == s and s.endswith('.safetensors') and (weights/s).is_file() for s in shards):
        raise RuntimeError('Incomplete pinned snapshot; no model download or fallback')
    gpu_check(subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.free,compute_cap',
                                       '--format=csv,noheader,nounits'],text=True,timeout=15))
    if snapshot_digest(weights) != SNAPSHOT_DIGEST:
        raise RuntimeError('Pinned snapshot bytes differ; no model started')
    with tempfile.TemporaryDirectory(prefix='synthetic-hermes-',dir=root) as d:
        work = Path(d); server_home = work/'server'; agent_home = work/'worker'
        server_home.mkdir(mode=0o700); agent_home.mkdir(mode=0o700)
        env = child_env(server_home)
        env.update(PATH=f'{vp.parent}:/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin',
                   LD_LIBRARY_PATH='/usr/local/nvidia/lib64:/usr/lib64-nvidia:/usr/local/cuda/lib64',
                   CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES','0'), VLLM_HOST_IP=HOST,
                   TIKTOKEN_ENCODINGS_BASE=str(enc), TRANSFORMERS_OFFLINE='1')
        ver = subprocess.check_output([str(vp),'-I','-c','from importlib.metadata import version;print(version("vllm"))'],
                                      env=env,cwd=server_home,text=True,timeout=15).strip()
        if ver != '0.15.1': raise RuntimeError('Expected the project vLLM 0.15.1 environment')
        if subprocess.check_output([str(hp), '-I', '-c', 'import sys; print(sys.version_info[:2])'],
                                   env=child_env(agent_home),cwd=agent_home,text=True,timeout=15).strip() != '(3, 14)':
            raise RuntimeError('Pinned Hermes requires a separate Python 3.14 environment')
        with socket.socket() as reserve:
            reserve.bind((HOST,0)); port = reserve.getsockname()[1]
        key = secrets.token_urlsafe(32)
        # No notebook/Drive logs; missing assets, startup OOM, timeout, or interrupt are not a pass.
        server = subprocess.Popen(server_args(cli, weights, port), env={**env,'VLLM_API_KEY':key}, cwd=server_home,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            deadline = time.monotonic()+600
            while time.monotonic() < deadline:
                if server.poll() is not None: raise RuntimeError(f'vLLM exited before readiness (exit {server.returncode}); stop')
                try: probe(port,key); break
                except (ConnectionRefusedError, ConnectionResetError, TimeoutError, http.client.RemoteDisconnected): time.sleep(1)
            else: raise TimeoutError('vLLM did not become ready in time')
            result = run_worker(hp, src, agent_home, port, key)
            if server.poll() is not None: raise RuntimeError('Owned vLLM process exited during verification')
            return result
        finally: terminate(server)


if __name__ == '__main__' and len(sys.argv) == 4 and sys.argv[1] == 'worker':
    worker(Path(sys.argv[2]), int(sys.argv[3]))
