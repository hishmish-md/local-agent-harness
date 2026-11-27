# Coordination review: four seats, one repository

[Coordination](../../COORDINATION.md) names the four writers, their tickets and independent reviewers. Owner Astra coordinates; owner Gemini Neon High handles isolation and embedded inference on separate tickets. Friend Sol and friend Neon are peers. Reviewers report findings, not edits in another seat's lane.

## Claim before editing

1. Start from the baseline commit Astra identifies. Use the first-ticket branch named in onboarding or `lane/<lane>/<ticket>` for a new ticket, and one worktree per active ticket in the same repository. No forks or shared working directory.
2. Use the seat’s `handoffs/` note to prepare a claim: ticket, owner, reviewer, baseline SHA, writable paths, dependencies and an observable acceptance check. Tell Astra about the claim; a note on an isolated branch is not visible to peers by itself.
3. Astra compares proposed paths against active claims and acknowledges the scope before edits begin. Overlap includes renames, generated outputs and shared fixtures. If two claims overlap, split ownership by path or queue the dependent ticket. Read access is not a write claim.

## Conflicts and integration

If an unclaimed shared edit becomes necessary, stop at that file and request a scope change. For a breaking contract change, producer and consumer agree on the version and compatibility fixture before implementation. Do not resolve a collision by editing a peer’s branch. Astra integrates reviewed commits one at a time, reruns the affected checks on the combined tree and releases the claim after they pass. A clean Git merge is not evidence that contracts still agree.

## Handoff and recovery

At a checkpoint, send the next consumer the ticket, baseline and tip SHAs, changed paths, synthetic fixture provenance, exact test command and observed result, outstanding risks and next action. Distinguish **not run** from **passed**. The receiving seat acknowledges the handoff and reproduces the check before relying on it.

If a worker disconnects, pause its claim; silence does not transfer ownership. Astra records the last available commit and explicitly reassigns the claim to an existing seat. Resume in a fresh worktree from the verified checkpoint and rerun its check. If no checkpoint survived, identify the lost changes as unknown and restart from the baseline. A returning worker offers late changes for review rather than resuming a stale claim. If integration fails, stop dependent merges, revert the failed integration on the integration branch and return the ticket to its owner. Never force-push or reset a peer’s worktree.

## Scope of setup

Use synthetic fixtures only. Local setup does not authorize a push, publication, runtime change or model call. Keep existing worktrees intact. If the designated reviewer wrote the change, Astra routes it to a different active seat or holds the gate open.
