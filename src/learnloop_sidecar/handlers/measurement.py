from __future__ import annotations

from typing import Any

from learnloop.services.causal_health import causal_lane_health
from learnloop.services.causal_probe_coherence import (
    candidate_has_current_blind_input_contract,
    transition_probe_candidate,
)
from learnloop.services.certification_cold_probe import (
    certification_cold_probe_report,
    schedule_certification_cold_probes,
)
from learnloop.services.contract_reachability import analyze_contract_reachability
from learnloop.services.facet_mint_gate import judge_facet_mints
from learnloop.services.integration_backfill import (
    COORDINATION,
    apply_integration_backfill,
    apply_integration_backfill_and_recalibrate,
    plan_integration_backfill,
)
from learnloop.services.missing_vocabulary import missing_vocabulary_report
from learnloop.services.persona_gate import gate_precision
from learnloop.services.scoreboard import scoreboard
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ScheduleCertificationColdProbesInput(ParamsModel):
    learning_object_id: str | None = None


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
    """Stage 0–5 operational surface for the Tauri Maintain view.

    Every producer is the same service used by the CLI, so the desktop does not
    carry a second definition of reachability, efficiency, or causal health.
    Expensive certification replay is deliberately excluded from this refresh;
    metrics that require it retain their typed ``requires_replay`` arm.
    """

    vault, repository = ctx.require_vault()
    return versioned(
        {
            "scoreboard": scoreboard(vault, repository, replay=False),
            "reachability": analyze_contract_reachability(vault).as_dict(),
            "cold_probes": certification_cold_probe_report(vault, repository),
            "missing_vocabulary": missing_vocabulary_report(repository),
            "causal_health": causal_lane_health(repository),
            "persona_gate": gate_precision(repository).as_dict(),
            "facet_mint_gate": _facet_mint_gate_payload(vault),
            "integration_backfill": _integration_backfill_payload(vault),
            "causal_probe_review": _causal_probe_review_queue(repository),
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
