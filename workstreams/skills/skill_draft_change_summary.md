# Skill Draft Change Summary Contract (`change_summary_v1`)

Pure, in-memory count comparison for two already-redacted synthetic snapshots of the same skill draft under `workstreams/skills/` (ticket `F-NEON-01 / skill-draft-change-summary`, source `7226109056`, baseline `3884672025b056694149ecac346bfd515479a4c6`).

This feature is a **count comparison only** — not an edit log, identity check, or reconstruction of what changed. Zero deltas never imply "identical," "no edits," or "unchanged draft."

## 1. Unchanged Behaviors & Isolation
- All existing files under `workstreams/skills/` (`src/`, `edited_skill_export.py`, `edited_skill_v1.md`, `skill_edit_history.py`, `skill_edit_history.md`, `fixtures/`, `tests/`) remain untouched and independent.
- Stdlib only. No dependency on history, exporter, or importer; no file/network I/O, persistence, recording, replay, wait execution, or admin UI.

## 2. Closed Input Contract (`change_summary_v1`)
Both snapshots and their caller-supplied pairing are fully validated **before** returning any counts.

### Snapshot Mapping (exact keys)
- `version`: exact `str` `"change_summary_v1"`.
- `draft_scope`: synthetic bounded ASCII token (`str`, length `1..32`, chars `a-z`, `0-9`, `_`, `-`; never a real ID, never echoed in outputs or errors).
- `revision`: strict `int` (never `bool`) in `1..1000000`.
- `steps`: `list` or `tuple` of `0..64` redacted step descriptors.

### Allowed Step Descriptors (exact keys)
1. `wait`: exact keys `op` (`"wait"`), `ms` (strict `int`, never `bool`, in `0..60000`). Duration `ms` is required — missing `ms` is rejected, never assumed zero.
2. `set_field`: exact keys `op` (`"set_field"`), `target`, `value`.
   - `target`: exact keys `type` (`"field"`), `slot` (strict `int`, never `bool`, in `1..64`).
   - `value`: exact keys `type` (`"text"` | `"number"` | `"boolean"`), `slot` (strict `int`, never `bool`, in `1..64`).
   - Slot numbers are `1..64` (max `64` distinct slots per snapshot); a slot cannot be reused with a conflicting `type` within a snapshot.

### Caller-Supplied Pairing
`summarize_draft_change(before, after, *, expected_scope, expected_before_rev, expected_after_rev)`
- `expected_scope` must be a valid synthetic scope token matching both `before["draft_scope"]` and `after["draft_scope"]` (else `cross_draft`).
- `expected_before_rev` and `expected_after_rev` must be strict `int` in `1..1000000` with `expected_before_rev < expected_after_rev`.
- `before["revision"]` must equal `expected_before_rev` and `after["revision"]` must equal `expected_after_rev` (else `stale_revision`).

## 3. Units, Exact Arithmetic & Explicit Bounds
- **Wait unit:** exact integer milliseconds (`ms`), preserving fractional seconds (e.g. `1500 ms` = `1.5 s`, `3000 ms` = `3 s`, `5000 ms` = `5 s`). Never floats, rounding, or clamping.
- **Bounds:** `0..64` steps per snapshot; `0..60000 ms` per `wait` step; `0..300000 ms` (`5 min`) max total wait per snapshot (`wait_total_overflow` if exceeded).
- **Purity:** Counts every allowed step once; only `wait` steps add duration. Signed net deltas are `after - before`. Inputs are never mutated or stored; repeated calls return identical results.

## 4. Result Shape & Fixed Reason Codes
`ChangeSummaryResult(status, reason, unit, before_steps, after_steps, delta_steps, before_wait_ms, after_wait_ms, delta_wait_ms)`
- On success: `status="ok"`, `reason="ok"`, `unit="ms"`, and all six exact integers populated.
- On rejection: `status="rejected"`, `unit=None`, all six count/delta fields `None` (no partial counts, no raw errors, no echoed tokens or values).
- Fixed path-free `reason` allowlist: `ok`, `invalid_version`, `invalid_shape`, `invalid_scope`, `invalid_revision`, `cross_draft`, `stale_revision`, `step_limit_exceeded`, `invalid_step`, `missing_wait_duration`, `invalid_wait_duration`, `wait_total_overflow`, `invalid_placeholder`.

## 5. Offline Demo CLI & Expected Outputs
From repo root (built-in synthetic fixtures only):
- `python -B workstreams/skills/skill_draft_change_summary.py --demo net-counts`
  - `forward`: `before_steps=2 after_steps=3 delta_steps=+1 before_wait_ms=3000 after_wait_ms=5000 delta_wait_ms=+2000 unit=ms`
  - `reverse`: `before_steps=3 after_steps=2 delta_steps=-1 before_wait_ms=5000 after_wait_ms=3000 delta_wait_ms=-2000 unit=ms`
  - `empty`: `before_steps=0 after_steps=0 delta_steps=0 before_wait_ms=0 after_wait_ms=0 delta_wait_ms=0 unit=ms`
- `python -B workstreams/skills/skill_draft_change_summary.py --demo reorder`
  - `reordered`: `before_steps=2 after_steps=2 delta_steps=0 before_wait_ms=1500 after_wait_ms=1500 delta_wait_ms=0 unit=ms` (count comparison only)
- `python -B workstreams/skills/skill_draft_change_summary.py --demo invalid`
  - `stale_pair`: `status=rejected reason=stale_revision`
  - `missing_wait`: `status=rejected reason=missing_wait_duration`
  - `wait_overflow`: `status=rejected reason=wait_total_overflow`

Astra owns all tests, review, verification, and signoff.
