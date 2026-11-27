# Coordination review: six workers, one repository

Astra, owner Neon Extra High, owner OSS, friend Sol, friend Neon and friend OSS are the six seats that may own development tickets. Astra is both a worker and the integration owner, not a seventh seat. Astra schedules the two other owner-side seats. If Neon Extra High delegates a bounded task to Hydrogen, Neon reviews the result and reports it to Astra; Hydrogen claims no separate ticket, branch or lane. The three friend-side seats accept or decline work as peers. No orchestrator, dispatcher or remote-control service runs on the friend’s machine.

## Claim before editing

1. Start from the baseline commit Astra identifies. Use one branch `lane/<lane>/<ticket>` and one worktree per active ticket in the same repository. No forks or shared working directory. If the repository has no commit yet, wait for Astra to establish the baseline.
2. Propose a claim in the seat’s existing `handoffs/` note: ticket, owner, reviewer, baseline SHA, writable paths, dependencies and an observable acceptance check. Tell Astra about the claim; a note on an isolated branch is not visible to peers by itself.
3. Astra compares proposed paths against active claims and acknowledges the scope before edits begin. Overlap includes renames, generated outputs and shared fixtures. If two claims overlap, split ownership by path or queue the dependent ticket. Read access is not a write claim.

## Conflicts and integration

If an unclaimed shared edit becomes necessary, stop at that file and request a scope change. For a breaking contract change, producer and consumer agree on the version and compatibility fixture before implementation. Do not resolve a collision by editing a peer’s branch. Astra integrates reviewed commits one at a time, reruns the affected checks on the combined tree and releases the claim after they pass. A clean Git merge is not evidence that contracts still agree.

## Handoff and recovery

At a checkpoint, send the next consumer the ticket, baseline and tip SHAs, changed paths, synthetic fixture provenance, exact test command and observed result, outstanding risks and next action. Distinguish **not run** from **passed**. The receiving seat acknowledges the handoff and reproduces the check before relying on it.

If a worker disconnects, pause its claim; silence does not transfer ownership. Astra records the last available commit and explicitly reassigns the claim to an existing seat. Resume in a fresh worktree from the verified checkpoint and rerun its check. If no checkpoint survived, identify the lost changes as unknown and restart from the baseline. A returning worker offers late changes for review rather than resuming a stale claim. If integration fails, stop dependent merges, revert the failed integration on the integration branch and return the ticket to its owner. Never force-push or reset a peer’s worktree.

## Colab boundary

Use separate owner and friend Colab sessions and credentials. Only generated synthetic inputs, fixtures and derived synthetic test results belong there. Do not upload real or anonymized user records, local logs, home-directory snapshots or secrets. If provenance is uncertain, keep the artifact out of Colab and generate a replacement fixture. Colab is optional development infrastructure, not a product runtime or coordination dependency. No remote, upload or publication is authorized by this planning document.
