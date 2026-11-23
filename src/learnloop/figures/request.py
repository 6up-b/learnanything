"""A figure request: what may be asked, by whom and from where, and the key its build is admitted under.

:class:`FigureRequest` is what a caller asks for (a passage or a region, a goal, a revision of a stored figure, the
host it is asked on); :class:`FigureRefused` is every refusal with its code. :func:`check_request` is the request
path's one check, run before any job or call and again by the build: the origin and its switch (selection, offers,
show me, an attempt host, a lesson, the in-process pre-build), the goal and note sizes, then held-out material over
the request's home and fixed grounding (:mod:`.protection`), then a revision's base figure (on this source, not held
out, its tier and panel kinds switched on). :func:`key_for` names what the build depends on for each kind of request
(:func:`build_key` and the switches that admit it), compared before every model request
(:class:`~learnloop.figure_admission.FiguresGate`); it is never in the reuse key.

The predicates the build and its callers share live here too: :func:`anchored` (a passage), :func:`show_me_input` (a
goal or no passage), :func:`attempt_hosted`, :func:`lesson_hosted`, :func:`offered`, :func:`prediction_home`. This
module reads stored rows only through :mod:`.view`'s row predicates and :mod:`.protection`; it imports nothing of the
grounding, the listing or the build.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import closing
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.figure_admission import (
    advanced_panels_enabled,
    author_learner_state_enabled,
    checked_labels_enabled,
    figures_enabled,
    help_kind_enabled,
    offers_enabled,
    region_enabled,
    revisions_enabled,
    rich_tiers_enabled,
    show_me_enabled,
    sketch_enabled,
    teacher_visuals_enabled,
)
from learnloop.figures import rich as RICH
from learnloop.figures import routes as R
from learnloop.figures.protection import ATTEMPT_HOST_REFS, keys_withheld, row_withheld, show_me_row, withheld_message
from learnloop.figures.sketch import sketch_ready
from learnloop.figures.view import _advanced_kinds, rich_row, sketch_row


#: The origins a request may name. RW5d P1 adds ``show_me`` (the Reader's
#: intent box with words, or its Ask rail); RW5d P3 adds ``ask`` (CA2's panel
#: on practice, feedback and the workbench: an attempt host, P3); RW5d P4b adds
#: ``teacher`` (a lesson's visual: made only by the lesson service, under a
#: ``teacher`` caller with the lesson as its host, never from an RPC);
#: ``prefetch`` (P5, reserved by migration 224) is made only in process by the
#: prefetch service (:func:`build_prefetch_figure`) and refused from every request.
ORIGINS = ("selection", "library", "tutor", "show_me", "ask", "teacher")
RESERVED_ORIGINS = ("prefetch",)
#: The origins no RPC may name (the lesson service's and the prefetch service's own).
SERVICE_ORIGINS = ("teacher", "prefetch")
#: RW5d P4b: a lesson host's tiers (spec §10.4, the teacher spec's "grammar or
#: sketch tier"; P3 ruling R1's precedent): the turn waits on its figure, so no
#: rich (minutes-long, queued) tier is on the author's menu in a lesson.
LESSON_TIERS = ("grammar", "sketch")
#: RW5d P3 ruling R1: an attempt host's tiers (practice, feedback, the workbench): rich (Manim) figures are made
#: and opened in the Reader only. The doors that keep it each read this: no spawner for the build (the sidecar's
#: press), no fuller version in the view and no rich figure opened or recorded there (the sidecar's attempt
#: host). The rich worker's refusal of an attempt-hosted job (``rich.attempt_hosted_job``) is the same rule; it
#: can't import this module, which imports it.
ATTEMPT_HOST_TIERS = ("grammar", "sketch")
#: RW5b: the origins an offer builds with (``figures.offers_enabled``).
OFFER_ORIGINS = ("library", "tutor")
#: RW5d: who wrote a goal (set on the server, never taken from a client;
#: ``teacher`` only by the lesson service, RW5d P4b).
GOAL_AUTHORS = ("learner", "tutor", "teacher")
GOAL_CHARS = 600
GROUNDINGS = ("anchor", "retrieved", "none")
NOTE_CHARS = 600


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
    #: RW5c (Codex review F3): *rebuild* of a figure whose stated claim differs:
    #: the check row it answers (in the reuse key only when set, so every other
    #: hash is unchanged) and that row's difference, in code's words, as the
    #: first attempt's problems. Set only by :func:`rebuild_request`.
    source_check_id: str | None = None
    initial_problems: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# What kind of request it is
# ---------------------------------------------------------------------------

def attempt_hosted(request: "FigureRequest") -> bool:
    """RW5d P3: a request made on an attempt host (practice, feedback or the
    workbench: its verified host references name an item or attempt)."""

    return any((request.host_ref or {}).get(name) for name in ATTEMPT_HOST_REFS)


def lesson_hosted(request: "FigureRequest") -> bool:
    """RW5d P4b: a lesson's visual (origin ``teacher``; its host is the lesson,
    so it has no reading position and no home: it shows in the lesson only)."""

    return request.origin == "teacher"


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


# ---------------------------------------------------------------------------
# What its build is admitted under (never in the reuse key)
# ---------------------------------------------------------------------------

def build_key(vault: Any) -> tuple[Any, ...]:
    """What a build depends on, compared before every request it makes
    (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch,
    the author route as configured, the day's cap and the price, and (RW5b)
    whether the advanced panels are on (the author's prompt depends on it);
    likewise (learner data-relax 2, Codex review F2) whether the author is
    sent the learner's state (``figures.author_learner_state``); RW5c (F5):
    whether step 3 runs, so a switch change between the sandbox's result and the
    second attempt stops it. Admission only: never in the reuse key."""

    from learnloop.practice_index.paid import plan_route

    section = getattr(vault.config, "figures", None)
    return (str(vault.root), figures_enabled(vault), plan_route(vault, R.AUTHOR_TASK, None),
            getattr(section, "max_daily_cost_usd", None), getattr(section, "price_per_million", None),
            advanced_panels_enabled(vault), sketch_enabled(vault), RICH.rich_tiers_switch(vault),
            RICH.manim_tier_ready(vault), author_learner_state_enabled(vault), checked_labels_enabled(vault))


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
        return lambda vault: (*base(vault), teacher_visuals_enabled(vault))
    if attempt_hosted(request):
        # RW5d P3 (Codex review F5): a build on an attempt host is admitted
        # only while figures in attempts stay on (switched off since: it asks
        # nothing more, and its delivery shows nothing).
        base = _key_for(request)
        return lambda vault: (*base(vault), help_kind_enabled(vault))
    return _key_for(request)


def _key_for(request: "FigureRequest"):
    if show_me_input(request):
        if offered(request):
            return lambda vault: (*offer_build_key(vault), show_me_enabled(vault))
        return show_me_build_key
    return offer_build_key if offered(request) else build_key


# ---------------------------------------------------------------------------
# The request path's check
# ---------------------------------------------------------------------------

#: RW5d P5: set only inside :func:`build_prefetch_figure` (the in-process
#: prefetch service); origin ``prefetch`` is refused everywhere else.
_PREFETCH_BUILD: ContextVar[bool] = ContextVar("learnloop_figures_prefetch_build", default=False)
#: Who may write a prefetch build's goal: the prefetch judge, or a lesson plan's teacher.
PREFETCH_GOAL_AUTHORS = ("prefetch", "teacher")


def _validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest:
    if not figures_enabled(vault):
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
        if not teacher_visuals_enabled(vault):
            raise FigureRefused("teacher_visuals_disabled", "The teacher's figures are switched off "
                                                            "(teacher.visuals).")
    if offered(request) and not offers_enabled(vault):
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
                         different_kind=bool(request.different_kind and request.supersedes_id is not None),
                         source_check_id=request.source_check_id if request.supersedes_id is not None else None,
                         initial_problems=list(request.initial_problems) if request.supersedes_id is not None else [])


def _validated_prefetch(vault: Any, request: FigureRequest) -> FigureRequest:
    """RW5d P5: a prefetch build's request, as the prefetch service made it:
    an anchor (a passage of a book), an optional goal by the prefetch judge
    or a lesson plan's teacher, never an attempt host, a region or a revision."""

    from learnloop.figures.power import prefetch_switch

    if not prefetch_switch(vault):
        raise FigureRefused("prefetch_disabled", "Figures ahead of need are switched off (figures.prefetch_enabled).")
    spans = [str(span) for span in dict.fromkeys(request.span_ids) if span][:40]
    goal = " ".join(str(request.goal_text or "").split())[:GOAL_CHARS] or None
    # Landing ruling R5: a lesson plan's planned visual is prebuilt as the very request the
    # lesson's step will make (teacher.visuals.figure_request): no passage, the delivered
    # passages as fixed grounding keys and the teacher's goal, so the step reuses it.
    planned = (not spans and not request.extraction_id and bool(request.grounding_keys)
               and goal is not None and request.goal_author == "teacher")
    if not planned and (not request.extraction_id or not spans):
        raise FigureRefused("validation_error", "A figure built ahead of need needs its passage.")
    if attempt_hosted(request) or request.region is not None or request.supersedes_id is not None:
        raise FigureRefused("validation_error", "A figure built ahead of need is a passage's, never an attempt's.")
    if goal is not None:
        if not show_me_enabled(vault):
            raise FigureRefused("show_me_disabled", "\"Show me\" in your own words is switched off "
                                                    "(figures.show_me_enabled).")
        if request.goal_author not in PREFETCH_GOAL_AUTHORS:
            raise FigureRefused("validation_error", "That figure goal can't come from here.")
    if planned:
        keys = [(str(key[0]), str(key[1])) for key in request.grounding_keys or () if len(key) == 2 and key[0] and key[1]]
        return FigureRequest(extraction_id=None, span_ids=[], origin="prefetch", goal_text=goal, goal_author="teacher",
                             caller=request.caller, grounding_keys=keys,
                             prefetch_decision_id=request.prefetch_decision_id)
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
        if rich_row(base) and not rich_tiers_enabled(vault):
            # RW5d P2b: an animation is revised only with the rich tiers on
            # (it lists as "can't show this kind here" while they are off).
            raise FigureRefused("rich_disabled", "That figure is an animation, and rich figures are switched off "
                                                 "(figures.rich_tiers_enabled).")
        if rich_row(base) and not request.different_kind and (
                base.get("verification") not in store.SHOWN or not base.get("spec_json")):
            raise FigureRefused("not_found", "That animation is not shown, so there is no version to improve: "
                                             "ask again.")
        if sketch_row(base) and not sketch_ready(vault):
            # RW5d P2: a sketch is revised only by the sketch tier (RW5b's
            # contract can't write one back).
            raise FigureRefused("sketch_disabled", "That figure is a simulation, and the sketch tier is switched "
                                                   "off (figures.sketch_enabled).")
        if not advanced_panels_enabled(vault) and _advanced_kinds(base):
            # Codex review F4: a figure that uses a panel kind switched off
            # (listed as "can't draw this yet", or a failed attempt at one) is
            # not revised: its spec would be sent under RW5a's prompt, which
            # can only re-emit what is refused, two paid calls for nothing.
            raise FigureRefused("advanced_disabled", "That figure uses a panel kind that is switched off "
                                                     "(figures.advanced_panels_enabled).")
    return request


__all__ = [
    "ATTEMPT_HOST_TIERS",
    "FigureRefused",
    "FigureRequest",
    "GOAL_AUTHORS",
    "GOAL_CHARS",
    "GROUNDINGS",
    "LESSON_TIERS",
    "NOTE_CHARS",
    "OFFER_ORIGINS",
    "ORIGINS",
    "PREFETCH_GOAL_AUTHORS",
    "RESERVED_ORIGINS",
    "SERVICE_ORIGINS",
    "anchored",
    "attempt_hosted",
    "build_key",
    "check_request",
    "key_for",
    "lesson_hosted",
    "offer_build_key",
    "offered",
    "prediction_home",
    "show_me_build_key",
    "show_me_input",
]
