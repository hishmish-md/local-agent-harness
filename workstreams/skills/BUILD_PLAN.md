# BUILD_PLAN — Ticket F-NEON-01 (workstreams/skills/)

## Seat Claim & Constraints
- **Seat / Model:** Friend / Neon — Gemini 4 Neon (Medium), Hermes CLI (`antigravity-subscription-directsdk`)
- **Repo / Branch:** `hishmish-md/local-agent-harness` | `friend/neon-skills`
- **Baseline:** `d72ce46f98fba2681f96a0e3313b343e3be4e6b6`
- **Writable Path:** `C:/Users/parha/Documents/GitHub/harness-neon/workstreams/skills/` (only)
- **Dependencies:** Astra acknowledgment + sealed synthetic calibration (`COORDINATION.md`); Friend Sol (`workstreams/experience/`) consumes the edit/preview interface.
- **Reviewers:** Friend Sol (edit/preview interface & consent wording); Friend GPT-OSS (`workstreams/qualification/`, revoke & crash cases).
- **Hard Rules:** Synthetic fixtures and fake clock only; no Hydrogen children; no network calls; no pushes, merges, or edits outside `workstreams/skills/`.

## Acceptance Checks
1. No events or files recorded before explicit scoped consent (`refuse/pre-consent -> 0 events`).
2. Fake secret field redacted before persistence/compilation; zero secret occurrences in stored drafts, compiled skills, or preview output.
3. Compiled declarative skill supports editing a bounded wait to `30` seconds (no executable scripts).
4. Replay requires explicit confirmation before submission and uses `FakeClock` (deterministic, offline).
5. Revocation (including mid-recording or mid-wait) or crash stops immediately, discards unapproved drafts, and prevents automatic resume.
6. `pytest workstreams/skills/tests` passes with reproducible output; preview contract documented for Sol and revoke case packaged for GPT-OSS.

## Proposed Folder Structure
```text
workstreams/skills/
  README.md                  (pre-existing, untouched)
  BUILD_PLAN.md              (this plan)
  PROGRESS.md                (phase checkpoint ledger)
  src/
    clock.py                 (FakeClock, deterministic time)
    consent.py               (consent state machine)
    recorder.py              (consent-gated recorder + secret redactor)
    compiler.py              (recorder-to-editable declarative skill compiler)
    preview.py               (edit/preview interface for Friend Sol)
    replay.py                (confirmation-gated replay + revoke stop)
  fixtures/
    synthetic_form.py        (synthetic form steps + fake secret field)
  tests/
    test_consent_recorder.py (pre-consent, redaction, pause/resume, revoke)
    test_compiler_replay.py  (30s wait edit, preview API, confirm, revoke/crash)
```

## Modular File Map (<= 180 lines target, 220 hard cap)
- `src/clock.py`: `FakeClock` with `now()`, `advance(seconds)`, wait tracking.
- `src/consent.py`: `ConsentScope`, `ConsentState`, `ConsentMachine` (grant, pause, resume, stop, revoke, crash-reset).
- `src/recorder.py`: `SyntheticEvent`, `SecretRedactor`, `SkillRecorder` (blocks pre-consent, redacts secret fields, discards unapproved drafts on revoke/crash).
- `src/compiler.py`: `DeclarativeSkill`, `SkillStep`, `compile_draft()`, `edit_wait_seconds()` (bounded wait editing to 30s, versioned schema).
- `src/preview.py`: `PreviewPayload`, `build_preview()`, `apply_preview_edit()` (read/edit contract for Friend Sol).
- `src/replay.py`: `ReplayResult`, `ReplayEngine` (dry run, approval check, explicit submit confirmation, immediate halt on revocation during wait).
- `fixtures/synthetic_form.py`: Pure synthetic form fixture with one fake secret field and a configurable wait step.

## Phased Execution Route
- **Phase 0 — Workspace Inspection & Claim Gate**
  - Scope: Verify worktree/HEAD/lane, read coordination docs, author plan & ledger, reply with seat claim. Hold implementation until Astra ack + calibration.
  - Files: `workstreams/skills/BUILD_PLAN.md`, `workstreams/skills/PROGRESS.md`
  - Skills: `none`
  - Checks: `git status` clean outside `workstreams/skills/`; line counts <= 220.
- **Phase 1 — FakeClock, Consent Machine & Redacting Recorder** (blocked on Astra ack + calibration)
  - Scope: Implement deterministic clock, consent state machine, and consent-gated recorder with fake-secret redaction.
  - Files: `workstreams/skills/src/clock.py`, `workstreams/skills/src/consent.py`, `workstreams/skills/src/recorder.py`
  - Skills: `tdd-fail-to-pass-loop`, `boundary-parsing-strict-types`
  - Checks: `python -m py_compile workstreams/skills/src/clock.py workstreams/skills/src/consent.py workstreams/skills/src/recorder.py`; line counts <= 220.
- **Phase 2 — Declarative Compiler & Sol Preview Interface**
  - Scope: Implement recorder-to-skill compiler (30s wait edit) and Sol-facing edit/preview contract.
  - Files: `workstreams/skills/src/compiler.py`, `workstreams/skills/src/preview.py`
  - Skills: `invariant-contract-planning`
  - Checks: `python -m py_compile workstreams/skills/src/compiler.py workstreams/skills/src/preview.py`; line counts <= 220.
- **Phase 3 — Confirmation-Gated Replay & Synthetic Fixture**
  - Scope: Implement replay engine (confirmation before submit, revoke stop) and synthetic form fixture.
  - Files: `workstreams/skills/src/replay.py`, `workstreams/skills/fixtures/synthetic_form.py`
  - Skills: `tdd-fail-to-pass-loop`
  - Checks: `python -m py_compile workstreams/skills/src/replay.py workstreams/skills/fixtures/synthetic_form.py`; line counts <= 220.
- **Phase 4 — Automated Verification & Peer Handoff Evidence**
  - Scope: Add pytest suite covering all acceptance checks, Sol preview contract, and GPT-OSS revoke/crash case; record exact command and expected vs actual.
  - Files: `workstreams/skills/tests/test_consent_recorder.py`, `workstreams/skills/tests/test_compiler_replay.py`
  - Skills: `edge-matrix-and-mutation-checks`
  - Checks: `pytest -v workstreams/skills/tests`; secret scan on `workstreams/skills/`; line counts <= 220.

## Follow-up Subtask: F-NEON-01 / edited-skill-exporter
- **Source:** Issue #1 comment `IC_kwDOV-GZWM8AAAABrnaLNg` (receipt confirmed at `issuecomment-7222582609`).
- **Scope:** Local implementation only under `workstreams/skills/`. Build an offline exporter for an already-edited synthetic skill.
- **Constraints:**
  - Export redacted placeholders (`[REDACTED]`) instead of sensitive values.
  - Synthetic inputs only; no recording, replay, or network access.
  - Do not push. Astra owns all tests, review, verification, and signoff (do not add test suites or self-certify).
- **Modular File Map (<= 180 lines target, 220 hard cap):**
  - `workstreams/skills/src/exporter.py`: `EXPORT_SCHEMA_VERSION = "skill.export.v1"`, `ExportError`, `ExportedStep`, `ExportedSkill`, `export_edited_skill()`, `serialize_exported_skill()`, `write_exported_skill()`, and `build_synthetic_edited_skill()` (constructs an already-edited synthetic `DeclarativeSkill` directly without recording or replay).
- **Phased Route:**
  - **Phase 5 (Exporter Phase 0) — Receipt & Plan Gate:** Confirm receipt on issue #1, inspect existing `compiler.py`/`preview.py`, append plan & checkpoint to `BUILD_PLAN.md` and `PROGRESS.md`. Skills: `none`. Checks: line counts <= 220, `git status` clean outside `workstreams/skills/`.
  - **Phase 6 (Exporter Phase 1) — Offline Edited-Skill Exporter Implementation:** Implement `workstreams/skills/src/exporter.py` (offline JSON export with redacted placeholders, synthetic-only input, zero recording/replay/network imports). Skills: `boundary-parsing-strict-types`, `invariant-contract-planning`. Checks: `python -B -m py_compile workstreams/skills/src/exporter.py`, static import/network scan, `wc -l <= 220`, `git status` clean outside `workstreams/skills/`. (Testing/review/signoff owned by Astra.)

## Milestone Clarification v1: F-NEON-01 / edited-skill-exporter (source 7221971766)
- **Source:** Issue #1 comment `IC_kwDOV-GZWM8AAAABro_cXw` (reconciles existing commit `bdf259c` to Astra's v1 format contract; exporter only, NO importer).
- **Artifacts:**
  - `workstreams/skills/edited_skill_v1.md`: v1 format contract (`format="edited-skill"`, `version=1`, `wait` 0..60000 ms, `set_field` typed slot placeholders 1..64, bounds, rejection rules, API).
  - `workstreams/skills/fixtures/edited_skill_v1.json`: minimal redacted expected v1 fixture.
  - `workstreams/skills/edited_skill_export.py`: offline v1 exporter + `--demo` CLI entry point (validated before emission, generic error with no value echo, <= 64 KiB UTF-8, deterministic JSON).
- **Phased Route:**
  - **Phase 7 (Clarification v1 — Define Contract & Fixture):** Author `edited_skill_v1.md` and `fixtures/edited_skill_v1.json`; reconcile `DeclarativeSkill` mapping (reject unsupported ops/units rather than dropping). Skills: `none`. Checks: `python -m json.tool workstreams/skills/fixtures/edited_skill_v1.json`, `wc -l <= 220`, `git status` clean outside `workstreams/skills/`.
  - **Phase 8 (Clarification v1 — Implement Exporter & Local Handoff):** Implement `workstreams/skills/edited_skill_export.py` (<= 220 lines; split validator helper if needed), run `py_compile`, static network/import scan, `--demo` stdout check against fixture (without committing generated sample), commit locally, and prepare patch digest for private relay. Skills: `boundary-parsing-strict-types`, `invariant-contract-planning`. (Testing, review, verification, and signoff remain owned by Astra.)

## Follow-up Subtask: F-NEON-01 / skill-edit-history (source 7225609010)
- **Source:** Issue #1 comment `IC_kwDOV-GZWM8AAAABrq4LMg` (numeric ID `7225609010`; independent local task under `workstreams/skills/` only; baseline `a89a3e21e570dee556d98212324a6a5eae743824`; importer remains gated/unassigned).
- **Constraints:** Stdlib only, in-memory synthetic draft only; do not modify, invoke, or depend on exporter/importer code or artifacts; no file I/O, persistence, draft logging, recording, replay, execution, sleep, network, telemetry, push, or merge. Astra owns tests, review, verification, and signoff.
- **Artifacts:**
  - `workstreams/skills/skill_edit_history.md`: `history_v1` API, closed step/placeholder grammar (`wait` 0..60000 ms, inert `set_field` target `field` / value `text`|`number`|`boolean` slots 1..64), bounds (64 steps, 64 slots, 32 prior+future snapshots combined + 1 current, retained-step bound, oldest-undo eviction), no-op/reject preservation, branch invalidation, alias isolation, close reference-disposal semantics.
  - `workstreams/skills/skill_edit_history.py`: `history_v1` implementation + `--demo undo-redo` CLI (prints only fixed result codes and stack lengths; split helper module if needed to stay <= 220 lines).
- **Phased Route:**
  - **Phase 9 (Skill-Edit-History Phase 0 — Receipt & Plan Gate):** Post receipt `@astra F-NEON-01 RECEIVED skill-edit-history source=7225609010`, record local baseline SHA, append plan & ledger. Skills: `none`. Checks: `wc -l <= 220`, `git status` clean outside `workstreams/skills/`.
  - **Phase 10 (Skill-Edit-History Phase 1 — Contract Documentation):** Author `workstreams/skills/skill_edit_history.md` (<= 180 lines target, 220 cap). Skills: `invariant-contract-planning`. Checks: `wc -l <= 220`, `git status` clean outside `workstreams/skills/`.
  - **Phase 11 (Skill-Edit-History Phase 2 — Implementation, Static Checks & Local Handoff):** Implement `workstreams/skills/skill_edit_history.py` (<= 220 lines), run `py_compile`, static AST import/I/O/sleep scan, `--demo undo-redo` check, `wc -l <= 220`, local commit + scratch patch & SHA-256 digest (no push/merge; Astra owns testing/review/signoff). Skills: `boundary-parsing-strict-types`, `invariant-contract-planning`.

## Follow-up Subtask: F-NEON-01 / skill-draft-change-summary (source 7226109056)
- **Source:** Issue #1 comment `IC_kwDOV-GZWM8AAAABrrWsgA` (numeric ID `7226109056`; independent local task under `workstreams/skills/` only; baseline `3884672025b056694149ecac346bfd515479a4c6`; no dependency on history, exporter, or importer).
- **Constraints:** Pure in-memory function over two already-redacted synthetic snapshots; stdlib only; integer-only wait units (ms) preserving fractional seconds; bounded synthetic scope/revision tokens (never echoed); fixed path-free reason codes; zero mutation, storage, persistence, file/network I/O, recording, replay, wait execution, push, or merge. Astra owns tests, review, and signoff.
- **Artifacts:**
  - `workstreams/skills/skill_draft_change_summary.md`: closed versioned contract (`change_summary_v1`), allowed descriptors/fields, scope/revision pairing, integer ms bounds/overflow, fixed reason codes, demo expectations.
  - `workstreams/skills/skill_draft_change_summary.py`: pure comparison API + offline CLI (`--demo net-counts`, `--demo reorder`, `--demo invalid`, built-in fixtures only, <= 220 lines).
- **Phased Route:**
  - **Phase 12 (Change-Summary Phase 0 — Receipt & Plan Gate):** Post receipt `@astra F-NEON-01 RECEIVED skill-draft-change-summary source=7226109056`, record local baseline SHA, append plan & ledger. Skills: `none`. Checks: `wc -l <= 220`, `git status` clean outside `workstreams/skills/`.
  - **Phase 13 (Change-Summary Phase 1 — Contract Documentation):** Author `workstreams/skills/skill_draft_change_summary.md` (<= 180 lines target, 220 cap). Skills: `invariant-contract-planning`. Checks: `wc -l <= 220`, `git status` clean outside `workstreams/skills/`.
  - **Phase 14 (Change-Summary Phase 2 — Implementation, Static Checks & Local Handoff):** Implement `workstreams/skills/skill_draft_change_summary.py` (<= 220 lines), run `py_compile`, static AST scan, `--demo net-counts`, `--demo reorder`, `--demo invalid`, `wc -l <= 220`, local commit + scratch patch & SHA-256 digest (no push/merge; Astra owns testing/review/signoff). Skills: `boundary-parsing-strict-types`, `invariant-contract-planning`.
