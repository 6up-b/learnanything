"""RO4 §8.9's forecast evaluation: the LLM policy's per-option forecasts, bound to observed outcomes.

The LLM policy (``router_llm_choice_v3``) states, for every option, ``p_cold_1``, ``p_cold_7`` and ``p_cold_30``: the
probability of a correct, unassisted answer to an unseen question on the option's main topic 1, 7 and 30 days after
the block, had the learner done that option now. That is RO2's ``lo_cold_success`` event, so the forecasts are
resolved by RO2's versioned resolver (``adaptive_difficulty.history_resolve.resolve_curves``) under its two
bindings, scored at the realized lag.

**The binding** (:data:`BINDING_VERSION`), stated so it can change by version: only the **drawn and served** option's
forecast can meet an outcome (the others describe actions not taken); its block is the decision's block (the first
plan presentation the decision served), its topic the option's main LO (its first, as the request names it), and the
stop offer, a declined LLM answer or a decision that served nothing are censored at birth with their reason. The
forecasts are read from the immutable trace (``router_objective_traces``), so nothing is written: the binding is
derived at read time, as RO2's resolution is.

Natural checks are selected, so every row is conditional on observation (RO2's label), and none of this enters
``w`` (§8.7: natural checks never do). Reported apart from the action-value and recommendation-value evaluations.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import json
import math
from typing import Any

#: v1: the drawn option's forecasts, its block the decision's first served presentation, its topic the main LO.
BINDING_VERSION = "ro4-policy-forecast-binding-v1"
FORECASTER = "router_llm_choice_v3"
STOP = "stop_for_today"


def groups(connection: Any) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """The resolvable curves (one per served decision whose drawn option the LLM policy forecast) and the counts of
    those censored at birth, by reason."""

    from learnloop.db.stores import router_objective as store

    if not store.table_present(connection, store.TRACES):
        return [], {}
    censored: dict[str, int] = {}
    found: list[dict[str, Any]] = []
    for row in connection.execute(
            "SELECT id, decision_id, chosen_ref, llm_status, trace_json FROM router_objective_traces "
            "WHERE decision_kind = 'plan_block' ORDER BY created_at, id"):
        trace = json.loads(row["trace_json"])
        chosen = str(row["chosen_ref"])
        if chosen == STOP:
            censored["stop_offer"] = censored.get("stop_offer", 0) + 1
            continue
        if row["llm_status"] != "answered":
            censored["llm_not_answered"] = censored.get("llm_not_answered", 0) + 1
            continue
        entry = (trace.get("candidates") or {}).get(chosen) or {}
        forecast = (entry.get("sensors") or {}).get("llm_forecast") or {}
        curve = {str(lag): forecast.get(f"p_cold_{lag}") for lag in (1, 7, 30)}
        lo = entry.get("main_lo")
        if not lo or any(value is None for value in curve.values()):
            censored["no_forecast_or_topic"] = censored.get("no_forecast_or_topic", 0) + 1
            continue
        served = connection.execute(
            "SELECT id FROM plan_presentations WHERE router_decision_id = ? ORDER BY served_at, id LIMIT 1",
            (row["decision_id"],)).fetchone()
        if served is None:
            censored["nothing_served"] = censored.get("nothing_served", 0) + 1
            continue
        policy = (trace.get("policies") or {}).get("llm") or {}
        found.append({"plan_presentation_id": str(served[0]), "forecaster": FORECASTER, "learning_object_id": str(lo),
                      "curve": curve, "receipt_ids": [str(row["id"])], "decision_id": str(row["decision_id"]),
                      "model": policy.get("model"), "prompt_version": (trace.get("versions") or {}).get("llm_schema"),
                      "card": (trace.get("versions") or {}).get("card"), "rung": None,
                      "binding_version": BINDING_VERSION})
    return found, censored


def resolve(connection: Any, vault: Any, repository: Any, *, now: str,
            resolve_curves: Callable[..., list[dict[str, Any]]]) -> dict[str, Any]:
    """The bound forecasts resolved by RO2's resolver, and the censored-at-birth counts (pure reads).
    ``resolve_curves`` is ``adaptive_difficulty.history_resolve.resolve_curves``, handed in by the caller (the CLI):
    this package sits below adaptive difficulty's importers, so importing it here would close a cycle."""

    curves, censored = groups(connection)
    rows = resolve_curves(connection, vault, repository, curves, now=now) if curves else []
    return {"binding_version": BINDING_VERSION, "rows": rows, "censored_at_birth": censored}


def summary(resolved: Mapping[str, Any] | None) -> dict[str, Any]:
    """Counts and scores per binding and comparator (model, prompt, card): scored, pending, censored by reason,
    mean log loss and Brier score, and observed against forecast (calibration in the large)."""

    if not resolved:
        return {"status": "not resolved (no vault was given to the report)"}
    rows: Sequence[Mapping[str, Any]] = resolved.get("rows") or ()
    out: dict[str, Any] = {}
    for row in rows:
        key = f"{row.get('binding')}|{row.get('model')}|{row.get('prompt_version')}|{row.get('card')}"
        entry = out.setdefault(key, {"binding": row.get("binding"), "model": row.get("model"),
                                     "prompt_version": row.get("prompt_version"), "card": row.get("card"),
                                     "scored": 0, "pending": 0, "censored": {}, "_p": [], "_y": [], "_ll": [],
                                     "_brier": []})
        status = row.get("status")
        if status == "scored" and row.get("p") is not None and row.get("y") is not None:
            entry["scored"] += 1
            entry["_p"].append(float(row["p"]))
            entry["_y"].append(float(row["y"]))
            if row.get("log_loss") is not None:
                entry["_ll"].append(float(row["log_loss"]))
            if row.get("brier") is not None:
                entry["_brier"].append(float(row["brier"]))
        elif status == "pending":
            entry["pending"] += 1
        else:
            reason = str(row.get("reason") or status)
            entry["censored"][reason] = entry["censored"].get(reason, 0) + 1
    comparators = []
    for entry in out.values():
        p, y, ll, brier = entry.pop("_p"), entry.pop("_y"), entry.pop("_ll"), entry.pop("_brier")
        entry["mean_forecast"] = round(sum(p) / len(p), 6) if p else None
        entry["observed_rate"] = round(sum(y) / len(y), 6) if y else None
        entry["mean_log_loss"] = round(sum(ll) / len(ll), 6) if ll else None
        entry["brier"] = round(sum(brier) / len(brier), 6) if brier else None
        entry["log_loss_finite"] = all(math.isfinite(v) for v in ll)
        comparators.append(entry)
    return {"binding_version": resolved.get("binding_version"), "forecaster": FORECASTER,
            "censored_at_birth": dict(resolved.get("censored_at_birth") or {}),
            "label": "observed outcomes, conditional on observation (natural checks are selected); never enters w",
            "comparators": sorted(comparators, key=lambda e: (str(e["binding"]), str(e["model"]))),
            "unique_assessments": len({row.get("attempt_id") for row in rows
                                       if row.get("status") == "scored" and row.get("attempt_id")})}


__all__ = ["BINDING_VERSION", "FORECASTER", "groups", "resolve", "summary"]
