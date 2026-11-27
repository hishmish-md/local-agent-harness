# Set up the friend PC with Hermes

Paste this entire block into your existing Hermes chat on the friend PC.

```text
Set up this PC for the three friend seats in https://github.com/hishmish-md/local-agent-harness.git. Do the Git and filesystem work yourself. I should only need to approve a choice or sign in through an official app if necessary, never type Git commands. You are setting up workspaces, not becoming a fourth seat or a second orchestrator. Astra coordinates the project.

1. Find the current user's project folder, existing checkout, Git executable (including Git bundled with an installed GitHub Desktop), and available model apps. Use supported local tools and my existing account sessions. Don't install software, change global settings, extract credentials or ask me to paste secrets. Public read access is enough. If sign-in is necessary, pause for my own account's normal sign-in flow. Never use the owner's accounts. Don't start cloud runtimes, buy credits, download models, send billable probes or enable paid fallbacks.

2. Reuse the checkout only after verifying its origin is the exact upstream above (an equivalent GitHub SSH URL is OK). If absent, clone into a new, unused local project directory. If the intended path is occupied by something else or the checkout choice is ambiguous, stop and ask. Fetch origin/main, record its full SHA as BASE and use that immutable commit for all three seats. Don't pull into a working branch or switch my checkout. Read COORDINATION.md, MODELS.md, docs/FRIEND-PROMPTS.md and the three friend handoffs at BASE. Use those seat prompts, not their manual setup steps.

3. Inspect git worktree list --porcelain, existing branches and the proposed sibling directories. Prepare these local worktrees from BASE using git worktree add -b only when both branch and path are unused:
   harness-sol  | friend/sol-experience      | Sol 6.2 medium | workstreams/experience/
   harness-neon | friend/neon-skills         | Neon           | workstreams/skills/
   harness-oss  | friend/oss-qualification   | gpt-oss-120b   | workstreams/qualification/
   On rerun, reuse an exact path/branch/BASE match after checking status. If a tree is dirty, has moved ahead, belongs to another checkout or conflicts with a branch or path, preserve it and report that lane blocked. Never reset, clean, stash, force, delete, prune or make duplicate branches. Verify each resulting worktree's actual root, branch, HEAD and status.

4. Prepare each matching seat prompt from docs/FRIEND-PROMPTS.md with BASE filled in and its absolute worktree path. Use an already supported project-opening integration if available; verify the visible project and model before claiming it is connected. Do not infer model access from a folder, send prompts that might incur charges, substitute models, or spawn helpers. If a desktop chat needs human input, give me its prepared prompt and folder. A hosted OSS chat does not have local file access by default: if there is no existing authorized no-cost connection, leave the worktree ready and mark the model connection unverified or blocked. Do not start Colab or mount Drive.

5. Stop before implementation, publication or any remote write. No push, fork, PR or merge. Return a compact table with the verified upstream and BASE, each seat's path/branch/HEAD, model connection evidence or blocker, and the next action. Give me the prepared claims or prompts to relay; don't claim Astra has received them. Wait for Astra's acknowledgment and the required calibration before editing any lane. Use only synthetic fixtures.
```
