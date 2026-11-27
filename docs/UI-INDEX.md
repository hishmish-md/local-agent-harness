# Desktop UI concepts

Compare the dark boards below with [Run ledger](../design/variant-b/index.html), an offline, interactive second concept. Open the HTML from your clone to try recording, edit a wait, resolve an ambiguous target, or stop during playback. Use the [reference checklist](../design/variant-b/REVIEW.md) to compare both designs; neither is the production application.

Open the [preview](../design/prototypes/preview.html) locally with the three SVGs beside it. On GitHub, open a board directly:

- [Employee](../design/prototypes/employee.svg): clarification, progress, Stop requested, and Stop acknowledged.
- [Admin](../design/prototypes/admin.svg): local runtime settings and an isolated draft preview.
- [Record and replay](../design/prototypes/record-replay.svg): recording scope, consent, and sequence review.

The [handoff](../design/prototypes/HANDOFF.md) has walkthroughs and acceptance criteria, not test results.

## UI → integration contract

| Control | Required integration behavior |
| --- | --- |
| Pause a task | Block new dispatches; an in-flight action may settle. Preserve the queue across reload. Resume only on explicit request; never repeat a completed action. |
| Stop a task | Block new dispatches immediately and discard queued work. Show **Stop requested** until the adapter confirms. If contact is lost, show **unconfirmed**, not **Stopped**. A stopped run cannot resume; starting again requires a new run. |
| Pause / Stop recording | Pause suspends capture within the consented session. Stop ends capture and leaves the sequence for review; it does not authorize replay. Revocation ends capture immediately and requires fresh consent before recording again. |
| Admin settings and consent | These boards use synthetic examples. No control grants OS permissions, starts capture, dispatches work, or changes runtime settings. A real integration must enforce authorization and consent independently of the UI. |
