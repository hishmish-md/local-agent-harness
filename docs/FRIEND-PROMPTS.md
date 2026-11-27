# Your first 15 minutes: one PC, three agents

Your job is to open three separate chats, give each one its prompt below, and send their replies to Astra (the project coordinator). You do not need to build the harness or manage your friend's PC. The models do not automatically see each other's chats.

## 1. Connect your PC once

1. Sign in to GitHub Desktop with **your own GitHub account**. Choose **File → Clone repository → URL**, enter `https://github.com/hishmish-md/local-agent-harness.git`, choose a local folder and click **Clone**. Do not fork. If already cloned, use **Fetch origin** instead.
2. From the clone, open Git Bash and run the four commands below. Use the printed commit as `BASE` in each prompt. The new folders are separate checkouts of the same repo, so one agent cannot accidentally switch another's branch. Run the three `worktree add` commands once, not before every session.

```bash
git fetch origin && git rev-parse origin/main
git worktree add -b friend/sol-experience ../harness-sol origin/main
git worktree add -b friend/neon-skills ../harness-neon origin/main
git worktree add -b friend/oss-qualification ../harness-oss origin/main
```

3. Open `harness-sol` in Sol and `harness-neon` in Neon. For GPT-OSS, use **your own** GPU/runtime and account; a hosted model cannot see your PC folders automatically. If using Colab without a connected coding worker, paste the public repo URL and BASE, supply only public repo text or synthetic fixtures, then review and apply its patch yourself in `harness-oss`. Never upload your home directory or mount a private Drive. If a model cannot access the repo, it should say so, not invent file contents.
4. Paste one block into each matching chat, replacing `BASE` with the hash. Send the three claim replies to Astra in the owner's chat for acknowledgment. **You can do this part now with read access.** If you need to push later, give the owner your GitHub username so they can invite you; accept the invitation using your own account. No one needs your password or token.

## 2. Copy one prompt per model

### Sol 6.2, medium reasoning → employee experience
```text
You are the Sol peer on hishmish-md/local-agent-harness, baseline BASE, ticket F-SOL-01. Read COORDINATION.md, handoffs/04-friend-sol.md and workstreams/experience/README.md. You own only workstreams/experience/. First reply with your model setting, actual baseline, writable path, dependency, reviewer, and acceptance check. Wait for Astra's acknowledgment and calibration before implementation. Then build the smallest local employee status/clarification/pause-stop flow using a fake adapter, separate from admin controls. Test that an employee cannot enable admin observation. Ask friend Neon to review consent wording and owner-side Neon to review isolation; coordinate through the human or ticket, not by spawning them. Use invented data only. Report changed files, exact test command, expected vs actual, and blockers. No network calls in the product, no push, no merge, no extra agents.
```

### Neon → recording and editable skills
```text
You are the friend-side Neon peer on hishmish-md/local-agent-harness, baseline BASE, ticket F-NEON-01. Read COORDINATION.md, handoffs/05-friend-neon.md and workstreams/skills/README.md. You own only workstreams/skills/. First reply with your actual model setting, baseline, writable path, dependency, reviewer and acceptance check. Wait for Astra's acknowledgment and calibration before implementation. Then build a synthetic consent-to-replay fixture: no recording before consent, redact one fake secret field, allow editing a wait to 30 seconds, require confirmation before submission, and stop on revocation. Use a fake clock, not a real employee recording. Give Sol the preview interface and friend GPT-OSS the revoke case for independent review. Report changed files, exact test command, expected vs actual, and blockers. No Hydrogen children on this seat, network calls in the product, pushes or merges.
```

### GPT-OSS-120B → independent tests
```text
You are the independent qualification peer on hishmish-md/local-agent-harness, baseline BASE, ticket F-OSS-01. Read COORDINATION.md, handoffs/06-friend-oss.md and workstreams/qualification/README.md. You own only workstreams/qualification/. First reply with actual model/runtime, baseline, writable path, dependency, reviewer and acceptance check; if files or tools are inaccessible, say exactly what you need. Wait for Astra's acknowledgment and calibration before implementation. Then design independent synthetic tests for a delayed button, two controls with identical names, and consent revoked during a wait. Define expected outcomes before reading implementation results. Require no action on ambiguity or after revocation. Report fixture seed, command, expected vs observed and blockers to Astra and the affected peer. Colab tests do not prove Windows isolation. If you cannot run a test, mark NOT RUN. No private data, nested agents, pushes or merges.
```

## 3. What to send back

Paste this for each seat: `ticket | seat/model | baseline | branch/path | reviewer | acceptance check | ready or blocked`. Astra will reconcile overlaps. If calibration fixtures or a reviewer aren't available, request them; do not self-certify. For handoff after work, include commit or patch, test command, actual output and risk. Do not edit outside the assigned folder; ask Astra for shared interface changes. No one pushes to main. After owner authorization and a collaborator invitation, the human can push only the reviewed ticket branch and open a pull request against main. A second person reproduces the test before integration.

Full rules: [coordination](../COORDINATION.md) · [seat guide](FRIEND-START.md) · [release gates](../README.md). GitHub and Colab are development tools only; the shipped harness must work offline.
