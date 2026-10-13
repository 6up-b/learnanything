"""EVSI calibration Part B: forecasts of the diagnosis-side VOI decisions.

Three live decisions pick a check by information value without going through
``evsi.rank_feasible``; each records its forecast through
:func:`learnloop.scheduling.voi_forecasts.record_forecast`:

* **probe selection** (a committed probe presentation): the instrument's
  grader-composed conditionals over the episode labels, under the
  selection-time posterior the presentation froze;
* **robust probe selection** (the mvp-0.8 stop/abstain gate,
  :func:`probe_robust.robust_selection`): the EIG path's verdict, its robust
  EIG and the minutes value ``VALUE_PER_NAT_MINUTES`` puts on it;
* **follow-up selection**: the chosen item's facet conditionals over the
  primary facet's hypothesis marginal.

For the probe paths the "action" is the first intervention of the most
probable hypothesis's triage route (``action_proxy: triage_route_of_map``),
or the most probable label itself when a label has no active route
(``map_hypothesis``). Logging only: every function returns quietly on any
failure and changes nothing the decision does.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis import robust_composition as rc
from learnloop.diagnosis.probes import facet_conditional_distribution, resolve_item_irt
from learnloop.learner.facet_diagnostics import candidate_facet_support
from learnloop.diagnosis.probe_families import (
    GRADER_CHANNEL_RELIABILITY,
    ORDINAL_VOCABULARY,
    SELECTION_POLICY_VERSION,
    CompiledInstrument,
    instrument_conditionals,
)
from learnloop.scheduling import voi_forecasts as VF

logger = logging.getLogger(__name__)


def _route_action_of(
    repository: Repository, labels: Sequence[str]
) -> tuple[Callable[[Mapping[str, float]], str | None], str]:
    from learnloop.diagnosis.probe_hypotheses import triage_reason_for_label

    routes: dict[str, str] = {}
    for label in labels:
        route = repository.failure_triage_route_for_reason(triage_reason_for_label(label))
        first = (route or {}).get("first_intervention") if route and route.get("active", True) else None
        if first:
            routes[label] = str(first)
    proxy = "triage_route_of_map" if len(routes) == len(labels) and labels else "map_hypothesis"

    def action_of(belief: Mapping[str, float]) -> str | None:
        if not belief:
            return None
        top = max(sorted(belief), key=lambda h: belief[h])
        return routes.get(top, top) if proxy == "triage_route_of_map" else top

    return action_of, proxy


def _vocabulary_parameters(instrument: CompiledInstrument) -> list[dict[str, Any]]:
    out = [
        VF.parameter("probe_families.ORDINAL_VOCABULARY", dict(ORDINAL_VOCABULARY), "heuristic",
                     source="authored_prior", note="ordinal words -> probabilities, never fitted"),
        VF.parameter("instrument.pseudo_count", instrument.pseudo_count, "heuristic", source="authored_prior"),
        VF.parameter("instrument.expected_seconds", instrument.expected_seconds, "heuristic",
                     source="authored_prior"),
        VF.parameter("probe_families.GRADER_CHANNEL_RELIABILITY",
                     GRADER_CHANNEL_RELIABILITY.get(instrument.grader_policy, 0.9), "heuristic",
                     source="registry:heuristic"),
    ]
    if instrument.provenance != "instrument_card":
        out.append(VF.parameter("instrument.provenance", instrument.provenance, "heuristic",
                                source="legacy_fallback"))
    return out


def record_probe_presentation_forecast(
    vault: Any,
    repository: Repository,
    presentation: Any,
    *,
    learning_object_id: str | None = None,
    candidate_count: int | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Forecast of one committed probe presentation (site ``probe_selection``)."""

    try:
        snapshot = presentation.instrument_card_snapshot
        if not snapshot:
            return None
        instrument = CompiledInstrument.from_snapshot(snapshot)
        slot_map = dict(snapshot.get("resolved_slot_map") or {})
        belief = {k: float(v) for k, v in dict(presentation.posterior_at_selection or {}).items()}
        conditionals = instrument_conditionals(instrument)
        likelihood = {label: dict(conditionals[slot]) for label, slot in slot_map.items()
                      if label in belief and slot in conditionals}
        if not likelihood:
            return None
        action_of, proxy = _route_action_of(repository, sorted(likelihood))
        body = VF.forecast_block(likelihood, belief, action_of=action_of, action_proxy=proxy)
        components = dict(presentation.selection_components or {})
        body["selection"] = {
            key: components.get(key)
            for key in ("selection_objective", "expected_information_gain", "predictive_eig",
                        "predictive_information_rate", "redundancy_penalty", "expected_seconds")
            if key in components
        }
        if components.get("channel_pin"):
            body["channel_pin"] = components["channel_pin"]
        body["presentation_eig_nats"] = presentation.expected_information_gain
        probe = vault.config.probe
        parameters = [
            *_vocabulary_parameters(instrument),
            VF.parameter("probe.episode.selection_overhead_seconds",
                         probe.episode.selection_overhead_seconds, "heuristic", source="config"),
            VF.parameter("probe.block.family_redundancy_penalty",
                         probe.block.family_redundancy_penalty, "heuristic", source="config"),
            VF.parameter("probe.episode.posterior_stop_threshold",
                         probe.episode.posterior_stop_threshold, "heuristic", source="config"),
            VF.parameter("probe.episode.maximum_observations",
                         probe.episode.maximum_observations, "heuristic", source="config"),
        ]
        return VF.record_forecast(
            repository,
            vault=vault,
            site="probe_selection",
            receipt_key=f"probe_selection:{presentation.id}",
            verdict="measure",
            forecast=body,
            parameters=parameters,
            versions={
                "selection_policy_version": presentation.selection_policy_version or SELECTION_POLICY_VERSION,
                "compiled_likelihood_hash": snapshot.get("compiled_likelihood_hash"),
            },
            candidate_count=int(candidate_count or 0),
            clock=clock,
            decision_ref=presentation.id,
            learning_object_id=learning_object_id,
            probe_episode_id=presentation.probe_episode_id,
            presentation_id=presentation.id,
            chosen_ref=presentation.practice_item_id,
            chosen_practice_item_id=presentation.practice_item_id,
            scheduler_candidate_id=presentation.scheduler_candidate_id,
            eig_nats=(
                float(presentation.expected_information_gain)
                if presentation.expected_information_gain is not None else body.get("eig_nats")
            ),
        )
    except Exception:  # noqa: BLE001 - logging must never break a decision
        logger.warning("probe presentation forecast not recorded", exc_info=True)
        return None


def record_robust_selection_forecast(
    vault: Any,
    repository: Repository,
    *,
    episode: Any,
    decision: rc.RobustDecision,
    candidates: Sequence[Any],
    ensembles: Mapping[str, rc.Ensemble] | None,
    posterior: Mapping[str, float],
    observations: int,
    clock: Clock | None = None,
) -> str | None:
    """Forecast of the robust stop/abstain gate (site ``probe_robust_selection``).

    ``candidates`` are the ``RobustCandidate`` slate. ``ensembles`` maps a
    candidate id to its built ensemble when the caller has it; the chosen
    candidate's mean member is the forecast likelihood.
    """

    try:
        belief = {k: float(v) for k, v in posterior.items()}
        chosen = decision.chosen_slot
        body: dict[str, Any] = {
            "verdict": decision.verdict,
            "should_stop": decision.should_stop,
            "abstained": decision.abstained,
            "robust_eig_per_second": round(decision.robust_eig_per_second, 8),
            "lcb_advantage_over_runner_up": round(decision.lcb_advantage_over_runner_up, 8),
            "action_agreement_fraction": round(decision.action_agreement_fraction, 6),
            "observations_so_far": observations,
        }
        eig = None
        evsi_minutes = None
        by_id = {c.identifier: c for c in candidates}
        if chosen is not None and ensembles and chosen in ensembles:
            ensemble = ensembles[chosen]
            labels = sorted(h for h in belief if h in ensemble.mean_member)
            action_of, proxy = _route_action_of(repository, labels)
            body.update(VF.forecast_block(ensemble.mean_member, belief, action_of=action_of, action_proxy=proxy))
            eig_series = [rc.expected_information_gain(member, belief) for member in ensemble.members]
            robust_eig = rc.robust_quantile(eig_series, ensemble.quantile)
            evsi_minutes = rc.VALUE_PER_NAT_MINUTES * robust_eig
            eig = eig_series[0]
            seconds = float(by_id[chosen].expected_seconds) if chosen in by_id else None
            body["robust_eig_nats"] = round(robust_eig, 8)
            body["evsi_from_eig_minutes"] = round(evsi_minutes, 8)
            body["stop_threshold_minutes"] = (
                round(rc.LAMBDA_TIME * seconds / 60.0 + rc.BURDEN_COST, 8) if seconds is not None else None
            )
        parameters = [
            VF.parameter("robust_composition.VALUE_PER_NAT_MINUTES", rc.VALUE_PER_NAT_MINUTES, "heuristic",
                         source="registry:heuristic", note="minutes per nat of the EIG path's stop rule"),
            VF.parameter("robust_composition.ROBUST_QUANTILE", rc.ROBUST_QUANTILE, "heuristic",
                         source="registry:heuristic"),
            VF.parameter("robust_composition.ROBUST_DRAW_COUNT", rc.ROBUST_DRAW_COUNT, "heuristic",
                         source="registry:heuristic"),
            VF.parameter("robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION",
                         rc.INSTRUMENT_PERTURBATION_CONCENTRATION, "heuristic", source="registry:heuristic"),
            VF.parameter("robust_composition.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD",
                         rc.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD, "heuristic", source="registry:heuristic"),
            VF.parameter("robust_composition.LAMBDA_TIME", rc.LAMBDA_TIME, "structural",
                         source="minutes numeraire (U-023)"),
            VF.parameter("robust_composition.BURDEN_COST", rc.BURDEN_COST, "heuristic",
                         source="registry:heuristic"),
            VF.parameter("probe_families.ORDINAL_VOCABULARY", dict(ORDINAL_VOCABULARY), "heuristic",
                         source="authored_prior"),
            VF.parameter("grader channel", getattr(episode, "calibration_model_hash", None),
                         "measured", source="pinned calibration model (Dirichlet counts)"),
        ]
        chosen_candidate = by_id.get(chosen) if chosen is not None else None
        return VF.record_forecast(
            repository,
            vault=vault,
            site="probe_robust_selection",
            receipt_key=f"probe_robust_selection:{episode.id}:{observations}:{chosen or 'none'}",
            verdict=decision.verdict,
            forecast=body,
            parameters=parameters,
            versions={"calibration_model_hash": getattr(episode, "calibration_model_hash", None),
                      "algorithm_version": getattr(episode, "algorithm_version", None)},
            candidate_count=len(candidates),
            clock=clock,
            decision_ref=episode.id,
            learning_object_id=getattr(episode, "learning_object_id", None),
            probe_episode_id=episode.id,
            chosen_ref=chosen,
            chosen_practice_item_id=chosen_candidate.identifier if chosen_candidate is not None else None,
            eig_nats=eig,
            evsi_point_minutes=evsi_minutes,
            evsi_lcb_minutes=evsi_minutes,
        )
    except Exception:  # noqa: BLE001
        logger.warning("robust selection forecast not recorded", exc_info=True)
        return None


def record_followup_forecast(
    vault: Any,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    selection: Any,
    clock: Clock | None = None,
) -> str | None:
    """Forecast of a queued follow-up (site ``followup_selection``)."""

    try:
        candidate = selection.candidate
        if candidate is None:
            return None
        row = next((r for r in selection.slate if r.get("practice_item_id") == candidate.id), None)
        if row is None:
            return None
        body: dict[str, Any] = {
            "rank_score": row.get("rank_score"),
            "total_facet_eig": row.get("total_facet_eig"),
            "total_predictive_eig": row.get("total_predictive_eig"),
            "facet_eig_by_facet": row.get("facet_eig_by_facet"),
            "predictive_eig_by_facet": row.get("predictive_eig_by_facet"),
            "misconception_eig": row.get("misconception_eig"),
            "eligible_slate_size": selection.eligible_slate_size,
        }
        focus = selection.diagnostic_focus or {}
        facet = focus.get("primary_target_facet") or selection.dominant_target_facet
        marginal = (focus.get("target_facet_marginals") or {}).get(facet) if facet else None
        eig = None
        if facet and marginal:
            item_a, item_b, irt = resolve_item_irt(vault, candidate)
            rubric = vault.rubric_for_item(candidate)
            fatal = {fe.id for fe in rubric.fatal_errors} if rubric is not None else set()
            support = set(candidate_facet_support(candidate))
            known = sorted(label.split(":", 1)[1] for label in marginal if label.startswith("misconception:"))
            likelihood = {
                label: {
                    f"{bucket}|{error or ''}": p
                    for (bucket, error), p in facet_conditional_distribution(
                        label, facet_id=facet, candidate_facet_support=support, fatal_error_ids=fatal,
                        known_error_types=known, item_a=item_a, item_b=item_b, irt=irt,
                    ).items()
                }
                for label in marginal
            }

            def action_of(belief: Mapping[str, float]) -> str | None:
                return max(sorted(belief), key=lambda h: belief[h]) if belief else None

            body.update(VF.forecast_block(likelihood, marginal, action_of=action_of, action_proxy="map_hypothesis"))
            body["facet_id"] = facet
            body["item_irt"] = {"a": item_a, "b": item_b}
            eig = (row.get("facet_eig_by_facet") or {}).get(facet)
        followup = vault.config.scheduler.followup
        irt_config = vault.config.probe.irt
        parameters = [
            VF.parameter("scheduler.followup.predictive_eig_weight", followup.predictive_eig_weight, "heuristic",
                         source="config"),
            VF.parameter("scheduler.followup.max_interventions_per_lo_per_session",
                         followup.max_interventions_per_lo_per_session, "heuristic", source="config",
                         note="count cap (successor stage moves it onto value of information)"),
            VF.parameter("recall_coverage.kappa_uncertain", vault.config.recall_coverage.kappa_uncertain,
                         "heuristic", source="config"),
            VF.parameter("probe.irt", irt_config.model_dump(), "heuristic", source="config",
                         note="theta/cuts/err fractions of the facet response model"),
        ]
        return VF.record_forecast(
            repository,
            vault=vault,
            site="followup_selection",
            receipt_key=f"followup_selection:{attempt_id}",
            verdict="select",
            forecast=body,
            parameters=parameters,
            candidate_count=len(selection.slate),
            clock=clock,
            decision_ref=attempt_id,
            learning_object_id=learning_object_id,
            source_attempt_id=attempt_id,
            chosen_ref=candidate.id,
            chosen_practice_item_id=candidate.id,
            eig_nats=float(eig) if eig is not None else body.get("eig_nats"),
        )
    except Exception:  # noqa: BLE001
        logger.warning("follow-up forecast not recorded", exc_info=True)
        return None


__all__ = [
    "record_followup_forecast",
    "record_probe_presentation_forecast",
    "record_robust_selection_forecast",
]
