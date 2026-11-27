# Variant B accessibility QA — Run ledger

**Fixed and verified:** Esc blocks the queue immediately. When acknowledgment is withheld, the page opens Simulation settings and focuses **Deliver acknowledgment**. It reports **Stop requested**, not **Stopped**, until acknowledgment arrives.

Tested `design/variant-b/index.html` directly from disk in headless Chrome 156.0.8078.80 on Windows, at 1280 × 800 CSS pixels. Used browser keyboard input without mouse clicks or scripted focus. Evidence below comes from the focused element (`document.activeElement`), rendered status and row labels, and Chrome’s accessibility tree. Screen-reader speech was not tested.

## Observed keyboard order and Stop paths

| Starting state | Keys and observed focus |
|---|---|
| Ready, settings collapsed | From a fresh load, Tab visits **Edit wait → Play sequence → Record → Simulation settings**. Stop is disabled and skipped. Opening settings adds **Withhold Stop acknowledgment** after the summary. |
| Editing the wait | Enter on Edit wait moves to **Wait duration (seconds)**. Tab → **Apply wait** → **Cancel**. Esc from Cancel closes the editor and restores **Edit wait**. |
| Recording | Starting Record leaves focus on **Finish recording**. Tab → **Capture sample click**; Space appends a sample and retains focus. Shift+Tab twice returns through **Finish recording** to **Stop**. Space on Stop changes the status to **Stop requested**. |
| Playing / Waiting | Enter on Play sequence puts focus directly on **Stop**, with no Tab needed. Focus stays there when the default three-second wait begins. Esc during the wait blocks the remaining rows (see below). |
| Clarification | Focus moves to **Editorial**; neither tray is checked. Shift+Tab reaches **Stop** in one press. Tab returns to Editorial; ↓ selects **Production**, then Tab reaches **Confirm and continue**. Esc there stops without confirming. With normal acknowledgment, **Stopped** returns focus to **Play sequence**. On a separate run, Enter on Confirm instead returned focus to **Stop**, then **Complete** returned it to **Play sequence**. |

## Before the fix: withheld acknowledgment lost focus behind collapsed settings

**Medium severity:** recovery was possible, but the next action was hidden during an unresolved Stop. The queue itself halted correctly.

1. From a fresh load, Tab four times to **Simulation settings**. Press Enter, Tab, Space to check **Withhold Stop acknowledgment**.
2. Shift+Tab, Enter to collapse settings without clearing the checkbox. Shift+Tab twice to **Play sequence** and press Enter.
3. When the status reads **Waiting**, press Esc. Do not reopen settings yet.

**Actual:** Status changed to **Stop requested** and focus became `BODY`. The message was “Queue blocked immediately. Final executor status is unconfirmed.” Four seconds later, past the original wait, the rows still read `Done / Blocked / Blocked / Blocked`. `#ack.hidden` was `false`, but `#ack.checkVisibility()` was `false`: its parent disclosure was closed. Chrome’s accessibility tree exposed **Simulation settings**, not **Deliver acknowledgment**. Reproduced again by pressing Esc during **Playing**. Leaving settings *open* was the control case: the same Esc put focus directly on the visible acknowledgment button.

**Verified workaround:** From the lost-focus state, Tab → **Simulation settings**, Enter to expand, Tab → **Withhold Stop acknowledgment**, Tab → **Deliver acknowledgment**, Enter. Status becomes **Stopped** and focus returns to **Play sequence**.

## After the fix: offline Chromium regression

Run `node design/qa/variant-b-stop-focus.cjs` from the repository root with Node, a locally available `playwright-core` (tested with 1.63.0), and installed Chrome. If the module is outside the normal search path, point `NODE_PATH` to its containing `node_modules`; for another installed Chromium executable, set `CHROMIUM_PATH`. The check opens the file directly with the browser context offline, sends keyboard input, and advances the page clock without changing focus or calling application handlers.

On Chromium **158.0.8127.37**, the same regression failed before the change with **`'BODY' !== 'ack'`** and passed after it:

| Stop path | Immediately after Esc during Waiting | Later result |
|---|---|---|
| Withheld, settings initially closed | **Stop requested**; executor status unconfirmed; rows `Done / Blocked / Blocked / Blocked`; Play disabled. **Deliver acknowledgment** is visible, exposed by button role and name, and focused. | After four simulated seconds, status, focus, and rows are unchanged. Enter acknowledges: **Stopped**, focus on enabled **Play sequence**. |
| Normal acknowledgment, settings closed | Same pending status and blocked rows; settings stays closed and no manual acknowledgment button is exposed. | The normal simulated acknowledgment at 850 ms changes the status to **Stopped** and restores focus to **Play sequence**. |
