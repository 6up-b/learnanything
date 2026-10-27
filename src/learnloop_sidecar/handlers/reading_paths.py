"""Reader workbench RW7a RPCs: the Guide's reading path (spec_reader_workbench_v1 §10.1).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``reader.reading_path``: the path view. When the depth is known and the
  cached path is not the current state's, the judge (one call per source and
  depth, route ``reading_path_judge``) runs in the background and the Reader
  reads the view again (it never waits on the request path). A fresh cached
  path makes no call.
* ``reader.reading_path_set_depth``: the Guide's "How deep do you want to
  go?" for the source (its own row; DL2's intent is only read).
* ``reader.reading_path_override``: "read it anyway" / "skip it" (or clear):
  a ``learner_card`` verdict and a ``reader_path_sections`` row, nothing else.

Kill switch ``reading_paths.enabled``: off, every RPC here refuses, no call
is made and the prompt contract has no ``reading_paths`` key (today's Guide).
Display only: nothing here writes a plan, evidence, mastery, FSRS,
scheduler state or anything served.
"""
from __future__ import annotations

import logging
import threading
from typing import Any

from learnloop.reader import reader_dialogue as RD
from learnloop.source_retrieval import reading_paths as RP
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
READING_PATH_RPCS: tuple[str, ...] = (
    "reader.reading_path",
    "reader.reading_path_set_depth",
    "reader.reading_path_override",
)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW7a (absent while off)."""

    if not RP.enabled(vault):
        return {}
    return {"reading_paths": {"enabled": True, "depths": [
        {"id": depth, "label": RP.DEPTH_LABELS[depth]} for depth in RP.DEPTHS]}}


def _require(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]:
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    if not RP.enabled(vault):
        raise SidecarError("reading_paths_disabled", "Reading paths are off (reading_paths.enabled = false).")
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    return vault, repository, resolved


# -- the background judgment -------------------------------------------------------------------


class _Judgments:
    """Judgments in flight or failed, by (reading, depth, state key), in memory."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.state: dict[tuple[str, str, str], dict[str, Any]] = {}
        #: Plan-first transport T1: the OpenRouter offer a failed judgment's
        #: request made (a ``plan_fallback`` hint), relayed by each read of it.
        self.offers: dict[tuple[str, str, str], dict[str, Any]] = {}


def _judgments(ctx: SidecarContext) -> _Judgments:
    found = getattr(ctx, "reading_path_judgments", None)
    if found is None:
        found = _Judgments()
        ctx.reading_path_judgments = found  # type: ignore[attr-defined]
    return found


def _start(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, depth: str, state_key: str) -> None:
    judgments = _judgments(ctx)
    key = (extraction_id, depth, state_key)
    with judgments.lock:
        if (judgments.state.get(key) or {}).get("state") == "running":
            return
        judgments.state[key] = {"state": "running"}
    client = getattr(ctx, "reading_path_judge_client", None)
    sqlite_path = repository.sqlite_path

    # T1 landing (redesign D): the job belongs to the action whose request started it,
    # and carries that action's token when it is granted (taken here, in the request).
    from learnloop.ai import plan_fallback as _plan_fallback

    grant, origin = _plan_fallback.unit_token(vault.root), _plan_fallback.unit_origin()
    stamp = _plan_fallback.unit_stamp(vault.root)  # its vault and epoch, now
    _plan_fallback.note_unit("job", f"reading-path:{extraction_id}:{depth}")

    def run() -> None:
        from learnloop.ai import plan_fallback
        from learnloop.ai.execution import record_model_calls
        from learnloop.db.repositories import Repository

        outcome: dict[str, Any] | None
        # Plan-first transport T1: the judgment's thread has no RPC collector;
        # it keeps its own offers and each read of the failed state relays them.
        with plan_fallback.unit(grant, origin, stamp) as offers:
            try:
                worker = Repository.attach(sqlite_path)
                with record_model_calls(worker, owner_kind="sidecar_rpc",
                                        owner_id=f"reader.reading_path:{extraction_id}:{depth}"):
                    result = RP.judge(vault, worker, extraction_id, depth, client=client)
                # ``held``: another process kept its claim past the wait; nothing
                # failed here, the next read finds its rows (or claims again).
                outcome = None if result.status in ("ready", "fresh", "held") else {
                    "state": "failed", "reason": result.reason, "message": result.message}
            except BaseException as exc:  # noqa: BLE001 - a failed judgment answers the view, never the loop
                LOG.warning("reading path judgment failed: %s", type(exc).__name__, exc_info=exc)
                outcome = {"state": "failed", "reason": "judge_failed",
                           "message": "Couldn't read a path for this book just now. Try again ↵"}
        offer = offers.hint() if outcome is not None else None
        with judgments.lock:
            if outcome is None:
                judgments.state.pop(key, None)
            else:
                judgments.state[key] = outcome
            if offer is None:
                judgments.offers.pop(key, None)
            else:
                judgments.offers[key] = offer

    if getattr(ctx, "reading_path_inline", False):
        run()
    else:
        # Owned by the context: its close cancels the job's further requests
        # and joins it, bounded (test-thread-leak review F1).
        from learnloop_sidecar.background_jobs import background_jobs

        background_jobs(ctx).spawn(run, name=f"reading-path-{extraction_id}-{depth}")


def _readmit(ctx: SidecarContext, vault: Any, repository: Any, state_key: tuple[str, str, str],
             current: dict[str, Any]) -> dict[str, Any]:
    """An admission refusal (capped, unpriced, unrouted, models off) holds
    only while its condition does (Codex review F4): each read asks again,
    before any call, against today's envelope and the vault's config now.
    Lifted, the refusal is dropped (the caller judges); still refused, it is
    kept with today's wording. A model failure is not this: it waits for
    "try again"."""

    try:
        problem = RP.admission_problem(vault, repository, client=getattr(ctx, "reading_path_judge_client", None))
    except Exception:  # noqa: BLE001 - an unreadable check keeps the refusal shown
        LOG.warning("reading path admission check failed", exc_info=True)
        return current
    judgments = _judgments(ctx)
    with judgments.lock:
        if judgments.state.get(state_key) != current:
            return dict(judgments.state.get(state_key) or {})  # changed meanwhile: that state stands
        if problem is None:
            judgments.state.pop(state_key, None)
            return {}
        refreshed = {"state": "failed", "reason": problem.reason, "message": problem.message}
        judgments.state[state_key] = refreshed
        return dict(refreshed)


def _view(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, *, judge: bool,
          retry: bool = False) -> dict[str, Any]:
    try:
        inputs = RP.path_inputs(vault, repository, extraction_id)
    except RP.ReadingPathError as exc:
        if exc.code != "withheld":
            raise SidecarError(exc.code, str(exc)) from exc
        return RP.path_view(vault, repository, extraction_id)
    view = RP.path_view(vault, repository, extraction_id, inputs=inputs)
    key = view.get("state_key")
    if key is None or view["status"] == "ready":
        return view
    judgments = _judgments(ctx)
    state_key = (extraction_id, str(view["depth"]), str(key))
    with judgments.lock:
        current = dict(judgments.state.get(state_key) or {})
        if retry and current.get("state") == "failed":
            judgments.state.pop(state_key, None)
            current = {}
    if current.get("state") == "failed" and current.get("reason") in RP.ADMISSION_REASONS:
        current = _readmit(ctx, vault, repository, state_key, current)
    if judge and not current:
        _start(ctx, vault, repository, extraction_id, str(view["depth"]), str(key))
        with judgments.lock:
            current = dict(judgments.state.get(state_key) or {})
    if current.get("state") == "failed":
        from learnloop.ai import plan_fallback

        # Relayed once (review F8): the next read of this failed state shows no banner again.
        with judgments.lock:
            offer = judgments.offers.pop(state_key, None)
        plan_fallback.relay_hint(offer)
    return RP.path_view(vault, repository, extraction_id, inputs=RP.path_inputs(vault, repository, extraction_id),
                        judging=current or None)


class ReadingPathInput(ParamsModel):
    extraction_id: str
    #: Start the judge when the cached path is not the current state's (the
    #: Guide's open and its polls); False reads only.
    judge: bool = True
    #: "Try again" after a failed judgment.
    retry: bool = False


@method("reader.reading_path", ReadingPathInput)
def reader_reading_path(ctx: SidecarContext, params: ReadingPathInput) -> dict[str, Any]:
    """The Guide's reading path for this reading (at once; a judgment runs in the background)."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    return versioned(_view(ctx, vault, repository, resolved, judge=params.judge, retry=params.retry))


class ReadingPathDepthInput(ParamsModel):
    extraction_id: str
    depth: str


@method("reader.reading_path_set_depth", ReadingPathDepthInput)
def reader_reading_path_set_depth(ctx: SidecarContext, params: ReadingPathDepthInput) -> dict[str, Any]:
    """"How deep do you want to go?" for the source; DL2's intent is not written."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    if params.depth not in RP.DEPTHS:
        raise SidecarError("validation_error", f"Unknown depth {params.depth!r}.")
    source_id, _revision = RP.reading_of(repository, resolved)
    RP.set_depth(repository, source_id, params.depth)
    return versioned(_view(ctx, vault, repository, resolved, judge=True))


class ReadingPathOverrideInput(ParamsModel):
    extraction_id: str
    depth: str
    section_id: str
    #: read_anyway | skip | none (clears an earlier choice)
    choice: str


@method("reader.reading_path_override", ReadingPathOverrideInput)
def reader_reading_path_override(ctx: SidecarContext, params: ReadingPathOverrideInput) -> dict[str, Any]:
    """"Read it anyway" / "skip it": kept, and marks nothing as known."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        RP.override(vault, repository, resolved, params.depth, params.section_id, params.choice)
    except RP.ReadingPathError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(_view(ctx, vault, repository, resolved, judge=False))


__all__ = ["READING_PATH_RPCS", "prompt_contract_fields"]
