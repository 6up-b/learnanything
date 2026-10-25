"""E1's scoring and its prespecified decision (spec §8; fixed before any v2 result).

Every arm is scored on the SAME merged labels and common units (E0's
candidate units, exact cosine, @10). Comparisons are paired, family-clustered
bootstraps (E0's ``metrics.paired_bootstrap``) on the primary development
slice (context-dependent/support questions), with the logged slice apart:

* ``context_gain_v2``: V2_grouped minus V2_singleton (same model);
* ``v2_vs_best_frozen``: the v2 arm chosen on that slice (disclosed: no
  separate confirmation slice exists) minus each copy's best E0 finalist
  (one-model Qwen, Perplexity v1 family, Voyage family), re-scored;
* the same against each finalist family (hosted v1 is a model baseline,
  never a numerical reference for v2).

Decision: no verdict unless E0's S1 passed, the replay reproduced E0, the
smoke checks passed, the v2 arms scored >= 95% of eligible questions and
the supplementary labels are complete with κ >= 0.60; then ``retain_candidate``
(>= +5 points, CI excluding 0; always exploratory with under 5 independent
families: independent confirmation is needed before any adoption, §7),
``non_inferior_cost_latency_only`` (lower bound above -0.02) or ``stop``.
Production adoption is never authorized by E1.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins
from learnloop.experiments.contextual_embeddings.evaluate import arm_summary, completion, paired

METRICS = ("ce10", "support10", "answer10", "ndcg10", "mrr", "unknown")
FINALIST_KEYS = ("one_model", "R4", "R5")


def _primary(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    from learnloop.experiments.contextual_embeddings.paid import primary_rows

    return primary_rows(rows)


def _best(summary: Mapping[str, Mapping[str, Any]], arms: Sequence[str]) -> str | None:
    scored = [(summary[arm]["ce10"], arm) for arm in arms if arm in summary and summary[arm].get("ce10") is not None]
    return min(scored, key=lambda item: (-item[0], item[1]))[1] if scored else None


def add_virtual_arms(rows: list[dict[str, Any]], finalists: Mapping[str, str | None], best: str | None,
                     v2_best: str | None) -> None:
    """Per-row columns for each copy's finalists, its best finalist and the chosen v2 arm."""

    columns = {f"F_{key}": finalists.get(key) for key in FINALIST_KEYS} | {"F_best": best, "V2_best": v2_best}
    for row in rows:
        for column, arm in columns.items():
            for metric in METRICS:
                row[f"{column}:{metric}"] = row.get(f"{arm}:{metric}") if arm else None


def decide_e1(plan: Mapping[str, Any], copies: Mapping[str, Mapping[str, Any]], pooled: list[dict[str, Any]], *,
              measured: Sequence[Mapping[str, Any]], gpu_meter: Mapping[str, Any],
              spend: Mapping[str, Any]) -> dict[str, Any]:
    v2_arms = list(e1_pins.V2_ARMS)
    e0_arms = list(e1_pins.E0_REPRESENTATION_ARMS)
    v2_summary = arm_summary(_primary(pooled), v2_arms)
    v2_best = _best(v2_summary, v2_arms)
    per_copy: dict[str, Any] = {}
    for label, copy in copies.items():
        rows = copy["rows"]
        primary = _primary(rows)
        summary = arm_summary(primary, [*e0_arms, *v2_arms])
        finalists = {key: copy["finalists"].get(key) for key in FINALIST_KEYS}
        best = _best(summary, [arm for arm in finalists.values() if arm])
        add_virtual_arms(rows, finalists, best, v2_best)
        per_copy[label] = {
            "retrieval": summary, "finalists": finalists, "best_frozen": best,
            "logged": arm_summary([row for row in rows if row["split"] == "logged"], [*e0_arms, *v2_arms]),
            "v2_completion": completion(primary, v2_arms), "v2_missing": copy["missing"],
            "supplement": copy["supplement"], "merged": copy["merged"], "replay_ok": bool(copy["replay"].get("ok")),
            "e0_s1": copy["e0_s1"],
        }
    primary = _primary(pooled)
    logged = [row for row in pooled if row["split"] == "logged"]
    comparisons = {
        "context_gain_v2": paired(primary, "V2_singleton", "V2_grouped"),
        "v2_vs_best_frozen": paired(primary, "F_best", "V2_best"),
        **{f"v2_vs_{key}": paired(primary, f"F_{key}", "V2_best") for key in FINALIST_KEYS},
        "v2_vs_best_frozen:logged": paired(logged, "F_best", "V2_best"),
    }
    reasons = []
    if not all(item["e0_s1"] == "labels_ok" for item in per_copy.values()):
        reasons.append("E0's S1 stopped verdicts")
    if not all(item["replay_ok"] for item in per_copy.values()):
        reasons.append("the replay did not reproduce E0")
    smoke_ok = any(((item.get("smoke") or {}).get("all_ok")) for item in measured)
    measured = [item for item in measured if not item.get("smoke_only")] or list(measured)
    if not smoke_ok:
        reasons.append("no worker passed the smoke checks")
    thin = sorted(f"{label}:{arm}" for label, item in per_copy.items() for arm, share in item["v2_completion"].items()
                  if share < e1_pins.V2_COMPLETION_MIN)
    if thin:
        reasons.append("v2 arms materially incomplete: " + ", ".join(thin))
    for label, item in per_copy.items():
        counts = (item["supplement"] or {}).get("counts")
        audits = (item["supplement"] or {}).get("audits") or {}
        kappa = (((item["supplement"] or {}).get("agreement") or {}).get("agreement") or {}).get("kappa")
        if counts is None:
            reasons.append(f"{label}: the supplementary labels never ran")
            continue
        if counts.get("stopped") or counts.get("missing") or audits.get("mandatory_missing"):
            reasons.append(f"{label}: supplementary labels incomplete")
        if counts.get("new_candidates") and (kappa is None or kappa < e1_pins.SUPPLEMENT_KAPPA_MIN):
            reasons.append(f"{label}: supplementary κ below {e1_pins.SUPPLEMENT_KAPPA_MIN}")
    versus = comparisons["v2_vs_best_frozen"]
    if reasons:
        decision = "no_verdict"
    elif versus.get("difference") is None:
        decision, reasons = "no_verdict", ["nothing paired"]
    elif versus["difference"] >= e1_pins.RETAIN_GAIN_MIN and versus["ci95"][0] > 0:
        decision = "retain_candidate"
    elif versus["ci95"][0] > -e1_pins.NONINFERIORITY_MARGIN:
        decision = "non_inferior_cost_latency_only"
    else:
        decision = "stop"
    last = measured[-1] if measured else {}
    return {
        "plan_id": plan["plan_id"], "e0_run_id": (plan.get("e0") or {}).get("run_id"),
        "status": "complete" if not reasons else "incomplete",
        "v2_selected_on_primary_development": v2_best, "v2_pooled": v2_summary,
        "copies": per_copy, "comparisons": comparisons,
        "decision": {"e1": decision, "reasons": reasons, "exploratory": bool(versus.get("exploratory", True)),
                     "rule": (plan.get("decision_rules") or {}).get("rule"),
                     "production_adoption": "not_authorized_by_e1"},
        "local": {"processes": len(measured), "statuses": [item.get("status") for item in measured],
                  "load": last.get("load"), "smoke": last.get("smoke"), "profile": last.get("profile"),
                  "peaks": last.get("peaks"), "device_peak": last.get("device_peak"), "unload": last.get("unload"),
                  "documents": last.get("documents"), "queries": last.get("queries"), "wall_s": last.get("wall_s")},
        "gpu_meter": dict(gpu_meter), "spend": dict(spend),
    }
