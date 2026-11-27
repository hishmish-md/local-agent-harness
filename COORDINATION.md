# Four-seat operating agreement

Astra is the main coordinator and integration owner. Owner Gemini Neon High works with Astra on the owner PC. Friend Sol and friend Neon are peers: each accepts or declines its own ticket and reports to Astra and its reviewer. Neither dispatches the other. Hermes on the friend PC prepares workspaces; it is not a seat. Only these four seats take tickets. If a seat is unavailable, pause its ticket or have Astra explicitly reassign it to another existing seat. Do not spawn helpers or substitute models.

## Assignments and review routing

| Ticket / writable lane | Writer | Independent review and next consumer |
|---|---|---|
| `O-ASTRA-01` · `workstreams/integration/` | [Owner Astra](handoffs/01-astra.md) | Friend Sol reviews the contract against the employee flow; producers and consumers sign off on breaking changes. |
| `O-NEON-01` · `workstreams/isolation/` | [Owner Gemini Neon High](handoffs/02-own-neon.md) | Astra checks denial and non-interference evidence. Give synthetic snapshots to both friend peers. |
| `F-SOL-01` · `workstreams/experience/` | [Friend Sol](handoffs/04-friend-sol.md) | Friend Neon reviews consent and stop behavior; owner Gemini Neon High checks the observer boundary. |
| `F-NEON-01` · `workstreams/skills/` | [Friend Neon](handoffs/05-friend-neon.md) | Friend Sol reviews the preview and independently tests revoke and crash; give failures to friend Neon and Astra. |
| `O-NEON-02` · `workstreams/inference/` | Owner Gemini Neon High, follow-up | Astra checks the embedded-runtime contract; friend Sol reproduces on the reference PC when available. |
| `F-SOL-02` · `workstreams/qualification/` | Friend Sol, follow-up | Friend Neon reviews synthetic oracles and reproductions. For gates covering Sol’s own implementation, friend Neon runs the check independently; for gates covering friend Neon’s implementation, Astra reviews Sol’s evidence. |

Follow-ups are separate tickets, not extra seats or additions to the first ticket's scope. Astra queues them until the first ticket is handed off. A reviewer reports findings rather than writing in the author's lane. No one signs off their own implementation, test artifact or integration change. If no independent reviewer is available, the gate stays open.

## Claim, review, integrate

1. Use one shared upstream, no forks. Claim `ticket | seat | baseline SHA | writable paths | dependencies | reviewer | acceptance check`. Astra acknowledges scope before edits. One writer and one worktree per active ticket. First friend branches are `friend/sol-experience` and `friend/neon-skills`; use `lane/<lane>/<ticket>` for new tickets. Preserve existing worktrees, including inactive ones.
2. At handoff send the baseline and tip or patch, changed paths, synthetic fixture provenance, test command, expected and observed results, blockers and next consumer. Mark unexecuted checks **not run**. For a breaking schema change, agree on a version with producer and consumer and land compatibility fixtures first.
3. An independent reviewer reproduces the relevant check; Astra integrates reviewed changes and reruns affected checks. Revert a failed integration on the integration branch rather than modifying a peer's checkout. No force-push. Onboarding is local: no pushes, PRs, account or remote runtime changes. Publication requires separate owner approval.
