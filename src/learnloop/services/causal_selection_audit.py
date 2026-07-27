"""EVSI-2 — the causal-selection readiness report (decision-value spec WP0/§8 Stage 0).

Answers, with measured denominators, whether the formal selector could change
any decision on this vault yet: candidate multiplicity, likelihood-regime
availability, duration-source shares, shadow conversion counts, and
repair-linked cold-outcome volume. Every empty denominator is a typed
unavailable arm — the report never renders a favorable zero (spec §10.3).

The expectations note is part of the report by design: with bijective
hypothesis→repair routes and one pooled/default duration, the full-loss and
equal-cost EVSI baselines are PROVABLY identical, so a zero-divergence count is
a statement about missing duration data, not about the loss model's value.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.causal_diagnostic_selector import (
    duration_estimates_for_repair_classes,
    likelihood_regime_for_candidate,
)
from learnloop.services.causal_probe_coherence import (
    candidate_has_current_blind_input_contract,
    order_probe_candidates,
)
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.vault.models import LoadedVault

READINESS_REPORT_VERSION = "causal_selection_readiness_v1"

#: §6.2 expectation, stated rather than implied by a zero: full-loss vs
#: equal-cost divergence requires per-intervention durations that differ.
EXPECTATIONS_NOTE = (
    "full-loss and equal-cost EVSI are provably identical until "
    "per-intervention durations exist and differ (routes are 1:1 and every "
    "action currently shares one pooled/authored/default minute estimate); a "
    "zero divergence count below is missing-duration data, not evidence that "
    "repair-specific costs carry no decision information"
)


def _unavailable(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def _concrete_hypothesis_ids(factor: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for value in factor.get("candidate_causes") or []:
        if not isinstance(value, dict):
            continue
        if value.get("open_set") or value.get("hypothesis_id") in (None, "H_OTHER", H_OTHER):
            continue
        ids.append(str(value["hypothesis_id"]))
    return sorted(set(ids))


def causal_selection_readiness(
    vault: LoadedVault | None, repository: Repository
) -> dict[str, Any]:
    """The WP0 readiness report over one vault. Read-only; no provider calls."""

    factors = repository.unresolved_cause_factors(status=None)
    open_factors = [f for f in factors if f.get("status") == "open"]

    # --- candidate multiplicity (0 / 1 / 2+), policy v3 makes 2 reachable ----
    multiplicity = Counter()
    regimes: Counter = Counter()
    repair_class_ids: set[str] = set()
    for factor in open_factors:
        candidates = order_probe_candidates(
            [
                value
                for value in repository.causal_probe_candidates_for_factor(
                    str(factor["id"])
                )
                if candidate_has_current_blind_input_contract(value)
                and value.get("status") != "rejected"
            ]
        )
        bucket = "2+" if len(candidates) >= 2 else str(len(candidates))
        multiplicity[bucket] += 1
        concrete = _concrete_hypothesis_ids(factor)
        if candidates:
            regime, _detail, _member = likelihood_regime_for_candidate(
                repository, candidates[0], concrete_hypothesis_ids=concrete
            )
            regimes[regime] += 1
        else:
            regimes["none"] += 1
    # The durable repair-class store is the action vocabulary the shadow loss
    # table prices in; duration readiness is measured over all of it.
    repair_class_ids = set(repository.causal_repair_class_definitions())

    # --- duration source shares ----------------------------------------------
    pooled_seconds, pooled_n = repository.median_attempt_latency_seconds()
    duration_block: dict[str, Any]
    if repair_class_ids:
        estimates = duration_estimates_for_repair_classes(
            repository, sorted(repair_class_ids)
        )
        source_counts = Counter(value["source"] for value in estimates.values())
        distinct_minutes = {round(value["minutes"], 6) for value in estimates.values()}
        duration_block = {
            "available": True,
            "repair_classes": len(estimates),
            "source_counts": dict(sorted(source_counts.items())),
            "distinct_minute_values": len(distinct_minutes),
            "pooled_latency": {
                "median_seconds": pooled_seconds,
                "sample_count": pooled_n,
            },
        }
    else:
        duration_block = {
            **_unavailable("no_repair_classes"),
            "pooled_latency": {
                "median_seconds": pooled_seconds,
                "sample_count": pooled_n,
            },
        }

    # --- shadow conversion counts (§9.2 denominators) --------------------------
    shadows = repository.causal_shadow_selection_receipts(limit=5000)
    if shadows:
        formal_available = [
            s for s in shadows if (s.get("baselines") or {}).get("formal_evsi", {}).get("available")
        ]
        divergence = [
            s
            for s in formal_available
            if (s.get("baselines") or {}).get("formal_evsi", {}).get("available")
            and (s.get("baselines") or {}).get("equal_cost_modal_route", {}).get("available")
        ]
        full_vs_equal_diverged = 0
        for s in divergence:
            formal = s["baselines"]["formal_evsi"]
            equal = s["baselines"]["equal_cost_modal_route"]
            ranked = (formal.get("rank") or {}).get("ranked") or []
            formal_point = ranked[0]["evsi"]["point"] if ranked else None
            if formal_point is not None and equal.get("evsi_minutes") is not None:
                if abs(float(formal_point) - float(equal["evsi_minutes"])) > 1e-9:
                    full_vs_equal_diverged += 1
        shadow_block = {
            "available": True,
            "receipts": len(shadows),
            "by_incumbent_decision": dict(
                sorted(Counter(str(s["incumbent_decision"]) for s in shadows).items())
            ),
            "by_shadow_verdict": dict(
                sorted(Counter(str(s["shadow_verdict"]) for s in shadows).items())
            ),
            "by_likelihood_regime": dict(
                sorted(Counter(str(s["likelihood_regime"]) for s in shadows).items())
            ),
            "formal_arm_available": len(formal_available),
            "would_change_measure_vs_repair": sum(
                1 for s in shadows if s.get("would_change_measure_vs_repair") is True
            ),
            "would_change_candidate": sum(
                1 for s in shadows if s.get("would_change_candidate") is True
            ),
            "would_change_repair": sum(
                1 for s in shadows if s.get("would_change_repair") is True
            ),
            "full_vs_equal_cost_comparable": len(divergence),
            "full_vs_equal_cost_diverged": full_vs_equal_diverged,
        }
    else:
        shadow_block = _unavailable("no_shadow_receipts")

    # --- repair-linked cold outcomes (migration 145) ---------------------------
    cold = repository.causal_cold_outcomes()
    if cold:
        cold_block = {
            "available": True,
            "outcomes": dict(
                sorted(Counter(str(row["outcome"]) for row in cold).items())
            ),
            "training_eligible": sum(
                1 for row in cold if row["outcome"] in ("cold_success", "cold_failure")
            ),
        }
    else:
        cold_block = _unavailable("no_cold_outcomes")

    return {
        "version": READINESS_REPORT_VERSION,
        "factors": {
            "total": len(factors),
            "open": len(open_factors),
        },
        "candidate_multiplicity": (
            {
                "available": True,
                "counts": {
                    "0": multiplicity.get("0", 0),
                    "1": multiplicity.get("1", 0),
                    "2+": multiplicity.get("2+", 0),
                },
            }
            if open_factors
            else _unavailable("no_open_factors")
        ),
        "likelihood_regimes": (
            {"available": True, "counts": dict(sorted(regimes.items()))}
            if open_factors
            else _unavailable("no_open_factors")
        ),
        "duration_sources": duration_block,
        "shadow_conversions": shadow_block,
        "cold_outcomes": cold_block,
        "findings": [
            {
                "kind": "unregistered_decision_parameter",
                "parameter": "causal_probe_commissioning:MAX_CANDIDATES_PER_FACTOR",
                "note": (
                    "the multiplicity cap is documented in-module but not in the "
                    "parameter registry; no causal-lane module constant is — "
                    "deciding the registration convention is a readiness output, "
                    "not something this report resolves"
                ),
            }
        ],
        "expectations_note": EXPECTATIONS_NOTE,
    }
