"""Daily-loop DL1 RPCs: the finite plan (``spec_daily_loop_v1.md`` §6, §7, §12).

``get_daily_plan``, ``set_plan_minutes``, ``next_plan_item``,
``plan_reading_ended``, ``plan_keep_going``, ``plan_more_new``,
``plan_learner_pick``, ``get_today_headline``, ``plan_prefetch`` and IH3's ``plan_something_else_options`` and
``plan_something_else``. While the plan is off (a
pre-``mvp-0.14`` vault or ``plan.enabled = false``) every one of them answers
``enabled: false`` without building a queue or writing a row, and Today, Start
and ``get_today_queue`` are mvp-0.13's (G1).

**The phone** (mobile v2 §2.2, owner decision D1, reversing M2a's "the phone shows the queue"):
the same stored plan serves both devices, and the phone's door filters at the step
(``PlanStepFilter``): the build, the router's support and every desktop reply are unchanged, and
with no request origin nothing here differs from before. A phone request's boundary decisions
record the surface ``phone_plan`` and the device rules they served under. Plan writes that name a
session check its owner (§5.6, :func:`refuse_moved_session`), and check it again inside every
transaction they commit (:class:`OwnerCheckedRepository`); a phone's write that names no open
session is refused while another device owns one; reads never check. A by-id pick refuses what the
phone's step filter holds (:func:`_refuse_held_pick`). The host's
secondary attach runs none of the plan's background work (D6): the deliverable refresh, AD's
preparation and the figure prefetch stay the desktop's.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
import logging
from dataclasses import replace as dataclass_replace
from typing import Any, Literal

from pydantic import Field

from learnloop.daily_plan.engine import (
    PlanEnv,
    PlanInactiveError,
    PlanStillOpenError,
    advance_with_context,
    keep_going,
    learner_pick,
    more_new,
    picked_under,
    plan_active,
    plan_scheduler_session,
    prefetch_boundary,
    reading_ended,
    set_minutes,
    stop_today,
)
from learnloop.daily_plan.headline import today_headline
from learnloop.daily_plan.policy import policy_for, prefetch_can_start
from learnloop.daily_plan.engine import intent_view
from learnloop.daily_plan.reentry import ReentryGap, reentry_panel
from learnloop.daily_plan.view import disabled_view, plan_view
from learnloop.scheduling.scheduler import build_due_queue, read_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.goals import _nearest_active_goal
from learnloop_sidecar.handlers.queue import prepare_queue_build
from learnloop_sidecar.handlers.sessions import refuse_moved_session
from learnloop_sidecar.request_origin import host_mutation
from learnloop_sidecar.handlers.teach_back import filter_unready_teach_back_items
from learnloop_sidecar.registry import method

#: The DL1 RPCs (phone-allowed from mobile v2 stage V2, tests/test_mobile_allowlist.py).
DAILY_PLAN_RPCS = (
    "get_daily_plan",
    "set_plan_minutes",
    "next_plan_item",
    "plan_reading_ended",
    "plan_keep_going",
    "plan_more_new",
    "plan_learner_pick",
    "get_today_headline",
    "plan_prefetch",
    "plan_something_else_options",
    "plan_something_else",
)


class PlanSessionInput(ParamsModel):
    session_id: str | None = None


class NextPlanItemInput(ParamsModel):
    session_id: str | None = None
    #: Record the step as served (the learner opened it). Without it this is
    #: the prefetch made while feedback shows (§6.5).
    serve: bool = False
    skip_practice_item_id: str | None = None


class PlanPrefetchInput(ParamsModel):
    session_id: str


class PlanSomethingElseOptionsInput(ParamsModel):
    session_id: str | None = None


class PlanSomethingElseInput(ParamsModel):
    """IH3: the learner's choice at "Something else would help". ``preference_id`` is the act's own key: the same id
    sent again (a retry) is answered as it was made and writes nothing."""

    kind: Literal["question", "review", "new", "read", "lesson", "stop"]
    ref: str | None = Field(default=None, max_length=300)
    surface: str = Field(max_length=40)
    attempt_id: str | None = Field(default=None, max_length=100)
    note_md: str | None = Field(default=None, max_length=4000)
    preference_id: str | None = Field(default=None, max_length=100)
    session_id: str | None = None


class OfferShownInput(ParamsModel):
    block_id: str
    #: "today" (the card) or "offer_page" (the page feedback's Next opens).
    surface: str
    session_id: str | None = None


class PlanMinutesInput(ParamsModel):
    minutes: int
    session_id: str | None = None


class PlanReadingEndedInput(ParamsModel):
    outcome: Literal["left_reader", "skipped", "section_completed"]
    session_id: str | None = None


class PlanKeepGoingInput(ParamsModel):
    session_id: str | None = None
    #: "Done" on the plan: stop for today instead of extending it.
    stop: bool = False


class PlanMoreNewInput(ParamsModel):
    session_id: str | None = None
    #: Without it only the trade-off is returned ("adds about N min/day").
    confirm: bool = False


class PlanLearnerPickInput(ParamsModel):
    practice_item_id: str
    session_id: str | None = None
    #: The offer the learner picked it from: the full list's own candidate id
    #: (``get_today_queue`` published that list as shown). Without it the pick
    #: is served with the plan build's candidate for the item.
    scheduler_candidate_id: str | None = None
    #: A ``find_practice`` proposal the learner picked this item from (canonical
    #: sources S0): the pick appends the proposal's ``practised`` usage signal.
    proposal_id: str | None = None
    #: The ``import_source_exercise`` import that wrote this item from a
    #: proposed textbook exercise (with ``proposal_id``): serving it delivers
    #: that exercise.
    source_exercise_import_id: str | None = None
    #: Reader RW4b fix round 5 (R1): a caller that may retry the same pick (a
    #: picked exercise's admission) names it; the pick's receipt keeps it, and
    #: a pick already made under it is returned as made, recording nothing again.
    idempotency_key: str | None = Field(default=None, max_length=200)


def _env(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None, *, serve: bool = False,
         prefetch: bool = False) -> PlanEnv:
    """``prefetch``: the phone's (:func:`plan_prefetch`): ``repository`` is read-only, the build persists nothing and
    the chooser only starts its job."""

    def eligible(minutes: float) -> list[Any]:
        # Today's own build: the same scheduler call and teach-back filter as
        # get_today_queue, so a served plan item carries the candidate id of
        # the slate that ranked it. No offer is finalized: the learner sees one
        # block, not this list, so publishing it as "offered" (as the full
        # list does when it is shown) would be a false offer set for the field
        # and router logging (review F5). The plan's own item_served receipt
        # records what was served. Where the router composes Today the list is
        # the scheduler's greedy order, without its seeded exploration
        # (plan_scheduler_session: staged plans are deterministic). The prefetch
        # reads on a read-only attach, where any write of the build would fail.
        queue = (read_due_queue if prefetch else build_due_queue)(
            vault,
            repository,
            session=plan_scheduler_session(vault, session_id, minutes),
            limit=None,
        )
        return filter_unready_teach_back_items(
            vault, queue, grading_provider_override=ctx.grading_provider_override
        )

    # Router R2a: the staged frame composes Today at mvp-0.23 with the router
    # on; otherwise DL1's pair exactly (daily_plan.policy, G8). Router R2b: at
    # the mixture's successor the models are asked off the hot path; a read
    # (``serve`` false) never waits on them, a serving step waits a few seconds.
    return PlanEnv(
        vault=vault,
        repository=repository,
        session_id=session_id,
        eligible=eligible,
        policy=policy_for(vault, repository, session_id=session_id, serve=serve, start_only=prefetch),
        device=_step_filter(ctx, vault, repository, session_id),
    )


def _step_filter(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> Any:
    """Mobile v2 §2.2: the requesting device's step filter, from the request's origin (never a
    parameter); None for the desktop. The PR-6 rules, the diagnostic check this session left for
    the desktop, and a generated follow-up probe the phone may not open: every one below V3 (or
    with ``phone_probes`` off), and from V3 on (owner decision D3) one already served on the
    desktop, whose single administration is the desktop's."""

    if ctx.request_origin is None:
        return None
    from learnloop.followup_serve import identity
    from learnloop.followup_serve.gates import PHONE_SURFACE
    from learnloop.scheduling.device_eligibility import PlanStepFilter
    from learnloop_sidecar.request_origin import phone_probes_on, plan_surface
    from learnloop_sidecar.serving import device_filter, device_policy

    if phone_probes_on(ctx.request_origin, vault.config):
        def generated_probe(practice_item_id: str) -> bool:
            return identity.served_elsewhere(repository, practice_item_id, PHONE_SURFACE)
    else:
        def generated_probe(practice_item_id: str) -> bool:
            return identity.is_generated_probe(repository, practice_item_id)

    return PlanStepFilter(
        device_filter=device_filter(ctx.request_origin, vault, repository, session_id),
        surface=plan_surface(ctx.request_origin),
        device_policy=device_policy(vault, ctx.request_origin),
        generated_probe=generated_probe,
        reading=phone_reading_check(ctx, vault, repository),
    )


def phone_reading_check(ctx: SidecarContext, vault: Any, repository: Any) -> Any:
    """Mobile v2 V4: which of the plan's reading blocks the phone's Reader takes (the host's ``phone_reader``),
    or None (V3's phone, which leaves every reading for the desktop). A block is the phone's when its book opens
    in the phone's Reader: the Reader on, the source not opted out of it, and nothing of its section withheld
    from the phone (``phone_reader.phone_withheld``). Anything that can't be read leaves it for the desktop."""

    from learnloop_sidecar.request_origin import phone_reader_on

    if not phone_reader_on(ctx.request_origin):
        return None

    def check(reading: Mapping[str, Any]) -> bool:
        try:
            return _phone_reading_eligible(vault, repository, reading)
        except Exception:  # noqa: BLE001 - fail closed: the desktop shows it
            logging.getLogger(__name__).warning("phone reading eligibility unreadable", exc_info=True)
            return False

    return check


def _phone_reading_eligible(vault: Any, repository: Any, reading: Mapping[str, Any]) -> bool:
    from learnloop.reader import reader_dialogue as RD
    from learnloop.section_map import extraction_sections
    from learnloop_sidecar.phone_reader import phone_withheld

    extraction_id = str(reading.get("extraction_id") or "")
    section_id = str(reading.get("section_id") or "")
    if not extraction_id or not section_id or not RD.reader_enabled(vault):
        return False
    run = repository.get_extraction_run(extraction_id)
    if run is None or run.get("status") != "completed":
        return False
    revision = repository.get_source_revision(run["revision_id"]) if run.get("revision_id") else None
    artifact = repository.get_source_artifact(revision["source_id"]) if revision else None
    if artifact is None or not artifact.get("reader_enabled", 1):
        return False
    ir = repository.load_document_ir(extraction_id)
    section = next((row for row in (extraction_sections(ir)[0] if ir is not None else []) if row["id"] == section_id),
                   None)
    if section is None:
        return False
    withheld = phone_withheld(vault, repository, extraction_id, section["span_ids"])
    return not withheld.whole and not withheld.spans


def _require(ctx: SidecarContext, session_id: str | None, *, serve: bool = False,
             writes: bool = False) -> tuple[Any, Any, PlanEnv] | None:
    """``writes``: the call is a plan write naming a session, so the session's owner is checked
    first (mobile v2 §5.6). A read never checks."""

    vault, repository = ctx.require_vault()
    if not plan_active(vault):
        return None
    check = refuse_moved_session(ctx, repository, session_id) if writes else None
    if not _secondary(ctx):
        # Curriculum C1 (spec §7.6): the daily quiet re-judgment of the nearest
        # deliverable's stale path starts before the plan is built (background,
        # once a day; nothing here waits on it). Never on the phone host's
        # secondary attach (mobile v2 D6): a background spender is the desktop's.
        from learnloop_sidecar.handlers.deliverables import refresh_for_plan

        refresh_for_plan(ctx, vault, repository)
    prepare_queue_build(ctx, vault, repository, session_id)
    env = _env(ctx, vault, repository, session_id, serve=serve)
    if check is not None:
        # Codex review of V2, F6: the owner checked above is checked again inside every transaction
        # the step commits, so a handoff during its slow work (the queue build, a boundary's model
        # call) refuses the step instead of committing it for the device that lost the session.
        # Only the plan's own writes: the policy's background work keeps the plain repository.
        env = dataclass_replace(env, repository=OwnerCheckedRepository(repository, check))
    return vault, env.repository, env


class OwnerCheckedRepository:
    """The repository a session's plan write commits through (mobile v2 §5.6; Codex review of V2,
    F6): each transaction it begins runs the session's ownership check first, under the write lock it
    has just taken, so no adopt can commit between the check and the step's rows. A nested
    ``atomic()`` is a savepoint of a transaction already checked (and may run under AD's read guard),
    so it checks nothing. Everything else is the repository's own. Nothing changes while the session
    stays where it was."""

    def __init__(self, repository: Any, check: Callable[[], None]) -> None:
        self._repository = repository
        self._check = check

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repository, name)

    @property
    def base(self) -> Any:
        return self._repository

    @contextmanager
    def atomic(self) -> Iterator[None]:
        begins = not self._repository.in_atomic()
        with self._repository.atomic():
            if begins:
                self._check()
            yield


def _secondary(ctx: SidecarContext) -> bool:
    """The phone host's attach (``load_secondary``): it runs only the phone's own work (D6)."""

    return bool(getattr(ctx, "secondary", False))


def _off(ctx: SidecarContext) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    # The plan is off only by its switch: every tag a vault opens at serves it.
    return versioned(disabled_view(vault, reason="plan_disabled"))


def _view(env: PlanEnv, record: Any, step: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    panel = None
    if record.kind == "reentry":
        # The break as measured when the re-entry plan was built: practising
        # inside it must not shrink the "welcome back" it opened with.
        stored = record.split.get("reentry_gap") or {}
        gap = ReentryGap(
            due=True,
            gap_days=int(stored.get("gap_days") or 0),
            threshold_days=int(stored.get("threshold_days") or env.vault.config.hypothesis.reentry_gap_days),
            last_activity_at=stored.get("last_activity_at"),
        )
        panel = reentry_panel(
            env.vault,
            env.repository,
            now=env.now(),
            gap=gap,
            goal=_nearest_active_goal(env.vault),
            intent=intent_view(env),
        ).as_dict()
        panel["minutes"] = round(record.budget, 4)
        panel["items_cap"] = record.split.get("items_cap")
        panel["planned_items"] = record.item_count()
        panel["planned_minutes"] = round(record.minutes_planned(), 4)
    view = plan_view(
        env,
        record,
        context=context,
        next_step=step,
        reentry_panel=panel,
        streak=env.repository.session_day_streak(),
    )
    return {**view, **_router_decision_line(env, record, step), **_preference_line(env)}


def _preference_line(env: PlanEnv) -> dict[str, Any]:
    """IH3: ``somethingElse`` says the quiet link may show. Absent with the switch off or below the tag, so the reply
    is the predecessor's exactly."""

    from learnloop.daily_plan import learner_action

    return {"something_else": True} if learner_action.enabled(env) else {}


def _router_decision_line(env: PlanEnv, record: Any, step: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """FG1 §6.4: the router's decision on the block in hand, for debugging and calibration.
    Absent with the switch or ``ui.show_router_decisions`` off, so the reply stays as it was.
    A device's block in hand is its step's (mobile v2 §2.2, J4)."""

    from learnloop.followup_serve.gates import generate_and_serve_on

    if not generate_and_serve_on(env.vault.config):
        return {}
    from learnloop.followup_run.decision_view import decision_view, show_router_decisions

    if not show_router_decisions(env.vault):
        return {}
    if env.device is not None:
        from learnloop.daily_plan.view import device_current

        current = device_current(record, step)
    else:
        current = record.current_block()
    decision = decision_view(env.repository, current.decision_ref) if current is not None else None
    return {"routerDecision": to_camel(decision)} if decision is not None else {}


def _current_view(env: PlanEnv) -> dict[str, Any]:
    record, step, context = advance_with_context(env, serve=False)
    return _view(env, record, step, context)


@method("get_daily_plan", PlanSessionInput)
def get_daily_plan(ctx: SidecarContext, params: PlanSessionInput) -> dict[str, Any]:
    """Today's plan (built on first read of the day), its split, blocks and next step."""

    required = _require(ctx, params.session_id)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    view = _current_view(env)
    _schedule_ad(ctx, env, step=None)
    _schedule_prefetch(ctx, env)
    return versioned(view)


def _schedule_prefetch(ctx: SidecarContext, env: PlanEnv) -> None:
    """RW5d P5 (spec §10b.2): the stored plan's reading section and the open gaps on its
    topics are figure triggers. The plan never calls into figures: the trigger reads the
    stored plan afterwards, in the background; a no-op with figures.prefetch_enabled off. A read,
    not the learner's action (the app's queue-revision poll refetches it when background work
    lands): these passes don't carry ``learner_activity``."""

    from learnloop_sidecar.prefetch_runtime import notify, runs_here

    if not runs_here(ctx):
        return
    try:
        from learnloop.daily_plan.engine import latest_today

        record = latest_today(env)
        if record is not None:
            notify(ctx, "plan", str(record.id))
            notify(ctx, "gap", f"plan:{record.id}")
    except Exception:  # noqa: BLE001 - background scheduling never reaches the plan
        import logging

        logging.getLogger(__name__).warning("figure prefetch not scheduled", exc_info=True)


def _schedule_ad(ctx: SidecarContext, env: PlanEnv, *, step: Mapping[str, Any] | None) -> None:
    """Adaptive difficulty AD1 (spec §8.2, §7.2): after the response is built,
    the planned items' revisions are prepared for the pool in the background
    (feature audit, then ``llm_v1:item``), and a served step's presentation
    gets its ``llm_v3`` forecasts. Never waits, fails or changes the step."""

    if _secondary(ctx):
        # Mobile v2 D6: the phone host runs only the phone's own work; AD's preparation, its
        # forecasts and a commission's generation stay the desktop's (they read the plan later).
        return
    try:
        from learnloop.adaptive_difficulty.background import (
            schedule_item_preparation,
            schedule_presentation_forecasts,
        )
        from learnloop.adaptive_difficulty.switches import any_background_work

        vault = env.vault
        # AD2+AD3 (§6.1, Codex review F5): a serve-time commission's generation, queued once
        # on the vault's durable job queue (read, too, on a plan read: the recovery path).
        from learnloop.adaptive_difficulty.generation import schedule_commission_generation

        # The plain repository: background work is no step of the session's (F6's check is the step's).
        schedule_commission_generation(vault, getattr(env.repository, "base", env.repository),
                                       _commission_enqueue(ctx))
        if not any_background_work(vault.config):
            return
        clients = getattr(ctx, "ad_clients", None)
        builds = getattr(ctx, "map_builds", None)
        # The vault loaded at each check, not this request's (fix round 4, V1).
        live_vault = getattr(ctx, "loaded_vault", None)
        sqlite_path = env.repository.sqlite_path
        presentation_id = (step or {}).get("presentation_id")
        if presentation_id:
            schedule_presentation_forecasts(vault, sqlite_path, str(presentation_id), clients=clients, builds=builds,
                                            live_vault=live_vault)
        from learnloop.daily_plan.engine import latest_today

        record = latest_today(env)
        if record is not None:
            planned = [item.practice_item_id for item in record.items() if not item.resolved]
            schedule_item_preparation(vault, sqlite_path, planned, clients=clients, builds=builds,
                                      live_vault=live_vault)
    except Exception:  # noqa: BLE001 - background scheduling never reaches the plan
        logging.getLogger(__name__).warning("AD1 background work not scheduled", exc_info=True)


def _commission_enqueue(ctx: SidecarContext) -> Any:
    """How a commission's generation is queued: a test's injected callable, else the vault's
    durable ingest queue, and nothing with ``LEARNLOOP_AD_MODELS=off`` (the suite, a copy run)."""

    injected = getattr(ctx, "ad_commission_enqueue", None)
    if injected is not None:
        return injected
    from learnloop.adaptive_difficulty.spend import models_off

    if models_off():
        return None

    def enqueue(commission_id: str, learning_object_id: str) -> str:
        return ctx.ingest_jobs.enqueue_practice_expansion(
            learning_object_ids=[learning_object_id], ad_commission_id=commission_id,
        )

    return enqueue


@method("set_plan_minutes", PlanMinutesInput)
@host_mutation
def set_plan_minutes(ctx: SidecarContext, params: PlanMinutesInput) -> dict[str, Any]:
    """A minutes chip (§6.6): remembered, and the remaining blocks re-planned."""

    if params.minutes <= 0 or params.minutes > 600:
        raise SidecarError("validation_error", "minutes must be between 1 and 600.", details={"field": "minutes"})
    required = _require(ctx, params.session_id, writes=True)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    set_minutes(env, int(params.minutes))
    return versioned(_current_view(env))


@method("next_plan_item", NextPlanItemInput)
@host_mutation
def next_plan_item(ctx: SidecarContext, params: NextPlanItemInput) -> dict[str, Any]:
    """The next step: ``{"kind": "item" | "reading" | "done", ...}`` (§6.10 typed steps)."""

    if params.serve and not params.session_id:
        raise SidecarError("validation_error", "serving a plan item needs a session.", details={"field": "sessionId"})
    # A serve or a skip is the session's step (mobile v2 §5.6); the desktop's prefetch read is not.
    # A phone never peeks (§4.5), and a read at a finished block crosses a boundary and writes its
    # decision, so every phone call is checked as a write (Codex review of V2, F1).
    required = _require(ctx, params.session_id, serve=params.serve,
                        writes=params.serve or bool(params.skip_practice_item_id) or ctx.request_origin is not None)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    if params.skip_practice_item_id:
        # FG1 §4.2: skipping a generated probe abandons it, and it is never served again.
        from learnloop.followup_run.serving import abandon

        abandon(env.repository, params.skip_practice_item_id)
    if params.serve and ctx.request_origin is None:
        _abandon_phone_served(env)
    record, step, context = advance_with_context(
        env, serve=params.serve, skip_practice_item_id=params.skip_practice_item_id
    )
    result = versioned({"enabled": True, "step": step, **_view(env, record, step, context)})
    if params.serve:
        from learnloop.followup_run.serving import bind_plan_step

        bind_plan_step(env.repository, step)
        _schedule_ad(ctx, env, step=step)
    return result


@method("plan_something_else_options", PlanSomethingElseOptionsInput)
def plan_something_else_options(ctx: SidecarContext, params: PlanSomethingElseOptionsInput) -> dict[str, Any]:
    """IH3 (spec_instruct_handoff_v1 §6): what the plan could do at this boundary, in plain words, for "Something else
    would help". Chooses nothing and draws nothing: the router's own feasible candidates, one per kind, with the
    probabilities the waiting decision logged (none when no draw is waiting)."""

    from learnloop.daily_plan import learner_action

    required = _require(ctx, params.session_id)
    if required is None:
        return versioned({"enabled": False})
    _vault, _repository, env = required
    return versioned(learner_action.options(env).view())


def _standing_view(env: PlanEnv) -> dict[str, Any]:
    """The plan as it stands, with no boundary crossed: a device's choice that serves nothing places nothing, and a read
    at a finished block would draw its decision in the same call (§6, spec_mobile_frontend_v2 §4.5). Nothing is being
    chosen because of this, so the reply doesn't say otherwise."""

    from learnloop.daily_plan.engine import get_or_create_today

    record = get_or_create_today(env, create=False)
    if record is None:
        return {"enabled": True, "plan": None}
    view = _view(env, record, None, None)
    view["plan"]["deciding"] = False
    return view


@method("plan_something_else", PlanSomethingElseInput)
@host_mutation
def plan_something_else(ctx: SidecarContext, params: PlanSomethingElseInput) -> dict[str, Any]:
    """IH3: serve the action the learner chose and log it with the options then (one transaction, idempotent on
    ``preference_id``). On the phone a lesson or a reading is logged and nothing is served: ``outcome`` says
    ``waits_on_desktop``."""

    from learnloop.daily_plan import learner_action

    required = _require(ctx, params.session_id, writes=True)
    if required is None:
        return versioned({"enabled": False})
    _vault, _repository, env = required
    try:
        chosen = learner_action.choose(env, kind=params.kind, ref=params.ref, surface=params.surface,
                                       attempt_id=params.attempt_id, note_md=params.note_md,
                                       preference_id=params.preference_id)
    except learner_action.PreferenceError as exc:
        raise SidecarError(exc.code if exc.code in ("validation_error", "not_found") else "invalid_request", str(exc),
                           details={"reason": exc.code}) from exc
    result = {
        "enabled": True,
        "preference": {"id": chosen.preference_id, "outcome": chosen.outcome, "kind": chosen.kind, "ref": chosen.ref,
                       "served_decision_id": chosen.served_decision_id, "lesson": chosen.lesson,
                       "replayed": chosen.replayed},
        "step": chosen.step,
        **(_standing_view(env) if env.device is not None and chosen.step is None else _current_view(env)),
    }
    if chosen.step is not None and chosen.outcome == "served":
        _schedule_ad(ctx, env, step=chosen.step)
    return versioned(result)


@method("record_offer_shown", OfferShownInput)
def record_offer_shown(ctx: SidecarContext, params: OfferShownInput) -> dict[str, Any]:
    """Spec_instruct_handoff_v1 §4 item 6: the offer's card or page rendered. One ``offer_shown`` event on the offer's
    block, at most once per block and surface; fire and forget, it never fails the page. Desktop only: it is not in
    ``DAILY_PLAN_RPCS``, so the phone host denies it (the phone shows no offers)."""

    try:
        _vault, repository = ctx.require_vault()
        from learnloop.daily_plan import lesson_offer

        recorded = lesson_offer.record_shown(repository, block_id=params.block_id, surface=params.surface,
                                             session_id=params.session_id)
    except Exception:  # noqa: BLE001 - a receipt never blocks the page
        logging.getLogger(__name__).warning("record_offer_shown failed", exc_info=True)
        recorded = False
    return versioned({"recorded": recorded})


@method("plan_prefetch", PlanPrefetchInput)
def plan_prefetch(ctx: SidecarContext, params: PlanPrefetchInput) -> dict[str, Any]:
    """Spec_instruct_handoff_v1 §3a: start the next boundary's objective job while the phone shows feedback, and
    return. Next's serve finds the job by its boundary key. Writes nothing, returns no step, and is not a host
    mutation. ``reason`` says why nothing started; it is for logs and tests, and the phone ignores the reply."""

    vault, repository = ctx.require_vault()
    reason = _prefetch(ctx, vault, repository, params.session_id)
    logging.getLogger(__name__).info("plan_prefetch: %s", reason)
    return versioned({"started": reason == "started", "reason": reason})


def _prefetch(ctx: SidecarContext, vault: Any, repository: Any, session_id: str) -> str:
    if not plan_active(vault):
        return "plan_off"
    if not prefetch_can_start(vault):
        return "no_model"
    from learnloop.db.repositories import Repository

    # Every read below goes through a read-only attach: a write fails at the database (``connect(read_only=True)``).
    # The job runs on its own writable attach, as every prefetch's does (``_objective_job``).
    reader = Repository.attach(repository.sqlite_path, read_only=True)
    session = reader.fetch_session(session_id)
    if session is None or session.get("ended_at") is not None:
        return "no_session"
    try:
        refuse_moved_session(ctx, reader, session_id)
    except SidecarError:
        return "session_moved"
    if reader.pending_live_diagnoses_for_session(session_id):
        # The serve waits for these (``_wait_for_session_diagnoses``), and what they find can change its pool, so its
        # key. The phone asks again once its diagnosis settles.
        return "diagnosis_pending"
    try:
        return prefetch_boundary(_env(ctx, vault, reader, session_id, prefetch=True))
    except Exception as exc:  # noqa: BLE001 - never reaches the learner; the serve decides as it always has
        # A write on the path fails here (``attempt to write a readonly database``). Only its type at the default
        # level: a traceback can quote what the plan read.
        logging.getLogger(__name__).warning("plan_prefetch: nothing started (%s)", type(exc).__name__)
        logging.getLogger(__name__).debug("plan_prefetch: nothing started", exc_info=True)
        return "unavailable"


def _abandon_phone_served(env: PlanEnv) -> None:
    """Mobile v2 V3 (owner decision D3): a generated probe this plan served on the phone, still unanswered, when the
    desktop (which owns the session now, checked above) asks for its next step. Its one administration was the
    phone's and the desktop's door refuses it, so the desktop's Next moves past it: it is abandoned (FG1 §4.2:
    abandonment closes it, what its workflow held is released, its decision's outcome is ``abandoned``), and the
    plan's reconcile then displaces it as a retired probe (``generated_probe_closed``). Only a phone's burn reaches
    here, which no vault had before V3; nothing else is read or written for the desktop.

    Not while the phone's answer to it is on its way (Codex review of V3, F2): one the host accepted before the
    handoff completes after it (§6.5), and abandoning now would end the presentation it consumes and release the
    feedback it releases, so it would record as incidental. It stays the phone's until that answer settles (the
    plan's reconcile then marks it done); meanwhile the plan resumes it, as it resumes any item whose answer is still
    being graded, and the learner's own Skip still abandons it. Nor once it has an answer."""

    from learnloop.capture.jobs import submission_in_flight
    from learnloop.daily_plan.engine import latest_today
    from learnloop.followup_run.serving import abandon
    from learnloop.followup_serve.gates import SERVING_SURFACE
    from learnloop.followup_serve.identity import served_elsewhere

    record = latest_today(env)
    if record is None or not record.is_open:
        return
    for item in record.items():
        if item.served_at is not None and not item.resolved \
                and served_elsewhere(env.repository, item.practice_item_id, SERVING_SURFACE) \
                and not _answered_since(env.repository, item.practice_item_id, item.served_at) \
                and not submission_in_flight(env.repository, item.practice_item_id):
            abandon(env.repository, item.practice_item_id, clock=env.clock)


def _answered_since(repository: Any, practice_item_id: str, served_at: str) -> bool:
    """An answer committed since the plan served it (the reconcile marks it done; nothing is left to abandon)."""

    with repository.connection() as connection:
        return connection.execute(
            "SELECT 1 FROM practice_attempts WHERE practice_item_id = ? AND created_at >= ? LIMIT 1",
            (practice_item_id, served_at),
        ).fetchone() is not None


@method("plan_reading_ended", PlanReadingEndedInput)
@host_mutation
def plan_reading_ended(ctx: SidecarContext, params: PlanReadingEndedInput) -> dict[str, Any]:
    """End the current reading block (left the reader, skipped, or completed)."""

    required = _require(ctx, params.session_id, writes=True)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    reading_ended(env, params.outcome)
    record, step, context = advance_with_context(env, serve=False)
    return versioned({"enabled": True, "step": step, **_view(env, record, step, context)})


@method("plan_keep_going", PlanKeepGoingInput)
@host_mutation
def plan_keep_going(ctx: SidecarContext, params: PlanKeepGoingInput) -> dict[str, Any]:
    """Keep going (§6.5): one more block of minutes; or "Done" (``stop``)."""

    required = _require(ctx, params.session_id, writes=True)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    if params.stop:
        stop_today(env)
    else:
        keep_going(env)
    return versioned(_current_view(env))


@method("plan_more_new", PlanMoreNewInput)
@host_mutation
def plan_more_new(ctx: SidecarContext, params: PlanMoreNewInput) -> dict[str, Any]:
    """"More new material" (§6.3): the trade-off first, then a labelled extension."""

    required = _require(ctx, params.session_id, writes=params.confirm)
    if required is None:
        return _off(ctx)
    _vault, _repository, env = required
    try:
        _record, preview = more_new(env, confirm=params.confirm)
    except PlanStillOpenError as exc:
        raise SidecarError("invalid_request", str(exc), details={"field": "confirm"}) from exc
    return versioned({"enabled": True, "preview": preview, **_current_view(env)})


@method("plan_learner_pick", PlanLearnerPickInput)
@host_mutation
def plan_learner_pick(ctx: SidecarContext, params: PlanLearnerPickInput) -> dict[str, Any]:
    """Open an item from the full list: a one-item learner-pick block (L3, G12).

    A proposal's pick is two records on either side of serving: the learner's
    selection (the usage signal, validated before anything is served) and, once
    the item was served, its delivery (S5's intervention, with the exact router
    decision of the block that served it)."""

    if params.idempotency_key:
        retried = _require(ctx, params.session_id)
        if retried is not None:
            made = picked_under(retried[2], params.idempotency_key, params.practice_item_id)
            if made is not None:
                # The same pick, retried (Reader RW4b fix round 5, R1):
                # answered as it was made. Its selection and delivery were
                # recorded with it; nothing is recorded again.
                return versioned({"enabled": True, "step": made[1], **_current_view(retried[2])})
    if params.source_exercise_import_id and not params.proposal_id:
        raise SidecarError("validation_error", "An imported exercise is delivered with its proposal.",
                           details={"field": "proposalId"})
    # Mobile v2 §5.6: the owner is checked before the proposal's selection is recorded.
    refuse_moved_session(ctx, ctx.require_vault()[1], params.session_id)
    selection = _proposal_selection(ctx, params) if params.proposal_id else None
    required = _require(ctx, params.session_id, writes=True)
    if required is None:
        # The plan is off: nothing is served here. The open list serves the
        # item when the learner opens it (DL0's open, which the response tells
        # the surface to take, carrying the proposal's identity); that serve
        # records the delivery (Codex re-review F10). Only the selection is
        # recorded now: the learner may never open it.
        off = _off(ctx)
        if selection is not None:
            selection.pop("exercise", None)
            off["proposalPick"] = to_camel({**selection, "delivery": "on_open"})
        return off
    _vault, _repository, env = required
    _refuse_held_pick(env, params.practice_item_id)
    from learnloop_sidecar.handlers.queue import revalidate_cold_check

    # A pick revalidates a cold check like every other serve (rounds 5, 6;
    # the one eligibility decision).
    revalidate_cold_check(env.vault, env.repository, params.practice_item_id)
    delivered: dict[str, Any] = {}

    def deliver(served_record: Any, served_step: dict[str, Any]) -> None:
        # Reader RW4b fix round 6 (F13): a keyed pick's delivery is written
        # in the pick's own transaction (block, serve, keyed receipt), so a
        # failure anywhere leaves nothing to recover and a retry makes it all once.
        delivered["pick"] = _proposal_delivery(ctx, params, selection,
                                               router_decision_id=_served_decision(served_record, served_step))

    keyed_delivery = bool(params.idempotency_key) and selection is not None
    try:
        record, step = learner_pick(
            env, params.practice_item_id, offer_candidate_id=params.scheduler_candidate_id,
            idempotency_key=params.idempotency_key, within=deliver if keyed_delivery else None,
        )
    except KeyError as exc:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.") from exc
    result = {"enabled": True, "step": step, **_current_view(env)}
    if keyed_delivery:
        if "pick" in delivered:  # absent: the pick was made already, and delivered with it
            result["proposal_pick"] = delivered["pick"]
    elif selection is not None:
        result["proposal_pick"] = _proposal_delivery(ctx, params, selection,
                                                     router_decision_id=_served_decision(record, step))
    _schedule_ad(ctx, env, step=step)
    return versioned(result)


def _refuse_held_pick(env: PlanEnv, practice_item_id: str) -> None:
    """Mobile v2 §2.2 (Codex review of V2, F2): a by-id pick is a serving door too, so it refuses,
    before anything is served or written, what the device's step filter holds for the desktop (PR-6's
    rules, the diagnostic check this session left there, and a generated probe until V3). The
    desktop (no filter) is never refused here."""

    if env.device is None:
        return
    item = env.vault.practice_items.get(practice_item_id)
    if item is None:
        return  # learner_pick answers an unknown item as it always has
    reason = env.device.holds(item)
    if reason is None:
        return
    from learnloop.scheduling.device_eligibility import GENERATED_PROBE

    if reason == GENERATED_PROBE:
        from learnloop.followup_serve.identity import GENERATED_PROBE_RESERVED

        raise SidecarError(GENERATED_PROBE_RESERVED, f"{item.id} is a single-use question and can't be opened here.",
                           details={"practice_item_id": item.id})
    from learnloop_sidecar.serving import DESKTOP_ONLY_ERROR_CODE

    raise SidecarError(DESKTOP_ONLY_ERROR_CODE, f"{item.id} can only be answered on the desktop.",
                       details={"practice_item_id": item.id, "reason": reason})


def _served_decision(record: Any, step: Mapping[str, Any]) -> str | None:
    """The router decision of the block that served the pick (its ``decision_ref``,
    R1's row when R1 logs plan decisions), or None."""

    block_id = (step or {}).get("block_id")
    if record is None or not block_id:
        return None
    block = next((block for block in record.blocks if block.id == block_id), None)
    return getattr(block, "decision_ref", None)


def _proposal_selection(ctx: SidecarContext, params: PlanLearnerPickInput) -> dict[str, Any]:
    """The learner's selection, validated before serving (S0, §6.3)."""

    from learnloop.instructional.practice import imported_exercise_selection, record_proposal_selection

    vault, repository = ctx.require_vault()
    try:
        if params.source_exercise_import_id:
            # The exercise's usage verdict was recorded when it was picked for import.
            return imported_exercise_selection(repository, proposal_id=str(params.proposal_id),
                                               import_id=params.source_exercise_import_id,
                                               practice_item_id=params.practice_item_id, vault=vault)
        return record_proposal_selection(repository, proposal_id=str(params.proposal_id),
                                         practice_item_id=params.practice_item_id, vault=vault)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


def select_on_open(ctx: SidecarContext, *, practice_item_id: str, session_id: str, proposal_id: str,
                   source_exercise_import_id: str | None = None) -> tuple[PlanLearnerPickInput, dict[str, Any]]:
    """The open list is about to serve a picked proposal's item (the plan
    off): its selection, re-checked BEFORE the serve (an item reserved for a
    held-out exam since it was proposed is refused)."""

    params = PlanLearnerPickInput(practice_item_id=practice_item_id, session_id=session_id,
                                  proposal_id=proposal_id, source_exercise_import_id=source_exercise_import_id)
    return params, _proposal_selection(ctx, params)


def deliver_on_open(ctx: SidecarContext, params: PlanLearnerPickInput, selection: dict[str, Any]) -> dict[str, Any]:
    """The open list served a picked proposal's item (the plan off): its
    delivery, recorded once after the serve (Codex re-review F10)."""

    return _proposal_delivery(ctx, params, selection, router_decision_id=None)


def _proposal_delivery(ctx: SidecarContext, params: PlanLearnerPickInput, selection: dict[str, Any], *,
                       router_decision_id: str | None) -> dict[str, Any]:
    """S5's intervention for a served pick (after serving succeeded)."""

    from learnloop.instructional.practice import record_proposal_delivery

    vault, repository = ctx.require_vault()
    exercise = selection.pop("exercise", None)
    selection["intervention_id"] = record_proposal_delivery(
        vault, repository, selection, session_id=params.session_id, router_decision_id=router_decision_id,
        exercise=exercise, import_id=selection.get("import_id"))
    selection["router_decision_id"] = router_decision_id
    return selection


@method("get_today_headline", PlanSessionInput)
def get_today_headline(ctx: SidecarContext, _params: PlanSessionInput) -> dict[str, Any]:
    """The optional one-line headline (§6.7, D7). Read-only."""

    vault, repository = ctx.require_vault()
    if not plan_active(vault) or not bool(vault.config.plan.headline):
        return versioned({"enabled": False})
    env = PlanEnv(vault=vault, repository=repository)
    headline = today_headline(vault, repository, now=env.now())
    classes = headline.pop("learning_object_classes")
    return versioned(
        {
            "enabled": True,
            **headline,
            # A list, not a mapping: LO ids must not be camel-cased on the way out.
            "learning_objects": [
                {"learning_object_id": lo_id, "class": value} for lo_id, value in sorted(classes.items())
            ],
        }
    )


__all__ = ["DAILY_PLAN_RPCS", "PlanInactiveError"]
