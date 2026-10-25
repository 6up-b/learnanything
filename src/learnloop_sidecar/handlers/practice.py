from __future__ import annotations

from dataclasses import replace as _dataclass_replace
import sqlite3
from typing import Any, Literal

from pydantic import Field

from learnloop.clock import utc_now_iso
from learnloop.ai.errors import CodexUnavailable
from learnloop.config import CODEX_PROVIDER_NAMES
from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptResult,
    AttemptValidationError,
    SelfGradeErrorAttribution,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_ai_required,
    complete_attempt_with_codex_fallback,
    complete_attempt_with_codex_required,
    complete_empty_stuck_attempt,
    complete_self_graded_attempt,
)
from learnloop.attempts.hint_fold import ServerHintFold, read_fold
from learnloop.attempts.stuck import stuck_attempt_type, stuck_prompt_active
from learnloop.attempts.post_attempt import (
    CompletionRouteUnknown,
    probe_route,
    run_post_attempt_pipeline,
)
from learnloop.tutor.tutor_qa import hint_equivalents_for_submission
from learnloop.hints.map_builder import schedule_build_on_serve
from learnloop.hints.telemetry import (
    attach_reveals_to_attempt,
    record_authored_reveal,
    stamp_submission,
    stamp_window_submission,
    telemetry_enabled,
)
from learnloop.diagnosis.probe_episodes import (
    PROBE_ITEM_ANSWER_SHOWN,
    RoutineDisplayCovered,
    commit_item_presentation,
    enter_episode,
    episode_contract,
    episode_hypothesis_set,
    next_probe_item,
    probe_serving_block_reason,
    probe_value_block_reason,
    routine_display_covers_item,
    serve_presentation,
    stop_diagnosing_and_teach,
    validate_presentation_for_submission,
)
from learnloop.diagnosis.probes import probe_posterior
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.attempts.trace_evidence import (
    compose_learner_trace,
    decide_elicitation,
    elicited_explanations_in,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import ready_grading_provider
from learnloop_sidecar.handlers.queue import (
    PracticeItemInput,
    _sections,
    offer_trace_for,
    publish_offer,
)
from learnloop_sidecar.handlers.serializers import practice_item_detail
from learnloop_sidecar.handlers.sessions import (
    KEEP_HINT_SEEN,
    SessionCheckpointInput,
    clear_checkpoint,
    draft_plan_presentation,
    draft_self_grade_disclosure,
    patch_checkpoint,
    settle_self_grade_disclosure,
)
from learnloop_sidecar.logging import debug_enabled, log_event
from learnloop_sidecar.registry import method
from learnloop_sidecar.serving import (
    refuse_held_out_item,
    refuse_inactive_learning_object,
    refuse_unservable_item,
)


class PracticeDraftCheckpoint(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str
    hints_used: int = 0
    # Stable client retry key for the attempt being composed. Optional: a
    # client that does not persist one gets no recovery.
    submission_id: str | None = None
    scheduler_candidate_id: str | None = None
    #: Router R2a: the plan presentation the draft answers. Kept with the
    #: draft's retry key in the session checkpoint (review F5), so a draft
    #: resumed after a restart submits bound to it; binding happens at submit
    #: (the attempt row), never here.
    plan_presentation_id: str | None = None
    #: mvp-0.13 (review F2): the draft is being written after "I'm stuck".
    #: Kept with the draft so a navigation or restart before the grade
    #: commits restores the stuck answer it was, not an ordinary one.
    declared_stuck: bool = False
    #: Adaptive difficulty AD1 (§11.2): the first-hint progress marker, kept
    #: with the draft's retry key so a restored draft keeps it.
    first_hint_progress: Literal["no_draft", "draft_started"] | None = None
    #: AD1 fix round 5 (V4): a hint of any kind was seen on this draft (an
    #: authored reveal, a delivered hint, a carried hint or book), kept with
    #: the retry key, whatever the switches, so a draft restored without a
    #: marker knows its first hint's timing is unknown. Never read by
    #: grading, scheduling or the assistance count (``hints_used``).
    hint_seen: bool | None = None


class SelfGradeDisclosureInput(ParamsModel):
    """UX Phase 4 (Codex review F1): the whole trace a plain self-grade froze
    before it shows a full answer: the answer exactly as Submit sends it and
    the volunteered line apart, under the draft's retry key."""

    session_id: str
    practice_item_id: str
    submission_id: str
    answer_md: str
    explanation_md: str | None = None
    # Round 3 F1: with a display id this is not a freeze but one display of
    # the key for the draft frozen already (the screen writes one before the
    # key appears and at each renewal); a retry of that write reuses it.
    display_id: str | None = Field(default=None, min_length=1, max_length=128)


class PracticeSubmissionRecoveryInput(ParamsModel):
    session_id: str
    practice_item_id: str
    submission_id: str


class PracticeSubmissionAcknowledgementInput(ParamsModel):
    session_id: str
    practice_item_id: str
    submission_id: str


class SelfGradeErrorAttributionDto(ParamsModel):
    error_type: str
    criterion_id: str | None = None


class SelfGradeInputDto(ParamsModel):
    criterion_points: dict[str, float]
    confidence: int
    fatal_errors: list[str] | None = None
    error_type: str | None = None
    notes: str | None = None
    error_attributions: list[SelfGradeErrorAttributionDto] | None = None


class SubmitAttemptInput(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str
    attempt_type: str
    #: Meas §3.A6: the optional one-line justification, submitted as its own
    #: field. `answer_md` is the answer and nothing else — a client never
    #: appends the volunteered line to it, because that made a text delimiter a
    #: cross-language contract that only a comment held together.
    explanation_md: str | None = None
    hints_used: int = 0
    #: RW2b fix round 5 (items 4-5): the answer box's authored reveals on
    #: their own, apart from the book and the workbench's help the server
    #: counts itself (``combine_held``). Absent (an older client): round 4's rule.
    authored_hints: int | None = Field(default=None, ge=0)
    #: RW2b fix round 12 (item 2): the client counted a book in its count
    #: (``bookLeft``: a problem since abandoned), its own component, ORed into
    #: the book (``combine_held``). Absent: no client-held book is assumed.
    book_counted: bool | None = None
    latency_seconds: int | None = None
    self_grade: SelfGradeInputDto | None = None
    primed: bool = False
    # Probe redesign §5.1: the committed presentation this submission consumes.
    probe_presentation_id: str | None = None
    # Probe redesign §7.1: learner answer confidence (1-5), logged-only.
    answer_confidence: int | None = None
    assessment_contract_version_id: str | None = None
    submission_id: str | None = None
    scheduler_candidate_id: str | None = None
    #: Router R2a: the daily-plan presentation this answer is to (the plan
    #: step's ``presentationId``). A wrong or consumed id never fails the
    #: submit: the attempt records unbound.
    plan_presentation_id: str | None = None
    #: mvp-0.13: the answer was written after "I'm stuck" ("Write what you
    #: can, or what's confusing you"). It may be empty. Still an ordinary
    #: attempt of ``attempt_type``: graded when it has text, a deterministic
    #: zero when empty.
    declared_stuck: bool = False
    #: Adaptive difficulty AD1 (spec §12): the optional "Felt: easy / about
    #: right / hard" tap, sent only when tapped; stored only with
    #: ``adaptive_difficulty.rating_tap`` on. Logged only.
    difficulty_rating: Literal["easy", "about_right", "hard"] | None = None
    #: AD1 (§11.2): whether an answer had been started when the first hint of
    #: this attempt was revealed; stored only with ``forecast_receipts`` on.
    first_hint_progress: Literal["no_draft", "draft_started"] | None = None


class DontKnowInput(ParamsModel):
    session_id: str
    practice_item_id: str
    hints_used: int = 0
    #: RW2b fix round 5 (items 4-5): the answer box's authored reveals on
    #: their own, apart from the book and the workbench's help the server
    #: counts itself (``combine_held``). Absent (an older client): round 4's rule.
    authored_hints: int | None = Field(default=None, ge=0)
    #: RW2b fix round 12 (item 2): the client counted a book in its count
    #: (``bookLeft``: a problem since abandoned), its own component, ORed into
    #: the book (``combine_held``). Absent: no client-held book is assumed.
    book_counted: bool | None = None
    latency_seconds: int | None = None
    self_grade: SelfGradeInputDto | None = None
    probe_presentation_id: str | None = None
    answer_confidence: int | None = None
    assessment_contract_version_id: str | None = None
    submission_id: str | None = None
    scheduler_candidate_id: str | None = None
    #: Router R2a: the daily-plan presentation this answer is to.
    plan_presentation_id: str | None = None
    #: Adaptive difficulty AD1 (§12, §11.2), as on ``SubmitAttemptInput``.
    difficulty_rating: Literal["easy", "about_right", "hard"] | None = None
    first_hint_progress: Literal["no_draft", "draft_started"] | None = None


class SkipInput(ParamsModel):
    session_id: str
    practice_item_id: str


class HintRevealInput(ParamsModel):
    """Adaptive hints H0: one authored hint the practice screen revealed."""

    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    #: The screen's stable submission key for the attempt in progress (the
    #: one its submit will send): the row is attached to that submission's
    #: attempt and to no other (review F1).
    submission_id: str = Field(min_length=1)
    #: 0-based: the hint shown is ``item.hints[authored_index]``.
    authored_index: int = Field(ge=0)
    #: The draft the hint was revealed on; only its hash and length are kept.
    answer_md: str = ""
    #: The client's press time (ISO 8601); the sidecar's own when absent.
    revealed_at: str | None = None


#: Adaptive hints H0's RPCs (desktop only; pinned in tests/test_mobile_allowlist.py).
HINT_TELEMETRY_RPCS = ("practice.record_hint_reveal",)


class ServePracticeItemInput(ParamsModel):
    practice_item_id: str
    #: The open session this serve belongs to. Absent for read-only opens (the
    #: feedback screen re-reading the prompt, the inspector), which must not be
    #: offered an elicitation at all — see `get_practice_item`.
    session_id: str | None = None
    #: Canonical sources (Codex re-review F10): the ``find_practice`` proposal
    #: (and, for a textbook exercise, its import) the learner picked this item
    #: from with the daily plan off. This open-list serve records the pick's
    #: delivery, once.
    proposal_id: str | None = None
    source_exercise_import_id: str | None = None


def _require_active_item(vault, practice_item_id: str):
    """One terminal lifecycle gate for every practice write/serve."""

    item = vault.practice_items.get(practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice item {practice_item_id} not found.")
    if item.status != "active":
        raise SidecarError(
            "item_retired",
            f"Practice item {practice_item_id} has been retired and cannot be served.",
            details={"practice_item_id": practice_item_id},
        )
    return item


@method("get_practice_item", ServePracticeItemInput)
def get_practice_item(ctx: SidecarContext, params: ServePracticeItemInput) -> dict[str, Any]:
    """Serve one item, carrying A6's elicitation decision for this serve.

    Spec: ``spec_measurement_efficiency_v1.md`` §3.A6; plan item 6.2.

    The decision rides on the served DTO rather than on its own call because it
    is a property of *this* serve and not of the item: the same item opened
    later in the same session may be past the per-session budget, and a cached
    per-item answer would quietly defeat rule 4. All five arms travel, not just
    the boolean — "we did not ask" has four distinct meanings and A6's revert
    criterion has to tell them apart.

    Without a session there is no budget to spend against, so no decision is
    made at all (``None``, not a fabricated "no"): a read-only open is not a
    serve, and reporting it as a declined elicitation would put a learner-facing
    event in the record where nothing happened.
    """

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Practice item {params.practice_item_id} not found.")
    if params.session_id is not None:
        item = _require_active_item(vault, params.practice_item_id)
        # A session serve of a dormant/resolved LO's item, or of one made from
        # held-out material, is refused; read-only opens (feedback, inspector)
        # still render it.
        refuse_unservable_item(vault, item)
        refuse_held_out_item(vault, repository, item)
        # A session serve revalidates a cold check (a stale list, a restored
        # session, a deep link) against the one eligibility decision: deferred
        # while a time-bounded hold lasts, served as practice when submit
        # would prime it (rounds 5 and 6; the eligibility stage).
        from learnloop_sidecar.handlers.queue import revalidate_cold_check

        eligibility = revalidate_cold_check(vault, repository, item.id)
    else:
        eligibility = None
    pick = None
    if params.session_id is not None and params.proposal_id:
        # A picked proposal is re-checked BEFORE anything is served (an item
        # reserved for a held-out exam since it was proposed is refused);
        # its delivery is recorded after the serve (Codex re-review F10).
        from learnloop_sidecar.handlers.daily_plan import select_on_open

        pick = select_on_open(ctx, practice_item_id=params.practice_item_id, session_id=params.session_id,
                              proposal_id=params.proposal_id,
                              source_exercise_import_id=params.source_exercise_import_id)
    # Only a session serve opens a cold administration, behind the guard
    # above; a read without a session (feedback, the inspector) never does
    # (round 6).
    detail = practice_item_detail(
        vault, repository, params.practice_item_id, administer=params.session_id is not None
    )
    if params.session_id is not None:
        # Slice 1 E7: a session serve is the decision the lag rate counts.
        from learnloop_sidecar.handlers.queue import record_diagnosis_serve

        record_diagnosis_serve(ctx, repository, params.session_id)
        if pick is not None:
            from learnloop_sidecar.handlers.daily_plan import deliver_on_open

            detail["proposalDelivery"] = to_camel(deliver_on_open(ctx, *pick))
    if eligibility is not None:
        from learnloop_sidecar.handlers.queue import eligibility_dto

        detail["eligibility"] = eligibility_dto(eligibility)
    if params.session_id is not None:
        # Daily-loop DL2: a due "Check once" is served cold (Reader §9.3 item
        # 10): the banner, help never blocked with its consequence stated, and
        # a header that locates nothing until feedback. Absent otherwise.
        from learnloop.clock import SystemClock
        from learnloop.intent.checks import served_check

        check = served_check(vault, repository, item.id, now=SystemClock().now())
        if check is None:
            # Reader CA2 (mvp-0.34): a due cold follow-up with no "Check once"
            # is served the same way (the take step, never "no hints").
            from learnloop.intent.checks import cold_followup_view

            check = cold_followup_view(vault, repository, item.id, now=SystemClock().now())
        if check is not None:
            detail["intentCheck"] = to_camel(check)
    detail["elicitation"] = (
        None
        if params.session_id is None
        else to_camel(
            decide_elicitation(
                item,
                config=vault.config.trace_evidence,
                elicitations_this_session=elicited_explanations_in(
                    repository.session_learner_answers(params.session_id)
                ),
            ).as_dict()
        )
    )
    if params.session_id is not None:
        # Adaptive hints H1 (hints.maps.build_on_serve): a session serve starts
        # the item's approach-map build in the background when its revision
        # has none, after the response is built. The serve never waits on it,
        # fails because of it or changes because of it.
        _schedule_approach_map(ctx, vault, repository, item.id)
    return detail


def _schedule_approach_map(ctx: SidecarContext, vault, repository, practice_item_id: str) -> None:
    try:
        schedule_build_on_serve(vault, repository.sqlite_path, practice_item_id,
                                client=getattr(ctx, "approach_map_client", None),
                                builds=getattr(ctx, "map_builds", None))
    except Exception as exc:  # noqa: BLE001 -- never reaches the serve
        log_event("approach_map_schedule_failed", practice_item_id=practice_item_id, error=type(exc).__name__)


class ProbeContractInput(ParamsModel):
    practice_item_id: str
    session_id: str | None = None


#: Sentinel for a durable assignment that no session's slate owns.
_OTHER_SESSION = object()


def _committed_presentation(repository, episode, session_id: str | None):
    """The durable presentation this open of the item should consume.

    Routine probes are precommitted alongside a `scheduler_slate_candidates`
    row, so `active_probe_presentation_for_session` finds them by joining the
    session's slate. A CAUSAL probe (`causal_orchestrator.accept_probe_offer`)
    has no scheduler candidate at all — it is minted by a learner action, not
    by the planner — so that join misses it. Committing a SECOND presentation
    for the same item would drop the `causal_probe` selection component pinning
    the candidate and blind-bundle ids, which is exactly the replay pin §3.4
    exists to protect: classification would fall back to whatever bundles
    existed at answer time.

    A presentation with no `scheduler_candidate_id` is owned by no session's
    slate, so any session opening its item may consume it. One with a scheduler
    candidate that this session's slate does not contain still belongs to the
    other session (`_OTHER_SESSION`).
    """

    if session_id is not None:
        active = repository.active_probe_presentation_for_session(session_id)
        if active is not None:
            return active
        other = repository.active_probe_presentation(episode.id)
        if other is None:
            return None
        if other.scheduler_candidate_id is not None:
            return _OTHER_SESSION
        return other
    return repository.active_probe_presentation(episode.id)


@method("get_probe_contract", ProbeContractInput)
def get_probe_contract(ctx: SidecarContext, params: ProbeContractInput) -> dict[str, Any]:
    """The probe measurement contract for opening one item (§12).

    When the item's LO has an in-progress diagnostic episode and the item
    resolves an executable instrument, this durably commits and serves a
    presentation (§5.1) and returns the enforced interaction contract: forced
    `diagnostic_probe` attempt type, disabled assistance, delayed feedback,
    and the presentation id the submission must consume. Otherwise the item
    serves as ordinary practice (`active: false`).
    """

    vault, repository = ctx.require_vault()
    item = _require_active_item(vault, params.practice_item_id)
    episode = repository.open_probe_episode(item.learning_object_id)
    if episode is None or episode.status != "in_progress":
        return versioned({"active": False})
    from learnloop.placement.state import episode_ignored

    if episode_ignored(vault, repository, episode):
        # Under placement an unanswered opening episode is ignored for serving
        # (owner decision 2026-10-12): the item is ordinary new material.
        return versioned({"active": False})

    # §5.9 orchestration gate (shared with the Textual surface): the routine
    # per-session qualifying-observation cap and the fresh-vault onboarding
    # ceiling. An active, in-budget calibration session lifts both — it is an
    # explicit learner opt-in.
    from learnloop.diagnosis.calibration_sessions import calibration_cap_lifted

    cap_lifted = params.session_id is not None and calibration_cap_lifted(
        repository, params.session_id
    )
    block_reason = probe_serving_block_reason(
        vault, repository, session_id=params.session_id, cap_lifted=cap_lifted
    )
    if block_reason is not None:
        return versioned({"active": False, "reason": block_reason})

    # §5.8: measurement requires an approved diagnostic grading provider. Under
    # a manual/self-grading provider no qualifying observation may be served:
    # the episode parks and the LO degrades to belief-only ordinary practice.
    _provider, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    if not runtime.ready or client is None:
        active = _committed_presentation(repository, episode, params.session_id)
        if active is not None and active is not _OTHER_SESSION:
            repository.end_probe_presentation(active.id, end_reason="invalidated")
        repository.update_probe_episode_status(episode.id, status="pending_items")
        return versioned({"active": False, "reason": "grading_provider_unavailable"})

    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return versioned({"active": False, "reason": "no_instrument"})
    # Routine scheduling precommits the assignment in the same transaction as
    # its slate candidate. Opening the selected item merely marks that durable
    # presentation served; opening another returned item does not reinterpret
    # it as a probe.
    active = _committed_presentation(repository, episode, params.session_id)
    if active is _OTHER_SESSION:
        return versioned({"active": False, "reason": "probe_assigned_to_other_session"})
    if active is not None:
        validation = validate_presentation_for_submission(
            repository,
            active.id,
            practice_item_id=item.id,
        )
        if validation.valid:
            try:
                serve_presentation(repository, active.id, vault=vault)
            except RoutineDisplayCovered:
                # Committed before the item's answer was shown on a routine
                # display: ended, and the item is ordinary practice (round 7).
                return versioned({"active": False, "reason": PROBE_ITEM_ANSWER_SHOWN})
            contract = episode_contract(vault, repository, item.learning_object_id) or {}
            return versioned(_with_intent_check(vault, repository, item.id, {"active": True, "presentation_id": active.id, **contract}))
        if validation.reason == "item_mismatch":
            return versioned({"active": False, "reason": "different_probe_assignment"})
        return versioned({"active": False, "reason": validation.reason or "stale_presentation"})

    # §5.9 routine planner, shadow mode (§13.3): log where this episode ranks
    # among all open episodes under plain vs disagreement-boosted information
    # rate. Log-only until held-out predictive gains justify promotion.
    extra_components = None
    if vault.config.probe.shadow.enabled:
        from learnloop.diagnosis.calibration_sessions import routine_planner_shadow

        planner = routine_planner_shadow(vault, repository, episode.id)
        if planner is not None:
            extra_components = {"shadow_planner": planner}
    # mvp-0.21 (voi_stopping): a new observation is committed only while its
    # value of information pays for its minutes; the decision is logged on the
    # presentation it admits.
    value_reason, value_decision = probe_value_block_reason(
        vault, repository, episode, item.id, session_id=params.session_id, cap_lifted=cap_lifted
    )
    if value_reason is not None:
        return versioned({"active": False, "reason": value_reason})
    if value_decision is not None:
        extra_components = {**(extra_components or {}), "voi_stopping": value_decision}
    presentation = commit_item_presentation(
        vault, repository, episode, item, hypothesis_set,
        extra_selection_components=extra_components,
    )
    if presentation is None:
        # UX Phase 4 round 7: say why when it is the item's answer shown on a
        # routine display (the commit refused it), so the surface can too.
        if routine_display_covers_item(repository, item.id, vault=vault):
            return versioned({"active": False, "reason": PROBE_ITEM_ANSWER_SHOWN})
        return versioned({"active": False, "reason": "no_instrument"})
    contract = episode_contract(vault, repository, item.learning_object_id) or {}
    return versioned(_with_intent_check(vault, repository, item.id, {"active": True, "presentation_id": presentation.id, **contract}))


def _with_intent_check(vault: Any, repository: Any, practice_item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """DL2 verify F15 (fix round 4, R3): an active diagnostic presentation of a
    due "Check once" item is the check, served under the diagnostic's duty;
    the contract (the server's word that this is a probe) carries the check's
    measured view, which promises no help. Absent otherwise."""

    from learnloop.clock import SystemClock
    from learnloop.intent.checks import DUTY_DIAGNOSTIC, served_check

    check = served_check(vault, repository, practice_item_id, now=SystemClock().now(), duty=DUTY_DIAGNOSTIC)
    if check is not None:
        payload = {**payload, "intent_check": check}
    return payload


@method("stop_probe_diagnosing", PracticeItemInput)
def stop_probe_diagnosing(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    """`Stop diagnosing and teach me` (§3): end the measurement block, persist
    the typed transition decision, and open a post-intervention state segment."""

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
    decision = stop_diagnosing_and_teach(vault, repository, item.learning_object_id)
    return versioned({"stopped": decision is not None, "decision": decision})


class NextProbeItemInput(ParamsModel):
    learning_object_id: str


@method("get_next_probe_item", NextProbeItemInput)
def get_next_probe_item(ctx: SidecarContext, params: NextProbeItemInput) -> dict[str, Any]:
    """The item that would continue this LO's open diagnostic block, if any.

    Read-only peek (§5.7 continuity) — never commits a presentation. The Tauri
    UI uses this to jump straight to the next observation within an
    in-progress block instead of round-tripping through the general queue
    between every attempt.
    """

    vault, repository = ctx.require_vault()
    from learnloop.placement.state import servable_open_episode

    if servable_open_episode(vault, repository, params.learning_object_id) is None:
        # No open episode, or an unanswered opening episode placement ignores
        # (owner decision 2026-10-12): nothing continues a diagnostic block.
        return versioned({"active": False})
    candidate = next_probe_item(vault, repository, params.learning_object_id)
    if candidate is None:
        return versioned({"active": False})
    return versioned({"active": True, "practice_item_id": candidate.item.id})


class OverconfidenceProbeInput(ParamsModel):
    learning_object_id: str
    facet_id: str | None = None


@method("start_overconfidence_probe", OverconfidenceProbeInput)
def start_overconfidence_probe(ctx: SidecarContext, params: OverconfidenceProbeInput) -> dict[str, Any]:
    """Launch a diagnostic episode from the F5 overconfidence list (§4.3).

    Opens (or reuses) the LO's diagnostic episode tagged
    ``origin='overconfidence_list'`` so analytics can separate adversarial
    selection from drift. Idempotent per LO. The follow-up probe item surfaces
    in the ordinary Today queue, so the caller refreshes the queue afterward.
    """

    vault, repository = ctx.require_vault()
    if params.learning_object_id not in vault.learning_objects:
        raise SidecarError("not_found", f"Unknown Learning Object {params.learning_object_id}.")
    refuse_inactive_learning_object(vault, params.learning_object_id)
    episode = enter_episode(
        vault,
        repository,
        params.learning_object_id,
        trigger="goal_diagnostic",
        origin="overconfidence_list",
    )
    return versioned(
        {
            "episode_id": episode.id,
            "learning_object_id": params.learning_object_id,
            "status": episode.status,
        }
    )


@method("save_practice_draft", PracticeDraftCheckpoint)
def save_practice_draft(ctx: SidecarContext, params: PracticeDraftCheckpoint) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    _require_active_item(vault, params.practice_item_id)
    _bind_offer(repository, params, params.submission_id)
    patch_checkpoint(
        repository,
        SessionCheckpointInput(
            session_id=params.session_id,
            current_practice_item_id=params.practice_item_id,
            current_answer=params.answer_md,
            hints_used=params.hints_used,
            submission_id=params.submission_id,
            declared_stuck=params.declared_stuck,
        ),
        plan_presentation_id=params.plan_presentation_id,
        first_hint_progress=_draft_marker(vault, params),
        hint_seen=params.hint_seen if "hint_seen" in params.model_fields_set else KEEP_HINT_SEEN,
    )
    return {"ok": True}


def _draft_marker(vault, params: PracticeDraftCheckpoint) -> Any:
    """AD1 (§11.2): the draft's first-hint progress marker, kept with its retry
    key; untouched by a client that does not send it, and never kept with
    ``adaptive_difficulty.forecast_receipts`` off."""

    from learnloop.adaptive_difficulty.switches import receipts_enabled
    from learnloop_sidecar.handlers.sessions import KEEP_MARKER

    if not receipts_enabled(vault.config):
        return None
    if "first_hint_progress" not in params.model_fields_set:
        return KEEP_MARKER
    return params.first_hint_progress


@method("practice.record_hint_reveal", HintRevealInput)
def record_hint_reveal(ctx: SidecarContext, params: HintRevealInput) -> dict[str, Any]:
    """Adaptive hints H0 (spec_adaptive_hints_v1 §9, §10 H0): record one
    authored hint the practice screen revealed, as a ``help_assists`` row.

    Fire and forget: the screen has already shown the hint and never waits on
    this. Telemetry only: submit still takes ``hints_used`` from the client,
    and nothing that grades, schedules or projects reads the row. A no-op
    (``recorded: false``) with ``hints.telemetry_enabled`` off, and during a
    diagnostic block on the item, where the screen refuses the reveal itself.
    A failed write is logged and answered ``recorded: false``, never raised.
    """

    vault, repository = ctx.require_vault()
    if not telemetry_enabled(vault.config):
        return versioned({"recorded": False, "reason": "telemetry_disabled", "assist_id": None})
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
    if params.authored_index >= len(item.hints):
        raise SidecarError(
            "validation_error",
            f"Practice Item {item.id} has {len(item.hints)} authored hints; no hint {params.authored_index}.",
            details={"field": "authoredIndex"},
        )
    if _in_diagnostic_block(repository, item):
        return versioned({"recorded": False, "reason": "diagnostic_block", "assist_id": None})
    try:
        record = record_authored_reveal(
            repository,
            item=item,
            session_id=params.session_id,
            submission_id=params.submission_id.strip(),
            authored_index=params.authored_index,
            work_md=params.answer_md,
            revealed_at=params.revealed_at,
        )
    except Exception as exc:  # noqa: BLE001 -- telemetry never fails the reveal
        log_event("hint_reveal_telemetry_failed", practice_item_id=item.id, error=type(exc).__name__)
        return versioned({"recorded": False, "reason": "write_failed", "assist_id": None})
    return versioned(record.as_dict())


def _in_diagnostic_block(repository, item) -> bool:
    """The item is being served as a diagnostic probe (an in-progress episode
    with a served presentation of this item): the screen refuses hints then
    (probe redesign §5.5), so no reveal is recorded either."""

    episode = repository.open_probe_episode(item.learning_object_id)
    if episode is None or episode.status != "in_progress":
        return False
    presentation = repository.active_probe_presentation(episode.id, practice_item_id=item.id)
    return presentation is not None and presentation.status == "served"


def _server_hint_fold(
    repository, practice_item_id: str, session_id: str, submission_id: str | None, *,
    base_hints: int, base_primed: bool = False, max_useful_hints: int = 0, clamp_without_fold: bool = True,
    stuck_types: tuple[str, ...] | None = None, stuck_probe: bool = False, window_fold: bool = False,
    held: dict[str, Any] | None = None,
) -> ServerHintFold:
    """Adaptive hints H2a (spec §5, G-H2, G-H3): the hints the hint service
    showed in this submission (its ``help_assists`` rows, shown, counted by
    the server, still unattached): how many at levels 1-3, and whether any
    was worked help (levels 4-5, ``primed``), with the rule this submit adds
    them to its own counts by. A read; a vault without such rows folds
    nothing, so every submit is exactly as before H2a. The draft carries the
    fold, and the attempt's write transaction takes it again before the
    attempt commits (review round 2, V1: a second sidecar may deliver a hint
    of this submission in between). A workbench submit (``window_fold``)
    folds by the keyless window whatever its own key (H2b fix round 3,
    ruling R1): the answer box's shown hints of the item since its last
    attempt in this practice session, whatever their key."""

    from contextlib import closing

    from learnloop.db.connection import connect

    # Ruling R1: the workbench's fold has no key (its attempt keeps its own).
    fold_key = None if window_fold else submission_id
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        count, primed, since = read_fold(
            connection, practice_item_id=practice_item_id, session_id=session_id, submission_id=fold_key,
        )
    return ServerHintFold(
        practice_item_id=practice_item_id, session_id=session_id, submission_id=fold_key, since=since,
        folded_hints=count, folded_primed=primed, base_hints=int(base_hints), base_primed=bool(base_primed),
        max_useful_hints=int(max_useful_hints or 0), clamp_without_fold=clamp_without_fold,
        stuck_types=stuck_types, stuck_probe=stuck_probe, window_fold=window_fold, **(held or {}),
    )


def _stamp_hint_submission(
    vault, repository, submission_id: str | None, practice_item_id: str, latency_seconds: float | None = None
) -> str | None:
    """Adaptive hints H0 (review F2, round 2 V3): when this submission reached
    the sidecar, before any grading, and the latency it sent, on its revealed
    hints' rows. Telemetry only; a failure is logged, never raised."""

    if submission_id is None or not telemetry_enabled(vault.config):
        return None
    try:
        return stamp_submission(
            repository, submission_id=submission_id, practice_item_id=practice_item_id,
            latency_seconds=latency_seconds,
        )
    except Exception as exc:  # noqa: BLE001 -- telemetry never fails a submit
        log_event("hint_reveal_stamp_failed", practice_item_id=practice_item_id, error=type(exc).__name__)
        return None


def _stamp_window_hints(repository, fold: ServerHintFold, submitted_at: str | None) -> None:
    """H2b re-review F9 under fix round 3's ruling R1: a workbench
    submission's submit time on the window's rows it folds (requested under
    the answer box's key, so the keyed stamp above never reaches them). Only
    when that stamp was made (telemetry on, a key); the first stamp stays and
    no latency is written. Telemetry only: a failure is logged, never raised."""

    if submitted_at is None or not fold.window_fold:
        return
    try:
        stamp_window_submission(
            repository, practice_item_id=fold.practice_item_id, session_id=fold.session_id, since=fold.since,
            submitted_at=submitted_at,
        )
    except Exception as exc:  # noqa: BLE001 -- telemetry never fails a submit
        log_event("hint_window_stamp_failed", practice_item_id=fold.practice_item_id, error=type(exc).__name__)


def _attach_hint_reveals(
    vault, repository, submission_id: str | None, practice_item_id: str, attempt_id: str,
    *, submitted_at: str | None = None, latency_seconds: float | None = None,
) -> None:
    """Adaptive hints H0: the attempt the submission's revealed hints were
    part of, matched on the submission key alone (review F1), so it is
    idempotent and every path that answers for a committed submission (the
    submit, a retry from its receipt, a resumed completion, a recovery)
    repairs an attach that failed, and no later submission takes the rows.
    Telemetry only, after the attempt committed: never changes the attempt
    or the response, and a failure is logged, never raised."""

    if submission_id is None or not telemetry_enabled(vault.config):
        return
    try:
        attach_reveals_to_attempt(
            repository,
            submission_id=submission_id,
            practice_item_id=practice_item_id,
            attempt_id=attempt_id,
            submitted_at=submitted_at,
            latency_seconds=latency_seconds,
        )
    except Exception as exc:  # noqa: BLE001 -- telemetry never fails a submit
        log_event("hint_reveal_attach_failed", practice_item_id=practice_item_id, error=type(exc).__name__)


@method("record_self_grade_disclosure", SelfGradeDisclosureInput)
def record_self_grade_disclosure(ctx: SidecarContext, params: SelfGradeDisclosureInput) -> dict[str, Any]:
    """Freeze the learner's whole trace before the plain self-grade shows a
    full answer (UX Phase 4, Codex review F1).

    The desktop shows the expected answer beside the learner's only after
    this returns. The frozen trace is kept with the draft in the session
    checkpoint, so a resume (another screen, a restart) reopens it locked, and
    the submit compares against it: a trace changed after the answer was shown
    is recorded as primed. When the draft is done with, its exposure is
    settled in the reveal ledger (``sessions.settle_self_grade_disclosure``).
    """

    vault, repository = ctx.require_vault()
    item = _require_active_item(vault, params.practice_item_id)
    submission_id = _submission_id(params.submission_id, None)
    if submission_id is None:
        raise SidecarError("validation_error", "submissionId must not be blank.", details={"field": "submissionId"})
    if params.display_id is not None:
        return _record_disclosure_display(repository, item, params, submission_id)
    explanation_md = (params.explanation_md or "").strip() or None
    patch_checkpoint(
        repository,
        SessionCheckpointInput(
            session_id=params.session_id,
            current_practice_item_id=params.practice_item_id,
            current_answer=params.answer_md,
            submission_id=submission_id,
        ),
        self_grade_disclosure={
            "practiceItemId": params.practice_item_id,
            "learningObjectId": item.learning_object_id,
            "submissionId": submission_id,
            "answerMd": params.answer_md,
            "explanationMd": explanation_md,
        },
    )
    log_event(
        "self_grade_disclosure_frozen",
        session_id=params.session_id,
        practice_item_id=params.practice_item_id,
        has_explanation=explanation_md is not None,
    )
    return versioned({"frozen": True})


def _record_disclosure_display(repository, item, params: SelfGradeDisclosureInput, submission_id: str) -> dict[str, Any]:
    """One display of the key on a pending plain self-grade (UX Phase 4,
    round 3 F1): a routine display row written while the draft is pending, so
    every other production is judged against it at once; the frozen trace's
    own commit is exempt (``reveal_ledger.own_disclosure_bases``).

    Only for the draft frozen in the checkpoint now (same item, same retry
    key): a display for a draft already committed or abandoned is refused
    (``disclosure_not_pending``) and the screen keeps the key hidden. Nothing
    written is ``display_not_recorded`` (retryable)."""

    from learnloop.attempts.reveal_ledger import (
        DisplayNotRecorded,
        frozen_trace_hash,
        record_self_grade_disclosure_display,
    )

    disclosure = draft_self_grade_disclosure(repository.fetch_session_checkpoint(params.session_id))
    if (
        disclosure is None
        or disclosure["practice_item_id"] != params.practice_item_id
        or disclosure["submission_id"] != submission_id
    ):
        raise SidecarError("disclosure_not_pending", "This self-grade is no longer open.")
    try:
        receipt = record_self_grade_disclosure_display(
            repository,
            practice_item_id=params.practice_item_id,
            submission_id=submission_id,
            # The trace the checkpoint froze: the row carries its hash, the
            # durable proof a later commit is that trace (round 4, F1-2).
            frozen_hash=frozen_trace_hash(disclosure["answer_md"], disclosure["explanation_md"]),
            display_id=str(params.display_id),
            learning_object_id=item.learning_object_id,
        )
    except DisplayNotRecorded as exc:
        raise SidecarError(
            "display_not_recorded", "The full answer couldn't be recorded. Try again.", retryable=True
        ) from exc
    return versioned(
        {
            "frozen": True,
            "recorded": True,
            "already_recorded": receipt.already_recorded,
            "recorded_at": receipt.recorded_at,
        }
    )


def _changed_after_disclosure(repository, session_id: str, practice_item_id: str, submission_id: str | None,
                              learner_answer_md: str) -> bool:
    """Did the learner submit a trace other than the one frozen before the
    plain self-grade showed a full answer (UX Phase 4, Codex review F1)?

    Such an answer was (or may have been) written with the answer in view, so
    it is recorded as primed. A read failure admits (never blocks a submit)."""

    if not submission_id:
        return False
    try:
        checkpoint = repository.fetch_session_checkpoint(session_id)
    except Exception:  # noqa: BLE001 - a receipt never fails a submit
        return False
    disclosure = draft_self_grade_disclosure(checkpoint)
    if (
        disclosure is None
        or disclosure["practice_item_id"] != practice_item_id
        or disclosure["submission_id"] != submission_id
    ):
        return False
    frozen = compose_learner_trace(disclosure["answer_md"], disclosure["explanation_md"])
    return frozen != learner_answer_md


def _plan_presentation(repository, params: Any) -> str | None:
    """The plan presentation an answer binds to: the one it sends, else the one
    its saved draft named under the same retry key (router R2a, review F5: a
    draft resumed after a restart). Binding is validated at the attempt
    insert, which drops a wrong or used id without failing the submit."""

    if params.plan_presentation_id:
        return params.plan_presentation_id
    if not getattr(params, "submission_id", None):
        return None
    try:
        checkpoint = repository.fetch_session_checkpoint(params.session_id)
    except Exception:  # noqa: BLE001 - a receipt never fails a submit
        return None
    return draft_plan_presentation(
        checkpoint, practice_item_id=params.practice_item_id, submission_id=params.submission_id,
    )


def _held_assistance(repository, item, hints_used: int, attempt_type: str, *,
                     held: tuple[Any, ...] | None = None, authored_hints: int | None = None,
                     book_counted: bool | None = None) -> tuple[int, str]:
    """Fold in the assistance the item's open workbench problems hold (Reader
    workbench RW2a, review F2): the book one counted and the answer-box hints
    it carried. The server holds them, so the record never depends on a
    client having restored them before Submit, and it is never clamped to the
    hints the item shows today. The carried part (book, carried hints) and
    the client's count overlap (a client that restored them already sends
    them): the larger of the two. The problem's own shown checks and level
    1-3 hints add to it (RW2b fix round 4, item 4:
    :func:`learnloop.attempts.hint_fold.combine_held`). An independent
    attempt type becomes the assisted one the answer box picks.

    On an item that allows only ``independent_attempt`` that type stays, with
    ``hints_used`` > 0: exactly what main records for an authored hint
    revealed there (the answer box's ``chooseAttemptType`` and
    ``stuck_attempt_type`` fall back to the item's default type). The one
    activity policy (``resolve_attempt_activity_policy``) reads ``hints_used``
    > 0 as assisted and never certifying whatever the type, so the attempt is
    never unassisted evidence (RW2a round 4, F2). ``held``: the parts
    :func:`_held_read` already took (RW2b fix round 1, F1)."""

    from learnloop.attempts.hint_fold import combine_held

    if held is None:
        held = _held_read(repository, item)[0]
    largest = max((book + carried + len(ids) for book, carried, ids in held), default=0)
    if largest <= 0:
        return hints_used, attempt_type
    if attempt_type == "independent_attempt":
        attempt_type = stuck_attempt_type(item.attempt_types_allowed, hints_used=largest)
    return combine_held(int(hints_used), held, authored_hints=authored_hints,
                        client_book=bool(book_counted)), attempt_type


def _held_read(repository, item) -> tuple[tuple[tuple[int, int], ...], bool]:
    """Reader workbench RW2b (§5.4): the help the item's open problems hold,
    ``(parts, primed)``: per problem ``(book, carried, assist_ids)`` (fix
    rounds 4 and 5, items 4-5), and whether any showed worked help (a level 4-5 hint, which primes
    every submit of the item). ``((), False)`` with no workbench help, so
    every submit is exactly as before RW2b."""

    from contextlib import closing

    from learnloop.db.connection import connect
    try:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            parts, primed, worked = _held_parts_with_window(connection, item.id)
    except Exception as exc:  # noqa: BLE001 -- a vault without the tables holds nothing
        log_event("workbench_held_read_failed", practice_item_id=item.id, error=type(exc).__name__)
        return (), False, ()
    return tuple(parts), bool(primed), tuple(worked)


def _held_parts_with_window(connection, practice_item_id: str):
    """The open problems' RW2a parts (book, carried) and, as one more part,
    the item's WINDOW of workbench server assists (RW2b fix round 13: H2b's R1
    rule, whatever their problem's status, ``help_assists.workbench_window_ids``),
    which the attempt counts once and attaches in its own transaction."""

    from learnloop.db.stores.help_assists import workbench_window
    from learnloop.reader.workbench import held_parts_on

    parts, _problem_primed = held_parts_on(connection, practice_item_id)
    window, worked = workbench_window(connection, practice_item_id=practice_item_id)
    rw2a = tuple((int(book), int(carried), ()) for book, carried, _ids in parts)
    # Fix round 14, item 1: primed is derived from the WINDOW (any level 4-5
    # row in it, whatever its problem's status), never from the problem's
    # state; those rows are attached but never counted.
    return rw2a + (((0, 0, tuple(window)),) if window else ()), bool(worked), tuple(worked)


def _held_reader(practice_item_id: str):
    """RW2b fix round 1, F1: the same read on the attempt's own write
    connection, for its transactional refold (the attempt path never reads
    the workbench; the sidecar hands it this callable). A check or hint shown
    while the submit was grading is then counted; none is shown after the
    attempt commits under its key (``help_assists.mark_shown``)."""

    def read(connection) -> tuple[tuple[Any, ...], bool]:
        try:
            return _held_parts_with_window(connection, practice_item_id)
        except sqlite3.OperationalError:
            # A vault without the workbench tables holds nothing.
            return (), False, ()

    return read


def _held_fields(item, held: tuple[tuple[Any, ...], bool], *, client_hints: int, extra_hints: int,
                 attempt_types: bool, authored_hints: int | None = None,
                 client_book: bool | None = None) -> dict[str, Any]:
    from learnloop.attempts.hint_fold import held_components

    parts = tuple(held[0])
    union, book, carried = held_components(parts)
    return {"held_reader": _held_reader(item.id), "held_client_hints": int(client_hints),
            "held_union": union, "held_book": book, "held_carried": carried, "held_known": True,
            "held_client_book": bool(client_book),
            "held_extra_hints": int(extra_hints),
            "held_hints": max((book + carried + len(ids) for book, carried, ids in parts), default=0),
            "held_parts": parts, "held_primed": bool(held[1]), "held_authored_hints": authored_hints,
            "held_worked": tuple(held[2]) if len(held) > 2 else (),
            "held_types": tuple(item.attempt_types_allowed or ()) if attempt_types else None}


def _bind_offer(repository, params, submission_id, *, entry_surface: str | None = None):
    # Reader workbench RW2a: a workbench submit names its own surface; every
    # other caller binds exactly as before (the store's default surface).
    surface = {} if entry_surface is None else {"entry_surface": entry_surface}
    candidate_id = params.scheduler_candidate_id
    if candidate_id is not None and repository.scheduler_offer_answered(
        scheduler_candidate_id=candidate_id, session_id=params.session_id, practice_item_id=params.practice_item_id,
    ):
        # Owner capture 2026-10-25 (B4), as the workbench's kept offer (review
        # F13): an offer of this item in this session that another attempt
        # already answered (a screen held it after the item was answered in
        # steps, say) is dropped, never the learner's answer. The attempt is
        # then unattributed (direct selection, never inferred), so no
        # propensity is claimed for a serve it did not answer. An offer that
        # is not this item's in this session is still refused.
        log_event("scheduler_offer_stale", practice_item_id=params.practice_item_id,
                  scheduler_candidate_id=candidate_id)
        candidate_id = None
    try:
        return repository.bind_submission_offer(
            submission_id=submission_id, session_id=params.session_id,
            practice_item_id=params.practice_item_id,
            scheduler_candidate_id=candidate_id,
            **surface,
        )
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


@method("recover_practice_submission", PracticeSubmissionRecoveryInput)
def recover_practice_submission(
    ctx: SidecarContext,
    params: PracticeSubmissionRecoveryInput,
) -> dict[str, Any]:
    """Recover a completed submit before trying to serve the item again.

    A diagnostic surface may become inactive as part of its attempt commit, so
    restart recovery cannot require ``get_practice_item`` to succeed first. A
    successful receipt is the exact response the original call produced;
    absence is typed pending state. An attempt without a receipt resumes its
    saved completion; one without completion work fails closed with
    ``submission_committed``.
    """

    vault, repository = ctx.require_vault()
    submission_id = _submission_id(params.submission_id, None)
    if submission_id is None:
        raise SidecarError(
            "validation_error",
            "submissionId must not be blank.",
            details={"field": "submissionId"},
        )
    # Exact receipts are durable completion facts. Read them before checking
    # mutable session/item state: the session may have ended or a single-use
    # item may have disappeared after the original response was produced.
    submission_id, _successor = answering_key(repository, submission_id, params.session_id, params.practice_item_id)
    cached = _cached_submission(ctx, vault, repository, submission_id, params.practice_item_id)
    if cached is not None:
        return versioned({"status": "recovered", "result": cached})
    _require_open_session(repository, params.session_id)
    if params.practice_item_id not in vault.practice_items:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
    return versioned({"status": "pending", "result": None})


@method("acknowledge_practice_submission", PracticeSubmissionAcknowledgementInput)
def acknowledge_practice_submission(
    ctx: SidecarContext,
    params: PracticeSubmissionAcknowledgementInput,
) -> dict[str, Any]:
    """Clear only the checkpoint whose authoritative result was received.

    The compare and delete are one repository transaction. A delayed client
    completion can therefore never erase a newer item's draft in the same
    session, even when navigation and the new save race this acknowledgement.
    """

    _vault, repository = ctx.require_vault()
    submission_id = _submission_id(params.submission_id, None)
    if submission_id is None:
        raise SidecarError(
            "validation_error",
            "submissionId must not be blank.",
            details={"field": "submissionId"},
        )
    checkpoint = repository.fetch_session_checkpoint(params.session_id)
    disclosure = draft_self_grade_disclosure(checkpoint)
    if (
        disclosure is not None
        and disclosure["practice_item_id"] == params.practice_item_id
        and disclosure["submission_id"] == submission_id
    ):
        # The self-graded draft committed: its full answer counts against the
        # next attempt (Codex review F1).
        settle_self_grade_disclosure(repository, checkpoint)
    status = repository.acknowledge_practice_checkpoint(
        params.session_id,
        practice_item_id=params.practice_item_id,
        submission_id=submission_id,
    )
    return versioned({"status": status, "acknowledged": status != "checkpoint_mismatch"})


@method("submit_attempt", SubmitAttemptInput)
def submit_attempt(ctx: SidecarContext, params: SubmitAttemptInput) -> dict[str, Any]:
    return submit_attempt_on(ctx, params)


def submit_attempt_on(
    ctx: SidecarContext, params: SubmitAttemptInput, *, entry_surface: str = "desktop_practice",
    hint_window_fold: bool = False,
) -> dict[str, Any]:
    """``submit_attempt``, recorded on ``entry_surface``. The one submit
    implementation: the Reader workbench (RW2a) composes its answer and calls
    this with its own surface, so a workbench submit is validated, graded,
    diagnosed and admitted (the one eligibility decision) exactly as every
    other; the RPC passes the practice screen's surface, unchanged."""

    vault, repository = ctx.require_vault()
    workbench_surface = None if entry_surface == "desktop_practice" else entry_surface
    submission_id, successor = answering_key(repository, submission_key(params), params.session_id,
                                             params.practice_item_id)
    if successor:
        params = params.model_copy(update={"submission_id": submission_id})
    cached = _cached_submission(ctx, vault, repository, submission_id, params.practice_item_id)
    if cached is not None:
        return cached
    # Fix round 2, item 2: a stale draft's carried help is not this attempt's.
    params, stale = _without_stale_help(repository, params, successor=successor)
    hint_window_fold = hint_window_fold or stale
    declared_stuck = params.declared_stuck and stuck_prompt_active(vault)
    if params.declared_stuck and not declared_stuck and not params.answer_md.strip() and not (
        params.explanation_md or ""
    ).strip():
        # A stuck answer from a surface drawn before stuck_prompt was turned
        # off is recorded exactly as that switch says today: an empty one is
        # "I don't know" (and a non-empty one the ordinary attempt below).
        return submit_dont_know_on(
            ctx,
            DontKnowInput(
                session_id=params.session_id,
                practice_item_id=params.practice_item_id,
                hints_used=params.hints_used,
                # Fix round 12, item 4: every optional count field goes along.
                authored_hints=params.authored_hints,
                book_counted=params.book_counted,
                latency_seconds=params.latency_seconds,
                probe_presentation_id=params.probe_presentation_id,
                answer_confidence=params.answer_confidence,
                assessment_contract_version_id=params.assessment_contract_version_id,
                submission_id=params.submission_id,
                scheduler_candidate_id=params.scheduler_candidate_id,
                plan_presentation_id=params.plan_presentation_id,
                difficulty_rating=params.difficulty_rating,
                first_hint_progress=params.first_hint_progress,
            ),
            entry_surface=entry_surface,
            hint_window_fold=hint_window_fold,
        )
    _require_open_session(repository, params.session_id)
    item = _require_active_item(vault, params.practice_item_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    held = _held_read(repository, item)
    client_hints, attempt_type = _held_assistance(repository, item, params.hints_used, params.attempt_type,
                                                  held=held[0], authored_hints=params.authored_hints,
                                                  book_counted=params.book_counted)
    # Substantive tutor questions asked mid-attempt count as hints: fold them
    # into hints_used so the existing hint dampening / FSRS rating caps apply.
    question_hints = hint_equivalents_for_submission(
        repository, params.practice_item_id, params.session_id
    )
    # A6: compose the one trace the grader reads, here and nowhere else. The
    # volunteered line arrives as its own field and is joined to the answer by
    # the module that owns the format, so the delimiter never appears in a
    # client, a handler, or a detection site.
    explanation_md = (params.explanation_md or "").strip() or None
    learner_answer_md = compose_learner_trace(params.answer_md, explanation_md)
    # Codex review F1: the plain self-grade showed a full answer after
    # freezing this draft's trace, and the trace changed since.
    disclosure_primed = not params.primed and _changed_after_disclosure(
        repository, params.session_id, params.practice_item_id, submission_id, learner_answer_md
    )
    # Adaptive hints H2a (spec §5): the service's shown hints of this
    # submission, counted by the server beside the tutor questions (levels
    # 1-3 add one each; levels 4-5 set primed). The client keeps counting
    # only the authored hints it revealed itself, so nothing counts twice.
    # The draft carries the fold; the attempt's transaction takes it again
    # (review round 2, V1).
    hint_fold = _server_hint_fold(
        repository, params.practice_item_id, params.session_id, submission_id,
        base_hints=client_hints + question_hints,
        base_primed=bool(params.primed) or disclosure_primed,
        max_useful_hints=item.hint_policy.max_useful_hints, window_fold=hint_window_fold,
        held=_held_fields(item, held, client_hints=params.hints_used, extra_hints=question_hints,
                          attempt_types=True, authored_hints=params.authored_hints,
                          client_book=params.book_counted),
    )
    hints_used = hint_fold.hints_used()
    primed = hint_fold.primed()
    if disclosure_primed and not hint_fold.folded_primed:
        log_event("self_grade_trace_changed_after_disclosure", session_id=params.session_id,
                  practice_item_id=params.practice_item_id)
    scheduler_candidate_id = _bind_offer(repository, params, submission_id, entry_surface=workbench_surface)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md=learner_answer_md,
        elicited_explanation_md=explanation_md,
        attempt_type=attempt_type,
        hints_used=hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
        primed=primed,
        probe_presentation_id=params.probe_presentation_id,
        plan_presentation_id=_plan_presentation(repository, params),
        answer_confidence=params.answer_confidence,
        assessment_contract_version_id=params.assessment_contract_version_id,
        submission_id=submission_id,
        scheduler_candidate_id=scheduler_candidate_id,
        entry_surface=entry_surface,
        evidence_origin="human",
        declared_stuck=declared_stuck,
        server_hint_fold=hint_fold,
        difficulty_rating=params.difficulty_rating,
        first_hint_progress=params.first_hint_progress,
    )
    hint_submitted_at = _stamp_hint_submission(
        vault, repository, submission_id, params.practice_item_id, params.latency_seconds
    )
    _stamp_window_hints(repository, hint_fold, hint_submitted_at)
    # Fix round 4, F12: the admission time goes with the fold, so a row the
    # attempt's transactional refold takes is stamped then (first stamp kept).
    hint_fold = _dataclass_replace(hint_fold, submitted_at=hint_submitted_at)
    draft = _dataclass_replace(draft, server_hint_fold=hint_fold)
    if declared_stuck and not learner_answer_md.strip():
        # An empty stuck answer: nothing to grade, so no provider and no
        # self-grade; recorded at once as an ordinary attempt scored 0.
        return _record_empty_stuck(
            ctx, vault, repository, draft, params.session_id, before, hint_submitted_at=hint_submitted_at
        )
    self_grade = _self_grade(params.self_grade)
    provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    unavailable_label = "AI grading"
    try:
        if self_grade is None:
            if not runtime.ready or client is None:
                raise SidecarError(
                    "grading_fallback_required",
                    f"{unavailable_label} is unavailable. Grade your answer to continue.",
                    retryable=True,
                )
            if provider_name not in CODEX_PROVIDER_NAMES:
                result = complete_attempt_with_ai_required(
                    vault,
                    repository,
                    draft,
                    runtime=runtime,
                    ai_client=client,
                )
            else:
                result = complete_attempt_with_codex_required(
                    vault,
                    repository,
                    draft,
                    runtime=runtime,
                    codex_client=client,
                )
        else:
            if provider_name not in CODEX_PROVIDER_NAMES:
                result = complete_attempt_with_ai_fallback(
                    vault,
                    repository,
                    draft,
                    self_grade,
                    runtime=runtime,
                    ai_client=client,
                )
            else:
                result = complete_attempt_with_codex_fallback(
                    vault,
                    repository,
                    draft,
                    self_grade,
                    runtime=runtime,
                    codex_client=client,
                )
    except SidecarError:
        raise
    except (CodexUnavailable, TimeoutError):
        raise SidecarError(
            "grading_fallback_required",
            f"{unavailable_label} is unavailable. Grade your answer to continue.",
            retryable=True,
        )
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except sqlite3.IntegrityError:
        # A concurrent request with the same submission id committed first;
        # the unique submission index rejected this one. Answer with the
        # winner's attempt.
        winner = _cached_submission(ctx, vault, repository, submission_id, params.practice_item_id)
        if winner is None:
            raise
        return winner
    run_post_attempt_pipeline(
        vault,
        repository,
        result=result,
        session_id=params.session_id,
        self_grade=self_grade,
        ai_client=client if runtime.ready else None,
    )
    # Slice 1 §11: the diagnosis (if one was queued) runs on the worker.
    ctx.resume_post_attempt_jobs()
    # Keep the checkpoint (including its stable submission id) until the client
    # explicitly acknowledges this full result with clear_session_checkpoint.
    # If the response is lost, a restarted client can resend the durable key and
    # recover this exact route from the receipt instead of minting a new grade.
    _log_attempt_recorded(repository, params.session_id, learner_answer_md, result)
    _log_state_update(vault, repository, "submit_attempt", params.session_id, before, result)
    payload = _attempt_result(result, repository, vault)
    _store_submission_receipt(repository, submission_id, result.attempt_id, result.practice_item_id, payload)
    _attach_hint_reveals(
        vault, repository, submission_id, result.practice_item_id, result.attempt_id, submitted_at=hint_submitted_at,
        latency_seconds=params.latency_seconds,
    )
    # Adaptive hints H2b (spec §6.1, D11): a hinted answer graded not fully
    # correct is placed on its item's approach map in the background, after
    # the response is built. Measurement only; the submit never waits on it,
    # fails because of it or changes because of it.
    _schedule_hint_outcome(ctx, vault, repository, result.attempt_id)
    return payload


def _schedule_hint_outcome(ctx: SidecarContext, vault, repository, attempt_id: str) -> None:
    try:
        from learnloop.hints.outcome import schedule_outcome_placement

        schedule_outcome_placement(vault, repository.sqlite_path, attempt_id,
                                   client=getattr(ctx, "hint_outcome_client", None),
                                   builds=getattr(ctx, "map_builds", None))
    except Exception as exc:  # noqa: BLE001 -- never reaches the submit
        log_event("hint_outcome_schedule_failed", attempt_id=attempt_id, error=type(exc).__name__)


@method("submit_dont_know", DontKnowInput)
def submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]:
    return submit_dont_know_on(ctx, params)


def submit_dont_know_on(
    ctx: SidecarContext, params: DontKnowInput, *, entry_surface: str = "desktop_practice",
    hint_window_fold: bool = False,
) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    workbench_surface = None if entry_surface == "desktop_practice" else entry_surface
    submission_id, successor = answering_key(repository, submission_key(params), params.session_id,
                                             params.practice_item_id)
    if successor:
        params = params.model_copy(update={"submission_id": submission_id})
    cached = _cached_submission(ctx, vault, repository, submission_id, params.practice_item_id)
    if cached is not None:
        return cached
    # Fix round 2, item 2, as in ``submit_attempt_on``.
    params, stale = _without_stale_help(repository, params, successor=successor)
    hint_window_fold = hint_window_fold or stale
    _require_open_session(repository, params.session_id)
    item = _require_active_item(vault, params.practice_item_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    # The item's open workbench problems' assistance counts here too (RW2a F2).
    held = _held_read(repository, item)
    hints_used, _type = _held_assistance(repository, item, params.hints_used, "independent_attempt", held=held[0],
                                         authored_hints=params.authored_hints, book_counted=params.book_counted)
    # Adaptive hints H2a (spec §5): a shown hint is never lost, here too. The
    # tutor-question fold's absence here predates H2a and is left as it was
    # (spec §14 Q5); the clamp applies to the total the server's rows join.
    # An empty stuck answer's attempt type follows the count (the attempt's
    # transaction takes the fold again with the same rule, review round 2, V1).
    stuck = stuck_prompt_active(vault)
    hint_fold = _server_hint_fold(
        repository, params.practice_item_id, params.session_id, submission_id,
        base_hints=hints_used,
        max_useful_hints=item.hint_policy.max_useful_hints, clamp_without_fold=False,
        stuck_types=tuple(item.attempt_types_allowed or ()) if stuck else None,
        stuck_probe=params.probe_presentation_id is not None, window_fold=hint_window_fold,
        held=_held_fields(item, held, client_hints=params.hints_used, extra_hints=0, attempt_types=False,
                          authored_hints=params.authored_hints, client_book=params.book_counted),
    )
    hints_used = hint_fold.hints_used()
    server_primed = hint_fold.primed()
    hint_submitted_at = _stamp_hint_submission(
        vault, repository, submission_id, params.practice_item_id, params.latency_seconds
    )
    _stamp_window_hints(repository, hint_fold, hint_submitted_at)
    # Fix round 4, F12: the admission time goes with the fold (see above).
    hint_fold = _dataclass_replace(hint_fold, submitted_at=hint_submitted_at)
    if stuck:
        # mvp-0.13: "I don't know" no longer records `dont_know`. A client
        # still sending it gets what "I'm stuck" with an empty box records:
        # an ordinary attempt scored 0 at the standard mass.
        draft = AttemptDraft(
            practice_item_id=params.practice_item_id,
            learner_answer_md="",
            attempt_type=hint_fold.attempt_type("independent_attempt"),
            hints_used=hints_used,
            latency_seconds=params.latency_seconds,
            session_id=params.session_id,
            primed=server_primed,
            probe_presentation_id=params.probe_presentation_id,
            plan_presentation_id=_plan_presentation(repository, params),
            answer_confidence=params.answer_confidence,
            assessment_contract_version_id=params.assessment_contract_version_id,
            submission_id=submission_id,
            scheduler_candidate_id=_bind_offer(repository, params, submission_id, entry_surface=workbench_surface),
            entry_surface=entry_surface,
            evidence_origin="human",
            declared_stuck=True,
            server_hint_fold=hint_fold,
            difficulty_rating=params.difficulty_rating,
            first_hint_progress=params.first_hint_progress,
        )
        return _record_empty_stuck(
            ctx, vault, repository, draft, params.session_id, before, hint_submitted_at=hint_submitted_at
        )
    grade = _self_grade(params.self_grade) or SelfGradeInput(criterion_points={}, confidence=3)
    scheduler_candidate_id = _bind_offer(repository, params, submission_id, entry_surface=workbench_surface)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md="",
        attempt_type="diagnostic_probe" if params.probe_presentation_id else "dont_know",
        hints_used=hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
        primed=server_primed,
        probe_presentation_id=params.probe_presentation_id,
        plan_presentation_id=_plan_presentation(repository, params),
        answer_confidence=params.answer_confidence,
        assessment_contract_version_id=params.assessment_contract_version_id,
        submission_id=submission_id,
        scheduler_candidate_id=scheduler_candidate_id,
        entry_surface=entry_surface,
        evidence_origin="human",
        declared_dont_know=True,
        server_hint_fold=hint_fold,
        difficulty_rating=params.difficulty_rating,
        first_hint_progress=params.first_hint_progress,
    )
    try:
        result = complete_self_graded_attempt(vault, repository, draft, grade)
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except sqlite3.IntegrityError:
        # A concurrent request with the same submission id committed first;
        # the unique submission index rejected this one. Answer with the
        # winner's attempt.
        winner = _cached_submission(ctx, vault, repository, submission_id, params.practice_item_id)
        if winner is None:
            raise
        return winner
    run_post_attempt_pipeline(
        vault,
        repository,
        result=result,
        session_id=params.session_id,
    )
    # Client acknowledgment owns checkpoint removal; see submit_attempt.
    _log_attempt_recorded(repository, params.session_id, "", result)
    _log_state_update(vault, repository, "submit_dont_know", params.session_id, before, result)
    payload = _attempt_result(result, repository, vault)
    _store_submission_receipt(repository, submission_id, result.attempt_id, result.practice_item_id, payload)
    _attach_hint_reveals(
        vault, repository, submission_id, result.practice_item_id, result.attempt_id, submitted_at=hint_submitted_at,
        latency_seconds=params.latency_seconds,
    )
    return payload


def _record_empty_stuck(
    ctx: SidecarContext,
    vault,
    repository,
    draft: AttemptDraft,
    session_id: str,
    before,
    *,
    hint_submitted_at: str | None = None,
) -> dict[str, Any]:
    """Commit an empty "I'm stuck" answer and answer like any submission.

    No model call: the deterministic zero is instant (frictionless P7). The
    learner is routed to feedback exactly as after "I don't know".
    """

    try:
        result = complete_empty_stuck_attempt(vault, repository, draft)
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except sqlite3.IntegrityError:
        winner = _cached_submission(ctx, vault, repository, draft.submission_id, draft.practice_item_id)
        if winner is None:
            raise
        return winner
    run_post_attempt_pipeline(
        vault,
        repository,
        result=result,
        session_id=session_id,
    )
    ctx.resume_post_attempt_jobs()
    _log_attempt_recorded(repository, session_id, "", result)
    _log_state_update(vault, repository, "submit_stuck_empty", session_id, before, result)
    payload = _attempt_result(result, repository)
    _store_submission_receipt(repository, draft.submission_id, result.attempt_id, result.practice_item_id, payload)
    _attach_hint_reveals(
        vault, repository, draft.submission_id, result.practice_item_id, result.attempt_id,
        submitted_at=hint_submitted_at, latency_seconds=draft.latency_seconds,
    )
    return payload


def _submission_id(client_id: str | None, presentation_id: str | None) -> str | None:
    """Return the stable retry key; old probe clients inherit one for free."""

    if client_id and client_id.strip():
        return client_id.strip()
    if presentation_id:
        return f"probe:{presentation_id}"
    return None


def submission_key(params: Any) -> str | None:
    """The retry key a request's attempt, receipt and model calls are keyed on."""

    return _submission_id(
        getattr(params, "submission_id", None),
        getattr(params, "probe_presentation_id", None),
    )


def answering_key(repository, submission_id: str | None, session_id: str,
                  practice_item_id: str) -> tuple[str | None, bool]:
    """The key a submission's attempt, intent and receipt are written under,
    and whether it is a successor of the client's (owner capture 2026-10-25, B4).

    A retry key whose bound offer another submission's attempt answered (the
    answer box's draft, after the item was submitted in steps) answers no
    open offer, and its intent, which is immutable, still names that offer:
    an attempt written under it would be read as a second answer to one
    serve. Such a submission is written under a successor key derived from
    the client's key and the attempt that answered the offer, so it is
    deterministic (a retry, a recovery, finds the same attempt) and its
    intent binds no answered offer. Its hints fold by the keyless window
    (since the item's last attempt in the session, H2b ruling R1), so a hint
    of the earlier attempt is never counted on this one. Any other key is
    its own. Only a key bound in this session has a successor (fix round 2,
    item 1): another session's key stays as it is, and the bind refuses it
    as another session's."""

    if submission_id is None:
        return None, False
    answered_by = repository.submission_offer_answered_elsewhere(
        submission_id=submission_id, session_id=session_id, practice_item_id=practice_item_id)
    if answered_by is None:
        return submission_id, False
    return f"{submission_id}~after~{answered_by}", True


def _without_stale_help(repository, params: Any, *, successor: bool) -> tuple[Any, bool]:
    """The submit's params with the help a stale draft carried taken out, and
    whether the draft was stale (owner capture 2026-10-25, fix round 2,
    item 2).

    A submission written under a successor key (:func:`answering_key`), or
    naming an offer another attempt already answered (``_bind_offer``'s fail
    soft), comes from a draft that outlived an earlier attempt of the item:
    a checkpoint the owner's bug left behind restores the answer box's key
    and its ``hintsUsed``, and the hints it counts were shown before that
    attempt, which counted them. The client's count, its authored count, its
    book and its first-hint marker are therefore not this attempt's. Only
    help inside the item's window since its last attempt in this session
    counts, the server-side rule (H2b ruling R1): the server's rows by the
    window fold (the caller switches it on), and the authored hints the
    screen revealed in that window by their H0 rows (never more than the
    client reports). With ``hints.telemetry_enabled`` off no reveal is
    recorded, so a stale draft's authored hints count nothing."""

    stale = successor or (
        params.scheduler_candidate_id is not None
        and repository.scheduler_offer_answered(
            scheduler_candidate_id=params.scheduler_candidate_id, session_id=params.session_id,
            practice_item_id=params.practice_item_id,
        )
    )
    if not stale:
        return params, False
    client = int(params.authored_hints if params.authored_hints is not None else params.hints_used)
    kept = min(client, _window_authored_reveals(repository, params.practice_item_id, params.session_id))
    update: dict[str, Any] = {"hints_used": kept, "book_counted": None, "first_hint_progress": None}
    if params.authored_hints is not None:
        update["authored_hints"] = kept
    if int(params.hints_used) != kept:
        log_event("stale_draft_help_dropped", practice_item_id=params.practice_item_id,
                  client_hints=int(params.hints_used), kept_hints=kept)
    return params.model_copy(update=update), True


def _window_authored_reveals(repository, practice_item_id: str, session_id: str) -> int:
    """The authored hints the practice screen revealed on the item in this
    session since its last attempt there (H0 rows; any key): a read."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import authored_reveals_in_window, keyless_window_start

    try:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            since = keyless_window_start(connection, practice_item_id=practice_item_id, session_id=session_id)
            return authored_reveals_in_window(connection, practice_item_id=practice_item_id,
                                              session_id=session_id, since=since)
    except sqlite3.OperationalError:
        # A vault without ``help_assists`` recorded no reveal.
        return 0


def _cached_submission(
    ctx: SidecarContext, vault, repository, submission_id: str | None, practice_item_id: str
) -> dict[str, Any] | None:
    """The response for a submission that was already committed, if any.

    A process can stop after the attempt transaction and before the response
    receipt. Never grade or re-apply the same submission: resume its saved
    completion, or fail closed when none was saved. An attempt id alone is not
    an authoritative UI route, because a diagnostic response may have deferred
    feedback or closed a block.
    """

    if submission_id is None:
        return None
    receipt = repository.attempt_submission_receipt(submission_id)
    if receipt is not None:
        _require_same_item(receipt["practice_item_id"], practice_item_id)
        # Adaptive hints H0 (review F1): repair an attach the original call
        # failed to make (idempotent; telemetry only).
        _attach_hint_reveals(vault, repository, submission_id, practice_item_id, receipt["attempt_id"])
        # H2b (review F5): and the outcome placement a process that ended
        # after the receipt never scheduled (no-op once placed).
        _schedule_hint_outcome(ctx, vault, repository, str(receipt["attempt_id"]))
        return receipt["result"]
    attempt = repository.practice_attempt_by_submission_id(submission_id)
    if attempt is None:
        return None
    _require_same_item(attempt["practice_item_id"], practice_item_id)
    # The attempt committed: its revealed hints are its own, whatever the
    # route answered below (adaptive hints H0, review F1).
    _attach_hint_reveals(vault, repository, submission_id, practice_item_id, attempt["id"])
    # H2b (review F5): a committed attempt's outcome placement, whatever
    # the route answers below (measurement only; no-op once placed).
    _schedule_hint_outcome(ctx, vault, repository, str(attempt["id"]))
    work = repository.attempt_completion(attempt["id"])
    if work is None:
        raise _submission_committed(attempt)
    try:
        return _resume_saved_completion(ctx, vault, repository, work, submission_id)
    except CompletionRouteUnknown as exc:
        raise _submission_committed(attempt) from exc


def _resume_saved_completion(
    ctx: SidecarContext, vault, repository, work: dict[str, Any], submission_id: str
) -> dict[str, Any]:
    """Complete a committed attempt from its saved result and store the receipt.

    Only misconception normalization uses the provider client; the grade is
    the saved one. A session that has ended since the attempt gets no new
    follow-up insertions.
    """

    result = AttemptResult.from_dict(work["result"])
    run_post_attempt_pipeline(
        vault,
        repository,
        result=result,
        session_id=_open_session_id(repository, work["session_id"]),
        ai_client=_normalization_client(ctx, vault),
    )
    ctx.resume_post_attempt_jobs()
    payload = _attempt_result(result, repository, vault)
    _store_submission_receipt(repository, submission_id, result.attempt_id, result.practice_item_id, payload)
    return payload


def _normalization_client(ctx: SidecarContext, vault) -> Any | None:
    _provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    return client if runtime.ready else None


def _open_session_id(repository, session_id: str | None) -> str | None:
    if session_id is None:
        return None
    session = repository.fetch_session(session_id)
    if session is None or session["ended_at"] is not None:
        return None
    return session_id


def _require_same_item(recorded_item_id: str, practice_item_id: str) -> None:
    if recorded_item_id != practice_item_id:
        raise SidecarError("validation_error", "submission id was already used for another item")


def _submission_committed(attempt: dict[str, Any]) -> SidecarError:
    return SidecarError(
        "submission_committed",
        f"Attempt {attempt['id']} was recorded, but its completion route is unavailable. Retry recovery without changing the submission id.",
        retryable=False,
        details={
            "attempt_id": attempt["id"],
            "attempt_type": attempt.get("attempt_type"),
            "route_status": "unknown",
        },
    )


def _store_submission_receipt(
    repository,
    submission_id: str | None,
    attempt_id: str,
    practice_item_id: str,
    payload: dict[str, Any],
) -> None:
    if submission_id is None:
        return
    repository.insert_attempt_submission_receipt(
        submission_id=submission_id,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        result=payload,
    )


@method("skip_practice_item", SkipInput)
def skip_practice_item(ctx: SidecarContext, params: SkipInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    session = _require_open_session(repository, params.session_id)
    trace = offer_trace_for(vault, params.session_id)
    queue = build_due_queue(
        vault,
        repository,
        session=SchedulerSession(
            session_id=params.session_id,
            available_minutes=session.get("available_minutes"),
            energy=session.get("energy"),
        ),
        offer_trace=trace,
    )
    queue, dtos = publish_offer(
        ctx, vault, repository, queue, trace=trace, surface="skip_requeue",
        removed_ids=frozenset({params.practice_item_id}),
    )
    clear_checkpoint(repository, params.session_id)
    return versioned(
        {
            "generated_at": utc_now_iso(),
            "session_id": params.session_id,
            "sections": _sections(dtos),
            "total_items": len(dtos),
        }
    )


def _self_grade(payload: SelfGradeInputDto | None) -> SelfGradeInput | None:
    if payload is None:
        return None
    return SelfGradeInput(
        criterion_points=payload.criterion_points,
        confidence=payload.confidence,
        fatal_errors=payload.fatal_errors,
        error_type=payload.error_type,
        notes=payload.notes,
        error_attributions=[
            SelfGradeErrorAttribution(error_type=attribution.error_type, criterion_id=attribution.criterion_id)
            for attribution in payload.error_attributions
        ]
        if payload.error_attributions
        else None,
    )


def _attempt_result(result, repository=None, vault=None) -> dict[str, Any]:
    # `probe_block_end` rides along inside as_dict() (camelized to
    # probeBlockEnd): the §5.7 hook payload with released feedback and route.
    payload = versioned(result.as_dict())
    if repository is not None:
        # Probe redesign §5.6/§5.7: the client defers feedback while the
        # attempt's diagnostic episode is still measuring; the block-end hook
        # releases the block's withheld feedback and routes the learner.
        work = repository.attempt_completion(result.attempt_id)
        if work is not None and work["status"] == "completed":
            route = work["route"]
        else:
            # An unanswered opening episode placement ignores holds back no
            # feedback (owner decision 2026-10-12): the answer is new material.
            from learnloop.placement.state import servable_open_episode

            episode = (
                servable_open_episode(vault, repository, result.learning_object_id)
                if vault is not None
                else repository.open_probe_episode(result.learning_object_id)
            )
            route = probe_route(repository, result, episode_id=episode.id if episode is not None else None)
        payload["probeEpisode"] = to_camel(route)
        # Slice 1 §11: a blind-graded attempt's diagnosis runs after the
        # response; the feedback view polls ``diagnosis_status`` while pending.
        # Absent (not_needed) for attempts that queued no diagnosis.
        from learnloop.diagnosis.split.jobs import NOT_NEEDED, diagnosis_status

        status = diagnosis_status(repository, result.attempt_id)["status"]
        if status != NOT_NEEDED:
            payload["diagnosisStatus"] = status
        mark_released_held(payload, repository)
    return payload


def mark_released_held(payload: dict[str, Any], repository) -> None:
    """UX Phase 4 (display only): each released short-check answer says whether
    its grade is held for review (THE held predicate), so the result shows
    "held for review" and never the grader's provisional score."""

    block_end = payload.get("probeBlockEnd")
    released = block_end.get("releasedFeedback") if isinstance(block_end, dict) else None
    if not released:
        return
    from learnloop.held_grades import held_attempt_ids

    held = held_attempt_ids(repository, (entry.get("attemptId") for entry in released))
    for entry in released:
        entry["heldForReview"] = entry.get("attemptId") in held


def _log_attempt_recorded(repository, session_id: str, answer_md: str, result) -> None:
    attempt = repository.fetch_practice_attempt(result.attempt_id) or {}
    surprise = repository.latest_attempt_surprise(result.attempt_id) or {}
    feedback = repository.fetch_attempt_feedback_metadata(result.attempt_id) or {}
    log_event(
        "attempt_recorded",
        session_id=session_id,
        attempt_id=result.attempt_id,
        practice_item_id=result.practice_item_id,
        learning_object_id=result.learning_object_id,
        scheduler_slate_id=attempt.get("scheduler_slate_id"),
        scheduler_candidate_id=attempt.get("scheduler_candidate_id"),
        learner_answer_md=answer_md,
        rubric_score=result.rubric_score,
        correctness=result.correctness,
        hints_used=attempt.get("hints_used"),
        latency_seconds=attempt.get("latency_seconds"),
        grading_source=result.grading_source,
        grader_confidence=result.grader_confidence,
        feedback_md=feedback.get("feedback_md"),
        triggered_actions=surprise.get("triggered_actions"),
        suppressed_actions=surprise.get("suppressed_actions"),
    )


def _latent_snapshot(vault, repository, practice_item_id: str) -> dict[str, Any] | None:
    """Capture pre-attempt latent state for a practice item, for debug deltas.

    Returns ``None`` (and does no work) unless sidecar debug logging is enabled.
    """

    if not debug_enabled():
        return None
    item = vault.practice_items.get(practice_item_id)
    learning_object = vault.learning_object_for_item(item) if item is not None else None
    if learning_object is None:
        return {"learning_object_id": None}
    mastery = repository.mastery_state(learning_object.id)
    probe = repository.probe_state(learning_object.id)
    explanation = repository.latest_scheduler_explanation(practice_item_id)
    return {
        "learning_object_id": learning_object.id,
        "mastery_mean": _display_mean(mastery),
        "mastery_variance": _display_variance(mastery),
        "evidence_count": mastery.evidence_count if mastery is not None else 0,
        "probe_status": probe.status if probe is not None else None,
        "probe_completed": probe.probe_attempts_completed if probe is not None else None,
        "probe_target": probe.probe_attempts_target if probe is not None else None,
        # The EIG that motivated selecting this probe item, so realized updates
        # can be compared against expected information gain.
        "expected_information_gain": explanation.get("expected_information_gain") if explanation else None,
    }


def _log_state_update(vault, repository, method_name: str, session_id: str, before, result) -> None:
    if not debug_enabled():
        return
    probe_after = repository.probe_state(result.learning_object_id)
    before = before or {}
    before_var = before.get("mastery_variance")
    trace = result.mastery_trace
    # Realized IG over the same hypothesis set probe-EIG is computed on, so the
    # debug stream shows expected vs actual information gain side by side.
    posterior = probe_posterior(vault, repository, result.learning_object_id)
    log_event(
        "state_update",
        method=method_name,
        session_id=session_id,
        attempt_id=result.attempt_id,
        practice_item_id=result.practice_item_id,
        learning_object_id=result.learning_object_id,
        attempt_type="dont_know" if method_name == "submit_dont_know" else None,
        rubric_score=result.rubric_score,
        correctness=result.correctness,
        grading_source=result.grading_source,
        # Latent (mastery) delta: what the user space actually learned.
        mastery_mean_before=before.get("mastery_mean"),
        mastery_mean_after=result.mastery_mean,
        mastery_variance_before=before_var,
        mastery_variance_after=result.mastery_variance,
        mastery_variance_reduction=(
            round(before_var - result.mastery_variance, 6) if before_var is not None else None
        ),
        evidence_count_before=before.get("evidence_count"),
        # IRT 2PL picture of the mastery update (spec_irt_difficulty.md §7.2): the
        # "easy correct vs hard correct" distinction, with the mean/confidence split.
        item_difficulty_b=round(trace.difficulty_b, 4) if trace is not None else None,
        item_discrimination_a=round(trace.discrimination_a, 4) if trace is not None else None,
        expected_correctness=round(trace.expected_correctness, 4) if trace is not None else None,
        predicted_score=round(trace.predicted_score, 4) if trace is not None else None,
        observed_y=round(trace.observed_y, 4) if trace is not None else None,
        innovation=round(trace.innovation, 4) if trace is not None else None,
        sensitivity_h=round(trace.sensitivity_h, 4) if trace is not None else None,
        measurement_noise=round(trace.measurement_noise, 4) if trace is not None else None,
        kalman_gain=round(trace.kalman_gain, 4) if trace is not None else None,
        variance_reduction=round(trace.variance_reduction, 4) if trace is not None else None,
        mu_step=round(trace.mu_step, 4) if trace is not None else None,
        step_capped=trace.step_capped if trace is not None else None,
        mu_clamped=trace.mu_clamped if trace is not None else None,
        # Probe progress + the EIG that justified this elicitation vs realized IG.
        expected_information_gain=before.get("expected_information_gain"),
        realized_information_gain=(
            round(posterior.normalized_information_gain, 4) if posterior is not None else None
        ),
        posterior_top_probability=(round(posterior.top_probability, 4) if posterior is not None else None),
        posterior=(
            {label: round(value, 4) for label, value in posterior.posterior.items()}
            if posterior is not None
            else None
        ),
        probe_status_before=before.get("probe_status"),
        probe_status_after=probe_after.status if probe_after is not None else None,
        probe_completed_after=probe_after.probe_attempts_completed if probe_after is not None else None,
        probe_target=probe_after.probe_attempts_target if probe_after is not None else None,
        families_converged=probe_after.families_converged if probe_after is not None else None,
        # Surprise + downstream effects.
        surprise_direction=result.surprise_direction,
        predictive_surprise=round(result.predictive_surprise, 4),
        bayesian_surprise=round(result.bayesian_surprise, 4),
        due_at=result.due_at,
        fsrs_rating=result.fsrs_rating,
        error_event_ids=result.error_event_ids or None,
    )


def _display_mean(mastery) -> float | None:
    if mastery is None:
        return None
    from learnloop.learner.mastery import display_mastery

    return display_mastery(mastery).mastery_mean


def _display_variance(mastery) -> float | None:
    if mastery is None:
        return None
    from learnloop.learner.mastery import display_mastery

    return display_mastery(mastery).mastery_variance


def _require_open_session(repository, session_id: str) -> dict[str, Any]:
    session = repository.fetch_session(session_id)
    if session is None:
        raise SidecarError("not_found", f"Session {session_id} was not found.")
    if session["ended_at"] is not None:
        raise SidecarError("validation_error", f"Session {session_id} has ended.")
    return session
