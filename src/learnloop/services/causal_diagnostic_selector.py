"""EVSI-2 — the causal factor → formal-selector adapter, shadow-only.

Bridges one locked causal factor into :func:`evsi.rank_feasible` and persists a
shadow receipt carrying the decision-value spec's five §6.6 baselines beside the
live P2 verdict. Shadow has ZERO live authority (§3 invariant 2): the
orchestrator calls :func:`record_shadow_selection` inside its own try/except,
discards the return value for every live purpose, and nothing on a serving path
reads the shadow store.

The honesty rules this module exists to enforce:

- **No invented likelihoods.** There is no calibrated grader/instrument channel
  yet (arm A), so the only formal likelihood is the declared-emission noiseless
  partition (arm B) — an UPPER BOUND on realized EVSI, computable only when the
  factor's blind bundles use one uniform key schema and declare an ``H_OTHER``
  disposition. Structural separability alone (arm C) never becomes ``P(E|H)``;
  it may license a skip only through the EVPI bound, which needs no likelihood.
- **The open-set arm is excluded explicitly, never silently.** ``H_OTHER``
  carries prior mass but no declared emission and no repair route, so every
  computed arm here is *conditional on a concrete cause*, with the excluded
  mass stamped on the receipt (``conditional_scope``). This is the typed
  version of what :func:`evsi.evsi_for_conditionals` refuses to do silently.
- **Durations carry provenance.** Repair-class minutes are model self-reports
  (``authored_prior``), else the pooled attempt-latency median
  (``pooled_empirical`` — wall-clock, per the column's contract), else the
  fail-closed heuristic default. Expect ``authored_prior``/``heuristic_default``
  to dominate until latency volume accrues; the readiness report says so
  rather than letting a zero-divergence full-loss-vs-equal-cost finding read
  as meaningful.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import action_loss as AL
from learnloop.services import evsi as EV
from learnloop.services.causal_probe_coherence import (
    BLIND_INPUT_CONTRACT_VERSION,
    bundle_feature_row_report,
)
from learnloop.services.probe_hypotheses import H_OTHER

logger = logging.getLogger(__name__)

SHADOW_POLICY_VERSION = "causal_shadow_selection_v1"

#: §6.2 arms. ``arm_a_calibrated`` is reserved: no calibrated channel exists.
LIKELIHOOD_REGIMES = (
    "arm_a_calibrated",
    "arm_b_noiseless_partition",
    "arm_c_structural",
    "none",
)

#: The loss regime the shadow computes under today: the factor's own repair
#: classes routed 1:1 from its hypotheses, with provenance-stamped durations.
LOSS_TABLE_REGIME_SHADOW_V1 = "route_plus_provenance_stamped_minutes_v1"


def _stable_emission_key(values: Mapping[str, Any]) -> str:
    canonical = json.dumps(values, sort_keys=True, default=str)
    return "emission:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _unavailable(reason: str, detail: Sequence[str] = ()) -> dict[str, Any]:
    payload: dict[str, Any] = {"available": False, "reason": reason}
    if detail:
        payload["detail"] = [str(value) for value in detail]
    return payload


# ---------------------------------------------------------------------------
# Durations (estimator precedence, provenance-stamped).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Loss table over the factor's own repair classes.
# ---------------------------------------------------------------------------


def build_causal_loss_table(
    repository: Repository,
    *,
    repair_class_by_hypothesis: Mapping[str, str | None],
    duration_overrides: Mapping[str, float] | None = None,
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
        "regime": LOSS_TABLE_REGIME_SHADOW_V1,
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
        calibration_label="shadow_heuristic",
        scope="causal_factor",
    )
    meta["available"] = True
    meta["table_hash"] = table.table_hash
    return table, meta


# ---------------------------------------------------------------------------
# Likelihood arms (§6.2).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# The shadow computation itself.
# ---------------------------------------------------------------------------


def _conditional_concrete_prior(
    prior: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    """Strip the open-set arm EXPLICITLY, recording the excluded mass."""

    concrete = {
        str(key): max(float(value), 0.0)
        for key, value in prior.items()
        if str(key) != H_OTHER
    }
    excluded = max(float(prior.get(H_OTHER, 0.0) or 0.0), 0.0)
    total = sum(concrete.values())
    scope = {
        "basis": "conditional_on_concrete_hypotheses",
        "excluded": {H_OTHER: round(excluded, 6)},
    }
    if total <= 0:
        return {}, scope
    return {key: value / total for key, value in concrete.items()}, scope


def record_shadow_selection(
    repository: Repository,
    *,
    decision_receipt: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]] = (),
    chosen_candidate: Mapping[str, Any] | None = None,
    repair_class_by_hypothesis: Mapping[str, str | None] | None = None,
    common_repair_class_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Compute + persist the §6.6 baselines for one live probe decision.

    Returns the stored shadow receipt, or ``None`` when the live receipt
    already carries one. Raises nothing the caller must handle for the live
    path — the orchestrator wraps this in its own try/except regardless.
    """

    inputs = decision_receipt.get("inputs") or {}
    incumbent_decision = str(decision_receipt["decision"])
    incumbent_reason = str(decision_receipt.get("reason") or "")
    mapping = dict(repair_class_by_hypothesis or {})

    # --- prior --------------------------------------------------------------
    prior_block: dict[str, Any]
    prior_basis = None
    conditional_prior: dict[str, float] = {}
    conditional_scope: dict[str, Any] | None = None
    locked_set = None
    if chosen_candidate is not None and chosen_candidate.get("hypothesis_set_id"):
        locked_set = repository.fetch_hypothesis_set(
            str(chosen_candidate["hypothesis_set_id"])
        )
    if locked_set is not None:
        raw_prior = locked_set.get("prior") or {}
        prior_basis = (
            str(locked_set.get("prior_basis")) if locked_set.get("prior_basis") else None
        )
        conditional_prior, conditional_scope = _conditional_concrete_prior(raw_prior)
        prior_block = {
            "available": bool(conditional_prior),
            "prior": {k: round(v, 6) for k, v in sorted(conditional_prior.items())},
            "prior_basis": prior_basis,
            "live_value_eligible": prior_basis in EV.LIVE_VALUE_PRIOR_BASES,
            "conditional_scope": conditional_scope,
        }
        if not conditional_prior:
            prior_block["reason"] = "prior_mass_zero_after_open_set_exclusion"
    else:
        prior_block = _unavailable(
            "no_locked_hypothesis_set"
            if chosen_candidate is not None
            else "no_instrument"
        )

    # --- loss table ----------------------------------------------------------
    concrete_ids = sorted(conditional_prior) if conditional_prior else sorted(
        key for key in mapping if key != H_OTHER
    )
    scoped_mapping = {key: mapping.get(key) for key in concrete_ids}
    # The live targeting DROPS unmapped hypotheses from its repair-class map
    # (they ride the receipt's `unmapped_hypothesis_ids` instead), so the map
    # alone can look complete while the factor is not. Fold them back in as
    # unmappable — a hypothesis with no repair class must surface as the typed
    # `no_action_mapping` abstention, never vanish from the loss table.
    receipt_unmapped = [
        str(value) for value in inputs.get("unmapped_hypothesis_ids") or []
    ]
    for hypothesis_id in receipt_unmapped:
        scoped_mapping.setdefault(hypothesis_id, None)
    loss_table, loss_meta = (
        build_causal_loss_table(
            repository, repair_class_by_hypothesis=scoped_mapping
        )
        if scoped_mapping
        else (None, {"available": False, "reason": "no_hypotheses",
                     "regime": LOSS_TABLE_REGIME_SHADOW_V1})
    )

    # --- likelihood regime (classified on the candidate the live path chose) --
    regime, regime_detail, chosen_member = likelihood_regime_for_candidate(
        repository, chosen_candidate, concrete_hypothesis_ids=concrete_ids
    )

    probe_burden = float(inputs.get("probe_burden_minutes") or 0.0) or 1.5

    # --- baseline 2: formal EVSI (arm B only) ---------------------------------
    formal: dict[str, Any]
    rank_result = None
    if not conditional_prior:
        formal = _unavailable(str(prior_block.get("reason") or "no_prior"))
    elif loss_table is None:
        formal = _unavailable(
            str(loss_meta.get("reason") or "no_loss_table"),
            loss_meta.get("unmapped_hypothesis_ids") or (),
        )
    elif regime != "arm_b_noiseless_partition":
        formal = _unavailable(
            "incomplete_likelihoods",
            [str(regime_detail.get("reason") or regime)],
        )
    else:
        diagnostic_candidates = []
        for value in [chosen_candidate, *[c for c in candidates if c is not chosen_candidate]]:
            if value is None:
                continue
            c_regime, c_detail, c_member = (
                (regime, regime_detail, chosen_member)
                if value is chosen_candidate
                else likelihood_regime_for_candidate(
                    repository, value, concrete_hypothesis_ids=concrete_ids
                )
            )
            if c_regime != "arm_b_noiseless_partition" or c_member is None:
                continue
            diagnostic_candidates.append(
                EV.DiagnosticCandidate(
                    ref=str(value["id"]),
                    members=(c_member,),
                    prior=conditional_prior,
                    expected_minutes=probe_burden,
                    burden_minutes=0.0,
                    prior_basis=prior_basis,
                )
            )
        rank_result = EV.rank_feasible(diagnostic_candidates, loss_table)
        formal = {
            "available": True,
            # A declared-emission partition is the NOISELESS channel: exact for
            # it, an upper bound once response/grader noise exists (§6.2 arm B).
            # It may license a skip; a 'measure' verdict from it is recorded,
            # never served — shadow has no live authority anyway.
            "noiseless_upper_bound": True,
            "conditional_scope": conditional_scope,
            "rank": rank_result.as_dict(),
        }

    # --- baseline 3: equal-cost / modal-route ---------------------------------
    if conditional_prior and loss_table is not None and chosen_member is not None:
        pooled_seconds, _pooled_n = repository.median_attempt_latency_seconds()
        uniform_minutes = (
            float(pooled_seconds) / 60.0
            if pooled_seconds is not None
            else AL.DEFAULT_INTERVENTION_MINUTES
        )
        equal_table, _equal_meta = build_causal_loss_table(
            repository,
            repair_class_by_hypothesis=scoped_mapping,
            duration_overrides={
                action: uniform_minutes for action in loss_table.actions
            },
        )
        try:
            if equal_table is None:
                raise EV.EVSIInputError("incomplete_loss_table")
            member_result = EV.evsi_for_conditionals(
                chosen_member, conditional_prior, equal_table
            )
            equal_cost = {
                "available": True,
                "evsi_minutes": round(member_result.evsi, 6),
                "selected_action": member_result.current_action,
                "uniform_minutes": round(uniform_minutes, 6),
                "conditional_scope": conditional_scope,
            }
        except EV.EVSIInputError as error:
            equal_cost = _unavailable(error.reason, error.detail)
    elif conditional_prior and loss_table is not None:
        equal_cost = _unavailable(
            "incomplete_likelihoods", [str(regime_detail.get("reason") or regime)]
        )
    else:
        equal_cost = _unavailable(
            str((prior_block if not conditional_prior else loss_meta).get("reason")
                or "no_inputs")
        )

    # --- baseline 4: EVPI skip bound (no likelihood needed) -------------------
    if conditional_prior and loss_table is not None:
        try:
            current_action = loss_table.argmin_action(conditional_prior)
            current_loss = loss_table.expected_loss(current_action, conditional_prior)
            # Perfect information reaches each hypothesis's effective route,
            # whose loss is 0 by construction — EVPI == current expected loss.
            evpi = {
                "available": True,
                "evpi_minutes": round(current_loss, 6),
                "current_action": current_action,
                "skip_licensed": current_loss <= probe_burden,
                "burden_minutes": probe_burden,
                "conditional_scope": conditional_scope,
            }
        except (AL.LossTableIncompleteError, EV.EVSIInputError) as error:
            evpi = _unavailable(getattr(error, "reason", "loss_error"),
                                getattr(error, "detail", ()))
    else:
        evpi = _unavailable(
            str((prior_block if not conditional_prior else loss_meta).get("reason")
                or "no_inputs")
        )

    # --- baseline 5: no-measure / common repair -------------------------------
    repair_class_ids = [str(v) for v in decision_receipt.get("repair_class_ids") or []]
    no_measure = {
        "available": True,
        "common_repair_covers": bool(inputs.get("common_repair_covers")),
        "action_equivalent": len(set(repair_class_ids)) <= 1,
        "common_repair_class_id": common_repair_class_id,
    }

    baselines = {
        "p2_incumbent": {
            "available": True,
            "decision": incumbent_decision,
            "reason": incumbent_reason,
        },
        "formal_evsi": formal,
        "equal_cost_modal_route": equal_cost,
        "evpi_skip_bound": evpi,
        "no_measure_common_repair": no_measure,
    }

    # --- verdict + would_change flags -----------------------------------------
    if formal.get("available"):
        shadow_verdict = str(rank_result.verdict) if rank_result is not None else "unavailable"
    elif evpi.get("available") and evpi.get("skip_licensed"):
        # Arm C's only licensed claim: even perfect information is worth less
        # than the burden, so skipping is safe without any likelihood model.
        shadow_verdict = "stop"
    else:
        shadow_verdict = "unavailable"

    incumbent_measures = incumbent_decision == "probe_now"
    would_change_measure: bool | None = None
    if shadow_verdict in ("measure", "stop"):
        would_change_measure = (shadow_verdict == "measure") != incumbent_measures

    would_change_candidate: bool | None = None
    if (
        formal.get("available")
        and rank_result is not None
        and rank_result.best_ref is not None
        and chosen_candidate is not None
    ):
        would_change_candidate = rank_result.best_ref != str(chosen_candidate["id"])

    would_change_repair: bool | None = None
    if evpi.get("available") and common_repair_class_id:
        would_change_repair = evpi.get("current_action") != common_repair_class_id

    body = {
        "shadow_policy_version": SHADOW_POLICY_VERSION,
        "prior": prior_block,
        "loss_table": {
            **loss_meta,
            **({"table": loss_table.as_dict()} if loss_table is not None else {}),
        },
        "likelihood": {"regime": regime, **regime_detail},
        "candidate_ids_considered": [str(v["id"]) for v in candidates if v],
        "chosen_candidate_id": (
            str(chosen_candidate["id"]) if chosen_candidate is not None else None
        ),
        "probe_burden_minutes": probe_burden,
    }

    return repository.insert_causal_shadow_selection_receipt(
        decision_receipt_id=str(decision_receipt["id"]),
        factor_id=str(decision_receipt["factor_id"]),
        incumbent_decision=incumbent_decision,
        incumbent_reason=incumbent_reason,
        shadow_verdict=shadow_verdict,
        likelihood_regime=regime,
        loss_table_regime=LOSS_TABLE_REGIME_SHADOW_V1,
        baselines=baselines,
        body=body,
        shadow_policy_version=SHADOW_POLICY_VERSION,
        prior_basis=prior_basis,
        learning_object_id=(
            str(decision_receipt.get("learning_object_id"))
            if decision_receipt.get("learning_object_id")
            else None
        ),
        attempt_id=(
            str(decision_receipt.get("attempt_id"))
            if decision_receipt.get("attempt_id")
            else None
        ),
        candidate_id=(
            str(chosen_candidate["id"]) if chosen_candidate is not None else None
        ),
        would_change_candidate=would_change_candidate,
        would_change_measure_vs_repair=would_change_measure,
        would_change_repair=would_change_repair,
        clock=clock,
    )
