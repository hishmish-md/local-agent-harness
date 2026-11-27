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
