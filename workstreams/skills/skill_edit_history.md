# Skill Edit History Contract (`history_v1`)

In-memory undo/redo editor state for an open, already-edited synthetic skill draft under `workstreams/skills/` (ticket `F-NEON-01 / skill-edit-history`, source `7225609010`, baseline `a89a3e21e570dee556d98212324a6a5eae743824`).

This feature is **editor state only**: it is not recording, replay, execution, import, or export. It uses only the Python standard library and has zero dependency on exporter/importer code or artifacts.

## 1. Unchanged Behaviors
- Existing modules under `workstreams/skills/src/`, `workstreams/skills/edited_skill_export.py`, `workstreams/skills/edited_skill_v1.md`, `workstreams/skills/fixtures/`, and `workstreams/skills/tests/` remain untouched and independent.
- Importer remains gated and unassigned.

## 2. Version & Normalized Draft Grammar (`history_v1`)
A draft is a closed, fixed-shape mapping validated **before** retaining or mutating any state:
- Top-level keys (exact): `version` (`"history_v1"`), `steps` (ordered `list` or `tuple` of `0..64` step mappings).
- Only two step operations are allowed:
  1. `wait`: exact keys `op` (`"wait"`) and `ms` (strict `int`, never `bool`, in `0..60000`). Inert descriptor — never sleeps.
  2. `set_field`: exact keys `op` (`"set_field"`), `target`, `value`.
     - `target`: exact keys `type` (`"field"`) and `slot` (strict `int`, never `bool`, in `1..64`).
     - `value`: exact keys `type` (`"text"` | `"number"` | `"boolean"`) and `slot` (strict `int`, never `bool`, in `1..64`).
- **Slot rules:** Slot numbers are strict integers `1..64`, never keyed by original data. A slot number cannot be reused with a conflicting placeholder `type` within the same draft.
- **Strict rejection:** Reject unsupported versions, unknown keys or step types, booleans passed as integers, literal field names, raw strings, user values, live handles, callbacks, arbitrary objects, unbounded strings, and extra nested containers. Never log, retain, or convert unsafe drafts; generic errors never echo rejected values.

## 3. Bounds, Eviction & Alias Isolation
- **Max steps per draft:** `64`.
- **Max distinct slots per draft:** `64`.
- **Max combined history stack:** `32` prior (`undo`) + future (`redo`) snapshots **combined**, plus `1` `current` snapshot (`33` total snapshots max per open history).
- **Retained-step bound:** At most `33 * 64 = 2,112` normalized step descriptors retained per open history (`2,048` across undo/redo stacks + `64` in current).
- **Eviction policy:** On a valid, materially changed edit, `redo` is cleared first; if `len(undo) >= 32`, the oldest undo entry (`undo[0]`) is evicted **before** pushing the prior `current` snapshot so `len(undo) + len(redo)` never exceeds `32`.
- **Alias isolation:** Validated drafts are converted into deeply immutable internal tuples of frozen descriptors. `inspect()` returns a fresh unaliased dict/list copy each time, so caller mutations cannot alter retained snapshots. Each `open_history()` handle is completely isolated from all other open handles.

## 4. `history_v1` API & State Semantics
Module: `workstreams/skills/skill_edit_history.py` (stdlib only).

- `HISTORY_VERSION = "history_v1"`, `MAX_STEPS = 64`, `MAX_SLOTS = 64`, `MAX_HISTORY_SNAPSHOTS = 32`, `MAX_RETAINED_STEPS = 2112`.
- `HistoryValidationError(ValueError)` — generic validation error with no rejected-value echo.
- `HistoryResult(status, undo_count, redo_count, is_open)` — frozen result with fixed `status` codes: `opened`, `applied`, `noop`, `rejected`, `undone`, `redone`, `empty_undo`, `empty_redo`, `closed`.
- `HistoryView(status, is_open, undo_count, redo_count, current)` — frozen read-only inspection view.
- `open_history(initial_draft) -> SkillEditHistory`: validates `initial_draft` (raises `HistoryValidationError` on invalid input), sets baseline `current`, and starts with empty `undo` and `redo` stacks.
- `history.apply_edit(draft) -> HistoryResult`:
  - Closed handle -> `status="closed"` (no mutation).
  - Invalid draft -> `status="rejected"` (mutates neither stack; preserves `redo` branch).
  - Normalized draft equal to `current` -> `status="noop"` (mutates neither stack; preserves `redo` branch).
  - Materially changed valid draft -> clears `redo`, evicts oldest `undo` if at cap `32`, pushes prior `current` to `undo`, updates `current`, returns `status="applied"`.
- `history.undo() -> HistoryResult`: if closed -> `closed`; if `undo` empty -> `empty_undo`; otherwise moves `current` to `redo`, restores newest `undo` to `current`, returns `undone`.
- `history.redo() -> HistoryResult`: if closed -> `closed`; if `redo` empty -> `empty_redo`; otherwise moves `current` to `undo`, restores newest `redo` snapshot verbatim (without re-executing edits), returns `redone`.
- `history.inspect() -> HistoryView`: read-only; creates no history entries. When open, returns `status="open"`, stack counts, and a fresh unaliased dict copy of `current`. When closed, returns `status="closed"`, `is_open=False`, `0/0`, `current=None`.
- `history.close() -> HistoryResult`: discards `current`, `undo`, and `redo`, marks handle closed, returns `status="closed"`.

## 5. Close Semantics & Reference Disposal
- Once `close()` is called, the handle cannot restore or reveal prior snapshots; all subsequent `apply_edit`, `undo`, `redo`, and `inspect` calls return `status="closed"` with `0/0` counts and `current=None`.
- Opening a new draft via `open_history(...)` creates a fresh handle with empty stacks.
- **Accurate disposal note:** `close()` clears internal lists and drops Python object references so they become eligible for garbage collection; it does **not** claim cryptographic or secure erasure of runtime process memory.

## 6. Privacy, Non-Goals & Offline Demo
- **Forbidden:** File I/O, persistence, profile caches, draft logging, recording, replay, execution, `time.sleep`, exporter/importer imports, network calls, telemetry, or third-party dependencies.
- **Intended offline demo (from repo root):**
```bash
python -B workstreams/skills/skill_edit_history.py --demo undo-redo
```
- Runs the synthetic in-memory sequence (`wait 100 -> 250 -> 500 -> undo -> redo -> undo -> rejected negative wait -> edit 750 -> redo empty -> undo -> close`) and prints **only** fixed result codes and stack lengths.
- **Verification ownership:** Astra owns all tests, review, verification, and signoff.
