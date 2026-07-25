from __future__ import annotations

from typing import Any

from learnloop.services.causal_orchestrator import (
    CausalRepairError,
    accept_probe_offer,
    causal_repair_status,
    defer_probe_offer,
    request_teaching_now,
)
from learnloop.services.remediation import (
    RemediationBlocked,
    RemediationError,
    _case_value,
    _episode_case,
    misconception_status_history,
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.serializers import practice_item_detail
from learnloop_sidecar.registry import method


class MisconceptionInput(ParamsModel):
    misconception_id: str


class EpisodeInput(ParamsModel):
    episode_id: str


def _optional_case_payload(repository, misconception_id: str) -> dict[str, Any] | None:
    """The case payload for either kind, or None when the id resolves to neither.

    A causal hold is usually resolved for a *provisional* belief (a causal
    hypothesis id), which has no `misconceptions` row. That must not turn the
    typed §6 status into a `not_found` error — the whole point of this path is
    that the learner sees the hold reason, not a lookup failure. It resolves the
    provisional belief through the same projection the episode reads, so the
    held repair still names the belief it is about.
    """

    record = repository.misconception(misconception_id)
    if record is not None:
        return _case_dto(repository, record, durable=True)
    candidate = repository.misconception_candidate_by_id(misconception_id)
    if candidate is None:
        return None
    return _case_dto(repository, candidate, durable=False)


def _case_dto(repository, case: Any, *, durable: bool) -> dict[str, Any]:
    """The one case shape every remediation RPC returns.

    A durable misconception is an ORM-ish record; a provisional belief is the
    dict projection over its causal hypotheses. Both fill the same keys — the
    Tauri `RemediationCaseDto` reads them by name — and a provisional belief
    simply has no correction statement and no promotion history yet.
    """

    case_id = str(_case_value(case, "id", ""))
    return {
        "id": case_id,
        "statement": _case_value(case, "statement"),
        "correction_statement": _case_value(case, "correction_statement"),
        "mechanism": _case_value(case, "mechanism"),
        "target_facet": _case_value(case, "target_facet"),
        "confused_with_facet": _case_value(case, "confused_with_facet"),
        "status": _case_value(case, "status"),
        "history": misconception_status_history(repository, case_id) if durable else [],
    }


def _episode_case_payload(repository, episode: dict[str, Any]) -> dict[str, Any]:
    """The case a remediation episode repairs, of EITHER kind.

    `remediation_episodes.case_kind` is `misconception` or `diagnosis`, and the
    P2 orchestrator opens diagnosis-kind episodes whose `case_ref` is a causal
    hypothesis id with no `misconceptions` row. Looking that id up as a durable
    misconception raised `not_found`, so every causal repair episode 404'd the
    moment the surface tried to read it. `remediation._episode_case` already
    resolves both kinds — this is the same resolution, shaped for the wire.
    """

    case = _episode_case(repository, episode)
    if case is None:
        raise SidecarError("not_found", "Remediation case was not found.")
    return _case_dto(
        repository, case, durable=episode.get("case_kind") == "misconception"
    )


@method("start_remediation", MisconceptionInput)
def start_remediation_handler(ctx: SidecarContext, params: MisconceptionInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        episode = start_remediation_episode(
            repository, params.misconception_id, vault=vault
        )
    except RemediationBlocked as exc:
        # A causal hold is a STATE, not an error. Returning it as a normal
        # result is what lets the learner see the §6 copy and its actions
        # ("Take the quick check" / "Teach me now" / "Not now"); the previous
        # `invalid_request` raise surfaced as a developer-language toast and was
        # the whole learner-visible contact with the P2 lane.
        return versioned(
            {
                "episode": None,
                "case": _optional_case_payload(repository, params.misconception_id),
                "repair_status": exc.repair_status.as_dict(),
            }
        )
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned(
        {
            "episode": episode,
            "case": _optional_case_payload(repository, params.misconception_id),
            "repair_status": None,
        }
    )


class RepairStatusInput(ParamsModel):
    misconception_id: str
    session_id: str | None = None


class ProbeOfferInput(ParamsModel):
    factor_id: str
    misconception_id: str | None = None
    session_id: str | None = None
    decision_receipt_id: str | None = None


@method("causal_repair_status", RepairStatusInput)
def causal_repair_status_handler(
    ctx: SidecarContext, params: RepairStatusInput
) -> dict[str, Any]:
    """The single P2 repair-orchestration read (spec §6).

    One service call, not one RPC per low-level function: it resolves the open
    factor, discharges/queues machine checks, records the probe decision, and
    starts the repair when the causal state permits it.
    """

    vault, repository = ctx.require_vault()
    try:
        status = causal_repair_status(
            vault,
            repository,
            misconception_id=params.misconception_id,
            session_id=params.session_id,
            # A status read must not mint a remediation episode; the decision
            # receipt is still recorded.
            start_repair=False,
        )
    except CausalRepairError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"repair_status": status.as_dict()})


@method("causal_probe_offer_action", ProbeOfferInput)
def causal_probe_offer_action_handler(
    ctx: SidecarContext, params: ProbeOfferInput
) -> dict[str, Any]:
    """"Take the quick check" — enter the factor-aware episode and pin the probe."""

    vault, repository = ctx.require_vault()
    offer = accept_probe_offer(
        vault,
        repository,
        factor_id=params.factor_id,
        decision_receipt_id=params.decision_receipt_id,
        session_id=params.session_id,
    )
    return versioned({"offer": offer.as_dict()})


@method("causal_probe_defer", ProbeOfferInput)
def causal_probe_defer_handler(
    ctx: SidecarContext, params: ProbeOfferInput
) -> dict[str, Any]:
    """"Not now" — persist the decline so the next attempt does not re-offer."""

    _vault, repository = ctx.require_vault()
    record = defer_probe_offer(
        repository, factor_id=params.factor_id, session_id=params.session_id
    )
    return versioned({"preference": record})


@method("causal_teach_me_now", ProbeOfferInput)
def causal_teach_me_now_handler(
    ctx: SidecarContext, params: ProbeOfferInput
) -> dict[str, Any]:
    """"Teach me now" — explicit authorisation to repair under ambiguity."""

    vault, repository = ctx.require_vault()
    if not params.misconception_id:
        raise SidecarError(
            "invalid_request", "teach_me_now requires the misconception id"
        )
    try:
        status = request_teaching_now(
            vault,
            repository,
            misconception_id=params.misconception_id,
            factor_id=params.factor_id,
            session_id=params.session_id,
        )
    except CausalRepairError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"repair_status": status.as_dict()})


@method("prescribe_remediation", EpisodeInput)
def prescribe_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        episode = prescribe_remediation(vault, repository, params.episode_id)
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned({"episode": episode, "case": _episode_case_payload(repository, episode)})


@method("start_remediation_treatment", EpisodeInput)
def start_remediation_treatment_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        result = start_remediation_treatment(vault, repository, params.episode_id)
    except RemediationError as exc:
        raise SidecarError("invalid_request", str(exc)) from exc
    return versioned(
        {
            **result,
            "practice_item": practice_item_detail(vault, repository, result["primed_item_id"]),
        }
    )


@method("get_remediation", EpisodeInput)
def get_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    episode = repository.remediation_episode(params.episode_id)
    if episode is None:
        raise SidecarError("not_found", "Remediation episode was not found.")
    return versioned({"episode": episode, "case": _episode_case_payload(repository, episode)})
