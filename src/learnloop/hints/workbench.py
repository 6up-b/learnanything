"""Adaptive hints H3: the hint service on the Reader workbench (spec_adaptive_hints_v1 §10 H3, §16;
spec_reader_workbench_v1 §5.2-5.5, G7, G37, G60, G63, G64).

The one hint service gains the workbench surface here, and nowhere else: the
Reader passes its steps, the last check's verdicts and step graph, the
about-step and ``continue_from`` as the request's current work
(:class:`WorkbenchHintContext`), and the service

* offers the ladder's options (:func:`ladder_options`, :func:`taken_options`):
  every rung's kinds whose preconditions hold; with two or more rivals open on
  the about-step, level 1's only option is the discriminating question (G37);
  after a goal to aim for on this step, levels 3 and up aim at its target;
* suggests a rung (:func:`suggest`): one Decider request over the five rungs,
  sampled, the propensity logged (H2a's chooser, unchanged); the Reader's
  progression when no judgment is available;
* draws the kind of a rung the learner took (:func:`taken_choice`): the
  suggested rung serves the drawn option (the joint propensity); another rung
  draws from the same Decider vector renormalized over that level (the
  conditional propensity), 1 where the level has one option; under the
  fallback each rung has its fixed kind (§5.5);
* checks the rules only a step list makes exact (:func:`check_steps`, rules
  1-3 and 7 of the Reader's contract), beside H2a's shared ones;
* delivers a workbench row (:func:`deliver_workbench`) only while its
  submission has not been admitted (its ``submitted_at`` stamp, written by the
  workbench submit before it reads the fold), inside H2a's own delivery and
  fence; a row written after that stamp and shown during grading is counted
  by the attempt's transactional refold (fix round 1, F1), and none is shown
  once the attempt commits (G-H3);
* validates the map nodes a check names for its valid steps
  (:func:`place_steps`; the Reader never reads a map itself);
* verifies a hint's own checkable claims about the learner's steps before it
  is shown (:func:`verify_claims`, Reader §5.3 "hints are verified separately
  from how they are written"; fix round 1, F14): the writer declares each
  claim at level 2 and up (:class:`WorkbenchHintWriterOutputV1`, the
  workbench's output only), the Reader's check path checks it (an injected
  verifier: the sandboxed symbolic harness), a failed claim is re-asked once
  and then falls to H2a's level-3 downgrade, and an uncheckable one is
  labelled the model's reading.

Help, never evidence (``hints-never-write-evidence``): nothing here reads or
writes an attempt, a reveal, mastery, FSRS or certification.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import json
import random
from typing import Any

from pydantic import Field

from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as store
from learnloop.hints import chooser as chooser_module
from learnloop.hints.chooser import Choice
from learnloop.hints.contracts import Check, Target, in_work, nodes_by_id, routes_by_id
from learnloop.hints.discriminating import Rival, rival_id
from learnloop.hints.kinds import HORIZON_LABELS, KINDS, WORKED_HELP_MARK, WORKED_LEVELS, option_id, parse_option
from learnloop.hints.options import OFFERABLE, Option, OptionSet, build_options, precondition
from learnloop.hints.state import HintState
from learnloop.hints.writer import HintWriterOutputV1
from learnloop.ai.schemas import WireModel

SURFACE = "workbench"
#: The ladder's rungs (spec §5.2).
RUNGS: tuple[int, ...] = (1, 2, 3, 4, 5)
#: The reveal basis prefix of a workbench hint (Reader C15, hints §16.1 req. 6).
REVEAL_PREFIX = "workbench_hint"
WORKBENCH_PROMPT_NOTE = "workbench-steps-v1"

#: The rung labels (UX §5.5), and each rung's consequence (spec §5.2).
RUNG_LABELS: Mapping[int, str] = {
    1: "a question about your approach",
    2: "point to the first step that doesn't hold yet",
    3: "a hint on your step — a goal to aim for, a plan, the next step…",
    4: "work a piece of it for me, in my notation",
    5: "walk me through the rest, keeping my route",
}
DISCRIMINATING_RUNG_LABEL = "a question that tells apart two explanations of step {n}"
RUNG_CONSEQUENCE: Mapping[int, str] = {1: "hint", 2: "hint", 3: "hint", 4: WORKED_HELP_MARK, 5: WORKED_HELP_MARK}
FALLBACK_WHY = "no judgment available right now — the next rung up"
#: The fixed kind of a rung taken under the fallback (spec §5.5); rung 1 is
#: the discriminating question when rivals are open, rung 3 the item's next
#: authored hint while one remains.
FALLBACK_KIND: Mapping[int, str] = {1: "approach_question", 2: "localize", 3: "next_step", 4: "continuation",
                                    5: "walkthrough"}
#: The error kinds a check may guess (spec §5.2), with their plain words.
ERROR_KINDS: Mapping[str, str] = {
    "transcription": "a copying slip",
    "missing_prerequisite": "a missing prerequisite",
    "invalid_algebra": "an algebra step that doesn't hold",
    "wrong_method": "a method that doesn't fit",
    "conceptual": "a concept applied the wrong way",
    "unclear": "unclear",
}


def reveal_basis(kind: str, level: int) -> str:
    """The ``reveal_events`` basis of a hint shown in the workbench (§5.4)."""

    return f"{REVEAL_PREFIX}:{kind}:L{level}"


# ---------------------------------------------------------------------------
# The workbench's current work
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkbenchStep:
    """One live step: its stable id (the chain's first row), its newest
    version's row id, its number on screen and its text."""

    chain_id: str
    step_id: str
    number: int
    kind: str
    body_md: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.body_md.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class StepVerdict:
    """A check's verdict on one step (spec §5.2), keyed by the step's chain id."""

    chain_id: str
    verdict: str  # valid | questionable | unchecked
    method: str  # checked | checked_numerically | model
    depends_on: tuple[str, ...] = ()
    assumption: str = ""
    map_node_id: str | None = None
    route_id: str | None = None
    reason: str = ""
    #: The step's text hash when it was checked (stale when it changed).
    content_hash: str = ""


@dataclass(frozen=True)
class WorkbenchHintContext:
    """The workbench's part of a hint request (spec §5.2 "the service")."""

    workbench_session_id: str
    steps: tuple[WorkbenchStep, ...]
    verdicts: tuple[StepVerdict, ...] = ()
    check_assist_id: str | None = None
    first_questionable: str | None = None
    error_kind_guess: str | None = None
    #: The check's rival readings of the first questionable step (statement, kind).
    error_kind_alternatives: tuple[tuple[str, str], ...] = ()
    #: The step the hint is about and shown under (chain id), and the
    #: standing step it builds on (D45; rule 2).
    about: str | None = None
    continue_from: str | None = None
    #: Steps that stand: valid or unchecked, and depending on no questionable step.
    standing: tuple[str, ...] = ()
    #: The rung the ladder suggested when Help opened (logged; §5.5).
    offered_level: int | None = None
    #: The ``hint_choice`` judgment the suggestion was drawn in (None: the fallback).
    suggestion_id: str | None = None
    #: The header's per-problem help style (D31), else the stored preference.
    help_style: str | None = None
    #: "That's not where I'm stuck": the picked step (chain id).
    feedback_step: str | None = None
    discriminate_enabled: bool = True
    error_kind_enabled: bool = True

    def step(self, chain_id: str | None) -> WorkbenchStep | None:
        return next((step for step in self.steps if step.chain_id == chain_id), None) if chain_id else None

    def verdict(self, chain_id: str | None) -> StepVerdict | None:
        return next((row for row in self.verdicts if row.chain_id == chain_id), None) if chain_id else None

    def number(self, chain_id: str | None) -> int | None:
        step = self.step(chain_id)
        return step.number if step is not None else None

    @property
    def continue_from_node(self) -> str | None:
        verdict = self.verdict(self.continue_from)
        return verdict.map_node_id if verdict is not None and verdict.map_node_id else None

    def work_md(self) -> str:
        """The steps as the writer reads them: one per paragraph, numbered."""

        return "\n\n".join(f"Step {step.number}{' (stuck)' if step.kind == 'stuck' else ''}: {step.body_md}"
                           for step in self.steps)

    def placement_hash(self) -> str:
        """Where the help is placed: its about-step and that step's text (§5.2
        "two hints on the same step", "one at a time" per step). Without an
        about-step, the whole work."""

        step = self.step(self.about)
        if step is None:
            return hashlib.sha256(self.work_md().encode("utf-8")).hexdigest()
        return hashlib.sha256(f"{step.chain_id}\n{step.body_md}".encode("utf-8")).hexdigest()

    def snapshot(self) -> list[dict[str, Any]]:
        """``step_snapshot_json``: step ids and content hashes at request time,
        and each step's text (bounded) for the diagnoser's trace (§5.4)."""

        return [{"chain_id": step.chain_id, "step_id": step.step_id, "number": step.number, "kind": step.kind,
                 "hash": step.content_hash, "body_md": step.body_md[:2000]} for step in self.steps]

    def verdicts_record(self) -> list[dict[str, Any]]:
        return [verdict_record(row) for row in self.verdicts]

    def prompt_block(self) -> dict[str, Any]:
        """What the writer is told about the steps (spec §5.8 "context per call")."""

        by_chain = {step.chain_id: step.number for step in self.steps}
        rows = []
        for step in self.steps:
            verdict = self.verdict(step.chain_id)
            rows.append({
                "step": step.number, "kind": step.kind, "text": step.body_md,
                "verdict": verdict.verdict if verdict else "not checked",
                "method": verdict.method if verdict else None,
                "depends_on_steps": [by_chain[c] for c in (verdict.depends_on if verdict else ()) if c in by_chain],
                "assumption": verdict.assumption if verdict else "",
                "stands": step.chain_id in self.standing,
            })
        about = self.number(self.about)
        continue_from = self.number(self.continue_from)
        block: dict[str, Any] = {
            "version": WORKBENCH_PROMPT_NOTE,
            "steps": rows,
            "about_step": about,
            "continue_from_step": continue_from,
            "first_questionable_step": self.number(self.first_questionable),
            "rules": (
                "The learner works in numbered steps. Quote their steps EXACTLY, each quote inside one step. "
                f"Your hint is about step {about if about else 'their work'} and is shown under it: at level 2 "
                "and up quote it. Say first which steps stand, and build only on standing steps"
                + (f": continue from step {continue_from}." if continue_from else ".")
                + " Never treat a questionable step, or a step depending on it, as standing."
            ),
            "claims_rule": (
                "At level 2 and up, list in claims every checkable statement your hint makes about a step "
                "(that a step's derivative, integral, value, solution or rewriting is or is not right), with "
                "the step number and the transformation in sympy syntax (kind one of: equivalence, "
                "differentiation, integration, substitution, solving, limit, sum, inequality, boundary, "
                "normalization; the expression and the result it should equal). Code checks each claim before "
                "the hint is shown; a claim that does not hold sends the hint back. [] when it claims nothing."
            ),
        }
        if self.error_kind_enabled and self.error_kind_guess:
            block["error_kind_guess"] = f"{self.error_kind_guess} (the check's guess, not a diagnosis)"
        node = self.continue_from_node
        if node:
            block["continue_from_map_node"] = node
        return block


def verdict_record(row: StepVerdict) -> dict[str, Any]:
    return {"chain_id": row.chain_id, "verdict": row.verdict, "method": row.method,
            "depends_on": list(row.depends_on), "assumption": row.assumption, "map_node_id": row.map_node_id,
            "route_id": row.route_id, "reason": row.reason, "hash": row.content_hash}


def verdict_from_record(record: Mapping[str, Any]) -> StepVerdict:
    return StepVerdict(
        chain_id=str(record.get("chain_id") or ""), verdict=str(record.get("verdict") or "unchecked"),
        method=str(record.get("method") or "model"),
        depends_on=tuple(str(value) for value in record.get("depends_on") or ()),
        assumption=str(record.get("assumption") or ""), map_node_id=record.get("map_node_id") or None,
        route_id=record.get("route_id") or None, reason=str(record.get("reason") or ""),
        content_hash=str(record.get("hash") or ""))


# ---------------------------------------------------------------------------
# The step graph (spec §5.2 restored rows 18 and 60): what stands
# ---------------------------------------------------------------------------

def dependents(verdicts: Sequence[StepVerdict], chain_id: str) -> set[str]:
    """Every step that depends, directly or through others, on ``chain_id``."""

    graph = {row.chain_id: set(row.depends_on) for row in verdicts}
    found: set[str] = set()
    changed = True
    while changed:
        changed = False
        for step, deps in graph.items():
            if step not in found and (chain_id in deps or deps & found):
                found.add(step)
                changed = True
    return found


def standing_steps(steps: Sequence[WorkbenchStep], verdicts: Sequence[StepVerdict]) -> list[str]:
    """Steps that stand (rule 2): marked valid or unchecked (or not checked)
    and depending on no questionable step. Without a graph, the steps before
    the first questionable one. Stuck steps never stand."""

    by_chain = {row.chain_id: row for row in verdicts}
    questionable = [row.chain_id for row in verdicts if row.verdict == "questionable"]
    has_graph = any(row.depends_on for row in verdicts)
    order = [step.chain_id for step in steps if step.kind == "step"]
    if not questionable:
        return order
    if not has_graph:
        first = min((order.index(chain) for chain in questionable if chain in order), default=len(order))
        return order[:first]
    fallen: set[str] = set(questionable)
    for chain in questionable:
        fallen |= dependents(verdicts, chain)
    return [chain for chain in order if chain not in fallen and (by_chain.get(chain) is None
                                                                  or by_chain[chain].verdict != "questionable")]


def checkpoint_for(steps: Sequence[WorkbenchStep], standing: Sequence[str], about: str | None) -> str | None:
    """``continue_from`` (rule 2): the about-step itself when it stands (the
    picked step of "that's not where I'm stuck"), else the last standing step
    before it; with no about-step, the last standing step; None at the givens."""

    order = [step.chain_id for step in steps]
    standing_set = set(standing)
    if about is not None and about in standing_set:
        return about
    limit = order.index(about) if about in order else len(order)
    before = [chain for chain in order[:limit] if chain in standing_set]
    return before[-1] if before else None


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

def _waypoint_target(state: HintState) -> str | None:
    """After a goal to aim for at this placement (the about-step), levels 3+
    aim at its target (spec §5.2 "waypoints, with care")."""

    here = [hint for hint in state.shown_hints if hint.work_hash == state.work_hash]
    # The goal stays the target on this step (its text unchanged) through a
    # smaller step toward it and any later Help there (§5.2).
    waypoint = next((hint for hint in reversed(here) if hint.hint_kind == "waypoint"), None)
    return waypoint.target_node_id if waypoint is not None else None


def _adjust(option_set: OptionSet, state: HintState, context: WorkbenchHintContext) -> OptionSet:
    """The workbench's constraints on any option set: the discriminating
    switch, rung 1 is the discriminating question with rivals open (G37)."""

    options = list(option_set.options)
    excluded = dict(option_set.excluded)
    # A question that tells explanations apart is about a questionable step
    # (§5.2, UX §5.8 "when"): only on the check's first questionable step,
    # and never while the switch is off.
    reason = None if context.discriminate_enabled else "switched_off"
    if reason is None and not (context.first_questionable and context.about == context.first_questionable):
        reason = "no_questionable_step"
    if reason is not None:
        for option in [option for option in options if option.kind == "discriminating"]:
            options.remove(option)
            excluded[option.id] = reason
    level_one = [option for option in options if option.level == 1]
    if any(option.kind == "discriminating" for option in level_one):
        for option in level_one:
            if option.kind != "discriminating":
                options.remove(option)
                excluded[option.id] = "rivals_open"
    return replace(option_set, options=options, excluded=excluded)


def ladder_options(state: HintState, context: WorkbenchHintContext) -> OptionSet:
    """Every rung's options (the suggestion's choice set, §5.5)."""

    excluded: dict[str, str] = {}
    options: list[Option] = []
    for level in RUNGS:
        for kind in OFFERABLE:
            if level not in KINDS[kind].levels:
                continue
            reason = precondition(kind, state)
            if reason is not None:
                excluded[option_id(kind, level)] = reason
                continue
            options.append(Option(kind, level))
    return _adjust(OptionSet(options, level_source="offered", target_node_id=_waypoint_target(state),
                             excluded=excluded), state, context)


def taken_options(state: HintState, context: WorkbenchHintContext, *, request: str, answered: Any,
                  shortcut: str | None, taken_level: int | None) -> OptionSet:
    """A request's options: H2a's (a reply keeps its level, the learner's
    picks fix theirs, a taken rung offers its kinds), then the workbench's
    constraints. After a goal to aim for on this step, a taken rung 3 or
    higher aims at its target."""

    option_set = build_options(state, request=request, answered=answered, shortcut=shortcut,
                               taken_level=taken_level)
    if request == "more" and taken_level is not None and taken_level >= 3 and option_set.target_node_id is None:
        option_set = replace(option_set, target_node_id=_waypoint_target(state))
    return _adjust(option_set, state, context)


# ---------------------------------------------------------------------------
# The rivals the workbench adds (spec §5.2 "a question that tells explanations apart")
# ---------------------------------------------------------------------------

def check_rivals(context: WorkbenchHintContext) -> list[Rival]:
    """The check's own error-kind guess and its alternatives on the
    first questionable step, as rivals (statement and status only), when the
    hint is about that step."""

    if not context.error_kind_enabled or not context.first_questionable or context.about != context.first_questionable:
        return []
    found: list[Rival] = []
    seen: set[str] = set()
    for kind, statement in context.error_kind_alternatives:
        text = " ".join(str(statement or "").split())
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        found.append(Rival(rival_id(text), text, "check_guess", str(context.check_assist_id or ""),
                           "guess" if kind == context.error_kind_guess else "alternative"))
    return found


def apply_context(state: HintState, context: WorkbenchHintContext) -> HintState:
    """The state as the workbench places it: the about-step's placement
    hash, the per-problem help style, and the check's rivals beside the
    item's own (deduplicated by statement)."""

    state.work_hash = context.placement_hash()
    if context.help_style:
        state.help_style = context.help_style
    known = {rival.statement.lower() for rival in state.rivals}
    for rival in check_rivals(context):
        if rival.statement.lower() not in known:
            known.add(rival.statement.lower())
            state.rivals.append(rival)
    return state


# ---------------------------------------------------------------------------
# The suggestion and the draw of a taken rung (spec §5.5, G63)
# ---------------------------------------------------------------------------

@dataclass
class Suggestion:
    """The rung the ladder marks *suggested (why?)*, and how it was chosen."""

    level: int
    kind: str
    chooser: str  # decider | fallback
    horizon_index: int | None = None
    propensity: float | None = None
    judgment_id: str | None = None
    reason: str | None = None
    why: str = ""
    split: str | None = None
    #: The rung labels as shown (rung 1 with rivals open, the offered kind).
    rungs: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"level": self.level, "kind": self.kind, "chooser": self.chooser, "horizon_index": self.horizon_index,
                "propensity": self.propensity, "suggestion_id": self.judgment_id, "reason": self.reason,
                "why": self.why, "split": self.split, "rungs": self.rungs,
                "kind_label": KINDS[self.kind].label_at(self.level) if self.kind in KINDS else None,
                "horizon_label": HORIZON_LABELS.get(self.horizon_index) if self.kind == "waypoint"
                and self.horizon_index is not None else None}


def fixed_kind(level: int, option_set: OptionSet, state: HintState, item: Any) -> tuple[str, int | None]:
    """A rung's fixed kind under the fallback (spec §5.5), and the authored
    hint it serves at rung 3 while one remains."""

    if level == 1 and option_set.has("discriminating", 1):
        return "discriminating", None
    if level == 3:
        remaining = state.authored_remaining(item)
        if remaining:
            return "authored", remaining[0]
    kind = FALLBACK_KIND[level]
    if option_set.has(kind, level):
        return kind, None
    first = next((option for option in option_set.options if option.level == level), None)
    return (first.kind if first is not None else kind), None


def rung_labels(context: WorkbenchHintContext, option_set: OptionSet) -> list[dict[str, Any]]:
    """The five rungs as the ladder shows them: every one takeable (W11)."""

    about = context.number(context.about)
    rows = []
    for level in RUNGS:
        label = RUNG_LABELS[level]
        if level == 1 and option_set.has("discriminating", 1):
            label = DISCRIMINATING_RUNG_LABEL.format(n=about or "")
        elif level == 3 and about:
            label = f"a hint on your step {about} — a goal to aim for, a plan, the next step…"
        rows.append({"level": level, "label": label, "consequence": RUNG_CONSEQUENCE[level],
                     "worked_help": level in WORKED_LEVELS,
                     "discriminating": level == 1 and option_set.has("discriminating", 1)})
    return rows


def _why(state: HintState, context: WorkbenchHintContext, kind: str, level: int, horizon_index: int | None) -> str:
    """The chooser's inputs in plain words (spec §5.5 "what the learner sees")."""

    label = KINDS[kind].label_at(level) if kind in KINDS else kind
    if kind == "waypoint" and horizon_index is not None:
        label = f"{label}, {HORIZON_LABELS.get(horizon_index, '')}".rstrip(", ")
    parts = []
    demonstrated = sum(1 for row in state.facet_evidence if (row.get("unaided_credit") or 0) > 0)
    if demonstrated:
        parts.append(f"you've shown {demonstrated} of this problem's skills on your own")
    elif state.facet_evidence:
        parts.append("this problem's skills aren't yet shown on your own")
    if context.verdicts:
        questionable = sum(1 for row in context.verdicts if row.verdict == "questionable")
        parts.append("your steps so far stand" if not questionable else "a step doesn't hold yet")
    if len(state.rivals) >= 2 and kind == "discriminating":
        parts.append("two explanations of the step are open")
    style = (state.help_style or "balanced").replace("_", " ")
    inputs = "; ".join(parts)
    return f"{label}: {inputs + '; ' if inputs else ''}help style: {style} · LearnLoop's judgment"


def _split(probabilities: Mapping[str, float]) -> str | None:
    """"It leaned between …" when the judgment was split: the second option
    carries at least half the top option's probability (a display line)."""

    ranked = sorted(((float(p), option) for option, p in probabilities.items()), reverse=True)
    if len(ranked) < 2 or ranked[0][0] <= 0 or ranked[1][0] < ranked[0][0] / 2:
        return None
    labels = []
    for _p, option in ranked[:2]:
        kind, level = parse_option(option)
        labels.append(KINDS[kind].label_at(level))
    return f"it leaned between {labels[0]} and {labels[1]}"


def suggest(
    vault: Any,
    repository: Repository,
    state: HintState,
    context: WorkbenchHintContext,
    item: Any,
    *,
    fallback_level: int,
    assist_id: str,
    client_factory: Callable[[], Any] | None,
    seed: str | None,
    envelope: Any = None,
    clock: Any = None,
) -> Suggestion:
    """The suggested rung (spec §5.5): drawn from the Decider's own
    probabilities over the five rungs' options, the propensity logged by H2a's
    chooser (its ``hint_choice`` ledger row); with the chooser off, timed out
    or unavailable, ``fallback_level`` (the Reader's progression) with its
    fixed kind and propensity 1."""

    from learnloop.ai.spend import spend_envelopes

    option_set = ladder_options(state, context)
    rungs = rung_labels(context, option_set)
    reason = "chooser_disabled"
    if vault.config.hints.chooser_enabled and len(option_set.options) > 1:
        with spend_envelopes(envelope):
            choice = chooser_module.ask(
                config=vault.config, repository=repository, state=state, option_set=option_set, request="more",
                shortcut=None, assist_id=assist_id, client_factory=client_factory, seed=seed, clock=clock,
                where="the Reader workbench (the learner works in numbered steps beside the book)",
                extra_state=decider_extra(context))
        if choice.chooser == "decider":
            probabilities = (choice.probabilities or {}).get(chooser_module.KIND_QUESTION) or {}
            return Suggestion(level=choice.level, kind=choice.kind, chooser="decider",
                              horizon_index=choice.horizon_index, propensity=choice.propensity,
                              judgment_id=choice.judgment_id,
                              why=_why(state, context, choice.kind, choice.level, choice.horizon_index),
                              split=_split(probabilities), rungs=rungs)
        reason = str(choice.reason or "unavailable")
    elif len(option_set.options) <= 1:
        reason = "one_option"
    level = max(1, min(5, int(fallback_level)))
    kind, _index = fixed_kind(level, option_set, state, item)
    return Suggestion(level=level, kind=kind, chooser="fallback", propensity=1.0, reason=reason,
                      why=FALLBACK_WHY, rungs=rungs)


def decider_extra(context: WorkbenchHintContext) -> dict[str, Any]:
    """The workbench's additions to the Decider's typed state (spec §5.5
    "the state it gets"): the last check's summary and its map placement.
    Never a step's text, the reference or the map's states (§7.4)."""

    verdicts = list(context.verdicts)
    return {
        "surface": "workbench",
        "steps": len(context.steps),
        "check": {
            "checked": bool(verdicts),
            "valid": sum(1 for row in verdicts if row.verdict == "valid"),
            "questionable": sum(1 for row in verdicts if row.verdict == "questionable"),
            "unchecked": sum(1 for row in verdicts if row.verdict == "unchecked"),
            "symbolically_checked": sum(1 for row in verdicts if row.method != "model"),
            "first_questionable_step": context.number(context.first_questionable),
            "error_kind_guess": context.error_kind_guess if context.error_kind_enabled else None,
        },
        "about_step": context.number(context.about),
        "continue_from_step": context.number(context.continue_from),
        "map_placement": {"continue_from_node": context.continue_from_node,
                          "route": (context.verdict(context.continue_from).route_id
                                    if context.verdict(context.continue_from) else None)},
        "help_style_source": "this problem" if context.help_style else "stored preference",
    }


def suggestion_record(repository: Repository, judgment_id: str | None) -> dict[str, Any] | None:
    """A suggestion's ``hint_choice`` row (the Decider's vectors, the seed,
    the draw and its propensity), or None."""

    if not judgment_id:
        return None
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT verdict, rationale, judge, judge_model FROM judgment_ledger WHERE id = ? AND task = ?",
            (judgment_id, chooser_module.LEDGER_TASK)).fetchone()
    if row is None or row[2] != "decider":
        return None
    try:
        rationale = json.loads(row[1] or "{}")
    except (TypeError, ValueError):
        return None
    if rationale.get("status") != "ok" or not isinstance(rationale.get("drawn"), Mapping):
        return None
    return {**rationale, "judgment_id": judgment_id, "model": row[3]}


def _rng(seed: str) -> random.Random:
    return random.Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16))


def taken_choice(state: HintState, option_set: OptionSet, context: WorkbenchHintContext, item: Any, *,
                 taken_level: int, suggestion: Mapping[str, Any] | None) -> Choice | None:
    """The kind served on a rung the learner took (spec §5.5, G63).

    * One option at the rung: it, propensity 1 (``learner_pick``, as H2a).
    * The suggested rung: the drawn option, its joint propensity.
    * Another rung, with a Decider suggestion: drawn from the same vector
      renormalized over that rung's options, seeded, the conditional
      probability logged (a waypoint's horizon too, renormalized over the
      allowed horizons); ``argmax`` logs 1.
    * No judgment: the rung's fixed kind, propensity 1 (``fallback``).
    Returns None only when the rung has no option at all."""

    ids = option_set.ids
    if not option_set.options:
        return None
    common: dict[str, Any] = {}
    if suggestion is not None:
        probabilities = dict((suggestion.get("probabilities") or {}).get(chooser_module.KIND_QUESTION) or {})
        drawn = suggestion.get("drawn") or {}
        policy = str(suggestion.get("policy") or "sample")
        seed = str(suggestion.get("seed") or "")
        common = dict(options=ids, probabilities=dict(suggestion.get("probabilities") or {}), seed=seed or None,
                      policy=policy, judgment_id=suggestion.get("judgment_id"), model=suggestion.get("model"))
        if int(drawn.get("level") or 0) == taken_level and drawn.get("option") in ids:
            # The suggested rung serves the drawn option, with the joint
            # propensity it was drawn with (G63).
            propensity = 1.0 if policy == "argmax" else suggestion.get("propensity")
            return Choice(str(drawn["kind"]), taken_level, drawn.get("horizon_index"), chooser="decider",
                          propensity=propensity, **common)
    if len(option_set.options) == 1:
        return chooser_module.single_option_choice(option_set)
    if suggestion is not None:
        restricted = {option: float(probabilities.get(option) or 0.0) for option in ids}
        if sum(restricted.values()) > 0:
            rng = _rng(f"{seed}:L{taken_level}")
            if policy == "argmax":
                option, p_option = chooser_module.argmax(restricted), 1.0
            else:
                option, p_option = chooser_module.draw(restricted, rng)
            kind, level = parse_option(option)
            horizon_index = None
            propensity = p_option
            if kind == "waypoint":
                horizons = {int(key): float(value) for key, value in
                            ((suggestion.get("probabilities") or {}).get(chooser_module.HORIZON_QUESTION) or {}).items()}
                bounded = {index: horizons.get(index, 0.0) for index in (1, 2, 3)}
                if sum(bounded.values()) <= 0:
                    bounded = {index: 1.0 for index in (1, 2, 3)}
                if policy == "argmax":
                    horizon_index = chooser_module.argmax(bounded)
                else:
                    horizon_index, p_horizon = chooser_module.draw(bounded, rng)
                    propensity = p_option * p_horizon
            return Choice(kind, level, horizon_index, chooser="decider",
                          propensity=1.0 if policy == "argmax" else propensity, **common)
    kind, authored_index = fixed_kind(taken_level, option_set, state, item)
    reason = "no_judgment" if suggestion is None else "no_probability_at_rung"
    return Choice(kind, taken_level, 1 if kind == "waypoint" else None, chooser="fallback", propensity=1.0,
                  options=ids, policy="fallback", reason=reason, authored_index=authored_index)


# ---------------------------------------------------------------------------
# The rules a step list makes exact (the Reader's rules 1-3 and 7, G7, G60)
# ---------------------------------------------------------------------------

def _squash(text: str) -> str:
    return " ".join(str(text or "").split())


def step_of(quote: str, context: WorkbenchHintContext) -> WorkbenchStep | None:
    """The one step a quote lies inside (spacing ignored), or None."""

    needle = _squash(quote)
    if not needle:
        return None
    for step in context.steps:
        if needle in _squash(step.body_md):
            return step
    return None


def check_steps(check: Check, output: Any, *, target: Target, context: WorkbenchHintContext) -> Check:
    """The workbench's exact rules, added to H2a's check of one answer."""

    placement = output.placement
    quotes = [quote for quote in placement.quotes if str(quote).strip()]
    level = target.level
    if not context.steps:
        return check
    exempt = target.downgrade or target.from_givens
    # Rule 1: it cites the learner, each quote inside one existing step.
    if any(step_of(quote, context) is None for quote in quotes):
        check.fail("wb_rule1_quote_not_in_one_step")
    cited = [step for step in (step_of(quote, context) for quote in quotes) if step is not None]
    if level >= 2 and not exempt and not cited:
        check.fail("wb_rule1_no_step_cited")
    # Rule 3: shown under its about-step, which it quotes (G60).
    about = context.step(context.about)
    if about is not None and level >= 2 and not exempt:
        quoted_about = any(step.chain_id == about.chain_id for step in cited) or (
            str(placement.first_questionable_quote or "").strip()
            and in_work(placement.first_questionable_quote, about.body_md))
        if not quoted_about:
            check.fail("wb_rule3_about_step_not_quoted")
    # Rule 2: what stands lies in standing steps only; never the
    # questionable step or a step depending on it.
    stands = str(placement.stands_quote or "").strip()
    if stands:
        standing_step = step_of(stands, context)
        if standing_step is None or standing_step.chain_id not in set(context.standing):
            check.fail("wb_rule2_checkpoint_not_standing")
    # Rule 7: placed from the node the continue_from step reached.
    node = context.continue_from_node
    if node and output.route_id and output.route_id != "new_route" and not exempt and target.kind in (
            "waypoint", "subgoal_plan", "next_step", "continuation") and not target.reference_route:
        if placement.reached_node_id and placement.reached_node_id != node:
            check.fail("wb_rule7_not_from_continue_from")
    return check


# ---------------------------------------------------------------------------
# A hint's own checkable claims (Reader §5.3; fix round 1, F14)
# ---------------------------------------------------------------------------

class HintClaim(WireModel):
    """One checkable statement a workbench hint makes about a step, with its
    transformation in sympy syntax (the check's declared kinds)."""

    #: The step number the claim is about.
    step: int
    #: The claim in the hint's words ("your derivative in step 3 matches f").
    statement: str
    kind: str
    expression: str
    result: str
    variable: str
    value: str
    lower: str
    upper: str
    relation: str


class WorkbenchHintWriterOutputV1(HintWriterOutputV1):
    """The writer's answer on the workbench: H2a's, plus the hint's claims
    (the practice screen's output, prompt and schema are unchanged)."""

    claims: list[HintClaim] = Field(default_factory=list, description=(
        "at level 2 and up, every checkable statement the hint makes about a step, each with its step "
        "number and transformation; [] when none"))


#: How a claim stands once checked: ``checked`` / ``checked_numerically``
#: (the verifier decided it and it holds), ``failed`` (it decided it and it
#: does not hold: re-asked once, then downgraded), ``model`` (the model's
#: reading, not checked).
CLAIM_LABELS: Mapping[str, str] = {"checked": "checked", "checked_numerically": "checked numerically",
                                   "model": "model's reading, not checked"}
#: ``verifier(claims, context) -> [{"index", "method", "holds", "reason"}]``,
#: one per claim in order (the Reader's check path, injected by the caller).
ClaimVerifier = Callable[[Sequence[HintClaim], "WorkbenchHintContext"], Sequence[Mapping[str, Any]]]


def verify_claims(check: Check, output: Any, *, target: Target, context: WorkbenchHintContext,
                  verifier: ClaimVerifier | None) -> list[dict[str, Any]]:
    """Check one answer's claims (level 2 and up): a claim about a step that
    does not exist, or one the verifier decides does not hold, fails the
    round (``wb_claim_failed:<step>``: re-asked once with the failure named,
    then H2a's downgrade "without its unverified claims"); every other claim
    is labelled as it stands. Returns the claims as recorded and shown."""

    claims = list(getattr(output, "claims", None) or ())
    if not claims or target.level < 2:
        return []
    numbers = {step.number for step in context.steps}
    outcomes: list[Mapping[str, Any]] = []
    if verifier is not None:
        try:
            outcomes = list(verifier(claims, context))
        except Exception:  # noqa: BLE001 - a verifier failure leaves every claim the model's reading
            outcomes = []
    recorded = []
    for index, claim in enumerate(claims):
        outcome = outcomes[index] if index < len(outcomes) else {}
        method = str(outcome.get("method") or "model")
        holds = outcome.get("holds")
        if int(claim.step) not in numbers:
            status = "failed"
            check.fail(f"wb_claim_unknown_step:{claim.step}")
        elif method in ("checked", "checked_numerically") and holds is False:
            status = "failed"
            check.fail(f"wb_claim_failed:{claim.step}")
        elif method in ("checked", "checked_numerically") and holds is True:
            status = method
        else:
            status = "model"
        recorded.append({"step": int(claim.step), "statement": " ".join(str(claim.statement).split())[:240],
                         "status": status, "label": CLAIM_LABELS.get(status, "doesn't hold"),
                         "kind": claim.kind, "reason": str(outcome.get("reason") or "")[:200]})
    return recorded


# ---------------------------------------------------------------------------
# The row's workbench columns, and what the surface shows
# ---------------------------------------------------------------------------

def row_columns(context: WorkbenchHintContext, *, level: int | None, taken_level: int | None,
                request: str) -> dict[str, Any]:
    """The workbench's columns on a hint row (Reader §5.7)."""

    if request == "more" and taken_level is not None:
        level_source = "offered" if context.offered_level == taken_level else "learner_pick"
    else:
        level_source = None
    return {
        "surface": SURFACE,
        # Filled at Submit (the schema's rule): the workbench's rows are never
        # in the answer box's window fold before then.
        "practice_session_id": None,
        "workbench_session_id": context.workbench_session_id,
        "offered_level": context.offered_level,
        "level_source": level_source,
        "step_snapshot_json": json.dumps(context.snapshot(), sort_keys=True),
        "step_verdicts_json": json.dumps(context.verdicts_record(), sort_keys=True) if context.verdicts else None,
        "first_questionable_step_id": context.first_questionable,
        "error_kind_guess": context.error_kind_guess if context.error_kind_enabled else None,
        "about_step_id": context.about,
        "continue_from_step_id": context.continue_from,
        "feedback_step_id": context.feedback_step if request == "feedback" else None,
    }


def step_labels(context: WorkbenchHintContext) -> dict[str, Any]:
    """*on your step 3 · continues from step 2* (D45, G60)."""

    about = context.number(context.about)
    continue_from = context.number(context.continue_from)
    parts = []
    if about:
        parts.append(f"on your step {about}")
    parts.append(f"continues from step {continue_from}" if continue_from else "starts from the givens")
    return {"about_step": about, "continue_from_step": continue_from, "line": " · ".join(parts),
            "about_step_id": context.about, "continue_from_step_id": context.continue_from}


# ---------------------------------------------------------------------------
# Delivery (G-H3): a workbench row is shown only before its submission is admitted
# ---------------------------------------------------------------------------

def deliver_workbench(repository: Repository, assist_id: str, *, clock: Any = None,
                      item: Any = None) -> tuple[str, dict[str, Any] | None]:
    """Show a prepared workbench row (a check or a hint) through H2a's
    :func:`~learnloop.hints.service.deliver_hint` (its fence), in one
    transaction with the check that the row's submission was not admitted
    yet: the workbench submit stamps ``submitted_at`` on its rows BEFORE it
    reads the fold, so a row is either shown before that read (and counted)
    or never shown. Returns H2a's outcomes."""

    from learnloop.hints import service as hint_service

    with repository.atomic():
        connection = repository.connection()
        row = store.assist(connection, assist_id)
        if row is None or row.get("surface") != SURFACE:
            return hint_service.NOT_DELIVERABLE, None
        if not row.get("shown") and row.get("submitted_at"):
            return hint_service.SUBMISSION_COMPLETE, None
        return hint_service.deliver_hint(repository, assist_id, clock=clock, item=item)


def text_leaks(text: str, item: Any) -> bool:
    """Whether a check's line would give the item's answer away (H2a's leak
    control: the tutor's overlap check and H1's ``gives_away``, which also
    catches a short numeric answer). The check never states the answer."""

    from learnloop.hints.contracts import leak_flags

    return bool(str(text or "").strip()) and bool(leak_flags([text], item=item, current=None, level=3))


# ---------------------------------------------------------------------------
# Map placement of a check's valid steps (spec §5.2 "the check reads the approach map")
# ---------------------------------------------------------------------------

def current_map_for(vault: Any, repository: Repository, practice_item_id: str) -> dict[str, Any] | None:
    """The item's current approach map record (None with the maps off): the
    Reader reads maps only through the service."""

    try:
        from learnloop.hints.map_builder import current_map

        return current_map(vault, repository, practice_item_id)
    except Exception:  # noqa: BLE001 - a check works without a map
        return None


def map_for_prompt(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The map as the check writer reads it: nodes with their labels and
    recognizers, the routes; never sent to a grader (W8)."""

    current = (record or {}).get("map") if record else None
    if not current:
        return None
    return {"nodes": [{"id": node.get("id"), "role": node.get("role"), "label": node.get("label"),
                       "recognizers": node.get("recognizers") or []} for node in current.get("nodes") or ()],
            "routes": [{"id": route.get("id"), "name": route.get("name"), "path": route.get("path") or []}
                       for route in current.get("routes") or ()],
            "goal_node_id": current.get("goal_node_id")}


def place_steps(record: Mapping[str, Any] | None, claims: Sequence[tuple[str, str, str, str]]
                ) -> dict[str, tuple[str | None, str | None]]:
    """Validate the check's map claims for its valid steps: ``(chain, verdict,
    node, route)`` -> ``{chain: (node, route)}``. A node not on the map is
    dropped; a node on the map but on no claimed route keeps its node with the
    first route through it; a valid step the check placed on no route is
    ``new_route`` (adaptive-hints §4.4). Only valid steps are placed."""

    current = (record or {}).get("map") if record else None
    if not current:
        return {}
    nodes = nodes_by_id(current)
    routes = routes_by_id(current)
    placed: dict[str, tuple[str | None, str | None]] = {}
    for chain, verdict, node, route in claims:
        if verdict != "valid":
            continue
        node = str(node or "")
        route = str(route or "")
        if node and node in nodes:
            if route in routes and node in [str(n) for n in routes[route].get("path") or ()]:
                placed[chain] = (node, route)
            else:
                through = next((route_id for route_id, row in routes.items()
                                if node in [str(n) for n in row.get("path") or ()]), None)
                placed[chain] = (node, through)
        elif route == "new_route":
            placed[chain] = (None, "new_route")
    return placed


def schedule_map(vault: Any, sqlite_path: Any, practice_item_id: str, *, client: Any = None,
                 builds: Any = None) -> None:
    """A map built in the background when the workbench binds an item (§5.2),
    with H1's own switches, locks and envelope (``build_on_serve``)."""

    try:
        from learnloop.hints.map_builder import schedule_build_on_serve

        schedule_build_on_serve(vault, sqlite_path, practice_item_id, client=client, builds=builds)
    except Exception:  # noqa: BLE001 - map work never reaches the workbench
        return


__all__ = [
    "DISCRIMINATING_RUNG_LABEL",
    "ERROR_KINDS",
    "FALLBACK_KIND",
    "FALLBACK_WHY",
    "REVEAL_PREFIX",
    "RUNGS",
    "RUNG_CONSEQUENCE",
    "RUNG_LABELS",
    "SURFACE",
    "StepVerdict",
    "Suggestion",
    "WorkbenchHintContext",
    "WorkbenchStep",
    "apply_context",
    "check_rivals",
    "check_steps",
    "checkpoint_for",
    "current_map_for",
    "decider_extra",
    "deliver_workbench",
    "dependents",
    "fixed_kind",
    "ladder_options",
    "map_for_prompt",
    "place_steps",
    "reveal_basis",
    "row_columns",
    "rung_labels",
    "schedule_map",
    "standing_steps",
    "step_labels",
    "step_of",
    "suggest",
    "suggestion_record",
    "taken_choice",
    "taken_options",
    "text_leaks",
    "verdict_from_record",
    "verdict_record",
]
