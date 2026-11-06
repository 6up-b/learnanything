"""Teacher TE1 RPCs: a lesson (spec_teacher_v1 §6, §17, §19).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``lesson.turn``: every model-calling step of a lesson, ONE origin action (T1
  redesign D): ``open`` (an LO's or a Reader selection's "Teach me this"),
  ``reply``, ``answer_prediction``, ``answer_check`` (graded inline by the blind
  grader, under the same grant), ``stop`` and ``resume`` (run the teacher's turn an
  outage interrupted; an error after the lesson is saved carries its ``lesson_id``). With the ChatGPT plan down the
  error carries T1's standard offer; "Use OpenRouter instead" grants
  ``lesson.turn`` for this session and vault, so it covers the whole lesson (and
  no offer is made until ``teacher.metered_price_per_million`` is set).
* ``lesson.view``: the lesson as the screen shows it (no model call; it first runs
  what an interrupted action left of its last accepted teacher turn).

Kill switch ``teacher.enabled`` (and the vault below the teacher's successor):
both RPCs refuse, no lesson opens, nothing is written.

Teacher TE1b (spec_teacher_v1 §15.1, §19; ``learnloop.daily_plan.lesson_suggestion``):

* ``lesson.suggestion``: Today's suggestion card (no model call). The day's
  first call draws the day's decision and writes it; later calls read it back.
  ``null`` when there is no card (none today, already answered, or switched
  off: ``router.lesson_suggestions.enabled``, the router, its decision log or
  lessons off, or the vault below TE1b's tag; then nothing is written).
* ``lesson.suggestion_respond``: Start (``accepted``), an alternative
  (``chose_alternative``) or "Not now" (``declined``), appended once to
  ``router_suggestion_responses``. Start returns the lesson to open:
  ``lesson.turn`` ``open`` with ``origin = "router_suggestion"``, the decision id
  and the lesson id the response recorded.
  On a pending card (a Start whose lesson never opened) "Not now" is
  ``released``: the reservation is let go, the Start staying recorded.

Teacher TE2-log (spec_teacher_v1 §11.6): ``lesson.activity`` appends the lesson
screen's activity intervals (start and end on the client's clock, foreground with
input or not, the client's ``occurred_at`` and the sidecar's ``received_at``) to
``lesson_activity_intervals``; a resent interval writes nothing. No model call; with
``teacher.episode_log`` off it writes nothing. The view carries ``activity_log: true``
only while the switch is on, so the screen sends nothing otherwise.

Reader RW5d P4b: a teacher turn's ``visual`` is built inside ``lesson.turn`` by the
figure service (``learnloop.figures.service.build_figure``, origin ``teacher``,
the author route and live configuration the Reader's builds use), grammar and
sketch tiers only (no rich job is spawned from a lesson), so the lesson's grant
covers it and the lesson's spend envelope admits its requests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import Field

from learnloop.teacher import service as S
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import (
    MANUAL_PROVIDER,
    grading_source_for_provider,
    provider_label,
    ready_grading_provider,
)
from learnloop_sidecar.registry import method

#: Every TE1/TE1b RPC this module registers (pinned desktop-only in tests/test_mobile_allowlist.py).
LESSON_RPCS: tuple[str, ...] = ("lesson.turn", "lesson.view", "lesson.suggestion", "lesson.suggestion_respond")
#: Teacher TE2-log's RPC (desktop only; pinned in tests/test_teacher_te2log_activity.py; the blanket denial of
#: tests/test_mobile_allowlist.py covers it).
LESSON_ACTIVITY_RPCS: tuple[str, ...] = ("lesson.activity",)
#: Teacher TE2's RPCs (desktop only; pinned in tests/test_teacher_te2_sidecar.py; the blanket denial of
#: tests/test_mobile_allowlist.py covers them): the typed goal's resolution, and Today's open lessons.
LESSON_TE2_RPCS: tuple[str, ...] = ("lesson.goal", "lesson.open_lessons")


class LessonSelection(ParamsModel):
    extraction_id: str
    span_ids: list[str]


class LessonTurnInput(ParamsModel):
    # TE2: answer_probe (the open question), teach_anyway (one being prepared), close (Today's "Close it").
    action: Literal["open", "reply", "answer_prediction", "answer_check", "stop", "resume", "answer_probe",
                    "teach_anyway", "close"]
    lesson_id: str | None = None
    # open (TE2: typed_goal, its accepted new topics' phrases and their subject)
    entry: Literal["learning_object", "reader_selection", "new_topic", "typed_goal"] | None = None
    learning_object_ids: list[str] = []
    selection: LessonSelection | None = None
    goal_text: str | None = None
    add_topics: list[str] = Field(default_factory=list, max_length=12)
    subject_id: str | None = None
    probe_ref: str | None = None
    # TE1b: a router suggestion's Start (the decision; ``lesson_id`` is the id its response recorded)
    origin: Literal["learner_pick", "router_suggestion"] = "learner_pick"
    suggestion_decision_id: str | None = None
    # reply / answers
    text: str | None = None
    answer: str | None = None
    check_ref: str | None = None
    tap: int | None = None
    thinking: str | None = None


class LessonViewInput(ParamsModel):
    lesson_id: str


class LessonGoalInput(ParamsModel):
    """TE2 (§11.5): the typed goal to resolve (C0b's resolver; no lesson is written)."""

    text: str = Field(min_length=1, max_length=6000)


class LessonOpenLessonsInput(ParamsModel):
    pass


class LessonActivityInterval(ParamsModel):
    """One interval of the lesson screen (TE2-log, spec §11.6): on the client's clock, foreground with input or not."""

    screen_session: str = Field(min_length=1, max_length=80)
    seq: int = Field(ge=1)
    started_at: str
    ended_at: str
    foreground: bool


class LessonActivityInput(ParamsModel):
    lesson_id: str
    intervals: list[LessonActivityInterval] = Field(default_factory=list, max_length=500)
    #: When the client sent the batch (RO0 row 5's occurred_at; received_at is the sidecar's).
    occurred_at: str | None = None


@dataclass
class _RouteUnavailable(SidecarError):
    """The teacher's route is not ready; :func:`lesson_turn` words it by whether the lesson exists yet."""

    label: str = ""


def route_unavailable_message(label: str, *, saved: bool) -> str:
    """The unavailable route's line, true to what exists (followups batch 5, C: an opening that failed
    before its lesson was saved said "your lesson is saved")."""

    if saved:
        return f"{label} is unavailable for lessons; your lesson is saved and resumes when it's back."
    return f"{label} is unavailable for lessons, so the lesson didn't start and nothing was saved; try again when it's back."


class LessonSuggestionInput(ParamsModel):
    session_id: str | None = None


class LessonSuggestionRespondInput(ParamsModel):
    decision_id: str
    # ``released``: "Not now" on a pending card (a Start whose lesson never opened; landing ruling R2)
    response: Literal["accepted", "chose_alternative", "declined", "released"]
    candidate_ref: str | None = None
    session_id: str | None = None


def _error(exc: S.LessonError) -> SidecarError:
    retryable = exc.code in ("plan_unavailable", "teacher_unavailable", "grading_unavailable")
    # ``lesson_id`` once the lesson is saved (review F11): the screen resumes it, never opens another.
    return SidecarError(exc.code, str(exc), retryable=retryable, details=dict(exc.details))


def _figure_builder(ctx: SidecarContext, vault: Any, repository: Any) -> Any:
    """Reader RW5d P4b: how a lesson builds its teacher's visual (inline: the turn waits on it)."""

    def build(request: Any) -> Any:
        from learnloop.figures import service as FS

        # Every request is admitted against the vault loaded NOW (the build's FiguresGate); no rich
        # spawner: a lesson host is grammar and sketch only (FS.LESSON_TIERS).
        return FS.build_figure(vault, repository, request, author_client=getattr(ctx, "figure_author_client", None),
                               live_vault=getattr(ctx, "loaded_vault", None),
                               find=getattr(ctx, "figure_find_sources", None),
                               spawn_rich=None)

    return build


def _clients(ctx: SidecarContext, vault: Any) -> S.Clients:
    from learnloop.ai.routing import ready_client_for_task

    def teacher() -> Any:
        provider_name, runtime, client = ready_client_for_task(vault.root, vault.config, "teacher")
        if not runtime.ready or client is None:
            label = provider_label(provider_name)
            raise _RouteUnavailable("plan_unavailable", f"{label} is unavailable for lessons.", retryable=True,
                                    label=label)
        return client

    clients: S.Clients

    def grading() -> Any:
        if ctx.grading_provider_override == MANUAL_PROVIDER:
            raise SidecarError("provider_unavailable", "Lesson checks need a grader (grading is set to manual).")
        provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
        if not runtime.ready or client is None:
            raise SidecarError("provider_unavailable", f"{provider_label(provider_name)} is unavailable for grading.",
                               retryable=True)
        clients.grading_source = grading_source_for_provider(provider_name)
        return client

    clients = S.Clients(teacher=teacher, grading=grading)
    return clients


@method("lesson.turn", LessonTurnInput)
def lesson_turn(ctx: SidecarContext, params: LessonTurnInput) -> dict[str, Any]:
    """One step of a lesson; see the module docstring."""

    vault, repository = ctx.require_vault()
    try:
        S.require_active(vault)
        clients = _clients(ctx, vault)
        if clients.figures is None:
            # Reader RW5d P4b: the teacher's visuals are built here, inline.
            clients.figures = _figure_builder(ctx, vault, repository)
        if params.action == "open":
            if params.entry is None:
                raise SidecarError("validation_error", "A lesson needs an entry (a topic or a passage).")
            suggested = params.origin == "router_suggestion"
            result = S.open_lesson(
                vault, repository, entry=params.entry, learning_object_ids=params.learning_object_ids,
                selection=params.selection.model_dump() if params.selection is not None else None,
                goal_text=params.goal_text, clients=clients,
                origin="router" if suggested else "learner_pick",
                origin_ref=params.suggestion_decision_id if suggested else None,
                lesson_id=params.lesson_id if suggested else None,
                add_topics=params.add_topics, subject_id=params.subject_id)
        else:
            if not params.lesson_id:
                raise SidecarError("validation_error", "lesson_id is required.")
            payload = {"text": params.text, "answer": params.answer, "check_ref": params.check_ref,
                       "tap": params.tap, "thinking": params.thinking, "probe_ref": params.probe_ref}
            result = S.take_turn(vault, repository, lesson_id=params.lesson_id, action=params.action, payload=payload,
                            clients=clients)
    except S.LessonError as exc:
        raise _error(exc) from exc
    except _RouteUnavailable as exc:
        # Saved: a step of an existing lesson, or an opening that failed after its lesson was written (its
        # error carries the id). An opening resolves its route before writing anything.
        saved = params.action != "open" or bool(exc.details.get("lesson_id"))
        raise SidecarError(exc.code, route_unavailable_message(exc.label, saved=saved), retryable=True,
                           details=dict(exc.details)) from exc
    if result.get("vault_changed") or (params.action == "open" and params.entry == "typed_goal"):
        ctx.reload(maintenance=False)
    if result.get("te2"):
        # TE2: a probe's generation or a gap's reading may have been queued: the worker drains it now.
        worker = getattr(ctx, "post_attempt_worker", None)
        if worker is not None:
            worker.notify()
    lesson_id = result.get("lesson_id") or params.lesson_id
    if lesson_id and result.get("plan"):
        # RW5d P5 (spec §10b.2, §10.4): the plan's nodes not yet reached, and
        # the open gaps on the lesson's topics, ahead of need (quiet, not the
        # lesson's grant; a no-op with figures.prefetch_enabled off).
        from learnloop_sidecar.prefetch_runtime import notify

        notify(ctx, "lesson", str(lesson_id), learner_activity=True)
        notify(ctx, "gap", f"lesson:{lesson_id}", learner_activity=True)
    return versioned(result)


@method("lesson.view", LessonViewInput)
def lesson_view(ctx: SidecarContext, params: LessonViewInput) -> dict[str, Any]:
    """The lesson as the screen shows it (no model call)."""

    vault, repository = ctx.require_vault()
    try:
        S.require_active(vault)
        return versioned(S.view_lesson(vault, repository, params.lesson_id))
    except S.LessonError as exc:
        raise _error(exc) from exc


@method("lesson.goal", LessonGoalInput)
def lesson_goal(ctx: SidecarContext, params: LessonGoalInput) -> dict[str, Any]:
    """Teacher TE2 (§11.5): a typed goal resolved by C0b's resolver (one plan call; none when the same words over
    the same topics were resolved before): the topics it needs, each with the phrase it answers, and what nothing
    matched with a proposed topic. Nothing is written but the resolution and its ledger verdict."""

    from learnloop.teacher import te2 as T2
    from learnloop.teacher import topics as TP

    vault, repository = ctx.require_vault()
    try:
        S.require_active(vault)
        if not T2.on(vault):
            raise SidecarError("teacher_unavailable", "Typing a goal needs this vault upgraded (learnloop upgrade).")
        return versioned(TP.resolve(vault, repository, params.text))
    except S.LessonError as exc:
        raise _error(exc) from exc
    except TP.TopicsRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc


@method("lesson.open_lessons", LessonOpenLessonsInput)
def lesson_open_lessons(ctx: SidecarContext, params: LessonOpenLessonsInput) -> dict[str, Any]:
    """Teacher TE2 (§11.8): Today's *Continue your lesson on X* (no model call; empty unless TE2 serves)."""

    vault, repository = ctx.require_vault()
    return versioned({"lessons": S.open_lessons(vault, repository)})


@method("lesson.activity", LessonActivityInput)
def lesson_activity(ctx: SidecarContext, params: LessonActivityInput) -> dict[str, Any]:
    """Teacher TE2-log (spec §11.6): append the lesson screen's activity intervals (no model call, never evidence,
    never a decision). ``teacher.episode_log`` off: nothing is written (``enabled: false``)."""

    from learnloop.clock import utc_now_iso
    from learnloop.teacher import episodes as E

    vault, repository = ctx.require_vault()
    try:
        return versioned(E.record_intervals(
            vault, repository, lesson_id=params.lesson_id,
            intervals=[interval.model_dump() for interval in params.intervals], occurred_at=params.occurred_at,
            received_at=utc_now_iso()))
    except E.ActivityRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc


@method("lesson.suggestion", LessonSuggestionInput)
def lesson_suggestion(ctx: SidecarContext, params: LessonSuggestionInput) -> dict[str, Any]:
    """Today's suggestion card, or ``null`` (TE1b; no model call)."""

    from learnloop.daily_plan.lesson_suggestion import today_suggestion

    vault, repository = ctx.require_vault()
    return versioned({"suggestion": today_suggestion(vault, repository, session_id=params.session_id)})


@method("lesson.suggestion_respond", LessonSuggestionRespondInput)
def lesson_suggestion_respond(ctx: SidecarContext, params: LessonSuggestionRespondInput) -> dict[str, Any]:
    """The learner's one response to the card (TE1b); a Start returns the lesson to open."""

    from learnloop.daily_plan.lesson_suggestion import SuggestionError, respond

    vault, repository = ctx.require_vault()
    # Mobile v2 §5.6: a response bound to a session another device now holds is refused.
    from learnloop_sidecar.handlers.sessions import refuse_moved_session

    refuse_moved_session(ctx, repository, params.session_id)
    try:
        result = respond(vault, repository, decision_id=params.decision_id, response=params.response,
                         candidate_ref=params.candidate_ref, session_id=params.session_id)
    except SuggestionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(result)
