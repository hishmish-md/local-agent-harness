# Sol handoff: employee controls and admin settings

Sol — the first walkthrough should answer one question: **if the adapter goes quiet after I press Stop, can I tell what happened and what is still unknown?** Build the smallest editable local concept that makes the answer clear. This is a test brief, not a passing test report.

Use ticket `F-SOL-01`. Follow [coordination](../../COORDINATION.md) and the [seat handoff](../../handoffs/04-friend-sol.md); wait for Astra’s acknowledgment and calibration before implementing in `workstreams/experience/`. Use synthetic text and a fake adapter until the contracts freeze. No Antigravity, publishing, hosted assets or real employee data.

## Screens to build

| Screen | What the reviewer can change or do | What they should see |
| --- | --- | --- |
| Employee chat | Start a synthetic run, type and revise a clarification reply, submit it once, pause, resume or stop. | Put run status and Stop outside the scrolling transcript. Distinguish waiting for a reply, waiting for pause acknowledgment, paused, stopping, stopped and status unknown. Keep an unsent reply when connectivity changes. |
| Admin settings (separate session) | Edit policy, context or pace. Preview old → new values and when the change takes effect; cancel, apply or undo. | Cancel writes nothing. Show the effective setting after apply. If someone changed it again, explain the conflict rather than overwriting it on undo. An expired or unauthorized session gets no protected settings. |
| Observation | In the authorized admin session, preview the consent copy and exercise the view-only state. | Off by default. When active, the employee sees an explicit indicator. The observer has no chat, dispatch or resume controls. |

Keep screen copy, fixture values and transitions in editable local source, not screenshots. Give reviewers a fixture selector outside the product UI: reset, disconnect, reconnect and settle the in-flight action. Seed one action in flight and another queued; expose their IDs and dispatch counts so a tester can distinguish a reassuring label from a real state change. Fake authorization demonstrates the interaction only; it is not a release security check.

## Acceptance scripts for the local prototype

Start each row from a reset fixture. Keep the network disconnected from the internet throughout; toggle the **fake adapter** independently of browser connectivity.

| Test | Exercise | Pass condition |
| --- | --- | --- |
| Cold start offline | Open the local concept in a fresh session with internet access disabled. | Screens, labels, fixtures and controls load without an external request. No login to a hosted service is needed. |
| Lost acknowledgment | Disconnect after requesting Stop but before acknowledgment. Reconnect with the fixture reporting stopped. | Immediately block new dispatches. While disconnected show that Stop is unconfirmed, not that the run finished. Reconcile to Stopped only on confirmation; discard queued work. A new run requires an explicit start. |
| Pause across reload | Pause with one action in flight; settle it, refresh, then explicitly resume. | Show the outstanding action until it settles. No second dispatch before Resume, including after reload; the completed action is not replayed. |
| Clarification offline | Type a reply, disconnect before submitting, attempt submission, then reconnect. | Draft survives. Show that it was not sent; reconnect does not send it. One explicit submission produces one reply. |
| Keyboard only | Without a mouse, use Tab and Shift+Tab to reach Stop, answer a clarification, open an admin preview, cancel with Escape, then apply and undo an edit. | Focus is visible in both directions. Buttons work with Enter or Space. A modal keeps focus inside while open and returns it to the opener. Stop stays reachable with a long transcript. |
| Screen reader and zoom | Repeat the keyboard path with a screen reader, then at 200% zoom. Trigger a disconnect while typing. | Controls have meaningful names. Status and errors are conveyed in words and announced once per transition, not per streamed token. Focus stays in the draft; no action is clipped or covered. |

Return the editable patch, synthetic fixture, exact local launch/test commands, and expected versus observed results per row. Mark unrun checks **not tested**. Ask friend Neon to review consent wording and owner-side Neon to review observer isolation. Use the [employee/admin release gates](../../docs/reviews/employee-admin.md) for service-level checks; a prototype pass does not establish authorization or isolation.
