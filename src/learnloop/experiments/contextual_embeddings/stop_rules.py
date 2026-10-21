"""E0's stop rules S1-S4 (spec §7), computed from the results by code.

Each rule returns a decision with its inputs, so the report shows why. The
thresholds are fixed in ``pins`` before any result exists; nothing here
changes them. Adoption is never automatic: the result always carries
``production_adoption = "not_authorized_by_e0"`` (a second production space
needs the owner's explicit D6 amendment after independent confirmation).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.experiments.contextual_embeddings import pins


def s1(*, kappa: float | None, unresolved_sets: int, extraction_failures: int, policy_failures: int,
       arm_completion: Mapping[str, float], incomplete_work: Mapping[str, int] | None = None) -> dict[str, Any]:
    """Labels and coverage: stop verdicts for kappa < 0.60, unresolved
    evidence sets, extraction/policy failures, materially incomplete arms, or
    planned work left undone (``incomplete_work``: seeds the writer never
    answered, questions never labelled, mandatory audits or planned answers
    never made: Codex review F17)."""

    incomplete = sorted(arm for arm, share in arm_completion.items() if share < pins.ARM_COMPLETION_MIN)
    missing_work = {key: int(value) for key, value in sorted((incomplete_work or {}).items()) if value}
    reasons = []
    if missing_work:
        reasons.append("planned work missing: " + ", ".join(f"{key} {value}" for key, value in missing_work.items()))
    if kappa is None or kappa < pins.KAPPA_MIN:
        reasons.append(f"kappa {kappa if kappa is not None else 'n/a'} < {pins.KAPPA_MIN}")
    if unresolved_sets:
        reasons.append(f"{unresolved_sets} unresolved evidence sets")
    if extraction_failures:
        reasons.append(f"{extraction_failures} extraction failures")
    if policy_failures:
        reasons.append(f"{policy_failures} policy failures")
    if incomplete:
        reasons.append("materially incomplete arms: " + ", ".join(incomplete))
    return {"rule": "S1", "decision": "stop_verdicts" if reasons else "labels_ok", "reasons": reasons,
            "inputs": {"kappa": kappa, "unresolved_sets": unresolved_sets,
                       "extraction_failures": extraction_failures, "policy_failures": policy_failures,
                       "arm_completion": dict(sorted(arm_completion.items())), "incomplete_work": missing_work,
                       "kappa_min": pins.KAPPA_MIN, "completion_min": pins.ARM_COMPLETION_MIN}}


def _lower(result: Mapping[str, Any] | None) -> float | None:
    if not result or not result.get("ci95"):
        return None
    return float(result["ci95"][0])


def s2(direct: Mapping[str, Mapping[str, Any] | None], *, latency_fits: Mapping[str, bool | None]) -> dict[str, Any]:
    """Direct reading for known-location tasks: D2/D3 minus D1 answer pass.

    superior: the lower bound above 0; non-inferior: the lower bound above
    -0.02 (the 2-point margin); else inconclusive (an interval merely
    including zero decides nothing). Latency must fit the Reader budget with
    no paired regression against the incumbent D1 (``latency_fits`` per arm:
    True, False, or None when unmeasured or no budget is pinned)."""

    arms: dict[str, Any] = {}
    preferred = []
    for arm in ("D2", "D3"):
        result = direct.get(arm)
        lower = _lower(result)
        if lower is None:
            verdict = "not_scored"
        elif lower > 0:
            verdict = "superior"
        elif lower > -pins.S2_NONINFERIORITY_MARGIN:
            verdict = "non_inferior"
        else:
            verdict = "inconclusive"
        fits = latency_fits.get(arm)  # None: no pinned Reader latency budget (fails closed)
        if verdict in ("superior", "non_inferior") and fits:
            preferred.append(arm)
        arms[arm] = {"verdict": verdict, "lower_bound": lower, "latency_fits": fits,
                     "difference": None if not result else result.get("difference")}
    return {"rule": "S2", "decision": ("prefer_direct_reading_for_known_location:" + ",".join(preferred))
            if preferred else "no_direct_reading_preference",
            "arms": arms, "note": "the hosted screen is still finished; unknown-location retrieval is separate",
            "margin": pins.S2_NONINFERIORITY_MARGIN}


def s3(*, context_gain: Mapping[str, Mapping[str, Any] | None],
       qwen_vs_hosted: Mapping[str, Any] | None) -> dict[str, Any]:
    """Cheap context: per hosted family, grouped minus singleton Complete
    Evidence@10; and the best Qwen contextual recipe minus the best hosted arm."""

    families: dict[str, Any] = {}
    escalate = []
    for family, result in sorted(context_gain.items()):
        if not result or result.get("difference") is None:
            families[family] = {"decision": "not_scored"}
            continue
        gain = float(result["difference"])
        low, high = result["ci95"]
        if gain < pins.S3_CONTEXT_GAIN_MIN:
            equivalent = -pins.S3_CONTEXT_GAIN_MIN < low and high < pins.S3_CONTEXT_GAIN_MIN
            families[family] = {"decision": "no_local_escalation", "gain": gain, "ci95": [low, high],
                                "claim": "context adds less than 3 points (equivalence supported)" if equivalent
                                else "insufficient evidence to expand"}
        else:
            families[family] = {"decision": "context_gain_supports_screen", "gain": gain, "ci95": [low, high]}
            escalate.append(family)
    qwen = None
    if qwen_vs_hosted and qwen_vs_hosted.get("difference") is not None:
        # difference = best hosted minus best Qwen contextual recipe.
        difference = float(qwen_vs_hosted["difference"])
        low, high = qwen_vs_hosted["ci95"]
        within = difference < pins.S3_QWEN_WITHIN
        qwen = {"difference": difference, "ci95": [low, high], "qwen_within_2_points": within,
                "claim": ("equivalence supported" if within and high < pins.S3_QWEN_WITHIN
                          else "insufficient evidence to expand" if within else "hosted ahead")}
    no_escalation = not escalate or bool(qwen and qwen["qwen_within_2_points"])
    return {"rule": "S3", "decision": "no_local_escalation" if no_escalation else "screen_supports_hosted_context",
            "families": families, "qwen_vs_best_hosted": qwen}


def s4(*, finalist_vs_one_model: Mapping[str, Any] | None, answer_gain: Mapping[str, Any] | None,
       latency_ok: bool | None, independent_families: int, exploratory: bool = False) -> dict[str, Any]:
    """Local experiment gate: the hosted finalist beats the best one-model arm
    by >= 5 points Complete Evidence@10 with a paired CI excluding 0, improves
    blind D1 answers, and no Reader latency regression. An underpowered pilot
    defers E1 until independent confirmation: ``independent_families`` are
    those of the complete-case PAIRED evidence, and an ``exploratory`` paired
    result (its own flag) defers too (fix round 4, Medium 14)."""

    reasons = []
    gain = None if not finalist_vs_one_model else finalist_vs_one_model.get("difference")
    lower = _lower(finalist_vs_one_model)
    if gain is None or gain < pins.S4_GAIN_MIN:
        reasons.append(f"gain {gain} < {pins.S4_GAIN_MIN}")
    if lower is None or lower <= 0:
        reasons.append("paired CI does not exclude 0")
    answer = None if not answer_gain else answer_gain.get("difference")
    if answer is None or answer <= 0:
        reasons.append("no blind D1 answer improvement")
    if latency_ok is None:
        reasons.append("Reader latency budget not pinned")
    elif not latency_ok:
        reasons.append("Reader latency regression")
    if reasons:
        decision = "no_e1"
    elif independent_families < pins.MIN_INDEPENDENT_FAMILIES or exploratory:
        decision = "defer_e1_underpowered"
        reasons.append(f"{independent_families} independent families in the paired evidence "
                       f"(minimum {pins.MIN_INDEPENDENT_FAMILIES})" + ("; exploratory" if exploratory else ""))
    else:
        decision = "consider_e1"
    return {"rule": "S4", "decision": decision, "reasons": reasons,
            "inputs": {"gain": gain, "lower_bound": lower, "answer_gain": answer, "latency_ok": latency_ok,
                       "independent_families": independent_families, "exploratory": exploratory}}


def decide(*, s1_inputs: Mapping[str, Any], s2_inputs: Mapping[str, Any], s3_inputs: Mapping[str, Any],
           s4_inputs: Mapping[str, Any]) -> dict[str, Any]:
    """All four rules. S1 stopping blocks every verdict below it (reported as blocked)."""

    first = s1(**s1_inputs)
    result: dict[str, Any] = {"S1": first, "production_adoption": "not_authorized_by_e0"}
    if first["decision"] == "stop_verdicts":
        for rule in ("S2", "S3", "S4"):
            result[rule] = {"rule": rule, "decision": "blocked_by_S1"}
        return result
    result["S2"] = s2(**s2_inputs)
    result["S3"] = s3(**s3_inputs)
    result["S4"] = s4(**s4_inputs)
    return result


def incomplete_rules() -> dict[str, Any]:
    """The rules for a run with no results yet (a dry run or a budget stop)."""

    return {rule: {"rule": rule, "decision": "not_computed_no_results"} for rule in ("S1", "S2", "S3", "S4")} | {
        "production_adoption": "not_authorized_by_e0"}


def summarize_decisions(decisions: Mapping[str, Any]) -> list[str]:
    lines = []
    for rule in ("S1", "S2", "S3", "S4"):
        entry = decisions.get(rule) or {}
        reasons = entry.get("reasons") or []
        lines.append(f"{rule}: {entry.get('decision')}" + (f" ({'; '.join(reasons)})" if reasons else ""))
    lines.append(f"Production adoption: {decisions.get('production_adoption')}")
    return lines


__all__: Sequence[str] = ("decide", "incomplete_rules", "s1", "s2", "s3", "s4", "summarize_decisions")
