"""Deliverable curriculum C2 RPCs: the learner's notes, linked
(spec_deliverable_curriculum_v1 §10, §12 C2).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``notes.path``: the notes shown on a deliverable's path lines ("your note from 3 Oct"),
  by topic. Reading it starts the background linking for that deliverable (at most once a
  local day per path; route ``note_link_judge``), which the view never waits on.
* ``notes.marks``: the ``›`` marks of one reading (per passage, its linked notes).
* ``notes.passages``: Compare's *your take* band (the notes linked to the compared
  passages); *use as my take* is RW4d's own keep with a take quoting the note.
* ``notes.search`` / ``notes.link``: the Reader's *link one of your notes* (a search with
  no words uses the passage's section title; the learner's words search by words only),
  and the link made by hand.
* ``notes.decide``: one tap hides a link (``hide``), or keeps it after all (``keep``).
* ``notes.set_gaps``: curriculum C5's opt-in from Settings (``notes.gaps_enabled``, off by
  default): a linked note may then be read for gaps in the learner's understanding, on the
  ChatGPT plan only; it only ever steers what to suggest, never grades. The links that
  stand are queued for the gap pipeline when a link run ends, when the learner links a
  note or keeps a link, when the opt-in is turned on and when a vault opens
  (:func:`queue_note_gaps`); a hidden link never is.

**The ChatGPT plan only (§10.4):** the background linking runs under
``plan_fallback.quiet()``: no OpenRouter offer and no grant, ever; a route that does not
resolve to the plan sends nothing; with the plan down it waits and nothing asks. No RPC
here makes a model call in the request.

Kill switch ``notes.enabled`` (and tend absent): every RPC refuses, no tend call is made,
the prompt contract has no ``notes`` key, and the Reader, the path and Compare are
today's exactly. Display and learner-voice records only: nothing here writes a source, an
item, evidence, mastery, FSRS, scheduler state or a plan.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import note_links as NL
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)
#: The clock a waiting run's retry time is read on (a test sets it).
_monotonic = time.monotonic

#: Every RPC this module registers (pinned desktop-only).
NOTES_RPCS: tuple[str, ...] = (
    "notes.path",
    "notes.marks",
    "notes.passages",
    "notes.search",
    "notes.link",
    "notes.decide",
    "notes.set_gaps",
)

#: Settings' copy for curriculum C5's opt-in (owner Q9): honest about what it does.
GAPS_LINE = ("Let LearnLoop's model on your ChatGPT plan read the notes you've linked for gaps in your "
             "understanding. It only ever steers what to suggest, never grades you.")


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for C2 (absent while off or tend is absent)."""

    settings = NL.tend_settings(vault)
    if settings is None:
        return {}
    fields: dict[str, Any] = {"enabled": True, "lexical_only": settings.lexical_only,
                              "pocket_notes_label": NL.POCKET_NOTES_LABEL, "take_prefix": NL.TAKE_PREFIX}
    if bool(getattr(vault.config.notes, "gaps_enabled", False)):
        # Curriculum C5: present only with the opt-in on, so switched off the contract is today's.
        fields["gaps"] = True
    return {"notes": fields}


def queue_note_gaps(ctx: SidecarContext, vault: Any, repository: Any) -> int:
    """Curriculum C5: queue the linked notes' current snapshots for the gap pipeline and
    wake its worker (no model call here). Switched off it reads no note row and queues
    nothing; a failure never fails the learner's act."""

    try:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_learner_notes

        queued = enqueue_learner_notes(vault, repository)
    except Exception:  # noqa: BLE001 - gaps from notes never block the notes
        LOG.warning("could not queue linked notes for gaps", exc_info=True)
        return 0
    if queued:
        worker = getattr(ctx, "post_attempt_worker", None)
        if worker is not None:
            worker.notify()
    return queued


def _require(ctx: SidecarContext) -> tuple[Any, Any]:
    vault, repository = ctx.require_vault()
    if not NL.enabled(vault):
        raise SidecarError("notes_disabled", "Your notes are switched off (notes.enabled = false).")
    if not NL.available(vault):
        raise SidecarError("notes_unavailable", "Your notes aren't available here: tend isn't installed.")
    return vault, repository


def _error(exc: NL.NotesError) -> SidecarError:
    return SidecarError(exc.code, str(exc))


def _extraction(repository: Any, extraction_id: str) -> str:
    from learnloop.content.sources.source_outline import resolve_extraction_id

    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    return resolved


# -- background linking ---------------------------------------------------------------------------


class _Work:
    """One vault's background note linking, in memory: per deliverable, the (day, path)
    it last started for, and that run's state."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.started: dict[str, str] = {}
        self.state: dict[str, dict[str, Any]] = {}


_REGISTRY_LOCK = threading.Lock()


def _work(ctx: SidecarContext) -> _Work:
    repository = getattr(ctx, "repository", None)
    database = str(Path(repository.sqlite_path).resolve()) if repository is not None else ""
    with _REGISTRY_LOCK:
        registries = getattr(ctx, "notes_work", None)
        if not isinstance(registries, dict):
            registries = {}
            ctx.notes_work = registries  # type: ignore[attr-defined]
        return registries.setdefault(database, _Work())


def _spawn(ctx: SidecarContext, name: str, run: Any) -> None:
    if getattr(ctx, "notes_inline", False):
        run()
    else:
        # Owned by the context: its close cancels the job's further requests and joins it.
        background_jobs(ctx).spawn(run, name=name)


def _link(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, targets: list[NL.Target], *,
          retry: bool) -> None:
    """Start the deliverable's note linking in the background: once a local day per path
    (its topics and their passages), again after a run that waited for the plan or tend,
    once ``NL.WAITING_RETRY_SECONDS`` have passed since it stopped (Codex re-review F14:
    the reads polling a waiting run never restart it each time), or at once on ``retry``."""

    from learnloop.daily_plan.engine import local_date

    if not targets:
        return
    key = content_key({"day": local_date(), "path": [[t.learning_object_id, t.extraction_id, t.section_id]
                                                      for t in targets]})
    work = _work(ctx)
    with work.lock:
        state = work.state.get(goal_id) or {}
        if state.get("state") == "running":
            return
        if work.started.get(goal_id) == key and state.get("state") == "done" and not retry:
            return
        if state.get("state") == "waiting" and not retry and _monotonic() < float(state.get("retry_at") or 0.0):
            return
        work.started[goal_id] = key
        work.state[goal_id] = {"state": "running"}
    client = getattr(ctx, "note_link_client", None)
    sqlite_path = repository.sqlite_path
    live_vault = ctx.loaded_vault
    root = Path(vault.root).resolve()

    def still_wanted() -> bool:
        now_vault = live_vault()
        return now_vault is not None and Path(now_vault.root).resolve() == root and NL.available(now_vault)

    def run() -> None:
        from learnloop.ai import plan_fallback
        from learnloop.ai.execution import record_model_calls
        from learnloop.db.repositories import Repository

        outcome: dict[str, Any]
        try:
            # Quiet (§10.4): never an OpenRouter offer and never a grant; the plan or nothing.
            with plan_fallback.quiet():
                current = live_vault()
                if current is None or Path(current.root).resolve() != root or not still_wanted():
                    outcome = {"state": "done", "status": "switched_off"}
                else:
                    worker = Repository.attach(sqlite_path)
                    with record_model_calls(worker, owner_kind="sidecar_rpc", owner_id=f"notes.link:{goal_id}"):
                        result = NL.link_goal(current, worker, goal_id, client=client, live_vault=live_vault,
                                              still_wanted=still_wanted)
                    outcome = {"state": "waiting" if result.status in ("waiting", "tend_unavailable") else "done",
                               "status": result.status, "reason": result.reason,
                               "linked": sum(entry.linked for entry in result.results)}
        except BaseException as exc:  # noqa: BLE001 - a failed run answers the next read, never the loop
            LOG.warning("note linking failed: %s", type(exc).__name__, exc_info=exc)
            outcome = {"state": "waiting", "status": "failed", "reason": type(exc).__name__}
        if outcome["state"] == "waiting":
            outcome["retry_at"] = _monotonic() + NL.WAITING_RETRY_SECONDS
        elif outcome.get("status") == "done":
            # Curriculum C5: the links that stand now, queued for gaps (with the opt-in only).
            now_vault = live_vault()
            if now_vault is not None and Path(now_vault.root).resolve() == root:
                from learnloop.db.repositories import Repository

                queue_note_gaps(ctx, now_vault, Repository.attach(sqlite_path))
        with work.lock:
            work.state[goal_id] = outcome

    _spawn(ctx, f"notes-link-{goal_id}", run)


# -- the RPCs ------------------------------------------------------------------------------------


class GoalInput(ParamsModel):
    goal_id: str
    #: Start the background linking (once a day per path) when it is due.
    link: bool = True
    retry: bool = False


@method("notes.path", GoalInput)
def notes_path(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]:
    """The notes on a deliverable's path lines, by topic (no model call in the request)."""

    vault, repository = _require(ctx)
    if not DL.enabled(vault):
        raise SidecarError("curriculum_disabled", "The deliverable curriculum is off (curriculum.enabled = false).")
    targets = NL.path_targets(vault, repository, params.goal_id)
    if params.link:
        _link(ctx, vault, repository, params.goal_id, targets, retry=params.retry)
    with _work(ctx).lock:
        state = dict(_work(ctx).state.get(params.goal_id) or {})
    return versioned({"goal_id": params.goal_id, "linking": state.get("state"),
                      # A list, not a map: LO ids are data (the wire camel-cases map keys).
                      "lines": [{"learning_object_id": lo, "notes": views}
                                for lo, views in NL.for_goal(vault, repository, params.goal_id, targets=targets).items()]})


class ExtractionInput(ParamsModel):
    extraction_id: str


@method("notes.marks", ExtractionInput)
def notes_marks(ctx: SidecarContext, params: ExtractionInput) -> dict[str, Any]:
    """The ``›`` marks of one reading: per passage, the notes linked beside it."""

    vault, repository = _require(ctx)
    extraction_id = _extraction(repository, params.extraction_id)
    return versioned({"extraction_id": extraction_id, "marks": NL.marks(vault, repository, extraction_id)})


class PassageRef(ParamsModel):
    extraction_id: str
    span_id: str


class PassagesInput(ParamsModel):
    passages: list[PassageRef]


@method("notes.passages", PassagesInput)
def notes_passages(ctx: SidecarContext, params: PassagesInput) -> dict[str, Any]:
    """Compare's *your take* band: the notes linked to the compared passages."""

    vault, repository = _require(ctx)
    from learnloop.source_retrieval.kept_comparisons import MAX_TAKE_CHARS

    passages = [{"extraction_id": _extraction(repository, entry.extraction_id), "span_id": entry.span_id}
                for entry in params.passages[:40]]
    views = NL.for_passages(vault, repository, passages)
    return versioned({"notes": [{**view, "take_text": NL.take_text(view, limit=MAX_TAKE_CHARS)} for view in views]})


class SearchInput(ParamsModel):
    query: str | None = None
    extraction_id: str | None = None
    span_id: str | None = None


@method("notes.search", SearchInput)
def notes_search(ctx: SidecarContext, params: SearchInput) -> dict[str, Any]:
    """*link one of your notes*: tend's hits for the passage (or the learner's words, by words only)."""

    from learnloop.curriculum.notes_tend import TendUnavailable

    vault, repository = _require(ctx)
    extraction_id = _extraction(repository, params.extraction_id) if params.extraction_id else None
    try:
        return versioned(NL.search(vault, repository, query=params.query, extraction_id=extraction_id,
                                   span_id=params.span_id))
    except NL.NotesError as exc:
        raise _error(exc) from exc
    except TendUnavailable as exc:
        raise SidecarError("tend_unavailable", str(exc)) from exc


class NoteRef(ParamsModel):
    path: str
    line: int
    heading_path: str = ""
    title: str = ""
    content_hash: str = ""
    mtime: float = 0.0


class LinkInput(ParamsModel):
    note: NoteRef
    extraction_id: str
    span_id: str


@method("notes.link", LinkInput)
def notes_link(ctx: SidecarContext, params: LinkInput) -> dict[str, Any]:
    """The learner links a note to a passage by hand (theirs: kept, never re-judged)."""

    vault, repository = _require(ctx)
    extraction_id = _extraction(repository, params.extraction_id)
    try:
        out = NL.link_by_hand(vault, repository, hit=params.note.model_dump(), extraction_id=extraction_id,
                              span_id=params.span_id)
    except NL.NotesError as exc:
        raise _error(exc) from exc
    queue_note_gaps(ctx, vault, repository)
    return versioned({**out, "marks": NL.marks(vault, repository, extraction_id)})


class DecideInput(ParamsModel):
    link_id: str
    #: hide | keep
    choice: str


@method("notes.decide", DecideInput)
def notes_decide(ctx: SidecarContext, params: DecideInput) -> dict[str, Any]:
    """One tap: hide a note link (hidden across re-judgments), or keep it after all."""

    vault, repository = _require(ctx)
    try:
        out = NL.decide(vault, repository, params.link_id, params.choice)
    except NL.NotesError as exc:
        raise _error(exc) from exc
    if params.choice == "keep":
        queue_note_gaps(ctx, vault, repository)  # a hidden link is never queued (C5)
    return versioned(out)


class GapsInput(ParamsModel):
    enabled: bool


@method("notes.set_gaps", GapsInput)
def notes_set_gaps(ctx: SidecarContext, params: GapsInput) -> dict[str, Any]:
    """Curriculum C5's opt-in from Settings (owner Q9: off by default): writes
    ``notes.gaps_enabled``. On, the linked notes are queued for the gap pipeline (read on
    the ChatGPT plan only); off, the gaps code reads no note row again."""

    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates

    vault, _repository = _require(ctx)
    try:
        apply_config_updates(vault.root / "learnloop.toml", {("notes", "gaps_enabled"): bool(params.enabled)})
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    ctx.reload(maintenance=False)
    vault, repository = _require(ctx)
    enabled = bool(vault.config.notes.gaps_enabled)
    if enabled:
        queue_note_gaps(ctx, vault, repository)
    return versioned({"gaps_enabled": enabled, "line": GAPS_LINE})


__all__ = ["GAPS_LINE", "NOTES_RPCS", "prompt_contract_fields", "queue_note_gaps"]
