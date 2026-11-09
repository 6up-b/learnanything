"""Model route health from call receipts (``learnloop doctor``).

Every Decider call failed for weeks with nothing to show it (Decider v1.2
review, ``docs/reviews/decider-v1-2.md``): the receipts held the failures,
but nothing read them. This reads them. A *route* here is a call purpose
(``learner_gap_kind``, ``router_decision``, ...) as its root receipts record
it, and its provider/model is the one its most recent receipt named.

For each route: its last completed call and the failures since then (with
the last failure's error type, ``finish_reason``, e.g. ``http_404``, and the
provider's redacted error text where a transport recorded one). There is no
threshold (owner rule: no made-up constants). A route is flagged only when it
has failed since its provider/model last changed and nothing has completed
since then, or it never completed at all. A configured profile whose model
now differs from the receipts' counts as a change, so a route repaired by
config is not flagged before its next call shows what the new model does.

Functional core (:func:`route_health`, rows in, facts out) and a thin shell
(:func:`check_model_routes`, the doctor's reader).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

#: The doctor issue code of a flagged route.
FINDING_CODE = "ai:model_route_failing"


@dataclass
class RouteHealth:
    purpose: str
    provider: str | None
    model: str | None
    #: The model the provider profile is configured with now, if it names one.
    configured_model: str | None
    calls: int
    last_completed_at: str | None
    last_completed_provider: str | None
    last_completed_model: str | None
    failures_since_completed: int
    first_failure_since_completed_at: str | None
    last_failure_at: str | None
    last_failure_error_type: str | None
    last_failure_reason: str | None
    last_failure_text: str | None
    #: When the route's current provider/model was first used.
    current_since: str | None
    #: The configured model differs from the one the receipts name.
    model_changed_since: bool
    flagged: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def message(self) -> str:
        where = f"{self.provider or 'unknown provider'}, {self.model or 'unknown model'}"
        since = (f"since its last completed call at {self.last_completed_at}" if self.last_completed_at
                 else "and it has never completed")
        last = self.last_failure_error_type or "unknown error"
        if self.last_failure_reason:
            last += f" ({self.last_failure_reason})"
        text = f": {self.last_failure_text}" if self.last_failure_text else ""
        changed = (f"; none completed since this provider/model was first used at {self.current_since}"
                   if self.last_completed_at else "")
        return (f"Model route {self.purpose} ({where}) has failed {self.failures_since_completed} time(s) "
                f"{since}{changed}. Last failure {self.last_failure_at}: {last}{text}")


def route_health(
    rows: Iterable[Mapping[str, Any]], configured_models: Mapping[str, str | None] | None = None,
) -> list[RouteHealth]:
    """Facts per purpose from root receipts in ``started_at`` order.

    ``rows`` carry ``purpose``, ``provider``, ``model``, ``status``,
    ``started_at``, ``finish_reason``, ``error_type`` and ``failure_text``.
    Only ``completed`` and ``failed`` change the facts; a started (lost),
    interrupted or truncated call is neither a completion nor a failure.
    """

    configured = configured_models or {}
    routes: dict[str, dict[str, Any]] = {}
    for row in rows:
        purpose = str(row.get("purpose") or "")
        state = routes.setdefault(purpose, {
            "calls": 0, "current": None, "current_since": None, "run_failures": 0, "run_completed": 0,
            "last_completed": None, "failures_since": 0, "first_failure_since": None, "last_failure": None,
        })
        provider_model = (row.get("provider"), row.get("model"))
        if provider_model != state["current"]:
            state.update(current=provider_model, current_since=row.get("started_at"), run_failures=0,
                         run_completed=0)
        state["calls"] += 1
        status = row.get("status")
        if status == "completed":
            state["run_completed"] += 1
            state.update(last_completed=row, failures_since=0, first_failure_since=None)
        elif status == "failed":
            state["run_failures"] += 1
            state["failures_since"] += 1
            state["first_failure_since"] = state["first_failure_since"] or row.get("started_at")
            state["last_failure"] = row
    result = []
    for purpose, state in sorted(routes.items()):
        provider, model = state["current"]
        configured_model = configured.get(provider) if provider else None
        changed = bool(configured_model) and bool(model) and configured_model != model
        completed = state["last_completed"] or {}
        failure = state["last_failure"] if state["failures_since"] else None
        result.append(RouteHealth(
            purpose=purpose, provider=provider, model=model, configured_model=configured_model,
            calls=state["calls"],
            last_completed_at=completed.get("started_at"),
            last_completed_provider=completed.get("provider"),
            last_completed_model=completed.get("model"),
            failures_since_completed=state["failures_since"],
            first_failure_since_completed_at=state["first_failure_since"],
            last_failure_at=failure.get("started_at") if failure else None,
            last_failure_error_type=failure.get("error_type") if failure else None,
            last_failure_reason=failure.get("finish_reason") if failure else None,
            last_failure_text=failure.get("failure_text") if failure else None,
            current_since=state["current_since"],
            model_changed_since=changed,
            flagged=state["run_failures"] > 0 and state["run_completed"] == 0 and not changed,
        ))
    return result


def check_model_routes(repository: Any, configured_models: Mapping[str, str | None]) -> list[RouteHealth]:
    """The doctor's reader: every root receipt, oldest first."""

    return route_health(repository.model_route_receipts(), configured_models)


__all__ = ["FINDING_CODE", "RouteHealth", "check_model_routes", "route_health"]
