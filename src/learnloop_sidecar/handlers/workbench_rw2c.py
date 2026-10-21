"""Reader workbench RW2c RPCs: what helps this learner (spec_reader_workbench_v1 §5.10, G39, G40).

The adapter around :mod:`learnloop.workbench.route_example`,
:mod:`learnloop.workbench.passage_draw` and
:mod:`learnloop.workbench.compare_methods`. Desktop only (pinned in
``tests/test_mobile_allowlist.py``). Every RPC goes through RW2b's guard
(``workbench.help_enabled``, ``workbench.enabled``) and then its own switch,
refusing before reading or writing anything:

* ``workbench.show_example``: "Show me a similar example" on the step in
  focus (a job, read with ``workbench.help_job``); ``examples_unavailable``
  while ``workbench.examples_enabled`` is off or the sources spec's S3 is
  absent;
* ``workbench.another_passage``: the next option of a shown bridge or
  example whose draw logged options (no search, no call; a learner pick);
* ``workbench.compare_offer``: whether "Compare with the book's method" is
  offered for an attempt (after a correct Submit of a workbench problem);
* ``workbench.compare_methods``: open the comparison (its row and its reveal
  on the item in one transaction, then the reference and the learner's
  steps at once) and start its lines (a job on ``workbench_check``'s route).

The worked example after a level-3+ hint starts from the hint's delivery in
:mod:`learnloop_sidecar.handlers.workbench_help` (:func:`start_example_after_hint`).
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import Field

from learnloop.reader import workbench as WB
from learnloop.workbench import check as check_module
from learnloop.workbench import ladder as help_module
from learnloop.workbench import route_example
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import workbench_help as help_rpcs
from learnloop_sidecar.registry import method

#: How long the example after a hint waits for its sibling bridge job before
#: taking its own place among the problem's calls (the bridge, RW2b's, goes
#: first; past this the bridge's row is long written, F9).
BRIDGE_WAIT_SECONDS = 60.0

#: Every RPC this module registers (pinned desktop-only).
WORKBENCH_RW2C_RPCS: tuple[str, ...] = (
    "workbench.show_example",
    "workbench.another_passage",
    "workbench.compare_offer",
    "workbench.compare_methods",
)


def _start_job(ctx: SidecarContext, kind: str, session_id: str, item_id: str,
               work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> str:
    job = help_rpcs._jobs(ctx).start(ctx, item_id, work)
    help_rpcs._meta(ctx)[job.job_id] = help_rpcs._JobMeta(kind, session_id, item_id)
    return job.job_id


def _example_work(ctx: SidecarContext, vault: Any, *, session_id: str, item: Any, trigger: str,
                  about_step_id: str | None, hint_assist_id: str | None, after: Any | None = None):
    find = getattr(ctx, "workbench_example_find", None)

    def work(worker_repo: Any, _cancelled: Callable[[], bool]) -> dict[str, Any]:
        if after is not None:
            # The bridge takes its place among the problem's calls first, so
            # under the per-problem cap an example never displaces it.
            after.done.wait(BRIDGE_WAIT_SECONDS)
        steps = help_module.live_workbench_steps(worker_repo, session_id)
        return route_example.example_for(
            vault, worker_repo, workbench_session_id=session_id, item=item, steps=steps, trigger=trigger,
            about_step_id=about_step_id, hint_assist_id=hint_assist_id,
            submission_id=WB.submission_id_for(session_id), find=find,
            envelope=check_module.daily_envelope(vault, worker_repo),
            max_calls=int(vault.config.workbench.max_calls_per_session),
            draw_enabled=bool(vault.config.workbench.passage_draw_enabled),
            seed=getattr(ctx, "passage_draw_seed", None))

    return work


def start_example_after_hint(ctx: SidecarContext, meta: Any, result: dict[str, Any], *,
                             after_job_id: str | None = None) -> str | None:
    """After a shown hint at level 3 or higher in the Reader, the example in
    the background (never delaying the hint); None when it does not apply.
    ``after_job_id``: the hint's bridge job, which runs first."""

    vault, repository = ctx.require_vault()
    if not route_example.available(vault):
        return None
    level = result.get("level")
    if level is None or int(level) < route_example.MIN_HINT_LEVEL:
        return None
    try:
        session = WB.session_row(repository, meta.session_id)
    except WB.WorkbenchError:
        return None
    item = vault.practice_items.get(meta.practice_item_id)
    if session.get("origin") != "reader" or item is None:
        return None
    if check_module.session_calls(repository, meta.session_id) >= int(vault.config.workbench.max_calls_per_session):
        return None
    return _start_job(ctx, help_rpcs.EXAMPLE, meta.session_id, item.id, _example_work(
        ctx, vault, session_id=meta.session_id, item=item, trigger="after_hint", about_step_id=None,
        hint_assist_id=str(result["assist_id"]),
        after=help_rpcs._jobs(ctx).get(after_job_id) if after_job_id else None))


class ShowExampleInput(ParamsModel):
    session_id: str = Field(min_length=1)
    focused_step_id: str | None = None


@method("workbench.show_example", ShowExampleInput)
def show_example(ctx: SidecarContext, params: ShowExampleInput) -> dict[str, Any]:
    """"Show me a similar example" (§5.10): a job, read with ``workbench.help_job``."""

    vault, repository, session, item = help_rpcs._require(ctx, params.session_id)
    if not route_example.available(vault) or session.get("origin") != "reader":
        raise SidecarError("examples_unavailable",
                           "Worked examples from your books aren't available here "
                           "(workbench.examples_enabled, or the sources service).")
    context = help_module.hint_context(vault, repository, session, focused_step=params.focused_step_id)
    job_id = _start_job(ctx, help_rpcs.EXAMPLE, params.session_id, item.id, _example_work(
        ctx, vault, session_id=params.session_id, item=item, trigger="show_me", about_step_id=context.about,
        hint_assist_id=None))
    return help_rpcs._payload(ctx, job_id)


class AnotherPassageInput(ParamsModel):
    session_id: str = Field(min_length=1)
    assist_id: str = Field(min_length=1)


@method("workbench.another_passage", AnotherPassageInput)
def another_passage(ctx: SidecarContext, params: AnotherPassageInput) -> dict[str, Any]:
    """"another passage": the next of a draw's options (no search, no call)."""

    from learnloop.clock import utc_now_iso
    from learnloop.workbench import passage_draw
    from learnloop.workbench.bridge import COMPARE_LINE

    vault, repository, _session, _item = help_rpcs._require(ctx, params.session_id, open_=False)
    if not bool(vault.config.workbench.passage_draw_enabled):
        raise SidecarError("no_alternatives", "Other passages are switched off (workbench.passage_draw_enabled).")

    def line_for(option: dict[str, Any], placement: dict[str, Any]) -> str:
        if placement.get("trigger") or placement.get("role") == "worked_example":
            return route_example.example_line(option, placement.get("step_number"))
        return COMPARE_LINE.format(label=str(option.get("label") or "a passage")[:120])

    try:
        row = passage_draw.another_passage(repository, workbench_session_id=params.session_id,
                                           assist_id=params.assist_id, line_for=line_for, shown_at=utc_now_iso())
    except passage_draw.NoAlternative as exc:
        raise SidecarError("no_alternatives", "There is no other passage to show here.",
                           details={"reason": str(exc)}) from exc
    view = route_example.example_view(row) if row["assist_kind"] == "example" else help_module.bridge_view(row)
    return versioned(to_camel({"passage": view, "kind": row["assist_kind"]}))


class CompareInput(ParamsModel):
    attempt_id: str = Field(min_length=1)


@method("workbench.compare_offer", CompareInput)
def compare_offer(ctx: SidecarContext, params: CompareInput) -> dict[str, Any]:
    """Whether "Compare with the book's method" is offered for the attempt."""

    from learnloop.workbench import compare_methods

    vault, repository = help_rpcs._guard(ctx)
    return versioned(to_camel(compare_methods.offer(vault, repository, params.attempt_id)))


@method("workbench.compare_methods", CompareInput)
def open_compare_methods(ctx: SidecarContext, params: CompareInput) -> dict[str, Any]:
    """Open the comparison: the reveal on the item is written with its row
    BEFORE the reference is returned; the lines follow as a job."""

    from learnloop.workbench import compare_methods

    vault, repository = help_rpcs._guard(ctx)
    try:
        comparison = compare_methods.open_comparison(vault, repository, params.attempt_id)
    except compare_methods.CompareRefused as exc:
        raise SidecarError("compare_unavailable", "Comparing methods isn't available for this answer.",
                           details={"reason": exc.reason}) from exc
    except Exception as exc:  # noqa: BLE001 - the reveal could not be written: nothing is shown
        raise SidecarError("compare_unavailable", "Couldn't open the comparison just now.",
                           details={"reason": type(exc).__name__}) from exc
    assist_id = str(comparison["assist_id"])
    with repository.connection() as connection:
        from learnloop.db.stores.help_assists import assist

        row = assist(connection, assist_id)
    client = getattr(ctx, "workbench_check_client", None)

    def work(worker_repo: Any, cancelled: Callable[[], bool]) -> dict[str, Any]:
        return compare_methods.compare_lines(vault, worker_repo, assist_id, client=client, cancelled=cancelled)

    job_id = None
    if comparison.get("lines") is None and row is not None:
        # Review F7: one generation per comparison. A reopen while its job is
        # pending (or done with the lines) is handed that job; a new job starts
        # only when none is kept or the last one ended without lines. The row's
        # own claim (compare_methods) keeps any second worker from calling.
        kept = _compare_jobs(ctx)
        previous = kept.get(assist_id)
        job = help_rpcs._jobs(ctx).get(previous) if previous else None
        if job is not None and not job.cancelled and (
                not job.done.is_set() or (job.error is None and (job.result or {}).get("status") == "ready")):
            job_id = previous
        else:
            job_id = _start_job(ctx, help_rpcs.COMPARE, str(row["workbench_session_id"]),
                                str(row["practice_item_id"]), work)
            kept[assist_id] = job_id
    return versioned(to_camel({"comparison": comparison, "lines_job_id": job_id}))


def _compare_jobs(ctx: SidecarContext) -> dict[str, str]:
    """The comparison lines job kept for each comparison (assist id -> job id)."""

    kept = getattr(ctx, "workbench_compare_jobs", None)
    if kept is None:
        kept = {}
        ctx.workbench_compare_jobs = kept  # type: ignore[attr-defined]
    return kept


__all__ = ["WORKBENCH_RW2C_RPCS", "start_example_after_hint"]
