# Set up the friend PC with one paste

Paste this block once into your **existing Hermes** on the friend PC. Hermes handles Git and returns one report for Astra; you do not need to dispatch a prompt to each model.

```text
Prepare the two friend peer workspaces for https://github.com/hishmish-md/local-agent-harness.git: Sol 6.2 medium and friend Neon. Owner Astra coordinates the project; owner Gemini Neon High is the other owner-side seat. You are the setup assistant, not another seat. Do the local Git and filesystem steps yourself. Stop before implementation or any remote write.

1. Find the existing project checkout and Git (including Git bundled with GitHub Desktop). Verify origin identifies exactly hishmish-md/local-agent-harness on github.com (equivalent SSH is OK). If none exists, clone the named upstream into an unused directory. Stop on a mismatched origin, occupied target or ambiguous checkout. Read access suffices; do not infer write permission. Use only the friend's own account if interactive sign-in is necessary. Do not install software, change global settings, request secrets or enable paid services.

2. Fetch origin and record the full SHA from git rev-parse origin/main as BASE. Read COORDINATION.md, MODELS.md and the two current friend handoffs at BASE. If the baseline does not contain the four-seat agreement, report a stale/unpublished plan to Astra and stop; do not follow older prompts. Do not pull into, switch or reset anyone's checkout.

3. Inspect git worktree list --porcelain, existing branches and intended sibling directories. Prepare only these first-ticket worktrees at the immutable BASE:
   harness-sol  | friend/sol-experience | F-SOL-01  | workstreams/experience/ | handoffs/04-friend-sol.md
   harness-neon | friend/neon-skills    | F-NEON-01 | workstreams/skills/     | handoffs/05-friend-neon.md
   Reuse an exact clean root/branch/HEAD match. If the same registered root and branch are clean but behind BASE, verify git merge-base --is-ancestor HEAD <BASE> inside that tree; only on success fast-forward that tree with git merge --ff-only <BASE>. Recheck branch, HEAD and status. Use git worktree add -b <branch> <path> <BASE> only when both branch and path are unused. If the tree is dirty, ahead or diverged, the path/branch conflicts, or a check fails, preserve it, report that lane blocked and continue with the other peer. Leave every unrelated or retired worktree alone. Never clean, reset, stash, prune, delete, force or create duplicates.

4. Prepare each first claim from its handoff: actual worktree path, BASE, ticket, allowed files, reviewer, dependency and acceptance check. If a matching project/session is already open, use only visible evidence to report the model setting; otherwise say unverified or name the blocker. Do not send probes, switch models, start sessions or change runtimes. There is no third friend workspace to prepare. Do not send prompts to the models or ask me to relay two setup prompts.

5. Return one report that I can forward to Astra: upstream and BASE; for each peer, workspace (absolute root, branch, HEAD, clean/dirty or blocker), model (existing evidence or unverified), and the prepared claim. Say whether Astra's acknowledgment is pending; do not claim a message was delivered. Do not implement, push, fork, open a PR, merge or publish. Wait for Astra to acknowledge a ticket before work begins. Use only synthetic fixtures.
```
