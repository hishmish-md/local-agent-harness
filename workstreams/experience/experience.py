"""Offline, single-run employee demo; no production authentication or adapters."""

from collections import deque
from dataclasses import dataclass


OBSERVATION_CONSENT = (
    "Allow an admin to see the status of this run only? They cannot read your "
    "answer, send messages, or control the run. You can turn access off at any time."
)


class FakeAdapter:
    clarification = "Which fictional inbox: Cedar or Maple?"

    def __init__(self):
        self.connected = True
        self.dispatched: list[str] = []

    def actions_for(self, answer):
        if answer not in ("Cedar", "Maple"):
            raise ValueError("Choose Cedar or Maple.")
        return (f"{answer}: open", f"{answer}: summarize")

    def dispatch(self, action):
        self.dispatched.append(action)


@dataclass(frozen=True)
class Status:
    state: str
    clarification: str | None
    in_flight: str | None
    observation_active: bool


class Demo:
    """Trusted composition root issues separate opaque, in-process sessions."""

    def __init__(self):
        self.adapter = FakeAdapter()
        self.employee_session = object()
        self.admin_session = object()
        self._state = "Awaiting clarification"
        self._clarification = self.adapter.clarification
        self._queue: deque[str] = deque()
        self._in_flight: str | None = None
        self._consent = False
        self._observing = False

    def _status(self):
        state = self._state
        if not self.adapter.connected and state not in ("Completed", "Stopped"):
            state = "Status unknown"
        return Status(state, self._clarification, self._in_flight, self._observing)

    def _end(self, state):
        self._state = state
        self._clarification = None
        self._queue.clear()
        self._consent = self._observing = False

    def employee_request(self, session, operation, value=None):
        if session is not self.employee_session:
            raise PermissionError("Employee session required.")
        if operation == "status":
            return self._status()
        if operation == "answer":
            if self._state != "Awaiting clarification":
                raise ValueError("No clarification is accepting an answer.")
            self._queue.extend(self.adapter.actions_for(value))
            self._clarification = None
            self._state = "Running"
        elif operation == "pause":
            if self._state not in (
                "Running",
                "Awaiting clarification",
                "Pausing",
                "Paused",
            ):
                raise ValueError("No active run to pause.")
            self._state = "Pausing" if self._in_flight else "Paused"
        elif operation == "resume":
            if self._state != "Paused":
                raise ValueError("Only a paused run can resume.")
            self._state = "Awaiting clarification" if self._clarification else "Running"
        elif operation == "stop":
            if self._state != "Completed":
                self._end("Stopped")
        elif operation == "grant-observation":
            if self._state in ("Completed", "Stopped"):
                raise ValueError("No active run to share.")
            self._consent = True
        elif operation == "revoke-observation":
            self._consent = self._observing = False
        else:
            raise PermissionError("Operation unavailable to employees.")
        return self._status()

    def admin_request(self, session, operation):
        if session is not self.admin_session:
            raise PermissionError("Admin session required.")
        if operation == "enable-observation" and self._consent:
            self._observing = True
        elif operation == "disable-observation":
            self._observing = False
        elif operation == "observe" and self._observing:
            return self._status().state
        else:
            raise PermissionError("Admin operation not allowed.")
        return None

    def tick(self):
        """Each fake adapter tick either settles a dispatch or starts one, never both."""
        if not self.adapter.connected:
            return
        if self._in_flight is not None:
            self._in_flight = None
            if self._state == "Pausing":
                self._state = "Paused"
            elif self._state == "Running" and not self._queue:
                self._end("Completed")
        elif self._state == "Running":
            if self._queue:
                self._in_flight = self._queue.popleft()
                self.adapter.dispatch(self._in_flight)
            else:
                self._end("Completed")


def main():
    demo = Demo()
    session = demo.employee_session
    print(
        "Commands: status, answer Cedar, answer Maple, tick, pause, resume, stop, "
        "observation-info, grant-observation, revoke-observation, quit"
    )
    while True:
        status = demo.employee_request(session, "status")
        print(
            status.state,
            "| Admin observation:",
            "on" if status.observation_active else "off",
        )
        if status.clarification:
            print(status.clarification)
        if status.in_flight:
            print("Already in flight:", status.in_flight)
        try:
            command = input("employee> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        operation, _, value = command.partition(" ")
        if operation == "quit":
            return
        try:
            if operation == "tick":
                demo.tick()
            elif operation == "observation-info":
                print(OBSERVATION_CONSENT)
            else:
                if operation == "grant-observation":
                    print(OBSERVATION_CONSENT)
                    if input("Allow? [y/N] ").strip().lower() != "y":
                        continue
                demo.employee_request(session, operation, value)
        except (EOFError, KeyboardInterrupt):
            return
        except (PermissionError, ValueError) as exc:
            print(exc)


if __name__ == "__main__":
    main()
