"""Offline decision only; no action is executed."""


def validate(action, candidates, consent):
    if consent is not True:
        return "stop"
    if type(action) is not str or action != "select" or type(candidates) is not list:
        return "deny"
    if any(type(item) is not str for item in candidates):
        return "deny"
    if len(candidates) != 1:
        return "clarify"
    if candidates != ["fixture:button"]:
        return "deny"
    return "allow"


class PendingSelection:
    """Single-threaded fixture simulator. Clock and delay use integer ticks."""

    def __init__(self, action, candidates, consent, *, clock, wait):
        self._clock = clock
        self._start = clock()
        self._consent = consent
        self._state = 'waiting'
        self.events = ()
        self.edit_wait(wait)
        decision = validate(action, candidates, consent())
        if decision != 'allow':
            self._state = decision

    @property
    def status(self):
        """Observe without polling, even when a zero-tick wait is due."""
        return self._state

    def edit_wait(self, ticks):
        if type(ticks) is not int or ticks < 0:
            raise ValueError('wait must be a nonnegative integer')
        if self._state == 'waiting':
            self._deadline = self._start + ticks

    def cancel(self):
        if self._state == 'waiting':
            self._state = 'cancelled'

    def poll(self):
        if self._state == 'waiting' and self._clock() >= self._deadline:
            consent = self._consent()
            # A callback can cancel synchronously; never overwrite its terminal state.
            if self._state != 'waiting':
                return self._state
            if consent is not True:
                self._state = 'stop'
                return self._state
            self.events = (('select', 'fixture:button'),)
            self._state = 'dispatched'
        return self._state


class SelectionRun:
    """App view of one synthetic selection; stop acknowledgment is a separate input."""

    def __init__(self, pending):
        self._pending = pending
        self._stop_acknowledged = False

    @property
    def status(self):
        state = self._pending.status
        if state == 'cancelled':
            return 'stopped' if self._stop_acknowledged else 'stop_requested'
        return state

    @property
    def events(self):
        return self._pending.events

    def poll(self):
        self._pending.poll()
        return self.status

    def edit_wait(self, ticks):
        self._pending.edit_wait(ticks)
        return self.status

    def stop(self):
        self._pending.cancel()
        return self.status

    def acknowledge_stop(self):
        if self.status == 'stop_requested':
            self._stop_acknowledged = True
        return self.status


def start_selection(action, candidates, consent, *, clock, wait):
    """Start a fresh run without dispatching. Only poll() can advance a wait."""
    return SelectionRun(PendingSelection(action, candidates, consent, clock=clock, wait=wait))
