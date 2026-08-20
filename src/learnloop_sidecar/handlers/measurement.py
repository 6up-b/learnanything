from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.diagnosis.causal_health import causal_lane_health
from learnloop.diagnosis.causal_selection_audit import causal_selection_readiness
from learnloop.attempts.clarification import clarification_rate
from learnloop.diagnosis.causal_probe_coherence import (
    candidate_has_current_blind_input_contract,
    transition_probe_candidate,
)
from learnloop.goals.certification_cold_probe import (
    certification_cold_probe_report,
    schedule_certification_cold_probes,
)
from learnloop.content.authoring.contract_commissioning import commission_plan
from learnloop.learner.contract_reachability import analyze_contract_reachability
from learnloop.content.synthesis.facet_mint_gate import judge_facet_mints
from learnloop.curriculum.integration_backfill import (
    COORDINATION,
    apply_integration_backfill,
    apply_integration_backfill_and_recalibrate,
    plan_integration_backfill,
)
from learnloop.learner.inference_precheck import analyze_inference_precheck
from learnloop.diagnosis.missing_vocabulary import missing_vocabulary_report
from learnloop.content.authoring.persona_gate import gate_precision
from learnloop.diagnosis.scoreboard import scoreboard
from learnloop.attempts.trace_evidence import trace_evidence_report
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ScheduleCertificationColdProbesInput(ParamsModel):
    learning_object_id: str | None = None


class GenerateCommissioningPracticeInput(ParamsModel):
    #: Empty means "the whole commissioning queue" -- the default path, and the
    #: one the Maintain button uses. A caller may narrow it, but never widen it:
    #: ids outside the vault are rejected rather than silently skipped.
    learning_object_ids: list[str] = Field(default_factory=list)
    #: Cap on learning objects per run, applied after queue ordering so a capped
    #: run takes the queue's highest-priority gaps rather than an arbitrary slice.
    limit: int | None = None
    reason: str | None = None


class TransitionCausalProbeCandidateInput(ParamsModel):
    candidate_id: str
    to_status: str
    reviewer: str | None = None
    reason: str | None = None


class ApplyIntegrationBackfillInput(ParamsModel):
    confirm: bool = False


def _integration_backfill(vault):
    # Stage 5.2 and the CLI deliberately scope the retroactive pass to the
    # coordination debt measured by §5.8.3. Other capabilities require a
    # separate authoring decision and must not be swept into a desktop button.
    return plan_integration_backfill(vault, capabilities=[COORDINATION])


def _integration_backfill_payload(vault) -> dict[str, Any]:
    report = _integration_backfill(vault)
    return {
        **report.as_dict(),
        "preview_edits": [
            edit.as_dict()
            for edit in apply_integration_backfill(
                vault,
                report.verdicts,
                dry_run=True,
            )
        ],
    }


def _causal_probe_review_queue(repository) -> dict[str, Any]:
    factors: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for factor in repository.open_unresolved_cause_factors():
        factor_candidates = repository.causal_probe_candidates_for_factor(
            str(factor["id"])
        )
        factors.append(
            {
                "id": factor["id"],
                "attempt_id": factor["attempt_id"],
                "observation_id": factor["observation_id"],
                "candidate_cause_count": len(factor.get("candidate_causes") or []),
                "probe_candidate_count": len(factor_candidates),
                "created_at": factor["created_at"],
            }
        )
        for candidate in factor_candidates:
            discrimination = candidate.get("discrimination")
            discrimination = (
                discrimination if isinstance(discrimination, dict) else {}
            )
            candidates.append(
                {
                    "id": candidate["id"],
                    "factor_id": candidate["factor_id"],
                    "practice_item_id": candidate["practice_item_id"],
                    "status": candidate["status"],
                    "blind_input_contract_valid": (
                        candidate_has_current_blind_input_contract(candidate)
                    ),
                    "distinguishable": bool(
                        discrimination.get("distinguishable")
                    ),
                    "minimum_margin": discrimination.get("minimum_margin"),
                    "reviewer": candidate.get("reviewer"),
                    "review_reason": candidate.get("review_reason"),
                    "created_at": candidate.get("created_at"),
                }
            )
    return {
        "open_factors": factors,
        "candidates": candidates,
        "pending_machine_checks": repository.causal_machine_checks(status="pending"),
    }


def _instrument_audit_payload(vault, repository) -> dict[str, Any]:
    """Every Meas §3 instrument class's REVERT criterion, plus A4 commissioning.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A2–§3.A5; implementation plan
    item 6.4. Same four producers, in the same order, as
    ``learnloop instrument-audit`` — this is the desktop reading them, not a
    second definition of any of them:

    * A2 ``laddered_stem_cross_column_agreement`` — revert when cross-column
      outcomes on one stem correlate as tightly as within-column ones, because
      the independence claim is then false;
    * A3 ``error_hunt_constructed_response_agreement`` — revert when error-hunt
      outcomes are uncorrelated with constructed-response outcomes on the same
      facet, because the instrument is then measuring proofreading;
    * A4 ``contrast_pair_order_effect`` — revert when serving order dominates the
      within-pair difference;
    * A5 ``discrimination_profile_rejection_rate`` — two-tailed: revert when
      ``no_profile_applies`` collapses toward zero, and treat a profile matching
      nearly every failure as equally suspect.

    The companions travel with the metrics deliberately: a rejection rate of 0.4
    over three profiled items says almost nothing, and a reader who cannot see
    the pool it was computed over will read it as though it did. Every arm keeps
    its own availability, so a rate over too little data renders as ``no_data``
    with counts beside it rather than as a zero.

    ``contrast_pair_commissioning`` is the read-only A4 queue
    (``learnloop commission-contrast-pairs``): identifiability findings turned
    into authoring requests. Deferred findings stay IN the queue with a typed
    reason instead of being dropped, so nothing silently falls off. Nothing here
    schedules, persists or applies anything — it is a derivation, like the
    reachability and backfill panels beside it.

    No ``since`` bound: the desktop panel asks the lifetime question ("is this
    instrument earning its place?"), and a window is the CLI's affordance for
    asking a narrower one. Each producer scans the attempt table once, which is
    the same order of cost as the scoreboard this refresh already pays for.
    """

    from learnloop.diagnosis.contrast_pairs import (
        commission_contrast_pairs,
        contrast_pair_order_effect,
    )
    from learnloop.diagnosis.discrimination_profiles import (
        profile_coverage,
        profile_match_fill_rate,
    )
    from learnloop.diagnosis.error_hunt import error_hunt_outcome_summary, proofreading_signal
    from learnloop.content.authoring.laddered_stems import stem_independence_signal, stem_shapes

    metrics = [
        stem_independence_signal(vault, repository),
        proofreading_signal(vault, repository),
        contrast_pair_order_effect(vault, repository),
        profile_match_fill_rate(repository),
    ]
    return {
        "metrics": [metric.as_dict() for metric in metrics],
        "discrimination_profile_coverage": profile_coverage(vault),
        "error_hunt_outcomes": error_hunt_outcome_summary(repository),
        "laddered_stems": [shape.as_dict() for shape in stem_shapes(vault)],
        "contrast_pair_commissioning": commission_contrast_pairs(
            vault, repository
        ).as_dict(),
    }


def _facet_mint_gate_payload(vault) -> dict[str, Any]:
    payloads = [
        facet.model_dump(mode="json")
        for _facet_id, facet in sorted(vault.evidence_facets.items())
    ]
    return {
        **judge_facet_mints(payloads).as_dict(),
        # The audit found this is not the literal D2 shared-harness execution.
        # Carry that fact to every consumer instead of leaving it in prose.
        "implementation_status": "structural_proxy",
        "original_spec_complete": False,
        "limitation": (
            "Uses exclusive normalized error signatures as an authorability "
            "proxy; it does not author and grade an item through the shared "
            "planted-persona harness."
        ),
    }


@method("get_measurement_health", EmptyParams)
def get_measurement_health(
    ctx: SidecarContext, _params: EmptyParams
) -> dict[str, Any]:
    """Stage 0–6 plus the Stage 8.1 precheck for the Tauri Maintain view.

    Every producer is the same service used by the CLI, so the desktop does not
    carry a second definition of reachability, efficiency, or causal health.
    Expensive certification replay is deliberately excluded from this refresh;
    metrics that require it retain their typed ``requires_replay`` arm.

    ``trace_evidence`` and ``clarification_rate`` are the two §3.A6/§3.A8 revert
    criteria that no other panel here watches: opportunistic credit
    concentrating on a favourite facet (the grader pattern-matching vocabulary
    rather than reading work), and a clarification rate above a small fraction
    of attempts (machine-resident uncertainty being misclassified as
    learner-resident, which principle 8 requires be fixed machine-side).
    """

    vault, repository = ctx.require_vault()
    reachability = analyze_contract_reachability(vault)
    return versioned(
        {
            "scoreboard": scoreboard(vault, repository, replay=False),
            "reachability": reachability.as_dict(),
            "inference_precheck": analyze_inference_precheck(
                vault, reachability=reachability
            ).as_dict(),
            "cold_probes": certification_cold_probe_report(vault, repository),
            "missing_vocabulary": missing_vocabulary_report(repository),
            "causal_health": causal_lane_health(repository),
            # EVSI-2's WP0 readiness: can the formal selector change any
            # decision here yet? Typed unavailable arms, never favorable zeros.
            "causal_selection": causal_selection_readiness(vault, repository),
            "persona_gate": gate_precision(repository).as_dict(),
            "facet_mint_gate": _facet_mint_gate_payload(vault),
            "integration_backfill": _integration_backfill_payload(vault),
            "causal_probe_review": _causal_probe_review_queue(repository),
            "trace_evidence": trace_evidence_report(repository),
            "clarification_rate": clarification_rate(repository),
            # Plan item 6.4's four revert producers. They shipped CLI-only, which
            # made "is this instrument still earning its place?" a question only
            # a terminal could answer — and a revert criterion nobody reads is a
            # rung kept on judgement, which is what §3 forbids.
            "instrument_audit": _instrument_audit_payload(vault, repository),
        }
    )


@method(
    "schedule_certification_cold_probes",
    ScheduleCertificationColdProbesInput,
)
def schedule_certification_cold_probes_handler(
    ctx: SidecarContext, params: ScheduleCertificationColdProbesInput
) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    report = schedule_certification_cold_probes(
        vault,
        repository,
        learning_object_id=params.learning_object_id,
    )
    return versioned({"schedule": report.as_dict()})


@method(
    "transition_causal_probe_candidate",
    TransitionCausalProbeCandidateInput,
)
def transition_causal_probe_candidate_handler(
    ctx: SidecarContext, params: TransitionCausalProbeCandidateInput
) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        candidate = transition_probe_candidate(
            repository,
            params.candidate_id,
            to_status=params.to_status,
            reviewer=params.reviewer,
            reason=params.reason,
        )
    except ValueError as exc:
        raise SidecarError("invalid_causal_probe_transition", str(exc)) from exc
    return versioned({"candidate": candidate})


@method("apply_integration_backfill", ApplyIntegrationBackfillInput)
def apply_integration_backfill_handler(
    ctx: SidecarContext, params: ApplyIntegrationBackfillInput
) -> dict[str, Any]:
    """Apply reviewed D3 coordination edits and narrate the recalibration.

    This is intentionally an explicit confirmation action: it rewrites authored
    YAML, then uses the same reload/replay/boundary service as the CLI.
    """

    if not params.confirm:
        raise SidecarError(
            "confirmation_required",
            "Applying the integration backfill rewrites authored learning-object files.",
        )
    vault, repository = ctx.require_vault()
    report = _integration_backfill(vault)
    applied = apply_integration_backfill_and_recalibrate(
        vault,
        repository,
        report.verdicts,
        dry_run=False,
    )
    ctx.reload(maintenance=False)
    refreshed_vault, _repository = ctx.require_vault()
    return versioned(
        {
            "applied": applied.as_dict(),
            "integration_backfill": _integration_backfill_payload(
                refreshed_vault
            ),
        }
    )


@method("generate_commissioning_practice", GenerateCommissioningPracticeInput)
def generate_commissioning_practice(
    ctx: SidecarContext, params: GenerateCommissioningPracticeInput
) -> dict[str, Any]:
    """Author practice for the commissioning queue's authorable gaps.

    The Maintain view has shown the reachability queue read-only: it names the
    contract cells no instrument observes, and then leaves the learner with
    nowhere to go. This is the action that closes them.

    Two things are deliberate.

    *The default target set comes from the commissioning plan, not the screen.*
    ``MeasurementHealthPanel`` renders a truncated slice of the reachability
    cells, so a button that posted what it displayed would author for the first
    eight rows and silently skip the rest. The plan is recomputed here and
    consumed in ``commissioning_queue`` order, which is the same order
    ``build_practice_expansion_plan`` uses -- one priority, not two. Only
    ``COMMISSION`` cells are targeted; the deferred dispositions (coordination
    depth envelopes, downward dominance, blueprint repair) are not authoring
    work and are reported, not generated for.

    *It enqueues rather than generates.* This is a multi-item model-backed
    authoring run, and the sidecar has a single stdin/stdout channel -- blocking
    it for the length of a generation would freeze every other call the app
    makes, timeout ceiling or not. So it takes the same durable
    ``practice_expansion`` job every other multi-item authoring path takes and
    returns the batch for the caller to watch. Items land as a proposal awaiting
    review, never applied silently.
    """

    vault, repository = ctx.require_vault()
    plan = commission_plan(vault, repository)
    ranked = plan.learning_object_rank()

    requested = [str(value).strip() for value in params.learning_object_ids if str(value).strip()]
    if requested:
        unknown = [value for value in requested if value not in vault.learning_objects]
        if unknown:
            raise SidecarError(
                "not_found",
                f"Unknown learning object(s): {', '.join(sorted(unknown))}.",
                details={"learning_object_ids": sorted(unknown)},
            )
        # An explicit selection is still ordered by the queue, and anything the
        # queue has nothing authorable for sorts last rather than being dropped:
        # the caller asked for it, so it is generated for, just not first.
        targets = sorted(requested, key=lambda lo_id: (ranked.get(lo_id, len(ranked)), lo_id))
    else:
        targets = sorted(ranked, key=lambda lo_id: (ranked[lo_id], lo_id))

    if params.limit is not None:
        targets = targets[: params.limit]

    if not targets:
        # Not an error: an empty commissioning queue is the good outcome, and a
        # surface that raised here would report success as a failure.
        return versioned(
            {
                "batch_id": None,
                "batch": None,
                "learning_object_ids": [],
                "commissionable_cell_count": 0,
                "deferred_cell_count": len(plan.deferred),
            }
        )

    subjects = {
        subject
        for lo_id in targets
        for subject in vault.learning_objects[lo_id].subjects
    }
    batch_id = ctx.ingest_jobs.enqueue_practice_expansion(
        learning_object_ids=targets,
        subject_id=next(iter(sorted(subjects))) if len(subjects) == 1 else None,
        reason=params.reason or "commissioning_queue_gap",
    )
    return versioned(
        {
            "batch_id": batch_id,
            "batch": ctx.ingest_jobs.get_batch(batch_id),
            "learning_object_ids": targets,
            "commissionable_cell_count": sum(
                len(plan.for_learning_object(lo_id)) for lo_id in targets
            ),
            "deferred_cell_count": len(plan.deferred),
        }
    )
