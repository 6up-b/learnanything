"""Causal loss tables and likelihood regimes for instructional valuation.

Repair-class durations retain their provenance. A noiseless likelihood requires
uniform declared emissions and an explicit open-set disposition; structural
separability alone does not supply a likelihood.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from learnloop.db.repositories import Repository
from learnloop.scheduling import action_loss as AL
from learnloop.diagnosis.causal_probe_coherence import (
    BLIND_INPUT_CONTRACT_VERSION,
    bundle_feature_row_report,
)

# These names and values feed persisted loss-table identities in live valuation.
LOSS_TABLE_REGIME_SHADOW_V1 = "route_plus_provenance_stamped_minutes_v1"
LOSS_TABLE_REGIME_MEASURED_V1 = "route_plus_measured_unresolved_minutes_v1"


def _stable_emission_key(values: Mapping[str, Any]) -> str:
    canonical = json.dumps(values, sort_keys=True, default=str)
    return "emission:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def duration_estimates_for_repair_classes(
    repository: Repository,
    repair_class_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """Minutes per repair class with an honest source label.

    Precedence: the class definition's model-reported ``expected_minutes``
    (``authored_prior``) → the pooled attempt-latency median
    (``pooled_empirical``) → :data:`action_loss.DEFAULT_INTERVENTION_MINUTES`
    (``heuristic_default``). A repair-class *empirical* estimate would need
    completed remediation episodes tagged by class, which do not exist yet;
    when they do, they slot in ahead of ``authored_prior``.
    """

    wanted = [str(value) for value in repair_class_ids if value]
    definitions = repository.causal_repair_class_definitions(wanted)
    pooled_seconds, pooled_n = repository.median_attempt_latency_seconds()
    estimates: dict[str, dict[str, Any]] = {}
    for repair_class_id in wanted:
        definition = definitions.get(repair_class_id) or {}
        authored = definition.get("expected_minutes")
        if isinstance(authored, (int, float)) and not isinstance(authored, bool) and authored > 0:
            estimates[repair_class_id] = {
                "minutes": float(authored),
                "source": "authored_prior",
                "sample_count": 0,
            }
        elif pooled_seconds is not None:
            estimates[repair_class_id] = {
                "minutes": float(pooled_seconds) / 60.0,
                "source": "pooled_empirical",
                "sample_count": pooled_n,
            }
        else:
            estimates[repair_class_id] = {
                "minutes": AL.DEFAULT_INTERVENTION_MINUTES,
                "source": "heuristic_default",
                "sample_count": 0,
            }
    return estimates


def build_causal_loss_table(
    repository: Repository,
    *,
    repair_class_by_hypothesis: Mapping[str, str | None],
    duration_overrides: Mapping[str, float] | None = None,
    unresolved_minutes: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[AL.LossTable | None, dict[str, Any]]:
    """L(hypothesis, repair_class) for the factor's concrete hypotheses.

    The action-vocabulary gap is real: causal repair classes and
    ``failure_triage_routes.first_intervention`` are disjoint vocabularies, so
    the shadow prices decisions in the factor's OWN repair classes and
    type-abstains (``no_action_mapping``) for any hypothesis without one —
    never inventing a route.
    """

    unmapped = sorted(
        hypothesis
        for hypothesis, repair_class in repair_class_by_hypothesis.items()
        if not repair_class
    )
    mapped = {
        hypothesis: str(repair_class)
        for hypothesis, repair_class in repair_class_by_hypothesis.items()
        if repair_class
    }
    meta: dict[str, Any] = {
        "regime": LOSS_TABLE_REGIME_MEASURED_V1 if unresolved_minutes else LOSS_TABLE_REGIME_SHADOW_V1,
        "unmapped_hypothesis_ids": unmapped,
    }
    if unmapped or not mapped:
        meta["available"] = False
        meta["reason"] = "no_action_mapping" if unmapped else "no_hypotheses"
        return None, meta

    repair_classes = sorted(set(mapped.values()))
    if duration_overrides is None:
        estimates = duration_estimates_for_repair_classes(repository, repair_classes)
        overrides = {key: value["minutes"] for key, value in estimates.items()}
        meta["duration_estimates"] = estimates
    else:
        overrides = {key: float(value) for key, value in duration_overrides.items()}
        meta["duration_estimates"] = {
            key: {"minutes": value, "source": "override", "sample_count": 0}
            for key, value in overrides.items()
        }
    routes = [
        {"reason": hypothesis, "first_intervention": mapped[hypothesis]}
        for hypothesis in sorted(mapped)
    ]
    table = AL.build_loss_table(
        routes=routes,
        duration_overrides=overrides,
        calibration_label="shadow_measured_unresolved" if unresolved_minutes else "shadow_heuristic",
        scope="causal_factor",
        unresolved_minutes=(
            {h: v for h, v in unresolved_minutes.items() if h in mapped} if unresolved_minutes else None
        ),
    )
    meta["available"] = True
    meta["table_hash"] = table.table_hash
    return table, meta


def likelihood_regime_for_candidate(
    repository: Repository,
    candidate: Mapping[str, Any] | None,
    *,
    concrete_hypothesis_ids: Sequence[str],
) -> tuple[str, dict[str, Any], dict[str, dict[str, float]] | None]:
    """Classify the §6.2 arm and, for arm B, build the noiseless member.

    Arm B requires: every concrete hypothesis has exactly one usable declared
    row, every row shares one identical key schema, and some bundle declares an
    ``H_OTHER`` disposition (the open-set arm is excluded *formally*, never by
    omission). Anything else is arm C — a structural audit, not a likelihood.
    """

    if candidate is None:
        return "none", {"reason": "no_instrument"}, None
    wanted = sorted({str(value) for value in concrete_hypothesis_ids})
    bundles = repository.causal_blind_prediction_bundles(
        practice_item_id=str(candidate["practice_item_id"]),
        hypothesis_ids=wanted,
    )
    latest: dict[str, Mapping[str, Any]] = {}
    for bundle in bundles:
        if not bundle.get("generated_without_observation"):
            continue
        if bundle.get("blind_input_contract_version") != BLIND_INPUT_CONTRACT_VERSION:
            continue
        latest[str(bundle["hypothesis_id"])] = bundle

    detail: dict[str, Any] = {"hypothesis_ids": wanted}
    missing = [value for value in wanted if value not in latest]
    if missing:
        detail["reason"] = "missing_blind_bundles"
        detail["missing_hypothesis_ids"] = missing
        return "arm_c_structural", detail, None

    rows_by_hypothesis: dict[str, list] = {}
    open_set_declared = False
    for hypothesis_id in wanted:
        predictions = latest[hypothesis_id].get("predictions") or {}
        if isinstance(predictions, Mapping) and predictions.get("open_set_disposition"):
            open_set_declared = True
        report = bundle_feature_row_report(
            predictions if isinstance(predictions, Mapping) else None
        )
        rows_by_hypothesis[hypothesis_id] = list(report.rows)

    single_rowed = all(len(rows) == 1 for rows in rows_by_hypothesis.values())
    key_schemas = {
        rows[0].keys for rows in rows_by_hypothesis.values() if len(rows) == 1
    }
    uniform_keys = single_rowed and len(key_schemas) == 1
    if not (single_rowed and uniform_keys and open_set_declared):
        reasons = []
        if not single_rowed:
            reasons.append("multiple_or_missing_rows")
        if single_rowed and not uniform_keys:
            reasons.append("non_uniform_key_schema")
        if not open_set_declared:
            reasons.append("no_h_other_disposition")
        detail["reason"] = "+".join(reasons) or "not_partitionable"
        return "arm_c_structural", detail, None

    member: dict[str, dict[str, float]] = {}
    emissions: dict[str, str] = {}
    for hypothesis_id, rows in rows_by_hypothesis.items():
        key = _stable_emission_key(rows[0].values)
        emissions[hypothesis_id] = key
        member[hypothesis_id] = {key: 1.0}
    if len(set(emissions.values())) < len(emissions):
        # Two hypotheses declaring an identical emission cannot be partitioned;
        # the noiseless channel would be lying about separability.
        detail["reason"] = "identical_declared_emissions"
        return "arm_c_structural", detail, None
    detail["emission_keys"] = emissions
    detail["key_schema"] = sorted(next(iter(key_schemas)))
    return "arm_b_noiseless_partition", detail, member
