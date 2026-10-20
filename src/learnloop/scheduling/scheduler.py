from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from math import exp, log
from typing import Any, Mapping

from learnloop.algorithm_versions import PROBE_TIE_VERSIONS
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import (
    ActiveErrorEvent,
    MasteryState,
    PracticeItemQualityState,
    PracticeItemState,
    Repository,
)
from learnloop.db.scopes import pinned_repository_call
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, forgetting_curve
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.diagnosis.probe_episodes import (
    EligibleInstrument,
    EpisodePosterior,
    RoutineDisplayCovered,
    administered_surface_exclusions,
    eligible_instruments,
    episode_hypothesis_set,
    episode_posterior,
    presentation_commit_payload,
    probe_serving_block_reason,
    record_presentation_forecast,
    robust_gate_counterfactual,
)
from learnloop.diagnosis.probes import HypothesisSet
from learnloop.numeric import clamp
from learnloop.goals.goal_projection import build_goal_frontier
from learnloop.learner.facet_state_reader import facet_states_by_lo as read_facet_states_by_lo
from learnloop.learner.recall_coverage import (
    familiarity_discount,
    familiarity_discount_from_attempts,
    resolve_coverage,
)
from learnloop.scheduling.serving_exclusions import (
    PROBE_RESERVED_GATES,
    ServingExclusions,
    admission_reason,
    out_of_timing_serving_exclusions,
    routine_serving_exclusions,
)
from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling.selection_rewards import (
    SchedulerIntent,
    ability_vector,
    item_demand_vector,
    score_selection_reward,
)
from learnloop.vault.lifecycle import practice_item_servable
from learnloop.vault.models import LoadedVault, PracticeItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchedulerSession:
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None
    #: Whether the build may apply the seeded epsilon tie-break (router R1's
    #: ``scheduler_seeded_exploration``). False makes the build greedy, and its
    #: logged design probabilities say so (one on the head), as a build with no
    #: session does. The daily plan turns it off where the router composes
    #: Today (``daily_plan.engine.plan_scheduler_session``): staged plans are
    #: deterministic, and the router's only exploration is the mixture's floor.
    seeded_exploration: bool = True
    #: What a contrast pair's member-order draw (Meas §3.A4) is seeded on
    #: (``diagnosis.contrast_pairs.serving_seed``): ``"session"`` (the session
    #: and the pair; the order varies across sessions) or ``"pair"`` (the pair
    #: alone; the same order in every session, still drawn across pairs and
    #: recorded). The daily plan draws per pair wherever its pool is greedy
    #: (plan-determinism Codex review F1): the plan packs its pool in this
    #: order, so a per-session order would choose a different member, or order
    #: a block differently, by session.
    contrast_order_seed: str = "session"


@dataclass(frozen=True)
class ScheduledItem:
    practice_item_id: str
    learning_object_id: str
    priority: float
    components: dict[str, float]
    readiness_factor: float | None
    selected_mode: str
    plain_english: list[str]
    reward_debug: dict[str, object] | None = None
    #: Which delayed follow-up lane resurrected this item, or ``None`` for an
    #: ordinary due pick. Three lanes (``intervention_followup``, ``cold_retry``,
    #: ``certification_cold_probe``) share the one ``intervention_followup``
    #: priority component, so the component alone cannot say what the item is
    #: FOR: a §5.7 certification cold probe is a held-out validity check on an
    #: already-certified skill, not a repair retry. This carries the originating
    #: ``followup_tasks.kind`` so surfaces need not reverse-engineer the lane
    #: from the learner-facing prose.
    followup_kind: str | None = None
    scheduler_slate_id: str | None = None
    scheduler_candidate_id: str | None = None
    #: mvp-0.21 (voi_stopping): an in-episode probe's likelihood rows over its
    #: open episode's hypotheses (``{belief_key, prior, likelihood,
    #: objective}``), so checks chosen together (teach-backs, project probes)
    #: value its hypothesis information over the expected posterior branches
    #: the others leave (``voi_stopping.HypothesisChannel``). Never persisted,
    #: never compared; None below mvp-0.21 and for every other item.
    hypothesis_channel: Mapping[str, Any] | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class ExplorationOutcome:
    """One outcome of the seeded epsilon tie-break and the offer it composes to.

    ``explored_item_id`` is the near-tie moved to the front, or ``None`` for the
    greedy order. ``composed`` is the queue after the whole deterministic
    composition (and the committed presentation pin) under that outcome, before
    ``limit``: what the build would have produced had the draw landed there.
    """

    explored_item_id: str | None
    probability: float
    composed: tuple[ScheduledItem, ...]


@dataclass
class OfferTrace:
    """What one queue build decided, for router decision logging (router R1).

    Filled only when a caller passes it to :func:`build_due_queue`; the build
    itself is unchanged. ``exclusions`` maps a reason code to the item ids the
    candidate loop withheld for it. ``outcomes`` enumerates the exploration's
    whole support, each recomposed through the same steps as the live build,
    so a caller can compute the exact probability of whichever item heads the
    offer it shows. ``realized`` indexes the outcome the seeded draw chose.
    """

    exclusions: dict[str, list[str]] = field(default_factory=dict)
    algorithm_version: str | None = None
    session_id: str | None = None
    now_iso: str | None = None
    limit: int | None = None
    slate_id: str | None = None
    candidate_ids: dict[str, str] = field(default_factory=dict)
    greedy_item_ids: tuple[str, ...] = ()
    #: The greedy order before the draw: each candidate's planner values with
    #: no outcome-specific mark (an explored item's ``exploration_selected``).
    greedy: tuple[ScheduledItem, ...] = ()
    considered: tuple[ScheduledItem, ...] = ()
    base_propensity: dict[str, float] = field(default_factory=dict)
    exploration: dict[str, Any] = field(default_factory=dict)
    outcomes: tuple[ExplorationOutcome, ...] = ()
    realized: int = 0
    pinned_item_id: str | None = None
    probe_block_reason: str | None = None
    cold_deferrals: tuple[dict[str, Any], ...] = ()
    placement_active: bool = False
    #: The session the build was composed for (budget, energy, readiness).
    session_context: dict[str, Any] = field(default_factory=dict)
    #: The configuration that shaped the build (hashed into the decision).
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    #: mvp-0.21: every value-of-information stop/continue decision the build
    #: made (probe episodes, further teach-backs), each with its forecast.
    voi_decisions: tuple[dict[str, Any], ...] = ()
    #: The exclusion reason for teach-back items the composition dropped:
    #: the count cap below mvp-0.21, their value at it.
    teach_back_exclusion_reason: str = "teach_back_session_cap"


@pinned_repository_call
def build_due_queue(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
    session: SchedulerSession | None = None,
    limit: int | None = None,
    persist_explanations: bool = True,
    offer_trace: OfferTrace | None = None,
) -> list[ScheduledItem]:
    now = (clock or SystemClock()).now().astimezone(UTC)
    session = session or SchedulerSession()
    config = vault.config
    # Router R1: reason codes for the candidates the loop withholds, recorded
    # only when a caller logs the offer. Never consulted by the build.
    traced_exclusions = offer_trace.exclusions if offer_trace is not None else None

    def withheld(reason: str, item_id: str) -> None:
        if traced_exclusions is not None:
            traced_exclusions.setdefault(reason, []).append(item_id)

    if persist_explanations:
        # Freshness supply reconciliation: a consumed (administered) single-use
        # diagnostic_probe surface leaves a diagnostic-coverage hole; derive the
        # deduplicated replacement-generation need here, on the path that always
        # runs right after an attempt. Idempotent and replay-safe (needs are a
        # function of attempts + item state), and guarded by persist_explanations
        # so explicitly side-effect-free queue builds stay pure.
        from learnloop.diagnosis.diagnostic_surface_supply import (
            reconcile_diagnostic_surface_needs,
            reconcile_empty_probe_pools,
        )

        reconcile_diagnostic_surface_needs(vault, repository, clock=clock)
        # Owner decision: an EMPTY eligible pool behind an open probe episode or
        # a pending diagnostic need must never be silent. Queue generation
        # through the existing needs→commissioning path when an authoring
        # provider is routed, and always raise one urgent deduplicated
        # maintenance notice per LO (self-resolving when a fresh surface
        # appears). Same guard as the supply sweep: side-effect-free builds
        # stay pure.
        reconcile_empty_probe_pools(vault, repository, clock=clock)
    cap_lifted = False
    if session.session_id is not None:
        from learnloop.diagnosis.calibration_sessions import calibration_cap_lifted

        cap_lifted = calibration_cap_lifted(repository, session.session_id)
    probe_block_reason = probe_serving_block_reason(
        vault,
        repository,
        session_id=session.session_id,
        cap_lifted=cap_lifted,
    )
    # mvp-0.21 (voi_stopping): the session's qualifying-observation cap no
    # longer blocks probes; each episode's next observation is served while
    # its value pays for its minutes. A calibration session (an explicit
    # learner opt-in) lifts the value gate as it lifted the cap.
    voi_context = voi.VoiContext(vault, repository)
    voi_probe_active = voi.voi_stopping_active(config, voi.SITE_PROBE_EPISODE) and not cap_lifted
    voi_probe_decisions: dict[str, voi.SiteDecision] = {}
    # Checks chosen together (teach-backs here, project probes in the plan)
    # need an in-episode probe's likelihood rows to value its hypothesis
    # information conditionally (review F2 reopened).
    carry_hypothesis_channels = voi.voi_stopping_active(config, voi.SITE_TEACH_BACK) or voi.voi_stopping_active(
        config, voi.SITE_PROJECT_PROBE
    )
    item_states = repository.practice_item_states()
    quality_states = repository.practice_item_quality_states()
    # The routine-serving exclusions, shared with the quick check
    # (``serving_exclusions``): items reserved for a goal's held-out exam are
    # quarantined from practice so the exam stays an honest, uncontaminated
    # test; pending-variant holds and staged-owned commitments are below.
    exclusions = routine_serving_exclusions(vault, repository)
    reserved_item_ids = set(exclusions.reserved_exam_item_ids)
    # Exam protection (Codex review F1): an item made from held-out material
    # is never routine practice, however long ago it was imported.
    held_out_item_ids = set(exclusions.held_out_item_ids)
    rung_variant_hold_ids = set(exclusions.rung_variant_hold_ids)
    # Learner-requested items (tutor promotions + applied rung variants, never
    # attempted). Fetched once: the in-loop eligibility floor and the §4a
    # requested-items reorder floor must see the same set — a fresh sibling has
    # no attempts, stability, or due_at, so without the eligibility floor it
    # zeroes out at the priority filter and the reorder floor never sees it.
    # Daily-loop DL2 (intent; the successor mvp-0.29 behind intent.enabled):
    # None when intent changes nothing (below the tag, switch off, or no
    # commitment covers an item), and every branch below is then exactly the
    # predecessor's.
    intent_view = _intent_serving(vault, repository, now)
    if intent_view is None:
        requested_item_ids = repository.requested_practice_item_ids()
    else:
        # Read here; intent's filter (which adds the due checks' candidates,
        # so reads the build's admission) applies once that is bound, below.
        requested_item_ids = repository.requested_practice_item_ids(
            skip_commitment_ids=intent_view.intent_control_request_commitments()
        )
    # P4 §14.2 step 3 (design §A.2 rule 3): during the dual-controller cutover the
    # staged policy owns P2 golden-path commitments. Their practice items are EXCLUDED
    # from the legacy queue so no commitment is scheduled by both controllers. Empty
    # (a no-op, byte-identical legacy queue) when no commitment is staged-owned.
    staged_owned_item_ids = set(exclusions.staged_owned_item_ids)
    # Learner field F2 (mvp-0.11, kill switch placement.enabled): starting new
    # material without ceremony. Fast-track runs first on the persisting path
    # (the one that always follows an attempt), so an LO it assumes known stops
    # being served as new material in this very build. None when placement is
    # off: every branch below then behaves exactly as the predecessor.
    placement_serving = _placement_serving(
        vault,
        repository,
        clock=clock,
        persist=persist_explanations,
        item_states=item_states,
        excluded_item_ids=reserved_item_ids | rung_variant_hold_ids | staged_owned_item_ids | held_out_item_ids,
    )
    mastery_states = repository.mastery_states()
    # Probe redesign: open diagnostic episodes replace lo_probe_state (frozen
    # legacy). `pending_items` episodes keep their LO schedulable for ordinary
    # practice; only `in_progress` episodes score probe EIG.
    if placement_serving is not None:
        # F2 (owner decision 2026-10-12): an opening episode an earlier version
        # opened and nobody answered is ignored while placement serves, so its
        # never-practised LO enters as new material. It is not rewritten or
        # closed: the kill switch serves it again exactly.
        from learnloop.placement.state import servable_open_episodes

        open_episodes = servable_open_episodes(vault, repository)
    else:
        open_episodes = repository.open_probe_episodes()
    errors_by_lo = _errors_by_learning_object(repository.active_error_events())
    short_session = (
        session.available_minutes is not None
        and session.available_minutes <= config.scheduler.short_session_minutes
    )
    readiness_factor = _readiness_factor(session, config)
    fsrs_weights = resolve_fsrs_weights(repository)
    episode_posterior_cache: dict[str, tuple[HypothesisSet, dict[str, float], float] | None] = {}
    episode_eligible_cache: dict[str, dict[str, EligibleInstrument]] = {}
    pending_followups = repository.pending_followup_practice_items(clock=clock)
    # Meas §6.2: a due cold task whose item's answer has been revealed since the
    # task was created must be DEFERRED, not served. Burning the one single-use
    # measurement on contaminated evidence is the failure this prevents.
    pending_followups, cold_deferrals = _defer_revealed_cold_followups(
        vault, repository, pending_followups, clock=clock, persist=persist_explanations
    )
    # KM2b: canonical shared facet state under mvp-0.7 (byte-identical legacy
    # per-LO reads under mvp-0.6). One reader build feeds the whole vault sweep.
    facet_states_by_lo = read_facet_states_by_lo(vault, repository)
    frontier = build_goal_frontier(
        vault,
        repository,
        clock=clock,
        item_states=item_states,
        facet_states_by_lo=facet_states_by_lo,
    )

    # P0.4 §3.4: practice progression reads the confirmed terminal-contract HEAD at
    # each decision and logs the evaluated version in its trace -- it holds NO
    # cross-decision pin. Resolved once per build; inert (empty) for unconfirmed
    # goals so legacy scheduling is byte-identical.
    from learnloop.goals.goal_contracts import resolve_head

    evaluated_head_ids: list[str] = []
    for goal_id in frontier.active_goal_ids:
        head = resolve_head(repository, goal_id)
        if head is not None:
            evaluated_head_ids.append(head.id)

    queue: list[ScheduledItem] = []
    # Annotation-only rows for diagnostic surfaces the freshness rules kept out
    # of the queue. Logged with the slate ("no silent caps"), never served.
    probe_reserved_exclusions: list[ScheduledItem] = []
    probe_item_ids: dict[str, str] = {}
    probe_entropy_before: dict[str, float] = {}
    # One partitioned query supplies the familiarity window for every LO that
    # can contribute to an active goal frontier.  The former lazy cache still
    # issued one query per frontier LO on every queue rebuild.
    recent_attempts_by_lo = repository.list_recent_attempts_by_learning_objects(
        frontier.by_lo,
        limit=config.recall_coverage.familiarity_recent_attempt_window,
    )
    # held-grade-evidence: an exposure is an exposure, but a held grade's
    # provisional score never weighs it (THE held predicate marks the rows).
    from learnloop.held_grades import held_attempt_ids
    from learnloop.outcome_contract import HELD_ROW_KEY

    held_recent = held_attempt_ids(
        repository, (row.get("id") for rows in recent_attempts_by_lo.values() for row in rows)
    )
    if held_recent:
        recent_attempts_by_lo = {
            lo_id: [{**row, HELD_ROW_KEY: True} if row.get("id") in held_recent else row for row in rows]
            for lo_id, rows in recent_attempts_by_lo.items()
        }
    # The build's admission (``serving_exclusions.admission_reason``, the one
    # per-item predicate; orchestrator ruling R1): the routine gate, the
    # freshness reserve, placement, the cold-start gate and the probe-episode
    # gates over this build's reads. A DL2 "Check once" asks the same
    # predicate of every candidate before it prefers a cold one over
    # practice, so a candidate this build would not serve never decides a
    # check (Codex re-review F11).
    admission = _BuildAdmission(
        vault,
        repository,
        now=now,
        session=session,
        intent_view=intent_view,
        exclusions=_Once.of(exclusions),
        item_states=_Once.of(item_states),
        placement_serving=_Once.of(placement_serving),
        open_episodes=_Once.of(open_episodes),
        probe_block_reason=_Once.of(probe_block_reason),
        mastery_states=_Once.of(mastery_states),
        frontier=_Once.of(frontier),
        errors_by_lo=_Once.of(errors_by_lo),
        fsrs_weights=_Once.of(fsrs_weights),
        recent_attempts_by_lo=_Once.of(recent_attempts_by_lo),
        voi_context=_Once.of(voi_context),
        voi_probe_active=voi_probe_active,
        carry_hypothesis_channels=carry_hypothesis_channels,
        short_session=short_session,
        voi_probe_decisions=voi_probe_decisions,
        episode_posterior_cache=episode_posterior_cache,
        episode_eligible_cache=episode_eligible_cache,
    )
    if intent_view is not None:
        intent_view.bind_admission(admission.check_candidate_refusal)
        requested_item_ids = intent_view.filter_requests(requested_item_ids)
        # DL2 (Codex review F1): follow-up insertion is a second door that
        # rebuilds an item by id after the ranked loop, so the intent gate
        # applies here too: a paused, referenced, let-go or answered-check
        # item, or one a "Check once" still holds, is never resurrected. The
        # task stays pending (nothing is written) and serves once intent
        # allows it again.
        pending_followups = [
            pending
            for pending in pending_followups
            if intent_view.withhold_reason(str(pending["practice_item_id"])) is None
        ]
    requested_id_set = set(requested_item_ids)
    for item in vault.practice_items.values():
        state = item_states.get(item.id)
        requested = item.id in requested_id_set
        # THE admission predicate, with intent's gate after the routine one
        # (DL2 §5.3: Pause, Reference, Let go and an answered "Check once" are
        # not served, requests included; a check holds its items back until
        # its date; a held-out or reserved item is never a check).
        reason = admission_reason(
            vault,
            item,
            state,
            exclusions,
            admission,
            requested=requested,
            intent_gate=intent_view.withhold_reason if intent_view is not None else None,
        )
        if reason is not None:
            if reason in PROBE_RESERVED_GATES:
                # In an open probe episode but not servable as a probe this
                # refresh. The surface stays reserved rather than leaking into
                # ordinary practice; the exclusion is logged with the slate so
                # it never fails silently.
                score = admission.probe_score(item, state)
                score.record(item.id, probe_item_ids, probe_entropy_before)
                probe_reserved_exclusions.append(admission.reserved_annotation(item, score, readiness_factor))
            withheld(reason, item.id)
            continue
        learning_object = vault.learning_object_for_item(item)
        mastery = mastery_states.get(learning_object.id)
        episode = open_episodes.get(learning_object.id)
        in_probe = admission.in_probe(item)
        new_material, assumed_check = (False, False) if requested else admission.placement(item, state)[1:]
        # The ranking components and, in an open probe episode, the probe's
        # (``_BuildAdmission.probe_score``: read once per build, so the probe
        # gate above and this ranking see the same values).
        score = admission.probe_score(item, state)
        score.record(item.id, probe_item_ids, probe_entropy_before)
        components = dict(score.components)
        goal_frontier_component = components["goal_frontier"]
        probe_familiarity_discount = score.probe_familiarity_discount
        hypothesis_channel = score.hypothesis_channel

        legacy_priority = _priority(components, config)
        intent = _intent_for_item(item, in_probe=in_probe, components=components)
        reward = score_selection_reward(
            vault,
            item,
            learning_object,
            mastery=mastery,
            facet_states=facet_states_by_lo.get(learning_object.id, []),
            quality_state=quality_states.get(item.id),
            active_errors=errors_by_lo.get(learning_object.id, []),
            base_components=components,
            probe_eig=components.get("probe_eig_raw", components["probe_eig"]),
            probe_familiarity_discount=probe_familiarity_discount,
            intent=intent,
        )
        components.update(reward.as_components())
        boundary_priority = 0.20 * max(0.0, components.get("targeted_boundary_fit", 0.0))
        components["boundary_target"] = boundary_priority
        components["legacy_priority"] = legacy_priority
        priority = max(legacy_priority, boundary_priority)
        if item.practice_mode == "teach_back":
            # Small floor (not a new weight): transfer escalation keeps solid
            # items weakly schedulable, so a teach_back item must survive the
            # zero-priority filter and rank by its selection reward.
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
        if new_material or assumed_check:
            # F2: the same small floor the predecessor's opening episode gave a
            # never-attempted LO; the selection reward decides the rest.
            components["new_material" if new_material else "assumed_check"] = 1.0
            if assumed_check and placement_serving is not None:
                if learning_object.id in placement_serving.committed_learning_object_ids:
                    # A prerequisite created from the learner's own text.
                    components["gap_commitment_check"] = 1.0
                elif (
                    learning_object.id in placement_serving.gap_check_learning_object_ids
                    or learning_object.id in placement_serving.advanced_learning_object_ids
                ):
                    components["gap_sooner_check"] = 1.0
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
        if episode is not None and (mastery is None or mastery.last_evidence_at is None):
            # Cold-start floor (probe redesign §10): an open episode — including
            # a pending_items one — keeps its never-attempted LO practicable for
            # belief-only ordinary practice instead of blocking on instruments.
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
        if intent_view is not None and intent_view.pushes(item.id, state):
            # DL2 (§6.1): Learn and Master keep their not-yet-due items in
            # reach of the push lane, as a goal frontier does.
            components["intent_push"] = 1.0
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
        if item.id in requested_id_set:
            # Requested-items eligibility floor: the learner explicitly asked
            # for this card (promotion or easier/harder variant) and it has no
            # attempt/state/due signal yet — zero scheduler priority by
            # construction. It must survive this filter for the §4a requested
            # reorder floor below to be able to pull it forward.
            priority = max(priority, _REQUESTED_PRIORITY_FLOOR)
        if priority <= 0:
            withheld("zero_priority", item.id)
            continue
        plain_english = _plain_english(item, components)
        if evaluated_head_ids and goal_frontier_component > 0:
            plain_english = plain_english + [
                f"evaluated terminal-contract head {version_id}"
                for version_id in evaluated_head_ids
            ]
        queue.append(
            ScheduledItem(
                practice_item_id=item.id,
                learning_object_id=learning_object.id,
                priority=priority,
                components=components,
                readiness_factor=readiness_factor,
                selected_mode=item.practice_mode,
                plain_english=plain_english,
                reward_debug=reward.as_debug(),
                hypothesis_channel=hypothesis_channel,
            )
        )

    queue.sort(
        key=lambda scheduled: (
            -scheduled.components.get("selection_reward", 0.0),
            -scheduled.priority,
            scheduled.practice_item_id,
        )
    )
    if placement_serving is not None:
        queue = _order_new_material(vault, repository, queue, placement_serving)
    # DL2 (§5.2): the items due "Check once" requests chose; composition never
    # drops them for value or cost (fix round 4, R2: the learner asked).
    check_item_ids: frozenset[str] = frozenset()
    if intent_view is not None and intent_view.due_checks():
        # DL2 (§5.2): one item per due "Check once", the top-ranked of its
        # candidates; the dated request is that item.
        queue, chosen_checks = intent_view.pick_checks(queue)
        chosen = set(chosen_checks)
        check_item_ids = frozenset(chosen)
        candidates = {item_id for check in intent_view.due_checks() for item_id in check.candidates}
        requested_item_ids = [
            item_id for item_id in requested_item_ids if item_id not in candidates or item_id in chosen
        ]
    # Propensity is computed on the greedy-sorted order, before exploration reorders
    # it: it is P(this candidate is served | slate) under the seeded exploration
    # policy, which is what off-policy estimation reweights by.
    propensity_by_id = _selection_propensities(queue, session, config)
    greedy_queue = list(queue)
    # mvp-0.21 (voi_stopping): no teach-back count; each teach-back stays
    # while its value, conditional on those already kept, pays for its
    # minutes (a teach-back is a valued probe, router D11). Valued once,
    # before the draw.
    # A due check's teach-back is the learner's request, served, not valued
    # (DL2 verify F14, fix round 4 R2): it is left out of the value
    # admission and kept by the cap without counting toward it.
    teach_back_admitted, teach_back_voi_decisions = _teach_back_value_admission(
        vault,
        voi_context,
        [scheduled for scheduled in greedy_queue if scheduled.practice_item_id not in check_item_ids]
        if check_item_ids
        else greedy_queue,
        config,
    )
    queue = _apply_seeded_exploration(queue, session, config, now)

    def compose(composed: list[ScheduledItem], *, record: bool) -> list[ScheduledItem]:
        # The deterministic composition after the exploration draw. One function
        # for the live build and for router R1's counterfactual outcomes, so an
        # offer's logged propensity is computed through exactly these steps;
        # ``record`` is False only for those counterfactuals (no audit rows).
        composed = _enforce_teach_back_session_cap(
            composed, config.teach_back.session_cap, admitted=teach_back_admitted, keep=check_item_ids
        )
        # Goal-composition quota: guarantee a floor share of goal-frontier items in the
        # ordered queue while a goal has at-risk facets. Applied before the limit slice
        # so the floor holds even in short sessions, and before follow-up insertion
        # (force-inserted follow-ups are a separate triggered decision).
        composed = _apply_goal_quota(composed, frontier.quota_floor)
        # Requested-items floor (spec §4a): the learner explicitly asked to chase a
        # promoted item, so guarantee up to N of them a front slot. Applied AFTER the
        # goal quota — the goal quota establishes its floor first, then this pulls at
        # most `requested_items_per_session` items to the very front, displacing the
        # goal prefix by at most that many positions (a tiny cap, default 1). Reorder
        # only: it can never surface a requested item that failed eligibility/gates,
        # because it only touches items already in the built (eligible) queue.
        composed = _apply_requested_floor(
            composed,
            requested_item_ids,
            config.tutor_promotion.requested_items_per_session,
        )
        composed = _rotate_same_day_frontier_repeats(composed, item_states, now)
        composed = _insert_pending_followups(
            vault, composed, pending_followups, readiness_factor, item_states=item_states
        )
        return _apply_contrast_pair_order(
            vault, repository, composed, session, clock=clock, record=record
        )

    queue = compose(queue, record=True)
    active_session_presentation = (
        repository.active_probe_presentation_for_session(session.session_id)
        if session.session_id is not None
        else None
    )
    if active_session_presentation is not None and probe_block_reason is not None:
        repository.end_probe_presentation(
            active_session_presentation.id,
            end_reason="invalidated",
            clock=clock,
        )
        active_session_presentation = None
    if active_session_presentation is not None:
        # A selected presentation is a durable assignment, not a suggestion to
        # recompute on every queue refresh. Keep it at the front until it is
        # served/consumed or explicitly ended.
        assigned = next(
            (
                item
                for item in queue
                if item.practice_item_id == active_session_presentation.practice_item_id
            ),
            None,
        )
        if assigned is not None:
            queue = [assigned] + [item for item in queue if item is not assigned]
        else:
            repository.end_probe_presentation(
                active_session_presentation.id,
                end_reason="invalidated",
                clock=clock,
            )
            active_session_presentation = None
    considered_queue = list(queue)
    if limit is not None:
        queue = queue[:limit]
    # §11.2 intent-first composition — SHADOW ONLY. Compute the intent + rankings
    # over the already-composed live queue and log them alongside live behavior;
    # the live queue is NOT reordered (promotion needs held-out gains, not here).
    shadow_intent = None
    if vault.config.probe.shadow.enabled:
        from learnloop.scheduling.intent_planner import shadow_intent_plan

        shadow_intent = shadow_intent_plan(vault, considered_queue)
    traced_slate_id: str | None = None
    traced_candidate_ids: dict[str, str] = {}
    if persist_explanations and session.session_id is not None:
        selected_ids = {item.practice_item_id for item in queue}
        explanations = [
            _explanation_payload(
                item,
                selected=item.practice_item_id in selected_ids,
                # Later composition and learner choice change the action
                # distribution. The pre-composition draw is not an OPE weight.
                selection_propensity=None,
            )
            for item in considered_queue
        ] + [
            # "No silent caps": reserved diagnostic surfaces excluded by the
            # freshness rules are logged as unselected candidates, so the slate
            # says WHY a probe surface was withheld instead of omitting it.
            _explanation_payload(excluded, selected=False, selection_propensity=None)
            for excluded in probe_reserved_exclusions
        ]
        # Same contract for the cold lane: a single-use measurement held back
        # because its answer was revealed is visible in the slate instead of
        # looking like the task silently vanishing for a day. Merged onto the
        # item's own row when it is already a candidate (the cold item is an
        # ordinary practice card too, and the slate holds one row per item);
        # appended as an unselected annotation when the deferral is the only
        # reason the item was considered at all.
        explanations = _merge_cold_deferral_explanations(
            vault, explanations, cold_deferrals, readiness_factor
        )
        probe_presentation = None
        probe_forecast_context: tuple[str, int] | None = None
        if queue:
            selected = queue[0]
            episode = open_episodes.get(selected.learning_object_id)
            if (
                episode is not None
                and episode.status == "in_progress"
                and selected.components.get("probe_eig", 0.0) > 0.0
                and active_session_presentation is None
                and repository.active_probe_presentation(episode.id) is None
                and probe_block_reason is None
            ):
                context = _load_episode_context(
                    vault, repository, episode, episode_posterior_cache
                )
                if context is not None:
                    eligible_by_id = _load_episode_eligible(
                        vault,
                        repository,
                        episode,
                        context,
                        episode_eligible_cache,
                    )
                    eligible = eligible_by_id.get(selected.practice_item_id)
                    if eligible is not None:
                        extra_components = None
                        if vault.config.probe.shadow.enabled:
                            from learnloop.diagnosis.calibration_sessions import (
                                routine_planner_shadow,
                            )

                            planner = routine_planner_shadow(vault, repository, episode.id)
                            if planner is not None:
                                extra_components = {"shadow_planner": planner}
                        if selected.components.get("exploration_selected", 0.0) > 0.0:
                            # Router R1 (mvp-0.15): the seeded exploration moved
                            # this probe to the front; it is not the EIG pick
                            # the presentation's other components describe.
                            extra_components = {
                                **(extra_components or {}),
                                "scheduler_exploration": {
                                    "mechanism": "scheduler_seeded_exploration",
                                    "exploration_selected": True,
                                    "exploration_rate": selected.components.get("exploration_rate"),
                                    "exploration_propensity": propensity_by_id.get(
                                        selected.practice_item_id, 0.0
                                    ),
                                    "greedy_item_id": greedy_queue[0].practice_item_id,
                                },
                            }
                        voi_decision = voi_probe_decisions.get(episode.id)
                        if voi_decision is not None:
                            # mvp-0.21: the continue decision that admitted
                            # this observation. It names value's own pick
                            # (``recommended_ref``) and the item served, with
                            # the SERVED item's complete forecast and how it
                            # came to the front (router R1's seeded
                            # exploration and its propensity, or the queue's
                            # greedy order), so calibration scores the answer
                            # against the forecast of the question asked.
                            explored = selected.components.get("exploration_selected", 0.0) > 0.0
                            served_by: dict[str, Any] = {
                                "mechanism": (
                                    "scheduler_seeded_exploration" if explored else "scheduler_greedy_order"
                                ),
                                # Review F11: the probability this item heads
                                # the COMPOSED queue (every draw outcome
                                # recomposed as the build composes), not the
                                # pre-composition draw's, which is kept apart.
                                "selection_propensity": _composed_head_probability(
                                    selected.practice_item_id,
                                    greedy_queue=greedy_queue,
                                    considered=considered_queue,
                                    session=session,
                                    config=config,
                                    compose=compose,
                                    pinned_item_id=None,
                                ),
                                "selection_propensity_kind": "composed_outcomes",
                                "base_draw_propensity": propensity_by_id.get(selected.practice_item_id, 0.0),
                                "greedy_item_id": greedy_queue[0].practice_item_id,
                            }
                            if explored:
                                served_by["exploration_rate"] = selected.components.get("exploration_rate")
                            # The multi-family EVSI study's rank 1: where value
                            # outranked the robust completion gate, the
                            # committed receipt says what the gate would have
                            # said (computed once per committed observation).
                            gate_applies, gate_verdict = robust_gate_counterfactual(
                                vault, repository, episode, context[1]
                            )
                            if gate_applies:
                                voi_decision = voi.with_robust_gate_counterfactual(voi_decision, gate_verdict)
                            extra_components = {
                                **(extra_components or {}),
                                "voi_stopping": voi_decision.as_dict(
                                    served_ref=selected.practice_item_id, served_by=served_by
                                ),
                            }
                        try:
                            probe_presentation = presentation_commit_payload(
                                vault,
                                repository,
                                episode,
                                eligible,
                                candidates=list(eligible_by_id.values()),
                                extra_selection_components=extra_components,
                                clock=clock,
                            )
                        except RoutineDisplayCovered:
                            # UX Phase 4 round 7: its answer was just shown on
                            # a routine display. No presentation is committed;
                            # the slate still records and the item is served
                            # as ordinary practice.
                            probe_presentation = None
                        else:
                            probe_forecast_context = (episode.learning_object_id, len(eligible_by_id))
        ability_by_lo: dict[str, dict[str, object]] = {}
        # The decision_features receipt reads the error events through the
        # diagnosis overlay (owner decision 2026-10-12/13, the Guide-fix
        # audit's question 3): on a split vault its misconception posterior is
        # the diagnoser's verdict, not the blind grader's taxonomy prior. A
        # joint-graded event reads as stored, so a joint vault logs what it
        # always logged. Logging only: nothing here is served.
        feature_errors_by_lo = _errors_by_learning_object(repository.active_error_events_overlaid())
        for explanation in explanations:
            explanation["components"]["base_selection_propensity"] = propensity_by_id.get(explanation["practice_item_id"], 0.0)
            explanation["propensity_kind"] = UNAVAILABLE_PROPENSITY_KIND
            decision_item = vault.practice_items.get(explanation["practice_item_id"])
            if decision_item is None:
                continue
            features = _selection_decision_features(
                vault,
                decision_item,
                mastery_states=mastery_states,
                facet_states_by_lo=facet_states_by_lo,
                errors_by_lo=feature_errors_by_lo,
                quality_states=quality_states,
                ability_by_lo=ability_by_lo,
            )
            if features is not None:
                explanation["decision_features"] = features
        slate_id = repository.record_scheduler_slate(
            explanations,
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            requested_limit=limit,
            session_context=_session_context(session, short_session=short_session, readiness_factor=readiness_factor, shadow_intent=shadow_intent),
            config_snapshot=_scheduler_config_snapshot(config),
            selection_policy=SELECTION_POLICY,
            probe_presentation=probe_presentation,
            clock=clock,
        )
        candidates = {row["practice_item_id"]: row["id"] for row in repository.scheduler_slate_candidates(slate_id)}
        queue = [replace(scheduled, scheduler_slate_id=slate_id, scheduler_candidate_id=candidates[scheduled.practice_item_id]) for scheduled in queue]
        if voi_probe_decisions or teach_back_voi_decisions:
            # mvp-0.21 composed with EVSI calibration: the value decisions this
            # offer acted on (teach-backs kept or dropped, probes withheld) are
            # forecasts, one per decision per offer (router R1's grain), with
            # R1's exploration marker on a teach-back the draw moved forward.
            voi.record_offer_value_forecasts(
                vault,
                repository,
                slate_id=slate_id,
                candidate_ids=candidates,
                probe_decisions=voi_probe_decisions,
                teach_back_receipts=teach_back_voi_decisions,
                exploration_by_item={
                    scheduled.practice_item_id: {
                        "mechanism": "scheduler_seeded_exploration",
                        "exploration_selected": True,
                        "exploration_rate": scheduled.components.get("exploration_rate"),
                        "exploration_propensity": propensity_by_id.get(scheduled.practice_item_id, 0.0),
                        "greedy_item_id": greedy_queue[0].practice_item_id if greedy_queue else None,
                    }
                    for scheduled in queue
                    if scheduled.components.get("exploration_selected", 0.0) > 0.0
                },
                clock=clock,
            )
        committed = repository.active_probe_presentation_for_session(session.session_id)
        if (
            committed is not None
            and probe_presentation is not None
            and probe_forecast_context is not None
            and committed.practice_item_id == probe_presentation["practice_item_id"]
        ):
            # EVSI calibration Part B: the selection's forecast, logged beside
            # it (no serving change; idempotent per presentation).
            record_presentation_forecast(
                vault,
                repository,
                committed,
                learning_object_id=probe_forecast_context[0],
                candidate_count=probe_forecast_context[1],
                clock=clock,
            )
        if committed is not None:
            for scheduled in queue:
                scheduled.components["probe_committed"] = (
                    1.0 if scheduled.practice_item_id == committed.practice_item_id else 0.0
                )
        repository.insert_scheduler_explanations(
            explanations,
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            retention_limit=config.scheduler.candidate_log_retention_limit,
            clock=clock,
        )
        _record_probe_elicitation(
            repository, queue, probe_item_ids, session, entropy_before=probe_entropy_before, clock=clock
        )
        traced_slate_id, traced_candidate_ids = slate_id, candidates
    if offer_trace is not None:
        _fill_offer_trace(
            offer_trace,
            config=config,
            session=session,
            now=now,
            limit=limit,
            greedy_queue=greedy_queue,
            considered=considered_queue,
            compose=compose,
            base_propensity=propensity_by_id,
            pinned_item_id=(
                active_session_presentation.practice_item_id
                if active_session_presentation is not None
                else None
            ),
            probe_block_reason=probe_block_reason,
            cold_deferrals=cold_deferrals,
            slate_id=traced_slate_id,
            candidate_ids=traced_candidate_ids,
            placement_active=placement_serving is not None,
            session_context=_session_context(
                session, short_session=short_session, readiness_factor=readiness_factor
            ),
        )
        offer_trace.voi_decisions = tuple(
            [decision.as_dict() for _episode_id, decision in sorted(voi_probe_decisions.items())]
            + list(teach_back_voi_decisions)
        )
        if voi.voi_stopping_active(config, voi.SITE_TEACH_BACK):
            offer_trace.teach_back_exclusion_reason = "teach_back_value_below_minutes_cost"
    return queue


def probe_ties_admitted(config: LearnLoopConfig) -> bool:
    """Router R1's successor (``mvp-0.15``): probe near-ties join the tie-break.

    True only at a ``PROBE_TIE_VERSIONS`` member with the kill switch
    ``router.probe_tie_admission`` on; otherwise the exploration keeps the
    predecessor's probe exclusion exactly.
    """

    router = getattr(config, "router", None)
    return (
        config.algorithms.algorithm_version in PROBE_TIE_VERSIONS
        and bool(getattr(router, "probe_tie_admission", False))
    )


def _is_probe_intent(item: ScheduledItem) -> bool:
    return (item.reward_debug or {}).get("intent") == SchedulerIntent.PROBE.value


def _exploration_support(
    queue: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
) -> tuple[float, list[ScheduledItem]] | None:
    """The seeded epsilon tie-break's design: ``(rate, near-tie alternatives)``.

    ``None`` means the build is greedy: exploration is off (its rate, or the
    session's ``seeded_exploration``), there is no session to seed it, a single
    candidate, no alternative within the reward window,
    or (below the probe-tie successor) a PROBE-intent best. Before ``mvp-0.15``
    PROBE-intent items (in-episode diagnostic probes and teach-backs) are never
    displaced and never explored to; at ``mvp-0.15`` with
    ``router.probe_tie_admission`` they are ordinary near-ties (teach-backs
    included: owner decision D11, a teach-back dialogue is a high-value probe).
    """

    rate = clamp(config.scheduler.selection_exploration_rate)
    if rate <= 0 or session.session_id is None or not session.seeded_exploration or len(queue) < 2:
        return None
    admit_probes = probe_ties_admitted(config)
    best = queue[0]
    if not admit_probes and _is_probe_intent(best):
        return None
    best_reward = best.components.get("selection_reward", 0.0)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    alternatives = [
        item
        for item in queue[1:]
        if (admit_probes or not _is_probe_intent(item))
        and best_reward - item.components.get("selection_reward", 0.0) <= window
    ]
    if not alternatives:
        return None
    return rate, alternatives


def _explore_to_front(
    queue: list[ScheduledItem], selected: ScheduledItem, rate: float
) -> list[ScheduledItem]:
    """The order an exploration draw that chose ``selected`` produces."""

    promoted = replace(
        selected,
        components={
            **selected.components,
            "exploration_selected": 1.0,
            "exploration_rate": rate,
        },
        plain_english=[
            "seeded exploration"
        ] + [reason for reason in selected.plain_english if reason != "seeded exploration"],
    )
    return [promoted] + [
        item
        for item in queue
        if item.practice_item_id != selected.practice_item_id
    ]


def _pin_presentation(
    queue: list[ScheduledItem], practice_item_id: str | None
) -> list[ScheduledItem]:
    """The committed presentation pin, without its invalidation side effect."""

    if practice_item_id is None:
        return list(queue)
    assigned = next((item for item in queue if item.practice_item_id == practice_item_id), None)
    if assigned is None:
        return list(queue)
    return [assigned] + [item for item in queue if item is not assigned]


def _exploration_draws(
    queue: list[ScheduledItem], session: SchedulerSession, now: datetime, alternatives: list[ScheduledItem]
) -> tuple[float, float]:
    """The seeded roll and choice fractions ``_apply_seeded_exploration`` uses."""

    roll = _stable_fraction("roll", str(session.session_id), now, [item.practice_item_id for item in queue])
    choice = _stable_fraction(
        "choice", str(session.session_id), now, [item.practice_item_id for item in alternatives]
    )
    return roll, choice


def _fill_offer_trace(
    trace: OfferTrace,
    *,
    config: LearnLoopConfig,
    session: SchedulerSession,
    now: datetime,
    limit: int | None,
    greedy_queue: list[ScheduledItem],
    considered: list[ScheduledItem],
    compose,
    base_propensity: dict[str, float],
    pinned_item_id: str | None,
    probe_block_reason: str | None,
    cold_deferrals: list[dict[str, Any]],
    slate_id: str | None,
    candidate_ids: dict[str, str],
    placement_active: bool,
    session_context: dict[str, Any] | None = None,
) -> None:
    """Record the build's decision inputs and its exploration's whole support.

    Each outcome of the seeded draw is recomposed through ``compose`` (the live
    build's own composition, without audit writes) and the committed
    presentation pin, so the composed order under every outcome is exactly what
    the build would have produced. Read-only: nothing here changes the queue.
    """

    trace.algorithm_version = config.algorithms.algorithm_version
    trace.session_id = session.session_id
    trace.now_iso = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    trace.limit = limit
    trace.slate_id = slate_id
    trace.candidate_ids = dict(candidate_ids)
    trace.greedy_item_ids = tuple(item.practice_item_id for item in greedy_queue)
    trace.greedy = tuple(greedy_queue)
    trace.considered = tuple(considered)
    trace.base_propensity = dict(base_propensity)
    trace.pinned_item_id = pinned_item_id
    trace.probe_block_reason = probe_block_reason
    trace.cold_deferrals = tuple(dict(row) for row in cold_deferrals)
    trace.placement_active = placement_active
    trace.session_context = dict(session_context or {})
    trace.config_snapshot = {
        "algorithm_version": config.algorithms.algorithm_version,
        "scheduler": config.scheduler.model_dump(mode="json"),
        "teach_back_session_cap": config.teach_back.session_cap,
        "requested_items_per_session": config.tutor_promotion.requested_items_per_session,
        "router": config.router.model_dump(mode="json"),
    }
    if config.algorithms.algorithm_version in voi.VOI_STOPPING_VERSIONS:
        # mvp-0.21: the value-of-information switches shape the build too.
        trace.config_snapshot["voi_stopping"] = config.voi_stopping.model_dump(mode="json")
    rate = clamp(config.scheduler.selection_exploration_rate)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    support = _exploration_support(greedy_queue, session, config)
    exploration: dict[str, Any] = {
        "mechanism": "scheduler_seeded_exploration",
        "rate": rate,
        "reward_window": window,
        "probe_ties_admitted": probe_ties_admitted(config),
        "best_item_id": greedy_queue[0].practice_item_id if greedy_queue else None,
        "alternative_item_ids": [],
        "realized_item_id": None,
    }
    if support is None:
        trace.exploration = exploration
        trace.outcomes = (ExplorationOutcome(None, 1.0, tuple(considered)),)
        trace.realized = 0
        return
    support_rate, alternatives = support
    roll, choice = _exploration_draws(greedy_queue, session, now, alternatives)
    explored = roll < support_rate
    realized_item_id = None
    if explored:
        index = int(choice * len(alternatives))
        realized_item_id = alternatives[min(index, len(alternatives) - 1)].practice_item_id
    exploration.update(
        {
            "alternative_item_ids": [item.practice_item_id for item in alternatives],
            "realized_item_id": realized_item_id,
            "roll": roll,
            "choice": choice,
            # The draw's seed material is (label, session, UTC date, sorted
            # candidate ids); its hash identifies the draw without the ids.
            "seed": hashlib.sha256(
                "|".join(
                    [str(session.session_id), now.date().isoformat(), *sorted(trace.greedy_item_ids)]
                ).encode("utf-8")
            ).hexdigest()[:32],
        }
    )
    outcomes = _support_outcomes(greedy_queue, support, compose, pinned_item_id)
    realized = next(
        (index for index, outcome in enumerate(outcomes) if outcome.explored_item_id == realized_item_id),
        0,
    )
    trace.exploration = exploration
    trace.outcomes = tuple(outcomes)
    trace.realized = realized


def _support_outcomes(
    greedy_queue: list[ScheduledItem],
    support: tuple[float, list[ScheduledItem]],
    compose,
    pinned_item_id: str | None,
) -> list[ExplorationOutcome]:
    """Every outcome of the seeded draw, each recomposed through ``compose``
    (the live build's own composition, without audit writes) and the committed
    presentation pin: the greedy order (when ``1 - rate > 0``) first, then one
    outcome per near-tie alternative."""

    support_rate, alternatives = support
    outcomes: list[ExplorationOutcome] = []
    greedy_probability = 1.0 - support_rate
    if greedy_probability > 0:
        outcomes.append(
            ExplorationOutcome(
                None,
                greedy_probability,
                tuple(_pin_presentation(compose(list(greedy_queue), record=False), pinned_item_id)),
            )
        )
    share = support_rate / len(alternatives)
    for alternative in alternatives:
        pre = _explore_to_front(list(greedy_queue), alternative, support_rate)
        outcomes.append(
            ExplorationOutcome(
                alternative.practice_item_id,
                share,
                tuple(_pin_presentation(compose(pre, record=False), pinned_item_id)),
            )
        )
    return outcomes


def _composed_head_probability(
    practice_item_id: str,
    *,
    greedy_queue: list[ScheduledItem],
    considered: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
    compose,
    pinned_item_id: str | None,
) -> float:
    """``P(practice_item_id heads the composed queue)`` over the seeded draw's
    whole support: each outcome recomposed exactly as the live build composes
    (router R1's offer-trace machinery), so a teach-back value dropped, a
    requested floor or a follow-up insertion is accounted for. Review F11: the
    pre-composition draw probability (``_selection_propensities``) is the
    probability of the draw, not of the item served."""

    support = _exploration_support(greedy_queue, session, config)
    if support is None:
        outcomes = [ExplorationOutcome(None, 1.0, tuple(considered))]
    else:
        outcomes = _support_outcomes(greedy_queue, support, compose, pinned_item_id)
    return float(
        sum(
            outcome.probability
            for outcome in outcomes
            if outcome.composed and outcome.composed[0].practice_item_id == practice_item_id
        )
    )


@dataclass(frozen=True)
class _PlacementServing:
    """What learner-field F2 placement changes about one queue build."""

    open_learning_object_ids: frozenset[str]
    #: Passed their check: remaining learning items withheld (maintenance).
    maintained_learning_object_ids: frozenset[str]
    back_to_learning_learning_object_ids: frozenset[str]
    #: One first-review check item per assumed LO whose review is due.
    check_items: dict[str, str]
    predictor: Any
    #: Learner-text gaps: maintenance LOs whose brought-forward check is due
    #: (mvp-0.16), open assumptions it brought forward, and created LOs whose
    #: light commitment is open (their check is the seed item).
    gap_check_learning_object_ids: frozenset[str] = frozenset()
    advanced_learning_object_ids: frozenset[str] = frozenset()
    committed_learning_object_ids: frozenset[str] = frozenset()


#: Practice modes never used as an assumed-known first review: the check is a
#: normal cold item, not a single-use diagnostic surface or an AI conversation.
_CHECK_EXCLUDED_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "teach_back"})


def _placement_serving(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None,
    persist: bool,
    item_states: Mapping[str, PracticeItemState],
    excluded_item_ids: set[str],
) -> _PlacementServing | None:
    """F2 placement state for one build, or None when placement is off.

    ``excluded_item_ids`` are the build's own exclusions (exam reservations,
    pending rung variants, staged-owned commitments), so a first-review check
    is chosen only among items the queue may actually serve. The check is a
    normal cold item picked for its LO rather than by the routine timing, so
    it also skips an open cold follow-up's reserved item and an item whose
    answer was revealed within the cold retrieval delay
    (``serving_exclusions.out_of_timing_serving_exclusions``), as the quick
    check and ``find_practice`` do.
    """

    from learnloop.placement.decisions import reconcile_fast_track
    from learnloop.placement.predictor import active_predictor
    from learnloop.placement.state import (
        choose_check_items,
        diagnosis_can_arrive,
        load_placement_state,
        placement_active,
    )

    if not placement_active(vault):
        return None
    if persist:
        if not diagnosis_can_arrive(vault):
            # The split's kill switch is off: a queued diagnosis is held, and
            # a miss waiting on it is decided by today's rule. Record the hold
            # on the first serving build that sees it (write-once), so turning
            # the switch back on does not reopen what this build serves on
            # (Codex re-review F3).
            repository.hold_queued_live_diagnoses(clock=clock)
        reconcile_fast_track(vault, repository, clock=clock)
    now_iso = utc_now_iso(clock)
    state = load_placement_state(vault, repository, now_iso=now_iso)
    predictor = active_predictor(vault, repository, now_iso=now_iso)
    # A check answer whose diagnosis has not landed is the check: the decision
    # waits on it (owner decision 2026-10-12), so no second check item is served.
    due = state.due_learning_object_ids(now_iso) - state.awaiting_diagnosis_learning_object_ids
    gap_due = state.due_gap_check_learning_object_ids(now_iso) - state.awaiting_diagnosis_learning_object_ids
    due = due | gap_due
    if due:
        from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
        from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY

        excluded_item_ids = set(excluded_item_ids) | out_of_timing_serving_exclusions(
            vault, repository, cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS,
            reveal_window=COLD_RETRIEVAL_DELAY, clock=clock,
        ).out_of_timing_item_ids
    candidates: dict[str, list[str]] = {}
    for item in vault.practice_items.values():
        if item.learning_object_id not in due or item.status != "active":
            continue
        item_state = item_states.get(item.id)
        if item_state is not None and not item_state.active:
            continue
        if (
            item.id in excluded_item_ids
            or item.practice_mode in _CHECK_EXCLUDED_MODES
            or unservable_reason(item) is not None
            or vault.learning_object_for_item(item) is None
            or not practice_item_servable(vault, item)
        ):
            continue
        candidates.setdefault(str(item.learning_object_id), []).append(item.id)
    attempted = {item_id for item_id, item_state in item_states.items() if item_state.last_attempt_at is not None}
    return _PlacementServing(
        open_learning_object_ids=frozenset(state.open_by_lo),
        maintained_learning_object_ids=state.maintained_learning_object_ids,
        back_to_learning_learning_object_ids=state.back_to_learning_learning_object_ids,
        check_items=choose_check_items(predictor, candidates, attempted_item_ids=attempted),
        predictor=predictor,
        gap_check_learning_object_ids=frozenset(gap_due),
        advanced_learning_object_ids=state.advanced_learning_object_ids,
        committed_learning_object_ids=state.committed_learning_object_ids,
    )


def _order_new_material(
    vault: LoadedVault,
    repository: Repository,
    queue: list[ScheduledItem],
    placement: _PlacementServing,
) -> list[ScheduledItem]:
    """Reorder new-material items among the slots they already hold.

    Field §5.2: new material is ordered by prerequisites, then LOs the learner
    asked about or needed help on (taught first), then the active predictor's
    predicted success, easiest first. Every other item keeps its position, so
    the rest of the queue's composition is unchanged.
    """

    slots = [index for index, scheduled in enumerate(queue) if scheduled.components.get("new_material", 0.0) > 0]
    if not slots:
        return queue
    from learnloop.placement.signals import taught_first_learning_objects
    from learnloop.placement.state import order_new_material

    by_id = {queue[index].practice_item_id: queue[index] for index in slots}
    taught_first = taught_first_learning_objects(
        vault, repository, {queue[index].learning_object_id for index in slots}
    )
    ordered = order_new_material(
        vault,
        placement.predictor,
        [(queue[index].practice_item_id, queue[index].learning_object_id) for index in slots],
        taught_first=taught_first,
    )
    result = list(queue)
    for index, (item_id, components) in zip(slots, ordered, strict=True):
        scheduled = by_id[item_id]
        scheduled.components.update(components)
        if components["taught_first"] > 0:
            scheduled.plain_english.insert(0, "taught first: you asked about this topic or needed help on it")
        result[index] = scheduled
    return result


#: Policy name recorded on every persisted slate built by ``build_due_queue``.
SELECTION_POLICY = "composed_offer_v2"

#: ``propensity_kind`` of every candidate on a composed-offer slate. The offer
#: is composed after the exploration draw and then chosen from by the learner,
#: so no selection propensity is recorded for it.
UNAVAILABLE_PROPENSITY_KIND = "unavailable_composed_offer"

#: Shape tag for ``decision_features`` rows of ``decision_type='selection'``.
#: Components, propensity, policy and collection version are not repeated in
#: the row: they live on the candidate and slate rows its ``decision_id``
#: (the scheduler candidate id) points at.
SELECTION_FEATURE_SCHEMA = "selection_features_v1"


def _selection_decision_features(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    mastery_states: Mapping[str, MasteryState],
    facet_states_by_lo: Mapping[str, list[Any]],
    errors_by_lo: Mapping[str, list[ActiveErrorEvent]],
    quality_states: Mapping[str, PracticeItemQualityState],
    ability_by_lo: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    """Compact, immutable features for one considered candidate.

    The rows are append-only and written for every candidate of every saved
    queue build, so they hold only what the selector consumes: the learner's
    ability vector for the item's learning object and the item's numeric and
    categorical demand. The scored item revision is referenced by the hash of
    its full serialized form; ``item_snapshot`` carries that serialization so
    the repository stores it once per distinct revision in
    ``practice_item_snapshots``.
    """

    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        return None
    learning_object_id = learning_object.id
    ability = ability_by_lo.get(learning_object_id)
    if ability is None:
        ability = _selection_ability_features(
            vault,
            learning_object_id,
            mastery=mastery_states.get(learning_object_id),
            facet_states=facet_states_by_lo.get(learning_object_id, []),
            active_errors=errors_by_lo.get(learning_object_id, []),
        )
        ability_by_lo[learning_object_id] = ability
    demand = item_demand_vector(vault, item, learning_object, quality_states.get(item.id))
    snapshot_hash, item_json = _practice_item_snapshot(item)
    item_demand = {
        "practice_item_id": item.id,
        "content_hash": snapshot_hash,
        **demand.as_dict(),
    }
    return {
        "ability_vector": ability,
        "item_demand_vector": item_demand,
        "context": {
            "feature_schema": SELECTION_FEATURE_SCHEMA,
            # The ability vector's misconception posterior reads the diagnoser's
            # verdict where one is in force (the overlay); said, not silent.
            "error_events": "diagnosis_overlay",
        },
        "item_snapshot": {
            "content_hash": snapshot_hash,
            "practice_item_id": item.id,
            "item_json": item_json,
        },
    }


def _practice_item_snapshot(item: PracticeItem) -> tuple[str, str]:
    """Canonical JSON of the whole item and the SHA-256 of exactly that text.

    ``practice_item_hash`` covers only the grading-relevant fields, so two
    revisions that differ in a scored demand field (scaffold level, transfer
    distance, surface family) would share it. The snapshot key must change
    whenever anything the selector could have read changes.
    """

    item_json = json.dumps(
        item.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(item_json.encode("utf-8")).hexdigest(), item_json


def _selection_ability_features(
    vault: LoadedVault,
    learning_object_id: str,
    *,
    mastery: MasteryState | None,
    facet_states: list[Any],
    active_errors: list[ActiveErrorEvent],
) -> dict[str, object]:
    """The selector's ability vector plus the mastery summary behind it.

    ``LearnerAbilityVector`` squashes the mastery logit; the blueprint
    correctness projection also reads the raw logit and its evidence count, so
    both are kept to make the recorded features sufficient to recompute it.
    """

    ability = ability_vector(
        learning_object_id,
        mastery,
        facet_states,
        active_errors,
        facet_aliases=vault.facet_aliases,
    ).as_dict()
    ability["mastery"] = (
        {
            "logit_mean": mastery.logit_mean,
            "logit_variance": mastery.logit_variance,
            "evidence_count": mastery.evidence_count,
            "last_evidence_at": mastery.last_evidence_at,
        }
        if mastery is not None
        else None
    )
    return ability


#: Learner-facing reason per delayed follow-up lane. Keyed on the
#: ``followup_tasks.kind`` the repository now passes through as ``action_type``.
FOLLOWUP_REASONS: dict[str, str] = {
    "cold_retry": "unassisted cold retry",
    "certification_cold_probe": "held-out check on a certified skill",
}

#: Follow-up lanes that ride the ``intervention_followup`` priority component.
#: Anything outside this set is treated as a negative-surprise insertion, which
#: is also the ``action_type`` default when a task does not name one.
_INTERVENTION_FOLLOWUP_KINDS: frozenset[str] = frozenset(
    {"intervention_followup", "cold_retry", "certification_cold_probe"}
)

#: Task kinds created by explicit repair/diagnostic JOURNEYS, whose by-id
#: selections are honored even when they name a ``diagnostic_probe`` item the
#: learner has already administered. Today that is exactly the remediation
#: ``cold_retry`` lane: its cold item is chosen at prescription time as part of
#: the repair measurement pair, and refusing the injection would strand the
#: episode in ``cold_scheduled`` forever. (In practice the remediation ranker
#: never picks an administered diagnostic item — attempt recording deactivates
#: it and ``_rank_items`` skips inactive state — so the allowlist protects
#: explicit-journey injections, not staleness.) Probe-episode serving does not
#: ride ``followup_tasks`` at all (it commits presentations), so no episode
#: kind appears here. Every OTHER kind — ``certification_cold_probe``,
#: ``intervention_followup``, ``negative_surprise_followup`` — is a generic
#: selection and must not resurrect a burned single-use surface: selection
#: time refuses to pick one (followups / certification_cold_probe), and the
#: serving door below refuses a stale task that still names one.
REPAIR_JOURNEY_TASK_KINDS: frozenset[str] = frozenset({"cold_retry"})


def _cold_task_reveals(
    repository: Repository,
    *,
    item_id: str,
    learning_object_id: str | None,
    since: str,
    now_iso: str,
) -> list[tuple[dict[str, Any], str]]:
    """The reveals that hold a cold task back now, each with the first moment it
    no longer holds it (ledger format), oldest first.

    Every reveal kind except the routine displays: one on the task's item or
    learning object after the task was created, counting for the lane's own
    retrieval delay (the reveals before it were visible to the scheduling
    decision). A routine full-answer display counts by its coverage, the one
    definition the submit path reads too (``learnloop.reveal_coverage``, UX
    Phase 4 round 4): whenever it was stamped, until its coverage ends, and
    also when stamped after now (the clock went back). So the queue never
    serves a cold task whose submission auto-prime would refuse ("a cold retry
    must be unassisted and unprimed").
    """

    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
    from learnloop.reveal_coverage import is_routine_display, routine_released_at, routine_row_covers

    held: dict[str, tuple[dict[str, Any], str]] = {}
    for row in repository.reveal_events_for_target(
        practice_item_id=item_id or None,
        learning_object_id=learning_object_id,
        since=since or None,
        until=now_iso,
    ):
        if is_routine_display(row.get("source_kind"), row.get("basis")):
            continue
        stamped = parse_utc(str(row.get("created_at") or ""))
        if stamped is None:
            continue
        until = (stamped.astimezone(UTC) + COLD_RETRIEVAL_DELAY).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        held[str(row.get("id"))] = (row, until)
    for row in repository.reveal_events_for_target(
        practice_item_id=item_id or None,
        learning_object_id=learning_object_id,
    ):
        if not is_routine_display(row.get("source_kind"), row.get("basis")):
            continue
        created_at = str(row.get("created_at") or "")
        released = routine_released_at(created_at)
        if released is not None and routine_row_covers(created_at, now_iso):
            held[str(row.get("id"))] = (row, released)
    return sorted(held.values(), key=lambda pair: (str(pair[0].get("created_at") or ""), str(pair[0].get("id") or "")))


def cold_check_decision(
    vault: LoadedVault,
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
    now_iso: str | None = None,
    learning_object_id: str | None = None,
):
    """The one eligibility decision for serving the item's cold check now
    (``serve_eligibility.decide(..., COLD_CHECK)``): serve it, serve the item
    as ordinary practice (re-timing the due cold task), or defer it until a
    time-bounded hold lifts. Every cold-check serve path asks this."""

    from learnloop import serve_eligibility

    item = vault.practice_items.get(practice_item_id)
    lo = (str(getattr(item, "learning_object_id", "") or "") or None) if item is not None else learning_object_id
    inputs = serve_eligibility.gather(
        repository, practice_item_id=practice_item_id, learning_object_id=lo, at=now_iso or utc_now_iso(clock),
    )
    return serve_eligibility.decide(inputs, serve_eligibility.COLD_CHECK)


def apply_eligibility_writes(
    vault: LoadedVault,
    repository: Repository,
    decision: Any,
    *,
    clock: Clock | None = None,
) -> None:
    """Act on a cold-check decision's writes (the one eligibility decision's
    imperative shell): its re-times (monotone pushes of a time-bounded hold)
    and its withdrawals (a check the item can no longer take cold ends now,
    with its typed disposition: ``remediation.withdraw_cold_measurement``)."""

    from learnloop import serve_eligibility
    from learnloop.diagnosis.remediation import withdraw_cold_measurement

    serve_eligibility.retime(repository, decision, clock=clock)
    for task_id, reason in decision.withdrawals:
        withdraw_cold_measurement(
            vault, repository, task_id, reason=reason, reveal_event_ids=decision.reveal_event_ids,
            decision=decision.record(), clock=clock,
        )


def _defer_revealed_cold_followups(
    vault: LoadedVault,
    repository: Repository,
    pending_followups: list[dict[str, str]],
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """The queue's cold lane: hold back, or withdraw, due cold tasks that
    cannot be served as cold checks now.

    At ``mvp-0.27`` with ``eligibility.enabled`` it asks the one eligibility
    decision (``serve_eligibility``) per item, so the lane never serves a cold
    check submit would refuse:

    * ``defer_until``: a time-bounded hold (a non-routine reveal on the item or
      its learning object since the task was created, for the lane's delay; a
      routine display's coverage): the task is withheld and its push persisted,
      exactly as the lane always deferred;
    * ``serve_as_ordinary``: the item can never give the task a cold reading
      (submit primes it with no lapse, or it was attempted since the task was
      set): the task is withdrawn with its typed disposition and the item stays
      in the queue as ordinary practice, labelled (Codex review F2, F3).

    The writes are persisted only on a build that is already allowed to write
    (``persist_explanations``); a side-effect-free build still withholds the
    task and recomputes the same decision next time. ``expires_at`` is never
    extended. Non-cold lanes are untouched. Below the tag, or with the switch
    off, the lane is mvp-0.26's (:func:`_predecessor_defer_revealed_cold_followups`).
    """

    from learnloop import serve_eligibility

    if not serve_eligibility.decision_active(vault):
        return _predecessor_defer_revealed_cold_followups(
            vault, repository, pending_followups, clock=clock, persist=persist
        )
    if not pending_followups:
        return pending_followups, []

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

    # Second-resolution, exactly like every other timestamp the lane writes
    # (`clock.utc_now_iso`): these strings are compared against stored ones.
    now_iso = utc_now_iso(clock)
    kept: list[dict[str, str]] = []
    deferrals: list[dict[str, Any]] = []
    decisions: dict[str, Any] = {}
    applied: set[str] = set()
    for pending in pending_followups:
        task_id = pending.get("followup_task_id")
        if not task_id or pending.get("action_type") not in COLD_FOLLOWUP_TASK_KINDS:
            kept.append(pending)
            continue
        task = repository.followup_task(str(task_id))
        if task is None:
            kept.append(pending)
            continue
        item_id = str(task.get("selected_item_id") or "")
        # The one eligibility decision (``serve_eligibility``), per item: the
        # scheduler's deferral scope (the item or its learning object, since
        # the task was created, for the lane's delay), routine-display
        # coverage, AND submit's own verdict, so the lane never serves a cold
        # check submit would refuse.
        try:
            decision = decisions.get(item_id)
            if decision is None:
                decision = decisions[item_id] = cold_check_decision(
                    vault, repository, item_id, now_iso=now_iso,
                    learning_object_id=str(task.get("learning_object_id") or "") or None,
                )
        except Exception:  # pragma: no cover - a ledger read must not break the queue
            kept.append(pending)
            continue
        if persist and decision.writes and item_id not in applied:
            applied.add(item_id)
            apply_eligibility_writes(vault, repository, decision, clock=clock)
        withdrawn = dict(decision.withdrawals)
        if str(task_id) not in withdrawn and (
            decision.verdict == serve_eligibility.SERVE or str(task_id) not in decision.task_ids
        ):
            kept.append(pending)
            continue
        retimes = dict(decision.retimes)
        deferred_to = None if str(task_id) in withdrawn else (retimes.get(str(task_id)) or decision.until or now_iso)
        selected_item = vault.practice_items.get(item_id) if item_id else None
        reveals = [
            row
            for row in repository.reveal_events_for_target(
                practice_item_id=item_id or None,
                learning_object_id=(
                    str(getattr(selected_item, "learning_object_id", "") or "") or None
                    if selected_item is not None
                    else (str(task.get("learning_object_id") or "") or None)
                ),
            )
            if str(row.get("id")) in decision.reveal_event_ids
        ]
        expires_at = str(task.get("expires_at") or "")
        withdrawal = withdrawn.get(str(task_id))
        deferral = {
            "followup_task_id": str(task_id),
            "practice_item_id": item_id or None,
            "kind": str(task.get("kind") or ""),
            "remediation_episode_id": (
                str(task.get("remediation_episode_id") or "") or None
            ),
            "reveal_event_ids": list(decision.reveal_event_ids),
            "reveal_amount": sum(float(row.get("amount") or 0.0) for row in reveals),
            "last_reveal_at": max((str(row.get("created_at") or "") for row in reveals), default=None),
            "deferred_to": deferred_to,
            "expires_at": expires_at or None,
            # No expiry extension: past this point the deferral simply outlives
            # the task and the expiry sweep records the censoring.
            "beyond_expiry": bool(expires_at and deferred_to and deferred_to > expires_at),
            "delay_seconds": serve_eligibility.COLD_RETRIEVAL_DELAY.total_seconds(),
            "reason": withdrawal or decision.reason,
            "served_as_practice": withdrawal is not None,
            "withdrawn": withdrawal is not None,
        }
        # A session build also writes the slate annotation below; the log line
        # is what a CLI or session-less build leaves behind, so the deferral is
        # never invisible on any path.
        serve_eligibility.log_decision(decision, path="queue_cold_lane")
        logger.info(
            "cold %s task %s %s: %d reveal(s) (%s)",
            deferral["kind"],
            task_id,
            "withdrawn, its item served as practice" if withdrawal else f"deferred to {deferred_to}",
            len(decision.reveal_event_ids),
            deferral["reason"],
        )
        deferrals.append(deferral)
        if withdrawal is not None and not any(
            entry.get("practice_item_id") == item_id and entry.get("action_type") == ANSWER_SHOWN_PRACTICE
            for entry in kept
        ):
            # The item can no longer be the cold check: it stays in the queue as
            # ordinary practice, labelled; the check itself was withdrawn.
            kept.append({
                "practice_item_id": item_id,
                "action_type": ANSWER_SHOWN_PRACTICE,
                "followup_task_id": str(task_id),
                "practice_reason": decision.message or "",
            })
    return kept, deferrals


def _predecessor_defer_revealed_cold_followups(
    vault: LoadedVault,
    repository: Repository,
    pending_followups: list[dict[str, str]],
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """mvp-0.26's cold lane, kept exactly for the predecessor and the kill switch
    (``eligibility.enabled = false``): hold back due cold tasks whose answer has
    been revealed since creation.

    A cold task is a SINGLE-USE measurement: the first attempt on its item
    consumes it, and whatever that attempt was worth is what the episode
    records forever. The submit path already refuses an assisted or auto-primed
    cold attempt (``attempts._resolve_attempt_target``), but that refusal
    arrives after the learner has typed an answer, and it protects the receipt
    rather than the measurement — the task stays due, so the next serve walks
    into the same wall. Serving is where it can still be spent well: if the
    reveal ledger (migration 154) has a row for the task's selected item, or
    anywhere in its learning object, dated after the task was created, the task
    is withheld from this build and its ``not_before`` is pushed to the last
    such reveal plus the lane's own retrieval delay — the same +1 day that made
    the original schedule cold.

    Deliberately bounded:

    * ``expires_at`` is NEVER extended. An episode that keeps being revealed
      runs out its original 30-day window and lands ``right_censored_expired``
      through ``causal_orchestrator.sweep_expired_cold_retries``. "We could not
      get a clean measurement" is an honest ending; a measurement window that
      grows every time the answer is shown is not.
    * The push is persisted only on a build that is already allowed to write
      (``persist_explanations``); a deliberately side-effect-free build still
      withholds the task, it just recomputes the same decision next time.
    * Non-cold follow-up lanes are untouched: an intervention follow-up is a
      re-practice, not a measurement, and being shown the answer is not a
      reason to withhold it.
    """

    if not pending_followups:
        return pending_followups, []

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY

    # Second-resolution, exactly like every other timestamp the lane writes
    # (`clock.utc_now_iso`): these strings are compared against stored ones.
    now_iso = utc_now_iso(clock)
    kept: list[dict[str, str]] = []
    deferrals: list[dict[str, Any]] = []
    for pending in pending_followups:
        task_id = pending.get("followup_task_id")
        if not task_id or pending.get("action_type") not in COLD_FOLLOWUP_TASK_KINDS:
            kept.append(pending)
            continue
        task = repository.followup_task(str(task_id))
        if task is None:
            kept.append(pending)
            continue
        item_id = str(task.get("selected_item_id") or "")
        selected_item = vault.practice_items.get(item_id) if item_id else None
        # The selected item's LO, not the task's column: the repair lane leaves
        # `followup_tasks.learning_object_id` NULL, and the LO is exactly the
        # scope a reveal has to be judged in. Note the asymmetry with the
        # RECEIPT, which treats an LO-wide reveal as soft: a receipt asks
        # whether a measurement already taken was contaminated, this asks
        # whether NOW is the moment to spend a single-use one, and "wait a day"
        # costs nothing while a wrong answer to the first question costs the
        # whole episode.
        learning_object_id = (
            str(getattr(selected_item, "learning_object_id", "") or "") or None
            if selected_item is not None
            else (str(task.get("learning_object_id") or "") or None)
        )
        # The task's own creation is the window start: reveals BEFORE it were
        # already visible to the scheduling decision (the primed attempt that
        # created the task is itself the licensed exposure), so re-counting them
        # would defer every cold retry the moment its own repair spent budget.
        since = str(task.get("created_at") or "")
        try:
            held = _cold_task_reveals(
                repository, item_id=item_id, learning_object_id=learning_object_id, since=since, now_iso=now_iso,
            )
        except Exception:  # pragma: no cover - a ledger read must not break the queue
            kept.append(pending)
            continue
        if not held:
            kept.append(pending)
            continue
        reveals = [row for row, _until in held]
        last_at = max(str(row.get("created_at") or "") for row in reveals)
        # Pushed to when the last reveal stops counting: the lane's delay after
        # an ordinary reveal, a routine display's coverage (round 4).
        deferred_to = max(until for _row, until in held)
        if deferred_to <= now_iso:
            # The delay has already elapsed since the last reveal: the task is
            # cold again on its own terms and is served normally.
            kept.append(pending)
            continue
        expires_at = str(task.get("expires_at") or "")
        deferral = {
            "followup_task_id": str(task_id),
            "practice_item_id": item_id or None,
            "kind": str(task.get("kind") or ""),
            "remediation_episode_id": (
                str(task.get("remediation_episode_id") or "") or None
            ),
            "reveal_event_ids": [str(row.get("id") or "") for row in reveals],
            "reveal_amount": sum(float(row.get("amount") or 0.0) for row in reveals),
            "last_reveal_at": last_at,
            "deferred_to": deferred_to,
            "expires_at": expires_at or None,
            # No expiry extension: past this point the deferral simply outlives
            # the task and the expiry sweep records the censoring.
            "beyond_expiry": bool(expires_at and deferred_to > expires_at),
            "delay_seconds": COLD_RETRIEVAL_DELAY.total_seconds(),
        }
        if persist:
            repository.defer_followup_task(
                str(task_id), not_before=deferred_to, clock=clock
            )
        # A session build also writes the slate annotation below; the log line
        # is what a CLI or session-less build leaves behind, so the deferral is
        # never invisible on any path.
        logger.info(
            "cold %s task %s deferred to %s: %d reveal(s) since %s",
            deferral["kind"],
            task_id,
            deferred_to,
            len(reveals),
            since,
        )
        deferrals.append(deferral)
    return kept, deferrals


#: The pending entry a cold task leaves when its item is served as practice
#: instead (``serve_eligibility.SERVE_AS_ORDINARY``, the check withdrawn): no
#: follow-up lane.
ANSWER_SHOWN_PRACTICE = "answer_shown_practice"


#: Why a cold check cannot be served as one now (``cold_check_serve_hold``).
COLD_CHECK_ROUTINE_DISPLAY = "cold_check_routine_display"


#: When a routine-display hold's release cannot be read (an unreadable
#: stamp): held, and never lifting on its own clock (fail closed).
COLD_CHECK_HOLD_UNKNOWN_RELEASE = "9999-12-31T23:59:59Z"


def cold_check_hold_until(
    vault: LoadedVault,
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> str | None:
    """When a cold check's hold lifts (ledger format), or None when it is not
    held: the one eligibility decision's ``defer_until``
    (``serve_eligibility``). Every hold is time-bounded (round-6 ruling 2):
    routine-display coverage (D + G), a reveal since the task was created
    (one cold delay), or a submit priming that only routine displays cause.
    Every open, unexpired cold task on the item that falls due within the hold
    is judged, so a task for later never masks one due now (round 6, E); the
    held ones are deferred, persisted when ``persist``. An unreadable stamp
    holds, with :data:`COLD_CHECK_HOLD_UNKNOWN_RELEASE` and nothing persisted.

    A cold check the item can no longer take cold (submit primes it with no
    lapse, or it was practised since the check was set) is not held: it is
    withdrawn (persisted when ``persist``) and the item served as ordinary
    practice, so this returns None. Below ``mvp-0.27``, or with
    ``eligibility.enabled`` off, it is mvp-0.26's routine-display hold
    (:func:`_predecessor_cold_check_hold_until`)."""

    from learnloop import serve_eligibility

    if not serve_eligibility.decision_active(vault):
        return _predecessor_cold_check_hold_until(vault, repository, practice_item_id, clock=clock, persist=persist)
    decision = cold_check_serve_decision(vault, repository, practice_item_id, clock=clock, persist=persist)
    if decision.verdict != serve_eligibility.DEFER_UNTIL:
        return None
    return decision.until or COLD_CHECK_HOLD_UNKNOWN_RELEASE


def _predecessor_cold_check_hold_until(
    vault: LoadedVault,
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> str | None:
    """mvp-0.26's serve-time hold, kept exactly for the predecessor and the kill
    switch: when a cold check's routine-display hold lifts (ledger format), or
    None when it is not held (UX Phase 4, rounds 5 to 7).

    Only a hold that time alone clears is made here (round-6 ruling 2): a
    routine display covers the item or its learning object now, and an open,
    unexpired cold task on the item falls due no later than that coverage
    releases it (due now, or deferred by it): every such task is judged, so a
    task for later never masks one due now (round 6, E). Those tasks are
    deferred, persisted when ``persist``, to the first second no covering row
    covers the item (``routine_released_at``), which is returned: the hold
    ends by itself within the coverage (D + G). Every other reveal kind keeps
    main's serving behaviour exactly (the scheduler's own deferral and the
    submit guard, unchanged): no hold. An unreadable stamp holds, with
    :data:`COLD_CHECK_HOLD_UNKNOWN_RELEASE` and nothing persisted.
    """

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
    from learnloop.reveal_coverage import routine_displays_covering, routine_released_at

    now_iso = utc_now_iso(clock)
    tasks = [
        task
        for kind in sorted(COLD_FOLLOWUP_TASK_KINDS)
        for task in repository.open_followup_tasks_of_kind(kind)
        if str(task.get("selected_item_id") or "") == practice_item_id
        and (not task.get("expires_at") or str(task.get("expires_at")) >= now_iso)
    ]
    if not tasks:
        return None
    item = vault.practice_items.get(practice_item_id)
    learning_object_id = str(getattr(item, "learning_object_id", "") or "") or None if item is not None else None
    covering = routine_displays_covering(
        repository, practice_item_id=practice_item_id, learning_object_id=learning_object_id, at=now_iso,
    )
    if not covering:
        return None
    releases = [routine_released_at(str(row.get("created_at") or "")) for row in covering]
    if any(value is None for value in releases):
        return COLD_CHECK_HOLD_UNKNOWN_RELEASE
    released = max(value for value in releases if value is not None)
    held = [task for task in tasks if str(task.get("not_before") or "") <= released]
    if not held:
        return None
    if persist:
        for task in held:
            repository.defer_followup_task(str(task["id"]), not_before=released, clock=clock)
    return released


def cold_check_serve_hold(
    vault: LoadedVault,
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> str | None:
    """Revalidate a cold check at the moment it would be served (UX Phase 4,
    rounds 5 to 7; one eligibility decision): the reason it cannot be served
    AS the cold check now and must wait (the decision's reason code), or None
    when it is served, as the cold check or as practice with its check
    withdrawn (:func:`cold_check_serve_decision` says which). Every path that
    serves an item it chose earlier (a daily-plan block, a learner's pick, a
    session serve, the TUI's open) calls it. Below ``mvp-0.27``, or switched
    off, the hold is mvp-0.26's (routine displays only)."""

    from learnloop import serve_eligibility

    if not serve_eligibility.decision_active(vault):
        held = _predecessor_cold_check_hold_until(vault, repository, practice_item_id, clock=clock, persist=persist)
        return COLD_CHECK_ROUTINE_DISPLAY if held is not None else None
    decision = cold_check_serve_decision(vault, repository, practice_item_id, clock=clock, persist=persist)
    return decision.reason if decision.verdict == serve_eligibility.DEFER_UNTIL else None


def cold_check_serve_decision(
    vault: LoadedVault,
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
    persist: bool = True,
):
    """:func:`cold_check_decision` at a serve, with its writes applied
    (persisted when ``persist``: :func:`apply_eligibility_writes`) and its
    record logged. Below ``mvp-0.27``, or with ``eligibility.enabled`` off,
    the decision is mvp-0.26's serve-time hold put in the record's terms
    (``defer_until`` while a routine display covers the item, else ``serve``),
    with that hold's own persistence, so callers stay one path."""

    from learnloop import serve_eligibility

    if not serve_eligibility.decision_active(vault):
        now_iso = utc_now_iso(clock)
        held = _predecessor_cold_check_hold_until(vault, repository, practice_item_id, clock=clock, persist=persist)
        return serve_eligibility.EligibilityDecision(
            request=serve_eligibility.COLD_CHECK,
            verdict=serve_eligibility.DEFER_UNTIL if held is not None else serve_eligibility.SERVE,
            reason=COLD_CHECK_ROUTINE_DISPLAY if held is not None else serve_eligibility.ELIGIBLE,
            practice_item_id=practice_item_id, at=now_iso, until=held,
        )
    decision = cold_check_decision(vault, repository, practice_item_id, clock=clock)
    if persist and decision.writes:
        apply_eligibility_writes(vault, repository, decision, clock=clock)
    if persist and (decision.verdict != serve_eligibility.SERVE or decision.writes):
        # Logged where it acts; a read (the plan's pool, ``persist=False``) is silent.
        serve_eligibility.log_decision(decision, path="cold_check_serve")
    return decision


def deferred_cold_followups(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Live cold tasks currently held back because their answer was shown.

    Purely a READ. ``_defer_revealed_cold_followups`` decides and persists the
    push, but it only ever sees a task on the build that defers it: afterwards
    ``not_before`` sits in the future, ``due_followup_tasks`` filters the row
    out, and the deferral becomes invisible to every surface. That silence is
    the problem this exists to fix — a queue that quietly withholds a scheduled
    measurement and says nothing is indistinguishable from one that lost it.

    A future ``not_before`` alone is not evidence of a deferral (every cold task
    spends its first day that way), so the reveal ledger is re-consulted for the
    same window the deferral used. Nothing is written and nothing is decided
    here; a task whose push has elapsed simply does not appear.
    """

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

    now_iso = utc_now_iso(clock)
    deferred: list[dict[str, Any]] = []
    for kind in sorted(COLD_FOLLOWUP_TASK_KINDS):
        try:
            tasks = repository.open_followup_tasks_of_kind(kind)
        except Exception:  # pragma: no cover - a queue read must not break here
            continue
        for task in tasks:
            not_before = str(task.get("not_before") or "")
            if not not_before or not_before <= now_iso:
                continue
            item_id = str(task.get("selected_item_id") or "")
            selected_item = vault.practice_items.get(item_id) if item_id else None
            learning_object_id = (
                str(getattr(selected_item, "learning_object_id", "") or "") or None
                if selected_item is not None
                else (str(task.get("learning_object_id") or "") or None)
            )
            try:
                reveals = [
                    row
                    for row, _until in _cold_task_reveals(
                        repository,
                        item_id=item_id,
                        learning_object_id=learning_object_id,
                        since=str(task.get("created_at") or ""),
                        now_iso=now_iso,
                    )
                ]
            except Exception:  # pragma: no cover - ledger read is advisory here
                continue
            if not reveals:
                # Ordinary cold-retrieval wait, not a deferral. Saying "held
                # back" about it would invent a reason that never happened.
                continue
            deferred.append(
                {
                    "followup_task_id": str(task.get("id") or ""),
                    "kind": kind,
                    "practice_item_id": item_id or None,
                    "learning_object_id": learning_object_id,
                    "deferred_to": not_before,
                    "last_reveal_at": max(
                        str(row.get("created_at") or "") for row in reveals
                    ),
                }
            )
    deferred.sort(key=lambda row: (row["deferred_to"], row["followup_task_id"]))
    return deferred


#: Plain-English reason on the annotation row a deferred cold task leaves in the
#: slate. Same "no silent caps" contract as the reserved-probe exclusions: an
#: item withheld from the queue says why, in the log the queue already writes.
_COLD_DEFERRAL_REASON = "cold check held back: its answer was shown since it was scheduled"
#: The same, when the item is served as practice instead and its check
#: withdrawn (one eligibility decision: the item can no longer be taken cold).
_COLD_PRACTICE_REASON = "practice, not a check: this question can no longer be a fresh check"


def _merge_cold_deferral_explanations(
    vault: LoadedVault,
    explanations: list[dict[str, Any]],
    deferrals: list[dict[str, Any]],
    readiness_factor: float | None,
) -> list[dict[str, Any]]:
    """Mark every deferred cold task in the slate, exactly once per item."""

    if not deferrals:
        return explanations
    by_item = {
        str(deferral.get("practice_item_id") or ""): deferral
        for deferral in deferrals
        if deferral.get("practice_item_id")
    }
    merged = list(explanations)
    for row in merged:
        deferral = by_item.pop(str(row.get("practice_item_id") or ""), None)
        if deferral is None:
            continue
        row["components"] = dict(row.get("components") or {}) | _deferral_components(
            deferral
        )
        reasons = list((row.get("plain_english") or {}).get("reasons") or [])
        row["plain_english"] = {
            "reasons": [*_deferral_reasons(deferral), *reasons]
        }
    for item_id, deferral in by_item.items():
        item = vault.practice_items.get(item_id)
        if item is None:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None:
            continue
        merged.append(
            _explanation_payload(
                ScheduledItem(
                    practice_item_id=item.id,
                    learning_object_id=learning_object.id,
                    priority=0.0,
                    components=_deferral_components(deferral),
                    readiness_factor=readiness_factor,
                    selected_mode=item.practice_mode,
                    plain_english=_deferral_reasons(deferral),
                    reward_debug=None,
                    followup_kind=str(deferral.get("kind") or "") or None,
                ),
                selected=False,
                selection_propensity=None,
            )
        )
    return merged


def _deferral_components(deferral: Mapping[str, Any]) -> dict[str, float]:
    return {
        "cold_followup_deferred_reveal": 1.0,
        "cold_followup_reveal_amount": float(deferral.get("reveal_amount") or 0.0),
    }


def _deferral_reasons(deferral: Mapping[str, Any]) -> list[str]:
    if deferral.get("withdrawn"):
        return [_COLD_PRACTICE_REASON, "its check no longer counts and was withdrawn"]
    return [_COLD_DEFERRAL_REASON, f"deferred until {deferral.get('deferred_to')}"]


def _bare_scheduled(vault: LoadedVault, practice_item: Any, readiness_factor: float | None) -> ScheduledItem | None:
    """A queue row for an item the ranked queue did not hold (a follow-up's item)."""

    learning_object = vault.learning_object_for_item(practice_item) if practice_item is not None else None
    if practice_item is None or learning_object is None:
        return None
    return ScheduledItem(
        practice_item_id=practice_item.id,
        learning_object_id=learning_object.id,
        priority=0.0,
        components={
            "forgetting_risk": 0.0,
            "goal_frontier": 0.0,
            "recent_error": 0.0,
            "probe_eig": 0.0,
        },
        readiness_factor=readiness_factor,
        selected_mode=practice_item.practice_mode,
        plain_english=[],
        reward_debug=None,
    )


def _insert_pending_followups(
    vault: LoadedVault,
    queue: list[ScheduledItem],
    pending_followups: list[dict[str, str]],
    readiness_factor: float | None,
    *,
    item_states: dict[str, PracticeItemState] | None = None,
) -> list[ScheduledItem]:
    if not pending_followups:
        return queue

    max_priority = max((item.priority for item in queue), default=0.0)
    by_id = {item.practice_item_id: item for item in queue}
    followups: list[ScheduledItem] = []
    inserted_ids: set[str] = set()
    for index, pending in enumerate(pending_followups):
        practice_item_id = pending["practice_item_id"]
        if practice_item_id in inserted_ids:
            continue
        # Meas §3.A2/§3.A3, second door. `build_due_queue`'s loop refuses an item
        # whose stimulus the practice surface cannot render, and this function
        # then RESURRECTS it: a follow-up task naming that id rebuilds a
        # `ScheduledItem` from the vault and pushes it above every ordinary pick.
        # So the cold retry of a repair, or the held-out check on a certified
        # skill, could serve the exact instrument the queue had just excluded --
        # and at maximum priority. Checked here rather than only in the
        # reconstruct branch below so a future refactor that widens `by_id`
        # cannot reopen it.
        candidate_item = vault.practice_items.get(practice_item_id)
        # The main queue loop rejects retired items, but this second door can
        # reconstruct one by id after that loop. Retirement is terminal even
        # when a stale delayed task still names the card.
        if candidate_item is None or candidate_item.status != "active":
            continue
        # Same lifecycle rule as the main loop: a stale task naming a card of a
        # dormant/resolved LO (or a switched-off adopted card) must not bring it
        # back at maximum priority.
        if not practice_item_servable(vault, candidate_item):
            continue
        if candidate_item is not None and unservable_reason(candidate_item) is not None:
            continue
        action_type = pending.get("action_type") or "negative_surprise_followup"
        if action_type == ANSWER_SHOWN_PRACTICE:
            # One eligibility decision: the item's cold check cannot be taken
            # now (submit would prime it), so the item is ordinary practice,
            # labelled; the cold task was re-timed. Same doors as above.
            practice = by_id.get(practice_item_id) or _bare_scheduled(vault, candidate_item, readiness_factor)
            if practice is None:
                continue
            reason = pending.get("practice_reason") or "practice: its answer was shown, so its check comes later"
            followups.append(
                replace(
                    practice,
                    priority=max_priority + len(pending_followups) - index,
                    plain_english=[reason] + [existing for existing in practice.plain_english if existing != reason],
                    followup_kind=None,
                )
            )
            inserted_ids.add(practice_item_id)
            continue
        # Single-use diagnostic surfaces stay single-use through this door too:
        # a stale GENERIC delayed task naming an ALREADY-ADMINISTERED
        # diagnostic_probe item must not resurrect the burned surface. A fresh
        # (never-attempted) diagnostic surface remains injectable by id — that
        # is a legitimate diagnostic serving path — and an explicit
        # repair-journey kind (REPAIR_JOURNEY_TASK_KINDS) keeps its selection
        # even post-administration, consistent with the selection-time rule.
        if (
            candidate_item.practice_mode == "diagnostic_probe"
            and action_type not in REPAIR_JOURNEY_TASK_KINDS
            and item_states is not None
        ):
            candidate_state = item_states.get(practice_item_id)
            if candidate_state is not None and candidate_state.last_attempt_at is not None:
                continue
        scheduled = by_id.get(practice_item_id)
        if scheduled is None:
            practice_item = candidate_item
            learning_object = vault.learning_object_for_item(practice_item) if practice_item is not None else None
            if practice_item is None or learning_object is None:
                continue
            scheduled = ScheduledItem(
                practice_item_id=practice_item.id,
                learning_object_id=learning_object.id,
                priority=0.0,
                components={
                    "forgetting_risk": 0.0,
                    "goal_frontier": 0.0,
                    "recent_error": 0.0,
                    "probe_eig": 0.0,
                },
                readiness_factor=readiness_factor,
                selected_mode=practice_item.practice_mode,
                plain_english=[],
                reward_debug=None,
            )
        components = dict(scheduled.components)
        is_intervention = action_type in _INTERVENTION_FOLLOWUP_KINDS
        component = "intervention_followup" if is_intervention else "negative_surprise_followup"
        # The lane survives on the item itself, not only in the prose below.
        # An unrecognised action_type lands on the negative-surprise component,
        # so it reports that lane rather than inventing a kind no surface knows.
        followup_kind = action_type if is_intervention else "negative_surprise_followup"
        # Measurement §5.7's probe is a retention/validity check, not a repair
        # retry, and the learner-facing reason says so: it is the one item in the
        # queue whose purpose is to test something the system already claimed.
        reason = FOLLOWUP_REASONS.get(action_type, "intervention follow-up")
        components[component] = 1.0
        reasons = [reason] + [existing for existing in scheduled.plain_english if existing != reason]
        followups.append(
            replace(
                scheduled,
                priority=max_priority + len(pending_followups) - index,
                components=components,
                plain_english=reasons,
                followup_kind=followup_kind,
            )
        )
        inserted_ids.add(practice_item_id)

    if not followups:
        return queue
    return followups + [item for item in queue if item.practice_item_id not in inserted_ids]


# Floor keeping teach_back items schedulable at low priority (transfer
# escalation on solid items). A constant, not a config weight: the scheduler
# priority-weight sweep showed those knobs are decision-inert.
_TEACH_BACK_PRIORITY_FLOOR = 0.05
# Eligibility floor for learner-requested items (promotions, rung variants):
# just enough to survive the zero-priority filter; the requested reorder floor
# and the selection reward decide actual placement.
_REQUESTED_PRIORITY_FLOOR = 0.05


def _apply_contrast_pair_order(
    vault: LoadedVault,
    repository: Repository,
    queue: list[ScheduledItem],
    session: SchedulerSession,
    *,
    clock: Clock | None = None,
    record: bool = True,
) -> list[ScheduledItem]:
    """Meas §3.A4: randomize which member of a contrast pair is served first.

    "*Revert if:* within-pair outcome differences are dominated by order effects —
    check by randomizing which member is served first." The randomization has to
    happen HERE, because this is the only place the order exists: by the time the
    attempts are read back, the order they show is the order the learner chose to
    work in, which is a different quantity.

    Three properties, all of them load-bearing:

    * **Reorder only, and only within the pair.** The two members swap SLOTS, so
      every other item keeps its position and the selection reward's ordering
      survives. A control that reshuffled the queue would confound the nuisance
      parameter it exists to remove.
    * **Deterministic per session.** ``build_due_queue`` is called repeatedly for
      one session and must produce the same slate; the draw is seeded on
      ``(session_id, pair_key)``, so it varies across sessions — where the
      balance accumulates — and never within one. A staged plan's pool
      (``session.contrast_order_seed == "pair"``) seeds it on the pair alone:
      one order per pair in every session, the balance accumulating across
      pairs (plan-determinism Codex review F1).
    * **Recorded, including the adjacency basis.** §3.A4 also forbids serving the
      two adjacent "unless the surfaces differ enough that the manipulation is
      not salient". Whether that held is a property of the realized queue, so it
      is observed and stored rather than assumed.

    A build with no session id is never recorded: there is nothing to key an
    idempotent serving record on, and a serving record that duplicated on every
    call would poison the balance audit the metric depends on. Its order: a
    per-session draw has no seed without a session, so the queue is left
    untouched (an ad-hoc build); the pair's own draw (``"pair"``) needs none
    and is applied, so a staged plan built with no session (Start's build,
    ``get_daily_plan`` with no session) orders a pair as every named session
    does (plan-determinism Codex re-review F1).

    PLACEMENT. This runs before the ``limit`` truncation and before the probe
    presentation pin, both deliberately. Ahead of the pin, because a committed
    probe presentation is a durable assignment and must keep the front of the
    queue whatever this does. Ahead of truncation, because the draw has to be
    independent of how many slots the session happens to have — a pair whose
    second member falls outside the limit is simply never *completed*, and
    ``contrast_pair_order_effect`` requires attempts on both members before it
    counts a pair at all.
    """

    from learnloop.diagnosis.contrast_pairs import (
        SEED_PER_PAIR,
        apply_serving_decisions,
        plan_contrast_pair_serving,
        record_contrast_pair_servings,
    )

    if not queue:
        return queue
    if session.session_id is None and session.contrast_order_seed != SEED_PER_PAIR:
        return queue
    ordered_ids = [item.practice_item_id for item in queue]
    decisions = plan_contrast_pair_serving(
        vault, ordered_ids, session_id=session.session_id, seed_scope=session.contrast_order_seed
    )
    if not decisions:
        return queue
    reordered_ids = apply_serving_decisions(ordered_ids, decisions)
    by_id = {item.practice_item_id: item for item in queue}
    if not record or session.session_id is None:
        # A router R1 counterfactual composition, or a staged plan built with
        # no session: the same order, no audit row (the pair's draw depends
        # only on its seed, the session's and the pair's or the pair's alone,
        # never on the order it is applied to).
        return [by_id[item_id] for item_id in reordered_ids]
    try:
        record_contrast_pair_servings(
            repository, decisions, session_id=session.session_id, clock=clock
        )
    except Exception:  # pragma: no cover - defensive
        # The order still changes; only the audit is lost. Failing the whole queue
        # build over a measurement record would trade the learner's session for a
        # metric, which is the wrong direction on standing constraint 10.
        import logging

        logging.getLogger(__name__).warning(
            "failed to record contrast pair servings for session %s",
            session.session_id,
            exc_info=True,
        )
    return [by_id[item_id] for item_id in reordered_ids]


def _rotate_same_day_frontier_repeats(
    queue: list[ScheduledItem],
    item_states: dict[str, PracticeItemState],
    now: datetime,
) -> list[ScheduledItem]:
    """Within goal-frontier queue slots, serve items not yet attempted today first.

    The at-risk treadmill: with no exposure term a failed frontier item stays
    argmax, so "practice at-risk facets" re-serves the same problem all day.
    Frontier items keep their queue slots as a group (non-frontier positions
    are untouched); within those slots, items attempted on the current UTC day
    sort after fresh ones, preserving reward order inside each half. If every
    frontier item was already attempted today the order is unchanged — the
    pool is genuinely exhausted and generation, not rotation, is the fix.
    """

    slots = [
        index
        for index, scheduled in enumerate(queue)
        if scheduled.components.get("goal_frontier", 0.0) > 0
    ]
    if len(slots) < 2:
        return queue
    today = now.strftime("%Y-%m-%d")

    def attempted_today(scheduled: ScheduledItem) -> int:
        state = item_states.get(scheduled.practice_item_id)
        last = state.last_attempt_at if state is not None else None
        return 1 if last is not None and last[:10] == today else 0

    rotated = sorted((queue[index] for index in slots), key=attempted_today)
    reordered = list(queue)
    for index, scheduled in zip(slots, rotated):
        reordered[index] = scheduled
    return reordered


def _enforce_teach_back_session_cap(
    queue: list[ScheduledItem],
    cap: int,
    *,
    admitted: frozenset[str] | None = None,
    keep: frozenset[str] = frozenset(),
) -> list[ScheduledItem]:
    """Keep at most ``cap`` teach_back items per built queue (config
    ``teach_back.session_cap``), preserving order for everything else.

    ``keep`` (DL2 fix round 4, R2): a due "Check once"'s item, which always
    stays and counts toward neither the cap nor the value admission.

    ``admitted`` (mvp-0.21, ``voi_stopping``): the teach-backs whose value of
    information pays for their minutes, each valued conditionally on those
    admitted before it; exactly these stay, the first included (the count is
    neither a cap nor a floor). ``None`` is the count cap exactly.
    """

    capped: list[ScheduledItem] = []
    teach_back_count = 0
    for scheduled in queue:
        if scheduled.selected_mode == "teach_back" and scheduled.practice_item_id not in keep:
            if admitted is not None:
                if scheduled.practice_item_id not in admitted:
                    continue
            elif teach_back_count >= cap:
                continue
            teach_back_count += 1
        capped.append(scheduled)
    return capped


def _teach_back_value_admission(
    vault: LoadedVault,
    context: "voi.VoiContext",
    greedy_queue: list[ScheduledItem],
    config: LearnLoopConfig,
) -> tuple[frozenset[str] | None, list[dict[str, Any]]]:
    """mvp-0.21 (c): value every teach-back, greedily and conditionally.

    Returns ``(admitted, receipts)``: ``admitted`` is ``None`` (the count cap
    serves exactly) unless the teach-back site is on. A teach-back's
    information is its reward's ``probe_eig_total`` (the existing LO-mastery
    and facet-recall entropy reduction, familiarity-discounted), decomposed
    from the reward's own body so each next teach-back is valued given the
    belief the ones already admitted are expected to leave
    (``voi_stopping.greedy_information_admission``): two teach-backs that
    would tell LearnLoop the same thing are not both kept. No hypothesis set
    is locked for a teach-back, so no next-action decision is at stake and its
    robust EIG in minutes must exceed its minutes. One receipt per
    teach-back: the step that admitted it, or the stop that left it out.
    """

    if not voi.voi_stopping_active(config, voi.SITE_TEACH_BACK):
        return None, []
    teach_backs = [scheduled for scheduled in greedy_queue if scheduled.selected_mode == "teach_back"]
    if not teach_backs:
        return frozenset(), []
    entries = []
    for index, scheduled in enumerate(teach_backs):
        item = vault.practice_items.get(scheduled.practice_item_id)
        eig = float(scheduled.components.get("probe_eig_total", 0.0) or 0.0)
        entries.append(
            voi.InformationEntry(
                ref=scheduled.practice_item_id,
                learning_object_id=scheduled.learning_object_id,
                eig_nats=eig,
                minutes=context.item_minutes(item),
                predicted_correct=scheduled.components.get("predicted_correctness"),
                terms=voi.InformationTerms.from_reward_debug(
                    scheduled.learning_object_id,
                    scheduled.reward_debug,
                    total_nats=eig,
                    hypothesis_channel=scheduled.hypothesis_channel,
                ),
                detail={"greedy_rank": index},
            )
        )
    admission = voi.greedy_information_admission(
        context, voi.SITE_TEACH_BACK, entries, cap_value=int(config.teach_back.session_cap)
    )
    receipts = [
        receipt
        for receipt in (admission.receipt_for(scheduled.practice_item_id) for scheduled in teach_backs)
        if receipt is not None
    ]
    return frozenset(admission.admitted), receipts


def _load_episode_context(
    vault: LoadedVault,
    repository: Repository,
    episode,
    cache: dict[str, tuple[HypothesisSet, dict[str, float], float] | None],
) -> tuple[HypothesisSet, dict[str, float], float] | None:
    # The locked entry prior is conditioned on the episode's observed evidence
    # so probe-EIG is computed against the live posterior, not the entry prior.
    # One locked set per episode, so the episode id is a stable cache key.
    if episode.id not in cache:
        hypothesis_set = episode_hypothesis_set(repository, episode)
        posterior: EpisodePosterior | None = (
            episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
            if hypothesis_set is not None
            else None
        )
        if hypothesis_set is None or posterior is None:
            cache[episode.id] = None
        else:
            cache[episode.id] = (hypothesis_set, posterior.posterior, posterior.entropy)
    return cache[episode.id]


def _load_episode_eligible(
    vault: LoadedVault,
    repository: Repository,
    episode,
    context: tuple[HypothesisSet, dict[str, float], float],
    cache: dict[str, dict[str, EligibleInstrument]],
) -> dict[str, EligibleInstrument]:
    """The episode's eligible instruments (with §7.4 predictive components),
    computed once per episode per queue build and keyed by item id."""

    if episode.id not in cache:
        hypothesis_set, posterior, _entropy_before = context
        entries = eligible_instruments(
            vault, repository, episode, hypothesis_set=hypothesis_set, posterior=posterior
        )
        cache[episode.id] = {entry.item.id: entry for entry in entries}
    return cache[episode.id]


def _record_probe_elicitation(
    repository: Repository,
    queue: list[ScheduledItem],
    probe_item_ids: dict[str, str],
    session: SchedulerSession,
    *,
    entropy_before: dict[str, float] | None = None,
    clock: Clock | None,
) -> None:
    probe_items = [item for item in queue if item.practice_item_id in probe_item_ids]
    if not probe_items:
        return
    selected = probe_items[0]
    repository.insert_elicitation_event(
        {
            "session_id": session.session_id,
            "selected_practice_item_id": selected.practice_item_id,
            "target_scope": {"learning_object_id": selected.learning_object_id},
            "policy": "probe_eig",
            "candidate_scores": {
                item.practice_item_id: item.components.get("probe_eig", 0.0) for item in probe_items
            },
            # §13.1: routine probe selections never log null entropy.
            "entropy_before": (entropy_before or {}).get(selected.practice_item_id),
            "expected_information_gain": selected.components.get("probe_eig", 0.0),
            "selected_reason": "highest probe expected information gain",
            "hypothesis_set_id": probe_item_ids[selected.practice_item_id],
            "trigger": "probe_phase_routine",
            "fallback_outcome": "existing_pi",
        },
        clock=clock,
    )


def explain_practice_item(vault: LoadedVault, repository: Repository, practice_item_id: str) -> ScheduledItem | None:
    queue = build_due_queue(vault, repository, persist_explanations=False)
    for item in queue:
        if item.practice_item_id == practice_item_id:
            return item
    return None


def _practice_information(item, learning_object, mastery, config: LearnLoopConfig) -> float:
    """Display-only measurement value of one ordinary attempt (never selection).

    Fisher information of a Bernoulli observation under the mastery channel's
    2PL link — ``a²·p·(1−p)`` with ``p = sigmoid(a·(θ − b))`` at the learner's
    current mastery logit θ (claim-seeded states carry the claim; no state →
    θ=0) — scaled by the default attempt type's evidence mass so the number
    reflects what a normal independent attempt actually moves. Peaks when the
    item sits on the learner's boundary (p≈0.5); near-zero for items far above
    or below their level. Deliberately NOT a priority term: practice selection
    optimizes learning (desirable difficulty), probes optimize measurement.
    """

    from learnloop.attempt_types import DEFAULT_ATTEMPT_TYPE
    from learnloop.attempts.evidence import attempt_evidence_mass
    from learnloop.learner.mastery import resolve_item_irt_params

    a, b = resolve_item_irt_params(item, learning_object, config.mastery)
    theta = mastery.logit_mean if mastery is not None else 0.0
    p = 1.0 / (1.0 + exp(-a * (theta - b)))
    mass = attempt_evidence_mass(DEFAULT_ATTEMPT_TYPE, config.evidence)
    return round(a * a * p * (1.0 - p) * mass, 3)


def _priority(components: dict[str, float], config: LearnLoopConfig) -> float:
    return (
        config.scheduler.forgetting_risk_weight * components["forgetting_risk"]
        + config.scheduler.goal_frontier_weight * components.get("goal_frontier", 0.0)
        + config.scheduler.recent_error_weight * components["recent_error"]
        + config.scheduler.probe_eig_weight * components["probe_eig"]
    )


def dominant_scheduler_reason(components: dict[str, float], config: LearnLoopConfig) -> str:
    """Stable learner-facing reason from the same weighted ranking terms."""

    if components.get("intervention_followup", 0.0) > 0:
        return "unassisted follow-up"
    if components.get("negative_surprise_followup", 0.0) > 0:
        return "recent surprising result"
    candidates = {
        "memory is due": config.scheduler.forgetting_risk_weight * components.get("forgetting_risk", 0.0),
        "active goal frontier": config.scheduler.goal_frontier_weight * components.get("goal_frontier", 0.0),
        "recent error": config.scheduler.recent_error_weight * components.get("recent_error", 0.0),
        "diagnostic information": config.scheduler.probe_eig_weight * components.get("probe_eig", 0.0),
        "boundary fit": components.get("boundary_target", 0.0),
    }
    reason, value = max(candidates.items(), key=lambda pair: (pair[1], pair[0]))
    return reason if value > 0 else "best available practice"


def _selection_propensities(
    queue: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
) -> dict[str, float]:
    """``P(item is served as the top candidate | slate)`` under seeded exploration.

    Mirrors the gating of `_apply_seeded_exploration` exactly so the logged
    propensity is the true probability the (stochastic) selection policy serves each
    candidate. The seeded hash is the policy's *randomization source*, so the
    propensity is the design probability — ``1 - rate`` on the greedy best and
    ``rate`` split uniformly over the eligible near-tie alternatives — not the
    realized deterministic outcome. Logging the design probability (rather than a
    degenerate 1.0/0.0) is what makes IPS / doubly-robust off-policy estimation
    identifiable across the logged dataset.

    Scope is the selection-reward policy over its candidates; force-inserted pending
    follow-ups (a separate, triggered decision) are not in this map and are logged
    with a NULL propensity by the caller.
    """

    if not queue:
        return {}
    propensity = {item.practice_item_id: 0.0 for item in queue}
    best = queue[0]
    # One support for both functions, so the logged design probability and the
    # draw can never disagree about the gating (including the probe-tie gate).
    support = _exploration_support(queue, session, config)
    if support is None:
        propensity[best.practice_item_id] = 1.0
        return propensity
    rate, alternatives = support
    propensity[best.practice_item_id] = 1.0 - rate
    share = rate / len(alternatives)
    for item in alternatives:
        propensity[item.practice_item_id] = share
    return propensity


def _apply_seeded_exploration(
    queue: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
    now: datetime,
) -> list[ScheduledItem]:
    support = _exploration_support(queue, session, config)
    if support is None:
        return queue
    rate, alternatives = support
    roll, choice = _exploration_draws(queue, session, now, alternatives)
    if roll >= rate:
        return queue
    index = int(choice * len(alternatives))
    selected = alternatives[min(index, len(alternatives) - 1)]
    return _explore_to_front(queue, selected, rate)


def _stable_fraction(label: str, session_id: str, now: datetime, candidate_ids: list[str]) -> float:
    seed = "|".join([label, session_id, now.date().isoformat(), *sorted(candidate_ids)])
    value = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")
    return value / float(2**64 - 1)


def _intent_for_item(item: PracticeItem, *, in_probe: bool, components: dict[str, float]) -> SchedulerIntent:
    if in_probe and components.get("probe_eig", 0.0) > 0:
        return SchedulerIntent.PROBE
    # Teach-back is elicitation, not retrieval practice: its reward is the
    # probe-EIG-style expected information gain over the item's facet pool
    # (existing PROBE machinery, no new priority weights).
    if item.practice_mode == "teach_back":
        return SchedulerIntent.PROBE
    if item.practice_mode == "diagnostic_probe":
        # Effectively dead in `build_due_queue` since the freshness reserve:
        # diagnostic surfaces only reach intent scoring with probe_eig > 0
        # (caught by the PROBE branch above). Kept for defense in depth — a
        # diagnostic surface must never be scored as ordinary practice/repair
        # supply by a future caller.
        if components.get("recent_error", 0.0) > 0 and item.repair_targets:
            return SchedulerIntent.REPAIR
        return SchedulerIntent.PRACTICE
    if components.get("recent_error", 0.0) > 0 and item.repair_targets:
        return SchedulerIntent.REPAIR
    if (item.transfer_distance or 0.0) > 0.0:
        return SchedulerIntent.TRANSFER
    return SchedulerIntent.PRACTICE


def _readiness_factor(session: SchedulerSession, config: LearnLoopConfig) -> float | None:
    factors: list[float] = []
    if session.energy is not None:
        energy = session.energy.strip().lower()
        factors.append(
            {
                "low": 0.5,
                "medium": 0.75,
                "normal": 0.75,
                "high": 1.0,
            }.get(energy, 0.75)
        )
    if session.available_minutes is not None:
        short_minutes = max(1, config.scheduler.short_session_minutes)
        factors.append(max(0.0, min(1.0, session.available_minutes / short_minutes)))
    if not factors:
        return None
    return sum(factors) / len(factors)


def _session_context(
    session: SchedulerSession,
    *,
    short_session: bool,
    readiness_factor: float | None,
    shadow_intent: dict[str, object] | None = None,
) -> dict[str, object]:
    context: dict[str, object] = {
        "session_id": session.session_id,
        "available_minutes": session.available_minutes,
        "energy": session.energy,
        "short_session": short_session,
        "readiness_factor": readiness_factor,
    }
    if shadow_intent is not None:
        # §11.2 shadow log: intent + within-intent rankings, decision-inert.
        context["shadow_intent"] = shadow_intent
    return context


def _scheduler_config_snapshot(config: LearnLoopConfig) -> dict[str, object]:
    scheduler = config.scheduler
    return {
        "forgetting_risk_weight": scheduler.forgetting_risk_weight,
        "goal_frontier_weight": scheduler.goal_frontier_weight,
        "goal_quota_floor_min": scheduler.goal_quota_floor_min,
        "goal_quota_floor_max": scheduler.goal_quota_floor_max,
        "goal_quota_ramp_days": scheduler.goal_quota_ramp_days,
        "recent_error_weight": scheduler.recent_error_weight,
        "probe_eig_weight": scheduler.probe_eig_weight,
        "short_session_minutes": scheduler.short_session_minutes,
        "selection_exploration_rate": scheduler.selection_exploration_rate,
        "selection_exploration_reward_window": scheduler.selection_exploration_reward_window,
        "algorithm_version": config.algorithms.algorithm_version,
    }


def _forgetting_risk(
    state: PracticeItemState | None,
    now: datetime,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
    *,
    effective_due: datetime | None = None,
) -> float:
    """``effective_due`` (DL2, §5.3) replaces ``due_at`` as the due gate when
    given; the retrievability is the item's own, as before."""

    if state is None or state.due_at is None:
        return 0.0
    due_at = effective_due if effective_due is not None else parse_utc(state.due_at)
    if due_at is None or due_at > now:
        return 0.0
    if state.stability is None:
        return 1.0
    last_attempt_at = parse_utc(state.last_attempt_at) or due_at
    elapsed_days = max(0.0, (now - last_attempt_at).total_seconds() / 86400)
    return 1 - forgetting_curve(state.stability, elapsed_days, weights)


def _intent_serving(vault: LoadedVault, repository: Repository, now: datetime):
    """DL2's per-build intent view (``learnloop.scheduling.intent.serving``), or None."""

    from learnloop.scheduling.intent.serving import intent_serving

    return intent_serving(vault, repository, now=now)


class _Once:
    """A build read made at most once, on first use. The queue build passes
    the values it already read (:meth:`of`); :func:`check_admission` passes
    readers, so a view that never meets a gate never pays for its reads."""

    __slots__ = ("_read", "_value", "_done")

    def __init__(self, read: Any) -> None:
        self._read = read
        self._value: Any = None
        self._done = False

    @classmethod
    def of(cls, value: Any) -> "_Once":
        once = cls(None)
        once._value, once._done = value, True
        return once

    def __call__(self) -> Any:
        if not self._done:
            self._value, self._done = self._read(), True
        return self._value


@dataclass
class _ProbeScore:
    """An item's ranking components before its selection reward, with its
    probe's when it is a candidate of an in-progress probe episode."""

    components: dict[str, float]
    hypothesis_channel: dict[str, Any] | None = None
    probe_familiarity_discount: float = 1.0
    probe_surface_repeat: bool = False
    #: Set when the probe was valued (the build records it for presentation).
    hypothesis_set_id: str | None = None
    entropy_before: float | None = None

    def record(self, item_id: str, probe_item_ids: dict[str, str], entropy_before: dict[str, float]) -> None:
        if self.hypothesis_set_id is not None:
            probe_item_ids[item_id] = self.hypothesis_set_id
            entropy_before[item_id] = float(self.entropy_before or 0.0)


class _BuildAdmission:
    """One build's gates after the routine one (``serving_exclusions.BuildGates``)
    and the reads behind them, each item's read once per build.

    ``build_due_queue`` asks them through ``serving_exclusions.admission_reason``
    for every item, and binds :meth:`admits_check_candidate` (the same
    predicate, for a request) to its DL2 intent view, so a "Check once"
    prefers a cold candidate over practice only among candidates this build
    admits (orchestrator ruling R1). A view built outside the queue (the
    plan, the practice view, settling) gets one over its own reads with no
    session (:func:`check_admission`)."""

    def __init__(
        self,
        vault: LoadedVault,
        repository: Repository,
        *,
        now: datetime,
        session: SchedulerSession,
        intent_view: Any,
        exclusions: _Once,
        item_states: _Once,
        placement_serving: _Once,
        open_episodes: _Once,
        probe_block_reason: _Once,
        mastery_states: _Once,
        frontier: _Once,
        errors_by_lo: _Once,
        fsrs_weights: _Once,
        recent_attempts_by_lo: _Once,
        voi_context: _Once,
        voi_probe_active: bool,
        carry_hypothesis_channels: bool,
        short_session: bool,
        voi_probe_decisions: dict[str, Any],
        episode_posterior_cache: dict[str, Any],
        episode_eligible_cache: dict[str, Any],
    ) -> None:
        self.vault = vault
        self.repository = repository
        self.config = vault.config
        self.now = now
        self.session = session
        self.intent_view = intent_view
        self.exclusions = exclusions
        self.item_states = item_states
        self.placement_serving = placement_serving
        self.open_episodes = open_episodes
        self.probe_block_reason = probe_block_reason
        self.mastery_states = mastery_states
        self.frontier = frontier
        self.errors_by_lo = errors_by_lo
        self.fsrs_weights = fsrs_weights
        self.recent_attempts_by_lo = recent_attempts_by_lo
        self.voi_context = voi_context
        self.voi_probe_active = voi_probe_active
        self.carry_hypothesis_channels = carry_hypothesis_channels
        self.short_session = short_session
        self.voi_probe_decisions = voi_probe_decisions
        self.episode_posterior_cache = episode_posterior_cache
        self.episode_eligible_cache = episode_eligible_cache
        # Lazily built: (attempted item ids, attempted surface groups), the
        # never-before-seen probe gate's exclusion set. Only probe-eligible
        # builds pay for it.
        self._attempted_surfaces: tuple[set[str], set[str]] | None = None
        self._placement: dict[str, tuple[str | None, bool, bool]] = {}
        self._scores: dict[str, _ProbeScore] = {}

    # -- the check's question -------------------------------------------------

    def admits_check_candidate(self, item_id: str) -> bool:
        """Would this build serve ``item_id`` as a due check's candidate (a
        request, intent's own gate aside)? The one predicate the loop asks."""

        return self.check_candidate_refusal(item_id) is None

    def check_candidate_refusal(self, item_id: str) -> str | None:
        """Why this build would not serve ``item_id`` as a due check's
        candidate, or None: the reason the one check gate keeps (DL2 fix
        round 6, F20)."""

        item = self.vault.practice_items.get(item_id)
        if item is None:
            return "unknown_item"
        state = self.item_states().get(item_id)
        return admission_reason(self.vault, item, state, self.exclusions(), self, requested=True)

    # -- the gates (``serving_exclusions.BuildGates``) ---------------------------

    def in_probe(self, item: PracticeItem) -> bool:
        learning_object = self.vault.learning_object_for_item(item)
        episode = self.open_episodes().get(learning_object.id)
        return episode is not None and episode.status == "in_progress" and self.probe_block_reason() is None

    def freshness_gate(self, item: PracticeItem, state: Any) -> str | None:
        # Freshness reserve (owner design intent): a diagnostic_probe surface
        # exists to carry one *diagnostic* administration on a never-before-seen
        # problem. Serving it as ordinary practice would burn that freshness on
        # a non-diagnostic administration, so the mode is excluded from the
        # ordinary pool ENTIRELY — not merely after administration. Diagnostic
        # surfaces reach the learner only through explicit diagnostic flows:
        # the probe-episode branch, and the by-id injection doors that bypass
        # this candidate gate (delayed follow-up tasks, exam pools, and repair
        # paths that request a specific item).
        return None if self.in_probe(item) else "diagnostic_freshness_reserve"

    def placement(self, item: PracticeItem, state: Any) -> tuple[str | None, bool, bool]:
        """``(reason, new_material, assumed_check)`` for an unrequested item."""

        cached = self._placement.get(item.id)
        if cached is not None:
            return cached
        placement_serving = self.placement_serving()
        learning_object = self.vault.learning_object_for_item(item)
        result: tuple[str | None, bool, bool] = (None, False, False)
        # F2 placement (None when off). New material: a never-attempted item
        # on an LO with no direct evidence (or back to learning after a missed
        # check, a miss in maintenance or "I don't know this") enters as
        # learning, where the predecessor opened an initial diagnostic episode
        # for it. An assumed LO is on its long first interval: nothing of it is
        # served routinely until its first review falls due, and then only the
        # check. After a passed check the LO is in maintenance: its practised
        # items keep their normal reviews, its remaining learning items stay
        # withheld. Learner-requested cards are the explicit exception.
        if placement_serving is not None:
            never_attempted = state is None or state.last_attempt_at is None
            mastery = self.mastery_states().get(learning_object.id)
            episode = self.open_episodes().get(learning_object.id)
            frontier_entry = self.frontier().by_lo.get(learning_object.id)
            if learning_object.id in placement_serving.open_learning_object_ids:
                if placement_serving.check_items.get(learning_object.id) != item.id:
                    result = ("placement_assumed_withheld", False, False)
                else:
                    result = (None, False, True)
            elif (
                learning_object.id in placement_serving.gap_check_learning_object_ids
                and placement_serving.check_items.get(learning_object.id) == item.id
            ):
                # mvp-0.16: a learner-text gap brought this maintenance LO's
                # next check forward and it is due: serve its check item.
                result = (None, False, True)
            elif learning_object.id in placement_serving.maintained_learning_object_ids:
                if never_attempted:
                    result = ("placement_maintained_withheld", False, False)
            elif (
                never_attempted
                and episode is None
                and frontier_entry is None
                and (
                    mastery is None
                    or mastery.last_evidence_at is None
                    or learning_object.id in placement_serving.back_to_learning_learning_object_ids
                )
            ):
                result = (None, True, False)
        self._placement[item.id] = result
        return result

    def placement_gate(self, item: PracticeItem, state: Any) -> str | None:
        return self.placement(item, state)[0]

    def cold_start_gate(self, item: PracticeItem, state: Any) -> str | None:
        # Cold-start gate: never-attempted LOs stay out of the routine queue —
        # EXCEPT when the LO is on an active goal's at-risk frontier or has an
        # open diagnostic episode. A `pending_items` episode explicitly keeps
        # the LO schedulable for belief-only ordinary practice (§10). The
        # frontier's widened semantics put unexamined facets at risk precisely
        # so the goal's untouched material gets scheduled before the due date;
        # skipping those items here would leave "practice at-risk facets"
        # re-serving the goal's only attempted item. A learner-requested card
        # (promotion, rung variant, a question written while reading) is also
        # exempt (``admission_reason`` never asks this of a request): the
        # learner explicitly adopted it, so a never-practised LO must not
        # swallow it.
        learning_object = self.vault.learning_object_for_item(item)
        _reason, new_material, assumed_check = self.placement(item, state)
        mastery = self.mastery_states().get(learning_object.id)
        if (
            (mastery is None or mastery.last_evidence_at is None)
            and self.open_episodes().get(learning_object.id) is None
            and self.frontier().by_lo.get(learning_object.id) is None
            and not new_material
            and not assumed_check
        ):
            return "cold_start_unattempted"
        return None

    def probe_gate(self, item: PracticeItem, state: Any) -> str | None:
        score = self.probe_score(item, state)
        if score.components.get("probe_eig", 0.0) <= 0.0:
            # Already-seen surface group, no eligible instrument binding, a
            # value below its minutes, or a short session withholding probe EIG.
            return "voi_value_below_minutes_cost" if score.components.get("voi_stop", 0.0) > 0.0 else "diagnostic_reserved"
        return None

    # -- the reads behind them ---------------------------------------------------

    def probe_score(self, item: PracticeItem, state: Any) -> _ProbeScore:
        """The item's ranking components and, in an in-progress probe episode,
        its probe's value: computed once per build (the probe gate and the
        ranking read the same values)."""

        cached = self._scores.get(item.id)
        if cached is not None:
            return cached
        vault, repository, config = self.vault, self.repository, self.config
        learning_object = vault.learning_object_for_item(item)
        mastery = self.mastery_states().get(learning_object.id)
        episode = self.open_episodes().get(learning_object.id)
        in_probe = self.in_probe(item)
        frontier_entry = self.frontier().by_lo.get(learning_object.id)
        intent_view = self.intent_view
        goal_frontier_component = _goal_frontier(vault, item, frontier_entry)
        components: dict[str, float] = {
            "forgetting_risk": _forgetting_risk(
                state,
                self.now,
                self.fsrs_weights(),
                effective_due=intent_view.effective_due_or_none(item.id, state) if intent_view is not None else None,
            ),
            "recent_error": _recent_error(self.errors_by_lo().get(learning_object.id, []), self.now),
            "probe_eig": 0.0,
            # DISPLAY ONLY (never a priority input — _priority reads exactly its
            # four weighted keys): how much one ordinary graded attempt is
            # expected to inform the LO mastery latent.
            "practice_information": _practice_information(item, learning_object, mastery, config),
        }
        if goal_frontier_component > 0:
            # Exposure discount: evidence from re-serving a just-attempted item
            # (or its surface family) is dependent evidence, worth less toward
            # the goal — and without this the argmax re-serves the same frontier
            # item after every failure. Reuses the follow-up/probe familiarity
            # machinery; no new constants.
            recent = self.recent_attempts_by_lo().get(learning_object.id, [])
            exposure = familiarity_discount_from_attempts(
                recent,
                item,
                covered_facets={str(facet): 1.0 for facet in item.evidence_facets},
                config=config,
            ).independent_evidence_discount
            components["goal_frontier_exposure_discount"] = exposure
            goal_frontier_component *= exposure
        components["goal_frontier"] = goal_frontier_component
        score = _ProbeScore(components=components)

        if in_probe and episode.hypothesis_set_id is not None:
            # Never-before-seen probe gate: familiarity merely DISCOUNTS
            # ordinary priority, but a probe administered on an already-seen
            # surface (same item, or any item in an attempted item's surface
            # group) measures memorization of the question, not understanding.
            # `eligible_instruments` enforces the same exclusion; the check here
            # exists so the exclusion is annotated instead of silent.
            if self._attempted_surfaces is None:
                self._attempted_surfaces = administered_surface_exclusions(vault, repository)
            attempted_ids, attempted_surfaces = self._attempted_surfaces
            score.probe_surface_repeat = (
                item.id in attempted_ids or surface_group_id(item) in attempted_surfaces
            )
            if score.probe_surface_repeat:
                components["probe_surface_repeat_excluded"] = 1.0
        if in_probe and episode.hypothesis_set_id is not None and not score.probe_surface_repeat:
            context = _load_episode_context(vault, repository, episode, self.episode_posterior_cache)
            eligible_entry = (
                _load_episode_eligible(vault, repository, episode, context, self.episode_eligible_cache).get(item.id)
                if context is not None
                else None
            )
            # §4.2 fix: only items with an executable instrument binding for
            # this episode's locked set (admitted card, or the logged registry
            # fallback) are probe candidates. Everything else scores zero
            # hypothesis EIG and stays ordinary practice.
            voi_withheld = False
            if context is not None and eligible_entry is not None and self.voi_probe_active:
                voi_decision = self.voi_probe_decisions.get(episode.id)
                if voi_decision is None:
                    voi_decision = voi.probe_episode_decision(
                        self.voi_context(),
                        episode,
                        list(
                            _load_episode_eligible(
                                vault, repository, episode, context, self.episode_eligible_cache
                            ).values()
                        ),
                        context[1],
                        session_id=self.session.session_id,
                    )
                    self.voi_probe_decisions[episode.id] = voi_decision
                voi_value = voi_decision.value_for(item.id)
                if voi_value is not None:
                    components["voi_value_minutes"] = voi_value.value_robust_minutes
                    components["voi_cost_minutes"] = voi_value.cost_minutes
                if not voi_decision.admits(item.id):
                    # Not worth its minutes this refresh: the item is not a
                    # probe candidate (a diagnostic surface stays reserved).
                    components["voi_stop"] = 1.0
                    voi_withheld = True
            if context is not None and eligible_entry is not None and not voi_withheld:
                hypothesis_set, posterior, entropy_before = context
                rubric = vault.rubric_for_item(item)
                prospective_coverage = resolve_coverage(
                    item,
                    rubric,
                    attempt_type="diagnostic_probe",
                    hints_used=0,
                    learner_answer_md="prospective_probe",
                    evidence=vault.config.evidence,
                )
                prospective_familiarity = familiarity_discount(
                    repository,
                    item,
                    learning_object_id=learning_object.id,
                    covered_facets=prospective_coverage.covered_facets,
                    config=config,
                )
                # Card-compiled, grader-composed conditionals — the same ones
                # posterior replay uses (§7.2). The primary objective is §7.4
                # predictive EIG (fraction of held-out predictive uncertainty
                # removed, [0, 1]) when the episode's target set is adequate;
                # hypothesis EIG normalized by the locked set's maximum
                # entropy is the fallback. Both are logged; never added (§7.4).
                eig_nats = eligible_entry.expected_information_gain
                size = len(posterior)
                hypothesis_eig_normalized = eig_nats / log(size) if size > 1 else 0.0
                predictive_primary = eligible_entry.selection_objective == "predictive_eig"
                if predictive_primary and eligible_entry.predictive_prior_entropy > 0:
                    candidate_probe_eig_raw = (
                        eligible_entry.predictive_eig / eligible_entry.predictive_prior_entropy
                    )
                else:
                    candidate_probe_eig_raw = hypothesis_eig_normalized
                score.probe_familiarity_discount = prospective_familiarity.independent_evidence_discount
                candidate_probe_eig = candidate_probe_eig_raw * score.probe_familiarity_discount
                if not self.short_session or _priority(components, config) <= 0:
                    components["probe_eig"] = candidate_probe_eig
                    components["probe_eig_raw"] = candidate_probe_eig_raw
                    # §7.3 telemetry separation: only response-conditioned
                    # entropy reduction is labeled EIG; coverage value is
                    # logged separately by the selection reward.
                    components["actual_hypothesis_eig"] = eig_nats
                    components["predictive_eig"] = eligible_entry.predictive_eig
                    components["predictive_information_rate"] = eligible_entry.predictive_information_rate
                    components["probe_predictive_primary"] = 1.0 if predictive_primary else 0.0
                    components["probe_eig_familiarity_discount"] = score.probe_familiarity_discount
                    score.hypothesis_set_id = episode.hypothesis_set_id
                    score.entropy_before = entropy_before
                    if self.carry_hypothesis_channels:
                        score.hypothesis_channel = voi.hypothesis_channel_body(
                            str(episode.id),
                            eligible_entry,
                            posterior,
                            objective="predictive_eig" if predictive_primary else "hypothesis_eig",
                        )
        self._scores[item.id] = score
        return score

    def reserved_annotation(
        self, item: PracticeItem, score: _ProbeScore, readiness_factor: float | None
    ) -> ScheduledItem:
        """The slate's annotation for a reserved diagnostic surface ("no silent caps")."""

        components = score.components
        reason = (
            "diagnostic probe excluded: surface group already administered"
            if score.probe_surface_repeat
            else (
                "diagnostic probe withheld: its value does not pay for its minutes this refresh"
                if components.get("voi_stop", 0.0) > 0.0
                else "diagnostic probe reserved: no eligible probe binding this refresh"
            )
        )
        return ScheduledItem(
            practice_item_id=item.id,
            learning_object_id=self.vault.learning_object_for_item(item).id,
            priority=0.0,
            components={**components, "diagnostic_reserved_excluded": 1.0},
            readiness_factor=readiness_factor,
            selected_mode=item.practice_mode,
            plain_english=[reason],
            reward_debug=None,
        )


def check_admission(
    vault: LoadedVault, repository: Repository, *, now: datetime, intent_view: Any, reasons: bool = False
) -> Any:
    """The build's admission for a DL2 intent view built outside the queue
    (the plan's pool, the practice view, settling): the same predicate over
    the same reads, with no session and nothing written, each read on first
    use. Returns ``admits_check_candidate``."""

    from learnloop.clock import FrozenClock

    clock = FrozenClock(now)
    config = vault.config
    item_states = _Once(repository.practice_item_states)
    exclusions = _Once(lambda: routine_serving_exclusions(vault, repository))

    def placement() -> Any:
        excluded = exclusions()
        return _placement_serving(
            vault,
            repository,
            clock=clock,
            persist=False,
            item_states=item_states(),
            excluded_item_ids=set(
                excluded.reserved_exam_item_ids
                | excluded.rung_variant_hold_ids
                | excluded.staged_owned_item_ids
                | excluded.held_out_item_ids
            ),
        )

    placement_serving = _Once(placement)

    def episodes() -> Any:
        if placement_serving() is not None:
            from learnloop.placement.state import servable_open_episodes

            return servable_open_episodes(vault, repository)
        return repository.open_probe_episodes()

    def frontier() -> Any:
        return build_goal_frontier(
            vault,
            repository,
            clock=clock,
            item_states=item_states(),
            facet_states_by_lo=read_facet_states_by_lo(vault, repository),
        )

    frontier_once = _Once(frontier)

    def recent() -> Any:
        rows_by_lo = repository.list_recent_attempts_by_learning_objects(
            frontier_once().by_lo,
            limit=config.recall_coverage.familiarity_recent_attempt_window,
        )
        from learnloop.held_grades import held_attempt_ids
        from learnloop.outcome_contract import HELD_ROW_KEY

        held = held_attempt_ids(repository, (row.get("id") for rows in rows_by_lo.values() for row in rows))
        if not held:
            return rows_by_lo
        return {
            lo_id: [{**row, HELD_ROW_KEY: True} if row.get("id") in held else row for row in rows]
            for lo_id, rows in rows_by_lo.items()
        }

    admission = _BuildAdmission(
        vault,
        repository,
        now=now.astimezone(UTC),
        session=SchedulerSession(),
        intent_view=intent_view,
        exclusions=exclusions,
        item_states=item_states,
        placement_serving=placement_serving,
        open_episodes=_Once(episodes),
        probe_block_reason=_Once(
            lambda: probe_serving_block_reason(vault, repository, session_id=None, cap_lifted=False)
        ),
        mastery_states=_Once(repository.mastery_states),
        frontier=frontier_once,
        errors_by_lo=_Once(lambda: _errors_by_learning_object(repository.active_error_events())),
        fsrs_weights=_Once(lambda: resolve_fsrs_weights(repository)),
        recent_attempts_by_lo=_Once(recent),
        voi_context=_Once(lambda: voi.VoiContext(vault, repository)),
        voi_probe_active=voi.voi_stopping_active(config, voi.SITE_PROBE_EPISODE),
        carry_hypothesis_channels=False,
        short_session=False,
        voi_probe_decisions={},
        episode_posterior_cache={},
        episode_eligible_cache={},
    )
    # ``reasons``: the refusal reason (or None) the one check gate keeps.
    return admission.check_candidate_refusal if reasons else admission.admits_check_candidate


def _goal_frontier(vault: LoadedVault, item: PracticeItem, entry) -> float:
    """Fraction of the item's evidence facets on its LO's goal frontier, scaled by goal priority.

    ``entry`` is the ``FrontierEntry`` for the item's LO (or ``None``). The frontier
    now spans unexamined/known-gap facets AND solid facets projected to decay below
    the goal's target_recall by its due date. The frontier's facet ids are canonical,
    so item evidence facets are canonicalized before the overlap.
    """

    if entry is None or not entry.facets or entry.goal_priority <= 0:
        return 0.0
    facets = [vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets]
    if not facets:
        return 0.0
    overlap = sum(1 for facet in facets if facet in entry.facets) / len(facets)
    return entry.goal_priority * overlap


def _apply_goal_quota(queue: list[ScheduledItem], floor: float) -> list[ScheduledItem]:
    """Reorder-only greedy quota guaranteeing a floor share of goal-frontier items.

    Composition gating (not a score weight): walk output positions ``k = 1..n``
    maintaining the running goal share; whenever it would fall below ``floor`` and a
    goal item remains, pull the highest-ranked remaining goal item forward, else emit
    the highest-ranked remaining item. Relative order is otherwise preserved (stable).
    """

    if floor <= 0:
        return queue

    def is_goal(item: ScheduledItem) -> bool:
        return item.components.get("goal_frontier", 0.0) > 0

    if not any(is_goal(item) for item in queue):
        return queue

    remaining = list(queue)
    result: list[ScheduledItem] = []
    goal_count = 0
    reason = f"goal quota: pulled forward (floor {floor:.2f})"
    while remaining:
        k = len(result) + 1
        if goal_count < floor * k and any(is_goal(item) for item in remaining):
            index = next(i for i, item in enumerate(remaining) if is_goal(item))
        else:
            index = 0
        chosen = remaining.pop(index)
        if index > 0:
            # Pulled ahead of higher-ranked non-goal items it would otherwise trail.
            chosen = replace(
                chosen,
                plain_english=[reason] + [existing for existing in chosen.plain_english if existing != reason],
            )
        if is_goal(chosen):
            goal_count += 1
        result.append(chosen)
    return result


def _apply_requested_floor(
    queue: list[ScheduledItem],
    requested_item_ids: list[str],
    cap: int,
) -> list[ScheduledItem]:
    """Prefix-floor reorder guaranteeing requested items a front slot (spec §4a).

    ``requested_item_ids`` are the learner's promoted-but-unattempted items,
    oldest promotion first. Among those that are ALSO eligible candidates in the
    built queue, pull the first ``cap`` to the front in that oldest-first order.
    Reorder only (never adds ineligible items — an id not already in the queue is
    skipped), and stable for everything else. Composes after the goal quota.
    """

    if cap <= 0 or not requested_item_ids:
        return queue
    by_id = {item.practice_item_id: item for item in queue}
    eligible = [item_id for item_id in requested_item_ids if item_id in by_id]
    if not eligible:
        return queue
    pull_ids = eligible[:cap]
    pull_set = set(pull_ids)
    reason = "requested: you asked to chase this"
    pulled = [
        replace(
            by_id[item_id],
            plain_english=[reason] + [existing for existing in by_id[item_id].plain_english if existing != reason],
        )
        for item_id in pull_ids
    ]
    rest = [item for item in queue if item.practice_item_id not in pull_set]
    return pulled + rest


def _recent_error(errors: list[ActiveErrorEvent], now: datetime) -> float:
    score = 0.0
    for error in errors:
        created_at = parse_utc(error.created_at)
        if created_at is None:
            continue
        days_since = max(0.0, (now - created_at).total_seconds() / 86400)
        score = max(score, error.severity * exp(-days_since / 7))
    return score


def _errors_by_learning_object(errors: list[ActiveErrorEvent]) -> dict[str, list[ActiveErrorEvent]]:
    """Active LEARNER errors per LO. Assessment-side events (the item or the
    grading was at fault — e.g. assessment_ambiguity from regrading a
    rung-variant placeholder answer) are excluded: they must not boost repair
    practice on an LO the learner never got wrong. They still influence the
    item-quality path (bad_item_suspicion) independently."""

    from learnloop.diagnosis.error_taxonomy_map import (
        ASSESSMENT_SIDE_ERROR_TYPES,
        map_legacy_error_type,
    )

    grouped: dict[str, list[ActiveErrorEvent]] = {}
    for error in errors:
        canonical = map_legacy_error_type(error.error_type) or error.error_type
        if canonical in ASSESSMENT_SIDE_ERROR_TYPES:
            continue
        grouped.setdefault(error.learning_object_id, []).append(error)
    return grouped


def _plain_english(item: PracticeItem, components: dict[str, float]) -> list[str]:
    reasons: list[str] = []
    if components.get("gap_commitment_check", 0.0) > 0:
        reasons.append("the one check on a topic added from your question")
    elif components.get("gap_sooner_check", 0.0) > 0:
        reasons.append("a check brought forward: your question pointed at this topic")
    elif components.get("assumed_check", 0.0) > 0:
        reasons.append("first review of a topic assumed known (not tested): this is the check")
    if components.get("new_material", 0.0) > 0:
        reasons.append("new material: starts as learning, no opening probe")
    if components["forgetting_risk"] > 0:
        reasons.append(f"forgetting risk {components['forgetting_risk']:.2f}")
    if components.get("goal_frontier", 0.0) > 0:
        reasons.append(f"goal frontier weight {components['goal_frontier']:.2f}")
    if components["recent_error"] > 0:
        reasons.append(f"recent error boost {components['recent_error']:.2f}")
    if components["probe_eig"] > 0:
        reasons.append(f"probe information gain {components['probe_eig']:.2f}")
    if components.get("boundary_target", 0.0) > 0:
        reasons.append(f"facet boundary fit {components['boundary_target']:.2f}")
    if components.get("probe_surface_repeat_excluded", 0.0) > 0:
        # Never-before-seen probe gate: the surface stays ordinary practice.
        reasons.append("probe excluded: surface group already administered")
    if components.get("selection_reward", 0.0) > 0:
        reasons.append(f"selection reward {components['selection_reward']:.2f}")
    if not reasons:
        reasons.append(f"{item.practice_mode} item is available")
    return reasons


def _explanation_payload(
    item: ScheduledItem,
    *,
    selected: bool = True,
    selection_propensity: float | None = None,
) -> dict[str, object]:
    components = dict(item.components)
    components["selected"] = 1.0 if selected else 0.0
    return {
        "practice_item_id": item.practice_item_id,
        "selected_mode": item.selected_mode,
        "priority": item.priority,
        "components": components,
        "readiness_factor": item.readiness_factor,
        "plain_english": {"reasons": item.plain_english},
        "expected_information_gain": item.components.get("probe_eig", 0.0),
        "selection_propensity": selection_propensity,
        # Realized flag: set only on the candidate actually promoted by exploration
        # (`_apply_seeded_exploration` tags it `exploration_selected`).
        "exploration_flag": 1 if float(item.components.get("exploration_selected") or 0.0) > 0.0 else 0,
        "target_scope": {
            "learning_object_id": item.learning_object_id,
            "selection_reward": item.reward_debug,
        },
    }
