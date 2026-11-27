# Single-GPU Colab: gpt-oss for agent tool calls

> **Historical only.** Superseded by the four-seat plan; not an assignment or setup step. See the [archive index](../HISTORICAL.md).

**Pick `openai/gpt-oss-120b` at `b5c939de8f754692c1647ca79fbf85e8c1e70f8a`, native MXFP4 safetensors.** The pinned config declares MXFP4 expert weights; the shard index reports 65,248,815,744 tensor bytes, not total runtime VRAM.[1] Start here rather than adding a second quantization: OpenAI evaluated this model on tool use and reports single-80-GB operation.[5]

**Check the assigned GPU, not just the Colab tier.** Prefer H100 80 GB; vLLM marks H100 verified. Its recipe also gives an A100 80 GB command but lists a 96 GB minimum elsewhere, so treat A100 as conditional. A 96 GB card still needs a supported kernel.[2] Check `nvidia-smi` and `df -h` before downloading; don't reserve a paid runtime just to check. Start with one request and 8K total context to leave room for the KV cache. Suggested launch on an already-provisioned Linux GPU runtime with compatible vLLM installed (not executed here):

```bash
vllm serve openai/gpt-oss-120b \
  --revision b5c939de8f754692c1647ca79fbf85e8c1e70f8a \
  --host 127.0.0.1 --max-model-len 8192 --max-num-seqs 1 \
  --tool-call-parser openai --enable-auto-tool-choice
```

Use the model's Harmony parser, not a generic JSON prompt.[2] Before accepting a build, send a local `/v1/chat/completions` request with a mock `lookup_item(id: string)` tool. Require a structured call with valid arguments, return a made-up item name using its `tool_call_id`, and require that name in the final answer without another call. Also test an unrelated prompt that should not call the tool. Record GPU, driver, vLLM version and pass/fail before raising context or concurrency.

**Fine-tune challengers, not drop-in replacements:** `Salesforce/xLAM-2-32b-fc-r` targets multi-turn function calling and reports BFCL v3 and τ-bench; it is research-only (CC BY-NC 4.0).[3] `nex-agi/Qwen3-32B-Nex-N1` is an Apache-2.0 alternative for longer agent tasks; don't attribute the card's flagship DeepSeek scores to the 32B checkpoint.[4] Neither is a gpt-oss conversion. Compare with each model's own template/parser on the same tasks, scoring valid arguments, warranted abstention, completed tool round trips and latency. No head-to-head win or Colab runtime fit was measured here.

## Sources

[1] https://huggingface.co/openai/gpt-oss-120b/tree/b5c939de8f754692c1647ca79fbf85e8c1e70f8a
[2] https://raw.githubusercontent.com/vllm-project/recipes/main/models/openai/gpt-oss-120b.yaml
[3] https://huggingface.co/Salesforce/xLAM-2-32b-fc-r
[4] https://huggingface.co/nex-agi/Qwen3-32B-Nex-N1
[5] https://openai.com/index/introducing-gpt-oss
