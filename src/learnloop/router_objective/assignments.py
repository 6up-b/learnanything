"""RO5 §9: each arm's assignment in ``policy_experiment_assignments`` (migration 098), the one place policy
experimentation lives, through its existing ``experiment_id`` (``daily_plan/measurement.py``'s
``experiment_id`` and ``scheduling/randomization_layer.py``'s are the same integration point). Not a generic
experiment framework: three experiment ids, each with its own unit and exact probability.

| Experiment | Unit (``unit_kind``, ``unit_id``) | Variant | Probability |
|---|---|---|---|
| :data:`STOP_COIN` | ``decision``, the ``plan_block`` router decision | ``offer_stop``, ``present_next``, ``policy`` | ``p``, ``p``, ``1 − 2p`` |
| :data:`CHECK` | ``decision``, ``check-day:<local date>:<slot>`` | the drawn topic | ``1/N_d`` (or the rate) |
| :data:`PICK` | ``decision``, the misconception pick's report | ``open``, ``resolve`` | the share, ``1 − share`` |

``decision_id`` (a foreign key to the P4 controller's decisions) stays NULL: the unit id names the router
decision, the check day or the report. ``design`` is ``mrt_reversible`` (each is a reversible, randomized
assignment), ``grade`` ``experimental``. The assignment's draw and seed replay it; ``detail_json`` holds what was
known before the draw (availability for the coin, the eligible set for a check, the eligibility for a pick).

Rows are inserted on the caller's connection, in the decision's own transaction where there is one (the coin
rides on the ``plan_block`` logger, as the trace does), each in its own savepoint: a refused row rolls back
alone with a warning and never blocks a plan or an answer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import logging
from typing import Any

from learnloop.ids import new_ulid

LOG = logging.getLogger(__name__)

STOP_COIN = "ro5_stop_coin:v1"
CHECK = "ro5_randomized_check:v1"
PICK = "ro5_open_pick:v1"
EXPERIMENTS: tuple[str, ...] = (STOP_COIN, CHECK, PICK)
DESIGN = "mrt_reversible"
TABLE = "policy_experiment_assignments"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def present(connection: Any) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (TABLE,)).fetchone() \
        is not None


def insert(connection: Any, *, experiment_id: str, unit_id: str, variant: str, propensity: float, seed: str,
           draw: float | None, candidate_refs: Sequence[Any] = (), detail: Mapping[str, Any] | None = None,
           at: str) -> str | None:
    """One assignment on ``connection`` in its own savepoint; its id, or None (a warning) when refused."""

    from learnloop.db.stores import router_objective as store

    if not present(connection):
        return None
    assignment_id = new_ulid()
    written = store.insert_assignment(connection, {
        "id": assignment_id, "experiment_id": experiment_id, "decision_id": None, "unit_kind": "decision",
        "unit_id": unit_id, "variant": variant, "propensity": float(propensity), "seed": seed, "draw": draw,
        "epsilon_margin": None, "near_equivalent": 0, "design": DESIGN, "grade": "experimental",
        "candidate_refs_json": _canonical(list(candidate_refs)), "detail_json": _canonical(dict(detail or {})),
        "created_at": at,
    })
    if not written:  # an assignment never blocks the plan: it rolled back alone, with the store's warning
        LOG.warning("router objective RO5: the %s assignment for %s was not written", experiment_id, unit_id)
        return None
    return assignment_id


def record_pending(connection: Any, pending: Iterable[Mapping[str, Any]], *, unit_id: str, at: str) -> list[str]:
    """The assignments a chooser froze on its record (``ro5_assignments``), written with the decision they belong
    to (``unit_id`` the router decision id)."""

    written = []
    for row in pending or ():
        assignment_id = insert(connection, experiment_id=str(row["experiment_id"]), unit_id=unit_id,
                               variant=str(row["variant"]), propensity=float(row["propensity"]),
                               seed=str(row["seed"]), draw=row.get("draw"),
                               candidate_refs=row.get("candidate_refs") or (), detail=row.get("detail") or {}, at=at)
        if assignment_id is not None:
            written.append(assignment_id)
    return written


def rows(connection: Any, experiment_id: str, *, unit_like: str | None = None,
         unit_id: str | None = None) -> list[dict[str, Any]]:
    """Every assignment of one experiment, oldest first, with its JSON decoded (read-only)."""

    if not present(connection):
        return []
    sql = "SELECT * FROM policy_experiment_assignments WHERE experiment_id = ?"
    parameters: list[Any] = [experiment_id]
    if unit_like is not None:
        sql += " AND unit_id LIKE ?"
        parameters.append(unit_like)
    if unit_id is not None:
        sql += " AND unit_id = ?"
        parameters.append(unit_id)
    out = []
    for row in connection.execute(sql + " ORDER BY created_at, id", parameters):
        found = dict(row)
        found["detail"] = json.loads(found.pop("detail_json") or "{}")
        found["candidate_refs"] = json.loads(found.pop("candidate_refs_json") or "[]")
        out.append(found)
    return out


def by_unit(connection: Any, experiment_id: str, unit_id: str) -> dict[str, Any] | None:
    found = rows(connection, experiment_id, unit_id=unit_id)
    return found[0] if found else None


__all__ = ["CHECK", "DESIGN", "EXPERIMENTS", "PICK", "STOP_COIN", "by_unit", "insert", "present", "record_pending",
           "rows"]
