"""Reader RW5d P4b: the teacher's manipulatives (``spec_reader_show_me_figures_v1`` §6.5, §10.4;
``spec_teacher_v1`` §8.2, §10 "Instruments over description").

With ``teacher.visuals`` on (and figures and "show me" on, and the lesson's host able to build a
figure), a teacher turn may carry a ``visual`` and ``write_plan`` nodes a planned one
(:mod:`.contracts`). Code completes the teacher's words into a ``FigureRequestV1``:

* origin ``teacher``, ``goal_author`` ``teacher`` (never the client's; G-SM5), the goal the
  teacher wrote from the brief;
* host: the lesson (``lesson_id`` and the step's node), caller kind ``teacher`` with the lesson's
  derived policy (``reading``; ``assisted_practice`` bound to the minted item while a lesson check
  is open: :func:`learnloop.teacher.actions.caller_for`);
* grounding: the delivered passages the teacher named, as fixed keys (no retrieval). The figure
  service refuses the whole request when any of them is exam or held-out material now, before
  any call (the one predicate); a lesson figure has no home in the Reader;
* tiers: grammar and sketch (:data:`learnloop.figures.service.LESSON_TIERS`): the turn waits on
  its figure, so no rich (queued, minutes-long) tier is offered in a lesson.

The figure renders in the turn. **Its own predictions are suppressed in a lesson** (the teacher
poses the prediction or the check): the lesson's view of a figure carries none, and the desktop's
lesson figure has the predictions contract off. **A figure never feeds certification**: the grader
sees a check's question text only (the minted item; ``teacher.checks`` imports no figure code), no
``figure_predictions`` row is written from a lesson, and no figure is evidence. Its words are
accounted as the lesson's exposure (reveal rows, basis ``lesson:<id>``) when it is shown, and it is
not shown when they give away the open check's solution or a vault item's key (the lesson's guards
on the figure's text, fail closed).

Off (``teacher.visuals`` false, figures or "show me" off, or no figure builder): the teacher's
prompt and turn schema are TE1's byte for byte (:data:`PROMPT_VERSION` and the doctrine unchanged),
no figure is built, and the lesson's view shows none.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from learnloop.teacher.contracts import PROMPT_VERSION, TeacherTurnV1, TeacherTurnVisualsV1

#: The visuals paragraph's version (recorded on every turn and receipt that used it).
VISUALS_VERSION = "teacher_visuals_v1"
#: The teacher prompt's identity with the paragraph (TE1's ``PROMPT_VERSION`` exactly when off).
VISUALS_PROMPT_VERSION = f"{PROMPT_VERSION}+visuals-v1"
_PARAGRAPH = Path(__file__).resolve().parent / "doctrine" / "visuals" / "v1.md"

#: A lesson figure's state as the lesson records it.
SHOWN = "shown"
FAILED = "failed"
WITHHELD = "withheld"
UNAVAILABLE = "unavailable"
STATUSES = (SHOWN, FAILED, WITHHELD, UNAVAILABLE)

#: ``FigureRequest -> BuildOutcome``: the host's figure builder (the sidecar's figure service with
#: its author route and live configuration; a fake in tests). None: the host builds no figure.
Builder = Callable[[Any], Any]


def active(vault: Any) -> bool:
    """``teacher.visuals``, under ``figures.enabled`` and ``figures.show_me_enabled`` (a teacher's
    figure is a goal, which "show me" governs: spec §7.1)."""

    from learnloop.figures import service as FS

    return FS.teacher_visuals_switch(vault) and FS.enabled(vault) and FS.show_me_enabled(vault)


def on(vault: Any, builder: Builder | None) -> bool:
    """Whether this lesson call offers visuals: the switches, and a host that can build a figure."""

    return builder is not None and active(vault)


@lru_cache(maxsize=1)
def paragraph() -> str:
    """The doctrine's visuals paragraph (versioned; appended to the doctrine only when on)."""

    return _PARAGRAPH.read_text(encoding="utf-8").strip() + "\n"


def instructions(doctrine: str, visuals: bool) -> str:
    return doctrine if not visuals else f"{doctrine}\n{paragraph()}"


def prompt_version(visuals: bool) -> str:
    return VISUALS_PROMPT_VERSION if visuals else PROMPT_VERSION


def turn_model(visuals: bool) -> type[TeacherTurnV1]:
    """The strict output schema of a turn: TE1's off, with the ``visual`` on."""

    return TeacherTurnVisualsV1 if visuals else TeacherTurnV1


def stored_turn(data: Mapping[str, Any] | None) -> TeacherTurnV1:
    """A stored accepted turn, read back (TE1's shape, the visuals shape and TE2-log's episode fields all
    validate: the widest stored shape)."""

    from learnloop.teacher.contracts import TeacherTurnVisualsEpisodesV1

    return TeacherTurnVisualsEpisodesV1.model_validate(dict(data or {}))


# --- the turn's visual ---------------------------------------------------------------------------


def _plan_visual(state: Any, turn_obj: TeacherTurnV1, node_id: str) -> Any | None:
    """The planned visual of ``node_id``: this turn's own ``write_plan`` first, else the stored plan."""

    for request in turn_obj.requests:
        if request.action == "write_plan":
            for node in request.plan:
                if node.id == node_id:
                    return getattr(node, "visual", None)
    plan = state.plans[-1]["outline"] if state.plans else []
    for node in plan:
        if node.get("id") == node_id and node.get("visual"):
            from learnloop.teacher.contracts import PlannedVisualV1

            return PlannedVisualV1.model_validate(node["visual"])
    return None


def resolve(state: Any, turn_obj: TeacherTurnV1) -> dict[str, Any] | None:
    """The turn's visual as code builds it: ``{goal, anchors, node, planned}``, or None (none asked)."""

    visual = getattr(turn_obj, "visual", None)
    if visual is None:
        return None
    if visual.planned_node:
        planned = _plan_visual(state, turn_obj, visual.planned_node)
        if planned is None:
            return {"goal": "", "anchors": [], "node": visual.planned_node, "planned": True}
        return {"goal": planned.goal, "anchors": list(planned.anchors), "node": visual.planned_node, "planned": True}
    node = None
    if turn_obj.check is not None:
        node = turn_obj.check.node
    elif turn_obj.prediction is not None:
        node = turn_obj.prediction.node
    return {"goal": visual.goal, "anchors": list(visual.anchors), "node": node, "planned": False}


def _anchor_problem(state: Any, anchors: Sequence[str], where: str) -> str | None:
    """By location (TE2-log landing, ruling R1 (b)): the anchors' indices, never their text."""

    if not anchors:
        return f"{where} needs one to three anchors: passage aliases you were given (S3)"
    unknown = [index for index, alias in enumerate(anchors) if not state.book.available(alias)]
    if unknown:
        named = ", ".join(f"{where}.anchors[{index}]" for index in unknown)
        return f"{named}: never delivered to you as passages"
    return None


def contract_problem(state: Any, turn_obj: TeacherTurnV1) -> str | None:
    """A visual or planned visual the lesson cannot build, as a correctable refusal (None: fine), naming the field
    by its location (request and node index), never by the model's text."""

    for index, request in enumerate(turn_obj.requests):
        if request.action != "write_plan":
            continue
        for position, node in enumerate(request.plan):
            planned = getattr(node, "visual", None)
            if planned is not None:
                problem = _anchor_problem(state, planned.anchors, f"requests[{index}].plan[{position}].visual")
                if problem:
                    return problem
    visual = getattr(turn_obj, "visual", None)
    if visual is None:
        return None
    if visual.planned_node:
        if visual.goal.strip() or visual.anchors:
            return "a visual names planned_node alone (the node's planned visual), or a goal with anchors, not both"
        resolved = resolve(state, turn_obj) or {}
        if not resolved.get("goal"):
            return "visual.planned_node: names no plan node with a planned visual"
        return _anchor_problem(state, resolved["anchors"], "visual.planned_node's visual")
    if not visual.goal.strip():
        return "a visual needs a goal: which quantity the learner moves, which stay fixed, what to watch"
    return _anchor_problem(state, visual.anchors, "visual")


def displayed(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]:
    """The visual goals a turn may show the learner (the figure's line quotes its goal): the turn's
    own and every planned one, so each passes the lesson's guards before it is stored."""

    out: list[tuple[str, str]] = []
    visual = getattr(turn_obj, "visual", None)
    if visual is not None and visual.goal:
        out.append(("visual", visual.goal))
    for request in turn_obj.requests:
        if request.action == "write_plan":
            out.extend(("plan", node.visual.goal) for node in request.plan if getattr(node, "visual", None))
    return out


# --- building it ---------------------------------------------------------------------------------


def figure_request(state: Any, resolved: Mapping[str, Any], *, caller: Any) -> Any:
    """The ``FigureRequestV1`` code completes from the teacher's words (module docstring). ``caller``:
    the lesson's caller context (:func:`learnloop.teacher.actions.caller_for`, passed in by the service,
    so this module never imports the read actions, which reach the notes' code)."""

    from learnloop.figures.service import FigureRequest

    keys = []
    for alias in resolved["anchors"]:
        passage = state.book.passages[alias]
        keys.append((str(passage["extraction_id"]), str(passage["span_id"])))
    host_ref = {"lesson_id": state.lesson_id, **({"node_id": str(resolved["node"])} if resolved.get("node") else {})}
    return FigureRequest(extraction_id=None, span_ids=[], origin="teacher", goal_text=str(resolved["goal"]),
                         goal_author="teacher", reading_at=None, host_ref=host_ref, caller=caller,
                         grounding_keys=keys)


#: The figure route's "cannot be called now" refusals (``learnloop.figures.routes.FigureUnavailable``).
_UNAVAILABLE = frozenset({"unavailable", "unrouted", "unpriced", "capped", "models_off", "not_isolated"})


def _budget_refused(state: Any, exc: BaseException) -> bool:
    """The LESSON's spend envelope refused a request of the build (§17): the lesson closes ``budget``.

    Only the lesson's own gate says so (its ``refusal``). A ``SpendLimitExceeded`` from anywhere else, the
    figures' daily envelope (``figures.max_daily_cost_usd``, which the figure service reports as
    ``capped``) above all, only leaves this visual unavailable and the lesson goes on (followups batch 5,
    E: any ``SpendLimitExceeded`` in the chain used to close the whole lesson)."""

    gate = getattr(state, "gate", None)
    return gate is not None and getattr(gate, "refusal", None) is not None


def _base(resolved: Mapping[str, Any]) -> dict[str, Any]:
    return {"node": resolved.get("node"), "goal": resolved.get("goal"), "planned": bool(resolved.get("planned")),
            "version": VISUALS_VERSION}


def not_built_for_protection(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """The record of a visual not built because the lesson's protection state changed since its brief
    (Codex review F1): its saved goal may carry words of a passage that is now exam or held-out material,
    which the figure service's check of the visual's own anchors cannot see, so nothing is sent."""

    return {**_base(resolved), "status": WITHHELD, "code": "protection_changed",
            "reason": "some of what this lesson relied on is now kept for your exam, so the figure isn't built"}


def build(vault: Any, repository: Any, state: Any, resolved: Mapping[str, Any], builder: Builder, *,
          caller: Any) -> dict[str, Any]:
    """Build the step's figure: ``{status, figure_id?, reason?, code?}`` (never raises a refusal; a spend
    refusal of the lesson's envelope propagates, so the lesson closes with ``budget``)."""

    from learnloop.figures import service as FS

    base = _base(resolved)
    try:
        outcome = builder(figure_request(state, resolved, caller=caller))
    except FS.FigureRefused as exc:
        if _budget_refused(state, exc):
            raise
        status = WITHHELD if exc.code == "exam_material" else (
            UNAVAILABLE if exc.code in _UNAVAILABLE else FAILED)
        return {**base, "status": status, "code": exc.code, "reason": str(exc.message)[:300]}
    except Exception as exc:  # noqa: BLE001 - a figure that cannot be built never fails the lesson's turn
        if _budget_refused(state, exc):
            raise
        from learnloop.ai.errors import AIProviderUnavailable

        unavailable = isinstance(exc, AIProviderUnavailable) or "unavailable" in type(exc).__name__.lower()
        return {**base, "status": UNAVAILABLE if unavailable else FAILED, "code": type(exc).__name__,
                "reason": "the figure couldn't be built just now"}
    view = getattr(outcome, "view", None)
    if not view or not view.get("figure_id"):
        return {**base, "status": FAILED, "code": "no_figure", "reason": "no figure was built"}
    figure_id = str(view["figure_id"])
    if view.get("verification") not in ("verified", "illustrative") or view.get("tier") == "manim":
        return {**base, "status": FAILED, "figure_id": figure_id, "code": str(view.get("verification")),
                "reason": str(view.get("reason") or view.get("label") or "")[:300]}
    return {**base, "status": SHOWN, "figure_id": figure_id}


def figure_row(repository: Any, figure_id: str) -> dict[str, Any] | None:
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores import figures as store

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.figure(connection, figure_id) if store.has_tables(connection) else None


def figure_text(row: Mapping[str, Any] | None) -> str:
    """The figure's words and displayed values as the lesson shows it (P3's reveal text over the stored
    spec or program **without its predictions**: a lesson suppresses them, :func:`lesson_view`), so a
    hidden prediction's prompt is neither exposure nor a reason to withhold the figure (Codex review F2)."""

    from learnloop.figures.help import reveal_text

    row = dict(row or {})
    raw = row.get("spec_json")
    if raw:
        try:
            data = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (TypeError, ValueError):
            data = None
        if isinstance(data, dict) and "predictions" in data:
            row["spec_json"] = json.dumps({key: value for key, value in data.items() if key != "predictions"})
    return reveal_text(row)


def summary(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """What the teacher is told a shown figure is: its tier, what it demonstrates and what the learner
    can move (names, labels, ranges and defaults), read from the stored spec or program."""

    if not row or not row.get("spec_json"):
        return None
    try:
        data = json.loads(row["spec_json"])
    except (TypeError, ValueError):
        return None
    controls = [{key: parameter.get(key) for key in ("name", "label", "min", "max", "default")}
                for parameter in data.get("parameters") or () if isinstance(parameter, Mapping)]
    return {"tier": row.get("tier") or "grammar", "demonstrates": data.get("demonstrates"), "controls": controls}


def lesson_view(vault: Any, repository: Any, figure_id: str) -> dict[str, Any] | None:
    """A lesson figure as the lesson shows it NOW, or None (gone, held out since, switched off): the
    figure service's view with **no predictions** (suppressed in a lesson) and no fuller version (a
    lesson host is grammar and sketch only)."""

    from learnloop.figures import service as FS

    if FS.figure_withheld(vault, repository, figure_id):
        return None
    row = figure_row(repository, figure_id)
    if row is None or FS.rich_row(row):
        return None
    view = FS.figure_view(vault, repository, row)
    if view.get("verification") not in ("verified", "illustrative") or not view.get("spec_json"):
        return None
    view["predictions"] = []
    if "fuller" in view:
        view["fuller"] = None
    view["host"] = "lesson"
    return view


__all__ = [
    "Builder",
    "FAILED",
    "SHOWN",
    "STATUSES",
    "UNAVAILABLE",
    "VISUALS_PROMPT_VERSION",
    "VISUALS_VERSION",
    "WITHHELD",
    "active",
    "build",
    "contract_problem",
    "displayed",
    "figure_request",
    "figure_row",
    "figure_text",
    "instructions",
    "lesson_view",
    "not_built_for_protection",
    "on",
    "paragraph",
    "prompt_version",
    "resolve",
    "stored_turn",
    "summary",
    "turn_model",
]
