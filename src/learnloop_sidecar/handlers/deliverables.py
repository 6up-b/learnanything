"""Deliverable curriculum C0b RPCs: the deliverable's scope, its path across books, the
Guide's slice, the learner's overrides and "Am I ready?"
(spec_deliverable_curriculum_v1 §5, §7.1-§7.5, §8.5, §12).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``curriculum.deliverables``: the learner's deliverables (learner goals with a
  resolution) and their scope lines. No model call.
* ``curriculum.create_deliverable``: a new learner goal from the learner's sentence
  (and deadline), resolved at once (pressed: route ``deliverable_scope_resolver``).
* ``curriculum.set_scope``: one more scope input (text, a topic list, a passage, a
  correction), then the resolution and the goal's facet scope (§5.3: the new RPC that
  writes a goal's scope). A protected passage is refused first (G-C2).
* ``curriculum.scope`` / ``curriculum.scope_decide``: the scope lines; *add it* / *no*
  on a phrase not in the library (``create_goal_lo``; the learner's yes is the decision).
* ``curriculum.set_depth``: "How deep for this?" (asked once).
* ``curriculum.path`` / ``curriculum.guide_slice``: the deliverable's path, and its
  slice for the open book (the Guide's path card shows it; ``status: none`` leaves the
  card to RW7a). A stale path is judged in the background (route
  ``deliverable_path_judge``); the view never waits on it.
* ``curriculum.path_override``: *use this one instead*, *read it anyway*, *skip it*,
  *I know this, check me later* (a Check once commitment) or ``none``.
* ``curriculum.ready`` / ``curriculum.ready_check``: "Am I ready?": the line per topic,
  and the pressed button that adds one Check once per untested topic.
* ``curriculum.also_about``: the learner's "also about…" words on a section, resolved
  by the scope resolver and kept as C0a's correction.

**T1 (plan-first):** a request's own call (the resolver in ``create_deliverable``,
``set_scope``, ``also_about``) offers OpenRouter keyed by that RPC when the plan is
down (redesign D: the offer is the grant). The work a request spawns (the coverage of
a scope change's LOs, a path judgment) captures the request's unit at creation, so a
grant on that RPC covers it in this session; otherwise it waits for the plan, and its
next read relays the offer once. Nothing spawned asks on its own.

Kill switch ``curriculum.enabled``: off, every RPC here refuses, no call is made, and
the Guide is RW7a's exactly. Display only: nothing here writes a plan, evidence,
mastery, FSRS or scheduler state; the checks are learner-pressed commitments DL2's
unchanged rule serves.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from learnloop.reader import reader_dialogue as RD
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
DELIVERABLE_RPCS: tuple[str, ...] = (
    "curriculum.deliverables",
    "curriculum.create_deliverable",
    "curriculum.set_scope",
    "curriculum.scope",
    "curriculum.scope_decide",
    "curriculum.set_depth",
    "curriculum.path",
    "curriculum.guide_slice",
    "curriculum.path_override",
    "curriculum.ready",
    "curriculum.ready_check",
    "curriculum.also_about",
)


def _require(ctx: SidecarContext) -> tuple[Any, Any]:
    vault, repository = ctx.require_vault()
    if not DL.enabled(vault):
        raise SidecarError("curriculum_disabled", "The deliverable curriculum is off (curriculum.enabled = false).")
    # A publication a stopped process left half done (goals.yaml and its receipt) is
    # finished first (Codex review F8); goals.yaml changed, the vault is read again.
    if DL.recover_publications(vault.root, repository):
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
    return vault, repository


def _error(exc: Exception) -> SidecarError:
    code = getattr(exc, "code", None) or "validation_error"
    return SidecarError(str(code), str(exc))


def _reload(ctx: SidecarContext) -> tuple[Any, Any]:
    ctx.reload(maintenance=False)
    return _require(ctx)


# -- background work: the coverage a scope change owes, and path judgments --------------------------


class _Work:
    """One vault's background curriculum work, in memory: coverage per goal, path judgments
    per (goal, depth, state key), and the OpenRouter offer each failure made (T1)."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.covering: dict[str, dict[str, Any]] = {}
        #: The (LO, statement key) pairs this sidecar already tried to cover per goal: an
        #: LO with no candidate writes no row, so without this every read would search
        #: for it again. Keyed by the statement (``DP.coverage_key``): a changed LO is
        #: tried again (Codex review F5).
        self.attempted: dict[str, set[tuple[str, str | None]]] = {}
        self.judging: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.offers: dict[Any, dict[str, Any]] = {}


_REGISTRY_LOCK = threading.Lock()


def _work(ctx: SidecarContext) -> _Work:
    repository = getattr(ctx, "repository", None)
    database = str(Path(repository.sqlite_path).resolve()) if repository is not None else ""
    with _REGISTRY_LOCK:
        registries = getattr(ctx, "deliverable_work", None)
        if not isinstance(registries, dict):
            registries = {}
            ctx.deliverable_work = registries  # type: ignore[attr-defined]
        return registries.setdefault(database, _Work())


def _spawn(ctx: SidecarContext, name: str, run: Any) -> None:
    if getattr(ctx, "deliverable_inline", False):
        run()
    else:
        # Owned by the context: its close cancels the job's further requests and joins it.
        background_jobs(ctx).spawn(run, name=name)


def _unit(vault: Any, label: str) -> tuple[Any, Any, Any]:
    from learnloop.ai import plan_fallback

    grant, origin = plan_fallback.unit_token(vault.root), plan_fallback.unit_origin()
    stamp = plan_fallback.unit_stamp(vault.root)
    plan_fallback.note_unit("job", label)
    return grant, origin, stamp


def _cover(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str) -> None:
    """Judge the coverage the deliverable's LOs owe (never judged yet), in the background.

    Captures the spawning request's unit (T1): a grant on that RPC covers it; otherwise
    it waits for the plan, and the path's next read relays the offer once."""

    work = _work(ctx)
    with work.lock:
        attempted = set(work.attempted.get(goal_id, ()))
    owed = [lo for lo in DP.coverage_owed(vault, repository, goal_id)
            if (lo, DP.coverage_key(vault, lo)) not in attempted]
    if not owed:
        return
    with work.lock:
        if (work.covering.get(goal_id) or {}).get("state") == "running":
            return
        work.covering[goal_id] = {"state": "running", "learning_object_ids": owed}
        work.attempted.setdefault(goal_id, set()).update((lo, DP.coverage_key(vault, lo)) for lo in owed)
    grant, origin, stamp = _unit(vault, f"deliverable-coverage:{goal_id}")
    live_vault = ctx.loaded_vault
    root = Path(vault.root).resolve()
    client = getattr(ctx, "coverage_judge_client", None)
    embedder = getattr(ctx, "coverage_embedder", None)
    sqlite_path = repository.sqlite_path

    def run() -> None:
        from learnloop.ai import plan_fallback
        from learnloop.ai.execution import record_model_calls
        from learnloop.db.repositories import Repository

        failure: dict[str, Any] | None = None
        with plan_fallback.unit(grant, origin, stamp) as offers:
            try:
                worker = Repository.attach(sqlite_path)
                with record_model_calls(worker, owner_kind="sidecar_rpc", owner_id=f"deliverable-coverage:{goal_id}"):
                    library = SC.Library(vault, worker)
                    for lo_id in owed:
                        current = live_vault()
                        if current is None or Path(current.root).resolve() != root:
                            failure = {"reason": "vault_switched", "message": SC.STALE_MESSAGE}
                            break
                        library = library.refreshed(current)
                        result = SC.judge(current, worker, lo_id, library=library, client=client, embedder=embedder,
                                          live_vault=live_vault)
                        if result.status in SC.STOPPING:
                            reason = str(result.reason or result.status).split(":", 1)[0]
                            failure = {"reason": reason, "message": result.message or SC.STALE_MESSAGE}
                            break
            except SC.CoverageError as exc:
                failure = {"reason": "protection_unreadable", "message": str(exc)}
            except BaseException as exc:  # noqa: BLE001 - a failed job answers its read, never the loop
                LOG.warning("deliverable coverage failed: %s", type(exc).__name__, exc_info=exc)
                failure = {"reason": "judge_failed",
                           "message": "Couldn't check where your books treat these topics just now. Try again ↵"}
        offer = offers.hint() if failure is not None else None
        with work.lock:
            work.covering[goal_id] = {"state": "failed", **failure} if failure else {"state": "done"}
            if offer is not None:
                work.offers[("cover", goal_id)] = offer

    _spawn(ctx, f"deliverable-coverage-{goal_id}", run)


def _judge_path(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, depth: str, state_key: str) -> None:
    work = _work(ctx)
    key = (goal_id, depth, state_key)
    with work.lock:
        if (work.judging.get(key) or {}).get("state") == "running":
            return
        work.judging[key] = {"state": "running"}
    grant, origin, stamp = _unit(vault, f"deliverable-path:{goal_id}:{depth}")
    client = getattr(ctx, "deliverable_path_client", None)
    sqlite_path = repository.sqlite_path
    live_vault = ctx.loaded_vault
    root = Path(vault.root).resolve()

    def run() -> None:
        from learnloop.ai import plan_fallback
        from learnloop.ai.execution import record_model_calls
        from learnloop.db.repositories import Repository

        outcome: dict[str, Any] | None
        with plan_fallback.unit(grant, origin, stamp) as offers:
            try:
                # The vault as it is when the job runs, not when it was spawned (Codex
                # review F1); protection is checked again before every request and the write.
                current = live_vault()
                if current is None or Path(current.root).resolve() != root:
                    outcome = {"state": "failed", "reason": "vault_switched", "message": SC.STALE_MESSAGE}
                else:
                    worker = Repository.attach(sqlite_path)
                    with record_model_calls(worker, owner_kind="sidecar_rpc",
                                            owner_id=f"curriculum.path:{goal_id}:{depth}"):
                        result = DP.judge(current, worker, goal_id, client=client, live_vault=live_vault)
                    outcome = None if result.status in ("ready", "fresh", "no_sections", "no_scope") else {
                        "state": "failed", "reason": result.reason, "message": result.message}
            except BaseException as exc:  # noqa: BLE001 - a failed judgment answers the view, never the loop
                LOG.warning("deliverable path judgment failed: %s", type(exc).__name__, exc_info=exc)
                outcome = {"state": "failed", "reason": "judge_failed",
                           "message": "Couldn't choose a path across your books just now. Try again ↵"}
        offer = offers.hint() if outcome is not None else None
        with work.lock:
            if outcome is None:
                work.judging.pop(key, None)
            else:
                work.judging[key] = outcome
            if offer is not None:
                work.offers[key] = offer

    _spawn(ctx, f"deliverable-path-{goal_id}-{depth}", run)


def _relay(work: _Work, key: Any) -> None:
    from learnloop.ai import plan_fallback

    with work.lock:
        offer = work.offers.pop(key, None)
    if offer is not None:
        plan_fallback.relay_hint(offer)


def _readmit_coverage(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str,
                      current: dict[str, Any]) -> dict[str, Any]:
    """A coverage admission refusal (capped, unpriced, unrouted, models off) holds only
    while its condition does (RW7a's rule; Codex review F6): asked again on each read,
    before any call. Lifted, the failure and the attempts it marked are dropped, so the
    coverage starts again; still refused, today's wording is kept."""

    try:
        problem = SC.admission_problem(vault, repository, client=getattr(ctx, "coverage_judge_client", None))
    except Exception:  # noqa: BLE001 - an unreadable check keeps the refusal shown
        LOG.warning("deliverable coverage admission check failed", exc_info=True)
        return current
    work = _work(ctx)
    with work.lock:
        if work.covering.get(goal_id) != current:
            return dict(work.covering.get(goal_id) or {})  # changed meanwhile: that state stands
        if problem is None:
            work.covering.pop(goal_id, None)
            work.attempted.pop(goal_id, None)
            return {}
        refreshed = {"state": "failed", "reason": problem[0], "message": problem[1]}
        work.covering[goal_id] = refreshed
        return dict(refreshed)


def _path_state(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, *, judge: bool,
                retry: bool) -> tuple[dict[str, Any] | None, bool, dict[str, Any] | None]:
    """``(judging, covering, coverage failure)`` for the deliverable now, starting what it
    owes: the coverage of its LOs first, then (once no coverage is running) the path
    judgment. A failed coverage check is returned so the view shows it with *try again*
    (Codex review F6); ``retry`` drops it and starts again."""

    work = _work(ctx)
    with work.lock:
        covering_state = dict(work.covering.get(goal_id) or {})
        if retry and covering_state.get("state") == "failed":
            work.covering.pop(goal_id, None)
            work.attempted.pop(goal_id, None)
            covering_state = {}
    if covering_state.get("state") == "failed" and covering_state.get("reason") in DL.ADMISSION_REASONS:
        covering_state = _readmit_coverage(ctx, vault, repository, goal_id, covering_state)
    if judge and covering_state.get("state") not in ("running", "failed"):
        _cover(ctx, vault, repository, goal_id)
    with work.lock:
        covering_state = dict(work.covering.get(goal_id) or {})
    covering = covering_state.get("state") == "running"
    failure = covering_state if covering_state.get("state") == "failed" else None
    if failure is not None:
        _relay(work, ("cover", goal_id))
    depth = DL.depth_of(repository, goal_id)
    if depth is None:
        return None, covering, failure
    try:
        inputs = DP.path_inputs(vault, repository, goal_id)
    except SC.CoverageError:
        return None, covering, failure
    if inputs is None:
        return None, covering, failure
    state_key = inputs.state_key()
    key = (goal_id, depth, state_key)
    with work.lock:
        current = dict(work.judging.get(key) or {})
        if retry and current.get("state") == "failed":
            work.judging.pop(key, None)
            current = {}
    if current.get("state") == "failed" and current.get("reason") in DL.ADMISSION_REASONS:
        problem = DL.admission_problem(vault, repository, DL.PATH_ROUTE,
                                       client=getattr(ctx, "deliverable_path_client", None))
        with work.lock:
            if problem is None:
                work.judging.pop(key, None)
                current = {}
            else:
                current = {"state": "failed", "reason": problem.reason, "message": problem.message}
                work.judging[key] = current
    with repository.connection() as connection:
        from learnloop.db.stores import deliverables as store

        fresh = bool(store.judged(connection, goal_id, depth, state_key))
    if judge and not covering and not current and not fresh and inputs.choosable:
        _judge_path(ctx, vault, repository, goal_id, depth, state_key)
        with work.lock:
            current = dict(work.judging.get(key) or {})
    if current.get("state") == "failed":
        _relay(work, key)
    return (current or None), covering, failure


def _likely(vault: Any, repository: Any) -> Any:
    """AD's labelled prediction per LO for "Am I ready?" (None while AD does not predict)."""

    def read(learning_object_id: str) -> dict[str, Any] | None:
        from learnloop.adaptive_difficulty.readiness import LIKELY, lo_readiness

        found = lo_readiness(vault, repository, learning_object_id)
        if not found.get("predicted"):
            return None
        cells = found.get("cells") or []
        return {"likely": bool(cells) and all(cell.get("label") == LIKELY for cell in cells),
                "line": found.get("line")}

    return read


# -- the RPCs -----------------------------------------------------------------------------------


@method("curriculum.deliverables")
def curriculum_deliverables(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    """The learner's deliverables and their scope lines (no model call)."""

    vault, repository = _require(ctx)
    goals = DL.deliverable_goals(vault, repository)
    return versioned({"deliverables": [DL.scope_view(vault, repository, goal.id) for goal in goals]})


class CreateDeliverableInput(ParamsModel):
    sentence: str
    due_at: str | None = None
    exam: bool = False


def _after_scope(ctx: SidecarContext, goal_id: str, result: DL.ScopeResult) -> dict[str, Any]:
    vault, repository = _reload(ctx)
    if result.status in ("ready", "fresh"):
        _cover(ctx, vault, repository, goal_id)
    return {"status": result.status, "reason": result.reason, "message": result.message,
            "scope": DL.scope_view(vault, repository, goal_id)}


@method("curriculum.create_deliverable", CreateDeliverableInput)
def curriculum_create_deliverable(ctx: SidecarContext, params: CreateDeliverableInput) -> dict[str, Any]:
    """A new deliverable from the learner's sentence, resolved at once (pressed)."""

    vault, repository = _require(ctx)
    try:
        created = DL.create_deliverable(vault, repository, params.sentence, due_at=params.due_at, exam=params.exam)
    except DL.DeliverableError as exc:
        raise _error(exc) from exc
    vault, repository = _reload(ctx)
    result = DL.resolve(vault, repository, created["goal_id"], client=getattr(ctx, "deliverable_scope_client", None),
                        live_vault=ctx.loaded_vault)
    return versioned({"goal_id": created["goal_id"], **_after_scope(ctx, created["goal_id"], result)})


class SetScopeInput(ParamsModel):
    goal_id: str
    #: text | topic_list | passage | correction
    kind: str
    text: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = []
    #: Where the words came from (a path line's "not what I need…"), kept with them.
    context: dict[str, Any] = {}


@method("curriculum.set_scope", SetScopeInput)
def curriculum_set_scope(ctx: SidecarContext, params: SetScopeInput) -> dict[str, Any]:
    """One more scope input in the learner's words, then the resolution and the goal's scope."""

    vault, repository = _require(ctx)
    if params.kind not in DL.SCOPE_KINDS:
        raise SidecarError("validation_error", f"Unknown scope input {params.kind!r}.")
    extraction_id = params.extraction_id
    if extraction_id:
        from learnloop.content.sources.source_outline import resolve_extraction_id

        extraction_id = resolve_extraction_id(repository, extraction_id) or extraction_id
    try:
        DL.add_input(vault, repository, params.goal_id, params.kind, text=params.text, extraction_id=extraction_id,
                     span_ids=params.span_ids, context=params.context)
        result = DL.resolve(vault, repository, params.goal_id, client=getattr(ctx, "deliverable_scope_client", None),
                            live_vault=ctx.loaded_vault)
    except DL.DeliverableError as exc:
        raise _error(exc) from exc
    return versioned(_after_scope(ctx, params.goal_id, result))


class GoalInput(ParamsModel):
    goal_id: str


@method("curriculum.scope", GoalInput)
def curriculum_scope(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]:
    """The deliverable's scope lines (no model call)."""

    vault, repository = _require(ctx)
    try:
        return versioned(DL.scope_view(vault, repository, params.goal_id))
    except DL.DeliverableError as exc:
        raise _error(exc) from exc


class ScopeDecideInput(ParamsModel):
    goal_id: str
    phrase: str
    #: create (add it) | decline (no)
    decision: str
    subject_id: str | None = None


@method("curriculum.scope_decide", ScopeDecideInput)
def curriculum_scope_decide(ctx: SidecarContext, params: ScopeDecideInput) -> dict[str, Any]:
    """*add it* / *no* on a phrase not in the library: an LO is created only on the learner's yes."""

    vault, repository = _require(ctx)
    try:
        out = DL.decide_unmatched(vault, repository, params.goal_id, params.phrase, params.decision,
                                  subject_id=params.subject_id)
    except DL.DeliverableError as exc:
        raise _error(exc) from exc
    vault, repository = _reload(ctx)
    if out["created"]:
        _cover(ctx, vault, repository, params.goal_id)
    return versioned({"created": out["created"], "scope": DL.scope_view(vault, repository, params.goal_id)})


class SetDepthInput(ParamsModel):
    goal_id: str
    depth: str


@method("curriculum.set_depth", SetDepthInput)
def curriculum_set_depth(ctx: SidecarContext, params: SetDepthInput) -> dict[str, Any]:
    """"How deep for this?" (asked once; the newest stands)."""

    vault, repository = _require(ctx)
    try:
        DL.add_input(vault, repository, params.goal_id, "depth", text=params.depth)
    except DL.DeliverableError as exc:
        raise _error(exc) from exc
    return versioned(_path(ctx, vault, repository, params.goal_id, judge=True, retry=False))


def _path(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, *, judge: bool, retry: bool) -> dict[str, Any]:
    try:
        judging, covering, failure = _path_state(ctx, vault, repository, goal_id, judge=judge, retry=retry)
        return DP.path_view(vault, repository, goal_id, judging=judging, covering=covering, coverage_failure=failure)
    except DL.DeliverableError as exc:
        raise _error(exc) from exc


class PathInput(ParamsModel):
    goal_id: str
    #: Start what a stale path owes (coverage, then the judgment) in the background.
    judge: bool = True
    retry: bool = False


@method("curriculum.path", PathInput)
def curriculum_path(ctx: SidecarContext, params: PathInput) -> dict[str, Any]:
    """The deliverable's path across books (at once; any judgment runs in the background)."""

    vault, repository = _require(ctx)
    return versioned(_path(ctx, vault, repository, params.goal_id, judge=params.judge, retry=params.retry))


class GuideSliceInput(ParamsModel):
    extraction_id: str
    judge: bool = True
    retry: bool = False


@method("curriculum.guide_slice", GuideSliceInput)
def curriculum_guide_slice(ctx: SidecarContext, params: GuideSliceInput) -> dict[str, Any]:
    """The Guide's slice of a deliverable's path for this reading (``status: none``: RW7a's card)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = _require(ctx)
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    goal = DP.guide_goal(vault, repository, resolved)
    if goal is None:
        return versioned({"extraction_id": resolved, "status": "none"})
    judging, covering, failure = _path_state(ctx, vault, repository, goal.id, judge=params.judge, retry=params.retry)
    return versioned(DP.guide_slice(vault, repository, resolved, judging=judging, covering=covering,
                                    coverage_failure=failure))


class PathOverrideInput(ParamsModel):
    goal_id: str
    learning_object_id: str
    #: use_instead | read_anyway | skip | check_later | none
    choice: str
    #: use_instead: the alternate's ``extraction_id/section_id``.
    section_ref: str | None = None


@method("curriculum.path_override", PathOverrideInput)
def curriculum_path_override(ctx: SidecarContext, params: PathOverrideInput) -> dict[str, Any]:
    """A path line's choice: kept across re-judgments; marks nothing as known."""

    vault, repository = _require(ctx)
    try:
        out = DP.override(vault, repository, params.goal_id, params.learning_object_id, params.choice,
                          section_ref=params.section_ref)
    except (DL.DeliverableError, SC.CoverageError) as exc:
        raise _error(exc) from exc
    if out.get("check"):
        repository.bump_queue_revision()
    return versioned({**out, "path": _path(ctx, vault, repository, params.goal_id, judge=False, retry=False)})


@method("curriculum.ready", GoalInput)
def curriculum_ready(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]:
    """The answer to "am I ready?": per topic demonstrated, likely (a prediction) or untested."""

    vault, repository = _require(ctx)
    try:
        return versioned(DP.readiness(vault, repository, params.goal_id, likely=_likely(vault, repository)))
    except DL.DeliverableError as exc:
        raise _error(exc) from exc


@method("curriculum.ready_check", GoalInput)
def curriculum_ready_check(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]:
    """The pressed "Am I ready?": one Check once per topic not shown and not already waiting."""

    vault, repository = _require(ctx)
    try:
        return versioned(DP.ready_checks(vault, repository, params.goal_id, likely=_likely(vault, repository)))
    except DL.DeliverableError as exc:
        raise _error(exc) from exc


class AlsoAboutInput(ParamsModel):
    extraction_id: str
    section_id: str
    text: str


@method("curriculum.also_about", AlsoAboutInput)
def curriculum_also_about(ctx: SidecarContext, params: AlsoAboutInput) -> dict[str, Any]:
    """*also about…* in the learner's words: resolved to a topic and kept as their correction."""

    vault, repository = _require(ctx)
    from learnloop.content.sources.source_outline import resolve_extraction_id

    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    try:
        return versioned(DL.also_about(vault, repository, resolved, params.section_id, params.text,
                                       client=getattr(ctx, "deliverable_scope_client", None),
                                       live_vault=ctx.loaded_vault))
    except DL.DeliverableError as exc:
        raise _error(exc) from exc


__all__ = ["DELIVERABLE_RPCS"]
