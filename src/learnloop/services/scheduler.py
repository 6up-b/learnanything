from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import exp, log
from typing import Any, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ActiveErrorEvent, PracticeItemState, Repository
from learnloop.services.fitted_params import resolve_fsrs_weights
from learnloop.services.instrument_serving import unservable_reason
from learnloop.services.fsrs import FSRS6_DEFAULT_WEIGHTS, forgetting_curve
from learnloop.services.canonical_projection import surface_group_id
from learnloop.services.probe_episodes import (
    EligibleInstrument,
    EpisodePosterior,
    administered_surface_exclusions,
    eligible_instruments,
    episode_hypothesis_set,
    episode_posterior,
    presentation_commit_payload,
    probe_serving_block_reason,
)
from learnloop.services.probes import HypothesisSet
from learnloop.numeric import clamp
from learnloop.services.goal_projection import build_goal_frontier
from learnloop.services.exam_pool import reserved_item_ids as reserved_exam_pool_item_ids
from learnloop.services.facet_state_reader import facet_states_by_lo as read_facet_states_by_lo
from learnloop.services.recall_coverage import (
    familiarity_discount,
    familiarity_discount_from_attempts,
    resolve_coverage,
)
from learnloop.services.selection_rewards import SchedulerIntent, score_selection_reward
from learnloop.vault.models import LoadedVault, PracticeItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchedulerSession:
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None


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


def build_due_queue(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
    session: SchedulerSession | None = None,
    limit: int | None = None,
    persist_explanations: bool = True,
) -> list[ScheduledItem]:
    now = (clock or SystemClock()).now().astimezone(UTC)
    session = session or SchedulerSession()
    config = vault.config
    if persist_explanations:
        # Freshness supply reconciliation: a consumed (administered) single-use
        # diagnostic_probe surface leaves a diagnostic-coverage hole; derive the
        # deduplicated replacement-generation need here, on the path that always
        # runs right after an attempt. Idempotent and replay-safe (needs are a
        # function of attempts + item state), and guarded by persist_explanations
        # so explicitly side-effect-free queue builds stay pure.
        from learnloop.services.diagnostic_surface_supply import (
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
        from learnloop.services.calibration_sessions import calibration_cap_lifted

        cap_lifted = calibration_cap_lifted(repository, session.session_id)
    probe_block_reason = probe_serving_block_reason(
        vault,
        repository,
        session_id=session.session_id,
        cap_lifted=cap_lifted,
    )
    item_states = repository.practice_item_states()
    # Items reserved for a goal's held-out exam are quarantined from practice so
    # the exam stays an honest, uncontaminated test (fetched once per build).
    reserved_item_ids = reserved_exam_pool_item_ids(repository)
    rung_variant_hold_ids = repository.rung_variant_pending_source_ids()
    # Learner-requested items (tutor promotions + applied rung variants, never
    # attempted). Fetched once: the in-loop eligibility floor and the §4a
    # requested-items reorder floor must see the same set — a fresh sibling has
    # no attempts, stability, or due_at, so without the eligibility floor it
    # zeroes out at the priority filter and the reorder floor never sees it.
    requested_item_ids = repository.requested_practice_item_ids()
    requested_id_set = set(requested_item_ids)
    # P4 §14.2 step 3 (design §A.2 rule 3): during the dual-controller cutover the
    # staged policy owns P2 golden-path commitments. Their practice items are EXCLUDED
    # from the legacy queue so no commitment is scheduled by both controllers. Empty
    # (a no-op, byte-identical legacy queue) when no commitment is staged-owned.
    from learnloop.services import controller_ownership as _ownership

    staged_owned_item_ids = _ownership.staged_owned_practice_item_ids(vault, repository)
    mastery_states = repository.mastery_states()
    # Probe redesign: open diagnostic episodes replace lo_probe_state (frozen
    # legacy). `pending_items` episodes keep their LO schedulable for ordinary
    # practice; only `in_progress` episodes score probe EIG.
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
    from learnloop.services.goal_contracts import resolve_head

    evaluated_head_ids: list[str] = []
    for goal_id in frontier.active_goal_ids:
        head = resolve_head(repository, goal_id)
        if head is not None:
            evaluated_head_ids.append(head.id)

    queue: list[ScheduledItem] = []
    # Annotation-only rows for diagnostic surfaces the freshness rules kept out
    # of the queue. Logged with the slate ("no silent caps"), never served.
    probe_reserved_exclusions: list[ScheduledItem] = []
    # Lazily built: (attempted item ids, attempted surface groups) — the
    # never-before-seen probe gate's exclusion set. Only probe-eligible builds
    # pay for it.
    attempted_surface_exclusions: tuple[set[str], set[str]] | None = None
    probe_item_ids: dict[str, str] = {}
    probe_entropy_before: dict[str, float] = {}
    recent_attempts_by_lo: dict[str, list[dict[str, Any]]] = {}
    for item in vault.practice_items.values():
        # Learner-retired items are never served, independent of sync ordering.
        if item.status != "active":
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        if item.id in reserved_item_ids:
            continue
        # Pending-variant hold: the learner asked for an easier/harder sibling
        # of this exact card and it is still being authored. The request's
        # self-report already re-dued the source (FSRS "again" on easier), but
        # re-serving the very card the learner stepped away from — before its
        # variant exists — inverts the intended variant-first ordering.
        if item.id in rung_variant_hold_ids:
            continue
        # P4 §14.2 step 3: a staged-owned commitment's items are the staged policy's to
        # schedule, never the legacy queue's (design §A.2 rule 3 -- the coexistence seam).
        if item.id in staged_owned_item_ids:
            continue
        # Ephemeral dialogue-turn instances (§8.1) exist only to carry their one
        # committed diagnostic attempt; they are never ordinary practice.
        if item.practice_mode == "diagnostic_microprobe":
            continue
        # Vault-authored diagnostic probes are single-use surfaces: once the
        # item has carried an attempt, re-serving it would conflate memorization
        # of the question with understanding. Attempt recording deactivates the
        # item; this gate also covers vaults whose administration predates that
        # deactivation (state.active is True but the attempt already happened).
        if (
            item.practice_mode == "diagnostic_probe"
            and state is not None
            and state.last_attempt_at is not None
        ):
            continue
        # Meas §3.A2/§3.A3: an item whose stimulus the practice surface cannot
        # render is not schedulable. Serving one produces a silent harmful write
        # rather than a visible failure -- see `services/instrument_serving`.
        if unservable_reason(item) is not None:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None:
            continue
        mastery = mastery_states.get(learning_object.id)
        episode = open_episodes.get(learning_object.id)
        in_probe = (
            episode is not None
            and episode.status == "in_progress"
            and probe_block_reason is None
        )
        # Freshness reserve (owner design intent): a diagnostic_probe surface
        # exists to carry one *diagnostic* administration on a never-before-seen
        # problem. Serving it as ordinary practice would burn that freshness on
        # a non-diagnostic administration, so the mode is excluded from the
        # ordinary pool ENTIRELY — not merely after administration. Diagnostic
        # surfaces reach the learner only through explicit diagnostic flows:
        # the probe-episode branch below, and the by-id injection doors that
        # bypass this candidate gate (delayed follow-up tasks, exam pools, and
        # repair paths that request a specific item).
        if item.practice_mode == "diagnostic_probe" and not in_probe:
            continue
        frontier_entry = frontier.by_lo.get(learning_object.id)
        # Cold-start gate: never-attempted LOs stay out of the routine queue —
        # EXCEPT when the LO is on an active goal's at-risk frontier or has an
        # open diagnostic episode. A `pending_items` episode explicitly keeps
        # the LO schedulable for belief-only ordinary practice (§10). The
        # frontier's widened semantics put unexamined facets at risk precisely
        # so the goal's untouched material gets scheduled before the due date;
        # skipping those items here would leave "practice at-risk facets"
        # re-serving the goal's only attempted item.
        if (mastery is None or mastery.last_evidence_at is None) and episode is None and frontier_entry is None:
            continue

        goal_frontier_component = _goal_frontier(vault, item, frontier_entry)
        components: dict[str, float] = {
            "forgetting_risk": _forgetting_risk(state, now, fsrs_weights),
            "recent_error": _recent_error(errors_by_lo.get(learning_object.id, []), now),
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
            recent = recent_attempts_by_lo.get(learning_object.id)
            if recent is None:
                recent = repository.list_recent_attempts_by_learning_object(
                    learning_object.id,
                    limit=config.recall_coverage.familiarity_recent_attempt_window,
                )
                recent_attempts_by_lo[learning_object.id] = recent
            exposure = familiarity_discount_from_attempts(
                recent,
                item,
                covered_facets={str(facet): 1.0 for facet in item.evidence_facets},
                config=config,
            ).independent_evidence_discount
            components["goal_frontier_exposure_discount"] = exposure
            goal_frontier_component *= exposure
        components["goal_frontier"] = goal_frontier_component
        probe_familiarity_discount = 1.0

        probe_surface_repeat = False
        if in_probe and episode.hypothesis_set_id is not None:
            # Never-before-seen probe gate: familiarity merely DISCOUNTS
            # ordinary priority, but a probe administered on an already-seen
            # surface (same item, or any item in an attempted item's surface
            # group) measures memorization of the question, not understanding.
            # `eligible_instruments` enforces the same exclusion; the check here
            # exists so the exclusion is annotated instead of silent.
            if attempted_surface_exclusions is None:
                attempted_surface_exclusions = administered_surface_exclusions(
                    vault, repository
                )
            attempted_ids, attempted_surfaces = attempted_surface_exclusions
            probe_surface_repeat = (
                item.id in attempted_ids or surface_group_id(item) in attempted_surfaces
            )
            if probe_surface_repeat:
                components["probe_surface_repeat_excluded"] = 1.0
        if in_probe and episode.hypothesis_set_id is not None and not probe_surface_repeat:
            context = _load_episode_context(vault, repository, episode, episode_posterior_cache)
            eligible_entry = (
                _load_episode_eligible(vault, repository, episode, context, episode_eligible_cache).get(item.id)
                if context is not None
                else None
            )
            # §4.2 fix: only items with an executable instrument binding for
            # this episode's locked set (admitted card, or the logged registry
            # fallback) are probe candidates. Everything else scores zero
            # hypothesis EIG and stays ordinary practice.
            if context is not None and eligible_entry is not None:
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
                probe_familiarity_discount = prospective_familiarity.independent_evidence_discount
                candidate_probe_eig = candidate_probe_eig_raw * probe_familiarity_discount
                if not short_session or _priority(components, config) <= 0:
                    components["probe_eig"] = candidate_probe_eig
                    components["probe_eig_raw"] = candidate_probe_eig_raw
                    # §7.3 telemetry separation: only response-conditioned
                    # entropy reduction is labeled EIG; coverage value is
                    # logged separately by the selection reward.
                    components["actual_hypothesis_eig"] = eig_nats
                    components["predictive_eig"] = eligible_entry.predictive_eig
                    components["predictive_information_rate"] = eligible_entry.predictive_information_rate
                    components["probe_predictive_primary"] = 1.0 if predictive_primary else 0.0
                    components["probe_eig_familiarity_discount"] = probe_familiarity_discount
                    probe_item_ids[item.id] = episode.hypothesis_set_id
                    probe_entropy_before[item.id] = entropy_before

        if item.practice_mode == "diagnostic_probe" and components.get("probe_eig", 0.0) <= 0.0:
            # In an open probe episode but not servable as a probe this refresh
            # (already-seen surface group, no eligible instrument binding, or a
            # short session withholding probe EIG). The surface stays reserved
            # rather than leaking into ordinary practice; the exclusion is
            # logged with the slate so it never fails silently.
            reason = (
                "diagnostic probe excluded: surface group already administered"
                if probe_surface_repeat
                else "diagnostic probe reserved: no eligible probe binding this refresh"
            )
            probe_reserved_exclusions.append(
                ScheduledItem(
                    practice_item_id=item.id,
                    learning_object_id=learning_object.id,
                    priority=0.0,
                    components={**components, "diagnostic_reserved_excluded": 1.0},
                    readiness_factor=readiness_factor,
                    selected_mode=item.practice_mode,
                    plain_english=[reason],
                    reward_debug=None,
                )
            )
            continue

        legacy_priority = _priority(components, config)
        intent = _intent_for_item(item, in_probe=in_probe, components=components)
        reward = score_selection_reward(
            vault,
            item,
            learning_object,
            mastery=mastery,
            facet_states=facet_states_by_lo.get(learning_object.id, []),
            quality_state=repository.practice_item_quality_state(item.id),
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
        if episode is not None and (mastery is None or mastery.last_evidence_at is None):
            # Cold-start floor (probe redesign §10): an open episode — including
            # a pending_items one — keeps its never-attempted LO practicable for
            # belief-only ordinary practice instead of blocking on instruments.
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
        if item.id in requested_id_set:
            # Requested-items eligibility floor: the learner explicitly asked
            # for this card (promotion or easier/harder variant) and it has no
            # attempt/state/due signal yet — zero scheduler priority by
            # construction. It must survive this filter for the §4a requested
            # reorder floor below to be able to pull it forward.
            priority = max(priority, _REQUESTED_PRIORITY_FLOOR)
        if priority <= 0:
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
            )
        )

    queue.sort(
        key=lambda scheduled: (
            -scheduled.components.get("selection_reward", 0.0),
            -scheduled.priority,
            scheduled.practice_item_id,
        )
    )
    # Propensity is computed on the greedy-sorted order, before exploration reorders
    # it: it is P(this candidate is served | slate) under the seeded exploration
    # policy, which is what off-policy estimation reweights by.
    propensity_by_id = _selection_propensities(queue, session, config)
    queue = _apply_seeded_exploration(queue, session, config, now)
    queue = _enforce_teach_back_session_cap(queue, config.teach_back.session_cap)
    # Goal-composition quota: guarantee a floor share of goal-frontier items in the
    # ordered queue while a goal has at-risk facets. Applied before the limit slice
    # so the floor holds even in short sessions, and before follow-up insertion
    # (force-inserted follow-ups are a separate triggered decision).
    queue = _apply_goal_quota(queue, frontier.quota_floor)
    # Requested-items floor (spec §4a): the learner explicitly asked to chase a
    # promoted item, so guarantee up to N of them a front slot. Applied AFTER the
    # goal quota — the goal quota establishes its floor first, then this pulls at
    # most `requested_items_per_session` items to the very front, displacing the
    # goal prefix by at most that many positions (a tiny cap, default 1). Reorder
    # only: it can never surface a requested item that failed eligibility/gates,
    # because it only touches items already in the built (eligible) queue.
    queue = _apply_requested_floor(
        queue,
        requested_item_ids,
        config.tutor_promotion.requested_items_per_session,
    )
    queue = _rotate_same_day_frontier_repeats(queue, item_states, now)
    queue = _insert_pending_followups(
        vault, queue, pending_followups, readiness_factor, item_states=item_states
    )
    queue = _apply_contrast_pair_order(vault, repository, queue, session, clock=clock)
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
        from learnloop.services.intent_planner import shadow_intent_plan

        shadow_intent = shadow_intent_plan(vault, considered_queue)
    if persist_explanations and session.session_id is not None:
        selected_ids = {item.practice_item_id for item in queue}
        explanations = [
            _explanation_payload(
                item,
                selected=item.practice_item_id in selected_ids,
                selection_propensity=propensity_by_id.get(item.practice_item_id),
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
                            from learnloop.services.calibration_sessions import (
                                routine_planner_shadow,
                            )

                            planner = routine_planner_shadow(vault, repository, episode.id)
                            if planner is not None:
                                extra_components = {"shadow_planner": planner}
                        probe_presentation = presentation_commit_payload(
                            vault,
                            repository,
                            episode,
                            eligible,
                            candidates=list(eligible_by_id.values()),
                            extra_selection_components=extra_components,
                            clock=clock,
                        )
        repository.record_scheduler_slate(
            explanations,
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            requested_limit=limit,
            session_context=_session_context(session, short_session=short_session, readiness_factor=readiness_factor, shadow_intent=shadow_intent),
            config_snapshot=_scheduler_config_snapshot(config),
            selection_policy="selection_reward_v1",
            probe_presentation=probe_presentation,
            clock=clock,
        )
        committed = repository.active_probe_presentation_for_session(session.session_id)
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
    return queue


#: Learner-facing reason per delayed follow-up lane. Keyed on the
#: ``followup_tasks.kind`` the repository now passes through as ``action_type``.
_FOLLOWUP_REASONS: dict[str, str] = {
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


def _defer_revealed_cold_followups(
    vault: LoadedVault,
    repository: Repository,
    pending_followups: list[dict[str, str]],
    *,
    clock: Clock | None = None,
    persist: bool = True,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Hold back due cold tasks whose answer has been revealed since creation.

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

    from learnloop.services.attempts import COLD_FOLLOWUP_TASK_KINDS
    from learnloop.services.remediation import COLD_RETRIEVAL_DELAY

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
            reveals = repository.reveal_events_for_target(
                practice_item_id=item_id or None,
                learning_object_id=learning_object_id,
                since=since or None,
                until=now_iso,
            )
        except Exception:  # pragma: no cover - a ledger read must not break the queue
            kept.append(pending)
            continue
        if not reveals:
            kept.append(pending)
            continue
        last_at = max(str(row.get("created_at") or "") for row in reveals)
        last_dt = parse_utc(last_at)
        if last_dt is None:
            kept.append(pending)
            continue
        deferred_to = (
            (last_dt.astimezone(UTC) + COLD_RETRIEVAL_DELAY)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
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

    from learnloop.services.attempts import COLD_FOLLOWUP_TASK_KINDS

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
                reveals = repository.reveal_events_for_target(
                    practice_item_id=item_id or None,
                    learning_object_id=learning_object_id,
                    since=str(task.get("created_at") or "") or None,
                    until=now_iso,
                )
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
    return [_COLD_DEFERRAL_REASON, f"deferred until {deferral.get('deferred_to')}"]


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
        if candidate_item is not None and unservable_reason(candidate_item) is not None:
            continue
        action_type = pending.get("action_type") or "negative_surprise_followup"
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
        reason = _FOLLOWUP_REASONS.get(action_type, "intervention follow-up")
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
      balance accumulates — and never within one.
    * **Recorded, including the adjacency basis.** §3.A4 also forbids serving the
      two adjacent "unless the surfaces differ enough that the manipulation is
      not salient". Whether that held is a property of the realized queue, so it
      is observed and stored rather than assumed.

    A session with no session id (an ad-hoc queue build) is left untouched and
    unrecorded: there is nothing to key an idempotent serving record on, and a
    serving record that duplicated on every call would poison the balance audit
    the metric depends on.

    PLACEMENT. This runs before the ``limit`` truncation and before the probe
    presentation pin, both deliberately. Ahead of the pin, because a committed
    probe presentation is a durable assignment and must keep the front of the
    queue whatever this does. Ahead of truncation, because the draw has to be
    independent of how many slots the session happens to have — a pair whose
    second member falls outside the limit is simply never *completed*, and
    ``contrast_pair_order_effect`` requires attempts on both members before it
    counts a pair at all.
    """

    from learnloop.services.contrast_pairs import (
        apply_serving_decisions,
        plan_contrast_pair_serving,
        record_contrast_pair_servings,
    )

    if session.session_id is None or not queue:
        return queue
    ordered_ids = [item.practice_item_id for item in queue]
    decisions = plan_contrast_pair_serving(
        vault, ordered_ids, session_id=session.session_id
    )
    if not decisions:
        return queue
    reordered_ids = apply_serving_decisions(ordered_ids, decisions)
    by_id = {item.practice_item_id: item for item in queue}
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


def _enforce_teach_back_session_cap(queue: list[ScheduledItem], cap: int) -> list[ScheduledItem]:
    """Keep at most ``cap`` teach_back items per built queue (config
    ``teach_back.session_cap``), preserving order for everything else."""

    capped: list[ScheduledItem] = []
    teach_back_count = 0
    for scheduled in queue:
        if scheduled.selected_mode == "teach_back":
            if teach_back_count >= cap:
                continue
            teach_back_count += 1
        capped.append(scheduled)
    return capped


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
    from learnloop.services.evidence import attempt_evidence_mass
    from learnloop.services.mastery import resolve_item_irt_params

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

    def greedy() -> dict[str, float]:
        propensity[best.practice_item_id] = 1.0
        return propensity

    rate = clamp(config.scheduler.selection_exploration_rate)
    if rate <= 0 or session.session_id is None or len(queue) < 2:
        return greedy()
    if (best.reward_debug or {}).get("intent") == SchedulerIntent.PROBE.value:
        return greedy()
    best_reward = best.components.get("selection_reward", 0.0)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    alternatives = [
        item
        for item in queue[1:]
        if (item.reward_debug or {}).get("intent") != SchedulerIntent.PROBE.value
        and best_reward - item.components.get("selection_reward", 0.0) <= window
    ]
    if not alternatives:
        return greedy()
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
    rate = clamp(config.scheduler.selection_exploration_rate)
    if rate <= 0 or session.session_id is None or len(queue) < 2:
        return queue
    if _stable_fraction("roll", session.session_id, now, [item.practice_item_id for item in queue]) >= rate:
        return queue
    best = queue[0]
    best_intent = (best.reward_debug or {}).get("intent")
    if best_intent == SchedulerIntent.PROBE.value:
        return queue
    best_reward = best.components.get("selection_reward", 0.0)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    alternatives = [
        item
        for item in queue[1:]
        if (item.reward_debug or {}).get("intent") != SchedulerIntent.PROBE.value
        and best_reward - item.components.get("selection_reward", 0.0) <= window
    ]
    if not alternatives:
        return queue
    index = int(
        _stable_fraction("choice", session.session_id, now, [item.practice_item_id for item in alternatives])
        * len(alternatives)
    )
    selected = alternatives[min(index, len(alternatives) - 1)]
    selected = replace(
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
    return [selected] + [
        item
        for item in queue
        if item.practice_item_id != selected.practice_item_id
    ]


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
) -> float:
    if state is None or state.due_at is None:
        return 0.0
    due_at = parse_utc(state.due_at)
    if due_at is None or due_at > now:
        return 0.0
    if state.stability is None:
        return 1.0
    last_attempt_at = parse_utc(state.last_attempt_at) or due_at
    elapsed_days = max(0.0, (now - last_attempt_at).total_seconds() / 86400)
    return 1 - forgetting_curve(state.stability, elapsed_days, weights)


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

    from learnloop.services.error_taxonomy_map import (
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
