# Edited-Skill Export Format v1 (`edited-skill`)

Offline, portable, redacted UTF-8 JSON export contract for an already-edited synthetic skill under `workstreams/skills/` (ticket `F-NEON-01 / edited-skill-exporter`, source `7221971766`).

This document defines the exporter contract only. Importer implementation is explicitly out of scope until Astra issues a separate importer assignment.

## 1. Envelope

A v1 document is a single UTF-8 JSON object with **exact** top-level keys:

- `format`: string literal `"edited-skill"`
- `version`: integer `1` (strictly `int`, never `bool` such as `true` or string `"1"`)
- `steps`: ordered JSON array of `0..64` step objects

Unknown or extra keys at any level are rejected.

## 2. Supported Operations (v1)

Only two operations are allowed in v1:

1. `wait`
   - Keys: `op` (`"wait"`), `ms` (strict integer in `0..60000`, never `bool` or `float`).
2. `set_field`
   - Keys: `op` (`"set_field"`), `target`, `value`.
   - `target`: placeholder object `{ "slot": N, "type": "field" }`.
   - `value`: placeholder object `{ "slot": N, "type": "text" | "number" | "boolean" }`.

### Placeholders & Structural Slot Assignment

- Every placeholder object has **exact** keys `slot` and `type`.
- `slot` is a strict integer in `1..64`.
- `type` is a single enum value: `"field"` for targets; `"text"`, `"number"`, or `"boolean"` for values.
- Slots are assigned monotonically (`1, 2, ...`) from synthetic structure alone — never derived from hashes of user values.
- A slot number cannot be reused with a conflicting placeholder type.
- No raw field names, literal values, original inputs, lookup tables, secret lengths, or reversible redaction tokens may appear in the exported document.

## 3. Mapping from Existing `DeclarativeSkill`

When exporting an in-memory `DeclarativeSkill` (`workstreams/skills/src/compiler.py`):

- `kind == "fill"` maps to `set_field` with a `field` target placeholder and a `text` value placeholder (ignoring and never serializing `target_id` or `value`).
- `kind == "wait"` maps to `wait` with `ms = round(wait_seconds * 1000)` **only** when `wait_seconds` represents an exact integer millisecond in `0..60000` (0.0s to 60.0s). Sub-millisecond waits or waits > 60s are rejected rather than truncated.
- Unsupported actions (`click`, `submit`, or any unknown kind) are **rejected** for v1 — never silently dropped or extended.
- Only already-edited skills (`version >= 2` when `require_edited=True`) are accepted.

## 4. Bounds & Rejection Rules

All checks run **before** emitting any bytes:

- Max UTF-8 serialized size: `65536` bytes (`64 KiB`).
- Max steps: `64`.
- Max distinct slots: `64`.
- Max container nesting depth: `4` (root object = 1, `steps` array = 2, step object = 3, placeholder object = 4).
- Max string token length: `32` characters; only declared keys and enum tokens are permitted.
- Reject unsupported versions, type mismatches, conflicting slot types, unknown keys/operations, external references, URLs, file paths, embedded scripts/commands, or executable payloads.
- Never resolve references or execute any operation during validation or export.
- On failure, raise a generic `InvalidEditedSkillFormatError("invalid edited-skill v1 format")` with **no partial output** and **no echo of rejected values** in exceptions, logs, or stderr.

## 5. Exporter API & Offline CLI

Module: `workstreams/skills/edited_skill_export.py` (stdlib only, no recording, replay, network, shell, plugin loading, or telemetry).

- `EXPORT_FORMAT = "edited-skill"`, `EXPORT_VERSION = 1`
- `InvalidEditedSkillFormatError(ValueError)` — generic error without echoing rejected values.
- `build_demo_edited_skill() -> DeclarativeSkill` — offline synthetic edited skill (one field edit + 500 ms wait).
- `export_edited_skill_v1(source, *, require_edited: bool = True) -> dict` — validates and returns the canonical v1 document dict (accepts a `DeclarativeSkill` or structured in-memory edited-skill dict).
- `serialize_edited_skill_v1(source, *, require_edited: bool = True) -> bytes` — validates, enforces `<= 64 KiB` UTF-8, and returns deterministic canonical UTF-8 JSON bytes (`sort_keys=True`, `indent=2`, trailing newline).

### Target Offline Reproduction (Astra runs)

```bash
python -B workstreams/skills/edited_skill_export.py --demo > edited_skill_sample.json
python -m json.tool edited_skill_sample.json
```

Expected minimal redacted fixture: `workstreams/skills/fixtures/edited_skill_v1.json`. Do not commit generated `edited_skill_sample.json`.
