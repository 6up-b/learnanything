"""Shared doubles for the structured-contract step's tests (``learnloop.ai.structured_contracts``).

``operation_send`` is what an adopting caller's one-attempt send looks like: it sends the attempt's prompt and
remaining time through ``execute_structured_operation`` with the shared check inside the operation. ``Refused`` is a
caller's failure type, carrying the ``ContractFailure`` it was raised for.
"""

from __future__ import annotations

from typing import Any

from learnloop.ai.structured_contracts import Attempt, ContractFailure, RecoveryState
from learnloop.ai.transport import execute_structured_operation


class Refused(RuntimeError):
    """A caller's own failure, raised through ``failure``."""

    def __init__(self, info: ContractFailure) -> None:
        super().__init__(info.reason)
        self.info = info


def refused(info: ContractFailure) -> Refused:
    return Refused(info)


def operation_send(client: Any, *, purpose: str, result_model: type, **kwargs: Any):
    """A one-attempt send through the transport; ``send.attempts`` lists what it was asked to send."""

    attempts: list[Attempt] = []

    def send(attempt: Attempt, check):
        attempts.append(attempt)
        return execute_structured_operation(client, purpose=purpose, prompt=attempt.prompt, result_model=result_model,
                                            timeout_seconds=attempt.timeout_seconds, check=check, **kwargs)

    send.attempts = attempts  # type: ignore[attr-defined]
    return send


class Recorder:
    """A durable store of a call's recovery state, as a job would keep it."""

    def __init__(self) -> None:
        self.states: list[RecoveryState] = []

    def __call__(self, state: RecoveryState) -> None:
        self.states.append(state)

    @property
    def last(self) -> RecoveryState:
        return self.states[-1] if self.states else RecoveryState()


class Admit:
    """A caller's retry slot: admits ``slots`` recoveries, counting every ask."""

    def __init__(self, slots: int = 1) -> None:
        self.slots = slots
        self.asked = 0

    def __call__(self) -> bool:
        self.asked += 1
        if self.slots <= 0:
            return False
        self.slots -= 1
        return True


def root_receipts(events: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """The root receipts an observer saw, each start merged with its finish, in start order."""

    finishes = {event["id"]: event for action, event in events if action == "finish"}
    return [{**event, **finishes.get(event["id"], {})}
            for action, event in events if action == "start" and event.get("parent_call_id") is None]
