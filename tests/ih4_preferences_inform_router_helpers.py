"""What other test files use from ``tests/test_ih4_preferences_inform_router.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.daily_plan import objective_chooser as OC
from learnloop.db.stores import router_objective as trace_store


def _traces(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return [trace_store.trace(connection, row["decision_id"])["trace"] for row in trace_store.traces(connection)
                if row["decision_kind"] == "plan_block"]


def _pin(monkeypatch) -> Any:
    """RO5's method: the plan's and the attempt's fresh ids and the version out of the key, so twin plans seed alike."""

    real_hash = OC._hash
    monkeypatch.setattr(OC, "_hash", lambda value: real_hash(
        {k: v for k, v in value.items() if k not in ("version", "plan_id")} if isinstance(value, dict) else value))
    monkeypatch.setattr(OC, "_latest_attempt", lambda _repository: "pinned-attempt")
    return lambda _key, _decision: "pinned-seed"


def _numbers(trace: dict[str, Any]) -> dict[str, Any]:
    return {"candidates": {ref: entry.get("terms") for ref, entry in trace["candidates"].items()},
            "mu": trace["mixing"]["mu"], "numeric": {key: trace["policies"]["numeric"][key] for key in ("choice", "tie")},
            "residual": {key: (trace.get("residual") or {}).get(key) for key in ("w_hat", "fit", "candidates")}}
