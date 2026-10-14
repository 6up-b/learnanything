"""Router R2b: the router's decisions as rows of the Decider agreement report.

``learnloop decider agreement`` (the Decider migration's report,
``learnloop.ai.agreement``) reads ``judgment_ledger`` rows. The router never
duplicates its answers there (plan §4: the report gets a router adapter
instead): this module reads ``router_decisions`` and turns each decision both
models answered into ledger-shaped rows, one per judge and question, so the
report's pairing, agreement, confusion and fallback counts apply unchanged.

* ``router_choose_block``: each model's argmax over the decision's options,
  with its distribution as ``probabilities`` (argmax agreement);
* ``router_teach_first`` / ``router_will_pass_next`` (R2c sensors) and
  ``router_intervene_now`` (the restraint): ``yes`` when P(yes) >= 0.5, with
  ``{"yes": p, "no": 1 - p}`` (P(yes) agreement by the same rule);
* a model that did not answer is a Decider row with no answer
  (``unavailable`` when not set up, ``refused`` for spend, ``failed``
  otherwise), so the report counts the Decider's failures and the LLM's
  answers beside them as fallbacks.

Read-only and pure over the rows; no model call, no write. A leaf module.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from typing import Any

TASK_CHOOSE = "router_choose_block"
TASK_SENSOR = {"teach_first": "router_teach_first", "will_pass_next": "router_will_pass_next"}
TASK_INTERVENE = "router_intervene_now"
_FAILURE_VERDICTS = {"not_ready": "unavailable", "spend": "refused"}


def _json(value: Any) -> Any:
    try:
        return json.loads(value) if isinstance(value, str) else value
    except ValueError:
        return None


def _argmax(distribution: Mapping[str, float]) -> str:
    return sorted(distribution.items(), key=lambda item: (-float(item[1]), item[0]))[0][0]


def _row(decision: Mapping[str, Any], *, task: str, judge: str, verdict: str, probabilities: Mapping[str, float] | None,
         right: tuple[str, str] | None = None) -> dict[str, Any]:
    return {
        "id": f"router:{decision['id']}:{task}:{right[1] if right else ''}:{judge}",
        "task": task,
        "left_kind": "router_decision",
        "left_id": decision["id"],
        "right_kind": right[0] if right else None,
        "right_id": right[1] if right else None,
        "input_hash": decision.get("card_hash") or decision.get("snapshot_hash"),
        "judge": judge,
        "verdict": verdict,
        "rationale": json.dumps({"probabilities": dict(probabilities)} if probabilities else {}, sort_keys=True),
        "created_at": decision["created_at"],
        "supersedes_id": None,
    }


def router_agreement_rows(decisions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Ledger-shaped rows for every decision with logged model answers."""

    rows: list[dict[str, Any]] = []
    for decision in decisions:
        distributions = _json(decision.get("model_distributions_json"))
        if not isinstance(distributions, Mapping):
            continue
        detail = _json(decision.get("detail_json")) or {}
        statuses = ((detail.get("mixture") or {}).get("models") or {}) if isinstance(detail, Mapping) else {}
        task = TASK_INTERVENE if decision.get("decision_kind") == "plan_interrupt" else TASK_CHOOSE
        for judge in ("decider", "llm"):
            distribution = distributions.get(judge)
            status = str((statuses.get(judge) or {}).get("status") or ("answered" if distribution else "failed"))
            if isinstance(distribution, Mapping) and distribution:
                rows.append(_row(decision, task=task, judge=judge, verdict=_argmax(distribution),
                                 probabilities=distribution))
            elif judge == "decider":
                rows.append(_row(decision, task=task, judge=judge,
                                 verdict=_FAILURE_VERDICTS.get(status, "failed"), probabilities=None))
        sensors = _json(decision.get("sensor_answers_json"))
        if not isinstance(sensors, Mapping):
            continue
        for judge in ("decider", "llm"):
            for kind, task_name in TASK_SENSOR.items():
                for topic, p_yes in ((sensors.get(judge) or {}).get(kind) or {}).items():
                    probabilities = {"yes": float(p_yes), "no": 1.0 - float(p_yes)}
                    rows.append(_row(decision, task=task_name, judge=judge,
                                     verdict="yes" if float(p_yes) >= 0.5 else "no",
                                     probabilities=probabilities, right=("learning_object", str(topic))))
    return rows


def router_decision_rows_for_agreement(connection: Any) -> list[dict[str, Any]]:
    """The decisions with logged model answers, from one database (none without the ledger)."""

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'router_decisions'"
    ).fetchone() is None:
        return []
    cursor = connection.execute(
        "SELECT id, decision_kind, card_hash, snapshot_hash, model_distributions_json, sensor_answers_json, "
        "detail_json, created_at FROM router_decisions WHERE model_distributions_json IS NOT NULL "
        "ORDER BY created_at, id"
    )
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor]


__all__ = [
    "TASK_CHOOSE",
    "TASK_INTERVENE",
    "TASK_SENSOR",
    "router_agreement_rows",
    "router_decision_rows_for_agreement",
]
