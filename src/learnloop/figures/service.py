"""Explorable figures: build, reuse, revise, list, predict, explain (spec_reader_workbench_v1 §8; UX §4.7).

**Build** (:func:`build_figure`): held-out or exam material is refused before
any model call (the one predicate, ``exam_material(...)``: the selection, the
figure block and the region's block); the same input under the same spec and
prompt version is reused from ``interactive_figures`` (``input_hash``) with
no call; otherwise the author writes a spec (at most two attempts, the second
told the first's problems), :mod:`.verify` checks it (structure, invariants,
shaded areas: §8.3 steps 1-2), and one row is written with its verification
and a ``judgment_ledger`` verdict (task ``figure_verified``, judge
``verifier``). A figure that fails steps 1-2 is stored ``failed`` (never
shown); every other figure, a reconstruction included, is stored
``illustrative``: RW5a makes no "matches the book" claim (owner scope
decision 2026-10-21; the source match, step 3, is RW5c's).

**Admission.** Every physical request a build makes passes one
:class:`~learnloop.figure_admission.FiguresGate`: before each one (retries
included) the switch, the author route, the day's cap and the price are read
as configured NOW and compared with the build's start; any change stops the
build with no further call and nothing stored.
One input builds once at a time in this process (an identical request made
meanwhile waits and takes that figure, with no call), its request identity
is the input and its retry generation (so a rerun after a crash recovers a
paid answer, and a stored failure asks afresh), and the schema keeps one
shown or unsupported row per input (Codex review F7).

**Held-out material, rechecked.** Each row keeps every span the author was
sent (``input_span_ids``: the selection, the paragraphs around it, the
cropped block). Listing, delivery, revisions, predictions and explanations
refuse a figure any of whose spans is held out now (Codex review F1).

**What a prompt carries.** The selected passage, the paragraphs around it
(held-out ones left out), the figure's crop when a figure block or a region
was selected and the route reads images (a region needs it), and, for a "not
right?" version, the earlier spec and the learner's note. Learner data-relax
2 (owner principle 2026-11-01: the learner's questions, answers and history
are not private; include them where they help): with
``figures.author_learner_state`` on, also ``learner_state``, the learner's
state on the passage's topics (:mod:`.learner_state`: status in words, open
misconception and gap statements, at most two recent answers of theirs, read
through ``learner_protection`` so exam, held-out, reserved and cold-in-flight
work never shows), under the prompt version's ``+learner-v1``, and the reuse
key names its hash. Only a non-empty state does any of this: a learner with
no state (or the switch off) is sent, prompted and keyed exactly as before.
Figures stay help, never evidence.

**RW5b** (spec §8.7). With ``figures.advanced_panels_enabled`` the author
is told of heat maps, vector fields, trajectories and iterated maps (its own
prompt version, so RW5a's reuse keys are unchanged while the panels are off);
off, it may not emit them, and a stored figure that uses one is shown as
"can't draw this yet" (:func:`advanced_off_row`). With
``figures.offers_enabled`` a build may start from an offer (origin
``library`` | ``tutor``): the same pipeline, its gate also watching the
offers switch (:func:`offer_build_key`).

**RW5d P1: "show me"** (spec_reader_show_me_figures_v1 §7, §8). A request may
carry a goal in the learner's words (``goal_text``; ``goal_author`` is set on
the server only: ``learner`` for the box, ``tutor`` only for a goal the
tutor's stored answer wrote), with a passage (a joint request: the anchor's
context exactly as before, plus the goal) or without one. With no passage the
request is grounded in the learner's books (:func:`ground`: the sources
service's verified retrieval, ``find_sources_for_caller(intent="explain",
verify=True)``, at most :data:`GROUNDING_PASSAGES` passages, each with its
neighbours; exam and held-out material is withheld inside it and every kept
span is rechecked here) and its home is where the learner was reading
(``reading_at``). Nothing found: it is built anyway with ``grounding`` none,
forced an illustration that quotes nothing, and labelled "not from your
books". A goal and its grounding enter the author's context, its prompt
version (``+show-me-v1``) and the reuse key; an RW5a/b request (no goal, an
anchor) is built, prompted and hashed exactly as before. Every request,
built or reused, appends one ``figure_requests`` row (what was asked, the
derived policy, the grounding and its manifest). ``figures.show_me_enabled``
off: a goal is refused and a figure built from one is not listed.

**RW5d P2: the sketch tier** (spec_reader_show_me_figures_v1 §8.4, §9).
With ``figures.sketch_enabled`` (and the engine ready on this machine:
:func:`learnloop.figures.sketch_engine.engine_ready`), the author may answer
``sketch`` with a :class:`~learnloop.figures.sketch.SketchProgramV1` when the
grammar can't express the idea (its own prompt version and contract,
:class:`~learnloop.figures.routes.FigureAuthorOutputV2`). The program is
verified in the sealed engine (:mod:`.sketch_verify`, steps 1-5) and stored
like any figure (``tier`` sketch, ``spec_version`` sketch-v1, the program in
``spec_json``, the engine digest it was verified under and its check lines);
every build with the tier on appends a ``figure_tier`` judgment (the
author's verdict and its reason) beside ``figure_verified``. A stored sketch
verified under another engine is verified again, by code, before it is
shown (:func:`sketch_rechecked`); one that now fails shows "couldn't run
under this version". Off: the author's contract, prompt and reuse key are
RW5b's byte for byte, and a stored sketch lists as "can't draw this yet".
Sketches are illustrations, never "checked against the book".

**RW5d P2b: the rich tiers, the Manim half** (spec_reader_show_me_figures_v1
§7.2, §8.4, §8.6, §9b.3). The author's menu is :func:`learnloop.figures.rich.tiers_allowed`
(Manim only with ``figures.rich_tiers_enabled``, Linux with ``bwrap``, Manim
installed, the standing opt-in, and a way to start its durable job:
``spawn_rich``); with a rich tier on it the contract is
:class:`~learnloop.figures.routes.FigureAuthorOutputV3` (the medium chosen by
what best explains the idea, ``why_this_tier`` receipted as ``figure_tier``)
under its own prompt version, and the reuse key names the menu and the rich
tier versions; with none, everything is P2's byte for byte. A rich status
stores its optional quick figure at once (verified as any spec or sketch)
and starts the rich job (:func:`learnloop.figures.rich.run_rich_job`) on the
sidecar's queue; the rich figure lands as a second row under the same
request (``fuller_of_id`` naming the quick one), listed as the quick
figure's fuller version (:func:`fuller_state`: one figure line, two
versions). With no quick figure the request's pending line shows
(:func:`rich_pending`) and the same input never asks twice while it builds.
Off: no rich menu entry, no rich keys in a view, and a stored rich figure
lists as "can't show this kind here" (:func:`rich_off_row`).

**RW5d P5: figures ahead of need** (spec_reader_show_me_figures_v1 §10b).
Origin ``prefetch`` is refused from every request except the in-process
prefetch service's (:func:`build_prefetch_figure`, under ``quiet()``): the
same pipeline, recorded with ``build_mode`` prefetch and its decision id, its
gate also holding on ``figures.prefetch_enabled`` and mains power
(:func:`learnloop.figures.power.background_hold`), so switching it off or
unplugging stops it before its next request. A press of the same input
reuses the figure by its input hash (the origin is never in the key). With
the switch off, a prebuilt figure nobody pressed for is not listed.

**Predictions** (:func:`record_prediction`): formative only (W1, tier 2).
Code decides ``matched`` from the observed readout before and after the
prediction's change; a missed one is queued for learner-text gaps as a
``reader_formative`` text (with its "what changed?" when written; one
written after that reading started is its own later text), only
while ``learner_text_gaps.enabled`` and ``reader_formative.enabled``. Nothing
writes an attempt, evidence, mastery, certification, scheduling, FSRS or
adaptive-difficulty state.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import sqlite3
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from learnloop.ai.execution import content_key, gate_model_requests
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.figure_admission import (
    FiguresChanged,
    FiguresGate,
    advanced_panels_enabled,
    author_learner_state_enabled,
    figure_home_keys,
    figures_enabled,
    offers_enabled,
)
from learnloop.figure_admission import sketch_enabled as admission_sketch_enabled
from learnloop.figure_admission import GROUNDING_PASSAGES as ADMISSION_GROUNDING_PASSAGES
from learnloop.figure_admission import show_me_enabled as admission_show_me_enabled
from learnloop.figures import grammar as G
from learnloop.figures import labels as L
from learnloop.figures import manim_figure as M
from learnloop.figures import rich as RICH
from learnloop.figures import routes as R
from learnloop.figures import sketch as K
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.ids import new_ulid

#: The origins a request may name. RW5d P1 adds ``show_me`` (the Reader's
#: intent box with words, or its Ask rail); RW5d P3 adds ``ask`` (CA2's panel
#: on practice, feedback and the workbench: an attempt host, P3); RW5d P4b adds
#: ``teacher`` (a lesson's visual: made only by the lesson service, under a
#: ``teacher`` caller with the lesson as its host, never from an RPC);
#: ``prefetch`` (P5, in-process only) is reserved by migration 224 and refused
#: from every request until its phase lands.
ORIGINS = ("selection", "library", "tutor", "show_me", "ask", "teacher")
RESERVED_ORIGINS = ("prefetch",)
#: The origins no RPC may name (the lesson service's and the prefetch service's own).
SERVICE_ORIGINS = ("teacher", "prefetch")
#: RW5d P4b: a lesson host's tiers (spec §10.4, the teacher spec's "grammar or
#: sketch tier"; P3 ruling R1's precedent): the turn waits on its figure, so no
#: rich (minutes-long, queued) tier is on the author's menu in a lesson.
LESSON_TIERS = ("grammar", "sketch")
#: RW5d P3: the host references that name an attempt (an attempt host's
#: figure has no reading position, so no home: spec §7.2, §13.1).
ATTEMPT_HOST_REFS = ("item_id", "submission_id", "workbench_session_id", "attempt_id")
#: RW5b: the origins an offer builds with (``figures.offers_enabled``).
OFFER_ORIGINS = ("library", "tutor")
#: RW5d: who wrote a goal (set on the server, never taken from a client;
#: ``teacher`` only by the lesson service, RW5d P4b).
GOAL_AUTHORS = ("learner", "tutor", "teacher")
GOAL_CHARS = 600
#: keep: prompt size (:data:`learnloop.figure_admission.GROUNDING_PASSAGES`).
GROUNDING_PASSAGES = ADMISSION_GROUNDING_PASSAGES
GROUNDINGS = ("anchor", "retrieved", "none")
SHOW_ME_VERSION = "show-me-v1"
REQUEST_PREFIX = "frq_"
#: What a figure built with nothing from the learner's books says (RW1c's
#: abstention): a code-owned label (:mod:`.labels`).
NOT_FROM_BOOKS_LABEL = L.NOT_FROM_BOOKS_LABEL
FIGURE_BLOCK_TYPES = frozenset({"Figure", "FigureGroup", "Picture", "PictureGroup"})
#: Paragraphs on each side of the selection sent as context.
CONTEXT_BLOCKS = 2
PASSAGE_CHARS = 6_000
CONTEXT_CHARS = 3_000
NOTE_CHARS = 600
EXPLANATION_CHARS = 600
ANSWER_CHARS = 120
LEDGER_TASK = "figure_verified"
#: Why a reconstruction is an illustration in RW5a (the owner's scope
#: decision, 2026-10-21: "matches the book's equation (checked)" is RW5c's).
RECONSTRUCTION_REASON = "the book check comes in a later version"
PREDICTION_PREFIX = "fpr_"
FIGURE_PREFIX = "fig_"

LABELS = {
    "illustrative": L.ILLUSTRATIVE_LABEL,
}
#: RW5d P2: the spec versions a stored figure may have (a grammar spec or a sketch).
SPEC_VERSIONS = (S.SPEC_VERSION, K.SKETCH_VERSION)
#: RW5d P2b: a rich figure's versions (a Manim figure); listed under its quick
#: figure when it follows one (``fuller_of_id``), else on its own line.
RICH_SPEC_VERSIONS = (M.MANIM_FIG_VERSION,)
ALL_SPEC_VERSIONS = SPEC_VERSIONS + RICH_SPEC_VERSIONS
#: The sketch's code-owned badges (spec §6.6, §9.5; :mod:`.labels`): never "checked against the book".
SKETCH_LABEL = L.SKETCH_LABEL
SKETCH_UNCHECKED_LABEL = L.SKETCH_UNCHECKED_LABEL
SKETCH_NOT_FROM_BOOKS_LABEL = L.SKETCH_NOT_FROM_BOOKS_LABEL
#: What a stored sketch shows while the tier is off, and when a new engine refuses it.
SKETCH_OFF_KIND = "a simulation (figures.sketch_enabled is off)"
ENGINE_CHANGED_REASON = "couldn't run under this version · rebuild"
TIER_LEDGER_TASK = "figure_tier"


class FigureRefused(Exception):
    """A request the Reader may not make (``code``: ``figures_disabled``,
    ``exam_material``, ``region_disabled``, ``revisions_disabled``,
    ``predictions_disabled``, ``offers_disabled`` and ``advanced_disabled``
    (RW5b), ``not_found``, ``validation_error``, ``no_image_input``,
    ``region_unreadable``) or a route that cannot be called (``capped``,
    ``unpriced``, ``unrouted``, ``unavailable``, ``models_off``)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FigureRequest:
    #: The home's extraction (the anchor's, else the reading position's);
    #: None only for an attempt host's figure with no reading position (P3).
    extraction_id: str | None
    span_ids: list[str]
    #: ``{span_id, bbox}``: a learner-drawn box over a figure block.
    region: dict[str, Any] | None = None
    origin: str = "selection"
    supersedes_id: str | None = None
    revision_note: str | None = None
    #: RW5d: the goal in the learner's words (or a tutor's goal).
    goal_text: str | None = None
    #: Who wrote the goal (``learner`` | ``tutor``): set on the server only.
    goal_author: str | None = None
    #: ``{extraction_id, span_id}``: where the learner was reading (the home
    #: of a request with no passage; never sent to the author).
    reading_at: dict[str, Any] | None = None
    #: The host references the server verified (P1: a tutor answer's question event).
    host_ref: dict[str, Any] = field(default_factory=dict)
    #: The caller the server derived (:class:`~learnloop.source_retrieval.policy.CallerContext`).
    caller: Any = None
    #: Fixed grounding passages (``(extraction_id, span_id)``): a tutor goal's
    #: cited spans, or a revision's own; None: retrieved (:func:`ground`).
    grounding_keys: list[tuple[str, str]] | None = None
    #: A revision keeps its base's grounding (``none`` stays ``none``).
    grounding_fixed: str | None = None
    #: RW5d P2: the tiers the author's menu offered (set by the build, never by a client).
    tiers_allowed: tuple[str, ...] = ("grammar",)
    #: RW5d P2b: the menu also needs a way to start the rich job (the sidecar's
    #: durable queue); set by the build from its ``spawn_rich``.
    rich_spawnable: bool = False
    #: RW5d P2b (spec §8.5): "try a different kind of figure" in the note box
    #: of an animation's "not right?": the note re-runs the tier choice
    #: instead of going to the rich author with the earlier program.
    different_kind: bool = False
    #: Learner data-relax 2: the learner's state on the passage's topics
    #: (:func:`learnloop.figures.learner_state.learner_state`), set by the build
    #: with ``figures.author_learner_state`` on, never by a client; None when
    #: off or empty (then payload, prompt and reuse key are the predecessor's).
    learner_state: dict[str, Any] | None = None
    #: What that state was read from (``LearnerStateRead.inputs``: answers,
    #: items, questions, passages), set with it by the build, never sent to a
    #: model: a rich job carries it and checks it again before it sends the
    #: saved state (Codex review F2).
    learner_state_inputs: dict[str, Any] | None = None
    #: RW5d P5: the prefetch decision this build serves (set only by the
    #: in-process prefetch service, :func:`build_prefetch_figure`).
    prefetch_decision_id: str | None = None


@dataclass
class SourceContext:
    passage: list[dict[str, Any]] = field(default_factory=list)
    around: list[dict[str, Any]] = field(default_factory=list)
    #: Every sent span's text (for quote verification).
    span_texts: dict[str, str] = field(default_factory=dict)
    figure_span: str | None = None
    #: RW5d: every ``(extraction_id, span_id)`` sent from retrieved passages
    #: (their neighbours too), rechecked for held-out material on every delivery.
    keys: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Grounding:
    """Where a request's source text comes from (spec §8.3): ``anchor`` (the
    learner chose the passage), ``retrieved`` (found in their books for the
    goal) or ``none`` (nothing found: an illustration that quotes nothing)."""

    mode: str
    keys: list[tuple[str, str]] = field(default_factory=list)
    #: The kept passages as the figure line cites them (source title, section).
    passages: list[dict[str, Any]] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)


def attempt_hosted(request: "FigureRequest") -> bool:
    """RW5d P3: a request made on an attempt host (practice, feedback or the
    workbench: its verified host references name an item or attempt)."""

    return any((request.host_ref or {}).get(name) for name in ATTEMPT_HOST_REFS)


def lesson_hosted(request: "FigureRequest") -> bool:
    """RW5d P4b: a lesson's visual (origin ``teacher``; its host is the lesson,
    so it has no reading position and no home: it shows in the lesson only)."""

    return request.origin == "teacher"


def teacher_visuals_switch(vault: Any) -> bool:
    """RW5d P4b: ``teacher.visuals`` (the teacher's manipulatives)."""

    teacher = getattr(getattr(vault, "config", vault), "teacher", None)
    return bool(getattr(teacher, "visuals", False))


def prediction_home(row: Mapping[str, Any]) -> str | None:
    """The extraction a figure's prediction is recorded under: its home, or
    (RW5d P3, an attempt host's figure with no home) the first book it was
    grounded in; None for a homeless illustration (its predictions are kept
    with no extraction: Codex review F9)."""

    if row.get("extraction_id"):
        return str(row["extraction_id"])
    keys = [key for key in row.get("input_span_keys") or () if len(key) == 2 and key[0]]
    return str(keys[0][0]) if keys else None


def anchored(request: "FigureRequest") -> bool:
    """A request with a passage (a selection or a region)."""

    return bool(request.span_ids or request.region)


def show_me_input(request: "FigureRequest") -> bool:
    """RW5d: a request whose goal or grounding the author is sent (a goal, or no
    passage). Every other request is RW5a/b's, prompted and hashed as before."""

    return request.goal_text is not None or not anchored(request)


def enabled(vault: Any) -> bool:
    """``figures.enabled``: the one predicate (:func:`learnloop.figure_admission.figures_enabled`)."""

    return figures_enabled(vault)


def build_key(vault: Any) -> tuple[Any, ...]:
    """What a build depends on, compared before every request it makes
    (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch,
    the author route as configured, the day's cap and the price, and (RW5b)
    whether the advanced panels are on (the author's prompt depends on it);
    likewise (learner data-relax 2, Codex review F2) whether the author is
    sent the learner's state (``figures.author_learner_state``)."""

    from learnloop.practice_index.paid import plan_route

    section = getattr(vault.config, "figures", None)
    return (str(vault.root), figures_enabled(vault), plan_route(vault, R.AUTHOR_TASK, None),
            getattr(section, "max_daily_cost_usd", None), getattr(section, "price_per_million", None),
            advanced_panels_enabled(vault), sketch_switch(vault), RICH.rich_tiers_switch(vault),
            RICH.manim_tier_ready(vault), author_learner_state_enabled(vault))


def offer_build_key(vault: Any) -> tuple[Any, ...]:
    """An offered build's key (origin ``library`` | ``tutor``): :func:`build_key`
    and ``figures.offers_enabled``, so switching offers off stops it."""

    return (*build_key(vault), offers_enabled(vault))


def offered(request: "FigureRequest") -> bool:
    """A build an offer started (a "not right?" version of an offered figure
    is a revision: ``figures.revisions_enabled`` governs it, not the offers)."""

    return request.origin in OFFER_ORIGINS and request.supersedes_id is None


def show_me_build_key(vault: Any) -> tuple[Any, ...]:
    """A show-me build's key: :func:`build_key` and ``figures.show_me_enabled``."""

    return (*build_key(vault), show_me_enabled(vault))


def key_for(request: "FigureRequest"):
    if request.origin == "prefetch":
        # RW5d P5: a background build also stops when figures ahead of need
        # are switched off (its hold also watches the power).
        from learnloop.figures.power import prefetch_switch

        base = _key_for(request)
        return lambda vault: (*base(vault), prefetch_switch(vault))
    if lesson_hosted(request):
        # RW5d P4b: a lesson's visual is admitted only while the teacher's
        # visuals stay on (switched off since: it asks nothing more).
        base = _key_for(request)
        return lambda vault: (*base(vault), teacher_visuals_switch(vault))
    if attempt_hosted(request):
        # RW5d P3 (Codex review F5): a build on an attempt host is admitted
        # only while figures in attempts stay on (switched off since: it asks
        # nothing more, and its delivery shows nothing).
        base = _key_for(request)
        return lambda vault: (*base(vault), help_enabled(vault))
    return _key_for(request)


def _key_for(request: "FigureRequest"):
    if show_me_input(request):
        if offered(request):
            return lambda vault: (*offer_build_key(vault), show_me_enabled(vault))
        return show_me_build_key
    return offer_build_key if offered(request) else build_key


def _switch(vault: Any, name: str) -> bool:
    return enabled(vault) and bool(getattr(vault.config.figures, name, False))


def predictions_enabled(vault: Any) -> bool:
    return _switch(vault, "predictions_enabled")


def region_enabled(vault: Any) -> bool:
    return _switch(vault, "region_enabled")


def revisions_enabled(vault: Any) -> bool:
    return _switch(vault, "revisions_enabled")


def advanced_enabled(vault: Any) -> bool:
    """RW5b's panels (``figures.advanced_panels_enabled``)."""

    return advanced_panels_enabled(vault)


def figure_offers_enabled(vault: Any) -> bool:
    """RW5b's offers (``figures.offers_enabled``)."""

    return offers_enabled(vault)


def show_me_enabled(vault: Any) -> bool:
    """RW5d's "show me" (``figures.show_me_enabled``; :func:`learnloop.figure_admission.show_me_enabled`)."""

    return admission_show_me_enabled(vault)


def help_enabled(vault: Any) -> bool:
    """RW5d P3: ``figures.help_kind_enabled`` (:func:`learnloop.figure_admission.help_kind_enabled`)."""

    from learnloop.figure_admission import help_kind_enabled

    return help_kind_enabled(vault)


def sketch_switch(vault: Any) -> bool:
    """RW5d P2's switch (``figures.sketch_enabled`` under ``figures.enabled``)."""

    return admission_sketch_enabled(vault)


def sketch_enabled(vault: Any) -> bool:
    """The sketch tier as offered on this machine: its switch, and the engine
    present with its pinned digest (spec §7.2: an unavailable tier is left
    out of the author's menu)."""

    if not sketch_switch(vault):
        return False
    from learnloop.figures.sketch_engine import engine_ready

    return engine_ready()


def rich_enabled(vault: Any) -> bool:
    """RW5d P2b's switch (``figures.rich_tiers_enabled`` under ``figures.enabled``)."""

    return RICH.rich_tiers_switch(vault)


def rich_row(row: Mapping[str, Any]) -> bool:
    """RW5d P2b: a stored rich figure (a Manim figure)."""

    return row.get("tier") in RICH.RICH_TIERS or row.get("spec_version") in RICH_SPEC_VERSIONS


#: What a stored figure that uses an RW5b panel shows while the panels are off.
ADVANCED_OFF_KIND = "a panel kind that is switched off (figures.advanced_panels_enabled)"


# ---------------------------------------------------------------------------
# Exam protection: the one predicate
# ---------------------------------------------------------------------------

def withheld_message(vault: Any, repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str | None:
    """The refusal when any of the spans (or the whole reading) is exam or
    held-out material (``exam_material(...).withheld``), else None: the
    shared :func:`~learnloop.content.sources.exam_material.spans_withheld`,
    which learner-text gaps ask too (fix round 2, F1)."""

    from learnloop.content.sources.exam_material import spans_withheld

    return spans_withheld(vault, repository, extraction_id, span_ids)


def _figure_spans(row: Mapping[str, Any]) -> list[str]:
    """Every span a figure was built from: the selection, the region's and
    the crop's block, and the complete manifest of what the author was sent
    (the paragraphs around it too: a figure may show a neighbour's quoted
    assumption; Codex review F1)."""

    spans = [str(span) for span in row.get("span_ids") or ()]
    region = row.get("region") or {}
    if region.get("span_id"):
        spans.append(str(region["span_id"]))
    if row.get("asset_id"):
        spans.append(str(row["asset_id"]))
    spans += [str(span) for span in row.get("input_span_ids") or ()]
    return list(dict.fromkeys(spans))


def keys_withheld(vault: Any, repository: Repository, keys: Sequence[Sequence[str]]) -> str | None:
    """RW5d: the refusal when any ``(extraction_id, span_id)`` (a retrieved
    passage in any source, or its neighbour) is held out now, else None: the
    one predicate, asked per source."""

    by_extraction: dict[str, list[str]] = {}
    for key in keys:
        if len(key) == 2 and key[0]:
            by_extraction.setdefault(str(key[0]), []).append(str(key[1]))
    for extraction_id, spans in by_extraction.items():
        message = withheld_message(vault, repository, extraction_id, spans)
        if message is not None:
            return message
    return None


def row_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None:
    """A stored figure's held-out refusal now, else None: its home's spans and
    (RW5d) every retrieved passage it was built from, across sources. A figure
    with no home (P3's practice hosts) is checked through its keys alone."""

    message = None
    if row.get("extraction_id"):
        message = withheld_message(vault, repository, row["extraction_id"], _figure_spans(row))
    elif not row.get("input_span_keys") and (row.get("grounding") or "anchor") != "none":
        return "That figure has no source to check, so it isn't shown."
    message = message or keys_withheld(vault, repository, row.get("input_span_keys") or ())
    if message is None and row.get("id"):
        # RW5d (Codex review F4): a figure with no passage is also checked at
        # every place it lands (its homes: never sent to the author, so not in
        # its input manifest), as the request itself was.
        homes = figure_homes(repository, row)
        if homes is None:
            return "That figure's place in the book is unreadable, so it isn't shown."
        message = keys_withheld(vault, repository, homes)
    # Learner data-relax 2 (Codex re-review F2): a rich figure whose author
    # was sent the learner's state keeps what that state was read from; it
    # goes out only while none of that is protected now.
    return message or RICH.stored_learner_state_withheld(vault, repository, row)


def figure_homes(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]] | None:
    """Where a figure with no passage lands (:func:`learnloop.figure_admission.figure_home_keys`):
    every recorded request's reading position; empty for an anchored figure."""

    if row.get("span_ids") or row.get("region"):
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return figure_home_keys(connection, str(row["id"]))


def show_me_row(row: Mapping[str, Any]) -> bool:
    """A figure built from a goal or with no anchor (RW5d): absent while ``figures.show_me_enabled`` is off."""

    return row.get("goal_text") is not None or (row.get("grounding") or "anchor") != "anchor"


def figure_withheld(vault: Any, repository: Repository, figure_id: str) -> bool:
    """Whether a stored figure may not go out now (its row is gone, or any
    span it was built from is held out, or (RW5d) it is a show-me figure
    while show me is off). Fails closed."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        return True
    if show_me_row(row) and not show_me_enabled(vault):
        return True
    return row_withheld(vault, repository, row) is not None


# ---------------------------------------------------------------------------
# The source context (text and the crop only)
# ---------------------------------------------------------------------------

def source_context(vault: Any, repository: Repository, request: FigureRequest) -> SourceContext:
    from learnloop.content.sources.exam_material import exam_material

    ir = repository.load_document_ir(request.extraction_id)
    if ir is None:
        raise FigureRefused("not_found", "That source is not open in the Reader.")
    blocks = list(ir.blocks)
    index = {block.span_id: position for position, block in enumerate(blocks)}
    wanted = [span for span in request.span_ids if span in index]
    if request.region and request.region.get("span_id") in index and request.region["span_id"] not in wanted:
        wanted.append(str(request.region["span_id"]))
    if not wanted:
        raise FigureRefused("validation_error", "The selection names no passage of this source.")
    wanted.sort(key=lambda span: index[span])
    material = exam_material(vault, repository)
    context = SourceContext()
    for span in wanted:
        block = blocks[index[span]]
        text = " ".join((block.text or "").split())
        context.passage.append({"span_id": span, "type": block.block_type, "text": text[:PASSAGE_CHARS]})
        context.span_texts[span] = block.text or ""
        if block.block_type in FIGURE_BLOCK_TYPES and context.figure_span is None:
            context.figure_span = span
    first, last = index[wanted[0]], index[wanted[-1]]
    neighbours = blocks[max(0, first - CONTEXT_BLOCKS):first] + blocks[last + 1:last + 1 + CONTEXT_BLOCKS]
    for block in neighbours:
        if block.span_id in context.span_texts or material.covers(request.extraction_id, block.span_id):
            continue
        context.around.append({"span_id": block.span_id, "type": block.block_type,
                               "text": " ".join((block.text or "").split())[:CONTEXT_CHARS]})
        context.span_texts[block.span_id] = block.text or ""
    return context


def passages_context(vault: Any, repository: Repository, grounding: Grounding) -> SourceContext:
    """RW5d: the retrieved passages as the author is sent them (spec §8.2,
    §8.3): each kept block with the paragraphs around it (held-out ones left
    out), keyed ``extraction_id:span_id`` so a quote is verified against the
    right block of the right book. Nothing for ``none``."""

    from learnloop.content.sources.exam_material import exam_material

    context = SourceContext()
    if grounding.mode != "retrieved" or not grounding.keys:
        return context
    material = exam_material(vault, repository)
    titles = {(str(item.get("extraction_id")), str(item.get("span_id"))): item.get("source_title")
              for item in grounding.passages}
    documents: dict[str, Any] = {}
    placed: list[tuple[str, list[Any], int]] = []
    for extraction_id, span_id in grounding.keys:
        if extraction_id not in documents:
            documents[extraction_id] = repository.load_document_ir(extraction_id)
        ir = documents[extraction_id]
        if ir is None:
            continue
        blocks = list(ir.blocks)
        index = {block.span_id: position for position, block in enumerate(blocks)}
        if span_id not in index or material.covers(extraction_id, span_id):
            continue
        key = f"{extraction_id}:{span_id}"
        if key in context.span_texts:
            continue
        block = blocks[index[span_id]]
        entry: dict[str, Any] = {"span_id": key, "type": block.block_type,
                                 "text": " ".join((block.text or "").split())[:PASSAGE_CHARS]}
        if titles.get((extraction_id, span_id)):
            entry["source"] = str(titles[(extraction_id, span_id)])[:200]
        context.passage.append(entry)
        context.span_texts[key] = block.text or ""
        context.keys.append((extraction_id, span_id))
        placed.append((extraction_id, blocks, index[span_id]))
    # Then the paragraphs around each (a kept passage is never repeated as a neighbour).
    for extraction_id, blocks, position in placed:
        for neighbour in blocks[max(0, position - CONTEXT_BLOCKS):position] + blocks[position + 1:position + 1 + CONTEXT_BLOCKS]:
            near = f"{extraction_id}:{neighbour.span_id}"
            if near in context.span_texts or material.covers(extraction_id, neighbour.span_id):
                continue
            context.around.append({"span_id": near, "type": neighbour.block_type,
                                   "text": " ".join((neighbour.text or "").split())[:CONTEXT_CHARS]})
            context.span_texts[near] = neighbour.text or ""
            context.keys.append((extraction_id, str(neighbour.span_id)))
    return context


#: ``(vault, repository, query, *, caller, **kwargs) -> SourceHits``: the
#: sources service's verified retrieval (injected in tests).
FindSources = Callable[..., Any]


def _find_sources(vault: Any, repository: Repository, query: str, **kwargs: Any) -> Any:
    from learnloop.source_retrieval.find_sources import find_sources_for_caller

    return find_sources_for_caller(vault, repository, query, **kwargs)


def _reading_learning_objects(vault: Any, repository: Repository, reading_at: Mapping[str, Any] | None) -> list[str]:
    """The learning objects of the passage the learner was reading (retrieval context only)."""

    if not reading_at or not reading_at.get("extraction_id") or not reading_at.get("span_id"):
        return []
    try:
        from learnloop.source_retrieval.reader_tutor import passage_learning_objects

        return list(passage_learning_objects(vault, repository, extraction_id=str(reading_at["extraction_id"]),
                                             span_ids=[str(reading_at["span_id"])]))
    except Exception:  # noqa: BLE001 - context for ranking only; none is fine
        return []


def _passage_ref(hit: Mapping[str, Any]) -> dict[str, Any]:
    return {"extraction_id": str(hit.get("extraction_id")), "span_id": str(hit.get("span_id")),
            "source_id": hit.get("source_id"), "source_title": hit.get("source_title"), "section": hit.get("section"),
            "page": hit.get("page")}


def _with_sources(repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each passage with its source's id and title (Codex review F8: the
    Reader's citation chips peek in this book and open another as a detour,
    which needs the source). Read from the stored extraction; a passage whose
    source cannot be read keeps what it had."""

    found: dict[str, tuple[str | None, str | None]] = {}
    shown = []
    for passage in passages:
        extraction_id = str(passage.get("extraction_id") or "")
        if extraction_id not in found:
            source_id, title = None, None
            try:
                run = repository.get_extraction_run(extraction_id) or {}
                revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
                source_id = revision.get("source_id")
                title = (repository.get_source_artifact(str(source_id)) or {}).get("display_title") if source_id else None
            except Exception:  # noqa: BLE001 - the chip only loses its detour
                pass
            found[extraction_id] = (source_id, title)
        source_id, title = found[extraction_id]
        shown.append({**passage, "source_id": passage.get("source_id") or source_id,
                      "source_title": passage.get("source_title") or title})
    return shown


def ground(vault: Any, repository: Repository, request: FigureRequest, *, find: FindSources | None = None
           ) -> Grounding:
    """A request's grounding (spec §8.3). With a passage, the anchor. With
    fixed keys (a tutor goal's cited spans, a revision's), those still allowed
    now. Otherwise the sources service's verified retrieval for the goal,
    under the caller's derived policy (exam material is withheld inside it),
    the reading position's learning objects as context: its verified picks,
    at most :data:`GROUNDING_PASSAGES`, each rechecked here. Nothing verified
    (or retrieval unavailable): ``none``, built anyway and labelled."""

    from learnloop.source_retrieval.policy import CallerContext

    if anchored(request):
        return Grounding("anchor")
    if request.grounding_keys is not None:
        given = list(dict.fromkeys((str(key[0]), str(key[1])) for key in request.grounding_keys))
        kept = [key for key in given if keys_withheld(vault, repository, [key]) is None][:GROUNDING_PASSAGES]
        mode = "none" if request.grounding_fixed == "none" or not kept else "retrieved"
        manifest = {"source": "given", "given": [list(key) for key in given],
                    "kept": [list(key) for key in kept] if mode == "retrieved" else []}
        if mode == "none":
            return Grounding("none", manifest=manifest)
        return Grounding("retrieved", kept, _with_sources(repository, [{"extraction_id": key[0], "span_id": key[1]}
                                                                      for key in kept]), manifest)
    caller = request.caller or CallerContext(kind="reader")
    query = request.goal_text or ""
    try:
        hits = (find or _find_sources)(
            vault, repository, query, caller=caller, intent="explain", verify=True, limit=GROUNDING_PASSAGES,
            learning_object_ids=_reading_learning_objects(vault, repository, request.reading_at),
            owner_id=f"figure_grounding:{content_key([query, request.extraction_id])[:24]}")
    except FiguresChanged:
        raise
    except Exception as exc:  # noqa: BLE001 - nothing found is an honest "not from your books"
        return Grounding("none", manifest={"source": "retrieval", "status": f"unavailable: {type(exc).__name__}"})
    manifest: dict[str, Any] = {"source": "retrieval", "status": getattr(hits, "status", "ok"),
                                "find_sources": dict(getattr(hits, "manifest", None) or {})}
    if manifest["status"] != "ok":
        # Unverified hits are not grounding: only the verification's picks are.
        return Grounding("none", manifest={**manifest, "kept": []})
    kept: list[tuple[str, str]] = []
    passages: list[dict[str, Any]] = []
    for hit in list(getattr(hits, "hits", None) or ()):
        key = (str(hit.get("extraction_id") or ""), str(hit.get("span_id") or ""))
        if not all(key) or key in kept or keys_withheld(vault, repository, [key]) is not None:
            continue
        kept.append(key)
        passages.append(_passage_ref(hit))
        if len(kept) >= GROUNDING_PASSAGES:
            break
    manifest["kept"] = [list(key) for key in kept]
    if not kept:
        return Grounding("none", manifest=manifest)
    return Grounding("retrieved", kept, _with_sources(repository, passages), manifest)


def _decode(render: str | None) -> tuple[str, bytes] | None:
    if not render or not render.startswith("data:") or ";base64," not in render:
        return None
    header, data = render.split(";base64,", 1)
    try:
        return header[len("data:"):], base64.b64decode(data, validate=True)
    except (ValueError, TypeError):
        return None


def crop_image(repository: Repository, request: FigureRequest, context: SourceContext
               ) -> tuple[tuple[str, bytes] | None, str | None, list[float] | None]:
    """``(image, asset span, clipped region box)``: a region's crop only, or
    the figure block's crop; nothing for a selection with no figure."""

    from learnloop.reader.span_view import build_block_region

    if request.region:
        found = build_block_region(repository, request.extraction_id, str(request.region["span_id"]),
                                   bbox=[float(value) for value in request.region.get("bbox") or ()])
        image = _decode(found.get("region_render"))
        if image is None:
            raise FigureRefused("region_unreadable", "LearnLoop couldn't crop that region of the page.")
        return image, str(request.region["span_id"]), found.get("bbox")
    if context.figure_span is not None:
        found = build_block_region(repository, request.extraction_id, context.figure_span)
        if found.get("reason") == "crop":
            return _decode(found.get("region_render")), context.figure_span, None
    return None, None, None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def shown_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """The row as RW5a may show it: nothing in RW5a produces "verified", and a
    stored one (from a build before the owner's scope decision of
    2026-10-21) is shown as the illustration RW5a's rules make it."""

    if store.shown_verification(row.get("verification")) == row.get("verification"):
        return row
    report = row.get("verification_report") or {}
    return {**row, "verification": V.ILLUSTRATIVE,
            "verification_report": {**report, "reason": RECONSTRUCTION_REASON}}


#: The properties code checked before a figure shows, as closed keys (final
#: round, High 1): the Reader's code-owned frame names each with its own
#: words, so nothing model-written can reach the frame's badge.
PROPERTY_CHECKS = ("values_finite", "integrates_to_one", "sums_to_one", "nonnegative", "bounded", "finite",
                   "monotone_nondecreasing", "shaded_areas")


def _advanced_kinds(row: Mapping[str, Any]) -> list[str]:
    """The RW5b panel kinds a stored figure's spec uses (none when it has no spec)."""

    if not row.get("spec_json"):
        return []
    try:
        return list(S.advanced_kinds(json.loads(row["spec_json"])))
    except (TypeError, ValueError, AttributeError):
        return []


def advanced_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5b: a shown figure that uses a heat map, vector field, trajectory or
    iterated map, while ``figures.advanced_panels_enabled`` is off, is the
    unsupported-kind state ("can't draw this yet"); its spec never goes out."""

    if advanced_enabled(vault) or row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    try:
        kinds = S.advanced_kinds(json.loads(row["spec_json"]))
    except (TypeError, ValueError):
        return row
    if not kinds:
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": ADVANCED_OFF_KIND, "spec_json": None,
            "verification_report": {**report, "reason": f"{', '.join(dict.fromkeys(kinds))} is switched off"}}


def sketch_row(row: Mapping[str, Any]) -> bool:
    """RW5d P2: a stored sketch."""

    return row.get("tier") == "sketch" or row.get("spec_version") == K.SKETCH_VERSION


def sketch_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5d P2: a shown sketch while ``figures.sketch_enabled`` is off (or the
    engine can't run here) is the unsupported-kind state ("can't draw this
    yet"); its program never goes out."""

    if not sketch_row(row) or row.get("verification") not in store.SHOWN or sketch_enabled(vault):
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": SKETCH_OFF_KIND, "spec_json": None,
            "verification_report": {**report, "reason": "the sketch tier is switched off"}}


def rich_off_row(vault: Any, row: Mapping[str, Any]) -> Mapping[str, Any]:
    """RW5d P2b: a shown rich figure while ``figures.rich_tiers_enabled`` is
    off is the unsupported-kind state ("can't show this kind here"); its
    program and video never go out."""

    if not rich_row(row) or row.get("verification") not in store.SHOWN or rich_enabled(vault):
        return row
    report = dict(row.get("verification_report") or {})
    return {**row, "verification": V.UNSUPPORTED, "unsupported_kind": RICH.RICH_OFF_KIND, "spec_json": None,
            "media_file_name": None, "verification_report": {**report, "reason": "the rich tiers are switched off",
                                                             "rich_off": True}}


_RECHECKED: dict[tuple[str, str, str], dict[str, Any]] = {}
_RECHECKED_GUARD = threading.Lock()
#: The input revision a re-verification judgment records (Codex review F8):
#: the program, the engine it was run under and (Codex review F11, round 3)
#: the verifier's report version.
REVERIFY_VERSION = "sketch-reverify-v1"


def reverify_hash(spec_json: str, engine_sha256: str, verifier_version: str | None = None) -> str:
    from learnloop.figures.sketch_verify import VERIFIER_REPORT_VERSION

    verifier = verifier_version or VERIFIER_REPORT_VERSION
    return hashlib.sha256(f"{REVERIFY_VERSION}\n{engine_sha256}\n{verifier}\n{spec_json}".encode("utf-8")).hexdigest()


def _stored_verifier(row: Mapping[str, Any]) -> str | None:
    """The verifier report version a stored row's report was made by (None:
    before the version existed)."""

    found = (row.get("verification_report") or {}).get("verifier_version")
    return str(found) if found else None


def _record_reverification(repository: Repository | None, row: Mapping[str, Any], cached: Mapping[str, Any],
                           engine_sha256: str) -> None:
    """Codex review F8: an engine re-verification is a verifier verdict, so
    it is appended to ``judgment_ledger`` (task ``figure_verified``, judge
    ``verifier``) before the figure is delivered, superseding the figure's
    last verdict on that question. Keyed by the program, the engine and the
    verifier version (:func:`reverify_hash`): once per (figure, engine,
    verifier), however often it is listed or the process restarts. The
    rationale is its provenance: both engine digests and verifier versions,
    the outcome's reason or check count, and the digest of the report the
    delivery uses."""

    if repository is None or getattr(repository, "_read_only", False):
        return
    figure_id = str(row["id"])
    input_hash = reverify_hash(str(row["spec_json"]), engine_sha256)
    report = cached.get("report") or {}
    outcome = str(cached["outcome"])
    summary = (f"{len(report.get('checks') or [])} checks" if outcome == V.ILLUSTRATIVE
               else str(report.get("reason") or "it no longer passes"))
    digest = hashlib.sha256(json.dumps(report, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    from learnloop.figures.sketch_verify import VERIFIER_REPORT_VERSION

    rationale = (f"re-verified under sketch engine {engine_sha256[:12]} and {VERIFIER_REPORT_VERSION} (built under "
                 f"{str(row.get('engine_sha256') or '?')[:12]} and {_stored_verifier(row) or 'an unversioned verifier'})"
                 f"; report {digest[:16]}; {summary}")
    with repository.atomic():
        connection = repository.connection()
        verdicts = store.figure_verdicts(connection, LEDGER_TASK, figure_id)
        if any(found["judge"] == "verifier" and found["input_hash"] == input_hash for found in verdicts):
            return
        append_judgment(connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id,
                        judge="verifier", input_hash=input_hash, verdict=outcome, rationale=rationale[:400],
                        supersedes_id=verdicts[-1]["id"] if verdicts else None, created_at=utc_now_iso(None))


def sketch_rechecked(row: Mapping[str, Any], repository: Repository | None = None) -> Mapping[str, Any]:
    """Spec §8.5, engine upgrades: a shown sketch verified under another
    engine, or (Codex review F11, round 3) by another verifier version
    (:data:`.sketch_verify.VERIFIER_REPORT_VERSION`: a report made before a
    verification fix may carry a check line the fixed verifier would not
    give), is verified again by code (no model call) before it is shown. One
    that passes shows with this engine's and verifier's check lines; one that
    fails shows "couldn't run under this version · rebuild", never as
    checked. Remembered per (figure, engine, verifier) in this process (a row
    is never rewritten); with a ``repository`` the verdict is appended to
    ``judgment_ledger`` first (Codex review F8,
    :func:`_record_reverification`)."""

    from learnloop.figures import sketch_verify as SV
    from learnloop.figures.sketch_engine import ENGINE_SHA256

    if not sketch_row(row) or row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    if row.get("engine_sha256") == ENGINE_SHA256 and _stored_verifier(row) == SV.VERIFIER_REPORT_VERSION:
        return row
    key = (str(row["id"]), ENGINE_SHA256, SV.VERIFIER_REPORT_VERSION)
    with _RECHECKED_GUARD:
        cached = _RECHECKED.get(key)
    if cached is None:
        try:
            compiled = K.parse_sketch(row["spec_json"])
            report = SV.verify_sketch(compiled)
            cached = {"outcome": report.outcome, "report": report.as_dict()}
        except Exception as exc:  # noqa: BLE001 - a program that no longer parses or runs fails closed
            cached = {"outcome": V.FAILED, "report": {"reason": f"{type(exc).__name__}", "tier": "sketch"}}
        _record_reverification(repository, row, cached, ENGINE_SHA256)
        with _RECHECKED_GUARD:
            _RECHECKED[key] = cached
    previous = dict(row.get("verification_report") or {})
    if cached["outcome"] != V.ILLUSTRATIVE:
        return {**row, "verification": V.FAILED, "spec_json": None,
                "verification_report": {**previous, "reason": ENGINE_CHANGED_REASON, "engine_changed": True}}
    # The stored report (its quote checks and assumptions, verified against the
    # passages at build time) with this engine's run and check lines over it.
    fresh = cached["report"]
    report = {**previous, **{key: fresh.get(key) for key in (
        "outcome", "checks", "not_covered", "unnamed_elements", "settings", "grid_points", "samples",
        "dropped_predictions", "engine_sha256", "verifier_version", "read_steps", "tested")}}
    return {**row, "verification_report": report, "checks": report.get("checks") or [],
            "engine_sha256": ENGINE_SHA256}


def worded_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """Spec §9b.4 when a stored figure is presented (Reader follow-ups Nov 1b,
    Codex review F3): a figure stored before the free-text label rule (or by
    any path that skipped it) is shown, listed and reused without its
    label-like text, as :mod:`.labels` rules for an answer that still
    violates after its repair call: what it shows emptied, a label-like
    assumption (in the spec and in the stored report) dropped, and a Manim
    figure's label-like title left out and each label-like transcript line
    replaced in code's words. The stored row (the paid output) is never
    rewritten. Unchanged (the same object) when nothing reads like a label."""

    if row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return row
    raw = row["spec_json"]
    spec_json = L.strip_json(raw)
    if rich_row(row):
        try:
            program = json.loads(spec_json) if isinstance(spec_json, str) else None
        except ValueError:
            program = None
        if isinstance(program, dict):
            title, narration = program.get("title"), program.get("narration_md")
            worded = {"title": "" if L.label_like(title) is not None else title,
                      "narration_md": L.strip_lines(narration) if narration else narration}
            if worded != {"title": title, "narration_md": narration}:
                spec_json = json.dumps({**program, **worded}, ensure_ascii=False)
    report = row.get("verification_report") or {}
    assumptions = report.get("assumptions")
    kept = [item for item in assumptions if L.label_like(item.get("text") if isinstance(item, Mapping) else item)
            is None] if isinstance(assumptions, list) else assumptions
    if spec_json is raw and kept == assumptions:
        return row
    return {**row, "spec_json": spec_json, "verification_report": {**report, "assumptions": kept}}


def drawable_now(vault: Any, row: Mapping[str, Any]) -> bool:
    """A stored figure that can be drawn as configured now (RW5b's panels and
    RW5d P2's sketch tier both on when it needs them)."""

    return advanced_off_row(vault, row) is row and sketch_off_row(vault, row) is row and rich_off_row(vault, row) is row


def property_checks(report: Mapping[str, Any]) -> list[str]:
    """The closed keys of the checks a shown figure passed (§8.3 steps 1-2)."""

    held = {str(entry.get("kind")) for entry in report.get("invariants") or () if entry.get("holds")}
    passed = {"values_finite"} | held
    if report.get("shades"):
        passed.add("shaded_areas")
    return [key for key in PROPERTY_CHECKS if key in passed]


def _label(row: Mapping[str, Any]) -> str:
    verification = row["verification"]
    if verification == "illustrative" and rich_row(row):
        if row.get("grounding") == "none":
            return RICH.MANIM_NOT_FROM_BOOKS_LABEL
        report = row.get("verification_report") or {}
        return RICH.MANIM_LABEL if report.get("checks") else RICH.MANIM_UNCHECKED_LABEL
    if verification == "unsupported" and (row.get("verification_report") or {}).get("rich_off"):
        return RICH.RICH_OFF_LABEL
    if verification == "illustrative" and sketch_row(row):
        if row.get("grounding") == "none":
            return SKETCH_NOT_FROM_BOOKS_LABEL
        report = row.get("verification_report") or {}
        return SKETCH_LABEL if report.get("checks") else SKETCH_UNCHECKED_LABEL
    if verification == "failed" and (row.get("verification_report") or {}).get("engine_changed"):
        return ENGINE_CHANGED_REASON
    if verification == "illustrative" and row.get("grounding") == "none":
        return NOT_FROM_BOOKS_LABEL
    if verification in LABELS:
        return LABELS[verification]
    reason = str((row.get("verification_report") or {}).get("reason") or "")
    if verification == "unsupported":
        kind = row.get("unsupported_kind") or "something the figure language can't express"
        return f"can't draw this yet — needs {kind} · noted"
    return f"couldn't build a reliable version of this ({reason or 'its checks did not pass'})"


def _prediction_view(found: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if found is None:
        return None
    observed = found.get("observed") or {}
    return {"prediction_id": found["id"], "figure_id": found.get("figure_id"),
            "extraction_id": found.get("extraction_id"), "prediction_index": found.get("prediction_index"),
            "learner_answer": found["learner_answer"], "matched": found["matched"],
            "before": observed.get("before"), "after": observed.get("after"), "answer": observed.get("answer"),
            "explanation_text": found.get("explanation_text")}


def _anchor_span(row: Mapping[str, Any], asked: Mapping[str, Any] | None,
                 home: Mapping[str, Any] | None) -> str | None:
    """Where a figure shows: under the selection's last block; a region's
    figure (no selected text) under the region's block (Codex review F2);
    RW5d: a figure with no passage under the passage the learner was reading
    (``home``, else its own request's reading position)."""

    region = row.get("region") or {}
    home = home or (asked or {}).get("reading_at") or {}
    return (list(row.get("span_ids") or ()) or [region.get("span_id") or home.get("span_id")])[-1]


def figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int = 1,
                home: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A figure as the Reader shows it. The spec goes out as JSON text (its
    keys are the spec's own), and only for a shown figure. A prediction's
    answer is never sent before the learner answers it. A stored "verified"
    shows as an illustration (:func:`shown_row`).

    ``home`` (RW5d, Codex review F3): where a figure with no passage lands in
    this view (the request delivering it, or one placement in a listing);
    unset, its own request's reading position."""

    row = rich_off_row(vault, sketch_off_row(vault, advanced_off_row(vault, shown_row(row))))
    if sketch_enabled(vault):
        row = sketch_rechecked(row, repository)
    # After the re-verification (it reads the stored program): the free-text
    # label rule as presented (spec §9b.4, Codex review F3, Nov 1b).
    row = worded_row(row)
    asked = _figure_request(repository, row)
    view: dict[str, Any] = {
        "figure_id": row["id"], "extraction_id": row["extraction_id"], "span_ids": list(row.get("span_ids") or ()),
        "anchor_span_id": _anchor_span(row, asked, home),
        "region": row.get("region"),
        "origin": row["origin"], "verification": row["verification"], "kind": row.get("kind"),
        "label": _label(row), "reason": (row.get("verification_report") or {}).get("reason") or None,
        "unsupported_kind": row.get("unsupported_kind"), "supersedes_id": row.get("supersedes_id"),
        "revision_note": row.get("revision_note"), "versions": versions, "created_at": row["created_at"],
        "spec_json": None, "demonstrates": None, "assumptions": [], "predictions": [], "property_checks": [],
    }
    if show_me_enabled(vault):
        # RW5d (absent while show me is off, so the view is RW5a/b's key for key):
        # the goal in its author's voice, the grounding and the cited passages.
        manifest = (asked or {}).get("grounding_manifest") or {}
        view.update({
            "goal_text": row.get("goal_text"), "goal_author": (asked or {}).get("goal_author"),
            "grounding": row.get("grounding") or "anchor",
            "passages": [dict(item) for item in manifest.get("passages") or ()]
            if (row.get("grounding") or "anchor") == "retrieved" else [],
        })
    if sketch_enabled(vault):
        # RW5d P2 (absent while the tier is off, so the view is P1's key for key).
        view["tier"] = "sketch" if sketch_row(row) else "grammar"
        view["sketch"] = None
    if rich_enabled(vault):
        # RW5d P2b (absent while the rich tiers are off, so the view is P2's key
        # for key): the tier, a Manim figure's video and checks, and on a quick
        # figure the state of its fuller version (one figure line, two versions).
        view["tier"] = "manim" if rich_row(row) else ("sketch" if sketch_row(row) else "grammar")
        view["manim"] = None
        view["fuller"] = None if rich_row(row) else fuller_state(vault, repository, row)
    if row["verification"] not in store.SHOWN or not row.get("spec_json"):
        return view
    if rich_row(row):
        return _manim_view(row, view)
    if sketch_row(row):
        return _sketch_view(vault, repository, row, view)
    compiled = S.parse_spec(row["spec_json"])
    report = row.get("verification_report") or {}
    view["spec_json"] = row["spec_json"]
    view["property_checks"] = property_checks(report)
    view["demonstrates"] = compiled.spec.demonstrates
    view["assumptions"] = report.get("assumptions") or [
        {"text": item.text, "span_id": None, "quote": None} for item in compiled.spec.assumptions]
    dropped = set(report.get("dropped_predictions") or ())
    answered: dict[int, dict[str, Any]] = {}
    if predictions_enabled(vault):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            answered = {found["prediction_index"]: found
                        for found in store.predictions_for_figure(connection, str(row["id"]))}
        for index, (prediction, _node) in enumerate(compiled.predictions):
            if index in dropped:
                continue
            outcome = S.prediction_outcome(compiled, index)
            choices = ([{"value": value, "label": S.DIRECTION_LABELS[value]} for value in S.DIRECTIONS]
                       if prediction.observe.kind == "direction"
                       else [{"value": label, "label": label} for label in outcome["choices"]])
            view["predictions"].append({
                # The change itself is in spec_json (parameter names are the
                # spec's own keys, which the wire's camel-casing would rename).
                "index": index, "prompt": prediction.prompt, "kind": prediction.observe.kind, "choices": choices,
                "answered": _prediction_view(answered.get(index)),
            })
    return view


def _sketch_view(vault: Any, repository: Repository, row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]:
    """A shown sketch as the Reader draws it: the program (its code runs in
    the desktop's sealed engine), the code-owned check lines and the *not
    covered* line, and its predictions (answers never sent first)."""

    from learnloop.figures import sketch_verify as SV
    from learnloop.figures.sketch_engine import ENGINE_SHA256

    compiled = K.parse_sketch(row["spec_json"])
    report = row.get("verification_report") or {}
    program = compiled.program
    view["spec_json"] = row["spec_json"]
    view["demonstrates"] = program.demonstrates
    view["assumptions"] = report.get("assumptions") or [
        {"text": item.text, "span_id": None, "quote": None} for item in program.assumptions]
    view["sketch"] = {
        "engine_sha256": ENGINE_SHA256, "seed": SV.VERIFY_SEED,
        "checks": [dict(check) for check in report.get("checks") or ()],
        "not_covered": list(report.get("not_covered") or ()),
        "unnamed_elements": int(report.get("unnamed_elements") or 0),
        "settings": int(report.get("settings") or 0),
        # Fix round 4 (the independent sandbox review): the read schedule every
        # run follows and the digest of every read verification checked, per
        # grid point (values in declared order, so no name is camelized); the
        # desktop compares its own and withdraws the checks on a difference.
        "read_steps": [int(step) for step in report.get("read_steps") or ()],
        "tested": [{"values": [float(v) for v in entry.get("values") or ()],
                    "steps": [int(s) for s in entry.get("steps") or ()],
                    "digests": [str(d) for d in entry.get("digests") or ()]}
                   for entry in report.get("tested") or ()],
    }
    dropped = set(report.get("dropped_predictions") or ())
    if predictions_enabled(vault):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            answered = {found["prediction_index"]: found
                        for found in store.predictions_for_figure(connection, str(row["id"]))}
        for index, prediction in enumerate(program.predictions):
            if index in dropped:
                continue
            kind = prediction.observe.kind
            choices = ([{"value": value, "label": S.DIRECTION_LABELS[value]} for value in S.DIRECTIONS]
                       if kind == "direction" else
                       [{"value": label, "label": label} for label in prediction.observe.choices])
            # target_step (Codex review F5): the clock step the answer is
            # graded at, so the desktop's playback stops exactly there.
            view["predictions"].append({"index": index, "prompt": prediction.prompt, "kind": kind,
                                        "choices": choices, "answered": _prediction_view(answered.get(index)),
                                        "target_step": SV.prediction_target_step(compiled, index)})
    return view


def _manim_view(row: Mapping[str, Any], view: dict[str, Any]) -> dict[str, Any]:
    """A shown Manim figure (RW5d P2b, spec §6.8): the content-addressed video
    (played over ``llmedia://``), its title and transcript, the code-owned
    check lines and *the video itself is not checked frame by frame*. The
    scene code never goes out."""

    report = row.get("verification_report") or {}
    try:
        program = json.loads(row["spec_json"])
    except (TypeError, ValueError):
        program = {}
    view["demonstrates"] = program.get("demonstrates") or None
    view["assumptions"] = report.get("assumptions") or []
    view["manim"] = {
        "media_file_name": row.get("media_file_name"),
        "title": program.get("title") or "",
        "narration_md": program.get("narration_md") or "",
        "duration_seconds": report.get("duration_seconds"),
        "checks": [dict(check) for check in report.get("checks") or ()],
        "not_checkable": [dict(entry) for entry in report.get("not_checkable") or ()],
        "not_covered": list(report.get("not_covered") or (RICH.MANIM_NOT_COVERED,)),
    }
    return view


def fuller_state(vault: Any, repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None:
    """RW5d P2b (spec §6.8, §8.6): the fuller version of a quick figure, or
    None when it has none: ``ready`` (with the rich figure's view),
    ``failed`` (code's reason; the quick version stays), ``pending`` (the
    job's phase), ``waiting_for_plan`` or ``cancelled``."""

    if row.get("verification") not in store.SHOWN:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.fuller_rows(connection, str(row["id"]))
    # Codex re-review F2: a fuller version whose author's learner state was
    # read from something protected now is not delivered (nor named failed).
    rows = [found for found in rows if RICH.stored_learner_state_withheld(vault, repository, found) is None]
    shown = [found for found in rows if found["verification"] in store.SHOWN]
    if shown:
        rich = shown[-1]
        if rich_off_row(vault, rich) is not rich:
            return None
        rich_view = figure_view(vault, repository, rich)
        return {"state": "ready", "figure": rich_view, "tier": "manim", "phase": None, "reason": None,
                "rich_job_id": None}
    job = RICH.rich_job_for_quick(repository, str(row["id"]))
    intent = (row.get("verification_report") or {}).get(RICH_INTENT_KEY)
    build_mode = ((job or {}).get("payload") or {}).get("build_mode") if job is not None \
        else (intent or {}).get("build_mode") if isinstance(intent, dict) else None
    # Landing ruling R1 (final verify F18): a fuller version built ahead of need that nobody
    # pressed for is marked, so the Reader bounds its reads for it by the prefetch lifetime
    # (pressed figures keep their polling). Present only then: every other view is unchanged.
    speculative = {"speculative": True} if build_mode == "prefetch" and not _prebuilt_pressed(repository, row) \
        else {}
    if job is not None:
        state = RICH.job_state(job)
        if state["state"] != "done":
            return {"tier": "manim", "figure": None, "phase": state.get("phase"), "reason": state.get("reason"),
                    **state, **speculative}
    if rows:
        failed = rows[-1]
        return {"state": "failed", "tier": "manim", "figure": None, "phase": None, "rich_job_id": None,
                "reason": str((failed.get("verification_report") or {}).get("reason") or "")[:300] or None}
    if job is None and isinstance(intent, dict):
        # Codex review F8: the intent committed but no job was started (the
        # sidecar stopped first, or the enqueue failed): reading this source
        # starts it (resume_rich_intents); until then the line says so.
        if build_mode == "prefetch" and _prefetch_intent_refused(vault, repository, intent):
            # Landing ruling R1 (final verify F18): a prebuild's intent is started by a read
            # only while background admission holds (resume_rich_intents); refused (battery,
            # the switch off, its passage held out) nothing will start it, so it is not pending.
            return None
        return {"state": "pending", "tier": "manim", "figure": None, "phase": "writing", "reason": None,
                "rich_job_id": None, **speculative}
    return None


def _prefetch_intent_refused(vault: Any, repository: Repository, intent: Mapping[str, Any]) -> bool:
    """Landing ruling R1: whether background admission refuses a prebuild's unqueued rich
    intent now: figures ahead of need off, this machine not on mains, or its input held out.
    (Foreground work only delays it, so it is not a refusal.)"""

    from learnloop.figures.power import power_state, prefetch_switch
    from learnloop.figures.rich import _withheld

    if not prefetch_switch(vault) or not power_state().on_mains:
        return True
    return _withheld(vault, repository, intent.get("base") or {}) is not None


def _figure_request(repository: Repository, row: Mapping[str, Any]) -> dict[str, Any] | None:
    """The ``figure_requests`` row a figure was built for (RW5d), or None (RW5a/b rows before 224)."""

    if not row.get("request_id"):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.request(connection, str(row["request_id"]))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

#: The origin every reuse key names (RW5b Codex review F2). A figure of a
#: block is the same figure whether the learner selected it or a library or
#: tutor offer named it (the author is sent the same input), so it is built
#: and paid for once; the row keeps its own ``origin``. RW5a's keys were all
#: made under ``selection``, so they are unchanged.
REUSE_ORIGIN = "selection"


def request_hash(request: FigureRequest, context: SourceContext, image_digest: str | None, *,
                 advanced: bool = False, grounding: Grounding | None = None, sketch: bool = False,
                 tiers: Sequence[str] | None = None, rich_runtime: str | None = None,
                 learner_state: Mapping[str, Any] | None = None) -> str:
    """The reuse key: the spec and prompt versions (RW5b's panels have their
    own prompt version, so RW5a's hashes are unchanged while they are off)
    and everything the author is sent (never the origin: :data:`REUSE_ORIGIN`).

    RW5d (spec §8.5): a show-me request's key also names the goal
    (whitespace-normalized, case kept) and who wrote it, the grounding and the
    kept passages' keys (their texts are the passage and around above); its
    prompt version carries ``+show-me-v1``. A request with no goal and an
    anchor hashes exactly as before migration 224 (G-SM4). A request with no
    passage names its home (``extraction_id``, where the learner was
    reading), so it lands and lists there.

    RW5d P2 (spec §8.5): with the sketch tier on, the prompt version carries
    ``+sketch-v1`` and the key names the tier versions (``sketch-v1`` and the
    engine digest); off, it is exactly P1's.

    RW5d P2b (spec §8.5): with a rich tier on the menu, the prompt version
    carries ``+rich-v1`` and the menu, and the key names ``tiers_allowed`` and
    the rich tier versions (``manim-fig-v1``, the Manim version and the
    sandbox profile); with none on the menu, it is exactly P2's. A revision
    asking for a different kind of figure names it (Codex re-review F13).

    Learner data-relax 2: a non-empty ``learner_state`` (what the author is
    sent about the learner) puts ``+learner-v1`` on the prompt version and
    names the state's hash; None or empty, the key is exactly the
    predecessor's (a learner with no state keeps today's keys and reuse)."""

    show_me = show_me_input(request)
    learner = bool(learner_state)
    key: dict[str, Any] = {
        "spec_version": S.SPEC_VERSION,
        "prompt_version": R.author_prompt_version(advanced=advanced, show_me=show_me, sketch=sketch, tiers=tiers,
                                                  learner=learner),
        "extraction_id": request.extraction_id,
        "span_ids": list(request.span_ids), "region": request.region, "origin": REUSE_ORIGIN,
        "passage": context.passage, "around": context.around, "image_sha256": image_digest,
        "supersedes_id": request.supersedes_id, "revision_note": request.revision_note,
    }
    if request.different_kind:
        # Codex re-review F13: "try a different kind of figure" is routed (and
        # prompted) apart from the ordinary correction with the same note, so
        # it is its own input: never that correction's pending job or its
        # stored animation. Absent otherwise: every other key is unchanged.
        key["different_kind"] = True
    if show_me:
        grounding = grounding or Grounding("anchor")
        key.update({"show_me": SHOW_ME_VERSION, "goal_text": request.goal_text, "goal_author": request.goal_author,
                    "grounding": grounding.mode, "grounding_keys": [list(item) for item in grounding.keys]})
    if sketch:
        from learnloop.figures.sketch_engine import ENGINE_SHA256

        key["sketch"] = {"program_version": K.SKETCH_VERSION, "engine_sha256": ENGINE_SHA256}
    menu = R.rich_menu(tiers)
    if menu is not None:
        key["rich"] = {"tiers_allowed": list(menu),
                       "manim": {"version": M.MANIM_FIG_VERSION, "runtime": rich_runtime}
                       if "manim" in menu else None}
    if learner:
        from learnloop.figures.learner_state import state_hash

        key["learner_state"] = state_hash(learner_state)
    return content_key(key)


def _reusable(vault: Any, repository: Repository, connection: Any, input_hash: str,
              other_hash: str | Sequence[str]) -> dict[str, Any] | None:
    """The figure a build reuses: this input's under the current prompt
    version, else (Codex review F2) a SHOWN one of the same input under the
    other prompt version when it can be drawn now. RW5a's figures are drawable
    with the panels on, and a panels-era figure with none of the new kinds is
    drawable with them off; so switching the panels never pays again for a
    figure already on the page. Another version's "can't draw this yet" is
    never reused: it was that prompt's verdict (the panels may draw it now).
    Nor is a rich figure whose author's learner state was read from something
    protected now (Codex re-review F2)."""

    found = store.reusable(connection, input_hash, SPEC_VERSIONS)
    if found is not None:
        return found
    # RW5d P2b: a rich figure built with no quick figure is this input's own
    # figure (its fuller version is reached through the quick one instead).
    rich_only = store.reusable(connection, input_hash, RICH_SPEC_VERSIONS) if rich_enabled(vault) else None
    if (rich_only is not None and not rich_only.get("fuller_of_id") and drawable_now(vault, rich_only)
            and RICH.stored_learner_state_withheld(vault, repository, rich_only) is None):
        return rich_only
    # RW5d P2: the same input under the other settings of the panels and of
    # the sketch tier; only a shown figure that can be drawn now.
    for other_key in ([other_hash] if isinstance(other_hash, str) else list(other_hash)):
        other = store.reusable(connection, other_key, SPEC_VERSIONS)
        if other is not None and other["verification"] in store.SHOWN and drawable_now(vault, other):
            return other
    return None


#: RW5d P5: set only inside :func:`build_prefetch_figure` (the in-process
#: prefetch service); origin ``prefetch`` is refused everywhere else.
_PREFETCH_BUILD: ContextVar[bool] = ContextVar("learnloop_figures_prefetch_build", default=False)
#: Who may write a prefetch build's goal: the prefetch judge, or a lesson plan's teacher.
PREFETCH_GOAL_AUTHORS = ("prefetch", "teacher")


def _validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest:
    if not enabled(vault):
        raise FigureRefused("figures_disabled", "Explorable figures are switched off (figures.enabled).")
    prefetch = request.origin == "prefetch" and _PREFETCH_BUILD.get()
    if request.origin in RESERVED_ORIGINS and not prefetch:
        raise FigureRefused("validation_error", f"Figures with origin {request.origin!r} are not made here.")
    if prefetch:
        return _validated_prefetch(vault, request)
    if request.origin not in ORIGINS:
        raise FigureRefused("validation_error", f"Unknown figure origin {request.origin!r}.")
    lesson_host = lesson_hosted(request)
    if lesson_host:
        # RW5d P4b (spec §7.1, G-SM5): a teacher's goal only from the lesson
        # service: a teacher caller (the lesson's derived policy), the lesson
        # as host, the passages it was delivered as fixed grounding, no
        # passage selection and no "not right?" in a lesson.
        caller = request.caller
        if getattr(caller, "kind", None) != "teacher" or not (request.host_ref or {}).get("lesson_id"):
            raise FigureRefused("validation_error", "Figures with origin 'teacher' are made in a lesson only.")
        if request.span_ids or request.region or request.supersedes_id is not None or not request.grounding_keys:
            raise FigureRefused("validation_error", "A lesson's figure rests on the passages the lesson delivered.")
        if not teacher_visuals_switch(vault):
            raise FigureRefused("teacher_visuals_disabled", "The teacher's figures are switched off "
                                                            "(teacher.visuals).")
    if offered(request) and not figure_offers_enabled(vault):
        raise FigureRefused("offers_disabled", "Offered figures are switched off (figures.offers_enabled).")
    goal = " ".join(str(request.goal_text or "").split())[:GOAL_CHARS] or None
    goal_author = request.goal_author if goal is not None else None
    if goal is not None:
        if not show_me_enabled(vault):
            raise FigureRefused("show_me_disabled", "\"Show me\" in your own words is switched off "
                                                    "(figures.show_me_enabled).")
        # Who wrote it is the server's: the learner for the box and the rail,
        # the tutor only for its stored answer's goal (G-SM5).
        expected = {"selection": "learner", "show_me": "learner", "tutor": "tutor", "ask": "learner",
                    "teacher": "teacher"}.get(request.origin)
        # RW5d P5: a revision of a prebuilt figure keeps its stored goal and who wrote it.
        revised_prebuilt = (request.origin == "selection" and request.supersedes_id is not None
                            and goal_author in PREFETCH_GOAL_AUTHORS)
        if (expected is None or goal_author != expected) and not revised_prebuilt:
            raise FigureRefused("validation_error", "That figure goal can't come from here.")
    elif request.origin in ("show_me", "ask", "teacher"):
        raise FigureRefused("validation_error", "Say what you want to see first.")
    attempt_host = attempt_hosted(request)
    if request.origin == "ask" and not attempt_host:
        raise FigureRefused("validation_error", "A figure from the Ask panel needs its practice item.")
    spans = [str(span) for span in dict.fromkeys(request.span_ids) if span][:40]
    reading_at = None
    if request.reading_at and request.reading_at.get("extraction_id") and request.reading_at.get("span_id"):
        reading_at = {"extraction_id": str(request.reading_at["extraction_id"]),
                      "span_id": str(request.reading_at["span_id"])}
    if not spans and not request.region:
        if goal is None:
            raise FigureRefused("validation_error", "Select a passage, an equation or a figure first.")
        if reading_at is None and not attempt_host and not lesson_host:
            # A figure with no passage lands under the passage the learner was
            # reading (spec §7.2, "Home"); RW5d P3: an attempt host's figure
            # with no reading position has no home (it lands in the panel);
            # RW5d P4b: a lesson's figure has none either (it shows in the lesson).
            raise FigureRefused("validation_error", "Open a passage first, so the figure has a place to land.")
    region = None
    if request.region is not None:
        if not region_enabled(vault):
            raise FigureRefused("region_disabled", "Selecting a region of a figure is switched off (figures.region_enabled).")
        bbox = request.region.get("bbox")
        if not request.region.get("span_id") or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise FigureRefused("validation_error", "A region needs its figure block and a box.")
        region = {"span_id": str(request.region["span_id"]), "bbox": [round(float(value), 2) for value in bbox]}
    note = None
    if request.supersedes_id is not None:
        if not revisions_enabled(vault):
            raise FigureRefused("revisions_disabled", "Asking for a better version is switched off (figures.revisions_enabled).")
        note = " ".join(str(request.revision_note or "").split())[:NOTE_CHARS] or None
    if lesson_host:
        reading_at = None
    extraction_id = str(request.extraction_id) if (spans or region) else (
        str(reading_at["extraction_id"]) if reading_at is not None else None)
    keys = None if request.grounding_keys is None else [
        (str(key[0]), str(key[1])) for key in request.grounding_keys if len(key) == 2 and key[0] and key[1]]
    return FigureRequest(extraction_id=extraction_id, span_ids=spans, region=region,
                         origin=request.origin, supersedes_id=request.supersedes_id, revision_note=note,
                         goal_text=goal, goal_author=goal_author, reading_at=reading_at,
                         host_ref=dict(request.host_ref or {}), caller=request.caller, grounding_keys=keys,
                         grounding_fixed=request.grounding_fixed if request.grounding_fixed in GROUNDINGS else None,
                         different_kind=bool(request.different_kind and request.supersedes_id is not None))


def _validated_prefetch(vault: Any, request: FigureRequest) -> FigureRequest:
    """RW5d P5: a prefetch build's request, as the prefetch service made it:
    an anchor (a passage of a book), an optional goal by the prefetch judge
    or a lesson plan's teacher, never an attempt host, a region or a revision."""

    from learnloop.figures.power import prefetch_switch

    if not prefetch_switch(vault):
        raise FigureRefused("prefetch_disabled", "Figures ahead of need are switched off (figures.prefetch_enabled).")
    spans = [str(span) for span in dict.fromkeys(request.span_ids) if span][:40]
    if not request.extraction_id or not spans:
        raise FigureRefused("validation_error", "A figure built ahead of need needs its passage.")
    if attempt_hosted(request) or request.region is not None or request.supersedes_id is not None:
        raise FigureRefused("validation_error", "A figure built ahead of need is a passage's, never an attempt's.")
    goal = " ".join(str(request.goal_text or "").split())[:GOAL_CHARS] or None
    if goal is not None:
        if not show_me_enabled(vault):
            raise FigureRefused("show_me_disabled", "\"Show me\" in your own words is switched off "
                                                    "(figures.show_me_enabled).")
        if request.goal_author not in PREFETCH_GOAL_AUTHORS:
            raise FigureRefused("validation_error", "That figure goal can't come from here.")
    return FigureRequest(extraction_id=str(request.extraction_id), span_ids=spans, origin="prefetch",
                         goal_text=goal, goal_author=request.goal_author if goal is not None else None,
                         caller=request.caller, prefetch_decision_id=request.prefetch_decision_id)


def check_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest:
    """Validate a request and refuse held-out material, on the request path,
    before any job or call (the handler's first step; the build repeats it)."""

    request = _validated_request(vault, repository, request)
    spans = [*request.span_ids, *([request.region["span_id"]] if request.region else [])]
    if not anchored(request):
        # RW5d: with no passage, the home (the passage the learner was
        # reading): a figure never lands on held-out material.
        spans = [str((request.reading_at or {}).get("span_id"))]
    # RW5d P3: an attempt host's figure with no reading position has no home
    # to check (its retrieved passages are checked as they are kept).
    message = withheld_message(vault, repository, request.extraction_id, spans) if request.extraction_id else None
    if message is None and request.grounding_keys:
        message = keys_withheld(vault, repository, request.grounding_keys)
    if message is not None:
        raise FigureRefused("exam_material", message)
    if request.supersedes_id is not None:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            base = store.figure(connection, request.supersedes_id)
        if base is None or base["extraction_id"] != request.extraction_id:
            raise FigureRefused("not_found", "That figure is not on this source.")
        if show_me_row(base) and not show_me_enabled(vault):
            raise FigureRefused("show_me_disabled", "\"Show me\" in your own words is switched off "
                                                    "(figures.show_me_enabled).")
        if row_withheld(vault, repository, base) is not None:
            raise FigureRefused("exam_material", "That figure's passage is held out now.")
        if rich_row(base) and not rich_enabled(vault):
            # RW5d P2b: an animation is revised only with the rich tiers on
            # (it lists as "can't show this kind here" while they are off).
            raise FigureRefused("rich_disabled", "That figure is an animation, and rich figures are switched off "
                                                 "(figures.rich_tiers_enabled).")
        if rich_row(base) and not request.different_kind and (
                base.get("verification") not in store.SHOWN or not base.get("spec_json")):
            raise FigureRefused("not_found", "That animation is not shown, so there is no version to improve: "
                                             "ask again.")
        if sketch_row(base) and not sketch_enabled(vault):
            # RW5d P2: a sketch is revised only by the sketch tier (RW5b's
            # contract can't write one back).
            raise FigureRefused("sketch_disabled", "That figure is a simulation, and the sketch tier is switched "
                                                   "off (figures.sketch_enabled).")
        if not advanced_enabled(vault) and _advanced_kinds(base):
            # Codex review F4: a figure that uses a panel kind switched off
            # (listed as "can't draw this yet", or a failed attempt at one) is
            # not revised: its spec would be sent under RW5a's prompt, which
            # can only re-emit what is refused, two paid calls for nothing.
            raise FigureRefused("advanced_disabled", "That figure uses a panel kind that is switched off "
                                                     "(figures.advanced_panels_enabled).")
    return request


@dataclass
class BuildOutcome:
    #: The figure as the Reader shows it (None: only a rich figure is being built).
    view: dict[str, Any] | None
    reused: bool
    author_calls: int = 0
    #: RW5d P2b: a rich build with no quick figure (its pending line): the
    #: request, where it lands, the job and its phase.
    rich: dict[str, Any] | None = None


#: ``(payload, origin) -> job id``: starts a rich job on the sidecar's durable
#: queue (RW5d P2b); unset, no rich tier is offered.
SpawnRich = Callable[[dict[str, Any]], str]


def _author_context(request: FigureRequest, context: SourceContext, image_digest: str | None,
                    previous: Mapping[str, Any] | None, problems: Sequence[str], *, request_id: str,
                    grounding: Grounding | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        # One request's own id: "try again" after a failure asks afresh (a
        # paid answer is recovered only for the same request).
        "request_id": request_id,
        "request": "region of a figure" if request.region else (
            "figure" if context.figure_span else "equation or passage"),
        "passage": context.passage,
        "around": context.around,
        "image": {"sha256": image_digest, "note": "the figure's crop (only the selected region) is attached"}
        if image_digest else None,
    }
    if show_me_input(request):
        # RW5d: the goal, labelled with who wrote it, and where the passages
        # come from (spec §8.2); a request with no passage says so.
        if not anchored(request):
            payload["request"] = "what the learner asked to see (no passage selected)"
        if request.goal_text is not None:
            payload["learner_request"] = {"text": request.goal_text, "written_by": request.goal_author}
        payload["grounding"] = (grounding or Grounding("anchor")).mode
    if previous is not None:
        if rich_row(previous):
            # RW5d P2b (spec §8.5): "try a different kind of figure" on an
            # animation: what it showed, never its program (the tier choice
            # runs again with the note).
            try:
                program = json.loads(previous.get("spec_json") or "{}")
            except (TypeError, ValueError):
                program = {}
            payload["earlier_version"] = {"animation": {"title": program.get("title") or "",
                                                        "demonstrates": program.get("demonstrates") or "",
                                                        "brief": program.get("brief") or ""},
                                          "verification": previous.get("verification"),
                                          "learner_asks_for_a_different_kind": True}
        elif sketch_row(previous):
            # RW5d P2: an earlier sketch goes back as its program.
            payload["earlier_version"] = {"sketch_json": previous.get("spec_json") or "",
                                          "verification": previous.get("verification")}
        else:
            payload["earlier_version"] = {"spec_json": previous.get("spec_json") or "",
                                          "verification": previous.get("verification")}
        payload["learner_note"] = request.revision_note or ""
    if problems:
        payload["problems_with_the_last_attempt"] = list(problems)[:12]
    if request.learner_state:
        # Learner data-relax 2: where the learner stands on the passage's
        # topics (protected work never in it); absent with none.
        payload["learner_state"] = request.learner_state
    return payload


def build_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None = None,
                 clock: Clock | None = None, live_vault: Callable[[], Any] | None = None,
                 find: FindSources | None = None, spawn_rich: SpawnRich | None = None) -> BuildOutcome:
    """Build one figure (module docstring). Raises :class:`FigureRefused`.

    ``live_vault`` gives the vault as configured now (the sidecar's loaded
    vault; unset, the vault is reloaded from disk): the build's
    :class:`~learnloop.figure_admission.FiguresGate` compares it with the
    start before every physical request and before the row is stored.
    ``find`` (RW5d) is the grounding retrieval (the sources service's, unset).
    ``spawn_rich`` (RW5d P2b) starts a rich job on the durable queue; unset,
    no rich tier is on the author's menu."""

    request = check_request(vault, repository, request)
    if lesson_hosted(request):
        # RW5d P4b: a lesson host is grammar and sketch only (LESSON_TIERS):
        # no rich job is started from a lesson, whatever the caller passed.
        spawn_rich = None
    request.rich_spawnable = spawn_rich is not None
    # One gate for the whole request (Codex review F1): grounding's rewrite,
    # embedding and verification calls, the reuse lookup and the author are
    # each admitted against the configuration as it is NOW (``live_vault``),
    # so switching figures or show me off stops the request wherever it is.
    # RW5d P5: a background build also holds on the switch, mains power and
    # foreground work, and (Codex review F2) on the figure author's route
    # being the plan as configured NOW: a prebuild is never metered.
    hold = _prefetch_build_hold(author_client) if request.origin == "prefetch" else None
    gate = FiguresGate(vault, key_for(request), live_vault=live_vault, hold=hold)
    try:
        with gate_model_requests(gate):
            return _build(vault, repository, request, gate=gate, author_client=author_client, clock=clock, find=find,
                          spawn_rich=spawn_rich)
    except FiguresChanged as exc:
        raise FigureRefused("figures_changed", str(exc)) from exc


#: RW5d P5 (Codex review F2): a prebuild whose figure author is not the plan now.
PREFETCH_AUTHOR_NOT_PLAN = ("Not built ahead of need: the figure author is not the ChatGPT plan now, and a figure "
                            "built ahead of need is never metered.")


def _prefetch_build_hold(author_client: Any | None) -> Callable[[Any], str | None]:
    from learnloop.figures.power import background_hold
    from learnloop.practice_index.paid import plan_route

    def hold(current: Any) -> str | None:
        reason = background_hold(current)
        if reason is None and plan_route(current, R.AUTHOR_TASK, author_client).billing != "subscription":
            return PREFETCH_AUTHOR_NOT_PLAN
        return reason

    return hold


def _build(vault: Any, repository: Repository, request: FigureRequest, *, gate: FiguresGate,
           author_client: Any | None, clock: Clock | None, find: FindSources | None,
           spawn_rich: SpawnRich | None = None) -> BuildOutcome:
    grounding = ground(vault, repository, request, find=find)
    # Rechecked against the live configuration (G-SM2; Codex review F1): the
    # switches as they are now, after grounding's calls.
    gate.check("grounding")
    context = source_context(vault, repository, request) if anchored(request) else \
        passages_context(vault, repository, grounding)
    previous = None
    versions = 1
    if request.supersedes_id is not None:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            previous = store.figure(connection, request.supersedes_id)
        versions = _chain_length(repository, request.supersedes_id) + 1
    envelope = R.daily_envelope(vault, repository, clock=clock)
    # The owner is named once the input is hashed (below): asking whether the
    # route reads images comes first.
    author = R.FigureRoute(vault, repository, R.AUTHOR_TASK, client=author_client, envelope=envelope,
                           owner_id="figure:pending", max_calls=R.MAX_AUTHOR_ATTEMPTS)
    image, asset_id, clipped = crop_image(repository, request, context)
    if image is not None and not author.reads_images():
        if request.region:
            problem = author.problem()
            if problem is not None:
                raise FigureRefused(problem.reason, problem.message)
            raise FigureRefused("no_image_input",
                                "The figure route can't read images, so a region can't be sent "
                                "(ai.routing.figure_author needs a profile with \"image\" in input_modalities).")
        image, asset_id = None, None
    if clipped is not None and request.region is not None:
        request.region = {**request.region, "bbox": [round(float(value), 2) for value in clipped]}
    digest = hashlib.sha256(image[1]).hexdigest() if image is not None else None
    advanced = advanced_enabled(vault)
    sketch = sketch_enabled(vault)
    # RW5d P2b: the menu (spec §7.2): a rich tier only with a way to start its job.
    menu = RICH.tiers_allowed(vault, sketch=sketch) if spawn_rich is not None else (
        ("grammar", "sketch") if sketch else ("grammar",))
    request.tiers_allowed = menu
    tiers = menu if R.rich_menu(menu) is not None else None
    runtime = RICH.runtime_digest(vault) if tiers is not None and "manim" in tiers else None
    # Learner data-relax 2: the learner's state on the passage's topics
    # (None with the switch off or nothing to say: everything below is then
    # the predecessor's byte for byte).
    read = _learner_state(vault, repository, request, context, grounding)
    request.learner_state = read.state if read is not None else None
    request.learner_state_inputs = read.inputs if read is not None and read.state else None
    learner = request.learner_state
    input_hash = request_hash(request, context, digest, advanced=advanced, grounding=grounding, sketch=sketch,
                              tiers=tiers, rich_runtime=runtime, learner_state=learner)
    # The same input under the other settings (RW5b's panels, RW5d P2's
    # sketch tier, RW5d P2b's rich menu): a shown figure drawable now is never
    # paid for again.
    other_hash = [request_hash(request, context, digest, advanced=a, grounding=grounding, sketch=k, tiers=t,
                               rich_runtime=runtime, learner_state=learner)
                  for a, k, t in ((not advanced, sketch, tiers), (advanced, not sketch, None),
                                  (not advanced, not sketch, None), (advanced, sketch, None),
                                  (not advanced, sketch, None)) if (a, k, t) != (advanced, sketch, tiers)]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reused = _reusable(vault, repository, connection, input_hash, other_hash)
        seen = store.latest_for_input(connection, input_hash, SPEC_VERSIONS)
    if reused is not None:
        return _reused(vault, repository, reused, request=request, grounding=grounding, clock=clock, gate=gate)
    pending = _rich_pending(vault, repository, request, input_hash)
    if pending is not None:
        # RW5d P2b: this input's rich figure is being built with no quick one:
        # the same pending line, no second call. The request is recorded (what
        # was asked; no figure named yet, as a rich-only request's own row).
        gate.check("reuse")
        try:
            with repository.atomic():
                store.insert_request(repository.connection(), _request_row(request, grounding, figure_id=None,
                                                                           clock=clock))
        except sqlite3.Error as exc:
            raise FigureRefused(STORAGE_BUSY, "LearnLoop couldn't record this request just now (the vault is "
                                              "busy). Try again: nothing is built twice.") from exc
        return pending
    # One build per input at a time (Codex review F7): an identical request
    # made while one runs waits for it and takes its figure, with no call.
    with _building(repository, input_hash):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            # Reread inside the lock (fix round 2, F7): a build that committed
            # between the reads above left `reused` empty but `seen` naming
            # its row, so only this read can tell its figure is reusable.
            reused = _reusable(vault, repository, connection, input_hash, other_hash)
            latest = store.latest_for_input(connection, input_hash, SPEC_VERSIONS)
            # Codex review F7: a stored rich failure (a rich-only build that
            # used both attempts) starts the next generation too, so "try
            # again" asks the author, and then the rich author, afresh.
            generation = store.builds_for_input(connection, input_hash, ALL_SPEC_VERSIONS)
        if reused is not None:
            return _reused(vault, repository, reused, request=request, grounding=grounding, clock=clock, gate=gate)
        if latest is not None and (seen is None or latest["id"] != seen["id"]):
            return _reused(vault, repository, latest, request=request, grounding=grounding, clock=clock, gate=gate)
        # The request's identity is its input and its retry generation, never
        # a fresh id: rerun after a crash between a paid answer and its row,
        # the same prompt recovers that answer (its checkpoint or receipt)
        # with no second request; a stored failure starts the next
        # generation, so "try again" asks afresh.
        request_id = content_key({"input_hash": input_hash, "generation": generation})
        if previous is not None and rich_row(previous) and not request.different_kind:
            # RW5d P2b (spec §8.5, Codex review F11): "not right?" on an
            # animation goes to the rich author with the note and the earlier
            # program, never back to the tier choice.
            return _rich_revision(vault, repository, request, context, grounding, previous=previous,
                                  input_hash=input_hash, digest=digest, asset_id=asset_id, generation=generation,
                                  request_id=request_id, spawn_rich=spawn_rich, gate=gate, clock=clock)
        author.bind_owner(f"figure:{request_id}")
        return _author_and_store(vault, repository, request, context, author, previous=previous,
                                 versions=versions, image=image, asset_id=asset_id, digest=digest,
                                 input_hash=input_hash, request_id=request_id, clock=clock, gate=gate,
                                 advanced=advanced, grounding=grounding, sketch=sketch, tiers=tiers,
                                 spawn_rich=spawn_rich, generation=generation)


def _learner_state(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                   grounding: Grounding) -> Any:
    """Learner data-relax 2: what the author is told about the learner on
    the passage's topics and what it was read from
    (:func:`.learner_state.read_learner_state`), or None (switched off or no
    topics; an empty or unreadable state: the predecessor's build)."""

    from learnloop.figures import learner_state as LS

    if not LS.enabled(vault):
        return None
    if anchored(request):
        spans = [*request.span_ids, *([request.region["span_id"]] if request.region else [])]
        los = LS.anchored_learning_objects(vault, repository, extraction_id=request.extraction_id, span_ids=spans)
    else:
        home = request.reading_at or {}
        keys = list(grounding.keys) or [(str(home.get("extraction_id") or ""), str(home.get("span_id") or ""))]
        los = LS.anchored_learning_objects(vault, repository, extraction_id=None, span_ids=(), keys=keys)
    return LS.read_learner_state(vault, repository, los) if los else None


def _rich_pending(vault: Any, repository: Repository, request: FigureRequest, input_hash: str
                  ) -> BuildOutcome | None:
    """A rich-only build of this input still running or waiting (its job is
    pending or waiting for the plan): the request takes its pending line."""

    if not rich_enabled(vault):
        return None
    job = RICH.rich_job_for(RICH.rich_jobs(repository), input_hash=input_hash)
    if job is None or (job.get("payload") or {}).get("fast_figure_id"):
        return None
    state = RICH.job_state(job)
    if state["state"] not in ("pending", "waiting_for_plan"):
        return None
    return BuildOutcome(None, reused=True, rich=_rich_line(request, job, state))


def _rich_line(request: FigureRequest, job: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    base = payload.get("base") or {}
    home = base.get("home") or {}
    spans = list(base.get("span_ids") or ())
    anchor = (spans or [(base.get("region") or {}).get("span_id") or home.get("span_id")])[-1]
    return {"request_id": payload.get("request_id"), "extraction_id": base.get("extraction_id"),
            "anchor_span_id": anchor, "tier": payload.get("tier"), "goal_text": base.get("goal_text"),
            "state": state.get("state"), "phase": state.get("phase"), "reason": state.get("reason"),
            "rich_job_id": job.get("id")}


def retry_rich_job(vault: Any, repository: Repository, job_id: str) -> str:
    """Codex review F9: the error code of a rich job that ended with no row
    and may be requeued (failed, not waiting for the plan, never cancelled),
    or :class:`FigureRefused`. The requeued job is the same build (its
    payload and request identity), so a paid answer is recovered, not paid
    for again."""

    if not rich_enabled(vault):
        raise FigureRefused("rich_disabled", "Rich figures are switched off (figures.rich_tiers_enabled).")
    job = repository.get_ingest_job(job_id)
    if job is None or job.get("job_type") != RICH.RICH_JOB_TYPE:
        raise FigureRefused("not_found", "That animation build is no longer kept.")
    code = str((job.get("error") or {}).get("code") or "")
    if job.get("status") != "failed" or job.get("cancel_requested") or not code:
        raise FigureRefused("not_failed", "That animation build hasn't failed, so there is nothing to try again.")
    payload = job.get("payload") or {}
    if _withheld_payload(vault, repository, payload):
        raise FigureRefused("exam_material", "That figure's passage is held out now.")
    return code


def _withheld_payload(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> bool:
    from learnloop.figures.rich import _withheld

    return _withheld(vault, repository, payload.get("base") or {}) is not None


_BUILDS_GUARD = threading.Lock()
_BUILDS: dict[str, list[Any]] = {}


@contextmanager
def _building(repository: Repository, input_hash: str) -> Iterator[None]:
    """Hold this process's one lock for (vault, input) while a build runs.

    The sidecar is the only builder; across processes the reuse index
    (unique among shown rows) refuses a second row and the stable request
    identity recovers the first paid answer."""

    key = f"{repository.sqlite_path}\0{input_hash}"
    with _BUILDS_GUARD:
        entry = _BUILDS.setdefault(key, [threading.Lock(), 0])
        entry[1] += 1
    try:
        with entry[0]:
            yield
    finally:
        with _BUILDS_GUARD:
            entry[1] -= 1
            if entry[1] == 0:
                _BUILDS.pop(key, None)


def _request_row(request: FigureRequest, grounding: Grounding, *, figure_id: str | None,
                 clock: Clock | None) -> dict[str, Any]:
    """The ``figure_requests`` row of one request (RW5d, spec §13.1): what was
    asked, as normalized, and what the server derived."""

    from learnloop.source_retrieval.policy import CallerContext, derive_policy

    caller = request.caller or CallerContext(kind="tutor" if request.origin == "tutor" else "reader")
    policy, derived_from = derive_policy(caller)
    anchor = {"extraction_id": request.extraction_id, "span_ids": list(request.span_ids),
              **({"region": request.region} if request.region else {})} if anchored(request) else None
    return {
        "id": REQUEST_PREFIX + new_ulid(), "origin": request.origin, "goal_text": request.goal_text,
        "goal_author": request.goal_author, "anchor": anchor, "reading_at": request.reading_at,
        "host_ref": dict(request.host_ref or {}), "policy": policy, "caller_kind": caller.kind,
        "policy_derived_from": derived_from, "grounding": grounding.mode,
        "grounding_manifest": {**grounding.manifest, "kept": [list(key) for key in grounding.keys],
                               "passages": list(grounding.passages)},
        "build_mode": "prefetch" if request.origin == "prefetch" else "pressed",
        "tiers_allowed": list(request.tiers_allowed or ("grammar",)),
        **({"prefetch_decision_id": request.prefetch_decision_id} if request.prefetch_decision_id else {}),
        "figure_id": figure_id,
        "created_at": utc_now_iso(clock),
    }


#: A reused figure's request could not be recorded (the vault is busy): the
#: request fails, retryably, and its retry reuses the same paid figure.
STORAGE_BUSY = "storage_busy"


def _reused(vault: Any, repository: Repository, row: Mapping[str, Any], *, request: FigureRequest | None = None,
            grounding: Grounding | None = None, clock: Clock | None = None,
            gate: FiguresGate | None = None) -> BuildOutcome:
    if gate is not None:
        # The live configuration, as for every other step (Codex review F1).
        gate.check("reuse")
    if request is not None:
        # RW5d: a reused figure's request is recorded too (what was asked, and
        # that it took this figure). Required (Codex review F7): a request
        # that cannot be recorded fails, retryably; its retry reuses this same
        # figure, so nothing is built or paid for twice.
        try:
            with repository.atomic():
                store.insert_request(repository.connection(), _request_row(
                    request, grounding or Grounding("anchor"), figure_id=str(row["id"]), clock=clock))
        except sqlite3.Error as exc:
            raise FigureRefused(STORAGE_BUSY, "LearnLoop couldn't record this request just now (the vault is "
                                              "busy). Try again: the figure is kept, so nothing is built twice.") from exc
    # Delivered where THIS request lands (Codex review F3): a goal-only figure
    # reused from another paragraph of the same book opens at this request's
    # home, not at the first request's.
    home = request.reading_at if request is not None and not anchored(request) else None
    return BuildOutcome(figure_view(vault, repository, row, versions=_chain_length(repository, str(row["id"])),
                                    home=home), reused=True)


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


def _author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                      author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int,
                      image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None, input_hash: str,
                      request_id: str, clock: Clock | None, gate: FiguresGate,
                      advanced: bool = False, grounding: Grounding | None = None,
                      sketch: bool = False, tiers: Sequence[str] | None = None,
                      spawn_rich: SpawnRich | None = None, generation: int = 0) -> BuildOutcome:
    problem = author.problem()
    if problem is not None:
        raise FigureRefused(problem.reason, problem.message)
    grounding = grounding or Grounding("anchor")
    show_me = show_me_input(request)
    images = (image,) if image is not None else ()
    learner = bool(request.learner_state)
    prompt_version = R.author_prompt_version(advanced=advanced, show_me=show_me, sketch=sketch, tiers=tiers,
                                             learner=learner)
    # RW5d P2b: with a rich tier on the menu the contract is V3 (the tier judgment, always receipted).
    v3 = tiers is not None
    request.tiers_allowed = tuple(tiers) if v3 else (("grammar", "sketch") if sketch else ("grammar",))
    brief: RICH.RichBrief | None = None
    quick_dropped: str | None = None
    problems: list[str] = []
    compiled: S.CompiledFigure | None = None
    report = V.Report()
    output: Any = None
    unsupported: tuple[str, str] | None = None
    # RW5d P2: a sketch answer, verified in the sealed engine.
    sketched: K.CompiledSketch | None = None
    sketch_report: Any = None
    verdict: tuple[str, str] | None = None
    for attempt in range(R.MAX_AUTHOR_ATTEMPTS):
        prompt = R.author_prompt(_author_context(request, context, digest, previous, problems, request_id=request_id,
                                                 grounding=grounding),
                                 advanced=advanced, show_me=show_me, sketch=sketch, tiers=tiers, learner=learner)
        try:
            output = author.ask(prompt, R.output_model(sketch=sketch, tiers=tiers), images=images,
                                metadata={"attempt": attempt + 1, "prompt_version": prompt_version})
        except FiguresChanged:
            raise  # the configuration changed: nothing more is asked, nothing stored
        except R.FigureUnavailable as exc:
            if attempt == 0:
                raise FigureRefused(exc.reason, exc.message) from exc
            break
        except SpendLimitExceeded as exc:
            # The daily envelope refused it before sending (another process
            # spent the rest of the day meanwhile).
            if attempt == 0:
                raise FigureRefused("capped", f"Today's figure budget is used ({exc}).") from exc
            break
        except Exception as exc:  # noqa: BLE001 - a failed call ends the attempts, honestly labelled
            problems = [f"the figure model failed: {type(exc).__name__}"]
            if attempt == 0:
                continue
            break
        status = str(output.status).strip().lower()
        # The free-text label rule (spec §9b.4, P2b ruling R2): free text
        # that reads like a code-owned check label is the repair call's
        # problem, in code's words; still there after it, the figure is
        # shown without that text (a Manim figure's own text: its job).
        labelled = L.label_problems(_free_text(output, status))
        if labelled:
            if attempt < R.MAX_AUTHOR_ATTEMPTS - 1:
                problems = labelled
                continue
            output = _without_label_text(output)
        if v3:
            # RW5d P2b: the status is the medium chosen; why_this_tier its reason.
            menu_statuses = {"spec" if tier == "grammar" else tier for tier in tiers or ()} | {"unsupported"}
            reason = (" ".join(str(output.unsupported_reason or "").split())[:400] if status == "unsupported"
                      else " ".join(str(getattr(output, "why_this_tier", "") or "").split())[:400])
            verdict = (status if status in menu_statuses else "invalid", reason)
            if status not in menu_statuses:
                problems = [f"status {status!r} is not one of the media offered ({sorted(menu_statuses)})"]
                continue
            if status != "unsupported" and not reason:
                problems = ["why_this_tier is empty: say in one sentence why this medium explains the idea best"]
                continue
            if status in RICH.RICH_TIERS:
                brief, brief_problems = RICH.parse_brief(output.rich_json, tiers or (), status,
                                                         grounded=grounding.mode != "none")
                if brief is None:
                    problems = brief_problems
                    continue
                # The optional quick figure (Q20): verified and shown as any spec
                # or sketch; one that fails is dropped (the rich half carries on).
                compiled, sketched, sketch_report = None, None, None
                if str(output.spec_json or "").strip():
                    try:
                        candidate = S.parse_spec(_ungrounded(output.spec_json) if grounding.mode == "none"
                                                 else output.spec_json, advanced=advanced)
                        report = V.verify_numerics(candidate)
                        if report.outcome == V.FAILED:
                            quick_dropped = report.reason
                        else:
                            compiled = candidate
                    except S.SpecError as exc:
                        quick_dropped = exc.problems[0] if exc.problems else "the quick figure is invalid"
                elif sketch and str(getattr(output, "sketch_json", "") or "").strip():
                    try:
                        raw = output.sketch_json
                        candidate_sketch = K.parse_sketch(_ungrounded_sketch(raw) if grounding.mode == "none" else raw)
                        from learnloop.figures import sketch_verify as SV

                        gate.check("sketch")
                        checked = SV.verify_sketch(candidate_sketch, span_texts=context.span_texts)
                        if checked.outcome == V.FAILED:
                            quick_dropped = checked.reason
                        else:
                            sketched, sketch_report = candidate_sketch, checked
                    except K.SketchError as exc:
                        quick_dropped = exc.problems[0] if exc.problems else "the quick sketch is invalid"
                    except FiguresChanged:
                        raise
                    except Exception as exc:  # noqa: BLE001 - the quick sketch could not run: dropped
                        quick_dropped = f"the quick sketch could not be run: {type(exc).__name__}"
                break
        elif sketch:
            # The author's status is the tier judgment (its receipt: figure_tier).
            reason = (" ".join(str(getattr(output, "why_not_spec", "") or "").split())[:400] if status == "sketch"
                      else " ".join(str(output.unsupported_reason or "").split())[:400] if status == "unsupported"
                      else "")
            verdict = (status if status in ("spec", "sketch", "unsupported") else "invalid", reason)
        if status == "unsupported":
            unsupported = (" ".join(str(output.unsupported_kind or "").split())[:80] or "something else",
                           " ".join(str(output.unsupported_reason or "").split())[:400])
            break
        if sketch and status == "sketch":
            compiled = None
            try:
                raw = output.sketch_json
                sketched = K.parse_sketch(_ungrounded_sketch(raw) if grounding.mode == "none" else raw)
            except K.SketchError as exc:
                problems, sketched = exc.problems, None
                continue
            from learnloop.figures import sketch_verify as SV

            gate.check("sketch")
            try:
                sketch_report = SV.verify_sketch(sketched, span_texts=context.span_texts)
            except Exception as exc:  # noqa: BLE001 - the engine itself failed: an honest failure, never shown
                problems, sketched = [f"the sketch could not be run: {type(exc).__name__}"], None
                sketch_report = None
                continue
            if sketch_report.outcome == V.FAILED:
                problems = list(sketch_report.problems) or [sketch_report.reason]
                sketched = None
                continue
            break
        sketched, sketch_report = None, None
        try:
            # Off, RW5b's panels are refused (the author was not told of them).
            compiled = S.parse_spec(_ungrounded(output.spec_json) if grounding.mode == "none" else output.spec_json,
                                    advanced=advanced)
        except S.SpecError as exc:
            problems, compiled = exc.problems, None
            continue
        report = V.verify_numerics(compiled)
        if report.outcome == V.FAILED:
            problems = [report.reason, *report.structural[1:], *report.invariant_problems[1:]]
            compiled = None
            continue
        break
    figure_id = FIGURE_PREFIX + new_ulid()
    asked = _request_row(request, grounding, figure_id=None, clock=clock)
    rich_spawn = None
    if brief is not None:
        rich_spawn = _RichSpawn(repository, spawn_rich, brief, request, context, grounding, digest, input_hash, asset_id,
                                verdict, author, prompt_version, generation, previous, request_id, quick_dropped)
        if compiled is None and sketched is None:
            return rich_spawn.only(vault, repository, asked, gate=gate, clock=clock)
    if sketched is not None or (sketch and verdict is not None and verdict[0] == "sketch"):
        return _store_sketch(vault, repository, request, context, author, sketched=sketched, report=sketch_report,
                             problems=problems, versions=versions, asset_id=asset_id, input_hash=input_hash,
                             prompt_version=prompt_version, figure_id=figure_id, asked=asked, clock=clock, gate=gate,
                             grounding=grounding, verdict=verdict, rich_spawn=rich_spawn)
    row: dict[str, Any] = {
        "id": figure_id, "extraction_id": request.extraction_id, "span_ids": request.span_ids,
        "region": request.region, "asset_id": asset_id,
        # Everything the author was sent, for every later held-out recheck (F1);
        # RW5d: retrieved passages (any source) by their keys.
        "input_span_ids": [] if context.keys else list(dict.fromkeys(
            [*context.span_texts, *([asset_id] if asset_id else [])])),
        "input_span_keys": list(dict.fromkeys(context.keys)),
        "request_id": asked["id"], "goal_text": request.goal_text, "grounding": grounding.mode, "tier": "grammar",
        "origin": request.origin,
        "supersedes_id": request.supersedes_id, "revision_note": request.revision_note,
        "spec_version": S.SPEC_VERSION, "model": author.model, "prompt_version": prompt_version,
        "input_hash": input_hash, "created_at": utc_now_iso(clock), "spec_json": None, "kind": None,
        "unsupported_kind": None,
    }
    if unsupported is not None:
        report.outcome, report.reason = V.UNSUPPORTED, unsupported[1] or unsupported[0]
        row["unsupported_kind"] = unsupported[0]
    elif compiled is None:
        report.outcome = V.FAILED
        report.reason = (problems[0] if problems else "the figure model gave no usable figure")[:300]
        report.structural = report.structural or list(problems)[:12]
    else:
        report.claims = V.check_claims(compiled, context.span_texts)
        assumptions = V.verified_assumptions(compiled, context.span_texts)
        row["spec_json"] = compiled.spec.canonical_json()
        row["kind"] = compiled.spec.kind
        report.outcome = V.ILLUSTRATIVE
        if compiled.spec.kind == "reconstructed":
            # RW5a checks no source match (§8.3 step 3 is RW5c's): a
            # reconstruction is an illustration, and says why.
            report.reason = RECONSTRUCTION_REASON
        report_dict = report.as_dict()
        report_dict["assumptions"] = assumptions
        row["verification_report"] = report_dict
    # Nothing is stored for a build whose configuration changed meanwhile:
    # its paid answers keep their checkpoints, so a later build recovers them
    # with no new call.
    gate.check("store")
    row["verification"] = report.outcome
    row.setdefault("verification_report", report.as_dict())
    if rich_spawn is not None and row["verification"] in store.SHOWN:
        # Codex review F8: the rich job's intent commits with the quick figure.
        row["verification_report"] = rich_spawn.with_intent(row["verification_report"], asked["id"], figure_id)
    try:
        with repository.atomic():
            connection = repository.connection()
            store.insert_request(connection, asked)
            store.insert_figure(connection, row)
            store.set_request_figure(connection, asked["id"], figure_id)
            append_judgment(connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id,
                            judge="verifier", input_hash=input_hash, verdict=report.outcome,
                            rationale=(report.reason or "")[:400], created_at=row["created_at"])
            if (sketch or v3) and verdict is not None:
                _append_tier(connection, figure_id, input_hash, verdict, author, prompt_version, row["created_at"])
    except sqlite3.IntegrityError:
        # Another process stored this input's figure first (the reuse index):
        # that one is the figure; this build's paid calls keep their receipts.
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            first = store.reusable(connection, input_hash, S.SPEC_VERSION)
        if first is None:
            raise
        return _reused(vault, repository, first, request=request, grounding=grounding, clock=clock, gate=gate)
    if rich_spawn is not None and row["verification"] in store.SHOWN:
        rich_spawn.after_quick(asked["id"], figure_id, row)
    stored = dict(row)
    stored["verification_report"] = row["verification_report"]
    return BuildOutcome(figure_view(vault, repository, stored, versions=versions), reused=False,
                        author_calls=author.made)


_LOG = logging.getLogger(__name__)
#: The key a quick figure's verification report keeps its rich job's intent
#: under (Codex review F8): the job's payload, committed with the figure.
RICH_INTENT_KEY = "rich_intent"
_RICH_SPAWN_GUARD = threading.Lock()


def ensure_rich_job(repository: Repository, spawn: SpawnRich, payload: dict[str, Any]) -> str | None:
    """Start a quick figure's rich job unless it already has one (in any
    state: a cancelled one stays cancelled) or a stored fuller version
    (Codex review F8). One process-wide lock makes the check and the enqueue
    one step, so the build that stored the figure and a reader recovering its
    intent never start two jobs. Returns the job's id (None: nothing to start)."""

    fast = payload.get("fast_figure_id")
    with _RICH_SPAWN_GUARD:
        if fast:
            existing = RICH.rich_job_id_for_quick(repository, str(fast))
            if existing is not None:
                return existing
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                if store.fuller_rows(connection, str(fast)):
                    return None
        return spawn(payload)


def resume_rich_intents(vault: Any, repository: Repository, extraction_id: str, spawn: SpawnRich | None) -> int:
    """Codex review F8: start the rich job of every shown quick figure of this
    source whose intent committed but whose job was never enqueued (the
    sidecar stopped between the two, or the enqueue failed). The recovered
    job belongs to no action (no grant: it waits for the plan when it is
    down). Returns how many were started."""

    if spawn is None or not enabled(vault) or not rich_enabled(vault):
        return 0
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return 0
        rows = store.figures_for_extraction(connection, extraction_id)
    started = 0
    for row in rows:
        intent = (row.get("verification_report") or {}).get(RICH_INTENT_KEY)
        if row.get("verification") not in store.SHOWN or not isinstance(intent, dict) or rich_row(row):
            continue
        if intent.get("build_mode") == "prefetch":
            # RW5d P5 (Codex review F3): a prebuild's intent stays a prebuild
            # when recovered: every P5 admission condition holds (the switch,
            # the power, foreground work, the plan route; the worker checks
            # them again), so with figures ahead of need off nothing starts.
            from learnloop.figures.power import background_hold

            if background_hold(vault) is not None:
                continue
            payload = dict(intent)
        else:
            payload = {**intent, "build_mode": "recovered"}
        if RICH.rich_job_id_for_quick(repository, str(row["id"])) is not None:
            continue
        try:
            if ensure_rich_job(repository, spawn, payload) is not None:
                started += 1
        except Exception:  # noqa: BLE001 - the line says it couldn't start; a later read tries again
            _LOG.warning("could not start the rich job of figure %s", row["id"], exc_info=True)
    return started


class _RichSpawn:
    """RW5d P2b (spec §8.6): starting the rich job of a rich status, after
    the quick figure is stored (:meth:`after_quick`) or with none
    (:meth:`only`). The job's payload carries what the rich author is sent
    (the author's context, the brief) and what its row needs (the input's
    spans and keys, its home, the tier verdict)."""

    def __init__(self, repository: Repository, spawn: SpawnRich | None, brief: RICH.RichBrief,
                 request: FigureRequest, context: SourceContext, grounding: Grounding, digest: str | None, input_hash: str,
                 asset_id: str | None, verdict: tuple[str, str] | None, author: R.FigureRoute | None,
                 prompt_version: str, generation: int, previous: Mapping[str, Any] | None, request_id: str,
                 quick_dropped: str | None, extra: Mapping[str, Any] | None = None):
        self.repository = repository
        self.spawn = spawn
        self.brief = brief
        self.request = request
        self.context = context
        self.grounding = grounding
        self.digest = digest
        self.input_hash = input_hash
        self.asset_id = asset_id
        self.verdict = verdict
        self.author = author
        self.prompt_version = prompt_version
        self.generation = generation
        self.previous = previous
        self.request_id = request_id
        self.quick_dropped = quick_dropped
        self.extra = dict(extra or {})

    def payload(self, request_row_id: str, fast_figure_id: str | None) -> dict[str, Any]:
        request = self.request
        # The author's context keeps its request_id (Codex review F7): the
        # input and its retry generation, so the rich prompt (and its paid
        # checkpoint) is the same across a crash and new after "try again".
        author_context = _author_context(request, self.context, self.digest, None, (), request_id=self.request_id,
                                         grounding=self.grounding)
        base = {
            "extraction_id": request.extraction_id, "span_ids": list(request.span_ids), "region": request.region,
            "asset_id": self.asset_id,
            "input_span_ids": [] if self.context.keys else list(dict.fromkeys(
                [*self.context.span_texts, *([self.asset_id] if self.asset_id else [])])),
            "input_span_keys": [list(key) for key in dict.fromkeys(self.context.keys)],
            "goal_text": request.goal_text, "grounding": self.grounding.mode, "origin": request.origin,
            "home": None if anchored(request) else dict(request.reading_at or {}),
        }
        if attempt_hosted(request):
            # RW5d P3 ruling R1: never reached (an attempt host's build has no
            # rich spawner); if it were, the worker refuses the job before any
            # request (``rich.attempt_hosted_job``).
            base["attempt_hosted"] = True
        payload = {"request_id": request_row_id, "fast_figure_id": fast_figure_id, "input_hash": self.input_hash,
                   "tier": self.brief.tier, "brief": self.brief.as_dict(), "author_context": author_context,
                   "span_texts": dict(self.context.span_texts), "base": base,
                   "verdict": list(self.verdict) if self.verdict else None,
                   "author_model": self.author.model if self.author is not None else None,
                   "prompt_version": self.prompt_version,
                   "build_mode": "prefetch" if request.origin == "prefetch" else "pressed",
                   "generation": self.generation,
                   "quick_dropped": self.quick_dropped, **self.extra}
        if "learner_state" in author_context:
            # Learner data-relax 2 (Codex review F2): what the saved state was
            # read from goes with the job (and the quick figure's intent), so
            # the job checks it again before it sends the state.
            payload["learner_state_inputs"] = request.learner_state_inputs
        return payload

    def with_intent(self, report: Mapping[str, Any], request_row_id: str, figure_id: str) -> dict[str, Any]:
        """The quick figure's report with its rich job's intent (Codex review F8)."""

        return {**dict(report), RICH_INTENT_KEY: self.payload(request_row_id, figure_id)}

    def after_quick(self, request_row_id: str, figure_id: str, row: Mapping[str, Any]) -> None:
        """Start the rich job of a stored quick figure. A failure is logged,
        never swallowed silently: the intent committed with the figure, so the
        next read of this source starts it (:func:`resume_rich_intents`)."""

        if self.spawn is None:
            return
        try:
            ensure_rich_job(self.repository, self.spawn, self.payload(request_row_id, figure_id))
        except Exception:  # noqa: BLE001 - recovered from the durable intent on the next read
            _LOG.warning("could not start the rich job of figure %s; it starts on the next read", figure_id,
                         exc_info=True)

    def only(self, vault: Any, repository: Repository, asked: dict[str, Any], *, gate: FiguresGate,
             clock: Clock | None) -> BuildOutcome:
        """No quick figure: the request is recorded with the author's tier
        receipt (Codex review F10: the judgment is the request's, whatever the
        job does next; the figure, once stored, is named by the request) and
        the rich job started; the pending line shows."""

        gate.check("store")
        with repository.atomic():
            connection = repository.connection()
            store.insert_request(connection, asked)
            if self.verdict is not None and self.author is not None:
                _append_tier(connection, str(asked["id"]), self.input_hash, self.verdict, self.author,
                             self.prompt_version, str(asked.get("created_at") or utc_now_iso(clock)),
                             left_kind="figure_request")
        job_id = self.spawn(self.payload(asked["id"], None)) if self.spawn is not None else None
        if job_id is None:
            raise FigureRefused("unavailable", "LearnLoop couldn't start building the animation just now.")
        job = {"id": job_id, "payload": self.payload(asked["id"], None), "status": "queued", "phase": "writing"}
        return BuildOutcome(None, reused=False, author_calls=self.author.made if self.author is not None else 0,
                            rich=_rich_line(self.request, job, RICH.job_state(job)))


def _rich_revision(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                   grounding: Grounding, *, previous: Mapping[str, Any], input_hash: str, digest: str | None,
                   asset_id: str | None, generation: int, request_id: str, spawn_rich: SpawnRich | None,
                   gate: FiguresGate, clock: Clock | None) -> BuildOutcome:
    """RW5d P2b (spec §8.5, Codex review F11): "not right?" on a Manim
    figure. The learner's note and the earlier program (its scene, declared
    functions and claims, and what it showed) go to ``figure_rich_author``
    on a rich job; the new version is checked, rendered and stored like any
    rich figure and supersedes the earlier one (kept: the version chain). A
    fuller version's revision stays that quick figure's fuller version."""

    if spawn_rich is None or "manim" not in (request.tiers_allowed or ()):
        raise FigureRefused("manim_unavailable", "A new version of an animation needs Manim figures on this "
                                                 "computer (figures.rich_tiers_enabled, the standing permission, "
                                                 "bubblewrap and Manim).")
    try:
        program = json.loads(previous.get("spec_json") or "{}")
    except (TypeError, ValueError):
        program = {}
    brief = RICH.RichBrief(
        tier="manim", brief=str(program.get("brief") or "")[:RICH.RICH_BRIEF_MAX],
        demonstrates=str(program.get("demonstrates") or ""),
        assumptions=[dict(item) for item in program.get("assumptions") or () if isinstance(item, dict)],
        source_claims=[dict(item) for item in program.get("source_claims") or () if isinstance(item, dict)])
    report = previous.get("verification_report") or {}
    revision = {
        "note": request.revision_note or "",
        "earlier_program": {
            "title": program.get("title") or "", "scene_class": program.get("scene_class") or "",
            "scene_code": str(program.get("scene_code") or "")[:12_000],
            "narration_md": program.get("narration_md") or "",
            "declared_json": json.dumps({key: program.get(key) or [] for key in ("functions", "claims",
                                                                                   "plotted_from")}),
            "checks_it_passed": [dict(check) for check in report.get("checks") or ()],
        },
    }
    asked = _request_row(request, grounding, figure_id=None, clock=clock)
    spawn = _RichSpawn(repository, spawn_rich, brief, request, context, grounding, digest, input_hash, asset_id, None, None,
                       RICH.RICH_PROMPT_VERSION, generation, previous, request_id, None,
                       extra={"supersedes_id": previous["id"], "fuller_of_id": previous.get("fuller_of_id"),
                              "revision": revision})
    return spawn.only(vault, repository, asked, gate=gate, clock=clock)


def _append_tier(connection: Any, figure_id: str, input_hash: str, verdict: tuple[str, str], author: R.FigureRoute,
                 prompt_version: str, created_at: str, *, left_kind: str = "interactive_figure") -> None:
    """The tier judgment's receipt (spec §8.4): the author's status, its reason
    (``why_not_spec`` or the unsupported reason), the model and prompt.
    ``left_kind`` ``figure_request`` (RW5d P2b, Codex review F10): a
    rich-only build's receipt, against its request."""

    append_judgment(connection, task=TIER_LEDGER_TASK, left_kind=left_kind, left_id=figure_id,
                    judge="llm", input_hash=input_hash, verdict=verdict[0], judge_model=author.model,
                    prompt_version=prompt_version, rationale=verdict[1][:400], created_at=created_at)


def _store_sketch(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                  author: R.FigureRoute, *, sketched: K.CompiledSketch | None, report: Any, problems: Sequence[str],
                  versions: int, asset_id: str | None, input_hash: str, prompt_version: str, figure_id: str,
                  asked: dict[str, Any], clock: Clock | None, gate: FiguresGate, grounding: Grounding,
                  verdict: tuple[str, str] | None, rich_spawn: "_RichSpawn | None" = None) -> BuildOutcome:
    """Store a sketch build (RW5d P2): shown (``illustrative``, its check lines)
    when verification passed, else ``failed`` with the reason (never shown)."""

    from learnloop.figures.sketch_engine import ENGINE_SHA256, ENGINE_VERSION

    row: dict[str, Any] = {
        "id": figure_id, "extraction_id": request.extraction_id, "span_ids": request.span_ids,
        "region": request.region, "asset_id": asset_id,
        "input_span_ids": [] if context.keys else list(dict.fromkeys(
            [*context.span_texts, *([asset_id] if asset_id else [])])),
        "input_span_keys": list(dict.fromkeys(context.keys)),
        "request_id": asked["id"], "goal_text": request.goal_text, "grounding": grounding.mode, "tier": "sketch",
        "origin": request.origin, "supersedes_id": request.supersedes_id, "revision_note": request.revision_note,
        "spec_version": K.SKETCH_VERSION, "model": author.model, "prompt_version": prompt_version,
        "input_hash": input_hash, "created_at": utc_now_iso(clock), "spec_json": None, "kind": None,
        "unsupported_kind": None, "program_version": K.SKETCH_VERSION, "engine_sha256": ENGINE_SHA256,
        "runtime_digest": f"{ENGINE_VERSION}:{ENGINE_SHA256}", "checks": [],
    }
    if sketched is not None and report is not None and report.outcome == V.ILLUSTRATIVE:
        verified = report.as_dict()
        verified["assumptions"] = _sketch_assumptions(sketched, context.span_texts)
        row.update({"spec_json": sketched.program.canonical_json(), "kind": "illustrative",
                    "verification": V.ILLUSTRATIVE, "verification_report": verified,
                    "checks": list(report.checks)})
    else:
        reason = (problems[0] if problems else (report.reason if report is not None else "")) or \
            "the figure model gave no usable sketch"
        failed = report.as_dict() if report is not None else {"tier": "sketch", "problems": list(problems)[:12]}
        failed.update({"outcome": V.FAILED, "reason": str(reason)[:300]})
        row.update({"verification": V.FAILED, "verification_report": failed})
    gate.check("store")
    if rich_spawn is not None and row["verification"] in store.SHOWN:
        # Codex review F8: the rich job's intent commits with the quick figure.
        row["verification_report"] = rich_spawn.with_intent(row["verification_report"], asked["id"], figure_id)
    try:
        with repository.atomic():
            connection = repository.connection()
            store.insert_request(connection, asked)
            store.insert_figure(connection, row)
            store.set_request_figure(connection, asked["id"], figure_id)
            append_judgment(connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id,
                            judge="verifier", input_hash=input_hash, verdict=row["verification"],
                            rationale=str(row["verification_report"].get("reason") or "")[:400],
                            created_at=row["created_at"])
            if verdict is not None:
                _append_tier(connection, figure_id, input_hash, verdict, author, prompt_version, row["created_at"])
    except sqlite3.IntegrityError:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            first = store.reusable(connection, input_hash, SPEC_VERSIONS)
        if first is None:
            raise
        return _reused(vault, repository, first, request=request, grounding=grounding, clock=clock, gate=gate)
    if rich_spawn is not None and row["verification"] in store.SHOWN:
        rich_spawn.after_quick(asked["id"], figure_id, row)
    return BuildOutcome(figure_view(vault, repository, row, versions=versions), reused=False,
                        author_calls=author.made)


def _sketch_assumptions(compiled: K.CompiledSketch, span_texts: Mapping[str, str]) -> list[dict[str, Any]]:
    """As :func:`.verify.verified_assumptions`: an unverified quote is dropped, the text stays (AI-written)."""

    shown = []
    for assumption in compiled.program.assumptions:
        quote = assumption.quote if (assumption.quote and assumption.span_id in span_texts
                                     and V.quote_in(assumption.quote, span_texts[assumption.span_id])) else None
        shown.append({"text": assumption.text, "span_id": assumption.span_id if quote else None, "quote": quote})
    return shown


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


def revision_request(repository: Repository, base: Mapping[str, Any], note: str) -> FigureRequest:
    """"Not right?" on a stored figure: the same input with the note. RW5d: a
    show-me figure keeps its goal (and who wrote it), its home and its
    grounding (its passages, or none: nothing is retrieved again)."""

    asked = _figure_request(repository, base) or {}
    keys = None
    fixed = None
    if (base.get("grounding") or "anchor") != "anchor":
        manifest = asked.get("grounding_manifest") or {}
        keys = [tuple(key) for key in manifest.get("kept") or ()]
        fixed = base.get("grounding")
    return FigureRequest(
        extraction_id=base["extraction_id"], span_ids=list(base.get("span_ids") or ()), region=base.get("region"),
        # RW5d P5: "not right?" on a prebuilt figure is the learner's request on its passage.
        origin="selection" if base["origin"] == "prefetch" else base["origin"], supersedes_id=base["id"],
        revision_note=note,
        goal_text=base.get("goal_text"), goal_author=asked.get("goal_author") if base.get("goal_text") else None,
        reading_at=asked.get("reading_at"), host_ref=dict(asked.get("host_ref") or {}),
        grounding_keys=keys, grounding_fixed=fixed)


def _chain_length(repository: Repository, figure_id: str) -> int:
    count = 0
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        current: str | None = figure_id
        seen: set[str] = set()
        while current and current not in seen and count < 100:
            seen.add(current)
            row = store.figure(connection, current)
            if row is None:
                break
            count += 1
            current = row.get("supersedes_id")
    return max(count, 1)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def _root(rows_by_id: Mapping[str, Mapping[str, Any]], row: Mapping[str, Any]) -> str:
    current = row
    seen = {current["id"]}
    while current.get("supersedes_id") and current["supersedes_id"] in rows_by_id and current["supersedes_id"] not in seen:
        current = rows_by_id[current["supersedes_id"]]
        seen.add(current["id"])
    return str(current["id"])


def _listed(vault: Any, repository: Repository,
            extraction_id: str) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]:
    """The rows :func:`list_figures` presents, with no presentation (RW5d P4a,
    Codex review F3): per version chain, the pick, the chain's length and its
    placements in this source. Read-only: nothing is verified or written."""

    if not enabled(vault):
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return []
        rows = store.figures_for_extraction(connection, extraction_id)
    # RW5d P2b: a rich figure that follows a quick one is that figure's fuller
    # version (one line, two versions), never a line of its own.
    rows = [row for row in rows if row["spec_version"] in ALL_SPEC_VERSIONS and not row.get("fuller_of_id")]
    if not show_me_enabled(vault):
        # RW5d off: a figure built from a goal (or with no passage) is absent.
        rows = [row for row in rows if not show_me_row(row)]
    if any(row.get("origin") == "prefetch" for row in rows):
        # RW5d P5: with figures ahead of need switched off, a prebuilt figure
        # nobody pressed for is absent (rev 1 exactly).
        rows = [row for row in rows if row.get("origin") != "prefetch" or _prebuilt_listed(vault, repository, row)]
    by_id = {row["id"]: row for row in rows}
    chains: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        chains.setdefault(_root(by_id, row), []).append(row)
    picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]] = []
    for chain in chains.values():
        shown = [row for row in chain if row["verification"] in store.SHOWN]
        # Codex review F5: with the panels off, the newest version that can
        # still be drawn, before one that would list as "can't draw this yet".
        drawable = [row for row in shown if drawable_now(vault, row)]
        pick = (drawable or shown or chain)[-1]
        if row_withheld(vault, repository, pick) is not None:
            continue
        # RW5d (Codex review F3): a figure with no passage is listed at every
        # paragraph of this source it was asked at (one view per placement),
        # each opening where that request was made.
        homes: list[dict[str, Any] | None] = [
            {"extraction_id": key[0], "span_id": key[1]} for key in figure_homes(repository, pick) or ()
            if key[0] == extraction_id] or [None]
        picks.append((pick, len(chain), homes))
    if any(pick.get("origin") == "prefetch" for pick, _length, _homes in picks):
        picks = _prebuilt_within_budget(vault, repository, extraction_id, picks)
    return picks


def _prebuilt_within_budget(vault: Any, repository: Repository, extraction_id: str,
                            picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]
                            ) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]:
    """RW5d P5 (spec §6.9; Codex review F11): a prebuilt figure nobody pressed for takes its
    place in the Reader's cue budget (``[cues] density``, per section; cues off: none), the
    earliest built first; once pressed it is the learner's like any figure (never cut)."""

    from learnloop.reader.reader_cues import cue_density, cues_enabled, density_budget
    from learnloop.reader.reader_guidance import extraction_sections

    budget = density_budget(cue_density(vault)) if cues_enabled(vault) else 0
    ir = repository.load_document_ir(extraction_id)
    section_of: dict[str, str] = {}
    if ir is not None:
        for section in extraction_sections(ir)[0]:
            for span in section["span_ids"]:
                section_of.setdefault(str(span), str(section["id"]))
    used: dict[str, int] = {}
    kept = []
    for entry in sorted(picks, key=lambda found: (str(found[0].get("created_at") or ""), str(found[0]["id"]))):
        row = entry[0]
        if row.get("origin") == "prefetch" and not _prebuilt_pressed(repository, row):
            spans = [str(span) for span in row.get("span_ids") or ()]
            section = next((section_of[span] for span in spans if span in section_of), "")
            if used.get(section, 0) >= budget:
                continue
            used[section] = used.get(section, 0) + 1
        kept.append(entry)
    order = {id(entry): index for index, entry in enumerate(picks)}
    return sorted(kept, key=lambda entry: order[id(entry)])


def _prebuilt_listed(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool:
    """RW5d P5: a prebuilt figure lists while figures ahead of need are on, or
    once a pressed request took it (then it is the learner's like any figure)."""

    from learnloop.figures.power import prefetch_switch

    if _prebuilt_pressed(repository, row):
        return True
    # Codex review F10: unpressed, only a completed (shown) prebuild lists,
    # never a failed or unsupported one (speculation is invisible until useful).
    return prefetch_switch(vault) and row.get("verification") in store.SHOWN


def _prebuilt_pressed(repository: Repository, row: Mapping[str, Any]) -> bool:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = connection.execute(
            "SELECT 1 FROM figure_requests WHERE figure_id = ? AND build_mode = 'pressed' LIMIT 1",
            (str(row["id"]),)).fetchone()
    return found is not None


def prefetch_pending(vault: Any, repository: Repository, extraction_id: str, *,
                     pass_running: bool = False) -> bool:
    """RW5d P5 (Codex review F11): whether a prebuild for this source is coming now: the Reader
    then reads its figures again, paced, so a completed prebuild appears without a reopen.
    False with figures ahead of need off (rev 1's payload).

    Codex re-review F18: only active, admissible work counts, so the Reader never polls for
    work no worker will do: nothing on battery (no background build runs there); a decision to
    build with no request yet only while a prefetch pass is running now (``pass_running``: the
    sidecar's drain thread, which builds the waiting decisions first; otherwise it waits for the
    next trigger, which a read does not fire); a prebuild's rich job only while it is queued or
    running (one waiting for the plan is asked again by the read, :func:`prefetch_plan_waits`,
    and is pending again once requeued)."""

    from learnloop.figures.power import power_state, prefetch_switch

    if not prefetch_switch(vault) or not power_state().on_mains:
        return False
    if pass_running:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = "
                                  "'figure_prefetch_decisions'").fetchone() is None:
                return False
            for raw in connection.execute(
                    "SELECT anchor_json FROM figure_prefetch_decisions WHERE outcome IS NULL AND request_id IS NULL "
                    "AND decision IN ('build', 'deferred_power', 'deferred_plan')"):
                try:
                    anchor = json.loads(raw[0] or "null")
                except (TypeError, ValueError):
                    continue
                if isinstance(anchor, dict) and str(anchor.get("extraction_id")) == str(extraction_id):
                    return True
    for job in RICH.rich_jobs(repository):
        payload = job.get("payload") or {}
        if payload.get("build_mode") == "prefetch" and RICH.job_state(job)["state"] == "pending" \
                and str((payload.get("base") or {}).get("extraction_id") or "") == str(extraction_id):
            return True
    return False


def prefetch_plan_waits(vault: Any, repository: Repository, extraction_id: str) -> list[str]:
    """RW5d P5 (Codex re-review F17): this source's speculative prebuild rich jobs waiting for
    the plan, newest per input, whose retry is admissible now: figures ahead of need on, this
    machine on mains, and the passage not held out. They list no line (Codex review F10), so the
    Reader's read asks the plan again for them here, paced as every plan wait is
    (``rich.due_for_plan_retry``); the requeued job's own gate checks the rest before any
    request. A newer job of the same input (a press, or a later prebuild) speaks for it."""

    from learnloop.figures.power import power_state, prefetch_switch
    from learnloop.figures.rich import _withheld

    if not rich_enabled(vault) or not prefetch_switch(vault) or not power_state().on_mains:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for job in RICH.rich_jobs(repository):
        payload = job.get("payload") or {}
        base = payload.get("base") or {}
        if str(base.get("extraction_id") or "") != str(extraction_id):
            continue
        key = str(payload.get("input_hash"))
        if key in seen:
            continue
        seen.add(key)
        if payload.get("build_mode") != "prefetch" or RICH.job_state(job)["state"] != RICH.WAITING_FOR_PLAN:
            continue
        if _withheld(vault, repository, base) is not None:
            continue
        found.append(str(job["id"]))
    return found


def build_prefetch_figure(vault: Any, repository: Repository, request: FigureRequest, *,
                          author_client: Any | None = None, clock: Clock | None = None,
                          live_vault: Callable[[], Any] | None = None, find: FindSources | None = None,
                          spawn_rich: SpawnRich | None = None) -> BuildOutcome:
    """RW5d P5: one background build for the prefetch service (spec §10b),
    under ``quiet()``: no offer, no grant (plan down: it waits). Origin
    ``prefetch``; everything else is :func:`build_figure`'s."""

    from learnloop.ai import plan_fallback

    request.origin = "prefetch"
    token = _PREFETCH_BUILD.set(True)
    try:
        with plan_fallback.quiet():
            return build_figure(vault, repository, request, author_client=author_client, clock=clock,
                                live_vault=live_vault, find=find, spawn_rich=spawn_rich)
    finally:
        _PREFETCH_BUILD.reset(token)


def list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]:
    """The figures of one source as the Reader shows them: per version chain,
    the newest shown version (else the newest failed or unsupported one), of
    the current spec version, and never one whose passage is held out now."""

    views = []
    for pick, versions, homes in _listed(vault, repository, extraction_id):
        try:
            views.extend(figure_view(vault, repository, pick, versions=versions, home=home) for home in homes)
        except (S.SpecError, K.SketchError):
            continue
    return sorted(views, key=lambda view: view["created_at"])


def section_figures(vault: Any, repository: Repository, extraction_id: str,
                    section_of: Callable[[str], str | None]) -> dict[str, list[dict[str, Any]]]:
    """RW5d P4a (spec §10.2): the kept figures of one reading by the section
    their anchor is in, for the correspondents read (figures follow the
    section). A read of what :func:`list_figures` lists (no copy, no
    ``source_objects`` row, Q8): only what the Reader would list on that
    reading now, held-out figures and figures switched off left out, and of
    those only the shown ones (verified or an illustration; never a failed or
    unsupported line). Read-only (Codex review F3): the rows are presented as
    the list presents them except that a sketch built under another engine is
    not re-verified here (opening it does that, and a figure that fails then
    is not shown). ``section_of`` maps an anchor span to its section (the
    caller's protected library: a withheld section maps to none). Each entry
    is the figure's id, its home (reading and anchor span), its label and kind;
    one entry per figure and section."""

    out: dict[str, list[dict[str, Any]]] = {}
    seen: set[tuple[str, str]] = set()
    picks = sorted(_listed(vault, repository, extraction_id), key=lambda found: str(found[0]["created_at"]))
    for pick, _versions, homes in picks:
        # Codex review F3: the list's own presentation, minus the sketch
        # re-verification (it runs the engine and appends to judgment_ledger):
        # that happens when the figure is opened, through its own book's
        # listing. A verdict this process already reached is honoured.
        row = rich_off_row(vault, sketch_off_row(vault, advanced_off_row(vault, shown_row(pick))))
        if sketch_row(row) and row.get("verification") in store.SHOWN:
            from learnloop.figures import sketch_verify as SV
            from learnloop.figures.sketch_engine import ENGINE_SHA256

            with _RECHECKED_GUARD:
                cached = _RECHECKED.get((str(row["id"]), ENGINE_SHA256, SV.VERIFIER_REPORT_VERSION))
            if cached is not None and cached["outcome"] != V.ILLUSTRATIVE:
                continue
        row = worded_row(row)
        if row.get("verification") not in store.SHOWN:
            continue
        asked = _figure_request(repository, row)
        for home in homes:
            anchor = _anchor_span(row, asked, home)
            if not anchor:
                continue
            section_id = section_of(str(anchor))
            if section_id is None or (section_id, str(row["id"])) in seen:
                continue
            seen.add((section_id, str(row["id"])))
            out.setdefault(section_id, []).append({
                "figure_id": row["id"], "extraction_id": row["extraction_id"], "anchor_span_id": anchor,
                "label": _label(row), "kind": row.get("kind"), "verification": row["verification"],
                "created_at": row["created_at"],
            })
    return out


def rich_pending(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]:
    """RW5d P2b (spec §6.8): the rich builds with no quick figure for this
    source that have not ended (pending, or waiting for the plan), each as
    the pending line under its passage; empty while the rich tiers are off.
    A build whose passage is held out now is left out.

    Codex review F9: a build that ended with no row (interrupted when
    LearnLoop stopped, or stopped with code's reason) stays as a ``failed``
    line with that reason and its job (``figure.rich_retry`` requeues it),
    until a later build of the same input replaces it; a cancelled one is
    gone (the learner chose).

    Codex re-review F14: a correction of an animation ("not right?") whose
    job stored a failure lists no line of its own (the earlier animation
    stays the chain's shown version), so it stays as a ``failed`` line with
    the stored reason (``figure.rich_retry`` asks again,
    :func:`rich_revision_retry`), until a later correction of the same
    figure replaces it. Reader follow-ups Nov 1b (P2b ruling R1): such a
    failure is found from the durable rows (the stored failure, its request,
    and that request's job over the whole queue), not only among the jobs
    the queue's recent window returns."""

    if not enabled(vault) or not rich_enabled(vault):
        return []
    lines = []
    seen: set[str] = set()
    corrected: set[str] = set()
    stored: list[dict[str, Any]] | None = None

    def stored_rows() -> list[dict[str, Any]]:
        nonlocal stored
        if stored is None:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                stored = store.figures_for_extraction(connection, extraction_id) \
                    if store.has_tables(connection) else []
        return stored

    def failed_corrections() -> list[dict[str, Any]]:
        # P2b ruling R1: the stored failures of animation corrections, newest
        # first, each with its job (by its request, over the whole queue).
        # Codex review F4 (Nov 1b): only while that job is still the newest
        # correction of the figure over the whole queue; a newer one (even a
        # cancelled one, which stores no row) speaks for it, as in the window.
        found = []
        for row in reversed(stored_rows()):
            if row.get("verification") != "failed" or row.get("spec_version") not in RICH_SPEC_VERSIONS \
                    or not row.get("supersedes_id") or not row.get("request_id"):
                continue
            job = RICH.rich_job_for_request(repository, str(row["request_id"]))
            if job is None or (job.get("payload") or {}).get("supersedes_id") != row["supersedes_id"]:
                continue
            newest = RICH.rich_job_for_figure(repository, str(row["supersedes_id"]))
            if newest is not None and str(newest.get("id")) == str(job.get("id")):
                found.append(job)
        return found

    jobs = RICH.rich_jobs(repository)
    windowed = {str(job.get("id")) for job in jobs}
    for job in [*jobs, *(job for job in failed_corrections() if str(job.get("id")) not in windowed)]:
        payload = job.get("payload") or {}
        base = payload.get("base") or {}
        if payload.get("fast_figure_id") or str(base.get("extraction_id") or "") != str(extraction_id):
            continue
        if payload.get("build_mode") == "prefetch":
            # RW5d P5 (Codex review F10): a speculative rich-only prebuild is
            # invisible until a figure exists (no building, waiting or failed
            # line, switch on or off); a press of the same input is its own
            # request with its own line.
            continue
        if str(payload.get("input_hash")) in seen:
            continue
        seen.add(str(payload.get("input_hash")))
        supersedes = payload.get("supersedes_id")
        if supersedes:
            # Jobs come newest first: a newer correction of the same figure
            # speaks for it (its own line, or its stored version).
            if str(supersedes) in corrected:
                continue
            corrected.add(str(supersedes))
        state = RICH.job_state(job)
        failed_correction = _failed_correction(payload, stored_rows()) if supersedes and \
            state["state"] in ("done", "failed") else None
        if failed_correction is not None:
            reason = str((failed_correction.get("verification_report") or {}).get("reason") or "")
            state = {"state": "failed", "reason": reason[:300] or "the job failed", "rich_job_id": job["id"]}
        elif state["state"] not in ("pending", "waiting_for_plan", "failed"):
            continue
        elif state["state"] == "failed" and payload.get("input_hash") in {row["input_hash"] for row in stored_rows()}:
            # A stored row (the figure, or its stored failure) lists itself.
            continue
        if base.get("goal_text") is not None and not show_me_enabled(vault):
            continue
        from learnloop.figures.rich import _withheld

        if _withheld(vault, repository, base) is not None:
            continue
        lines.append(_rich_line(FigureRequest(extraction_id=extraction_id, span_ids=[]), job, state))
    return lines


def _failed_correction(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Codex re-review F14: the failure a correction job stored (its request's
    row, ``failed``) while it is still the newest version of the figure it
    corrects: nothing supersedes it and no later correction of that figure
    was stored. None otherwise (it succeeded, stored nothing, or was replaced)."""

    supersedes = payload.get("supersedes_id")
    request_id = payload.get("request_id")
    if not supersedes or not request_id:
        return None
    mine = [row for row in rows if row.get("request_id") == request_id and row.get("supersedes_id") == supersedes]
    if not mine or mine[-1].get("verification") != "failed":
        return None
    failed = mine[-1]
    later = [row for row in rows if row.get("supersedes_id") in (supersedes, failed["id"])]
    if later and later[-1]["id"] != failed["id"]:
        return None
    return failed


def rich_revision_retry(vault: Any, repository: Repository, job_id: str) -> FigureRequest | None:
    """Codex re-review F14: "try again" on a correction of an animation whose
    job stored a failure (the line :func:`rich_pending` lists): the same
    correction (the figure it corrects, the learner's note), built afresh.
    Its input is the same, and the stored failure starts the next generation,
    so the rich author is asked anew (never the failed answer's checkpoint).
    None for any other job (:func:`retry_rich_job` decides those)."""

    if not rich_enabled(vault):
        return None
    job = repository.get_ingest_job(job_id)
    if job is None or job.get("job_type") != RICH.RICH_JOB_TYPE:
        return None
    payload = job.get("payload") or {}
    supersedes = payload.get("supersedes_id")
    extraction_id = str((payload.get("base") or {}).get("extraction_id") or "")
    if not supersedes or not extraction_id or RICH.job_state(job)["state"] not in ("done", "failed"):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return None
        if _failed_correction(payload, store.figures_for_extraction(connection, extraction_id)) is None:
            return None
        previous = store.figure(connection, str(supersedes))
    if previous is None:
        return None
    return revision_request(repository, previous, str((payload.get("revision") or {}).get("note") or ""))


def shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], Any]:
    """A figure that may be shown now: shown verification, a current spec
    version, its passage not held out. Returns the row and its compiled
    spec (a :class:`~learnloop.figures.spec.CompiledFigure`, or for a sketch
    a :class:`~learnloop.figures.sketch.CompiledSketch`)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        raise FigureRefused("not_found", "That figure is no longer kept.")
    if row["verification"] not in store.SHOWN or row["spec_version"] not in SPEC_VERSIONS or not row.get("spec_json"):
        # A rich figure (RW5d P2b) has no predictions and is shown through its view only.
        raise FigureRefused("not_found", "That figure is not shown.")
    if advanced_off_row(vault, row) is not row:
        raise FigureRefused("not_found", "That figure uses a panel kind that is switched off.")
    if sketch_off_row(vault, row) is not row:
        raise FigureRefused("sketch_disabled", "That figure is a simulation, and the sketch tier is switched off "
                                               "(figures.sketch_enabled).")
    if sketch_row(row):
        # Codex review F9: the rechecked row is the one delivered and
        # predicted on (its dropped predictions are this engine's).
        row = dict(sketch_rechecked(row, repository))
        if row.get("verification") not in store.SHOWN:
            raise FigureRefused("not_found", "That simulation couldn't run under this version.")
    if show_me_row(row) and not show_me_enabled(vault):
        raise FigureRefused("show_me_disabled", "\"Show me\" in your own words is switched off "
                                                "(figures.show_me_enabled).")
    if row_withheld(vault, repository, row) is not None:
        raise FigureRefused("exam_material", "That figure's passage is held out now.")
    if sketch_row(row):
        return row, K.parse_sketch(row["spec_json"])
    return row, S.parse_spec(row["spec_json"])


# ---------------------------------------------------------------------------
# Predictions (formative)
# ---------------------------------------------------------------------------

def record_prediction(vault: Any, repository: Repository, figure_id: str, index: int, answer: str, *,
                      clock: Clock | None = None, on_queued: Callable[[str], None] | None = None,
                      assist_id: str | None = None) -> dict[str, Any]:
    """The learner's prediction, its observed before/after readout and
    whether it matched (code decides). Idempotent per (figure, prediction).
    ``on_queued`` hears the learner-text job a missed one queued (the
    sidecar wakes its gap worker with it; Codex review F6). ``assist_id``
    (RW5d P3, Codex review F7): the open attempt's figure row it is made
    under (the caller derives it), kept on the row for the diagnoser."""

    if not predictions_enabled(vault):
        raise FigureRefused("predictions_disabled", "Figure predictions are switched off (figures.predictions_enabled).")
    row, compiled = shown_figure(vault, repository, figure_id)
    # RW5d P3 (Codex review F9): an attempt host's illustration with nothing
    # from the learner's books keeps its predictions with no home (NULL),
    # never an invented one.
    home = prediction_home(row)
    dropped = set((row.get("verification_report") or {}).get("dropped_predictions") or ())
    count = len(compiled.program.predictions) if isinstance(compiled, K.CompiledSketch) else len(compiled.predictions)
    if not 0 <= int(index) < count or int(index) in dropped:
        raise FigureRefused("validation_error", "That figure has no such prediction.")
    outcome = _sketch_outcome(compiled, int(index)) if isinstance(compiled, K.CompiledSketch) \
        else S.prediction_outcome(compiled, int(index))
    if outcome.get("answer") is None:
        raise FigureRefused("validation_error", "That prediction can't be decided.")
    answer = " ".join(str(answer or "").split())[:ANSWER_CHARS]
    if answer not in outcome["choices"]:
        raise FigureRefused("validation_error", "Pick one of the prediction's answers.")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        existing = store.prediction_for(connection, figure_id, int(index))
    if existing is not None:
        return _prediction_view(existing) or {}
    prediction = {
        "id": PREDICTION_PREFIX + new_ulid(), "figure_id": figure_id, "extraction_id": home,
        "prediction_index": int(index), "learner_answer": answer,
        "observed": {"kind": outcome["kind"], "before": outcome["before"], "after": outcome["after"],
                     "answer": outcome["answer"], "change": outcome["change"]},
        "matched": answer == outcome["answer"], "explanation_text": None, "created_at": utc_now_iso(clock),
        "assist_id": assist_id, "explained_at": None,
    }
    with repository.atomic():
        store.insert_prediction(repository.connection(), prediction)
    if not prediction["matched"]:
        _queued(_queue_formative(vault, repository, prediction["id"], clock=clock), on_queued)
    return _prediction_view({**prediction, "matched": prediction["matched"]}) or {}


def _sketch_outcome(compiled: K.CompiledSketch, index: int) -> dict[str, Any]:
    """A sketch's prediction, decided by code in the sealed engine (spec §9.3)."""

    from learnloop.figures import sketch_verify as SV
    from learnloop.figures.sketch_engine import SketchEngine, SketchRunError

    try:
        with SketchEngine() as engine:
            engine.load(compiled.program.code)
            return SV.prediction_outcome(compiled, engine, index)
    except SketchRunError as exc:
        raise FigureRefused("validation_error", f"That prediction can't be decided ({exc.kind}).") from exc


def record_explanation(vault: Any, repository: Repository, prediction_id: str, text: str, *,
                       clock: Clock | None = None, on_queued: Callable[[str], None] | None = None) -> dict[str, Any]:
    """ "What changed, and why?" (optional, once). On a missed prediction it
    is read with the answer: by the prediction's own reading while that is
    still queued, else as a later text of its own, the earlier reading kept
    (Codex review F5)."""

    if not predictions_enabled(vault):
        raise FigureRefused("predictions_disabled", "Figure predictions are switched off (figures.predictions_enabled).")
    text = " ".join(str(text or "").split())[:EXPLANATION_CHARS]
    if not text:
        raise FigureRefused("validation_error", "Write a line, or leave it empty.")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = store.prediction(connection, prediction_id) if store.has_tables(connection) else None
    if found is None:
        raise FigureRefused("not_found", "That prediction is no longer kept.")
    shown_figure(vault, repository, str(found["figure_id"]))
    with repository.atomic():
        set_now = store.set_explanation(repository.connection(), prediction_id, text, at=utc_now_iso(clock))
    if set_now and not found["matched"]:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_figure_explanation

        _queued(enqueue_figure_explanation(vault, repository, prediction_id=prediction_id, clock=clock), on_queued)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return _prediction_view(store.prediction(connection, prediction_id)) or {}


def _queue_formative(vault: Any, repository: Repository, prediction_id: str, *, clock: Clock | None) -> str | None:
    from learnloop.diagnosis.text_gaps.jobs import enqueue_figure_prediction

    return enqueue_figure_prediction(vault, repository, prediction_id=prediction_id, clock=clock)


def _queued(job_id: str | None, on_queued: Callable[[str], None] | None) -> None:
    if job_id and on_queued is not None:
        on_queued(job_id)


__all__ = [
    "BuildOutcome",
    "FigureRefused",
    "FigureRequest",
    "GROUNDING_PASSAGES",
    "Grounding",
    "LABELS",
    "LESSON_TIERS",
    "NOT_FROM_BOOKS_LABEL",
    "SERVICE_ORIGINS",
    "anchored",
    "build_figure",
    "check_request",
    "enabled",
    "figure_view",
    "figure_homes",
    "figure_withheld",
    "ground",
    "keys_withheld",
    "lesson_hosted",
    "revision_request",
    "row_withheld",
    "show_me_enabled",
    "show_me_input",
    "fuller_state",
    "ensure_rich_job",
    "resume_rich_intents",
    "retry_rich_job",
    "rich_enabled",
    "rich_off_row",
    "rich_pending",
    "rich_row",
    "sketch_enabled",
    "sketch_off_row",
    "sketch_rechecked",
    "sketch_row",
    "list_figures",
    "predictions_enabled",
    "record_explanation",
    "record_prediction",
    "region_enabled",
    "revisions_enabled",
    "section_figures",
    "shown_figure",
    "teacher_visuals_switch",
    "withheld_message",
]
