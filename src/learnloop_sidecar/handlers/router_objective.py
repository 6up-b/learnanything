"""Router objective RO4 (spec_router_objective_v1 §8.5, §8.8): the "why" surface's trace and a goal's use weights.

* ``router_objective_explain``: the trace of one plan decision in plain words, offered on demand from the "why"
  (frictionless by default, glass box on request). Read-only; a decision with no trace (below the tag, the objective
  off, a deterministic pick) says so.
* ``set_goal_use_weight``: adjust a goal's use weights (§8.5): its dated weight per topic and its undated density.
  A confirmed goal gets a contract successor of class ``use_weight_change`` (the support hash unchanged); an
  unconfirmed goal's ``goals.yaml`` entry holds the copy. Desktop only (never phone-allowed: not on the mobile
  allowlist).
"""

from __future__ import annotations

from contextlib import closing
from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

ROUTER_OBJECTIVE_RPCS = ("router_objective_explain", "set_goal_use_weight")


class ExplainInput(ParamsModel):
    decision_id: str


class GoalUseWeightInput(ParamsModel):
    goal_id: str
    dated: float | None = None
    undated_density: float | None = None
    per_lo: dict[str, float] | None = None


@method("router_objective_explain", ExplainInput)
def router_objective_explain(ctx: SidecarContext, params: ExplainInput) -> dict[str, Any]:
    from learnloop.db.connection import connect
    from learnloop.db.stores import router_objective as store
    from learnloop.router_objective.trace import explain

    vault, repository = ctx.require_vault()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.trace(connection, params.decision_id) if store.table_present(connection, store.TRACES) else None
    if row is None:
        return versioned({"available": False, "lines": [
            "This step was chosen by the plan's usual rule; there is nothing more to show."]})
    return versioned({"available": True, "decision_id": row["decision_id"], "lines": explain(row)})


@method("set_goal_use_weight", GoalUseWeightInput)
def set_goal_use_weight(ctx: SidecarContext, params: GoalUseWeightInput) -> dict[str, Any]:
    from learnloop.goals import goal_contracts
    from learnloop.goals.use_weights import for_goal
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    vault, repository = ctx.require_vault()
    goal = next((g for g in vault.goals if g.id == params.goal_id), None)
    if goal is None:
        raise SidecarError("goal_not_found", f"No goal {params.goal_id!r}.")
    current = for_goal(goal, repository, vault.config)
    proposed = {"dated": current.dated if params.dated is None else params.dated,
                "undated_density": current.undated_density if params.undated_density is None else params.undated_density,
                "per_lo": dict(current.per_lo) if params.per_lo is None else dict(params.per_lo)}
    try:
        canonical = goal_contracts.canonical_use_weight(proposed)
    except ValueError as exc:
        raise SidecarError("goal_invalid_use_weight", str(exc)) from exc
    if goal.confirmed_contract_head_id:
        version = goal_contracts.set_use_weight(repository, goal_id=goal.id, use_weight=canonical, vault=vault)
        ctx.reload(maintenance=False)
        return versioned({"goal_id": goal.id, "use_weight": canonical, "contract_version_id": version.id,
                          "change_class": version.change_class})
    paths = VaultPaths(vault.root, vault.config)
    data = read_yaml(paths.goals_path)
    for entry in (data or {}).get("goals") or []:
        if isinstance(entry, dict) and entry.get("id") == goal.id:
            entry["use_weight"] = canonical
            break
    write_yaml(paths.goals_path, data)
    ctx.reload(maintenance=False)
    return versioned({"goal_id": goal.id, "use_weight": canonical, "contract_version_id": None,
                      "change_class": None})


__all__ = ["ROUTER_OBJECTIVE_RPCS"]
