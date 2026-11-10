"""Reader RW5d P5: the desktop sidecar's prefetch runtime (spec_reader_show_me_figures_v1 §10b.1, §10b.4).

The five trigger hooks call :func:`notify` from the RPCs they belong to
(``get_daily_plan``, ``reader.mark_section_progress``, the tutor's and the
library organizer's answers, ``lesson.turn``, and the gap worker's nonempty
drains). It returns at once: the trigger is queued and one background thread of
this context (``ctx.background_jobs``: a close cancels and joins it) drains
the queue, one pass at a time (:func:`learnloop.figures.prefetch.run_trigger`).

A hook passes ``learner_activity=True`` only when the RPC is the learner's own
action (follow-ups batch 6, Codex verify V2; only such a pass retries a
prebuild's plan wait): section progress, an offer (once per question they
asked), a lesson's turn. Not ``get_daily_plan`` (Today's queue-revision poll
refetches it when background work lands) and not the gap worker's drain.

Never in the phone or MCP hosts (a secondary context) and never with
``figures.prefetch_enabled`` off: then nothing is queued, read, written or
called, so the RPCs behave exactly as before P5. ``ctx.figure_prefetch_inline``
runs the pass on the calling thread (tests); ``ctx.figure_prefetch_judge_client``
is the judge's injected client (tests; unset: the route as configured).
"""

from __future__ import annotations

import logging
import os
import threading
from collections import deque
from typing import Any

from learnloop import provenance
from learnloop.figures import power as P

_LOG = logging.getLogger(__name__)


class PrefetchRuntime:
    """One context's trigger queue and its single drain thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        #: ``(trigger, trace)``: each trigger with the trace of the request that queued it. One drain thread runs
        #: the passes of many requests, so the thread's own trace (the first submitter's) names none but the first.
        self._queue: deque[tuple[Any, str | None]] = deque()
        self._running = False
        self.results: list[Any] = []
        #: Offers already turned into a trigger (a finished job is read more than once).
        self.offers_seen: set[tuple[str, str]] = set()

    def running(self) -> bool:
        """A pass is draining the queue now (Codex re-review F18: the Reader's ``prefetchPending``)."""

        with self._lock:
            return self._running

    def submit(self, ctx: Any, trigger: Any) -> None:
        with self._lock:
            if any(queued == trigger for queued, _trace in self._queue):
                return
            self._queue.append((trigger, provenance.current_trace()))
            if self._running:
                return
            self._running = True
        if getattr(ctx, "figure_prefetch_inline", False):
            self._drain(ctx, None)
            return
        jobs = ctx.background_jobs
        epoch = jobs.epoch()
        jobs.spawn(lambda: self._drain(ctx, epoch), name="figure-prefetch", epoch=epoch)

    def _drain(self, ctx: Any, epoch: int | None) -> None:
        from learnloop.figures import prefetch as PF

        try:
            while True:
                with self._lock:
                    if not self._queue:
                        self._running = False
                        return
                    trigger, trace = self._queue.popleft()
                env = environment(ctx, epoch)
                if env is None:
                    continue
                try:
                    with provenance.trace_scope(trace):
                        self.results.append(PF.run_trigger(env, trigger))
                except Exception:  # noqa: BLE001 - background work never fails the sidecar
                    _LOG.warning("a figure prefetch pass failed", exc_info=True)
        except BaseException:
            with self._lock:
                self._running = False
            raise


def environment(ctx: Any, epoch: int | None) -> Any:
    """The pass's environment from the context as loaded now (None: no vault, or switched off)."""

    from learnloop.figures import prefetch as PF
    from learnloop_sidecar.handlers.figures import _rich_spawner, retry_plan_wait

    vault, repository = getattr(ctx, "vault", None), getattr(ctx, "repository", None)
    if vault is None or repository is None or not PF.enabled(vault):
        return None
    jobs = ctx.background_jobs

    def cancelled() -> bool:
        return epoch is not None and jobs.closed_since(epoch)

    from learnloop.figures import service as FS

    spawn = _rich_spawner(ctx, vault, granted=False) if FS.rich_enabled(vault) else None
    return PF.PrefetchEnv(
        vault=vault, repository=repository, judge_client=getattr(ctx, "figure_prefetch_judge_client", None),
        author_client=getattr(ctx, "figure_author_client", None), spawn_rich=spawn,
        find=getattr(ctx, "figure_find_sources", None), live_vault=ctx.loaded_vault,
        rng=getattr(ctx, "figure_prefetch_rng", None), pause_reader=getattr(ctx, "figure_prefetch_pause_reader", None),
        cancelled=cancelled, passages=getattr(ctx, "figure_prefetch_passages", None),
        # Follow-ups batch 6 (D, P5 F17): the pass asks the plan again for prebuilds' rich jobs
        # left waiting for it, paced as the Reader's reads do, whether or not the Reader polls.
        retry_plan_wait=lambda job_id: retry_plan_wait(ctx, job_id))


def _runtime(ctx: Any) -> PrefetchRuntime:
    runtime = ctx.__dict__.get("figure_prefetch")
    if runtime is None:
        runtime = PrefetchRuntime()
        ctx.figure_prefetch = runtime
    return runtime


#: ``LEARNLOOP_FIGURE_PREFETCH=off``: no trigger is queued unless the context injected the
#: prefetch runtime's test seams (``figure_prefetch_inline``); the test suite sets it, as it
#: sets ``LEARNLOOP_APPROACH_MAP_BUILDS``, so no test starts a background pass by accident.
PREFETCH_ENV = "LEARNLOOP_FIGURE_PREFETCH"


def runs_here(ctx: Any) -> bool:
    """Whether prefetch runs in this context now (the desktop sidecar, the switch on, the env)."""

    vault = getattr(ctx, "vault", None)
    if vault is None or getattr(ctx, "secondary", False) or not P.prefetch_switch(vault):
        return False
    if os.environ.get(PREFETCH_ENV, "").strip().lower() == "off" \
            and not ctx.__dict__.get("figure_prefetch_inline", False):
        return False
    return True


def pass_running(ctx: Any) -> bool:
    """Whether this context's prefetch pass is running now (never creates the runtime)."""

    runtime = getattr(ctx, "__dict__", {}).get("figure_prefetch")
    return bool(runtime is not None and runtime.running())


def notify(ctx: Any, kind: str, ref: str = "", **fields: Any) -> bool:
    """Queue one trigger (spec §10b.2); False when prefetch does not run here (switched off, a
    phone or MCP host, no vault). Never raises: a hook never fails its RPC. ``fields`` are the
    trigger's, ``learner_activity`` among them (module docstring)."""

    try:
        if not runs_here(ctx):
            return False
        from learnloop.figures.prefetch import Trigger

        blocks = tuple((str(key[0]), str(key[1])) for key in fields.pop("blocks", ()) or ())
        trigger = Trigger(kind=kind, ref=str(ref or ""), blocks=blocks, **fields)  # type: ignore[arg-type]
        _runtime(ctx).submit(ctx, trigger)
        return True
    except Exception:  # noqa: BLE001 - a trigger never fails the RPC that fired it
        _LOG.warning("figure prefetch trigger %s not queued", kind, exc_info=True)
        return False


def notify_offer(ctx: Any, origin: str, offer_ref: str | None) -> bool:
    """RW5b's offers (spec §10b.2): the blocks the tutor's answer or the library organizer's notes
    said were explorable, confirmed by their ledger rows (the press's own check), queued once per
    offer as an ``offer`` trigger."""

    try:
        vault, repository = getattr(ctx, "vault", None), getattr(ctx, "repository", None)
        if (vault is None or repository is None or not offer_ref or not runs_here(ctx)
                or not vault.config.figures.offers_enabled):
            return False
        runtime = _runtime(ctx)
        key = (origin, str(offer_ref))
        if key in runtime.offers_seen:
            return False
        from learnloop_sidecar.handlers.figures import offered_spans

        blocks = sorted(offered_spans(vault, repository, origin, offer_ref))
        runtime.offers_seen.add(key)
        if not blocks:
            return False
        # The offer answers the learner's own question, and fires once per question.
        return notify(ctx, "offer", f"{origin}:{offer_ref}", blocks=blocks, learner_activity=True)
    except Exception:  # noqa: BLE001 - a trigger never fails the RPC that fired it
        _LOG.warning("figure prefetch offer trigger not queued", exc_info=True)
        return False


__all__ = ["PREFETCH_ENV", "PrefetchRuntime", "environment", "notify", "notify_offer", "pass_running", "runs_here"]
