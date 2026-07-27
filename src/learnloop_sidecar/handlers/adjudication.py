"""Diagnosis adjudication over the sidecar (spec_diagnostic_augmentation_v1 §2 A4).

The store (``services/diagnosis_adjudication``) and the CLI
(``learnloop diagnosis queue|adjudicate|scoreboard``) already exist; this module
is the desktop supply step for the same three operations, and nothing more. All
verdict semantics — the abstention/filled partition, anchor inheritance, version
pinning, supersession — stay in the service. The handlers validate, assemble the
case context the overlay needs to judge one diagnosis, and translate the
service's ``ValueError`` vocabulary into stable codes so a partition violation is
a typed refusal rather than an opaque ``internal``.

The one thing added here that the CLI does not need: ``allowed_verdicts`` on
every queue case. The enum partition is load-bearing (an abstention verdict is
unrecordable against a filled diagnosis and vice versa), and a UI that decides
which buttons to render from its own copy of the rule would drift from the store
that enforces it. So the backend states it per case.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from learnloop.services.diagnosis_adjudication import (
    ABSTENTION_VERDICTS,
    ADJUDICATOR_SOURCES,
    ANCHOR_KINDS,
    FILLED_VERDICTS,
    QUEUE_REASONS,
    VERDICTS,
    adjudication_queue,
    append_diagnosis_adjudication,
    diagnosis_adjudication_scoreboard,
    diagnosis_snapshot,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


# Plain-English readings of the typed `declined` reasons `durable_promotion`
# returns. Anything unmapped falls through as the raw reason: an unfamiliar
# refusal shown verbatim is honest, an invented one is not.
_DECLINED_WORDING: dict[str, str] = {
    "no_verdict": "no active verdict on this attempt",
    "no_asserted_cause": "the diagnosis asserted no concrete cause to promote",
    "statement_empty": "the asserted cause carries no statement",
    "already_durable": "that belief was already durable",
    "no_promotable_candidate": "no promotable candidate remained",
    "trace_consistency_veto": "the learner's own work contradicts it",
    "already_withdrawn": "already withdrawn by an earlier verdict",
    "no_durable_belief": "nothing durable had been promoted from it",
}


def _declined_wording(reason: str) -> str:
    if reason in _DECLINED_WORDING:
        return _DECLINED_WORDING[reason]
    head, _, tail = reason.partition(":")
    if head == "neutral_verdict":
        return "this verdict does not move belief state"
    if head == "ambiguous_cause_set":
        return (
            f"the episode asserted {tail} rival causes, so none of them is promoted"
        )
    if head == "previously_withdrawn":
        return "it was withdrawn earlier and is not quietly re-asserted"
    if head == "learning_object_absent":
        return f"its learning object {tail} is no longer in the vault"
    if head == "candidate_status":
        return f"the candidate is {tail}, not promotable"
    return reason


class AdjudicationQueueInput(ParamsModel):
    learning_object_id: str | None = None
    reasons: list[str] | None = None
    limit: int = 20


class AdjudicatedAnchorInput(ParamsModel):
    anchor_kind: str
    criterion_id: str = ""
    quote: str | None = None
    checkpoint_id: str | None = None
    char_start: int | None = None
    char_end: int | None = None


class AdjudicationRecordInput(ParamsModel):
    attempt_id: str
    verdict: str
    anchor: AdjudicatedAnchorInput | None = None
    repair_md: str | None = None
    repair_class_id: str | None = None
    queue_reason: str | None = None
    adjudicator_source: str = "human_owner"
    rationale: str | None = None


class AdjudicationScoreboardInput(ParamsModel):
    group_by: str | None = "version"


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


def _learner_facing(vault, repository, attempt_id: str) -> dict[str, Any] | None:
    """What the learner was actually shown about this diagnosis, or ``None``.

    ``claim_checked_feedback`` fails closed (returns ``None``) when the receipt
    does not permit learner rendering, and raises on an unknown permitted use.
    Neither is a reason to withhold the whole case from the adjudicator — the
    system's own anchor and repair are still judgeable — so both degrade to "the
    learner saw no causal overlay here".
    """

    from learnloop.services.causal_attribution import claim_checked_feedback

    try:
        return claim_checked_feedback(vault, repository, attempt_id)
    except ValueError:
        return None


def _repair_class_options(repository, attempt_id: str) -> list[dict[str, Any]]:
    """The repair classes this episode offered, with enough to name them.

    The store refuses an adjudicated repair class outside this set (a repair the
    episode never offered "is the finding, not a class id"), so the overlay must
    choose from exactly these or record prose instead.
    """

    from learnloop.services.causal_attribution import causal_episode_for_attempt

    episode = causal_episode_for_attempt(repository, attempt_id) or {}
    receipt = episode.get("receipt")
    if not isinstance(receipt, Mapping):
        return []
    options: list[dict[str, Any]] = []
    for value in receipt.get("repair_classes") or []:
        if not isinstance(value, Mapping) or not value.get("id"):
            continue
        options.append(
            {
                "id": str(value["id"]),
                "operator": value.get("operator"),
                "expected_minutes": value.get("expected_minutes"),
                "target_refs": list(value.get("target_refs") or []),
            }
        )
    return options


def _case(vault, repository, entry) -> dict[str, Any]:
    snapshot = entry.snapshot
    attempt = repository.fetch_practice_attempt(entry.attempt_id) or {}
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    learning_object = vault.learning_objects.get(str(entry.learning_object_id or ""))
    metadata = repository.fetch_attempt_feedback_metadata(entry.attempt_id) or {}
    shown = _learner_facing(vault, repository, entry.attempt_id) or {}

    return {
        "attempt_id": entry.attempt_id,
        "queue_reason": entry.queue_reason,
        "priority": entry.priority,
        "detail": entry.detail,
        "created_at": entry.created_at,
        "learning_object_id": entry.learning_object_id,
        "learning_object_title": (
            learning_object.title if learning_object is not None else None
        ),
        "practice_item_id": entry.practice_item_id,
        "prompt": item.prompt if item is not None else None,
        # The learner's work IS the trace the anchor points into; the anchor's
        # offsets are computed against this text, so both travel together.
        "learner_answer_md": attempt.get("learner_answer_md"),
        "rubric_score": attempt.get("rubric_score"),
        "correctness": attempt.get("correctness"),
        # What the system did. Never a judgement — the abstention confusion
        # matrix is conditioned on it, so the adjudicator rules against it
        # rather than editing it.
        "system_abstained": snapshot.system_abstained,
        "abstention_basis": snapshot.abstention_basis,
        "system_anchor": snapshot.system_anchor,
        "anchor_disagreement": snapshot.anchor_disagreement,
        "system_repair_class_id": snapshot.system_repair_class_id,
        "incomplete_repair_mapping": snapshot.incomplete_repair_mapping,
        "repair_class_options": _repair_class_options(repository, entry.attempt_id),
        # What the learner was told, in the words they were shown.
        "shown_to_learner": {
            "rendered": bool(shown),
            "feedback_md": metadata.get("feedback_md"),
            "hypotheses": [
                {
                    "hypothesis_id": value.get("hypothesis_id"),
                    "label": value.get("label"),
                    "statement": value.get("statement"),
                    "trace_consistency": value.get("trace_consistency"),
                }
                for value in shown.get("causal_hypotheses") or []
            ],
            "proposed_next_action": shown.get("proposed_next_action"),
            "first_divergence": shown.get("first_divergence"),
            "repaired_trace": shown.get("repaired_trace"),
        },
        "learner_report": entry.learner_report,
        # The partition, stated by the side that enforces it.
        "allowed_verdicts": sorted(
            ABSTENTION_VERDICTS if snapshot.system_abstained else FILLED_VERDICTS
        ),
        "system": snapshot.as_dict(),
    }


@method("adjudication.queue", AdjudicationQueueInput)
def adjudication_queue_handler(
    ctx: SidecarContext, params: AdjudicationQueueInput
) -> dict[str, Any]:
    """Attempts owed a diagnosis verdict, highest information first (A4).

    Stratified: learner contests, then abstentions, then the cases the system
    flagged, then an unflagged `sampled` stratum so the eval set is not purely
    adversarially selected. The full queue is scored so the strata counts are
    the real ones; only the returned page is hydrated with case context.
    """

    vault, repository = ctx.require_vault()
    try:
        entries = adjudication_queue(
            repository,
            learning_object_id=params.learning_object_id,
            reasons=params.reasons,
            limit=None,
        )
    except ValueError as exc:
        raise SidecarError("invalid_queue_filter", str(exc)) from exc
    counts = Counter(entry.queue_reason for entry in entries)
    # `limit: 0` is legal and means "the strata counts only" — the shape a badge
    # or a maintenance link needs, without paying to hydrate a single case.
    limit = params.limit if params.limit >= 0 else 20
    return versioned(
        {
            "total": len(entries),
            # A list, not a map: these keys are enum values, and camelizing them
            # on the way out would rename the strata.
            "counts_by_reason": [
                {"reason": reason, "count": counts.get(reason, 0)}
                for reason in QUEUE_REASONS
            ],
            "cases": [_case(vault, repository, entry) for entry in entries[:limit]],
        }
    )


# ---------------------------------------------------------------------------
# Write path
# ---------------------------------------------------------------------------


def _outcome(repository, effect) -> dict[str, Any]:
    """The one honest line the overlay may show after a verdict.

    Sourced entirely from what ``apply_adjudicated_belief_effects`` returned. A
    withdrawal is only narrated to the learner when the belief was actually
    surfaced to them (``surfaced_belief_corrections`` applies that scope guard),
    so the message distinguishes the two rather than promising a correction the
    feed will never render.
    """

    from learnloop.services.surfaced_beliefs import surfaced_belief_corrections

    declined = [_declined_wording(reason) for reason in effect.declined]
    if effect.promoted:
        return {
            "status": "promoted",
            "message": "Promoted to a durable belief.",
            "belief_ids": list(effect.promoted),
            "learner_correction_pending": False,
            "declined": declined,
        }
    if effect.withdrawn:
        owed = {
            correction.belief_id for correction in surfaced_belief_corrections(repository)
        }
        pending = [value for value in effect.withdrawn if value in owed]
        return {
            "status": "withdrawn",
            "message": (
                "Belief withdrawn — the learner will see a correction."
                if pending
                else "Belief withdrawn — it was never shown to the learner, so no correction is owed."
            ),
            "belief_ids": list(effect.withdrawn),
            "learner_correction_pending": bool(pending),
            "declined": declined,
        }
    reason = declined[0] if declined else "no belief change"
    return {
        "status": "no_belief_change",
        "message": f"Verdict recorded — no belief change: {reason}.",
        "belief_ids": [],
        "learner_correction_pending": False,
        "declined": declined,
    }


@method("adjudication.record", AdjudicationRecordInput)
def adjudication_record_handler(
    ctx: SidecarContext, params: AdjudicationRecordInput
) -> dict[str, Any]:
    """Record one considered verdict on one diagnosis, append-only (A4).

    The verdict is recorded first and the §5.6 arm (d) belief effect applied
    second, in that order and separately, so the eval record can never be lost
    to a failure to move belief state — and so the effect is *returned* rather
    than discarded, which is the only way the overlay can report what actually
    happened instead of asserting it.
    """

    vault, repository = ctx.require_vault()

    if params.verdict not in VERDICTS:
        raise SidecarError(
            "unknown_verdict",
            f"Unknown diagnosis verdict {params.verdict!r}.",
            details={"verdicts": list(VERDICTS)},
        )
    if params.adjudicator_source not in ADJUDICATOR_SOURCES:
        raise SidecarError(
            "unknown_adjudicator_source",
            f"Unknown adjudicator source {params.adjudicator_source!r}.",
            details={"sources": list(ADJUDICATOR_SOURCES)},
        )
    if params.queue_reason is not None and params.queue_reason not in QUEUE_REASONS:
        raise SidecarError(
            "unknown_queue_reason",
            f"Unknown queue reason {params.queue_reason!r}.",
            details={"reasons": list(QUEUE_REASONS)},
        )

    snapshot = diagnosis_snapshot(repository, params.attempt_id)
    if snapshot is None:
        raise SidecarError(
            "no_diagnosis",
            f"Attempt {params.attempt_id} has no diagnosis receipt to adjudicate.",
        )
    # The partition the store enforces, surfaced as two distinct typed codes.
    # The overlay filters its buttons on `allowed_verdicts`, so reaching either
    # of these means the case changed underneath the open overlay.
    if snapshot.system_abstained and params.verdict not in ABSTENTION_VERDICTS:
        raise SidecarError(
            "verdict_requires_filled_diagnosis",
            f"The system abstained on {params.attempt_id}; {params.verdict!r} is only "
            "recordable against a diagnosis that named a cause.",
            details={"allowed_verdicts": sorted(ABSTENTION_VERDICTS)},
        )
    if not snapshot.system_abstained and params.verdict not in FILLED_VERDICTS:
        raise SidecarError(
            "verdict_requires_abstention",
            f"The system named a cause on {params.attempt_id}; {params.verdict!r} is "
            "only recordable against an abstention.",
            details={"allowed_verdicts": sorted(FILLED_VERDICTS)},
        )

    anchor: dict[str, Any] | None = None
    if params.anchor is not None:
        if params.anchor.anchor_kind not in ANCHOR_KINDS:
            raise SidecarError(
                "unknown_anchor_kind",
                f"Unknown adjudicated anchor kind {params.anchor.anchor_kind!r}.",
                details={"anchor_kinds": list(ANCHOR_KINDS)},
            )
        if (params.anchor.char_start is None) != (params.anchor.char_end is None):
            raise SidecarError(
                "invalid_anchor",
                "charStart and charEnd must be supplied together.",
            )
        if (
            params.anchor.anchor_kind == "missing_required_step"
            and not params.anchor.checkpoint_id
        ):
            raise SidecarError(
                "invalid_anchor",
                "A missing_required_step anchor requires a checkpoint id.",
            )
        anchor = {
            "anchor_kind": params.anchor.anchor_kind,
            "criterion_id": params.anchor.criterion_id or "",
        }
        if params.anchor.quote:
            anchor["quote"] = params.anchor.quote
        if params.anchor.checkpoint_id:
            anchor["checkpoint_id"] = params.anchor.checkpoint_id
        if params.anchor.char_start is not None:
            anchor["char_start"] = params.anchor.char_start
            anchor["char_end"] = params.anchor.char_end

    try:
        record = append_diagnosis_adjudication(
            repository,
            attempt_id=params.attempt_id,
            verdict=params.verdict,
            adjudicated_anchor=anchor,
            adjudicated_repair_md=params.repair_md,
            adjudicated_repair_class_id=params.repair_class_id,
            queue_reason=params.queue_reason,
            adjudicator_source=params.adjudicator_source,
            rationale=params.rationale,
            # Deliberately no vault: the arm (d) effect is applied below so its
            # typed result can be returned instead of thrown away.
        )
    except ValueError as exc:
        raise SidecarError("invalid_adjudication", str(exc)) from exc

    from learnloop.services.durable_promotion import apply_adjudicated_belief_effects

    try:
        effect = apply_adjudicated_belief_effects(
            vault, repository, attempt_id=params.attempt_id
        )
    except ValueError as exc:
        # The verdict is durable; only the downstream belief move failed. Say so
        # rather than reporting a promotion or a withdrawal that did not happen.
        return versioned(
            {
                "adjudication": record,
                "effect": None,
                "outcome": {
                    "status": "effect_failed",
                    "message": f"Verdict recorded — belief update failed: {exc}",
                    "belief_ids": [],
                    "learner_correction_pending": False,
                    "declined": [],
                },
            }
        )

    return versioned(
        {
            "adjudication": record,
            "effect": effect.as_dict(),
            "outcome": _outcome(repository, effect),
        }
    )


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------


def _counted(values: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    return [{key: name, "count": int(count)} for name, count in values.items()]


def _group(group: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        name: value
        for name, value in group.items()
        if name not in {"by_verdict", "by_queue_reason"}
    }
    payload["by_verdict"] = _counted(group.get("by_verdict") or {}, "verdict")
    payload["by_queue_reason"] = _counted(
        group.get("by_queue_reason") or {}, "reason"
    )
    return payload


@method("adjudication.scoreboard", AdjudicationScoreboardInput)
def adjudication_scoreboard_handler(
    ctx: SidecarContext, params: AdjudicationScoreboardInput
) -> dict[str, Any]:
    """The §3 B5 metrics over the active verdicts.

    Passthrough, with one shape change: the verdict/stratum count maps become
    lists so their enum keys survive camelCasing. Rates stay ``null`` on an empty
    denominator — an abstention precision of 1.0 over zero abstention cases is
    the false comfort the store refuses to produce, and the UI must not
    manufacture it either.
    """

    _vault, repository = ctx.require_vault()
    group_by = params.group_by
    if group_by == "none":
        group_by = None
    try:
        report = diagnosis_adjudication_scoreboard(repository, group_by=group_by)
    except ValueError as exc:
        raise SidecarError("invalid_grouping", str(exc)) from exc
    return versioned(
        {
            "store_version": report["store_version"],
            "group_by": report["group_by"],
            "overall": _group(report["overall"]),
            "groups": [_group(group) for group in report["groups"]],
        }
    )
