# Friend tickets: Sol and Neon

Use the [one-paste Hermes setup](FRIEND-HERMES.md) by default. It prepares **both** claims. The rest of this page is an alternative for someone who chooses manual setup; it is not an additional onboarding step.

## Manual checkout (optional)

1. Clone `https://github.com/hishmish-md/local-agent-harness.git` into an unused directory, or reuse your own checkout after checking `git remote get-url origin`. Stop on a mismatch. Use your own account, not a fork.
2. In Git Bash, run `git fetch origin`, then `BASE=$(git rev-parse origin/main)` and `git show "$BASE:COORDINATION.md"`. Continue only if this is the four-seat agreement. Inspect `git worktree list --porcelain`, `git branch --list` and the intended sibling paths. Reuse a clean match on the expected branch and SHA. A clean matching tree that is strictly behind may fast-forward: inside it verify `git merge-base --is-ancestor HEAD "$BASE"` succeeds, then run `git merge --ff-only "$BASE"`. Preserve and report any ahead, diverged, dirty or conflicting tree; do not move or delete it.
3. Run the corresponding line **only for a missing seat whose branch and path are both unused**. No other tree is needed.

   ```bash
   git worktree add -b friend/sol-experience ../harness-sol "$BASE"
   git worktree add -b friend/neon-skills ../harness-neon "$BASE"
   ```

4. In each tree verify `git rev-parse --show-toplevel`, `git branch --show-current`, `git rev-parse HEAD` and `git status --short`. A successful checkout proves neither model availability nor collaborator write access. No model check-in or runtime change is needed to prepare claims.

## First-ticket briefs

- **Sol — `F-SOL-01`**: Work only in `workstreams/experience/`. Use a fake adapter to show status, clarification, pause and stop. Show that an employee cannot enable admin observation. Friend Neon reviews consent/stop behavior; owner Gemini Neon High reviews the observer boundary. [Full handoff](../handoffs/04-friend-sol.md).
- **Friend Neon — `F-NEON-01`**: Work only in `workstreams/skills/`. Build a synthetic consent-to-replay fixture with redaction, an editable wait, submit confirmation and no action after revocation. Friend Sol reviews the preview and independently tests revoke/crash. [Full handoff](../handoffs/05-friend-neon.md).

Send Astra one report with both claims: `ticket | seat | upstream/BASE | branch/root/HEAD/state | model evidence or unverified | paths | dependency | reviewer | acceptance check`. Wait for acknowledgment before editing. Neither peer dispatches the other. Keep local patches and reviews local; no push, PR or merge during setup. For later work, follow the [operating agreement](../COORDINATION.md).
