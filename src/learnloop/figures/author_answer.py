"""What one figure-author answer is, and what the author loop does with it next.

The build's author loop (:mod:`.build`) asks the figure author at most twice. :func:`read_answer` is its rules for
one answer, over plain values: the answer, the tier menu it was offered (None: no rich tier, so V1 or V2), whether
the sketch tier and the advanced panels were on, whether the figure has passages from the learner's books, and
whether this is the last attempt. It applies the label rule, the menu and tier-reason rules, the rich brief's
parse, and the spec's or sketch's parse with prediction salvage, and returns a :class:`Reading`: retry with these
problems, unsupported, or a parsed figure for the loop to verify. Each retry carries the record code the attempt's
``figure_author`` record stores (:mod:`.records`), and every reading the codes noted beside it.

It calls no model, gate, sketch engine, source check or store, and reads no clock: the loop does those, and runs
the numeric verification, the engine and the source check on what this module parsed.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from learnloop.figures import labels as L
from learnloop.figures import records as FR
from learnloop.figures import rich as RICH
from learnloop.figures import sketch as K
from learnloop.figures import spec as S


@dataclass(frozen=True)
class Retry:
    """The attempt ends with record code ``rule``; the next prompt is told ``problems``."""

    rule: str
    problems: list[str]
    #: Whether the record counts the problems: the menu rules' one fixed sentence is not counted.
    counted: bool = True
    #: ``"spec"`` or ``"sketch"`` when that parse refused the answer: the figure an earlier attempt left (kept
    #: when only its source check differed) does not outlive it.
    parsed: str | None = None


@dataclass(frozen=True)
class Unsupported:
    """The author says no medium offered can show it: what it would take, and why."""

    kind: str
    reason: str


@dataclass(frozen=True)
class Spec:
    """A spec that parsed; ``dropped`` names the malformed predictions left out of it."""

    figure: S.CompiledFigure
    dropped: list[str]


@dataclass(frozen=True)
class Sketch:
    """A sketch program that parsed, for the sealed engine; ``dropped`` as for :class:`Spec`."""

    program: K.CompiledSketch
    dropped: list[str]


@dataclass(frozen=True)
class Rich:
    """A rich tier's brief, with its optional quick figure, or why that figure was dropped (the brief stands)."""

    brief: RICH.RichBrief
    quick: Spec | Sketch | None
    dropped: str | None


@dataclass(frozen=True)
class Reading:
    """One answer, read: ``then`` is what the loop does next."""

    #: The status the author wrote, normalized (the record's ``author_status``).
    status: str
    then: Retry | Unsupported | Spec | Sketch | Rich
    #: The tier judgment (``figure_tier``'s verdict and reason), or None where the answer is not judged on a tier:
    #: without a sketch or rich tier on the menu, and when the label rule sends it back before its status is read.
    verdict: tuple[str, str] | None = None
    #: Record codes noted beside the attempt's own (a stripped label, a V2 status outside its three).
    notes: tuple[str, ...] = ()


def status_of(output: Any) -> str:
    return str(output.status).strip().lower()


def _sentence(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def read_answer(output: Any, *, last: bool, tiers: Sequence[str] | None, sketch: bool, grounded: bool,
                advanced: bool) -> Reading:
    """``output`` is the author's parsed answer (its output contract's fields); ``tiers`` the menu when it held a
    rich tier, else None; ``grounded`` False when no passage came from the learner's books."""

    status = status_of(output)
    notes: list[str] = []
    # Free text that reads like a code-owned check label is the repair call's problem, in code's words; still
    # there on the last attempt, the figure is kept without that text (a video's own text is its job's).
    labelled = L.label_problems(_free_text(output, status))
    if labelled:
        if not last:
            return Reading(status, Retry(FR.LABEL_TEXT, labelled))
        notes.append(FR.LABEL_TEXT_STRIPPED)
        output = _without_label_text(output)
    verdict: tuple[str, str] | None = None
    if tiers is not None:
        # The status is the medium chosen, and why_this_tier its reason.
        menu = {"spec" if tier == "grammar" else tier for tier in tiers} | {"unsupported"}
        reason = _sentence(output.unsupported_reason if status == "unsupported" else
                           getattr(output, "why_this_tier", ""), 400)
        verdict = (status if status in menu else "invalid", reason)
        if status not in menu:
            problem = f"status {status!r} is not one of the media offered ({sorted(menu)})"
            return Reading(status, Retry(FR.STATUS_INVALID, [problem], counted=False), verdict, tuple(notes))
        if status != "unsupported" and not reason:
            problem = "why_this_tier is empty: say in one sentence why this medium explains the idea best"
            return Reading(status, Retry(FR.TIER_REASON_MISSING, [problem], counted=False), verdict, tuple(notes))
        if status in RICH.RICH_TIERS:
            brief, problems = RICH.parse_brief(output.rich_json, tiers, status, grounded=grounded)
            if brief is None:
                return Reading(status, Retry(FR.BRIEF_INVALID, problems), verdict, tuple(notes))
            return Reading(status, _with_quick(brief, output, sketch=sketch, grounded=grounded, advanced=advanced),
                           verdict, tuple(notes))
    elif sketch:
        # The status is the tier judgment between the grammar and the sketch.
        reason = (_sentence(getattr(output, "why_not_spec", ""), 400) if status == "sketch"
                  else _sentence(output.unsupported_reason, 400) if status == "unsupported" else "")
        verdict = (status if status in ("spec", "sketch", "unsupported") else "invalid", reason)
        if verdict[0] == "invalid":
            notes.append(FR.STATUS_INVALID)
    if status == "unsupported":
        return Reading(status, Unsupported(_sentence(output.unsupported_kind, 80) or "something else",
                                           _sentence(output.unsupported_reason, 400)), verdict, tuple(notes))
    if sketch and status == "sketch":
        try:
            program, dropped = K.parse_author_sketch(
                output.sketch_json if grounded else _ungrounded_sketch(output.sketch_json))
        except K.SketchError as exc:
            return Reading(status, Retry(FR.sketch_problem(exc.problems), exc.problems, parsed="sketch"), verdict,
                           tuple(notes))
        return Reading(status, Sketch(program, dropped), verdict, tuple(notes))
    try:
        # With the panels off, a panel is refused: the author was not told of them.
        figure, dropped = S.parse_author_spec(output.spec_json if grounded else _ungrounded(output.spec_json),
                                              advanced=advanced)
    except S.SpecError as exc:
        return Reading(status, Retry(FR.spec_problem(exc.problems), exc.problems, parsed="spec"), verdict,
                       tuple(notes))
    return Reading(status, Spec(figure, dropped), verdict, tuple(notes))


def _with_quick(brief: RICH.RichBrief, output: Any, *, sketch: bool, grounded: bool, advanced: bool) -> Rich:
    """The rich answer's optional quick figure, parsed: a spec first, else a sketch with the sketch tier on. One
    that does not parse is dropped and the brief carries on (as is one that fails its checks, in the loop)."""

    if str(output.spec_json or "").strip():
        try:
            return Rich(brief, Spec(*S.parse_author_spec(
                output.spec_json if grounded else _ungrounded(output.spec_json), advanced=advanced)), None)
        except S.SpecError as exc:
            return Rich(brief, None, exc.problems[0] if exc.problems else "the quick figure is invalid")
    if sketch and str(getattr(output, "sketch_json", "") or "").strip():
        try:
            return Rich(brief, Sketch(*K.parse_author_sketch(
                output.sketch_json if grounded else _ungrounded_sketch(output.sketch_json))), None)
        except K.SketchError as exc:
            return Rich(brief, None, exc.problems[0] if exc.problems else "the quick sketch is invalid")
        except Exception as exc:  # noqa: BLE001 - a quick sketch that cannot be read is dropped, never the brief
            return Rich(brief, None, f"the quick sketch could not be run: {type(exc).__name__}")
    return Rich(brief, None, None)


def _free_text(output: Any, status: str) -> list[tuple[str, Any]]:
    """The author's model-written free text the label rule reads (spec
    §9b.4): the tier reason, and what each figure it carries shows and
    assumes (a rich status's quick figure and brief included)."""

    if status == "unsupported":
        return []
    rich = status in RICH.RICH_TIERS
    fields: list[tuple[str, Any]] = [(name, getattr(output, name, None)) for name in ("why_this_tier", "why_not_spec")]
    if status != "sketch":
        fields += L.json_fields("spec_json", getattr(output, "spec_json", None))
    if status == "sketch" or rich:
        fields += L.json_fields("sketch_json", getattr(output, "sketch_json", None))
    if rich:
        fields += L.json_fields("rich_json", getattr(output, "rich_json", None))
    return fields


def _without_label_text(output: Any) -> Any:
    """The author's answer with its label-like free text left out (spec
    §9b.4): a tier reason in code's words, a figure's or brief's label-like
    ``demonstrates`` emptied and label-like assumptions dropped."""

    update: dict[str, Any] = {}
    for name in ("why_this_tier", "why_not_spec"):
        if L.label_like(getattr(output, name, None)) is not None:
            update[name] = L.REASON_WITHHELD
    for name in ("spec_json", "sketch_json", "rich_json"):
        raw = getattr(output, name, None)
        stripped = L.strip_json(raw)
        if stripped is not raw:
            update[name] = stripped
    if not update:
        return output
    if hasattr(output, "model_copy"):
        return output.model_copy(update=update)
    from types import SimpleNamespace

    return SimpleNamespace(**{**vars(output), **update})


def _ungrounded(raw: Any) -> Any:
    """RW5d (spec §8.3 step 3): with nothing from the learner's books, the
    figure is an illustration that quotes nothing, whatever the author wrote:
    code forces ``kind`` illustrative and drops every source claim and quote
    (there is no passage to verify them against)."""

    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    data["kind"] = "illustrative"
    data["source_claims"] = []
    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        data["assumptions"] = [{**item, "span_id": None, "quote": None} if isinstance(item, dict) else item
                               for item in assumptions]
    invariants = data.get("invariants")
    if isinstance(invariants, list):
        # An equals_source invariant names a passage's equation; there is none.
        data["invariants"] = [item for item in invariants
                              if not (isinstance(item, dict) and item.get("kind") == "equals_source")]
    return data


def _ungrounded_sketch(raw: Any) -> Any:
    """RW5d P2 + §8.3 step 3: a sketch built with nothing from the learner's
    books quotes nothing, whatever the author wrote."""

    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    data["source_claims"] = []
    assumptions = data.get("assumptions")
    if isinstance(assumptions, list):
        data["assumptions"] = [{**item, "span_id": None, "quote": None} if isinstance(item, dict) else item
                               for item in assumptions]
    return data


__all__ = [
    "Reading",
    "Retry",
    "Rich",
    "Sketch",
    "Spec",
    "Unsupported",
    "read_answer",
    "status_of",
]
