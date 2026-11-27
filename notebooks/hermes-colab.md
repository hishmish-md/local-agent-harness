# One supervised Hermes tool call inside the notebook

`hermes_colab.py` runs **one fixed synthetic exercise**, from a notebook cell, using the same pinned Hermes `AIAgent` engine as the local worker. It does not clone the desktop identity, prompt files, credentials, tools, projects or history. It starts a temporary authenticated vLLM listener only on runtime loopback, runs one local client, and stops both. There is no external worker queue or route from Windows. Do **not** run the older `gpt-oss-120b.ipynb` first: that is a separate 8,192-token API demo with different storage requirements.

## Before running any cells

- Use only a private, interactive notebook on your own account where ordinary notebook execution and this workload are permitted. For a school account, check with the school administrator about access and required parent/guardian consent. Google's built-in Colab AI features are 18+; this exercise neither calls nor unlocks them. If the account or workload is restricted, **stop and use the offline tests**. Do not borrow an account, change age information, or work around a restriction.[1][2]
- Only proceed if the runtime is **already attached**, the designated project GPU and local storage are already available, and using them will incur **no charge or paid compute-unit use**. The program cannot check your billing or eligibility. Do not connect to a new runtime to run these checks. No purchases, remote control, proxies, tunnels, Drive mounts, keep-alives, distributed jobs or alternative UIs. Stay in the notebook and run the cell manually. Google restricts unrelated web serving, proxies and certain remote/distributed use.[1][2]
- Trust the image, pre-staged packages and notebook. Do not share this runtime, attach personal storage, set notebook secrets, run third-party cells or use real documents. Loopback authentication is **not** isolation from other code running as the same OS user.

## Required local assets

The bootstrap makes **no installer, model download or provisioning calls**. On an eligible image the operator must already have the following under the runtime's ordinary, disposable `/content` filesystem (not a mount, symlink to another volume or Drive):

```
/content/hermes_colab.py                     reviewed copy of the sibling script
/content/synthetic-assets/
  hermes-agent/                              clean public-source Git checkout, including .git
  hermes-env/bin/python                      separate Linux CPython 3.14 environment for Hermes
  vllm-env/bin/{python,vllm}                 separate trusted project vLLM 0.15.1 environment
  snapshots/b5c939de8f754692c1647ca79fbf85e8c1e70f8a/   pinned native MXFP4 snapshot, standalone
  encodings/{cl100k_base,o200k_base}.tiktoken
```

The Hermes checkout must be exactly `caafe5389ae585ef77387a962aee05b1bcf17029` (local reference release `v0.23.3`), with no `.env`. Have an approved **Linux** dependency cache for its `uv.lock` and a trusted CPython 3.14 interpreter; don't copy a Windows venv or a live Hermes profile. If preparing the Hermes environment in the already-eligible image from that offline cache, the following is the command (not run by the launcher). `--no-install-project` installs locked dependencies only; the worker imports the verified source tree explicitly. Do not drop `--offline` or purchase capacity if something is missing.

```bash
cd /content/synthetic-assets/hermes-agent && \
  UV_PROJECT_ENVIRONMENT=/content/synthetic-assets/hermes-env \
  uv sync --locked --offline --no-python-downloads --no-dev --no-install-project --python 3.14
```

The snapshot verification streams all required safetensors, tokenizer, config and template bytes and compares the combined manifest with the pinned Hub tree. It separately checks both Harmony vocabularies.[7][8] This can take time; allow room for weights, both environments and compilation caches. Use an already available single RTX PRO 6000 Blackwell with at least 90,000 MiB total and 88,000 MiB free as in the project hardware gate. Passing this gate is **not** evidence that vLLM can serve the requested window on that GPU/driver/wheel combination.

## Executable notebook cell

Review the local script first. No login tokens or keys are input parameters. Run this in a normal **Python cell**, not a terminal, scheduler, or remote agent:

```python
from importlib.util import module_from_spec, spec_from_file_location
spec = spec_from_file_location('hermes_colab', '/content/hermes_colab.py')
bootstrap = module_from_spec(spec)
spec.loader.exec_module(bootstrap)
bootstrap.run_notebook()
```

The operator confirms eligibility and cost before the live path reads the assets or starts a process. An error is a **blocker**, not permission to resize the runtime, weaken the checks or substitute a hosted model. The only success result is `verified lookup` after the real worker has made exactly one `lookup_item({"id":"A17"})` call and returned the previously unseen synthetic answer. There is no user-controlled prompt or general-purpose tool. The worker has an empty temporary home, receives the random key through a pipe, checks its effective tool set/route, and disallows non-endpoint Python connections and subprocess launches. This tripwire is not a native-code sandbox. The server has a separate home/env and uses local weights/encodings. No model or credential output is displayed. On exit or ordinary cell interruption, process groups are terminated and temporary homes removed. A hard kernel/VM crash cannot execute `finally`; use Colab's UI to **disconnect and delete the runtime** after use, including after a crash. Staged assets are not deleted on ordinary return.

### Why this is not the 8K notebook

Official Hermes docs specify a **64,000-token** floor for normal tool-using agents; the pinned source defines that exact integer and enforces it for the custom vLLM provider. The explicit small-window LM Studio exception does not apply here.[3][4][5] This launcher requests **64,000 total, one sequence, at most 1,024 generated tokens per call**, checks unauthenticated denial, checks the authenticated model's exact `max_model_len`, and checks Hermes's own resolved window without overriding it. vLLM 0.15.1 derives that model-card field from its loaded model config.[6] This verifies an advertised runtime window, not a 64K-long inference benchmark. The worker checks a genuine tool round trip separately.

## Offline checks (no Colab, GPU, inference model, or paid provider)

From the harness repo: `python -B -m unittest discover -s tests -v`. The optional actual-core test is explicitly **skipped**, not passed, when `SYNTHETIC_HERMES_SRC` is not set. For that test, run from an interpreter with the matching Hermes dependencies and set `SYNTHETIC_HERMES_SRC` to the clean pinned checkout. Example in bash:

```bash
SYNTHETIC_HERMES_SRC=/path/to/pinned/hermes-agent python -B -m unittest discover -s tests -v
```

The deterministic fixture is an in-memory HTTP server on loopback; **it is not gpt-oss or vLLM**. It records the real worker's two requests and sole offered tool. Passing this test proves the pinned Hermes agent can execute the tool and consume its result, not that Linux GPU startup, real model behavior, allocation, or account eligibility were tested.

## Sources

[1] https://research.google.com/colaboratory/faq.html
[2] https://research.google.com/colaboratory/tos_v6.html
[3] https://hermes-agent.nousresearch.com/docs/integrations/providers
[4] https://raw.githubusercontent.com/NousResearch/hermes-agent/caafe5389ae585ef77387a962aee05b1bcf17029/agent/model_metadata.py
[5] https://raw.githubusercontent.com/NousResearch/hermes-agent/caafe5389ae585ef77387a962aee05b1bcf17029/agent/agent_init.py
[6] https://raw.githubusercontent.com/vllm-project/vllm/v0.15.1/vllm/entrypoints/openai/models/serving.py
[7] https://huggingface.co/api/models/openai/gpt-oss-120b/tree/b5c939de8f754692c1647ca79fbf85e8c1e70f8a
[8] https://raw.githubusercontent.com/openai/harmony/main/src/tiktoken_ext/public_encodings.rs
