"""Record learner actions on a causal quick-check offer.

An offer names the factor's reviewed active probe and its pinned blind bundles.
Accepting enters or retargets an episode, commits a presentation with the pin,
and records the settled probe_offer decision, including a refusal.
Deferring records a learner preference so the check is not offered again.
"Teach me now" records authorisation to skip the check, then reads repair status.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_attribution import CAUSAL_DECISION_POLICY_VERSION
from learnloop.diagnosis.causal_discrimination import pinned_causal_probe
from learnloop.diagnosis.causal_orchestrator import RepairStatus, causal_repair_status
from learnloop.diagnosis.causal_probe_coherence import (
    candidate_has_current_blind_input_contract,
    order_probe_candidates,
)
from learnloop.diagnosis.causal_reads import CAUSAL_ORCHESTRATOR_FORMULA_VERSION, CausalRepairError
from learnloop.diagnosis.probe_hard_stops import (
    EPISODE_CONFLICT_REASON,
    _causal_origin,
    episode_conflict_reason,
    record_learner_preference,
)
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ProbeOffer:
    """Result of accepting the quick check."""

    accepted: bool
    reason: str
    factor_id: str
    episode_id: str | None = None
    presentation_id: str | None = None
    practice_item_id: str | None = None
    candidate_id: str | None = None
    hypothesis_set_id: str | None = None
    blind_bundle_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "factor_id": self.factor_id,
            "episode_id": self.episode_id,
            "presentation_id": self.presentation_id,
            "practice_item_id": self.practice_item_id,
            "candidate_id": self.candidate_id,
            "hypothesis_set_id": self.hypothesis_set_id,
            "blind_bundle_ids": list(self.blind_bundle_ids),
        }


def _answer_shown(
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
) -> bool:
    """Was the item's answer shown, so no probe of it may be offered (UX Phase
    4 round 7; the one eligibility decision's question)? The offer asks before
    it changes anything."""

    from learnloop.diagnosis.probe_presentations import routine_display_covers_item

    return routine_display_covers_item(repository, practice_item_id, clock=clock)


class _OfferRefusedAtCommit(Exception):
    """The commit refused the probe after the episode was retargeted: rolls
    the retarget back with it (UX Phase 4 round 7)."""

    def __init__(self, offer: "ProbeOffer") -> None:
        super().__init__(offer.reason)
        self.offer = offer


def accept_probe_offer(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    decision_receipt_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
    candidate_id: str | None = None,
    followup_workflow_id: str | None = None,
    router_decision_id: str | None = None,
) -> ProbeOffer:
    """"Take the quick check" (:func:`_accept_probe_offer`), and its ``probe_offer`` decision record (refactor B7).

    The record names the id that decided the offer, so a learner-lane probe has a row at acceptance though no router
    decision exists for it (the map's break 5). It is written after the offer is settled and never raises; an
    exception from the offer itself propagates as before, with no record.
    """

    offer = _accept_probe_offer(
        vault, repository, factor_id=factor_id, decision_receipt_id=decision_receipt_id, session_id=session_id,
        clock=clock, ai_client=ai_client, candidate_id=candidate_id, followup_workflow_id=followup_workflow_id,
        router_decision_id=router_decision_id,
    )
    from learnloop.diagnosis.chain_records import record_probe_offer

    record_probe_offer(repository, offer=offer, decision_receipt_id=decision_receipt_id,
                       router_decision_id=router_decision_id, followup_workflow_id=followup_workflow_id)
    return offer


#: The probe router's tag: an offer request with no router decision selecting the factor's probe behind it.
ROUTER_DECISION_REQUIRED = "router_decision_required"


def router_disposition(repository: Repository, factor_id: str) -> dict[str, Any]:
    """The router's decision on the factor's learner-lane probe as the offer reads it: ``router_state`` (``pending``
    with no decision, ``selected`` or ``not_selected``) and ``router_decision_id``."""

    from learnloop.router.plan_log import PROBE_REF, automatic_probe_decision, learner_probe_decision

    with repository.connection() as connection:
        decided = learner_probe_decision(connection, factor_id)
        automatic = automatic_probe_decision(connection, factor_id) if decided is None else None
    if automatic is not None:
        # The automatic lane's decision on the factor is its one decision: nothing to accept here.
        return {"router_state": "not_selected", "router_decision_id": str(automatic["id"])}
    if decided is None:
        return {"router_state": "pending", "router_decision_id": None}
    selected = str(decided.get("chosen_ref")) == PROBE_REF
    detail = decided.get("detail") or {}
    return {"router_state": "selected" if selected else "not_selected", "router_decision_id": str(decided["id"]),
            "learning_object_id": detail.get("learning_object_id"),
            "misconception_id": detail.get("misconception_id"), "candidate_id": detail.get("candidate_id")}


def accept_routed_probe_offer(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    decision_receipt_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> tuple[ProbeOffer, dict[str, Any]]:
    """"Take the quick check" at the probe router's tag: only the router's selection of this factor's probe is
    accepted, and only its own candidate. The status is read again at the moment of acceptance, so every
    current hard stop applies: a "Not now" or "Teach me now", a machine check, a measuring foreign episode, or
    a selection made void (its candidate retired or no longer administrable). A request the router did not select
    (a stale offer from before the tag, a decision not made yet, or one that did not select the probe) is a typed
    refusal, never an offer of its own. Returns the offer and the router's disposition."""

    disposition = router_disposition(repository, factor_id)
    if disposition["router_state"] != "selected":
        return ProbeOffer(accepted=False, reason=ROUTER_DECISION_REQUIRED, factor_id=factor_id), disposition
    try:
        status = causal_repair_status(vault, repository, misconception_id=str(disposition.get("misconception_id") or ""),
                                      session_id=session_id, start_repair=False, clock=clock, factor_id=factor_id)
    except CausalRepairError:
        # The factor is no longer an open factor of its cause (resolved since the selection).
        return ProbeOffer(accepted=False, reason="factor_not_open", factor_id=factor_id), disposition
    disposition = {**disposition, "router_state": status.router_state,
                   "hard_stop_reasons": list(status.hard_stop_reasons)}
    if status.router_state != "selected" or status.factor_id != factor_id:
        reason = (status.hard_stop_reasons[0] if status.hard_stop_reasons else ROUTER_DECISION_REQUIRED)
        return ProbeOffer(accepted=False, reason=str(reason), factor_id=factor_id), disposition
    offer = accept_probe_offer(vault, repository, factor_id=factor_id, decision_receipt_id=decision_receipt_id,
                               session_id=session_id, clock=clock,
                               router_decision_id=disposition["router_decision_id"],
                               candidate_id=str(disposition.get("candidate_id") or "") or None)
    return offer, disposition


def _accept_probe_offer(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    decision_receipt_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
    candidate_id: str | None = None,
    followup_workflow_id: str | None = None,
    router_decision_id: str | None = None,
) -> ProbeOffer:
    """"Take the quick check": enter a factor-aware episode and pin the probe.

    FG1 §5.1: the same offer runs automatically for a generated probe, with the
    router's decision in place of the learner's click. ``candidate_id`` names the
    exact candidate (the served instrument is the one just admitted), and
    ``followup_workflow_id`` joins the pin to its workflow.

    Two ids name what decided the offer, one meaning each: ``decision_receipt_id``
    is the learner lane's causal probe decision receipt
    (``causal_probe_decision_receipts``), ``router_decision_id`` FG1's router
    decision (``router_decisions``). Before refactor B6 FG1 passed its router
    decision as ``decision_receipt_id``: a pin that carries
    ``followup_workflow_id`` and no ``router_decision_id`` holds a router
    decision id there, and is read that way rather than rewritten.

    This is the ONLY caller of ``enter_episode(causal_factor_id=...)`` — the
    parameter existed with zero callers anywhere, which is why the locked causal
    hypothesis set never reached a served instrument.

    The candidate id and its blind bundle ids are pinned into the presentation's
    ``selection_components`` (free-form JSON, so no schema change) under a
    dedicated ``causal_probe`` key.  Classification later replays against
    exactly those bundles, never a fresh query.
    """

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        return ProbeOffer(
            accepted=False, reason="factor_not_open", factor_id=factor_id
        )
    candidates = repository.causal_probe_candidates_for_factor(
        factor_id, statuses=("active",)
    )
    candidates = order_probe_candidates(
        [
            value
            for value in candidates
            if candidate_has_current_blind_input_contract(value)
        ]
    )
    if not candidates:
        return ProbeOffer(
            accepted=False,
            reason="no_reviewed_active_candidate",
            factor_id=factor_id,
        )
    # Same shared order as the decision path: the served instrument is the
    # receipt's chosen instrument by construction.
    candidate = candidates[0]
    if candidate_id is not None:
        named = [value for value in candidates if str(value["id"]) == candidate_id]
        if not named:
            return ProbeOffer(accepted=False, reason="no_reviewed_active_candidate", factor_id=factor_id)
        candidate = named[0]
    practice_item_id = str(candidate["practice_item_id"])
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return ProbeOffer(
            accepted=False,
            reason="probe_item_missing_from_vault",
            factor_id=factor_id,
            candidate_id=str(candidate["id"]),
        )
    learning_object_id = item.learning_object_id
    # UX Phase 4 round 7: the probe item's answer was just shown on a routine
    # display. Refused before anything changes: no episode is relocked or
    # entered, and no other presentation is invalidated.
    if _answer_shown(repository, practice_item_id, clock=clock):
        return ProbeOffer(
            accepted=False,
            reason="probe_item_answer_shown",
            factor_id=factor_id,
            candidate_id=str(candidate["id"]),
        )

    from learnloop.diagnosis.probe_episodes import (
        eligible_instruments,
        enter_episode,
        retarget_episode_to_causal_factor,
    )
    from learnloop.diagnosis.probe_presentations import (
        RoutineDisplayCovered,
        commit_presentation,
    )

    def finish(episode) -> ProbeOffer:
        """Everything after the episode is settled: eligibility, the pin and
        the commit."""

        if episode.status != "in_progress":
            return ProbeOffer(
                accepted=False,
                reason=f"episode_{episode.status}",
                factor_id=factor_id,
                episode_id=episode.id,
                candidate_id=str(candidate["id"]),
            )
        eligible = [
            entry
            for entry in eligible_instruments(vault, repository, episode, reserved_for=practice_item_id)
            if entry.item.id == practice_item_id
        ]
        if not eligible:
            return ProbeOffer(
                accepted=False,
                reason="probe_item_not_eligible",
                factor_id=factor_id,
                episode_id=episode.id,
                candidate_id=str(candidate["id"]),
            )
        bundle_ids = tuple(str(value) for value in candidate.get("blind_bundle_ids") or [])
        # Accepting twice (a re-tapped button, a remounted panel) must not commit a
        # second presentation: the newest would win at serving time and the older
        # pin would be stranded.  An already-pinned, unconsumed probe for this same
        # candidate IS this offer.
        committed = repository.active_probe_presentation(
            episode.id, practice_item_id=practice_item_id
        )
        if committed is not None:
            already = pinned_causal_probe(repository, committed.id) or {}
            if str(already.get("causal_probe_candidate_id") or "") == str(candidate["id"]):
                return ProbeOffer(
                    accepted=True,
                    reason="probe_already_pinned",
                    factor_id=factor_id,
                    episode_id=episode.id,
                    presentation_id=committed.id,
                    practice_item_id=practice_item_id,
                    candidate_id=str(candidate["id"]),
                    hypothesis_set_id=str(candidate["hypothesis_set_id"]),
                    blind_bundle_ids=tuple(
                        str(value) for value in already.get("blind_bundle_ids") or []
                    ),
                )
        try:
            presentation = commit_presentation(
                vault,
                repository,
                episode,
                eligible[0],
                extra_selection_components={
                    # Nested under one key: the near-clone basis reads top-level
                    # `source_practice_item_id`, and adding sibling keys there would
                    # change an unrelated eligibility decision.
                    "causal_probe": {
                        "causal_factor_id": factor_id,
                        "causal_probe_candidate_id": str(candidate["id"]),
                        "hypothesis_set_id": str(candidate["hypothesis_set_id"]),
                        "blind_bundle_ids": list(bundle_ids),
                        # A router-decided pin has no causal receipt: an empty key here would read as a learner-lane
                        # pin that lost its receipt.
                        **({"decision_receipt_id": decision_receipt_id}
                           if router_decision_id is None or decision_receipt_id is not None else {}),
                        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
                        "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
                        "session_id": session_id,
                        **({"followup_workflow_id": followup_workflow_id} if followup_workflow_id else {}),
                        **({"router_decision_id": router_decision_id} if router_decision_id else {}),
                    }
                },
                clock=clock,
            )
        except RoutineDisplayCovered:
            # Its answer was shown after the check above (UX Phase 4 rounds 6
            # and 7): no probe is administered for it until that coverage ends,
            # and a retarget made in this offer is rolled back with it.
            raise _OfferRefusedAtCommit(ProbeOffer(
                accepted=False,
                reason="probe_item_answer_shown",
                factor_id=factor_id,
                candidate_id=str(candidate["id"]),
            ))
        return ProbeOffer(
            accepted=True,
            reason="probe_pinned",
            factor_id=factor_id,
            episode_id=episode.id,
            presentation_id=presentation.id,
            practice_item_id=practice_item_id,
            candidate_id=str(candidate["id"]),
            hypothesis_set_id=str(candidate["hypothesis_set_id"]),
            blind_bundle_ids=bundle_ids,
        )

    origin = _causal_origin(factor_id)
    existing = repository.open_probe_episode(learning_object_id)
    if existing is not None and str(existing.origin or "") != origin:
        if episode_conflict_reason(repository, existing) is not None:
            # The open episode has already interpreted observations under its
            # own locked set.  Locking a second, causal hypothesis set over it
            # would reinterpret them.
            return ProbeOffer(
                accepted=False,
                reason=EPISODE_CONFLICT_REASON,
                factor_id=factor_id,
                episode_id=existing.id,
                candidate_id=str(candidate["id"]),
            )
        # An open episode that has measured NOTHING (the `initial` placement
        # episode vault state sync opens for every active LO is exactly this)
        # is relocked onto the cause set instead.  At most one episode may be
        # open per LO, so refusing here unconditionally made the whole journey
        # unreachable in the running app.  The relock and the commit are one
        # transaction (UX Phase 4 round 7): a commit-time refusal leaves the
        # episode's lock and its presentation as they were.
        try:
            with repository.atomic():
                episode = retarget_episode_to_causal_factor(
                    vault, repository, existing, factor_id, origin=origin, clock=clock,
                    reserved_for=practice_item_id,
                )
                return finish(episode)
        except _OfferRefusedAtCommit as refused:
            return refused.offer
    episode = enter_episode(
        vault,
        repository,
        learning_object_id,
        # `probe_episodes.trigger` is a closed CHECK vocabulary; a cause-set
        # probe IS a belief-diagnosis trigger.  The causal provenance rides
        # on `origin`, which is free-form and is what `accept_probe_offer`
        # matches on when deciding whether an already-open episode is ours.
        trigger="misconception",
        origin=origin,
        causal_factor_id=factor_id,
        clock=clock,
        ai_client=ai_client,
        reserved_for=practice_item_id,
    )
    try:
        return finish(episode)
    except _OfferRefusedAtCommit as refused:
        # A new episode only: nothing that existed before is changed.
        return refused.offer


def defer_probe_offer(
    repository: Repository,
    *,
    factor_id: str,
    learning_object_id: str | None = None,
    session_id: str | None = None,
    preference: str = "decline",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """"Not now": persist the decline so the next attempt does not re-offer."""

    return record_learner_preference(
        repository,
        preference=preference,
        factor_id=factor_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
        source="probe_offer_declined",
        detail={"factor_id": factor_id},
        clock=clock,
    )


def request_teaching_now(
    vault: LoadedVault,
    repository: Repository,
    *,
    misconception_id: str,
    factor_id: str,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> RepairStatus:
    """"Teach me now": an explicit learner authorisation to skip the check."""

    record_learner_preference(
        repository,
        preference="teach_now",
        factor_id=factor_id,
        session_id=session_id,
        source="teach_me_now",
        detail={"misconception_id": misconception_id},
        clock=clock,
    )
    # The status of the factor the consent was recorded on, never another factor of the same cause.
    return causal_repair_status(
        vault,
        repository,
        misconception_id=misconception_id,
        session_id=session_id,
        clock=clock,
        factor_id=factor_id,
    )

