# experience

Accountable seat: Friend / Sol 6.2 medium. First deliverable and dependency: [handoff](../../handoffs/04-friend-sol.md). Keep lane code, tests and evidence here; avoid secrets, weights, recordings and generated binaries in Git.

## F-SOL-01 local demo

From the repository root:

- Demo: `python -B workstreams/experience/experience.py`
- Tests: `python -B -m unittest discover -s workstreams/experience -v`

Try `answer Cedar`, `tick`, `pause`, `tick`, `status`, `resume`, `tick`, `stop`. Each `tick` either starts or settles one fake action. Stop discards the queued work; a prior dispatch may still settle. Restart the demo for a new run. No network, persistence, or real tool calls are used.

The employee CLI never receives the admin session. The separate admin request handler accepts an opaque, in-process capability provisioned by the trusted demo harness. The employee can grant or revoke per-run permission, but cannot switch on observation. Once enabled by admin, observation shows only the run state; it cannot see the clarification answer or control the run. These are demo request-level checks, not a security boundary against Python code in the same process. Production authentication, admin UI, and OS isolation are not implemented here.

Review requested: friend Neon for the consent wording in `OBSERVATION_CONSENT`; owner-side Neon for the employee/admin boundary and read-only observer. Production release gates are not signed off by this demo.
