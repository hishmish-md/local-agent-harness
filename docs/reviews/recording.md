# Recording and replay acceptance review

**Status: specification, not a test result.** Recording permission lets the harness observe a named target. It does not authorize replay or submission. This checklist qualifies the [recorder-to-skill handoff](../../handoffs/05-friend-neon.md).

## Test fixture

Use a disposable local form with a display name, password, user-marked private text field, delayed Ready indicator and Submit button. Open a second, excluded tab. Block external traffic. Give each sensitive input a distinct synthetic marker; never use real credentials. Instrument the capture boundary to count accepted events by target and the local submit handler to count effects without logging form contents. Reset counters and fixture state between cases.

| ID | Exercise | Pass condition |
| --- | --- | --- |
| C1 | Type before permission, decline the prompt, then start a new session and explicitly grant capture for the form tab and interaction events only. | No events accepted before grant. Prompt names target, data types, purpose and session end. While recording, a visible indicator identifies the target and offers Stop. No audio, screenshots or other tabs are captured. |
| C2 | Switch to the excluded tab and type; navigate the granted tab outside its approved origin. | No excluded events enter capture. Recording pauses on scope loss; returning does not silently resume. Expanding scope requires a new grant. |
| C3 | Stop while typing; type a distinct marker after Stop, then restart the harness. | Queued events cannot add post-stop input to the timeline. Restart is idle and cannot reuse the old grant. Previously saved steps remain available for review or deletion. |
| S1 | Type, paste and autofill synthetic markers into the password and marked-private fields. Force a validation error, save, reopen and export. | At the first recorder output, private inputs are named runtime references, not values or keystrokes. No marker appears in any event, preview, error, log, cache or export. Inspect any permitted image artifacts for visible markers as well. |
| S2 | Make field sensitivity unknown during input. During replay, leave a required secret reference unbound. | Recorder omits the uncertain value. Replay stops before filling or submitting; it never substitutes a recorded value or the placeholder text. |
| T1 | Record a name edit, a redundant click, a wait for Ready and a submit. Delete the click, change the wait timeout, then save and reopen. | The ordered timeline shows each action, target, editable arguments and confirmation point. Both edits survive reopening; the compiled preview omits the click and uses the new timeout. Editing causes no submission. |
| T2 | Move Submit before Ready or remove a required target. Attempt to save for execution. | Validation identifies the offending step and blocks replay until repaired. Editing cannot remove mandatory confirmation or widen scope. |
| R1 | Preview the edited timeline. Start replay on the disposable form, bind a synthetic secret locally and decline the final confirmation. | Preview dispatches no actions. Live replay waits for Ready and shows the exact destination and proposed submit without revealing secrets. Decline leaves the submit counter at zero. |
| R2 | Repeat R1 and confirm. Then start a second replay without confirming again. | First run increments the submit counter exactly once. The second run stops at a fresh confirmation; the counter does not change. |
| R3 | Independently try a wait timeout, duplicate matching controls, cancellation during the wait, and a destination change after confirmation but before dispatch. | Each run halts without submitting or executing later steps. No coordinate fallback, silent retry or reuse of stale approval. The reviewer sees the halted step and a redacted reason. |

**Release gate:** Pass every case on the same candidate revision. Record the revision, case ID, observed counters and outcome; mark unrun cases as untested. Keep raw recordings and generated binaries out of Git. Any captured secret, out-of-scope event or unconfirmed submit blocks release.
