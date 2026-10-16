from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from typing import Any

from learnloop.clock import SystemClock, utc_now_iso
from learnloop.substrate.instrument_serving import (
    UNSERVABLE_ERROR_CODE,
    unservable_refusal,
)
from learnloop.content.proposals.proposals import queue_accepted_diagnostic_followups
from learnloop.daily_plan.engine import plan_active
from learnloop.projects.capture import auto_sweep
from learnloop.scheduling.reentry_summary import reentry_session_cap
from learnloop.router.decisions import (
    build_today_offer_decision,
    logging_enabled,
    record_decision,
)
from learnloop.scheduling.scheduler import (
    SELECTION_POLICY,
    OfferTrace,
    ScheduledItem,
    SchedulerSession,
    build_due_queue,
    deferred_cold_followups,
    explain_practice_item,
)
from learnloop_sidecar.context import SidecarContext
from learnloop.content.pipeline.jobs import APPLYING_JOB_TYPES
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.goals import _nearest_active_goal
from learnloop_sidecar.handlers.serializers import (
    _due_status,
    latest_scheduler_explanation_dto,
    practice_item_detail,
    scheduled_item_dtos,
    scheduler_explanation_dto,
)
from learnloop_sidecar.handlers.teach_back import (
    TEACH_BACK_PRACTICE_MODE,
    filter_unready_teach_back_items,
    teach_back_offerable,
)
from learnloop_sidecar.logging import log_event
from learnloop_sidecar.registry import method
from learnloop_sidecar.serving import refuse_held_out_item, refuse_unservable_item


class QueueInput(ParamsModel):
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None
    limit: int | None = None


class PracticeItemInput(ParamsModel):
    practice_item_id: str


#: Job types whose completion must invalidate the sidecar's in-memory vault.
#:
#: This MUST stay in sync with ``pipeline.jobs.APPLYING_JOB_TYPES`` — that tuple
#: is the authority on which jobs change vault content, and any job listed there
#: but missing here applies items the Today queue then cannot see, because
#: ``get_today_queue`` reads the cached snapshot, so the set is derived rather
#: than restated.
_QUEUE_RELOAD_JOB_TYPES = frozenset(APPLYING_JOB_TYPES)


@method("get_queue_revision", ParamsModel)
def get_queue_revision(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    """Cheap durable high-water mark for asynchronous Today invalidation."""

    # A promotion job can write vault YAML between UI ticks. Reload exactly
    # once when its durable job completes so the subsequent Today refetch sees
    # the new item, rather than the pre-authoring in-memory vault snapshot.
    completed = [
        job["id"]
        for batch in ctx.ingest_jobs.list_batches(limit=8)
        for job in batch.get("jobs") or []
        if job.get("job_type") in _QUEUE_RELOAD_JOB_TYPES
        and job.get("status") == "completed"
        and ctx.ingest_jobs.needs_reload(job["id"])
    ]
    if completed:
        ctx.reload(maintenance=False)
        for job_id in completed:
            ctx.ingest_jobs.mark_reloaded(job_id)
    _vault, repository = ctx.require_vault()
    return versioned(repository.queue_revision())


def prepare_queue_build(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> None:
    """What every Today queue build does first (``get_today_queue`` and the plan)."""

    # Project understanding M1 (spec §3.2): the plan-build capture sweep. Git
    # only, throttled, never raises, and a no-op when no repo is enrolled.
    auto_sweep(
        vault.root,
        vault.config,
        trigger="plan_build",
        min_interval_minutes=vault.config.project.plan_sweep_min_interval_minutes,
        busy_timeout_ms=250,
    )
    # One connection for the whole backfill: it makes two small repository
    # calls per proposal batch, and opening a connection per call dominated
    # the Today refresh.
    with repository.pinned():
        queue_accepted_diagnostic_followups(repository)
    _wait_for_session_diagnoses(ctx, vault, repository, session_id)


@method("get_today_queue", QueueInput)
def get_today_queue(ctx: SidecarContext, params: QueueInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    prepare_queue_build(ctx, vault, repository, params.session_id)
    # Owner decision P6: after a break the session is the welcome-back panel's
    # "N refreshers" -- the scheduler's top N picks, never more (a smaller
    # requested limit still wins). The panel reads the cap back from this reply.
    # Daily-loop DL1 (daily_plan_v1): while the finite plan serves, re-entry is
    # the plan's own small automatic session (§7), so this full list -- one key
    # away from the plan -- is never capped (L3: picks from it are honoured).
    reentry_cap = (
        None
        if plan_active(vault)
        else reentry_session_cap(vault, repository, _nearest_active_goal(vault))
    )
    limit = params.limit
    if reentry_cap is not None:
        limit = reentry_cap if limit is None else min(limit, reentry_cap)
    trace = offer_trace_for(vault, params.session_id)
    queue = build_due_queue(
        vault,
        repository,
        session=SchedulerSession(
            session_id=params.session_id,
            available_minutes=params.available_minutes,
            energy=params.energy,
        ),
        limit=limit,
        offer_trace=trace,
    )
    queue, dtos = publish_offer(ctx, vault, repository, queue, trace=trace, surface="desktop_queue")
    slate = repository.latest_scheduler_slate_by_session(params.session_id) if params.session_id else None
    log_event(
        "scheduler_slate",
        session_id=params.session_id,
        scheduler_slate_id=slate["id"] if slate is not None else None,
        candidate_count=slate["candidate_count"] if slate is not None else len(queue),
        returned_count=slate["returned_count"] if slate is not None else len(queue),
        chosen_policy=slate["selection_policy"] if slate is not None else "selection_reward_v1",
        candidates=[
            {
                "practice_item_id": item.practice_item_id,
                "learning_object_id": item.learning_object_id,
                "priority": item.priority,
                "selection_reward": item.components.get("selection_reward"),
                "predicted_correctness": item.components.get("predicted_correctness"),
                "expected_information_gain": item.components.get("probe_eig"),
            }
            for item in queue
        ],
    )
    # Cold checks the scheduler is withholding because their answer was shown
    # since they were scheduled. They are NOT queue items — they were removed
    # before ranking — so they ride alongside the sections rather than in them,
    # and the surface reports them as waiting rather than offering them.
    deferrals = [
        {
            **row,
            "learning_object_title": (
                learning_object.title
                if (
                    learning_object := vault.learning_objects.get(
                        str(row.get("learning_object_id") or "")
                    )
                )
                is not None
                else row.get("learning_object_id")
            ),
        }
        for row in deferred_cold_followups(vault, repository)
    ]
    return versioned(
        {
            "generated_at": utc_now_iso(),
            "session_id": params.session_id,
            "sections": _sections(dtos),
            "total_items": len(dtos),
            "deferred_cold_checks": deferrals,
            "reentry_refresher_cap": reentry_cap,
        }
    )


def _wait_for_session_diagnoses(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> None:
    """Slice 1 §11: a bounded wait so a fast click still gets the diagnosis.

    When this session has a live diagnosis queued or running, the next-item
    queue build waits up to ``diagnosis.next_item_wait_seconds`` for the
    worker to settle it, then proceeds regardless. The wait is remembered
    for the session; whether the diagnosis was there is recorded when an
    item is actually SERVED (:func:`record_diagnosis_serve`), because a queue
    refresh serves nothing (review F10).
    """

    if not session_id:
        return
    pending = repository.pending_live_diagnoses_for_session(session_id)
    if not pending:
        return
    timeout = float(getattr(getattr(vault.config, "diagnosis", None), "next_item_wait_seconds", 10.0))
    ctx.resume_post_attempt_jobs()
    _remaining, waited = ctx.post_attempt_worker.wait_for(
        lambda: repository.pending_live_diagnoses_for_session(session_id), timeout
    )
    ctx.post_attempt_worker.note_wait(session_id, waited)


def record_diagnosis_serve(ctx: SidecarContext, repository: Any, session_id: str) -> None:
    """E7: one receipt per serve that follows a diagnosis-bearing answer.

    The population is every item served in a session after an attempt whose
    live diagnosis is required, so a serve whose diagnosis already landed (no
    wait at all) counts as served WITH it. ``served_without_diagnosis`` is
    set, and those attempts named, when any required diagnosis is not in
    force at the serve: still queued or running, failed, or skipped for
    budget (review F13). An attempt a regrade left with nothing to explain
    (``not_needed``) is outside the population. Telemetry: a failure here
    never fails the serve.
    """

    try:
        from learnloop.diagnosis.split.jobs import session_diagnosis_availability

        required, unavailable = session_diagnosis_availability(repository, session_id)
        if not required:
            return
        repository.insert_diagnosis_wait_receipt(
            session_id=session_id,
            pending_attempt_ids=unavailable,
            waited_seconds=ctx.post_attempt_worker.take_wait(session_id),
            served_without_diagnosis=bool(unavailable),
        )
    except Exception:  # pragma: no cover - telemetry boundary
        logging.getLogger(__name__).warning("failed to record the E7 serve receipt", exc_info=True)


@method("explain_practice_item", PracticeItemInput)
def explain_practice_item_handler(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    scheduled = explain_practice_item(vault, repository, params.practice_item_id)
    if scheduled is not None:
        return scheduler_explanation_dto(scheduled)
    latest = repository.latest_scheduler_explanation(params.practice_item_id)
    if latest is None:
        raise SidecarError("not_found", f"No scheduler explanation for {params.practice_item_id}.")
    return latest_scheduler_explanation_dto(latest)


@method("open_queue_item", PracticeItemInput)
def open_queue_item(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    """Open one item by id, or refuse with the reason it cannot be rendered.

    Meas §3.A2/§3.A3. ``build_due_queue`` keeps unrenderable instruments out of
    the queue, but this method takes an id, not a queue position: a deep link, a
    restored session, an inspector jump or a stale client all reach an item the
    queue would never have offered. Without the guard the learner gets the
    error-hunt prompt ("correct the worked solution below") with no solution
    under it, answers blind, and the grader — which DOES receive the solution —
    marks every plant missed.

    Refusing with ``not_found`` would be a lie the learner cannot act on: the
    item exists, passed every authoring gate, and is in their vault. So this is a
    distinct typed code carrying the arm and its remedy, and the item id, so the
    surface can say what is missing and the learner can stop looking for a
    mistake they did not make.
    """

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is not None and item.status != "active":
        raise SidecarError(
            "item_retired",
            f"{params.practice_item_id} has been retired and cannot be opened for practice.",
            details={"practice_item_id": params.practice_item_id},
        )
    if item is not None:
        refuse_unservable_item(vault, item)
        refuse_held_out_item(vault, repository, item)
        refuse_unservable_cold_check(vault, repository, item.id)
    refusal = unservable_refusal(item) if item is not None else None
    if refusal is not None:
        raise SidecarError(
            UNSERVABLE_ERROR_CODE,
            f"{params.practice_item_id} cannot be opened yet: {refusal['remedy']}.",
            details=refusal,
        )
    # An unknown id still belongs to `practice_item_detail`'s typed not_found;
    # only a KNOWN-but-unrenderable item takes the branch above.
    return practice_item_detail(vault, repository, params.practice_item_id)


def refuse_unservable_cold_check(vault, repository, practice_item_id: str) -> None:
    """UX Phase 4 round 5: a direct open revalidates a cold check against the
    one coverage the queue and submit read (``scheduler.cold_check_serve_hold``).
    A due cold retry whose answer was shown is deferred here (persisted), so the
    open records no cold administration and the answer is an ordinary one. A
    due one submit would still prime (and so refuse) is refused now, typed,
    rather than after the learner has written an answer."""

    from learnloop.scheduling.scheduler import COLD_CHECK_WOULD_BE_PRIMED, cold_check_serve_hold

    if cold_check_serve_hold(vault, repository, practice_item_id) == COLD_CHECK_WOULD_BE_PRIMED:
        raise SidecarError(
            "cold_check_unavailable",
            "This check can't be taken right now: its answer was shown recently.",
            details={"practice_item_id": practice_item_id},
        )


#: Today's sections in display order. Today focuses (and "Next" opens) the
#: first item of the first non-empty one, which is the offer's served head.
_SECTION_SPECS: tuple[tuple[str, frozenset[str]], ...] = (
    ("Due now", frozenset({"due", "followup"})),
    ("Probe queue", frozenset({"probe"})),
    ("Later today", frozenset({"later"})),
)


def _sections(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections = []
    for title, statuses in _SECTION_SPECS:
        grouped = [item for item in items if item["dueStatus"] in statuses]
        if grouped:
            sections.append({"title": title, "items": grouped})
    return sections


def _served_head(dtos: list[dict[str, Any]]) -> str | None:
    for section in _sections(dtos):
        if section["items"]:
            return section["items"][0]["practiceItemId"]
    return None


# -- Router R1: every published Today offer is a logged decision ---------------


def offer_trace_for(vault: Any, session_id: str | None) -> OfferTrace | None:
    """A trace to fill when this build's offer will be logged, else None.

    An offer without a session records no slate (nothing can be served from it
    under an offer id), so it is not a logged decision.
    """

    if session_id is None or not logging_enabled(vault.config):
        return None
    return OfferTrace()


def today_head_served(vault: Any) -> bool:
    """Whether Today serves the queue's head (router R1's chosen candidate).

    While the legacy queue is Today (below mvp-0.14, or ``plan.enabled =
    false``), Today focuses (and "Next" opens) the first item of its first
    non-empty section: that head is served. While daily-loop DL1's finite plan
    serves Today, this list is the full list one key away from the plan (picks
    from it go through ``plan_learner_pick``), so its builds are logged with no
    chosen candidate (``not_served``) and every bind from it is a learner pick
    (R1 review F3, wired when R1 merged after DL1).
    """

    return not plan_active(vault)


class _TeachBackReadiness:
    """One teach-back readiness probe per published offer, run only if needed.

    The served list's filter and the head rule's counterfactual offers share
    it, so they never disagree and the AI clients are resolved once.
    """

    def __init__(self, ctx: SidecarContext, vault: Any) -> None:
        self._ctx = ctx
        self._vault = vault
        self.value: bool | None = None

    def __call__(self) -> bool:
        if self.value is None:
            self.value = teach_back_offerable(
                self._vault, grading_provider_override=self._ctx.grading_provider_override
            )
        return self.value


class _OfferHeadRule:
    """Which item an offer shows first, for any composed order of the build.

    The same steps that turn a build into the published list: ``limit`` (inside
    the build's composed order), the teach-back readiness filter, the caller's
    removals (a skipped item), then the sections. One ``now``, one read of the
    item states and one readiness probe, shared with the published list.
    """

    def __init__(
        self,
        vault: Any,
        *,
        limit: int | None,
        removed_ids: frozenset[str],
        now: datetime,
        states: Mapping[str, Any],
        teach_back_ready: Callable[[], bool],
    ) -> None:
        self._vault = vault
        self._limit = limit
        self._removed = removed_ids
        self._now = now
        self._states = states
        self._teach_back_ready = teach_back_ready

    def _is_teach_back(self, scheduled: ScheduledItem) -> bool:
        item = self._vault.practice_items.get(scheduled.practice_item_id)
        return item is not None and item.practice_mode == TEACH_BACK_PRACTICE_MODE

    def probe_readiness(self, orders: Any) -> None:
        """Probe readiness once if any of ``orders`` would show a teach-back."""

        for composed in orders:
            items = list(composed)[: self._limit] if self._limit is not None else list(composed)
            if any(self._is_teach_back(item) for item in items):
                self._teach_back_ready()
                return

    def offered(self, composed: Any) -> list[ScheduledItem]:
        items = list(composed)
        if self._limit is not None:
            items = items[: self._limit]
        if any(self._is_teach_back(item) for item in items) and not self._teach_back_ready():
            items = [item for item in items if not self._is_teach_back(item)]
        return [item for item in items if item.practice_item_id not in self._removed]

    def section(self, scheduled: ScheduledItem) -> str:
        state = self._states.get(scheduled.practice_item_id)
        return _due_status(scheduled, state.due_at if state is not None else None, now=self._now)

    def head(self, composed: Any) -> str | None:
        items = self.offered(composed)
        for _title, statuses in _SECTION_SPECS:
            for item in items:
                if self.section(item) in statuses:
                    return item.practice_item_id
        return None


def _in_progress_draft(repository: Any, session_id: str | None) -> dict[str, Any] | None:
    """The session's saved, unsubmitted draft, if any (router R1's "continue")."""

    if session_id is None:
        return None
    checkpoint = repository.fetch_session_checkpoint(session_id)
    if not checkpoint:
        return None
    item_id = checkpoint.get("current_practice_item_id")
    if not item_id or not str(checkpoint.get("current_answer") or "").strip():
        return None
    practice = (checkpoint.get("focus_block_state") or {}).get("practice") or {}
    submission_id = practice.get("submissionId") if isinstance(practice, dict) else None
    if submission_id and repository.practice_attempt_by_submission_id(str(submission_id)) is not None:
        return None
    return {"source": "draft", "practice_item_id": str(item_id), "submission_id": submission_id}


def publish_offer(
    ctx: SidecarContext,
    vault: Any,
    repository: Any,
    queue: list[ScheduledItem],
    *,
    trace: OfferTrace | None,
    surface: str,
    removed_ids: frozenset[str] = frozenset(),
) -> tuple[list[ScheduledItem], list[dict[str, Any]]]:
    """Filter, serialize and publish one Today offer; returns (items, dtos).

    Teach-back items dead-end without their AI provider, so they are dropped
    from the offered queue while it is down; ``removed_ids`` are dropped too (a
    skipped item). The resulting list is what ``finalize_scheduler_offer``
    records as offered, and router R1's decision row commits with that receipt.
    The list, its DTOs and the decision's head rule read the item states once
    and probe teach-back readiness at most once, so the logged decision
    describes exactly the list that was published.
    """

    slate_id = queue[0].scheduler_slate_id if queue else None
    built = list(queue)
    teach_back_ready = _TeachBackReadiness(ctx, vault)
    queue = filter_unready_teach_back_items(vault, queue, offerable=teach_back_ready)
    kept = {item.practice_item_id for item in queue}
    unready = [item.practice_item_id for item in built if item.practice_item_id not in kept]
    if removed_ids:
        queue = [item for item in queue if item.practice_item_id not in removed_ids]
    now = SystemClock().now().astimezone(UTC)
    states = repository.practice_item_states()
    dtos = scheduled_item_dtos(vault, repository, queue, now=now, item_states=states)
    decision = None
    if trace is not None and trace.slate_id is not None:
        try:
            head_served = today_head_served(vault)
            head_rule = _OfferHeadRule(
                vault, limit=trace.limit, removed_ids=removed_ids, now=now, states=states,
                teach_back_ready=teach_back_ready,
            )
            # Readiness is a decision input: probe it now if any order the
            # exploration could compose would show a teach-back.
            head_rule.probe_readiness([outcome.composed for outcome in trace.outcomes])
            decision = build_today_offer_decision(
                trace,
                offered=queue,
                head_of=head_rule.head,
                section_of=head_rule.section,
                served_head=_served_head(dtos),
                surface=surface if head_served else "full_list",
                policy=SELECTION_POLICY,
                in_progress=_in_progress_draft(repository, trace.session_id),
                removed={
                    "teach_back_provider_unready": unready,
                    "skipped_by_learner": sorted(removed_ids),
                },
                inputs={"teach_back_ready": teach_back_ready.value},
                head_served=head_served,
            )
        except Exception:  # logging never fails the offer
            logging.getLogger(__name__).warning(
                "router R1: offer decision for slate %s not logged", trace.slate_id, exc_info=True
            )
            decision = None
    if slate_id is not None:
        repository.finalize_scheduler_offer(
            slate_id,
            [item.scheduler_candidate_id for item in queue if item.scheduler_candidate_id],
            entry_surface="desktop_queue",
            router_decision=decision,
        )
    elif decision is not None:
        # Nothing was published (an empty offer): the stop is still a decision.
        try:
            record_decision(repository, decision)
        except Exception:  # pragma: no cover - logging never fails the offer
            logging.getLogger(__name__).warning(
                "router R1: empty-offer decision for slate %s not logged", trace.slate_id if trace else None,
                exc_info=True,
            )
    return queue, dtos
