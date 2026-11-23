"""Reader workbench v2 RD6 RPCs: the goal lens (spec §3.4, §12.2-§12.5, §12.8).

* ``goal.band``: one goal's band: the goal in the learner's words, its LOs as dots in path order with
  readiness from cold checks (demonstrated, likely, untested), the LOs beyond the chosen depth, the
  unmatched phrases, each depth with the size of its path, the due and answered checks, "next for the
  goal", pace (``goals.goal_pace``) and the path's own view (``curriculum.path``'s lines).
* ``goal.lens``: per section of one reading (or of a visible range of it), its level for the goal,
  its mapping state, the why and the learner's part (``curriculum.goal_lens``'s rules).
* ``goal.section_choice``: *read it anyway* (or ``none``) on a section the lens dims. A path line's own
  choices stay ``curriculum.path_override``'s.

Display of the real model: no model call, and nothing is started (the background coverage and path
judgment start where they do today, from ``curriculum.path`` and the Guide). Nothing here writes
evidence, a plan, mastery or scheduler state; the only write is the section choice's ledger verdict.
Desktop only (pinned in tests/test_mobile_allowlist.py). Off with ``curriculum.enabled``, as the path is.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, time
from typing import Any

from pydantic import Field, model_validator

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.intent.inline_checks import answered_checks, due_checks, next_check_due, serving_view
from learnloop.section_map import RangeError
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import goal_lens_choices as choices
from learnloop.source_retrieval import goal_lens_reads as reads
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import deliverables as curriculum
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
GOAL_LENS_RPCS: tuple[str, ...] = ("goal.band", "goal.lens", "goal.section_choice")


def _day_start(clock: Any = None) -> str:
    """Today's first instant on the learner's clock, in UTC as stored stamps are."""

    now = parse_utc(utc_now_iso(clock)) or datetime.now(UTC)
    local = now.astimezone()
    return datetime.combine(local.date(), time.min, tzinfo=local.tzinfo).astimezone(UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _progress(ctx: SidecarContext, goal_id: str) -> reads.Progress:
    """The Guide's background work for this goal, read without starting any (the path view's inputs)."""

    work = curriculum._work(ctx)

    def read(depth: str | None, key: str | None) -> tuple[Any, bool, Any]:
        with work.lock:
            covering = dict(work.covering.get(goal_id) or {})
            judging = dict(work.judging.get((goal_id, depth, key)) or {}) if depth and key else {}
        failure = covering if covering.get("state") == "failed" else None
        return (judging or None), covering.get("state") == "running", failure

    return read


def _settled(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str) -> set[str]:
    """The unjudged LOs this sidecar's coverage already tried for the goal with nothing left to judge (no
    candidate section): their sections are settled. None while it runs, or after it failed."""

    work = curriculum._work(ctx)
    with work.lock:
        state = (work.covering.get(goal_id) or {}).get("state")
        attempted = set(work.attempted.get(goal_id, ()))
    if state in ("running", "failed") or not attempted:
        return set()
    # Settled only against the library it was tried in: a reading added since may hold the LO (RD6's fix round).
    keys = DP.attempt_keys(vault, repository, sorted({lo_id for lo_id, _key in attempted}))
    return {lo_id for lo_id, key in attempted if key == keys.get(lo_id)}


def _checks(vault: Any, repository: Any, goal_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """The due checks, today's answered ones, and when the next check falls due (the band reads again then: a newly
    due check must hide what it covers)."""

    view = serving_view(vault, repository)
    due = due_checks(vault, repository, goal_id=goal_id, view=view)
    answered = answered_checks(vault, repository, since=_day_start())
    return due, answered, next_check_due(view)


def _model(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str,
           due: list[dict[str, Any]], answered: list[dict[str, Any]]) -> reads.GoalModel:
    try:
        return reads.read_goal(vault, repository, goal_id, held={row["lo_id"] for row in due},
                               answered={row["lo_id"] for row in answered}, settled=_settled(ctx, vault, repository, goal_id),
                               progress=_progress(ctx, goal_id))
    except DL.DeliverableError as exc:
        raise curriculum._error(exc) from exc


def _not_a_deliverable(vault: Any, goal_id: str) -> dict[str, Any] | None:
    """A goal the learner did not make (it has no deliverable to map): the band says so, the lens is off."""

    goal = next((goal for goal in vault.goals if goal.id == goal_id), None)
    if goal is None:
        raise SidecarError("not_found", f"No goal {goal_id!r}.")
    if goal.creation_source == "learner":
        return None
    return {"goal_id": goal_id, "goal": reads.goal_view(goal), "status": "not_a_deliverable",
            "message": "LearnLoop maps only goals you set yourself to your sources."}


def _pace(vault: Any, repository: Any, goal: Any) -> dict[str, Any] | None:
    from learnloop.goals.goal_pace import compute_goal_pace
    from learnloop.goals.goal_projection import goal_report

    try:
        return compute_goal_pace(vault, repository, goal, goal_report(vault, repository, goal)).as_dict()
    except Exception:  # noqa: BLE001 - an unreadable pace shows no pace line, never a made-up one
        LOG.warning("goal pace unreadable for %s", goal.id, exc_info=True)
        return None


class GoalBandInput(ParamsModel):
    goal_id: str = Field(min_length=1)


@method("goal.band", GoalBandInput)
def goal_band(ctx: SidecarContext, params: GoalBandInput) -> dict[str, Any]:
    """The goal band (§12.2) and the path view's data (§12.5)."""

    vault, repository = curriculum._require_read(ctx)
    other = _not_a_deliverable(vault, params.goal_id)
    if other is not None:
        return versioned(other)
    due, answered, next_due = _checks(vault, repository, params.goal_id)
    model = _model(ctx, vault, repository, params.goal_id, due, answered)
    work = curriculum._work(ctx)
    with work.lock:
        covering = dict(work.covering.get(params.goal_id) or {})
    progress = {"covering": covering.get("state") == "running",
                "failure": ({"reason": covering.get("reason"), "message": covering.get("message")}
                            if covering.get("state") == "failed" else None)}
    band = reads.band_view(vault, repository, model, due=due, answered=answered,
                           protection=reads.protection(vault, repository, due, model),
                           likely=curriculum._likely(vault, repository), pace=_pace(vault, repository, model.goal),
                           progress=progress)
    return versioned({**band, "next_check_due": next_due})


class GoalLensInput(ParamsModel):
    goal_id: str = Field(min_length=1)
    extraction_id: str = Field(min_length=1)
    from_span_id: str | None = None
    to_span_id: str | None = None
    t0: float | None = Field(default=None, ge=0)
    t1: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _range(self) -> GoalLensInput:
        spans = (self.from_span_id is None) == (self.to_span_id is None)
        times = (self.t0 is None) == (self.t1 is None)
        both = self.from_span_id is not None and self.t0 is not None
        if not spans or not times or both:
            raise ValueError("a range is two passages (from_span_id, to_span_id), two times (t0, t1) or none "
                             "(the whole reading)")
        return self


@method("goal.lens", GoalLensInput)
def goal_lens(ctx: SidecarContext, params: GoalLensInput) -> dict[str, Any]:
    """Each section's level for the goal across one reading, or the visible range of it (§12.3)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.reader import reader_dialogue as RD
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = curriculum._require_read(ctx)
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    other = _not_a_deliverable(vault, params.goal_id)
    if other is not None:
        return versioned({**other, "extraction_id": resolved, "mapping": "unmapped", "levels": []})
    due, answered, _next_due = _checks(vault, repository, params.goal_id)
    model = _model(ctx, vault, repository, params.goal_id, due, answered)
    try:
        return versioned(reads.lens_view(vault, repository, model, resolved,
                                         protection=reads.protection(vault, repository, due, model),
                                         from_span_id=params.from_span_id,
                                         to_span_id=params.to_span_id, t0=params.t0, t1=params.t1))
    except RangeError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


class SectionChoiceInput(ParamsModel):
    goal_id: str = Field(min_length=1)
    extraction_id: str = Field(min_length=1)
    section_id: str = Field(min_length=1)
    #: read_anyway | none
    choice: str
    #: Client-minted: a retry returns the stored choice.
    operation_id: str


@method("goal.section_choice", SectionChoiceInput)
def goal_section_choice(ctx: SidecarContext, params: SectionChoiceInput) -> dict[str, Any]:
    """*Read it anyway* on a section the lens dims, for this goal (``none`` clears it)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    vault, repository = curriculum._require(ctx)
    try:
        DL.goal_of(vault, params.goal_id)
    except DL.DeliverableError as exc:
        raise curriculum._error(exc) from exc
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    try:
        return versioned({"choice": choices.choose(repository, params.goal_id, resolved, params.section_id,
                                                   params.choice, operation_id=params.operation_id)})
    except choices.ChoiceError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


__all__ = ["GOAL_LENS_RPCS"]
