# Windows isolation: feasibility and release gate

**Decision:** Qualify a disconnected, disposable guest first. Run both the headless browser and the native fixture driver inside it, with its viewer closed. The host should need neither a foreground window nor an input-injection helper. This is a design review, not a passing test report; no backend is qualified here. See the [isolation handoff](../../handoffs/02-own-neon.md).

| Option | What it separates | Decision |
|---|---|---|
| Task View virtual desktop | A different arrangement of windows for the same user | Not a worker session. Do not switch the user's workspace. |
| Alternate Win32 desktop | Window objects and messages. Only one desktop on the interactive window station receives physical input at a time.[1] | A candidate for a specific app with a cooperative API, not a general click/type backend. Never call `SwitchDesktop` to make an action succeed. |
| Separate interactive logon session | An RDS session has its own session ID and interactive window station.[2] | Feasible on a suitably configured host with an in-session worker. Do not assume simultaneous interactive sessions on a consumer PC. Session loss must cancel the action, not redirect it to the console. Not qualified. |
| Disposable guest | Independent worker OS, browser and fixture app | Preferred. Require no external network adapter, shared clipboard, host mounts, device redirection or saved credentials. If those conditions cannot be verified, refuse to start. |

## Browser scope

Headless Chrome does not display its platform windows.[4] A fresh Playwright context separates cookies and web storage between runs.[3] Neither property enforces offline operation or limits filesystem access. Use a guest-local fixture origin, an ephemeral profile and a private browser-control pipe. Target a named field in the approved page and read its value back. Never attach to the user's browser or substitute system keystrokes. Destroy the guest after success, timeout or crash. Native pickers, credential prompts, UAC and secure desktops are out of scope; a blocked action is an expected result, not a reason to switch input methods.

## Qualification: prove delivery and non-interference together

Run these checks with synthetic data and an operator on a test host. Use a test editor, not the operator's actual documents. Start observation before the guest launches; stop only after teardown.

1. **Calibrate the observer.** Subscribe to foreground-window and focused-control changes on the host. Deliberately focus a second fixture window, then return to the editor. Require both transitions to be observed; before/after snapshots alone miss a brief focus steal. Clear calibration events before the run.
2. **Exercise both paths.** Keep the host editor focused while the operator types `HOST-ONLY` and leaves the pointer stationary. From inside the guest, fill one approved browser field with `WEB-ONLY`; repeat against an approved native fixture control with `APP-ONLY`. Read back each target independently. Require exact values, unchanged sibling fields, host editor text exactly `HOST-ONLY`, no unexpected host focus or pointer changes, and no host marker in either guest target.
3. **Exercise denial paths.** Repeat with a stale target, revoked approval, an unexpected modal, and guest termination immediately before dispatch. Require a denial or explicit unknown outcome if delivery raced with termination. No replay, host fallback, clipboard paste or second mutation. If the host observer stops, mark the run inconclusive, not passed.
4. **Verify containment and reset.** Confirm guest policy rejects outbound traffic and host shares without contacting a public service. Seed browser storage with a synthetic nonce; a fresh guest on the same fixture origin must not see it. Verify the previous worker and profile are gone. A clean profile alone does not prove focus isolation.

Record host/guest builds, driver/browser versions, fixture revision, action IDs, expected and observed markers, focus-event counts and teardown status. Export only fixture-scoped, redacted accessibility results; omit host window titles, raw keystrokes and screenshots. Owner/Neon supplies evidence; Astra reviews denial paths before any support claim. A pass qualifies only the tested configuration, not locked or disconnected sessions, arbitrary apps, or unattended access to the user's desktop.

## Sources

[1] https://learn.microsoft.com/en-us/windows/win32/winstation/desktops
[2] https://learn.microsoft.com/en-us/windows/win32/termserv/terminal-services-sessions
[3] https://playwright.dev/docs/browser-contexts
[4] https://developer.chrome.com/docs/automation-and-testing/headless
