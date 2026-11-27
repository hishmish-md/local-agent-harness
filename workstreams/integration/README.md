# integration

Owner Astra owns `O-ASTRA-01`: see the [handoff](../../handoffs/01-astra.md). Friend Sol reviews the employee-facing contract.

Keep ticket code, synthetic fixtures and evidence here. Do not commit secrets, model weights, recordings or generated binaries.

## App-facing selection run

`start_selection` creates one single-threaded, in-memory run. Read `status` to
render it; reading does not poll, even at the deadline. Use integer clock ticks:

```python
from workstreams.integration.validator import start_selection

tick = 0
run = start_selection('select', ['fixture:button'], lambda: True,
                      clock=lambda: tick, wait=3)
assert run.status == 'waiting'
tick = 3
assert run.stop() == 'stop_requested'       # blocks dispatch immediately
assert run.poll() == 'stop_requested'       # the deadline is not an acknowledgment
assert run.events == ()
assert run.acknowledge_stop() == 'stopped'  # separate synthetic input for this run
```

`edit_wait(ticks)` changes the deadline relative to the start; only `poll()`
can produce the single `('select', 'fixture:button')` event. `dispatched` means
that event was recorded, not that an external action completed. `deny`,
`clarify`, and `stop` (no consent) retain their validator meanings. Stop does
not rewrite these outcomes or undo a dispatch. Repeated stops are harmless;
without acknowledgment the run remains `stop_requested`. Starting again creates
a new handle; deliver any delayed acknowledgment to the original handle.
