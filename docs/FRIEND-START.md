# Start here: friend seats

You operate three **peer seats**, not a second team with its own orchestrator. Each seat claims one ticket and reports directly to its reviewer and Astra. Sol does not dispatch Neon or OSS. Do not spawn helpers or add a seventh seat. Astra owns shared contracts and integration.

| Peer | Provisional write area | First handoff |
|---|---|---|
| Sol 6.2 medium | `workstreams/experience/` | [Employee chat and admin UI](../handoffs/04-friend-sol.md) |
| Neon | `workstreams/skills/` | [Consent and editable skills](../handoffs/05-friend-neon.md) |
| gpt-oss-120b | `workstreams/qualification/` | [Independent synthetic checks](../handoffs/06-friend-oss.md) |

## Access and checkout

Use your own GitHub and model-provider accounts. For OSS, use your own Google account and a separate Colab session, not the owner's notebook runtime, Drive, tokens or quota. Never exchange cookies, passwords, API keys or notebook secrets. If a model, accelerator or repo permission is missing, report the blocker; don't borrow a login, substitute a model or fork the repo.

Clone the single upstream below. Read access is enough to start; if the clone is denied, ask the owner to confirm access for **your** GitHub username. Do not request admin access. From Git Bash:

```bash
git clone https://github.com/hishmish-md/local-agent-harness.git
cd local-agent-harness
git remote get-url origin
git rev-parse origin/main
```

Confirm the URL matches the clone URL and agree on the printed commit hash with Astra. Read [the operating agreement](../COORDINATION.md) and [model evidence requirements](../MODELS.md). Before critical work, complete the common sealed calibration: schema repair, delayed wait and consent-bug review; two seeds, 30-minute cap, blind independent scoring. Pass requires at least 8/10 and no invariant breach.

## Claim → branch → review

1. Send a claim to Astra and the affected peers: `ticket | seat | baseline hash | writable paths | dependency | independent reviewer | acceptance check`. Wait for acknowledgment that no other writer holds the lane. A branch alone is not a claim.
2. From the clone root, create one local worktree per accepted ticket. Example for Sol (replace the lane and ticket for other seats). Run this only while `origin/main` still matches the agreed hash; otherwise use the agreed hash instead of `origin/main`.

   ```bash
   git worktree add -b lane/experience/consent-smoke ../experience-consent-smoke origin/main
   cd ../experience-consent-smoke
   git status --short --branch
   ```

3. Test only with invented fixtures. Example consent smoke test: in a fake form labeled `DEMO-01`, decline recording, type `SYNTHETIC-ONLY`, then stop. Expected: zero recorded events and no saved draft. Have a second seat independently inspect the event count and storage. Until a runnable recorder exists, mark this **not run**, not passed. Never use employee screenshots, documents, credentials or production services, even for debugging.
4. Inspect your changes (`git status --short`, `git diff`); stage only the claimed paths, inspect `git diff --cached`, then commit locally. Send the reviewer the baseline, patch, changed paths, synthetic fixture provenance/seed, exact reproduction command, expected and observed results, blockers and next consumer. The reviewer reproduces the check and records pass/fail; send failures back to the lane owner. Shared contract changes go to Astra and need producer and consumer signoff.
5. **Stop at local review unless the owner explicitly authorizes upload.** No push, fork, publication or direct merge to `main` is needed for onboarding. If upstream collaboration is later approved, request collaborator write access only for the ticket branch/PR workflow; Astra handles integration after independent review. Never force-push or change repository permissions yourself.
