"""Model route health from call receipts (``learnloop doctor``).

Every Decider call failed for weeks with nothing to show it (Decider v1.2
review, ``docs/reviews/decider-v1-2.md``): the receipts held the failures,
but nothing read them. This reads them. A *route* here is a call purpose
(``learner_gap_kind``, ``router_decision``, ...) on one provider profile, as
its root receipts record them: one purpose can run on two profiles at once
(the probability arms ask the Decider and an LLM under ``llm_probability``),
and one must not hide the other. The route's model is the one its latest
completed or failed call named.

For each route: its last completed call and the failures since then (with
the last failure's error type, ``finish_reason``, e.g. ``http_404``, and the
provider's redacted error text where a transport recorded one). There is no
threshold (owner rule: no made-up constants). A route is flagged only when it
has failed since its provider/model last changed and nothing has completed
since then, or it never completed at all. Three things count as a change:
the model its calls name, the profile now configured with another model (so
a route repaired by config waits for its next call), and the purpose moving
to another profile (a route whose calls all precede the other profile's
first call is superseded, not dead).

Functional core (:func:`route_health`, rows in, facts out) and a thin shell
(:func:`check_model_routes`, the doctor's reader).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from learnloop.clock import parse_utc

#: The doctor issue code of a flagged route.
FINDING_CODE = "ai:model_route_failing"
#: Only these statuses say whether a route works; a started (lost),
#: interrupted or truncated call counts as a call and nothing more.
_TERMINAL = frozenset({"completed", "failed"})
_UNPARSED = datetime.min.replace(tzinfo=UTC)


@dataclass
class RouteHealth:
    purpose: str
    provider: str | None
    model: str | None
    #: The model the provider profile is configured with now, if it names one.
    configured_model: str | None
    calls: int
    last_completed_at: str | None
    last_completed_model: str | None
    failures_since_completed: int
    first_failure_since_completed_at: str | None
    last_failure_at: str | None
    last_failure_error_type: str | None
    last_failure_reason: str | None
    last_failure_text: str | None
    #: When the route's current model was first used.
    current_since: str | None
    #: The configured model differs from the one the receipts name.
    model_changed_since: bool
    #: Another profile took this purpose over after this route's last call.
    superseded_by: str | None
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
        changed = (f"; none completed since this model was first used at {self.current_since}"
                   if self.last_completed_at else "")
        return (f"Model route {self.purpose} ({where}) has failed {self.failures_since_completed} time(s) "
                f"{since}{changed}. Last failure {self.last_failure_at}: {last}{text}")


def _instant(value: Any) -> datetime:
    """Receipt times compared as instants, not strings (``Z``, offsets and
    fractional seconds sort wrongly as text)."""

    try:
        return parse_utc(str(value)) if value else _UNPARSED
    except ValueError:
        return _UNPARSED


def route_health(
    rows: Iterable[Mapping[str, Any]], configured_models: Mapping[str, str | None] | None = None,
) -> list[RouteHealth]:
    """Facts per (purpose, provider) from root receipts, in any order.

    ``rows`` carry ``purpose``, ``provider``, ``model``, ``status``,
    ``started_at``, ``finish_reason``, ``error_type`` and ``failure_text``.
    """

    configured = configured_models or {}
    ordered = sorted(enumerate(rows), key=lambda pair: (_instant(pair[1].get("started_at")), pair[0]))
    routes: dict[tuple[str, Any], dict[str, Any]] = {}
    for _index, row in ordered:
        key = (str(row.get("purpose") or ""), row.get("provider"))
        state = routes.setdefault(key, {
            "calls": 0, "model": None, "current_since": None, "run_failures": 0, "run_completed": 0,
            "last_completed": None, "failures_since": 0, "first_failure_since": None, "last_failure": None,
            "first_at": None, "last_at": None,
        })
        state["calls"] += 1
        status = row.get("status")
        if status not in _TERMINAL:
            continue
        at = _instant(row.get("started_at"))
        state["first_at"] = state["first_at"] or at
        state["last_at"] = at
        if row.get("model") != state["model"] or state["current_since"] is None:
            state.update(model=row.get("model"), current_since=row.get("started_at"), run_failures=0,
                         run_completed=0)
        if status == "completed":
            state["run_completed"] += 1
            state.update(last_completed=row, failures_since=0, first_failure_since=None)
        else:
            state["run_failures"] += 1
            state["failures_since"] += 1
            state["first_failure_since"] = state["first_failure_since"] or row.get("started_at")
            state["last_failure"] = row
    result = []
    for (purpose, provider), state in sorted(routes.items(), key=lambda item: (item[0][0], str(item[0][1]))):
        model = state["model"]
        configured_model = configured.get(provider) if provider else None
        changed = bool(configured_model) and bool(model) and configured_model != model
        superseded = next((
            str(other_provider) for (other_purpose, other_provider), other in routes.items()
            if other_purpose == purpose and other_provider != provider and other["first_at"] is not None
            and state["last_at"] is not None and other["first_at"] > state["last_at"]
        ), None)
        completed = state["last_completed"] or {}
        failure = state["last_failure"] if state["failures_since"] else None
        result.append(RouteHealth(
            purpose=purpose, provider=provider, model=model, configured_model=configured_model,
            calls=state["calls"],
            last_completed_at=completed.get("started_at"),
            last_completed_model=completed.get("model"),
            failures_since_completed=state["failures_since"],
            first_failure_since_completed_at=state["first_failure_since"],
            last_failure_at=failure.get("started_at") if failure else None,
            last_failure_error_type=failure.get("error_type") if failure else None,
            last_failure_reason=failure.get("finish_reason") if failure else None,
            last_failure_text=failure.get("failure_text") if failure else None,
            current_since=state["current_since"],
            model_changed_since=changed,
            superseded_by=superseded,
            flagged=(state["run_failures"] > 0 and state["run_completed"] == 0 and not changed
                     and superseded is None),
        ))
    return result


def check_model_routes(repository: Any, configured_models: Mapping[str, str | None]) -> list[RouteHealth]:
    """The doctor's reader: every root receipt."""

    return route_health(repository.model_route_receipts(), configured_models)


__all__ = ["FINDING_CODE", "RouteHealth", "check_model_routes", "route_health"]
