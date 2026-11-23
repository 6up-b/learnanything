"""Building a figure: reuse it, or ask the author and store what passes (spec_reader_workbench_v1 §8; UX §4.7).

:func:`build_figure` runs one request. It repeats :func:`~.request.check_request`, and every model request it makes
passes one :class:`~learnloop.figure_admission.FiguresGate` over :func:`~.request.key_for` (the switches, the route,
the day's cap and the price as configured now; a pre-build also holds on power and its switch). The reuse key
(:func:`request_hash`) names the input: :mod:`.grounding`'s context, the goal, the crop, the prompt version, the tier
menu and a learner state's hash. A figure stored under it, or under the same input's key for another setting, that
can be drawn now is reused with no call, and one input builds once at a time in this process. Otherwise the author is
asked for a spec, a sketch or a rich tier (at most two attempts, the second told the first's problems), the answer is
verified by code (:mod:`.verify`, the sealed sketch engine, the source check), and one row is stored with its
``judgment_ledger`` verdicts; every request, built or reused, appends a ``figure_requests`` row. A rich answer stores
its quick figure and starts the durable rich job, its intent kept with the quick figure so that
:func:`resume_rich_intents` starts a job a crash lost. Revisions (:func:`revision_request`, :func:`rebuild_request`,
:func:`rich_revision_retry`, :func:`retry_rich_job`) and the pre-build pass (:func:`build_prefetch_figure`) take the
same path. How a stored figure is presented, listed and answered afterwards is :mod:`.view`'s, :mod:`.listing`'s and
:mod:`.predictions`'; this module imports them, and none of them imports it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from typing import Any

from learnloop.ai.execution import content_key, gate_model_requests
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.figure_admission import FiguresChanged, FiguresGate, figures_enabled, rich_tiers_enabled
from learnloop.figures import author_answer as AA
from learnloop.figures import records as FR
from learnloop.figures import rich as RICH
from learnloop.figures import routes as R
from learnloop.figures import sketch as K
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.figures.grounding import (
    FindSources,
    Grounding,
    SourceContext,
    crop_image,
    ground,
    passages_context,
    source_context,
)
from learnloop.figures.listing import _failed_correction, _rich_line
from learnloop.figures.protection import (
    INHERITED_LEARNER_INPUTS_KEY,
    LEARNER_STATE_INPUTS_KEY,
    RICH_INTENT_KEY,
    _learner_inputs_unrecorded,
    inherited_learner_inputs,
    learner_state_withheld,
)
from learnloop.figures.request import (
    _PREFETCH_BUILD,
    LESSON_TIERS,
    FigureRefused,
    FigureRequest,
    anchored,
    attempt_hosted,
    check_request,
    key_for,
    lesson_hosted,
    show_me_input,
)
from learnloop.figures.sketch import sketch_ready
from learnloop.figures.spec import ALL_SPEC_VERSIONS, RICH_SPEC_VERSIONS, SPEC_VERSIONS
from learnloop.figures.view import (
    LEDGER_TASK,
    RECONSTRUCTION_REASON,
    _figure_request,
    drawable_now,
    figure_view,
    rich_row,
    sketch_row,
    source_rejected,
)
from learnloop.ids import new_ulid

SHOW_ME_VERSION = "show-me-v1"
REQUEST_PREFIX = "frq_"
FIGURE_PREFIX = "fig_"

TIER_LEDGER_TASK = "figure_tier"


# ---------------------------------------------------------------------------
# The reuse key's learner-inputs record (the rule itself is .protection's)
# ---------------------------------------------------------------------------

def _unrecorded_occupant(vault: Any, connection: Any, input_hash: str) -> bool:
    """Codex re-review F5: whether this input's reusable figure (its quick
    figure, or a rich figure built with no quick one) is a marked row that
    keeps no record of what its author's learner state was read from."""

    found = store.reusable(connection, input_hash, SPEC_VERSIONS)
    rich_only = store.reusable(connection, input_hash, RICH_SPEC_VERSIONS) if rich_tiers_enabled(vault) else None
    if rich_only is not None and rich_only.get("fuller_of_id"):
        rich_only = None  # a fuller version is checked through its quick figure's intent
    return any(row is not None and _learner_inputs_unrecorded(row) for row in (found, rich_only))


def _recorded_input_key(input_hash: str) -> str:
    """Codex re-review F5: the key a fresh build of an input takes when that
    input's figure is a marked row with no record. Its dependencies are never
    inferred (a press whose learner state hashes the same may have read it from
    other sources: an identical statement from another gap), so the old row
    stays withheld and is never reused; the fresh figure keeps its own record
    under this key (the old row holds the input's place in the reuse index),
    and every later press of the input takes the same key and reuses it."""

    return content_key({"input_hash": input_hash, "learner_inputs": LEARNER_INPUTS_RECORDED})


#: Codex re-review F5: names :func:`_recorded_input_key`'s keys (a version
#: label, not a tunable).
LEARNER_INPUTS_RECORDED = "recorded-v1"


def _with_learner_inputs(report: Mapping[str, Any], request: "FigureRequest") -> dict[str, Any]:
    """A quick figure's report with what its author's learner state was read
    from (follow-ups Nov 2: the record rich rows keep since learner data-relax
    2, ``protection.LEARNER_STATE_INPUTS_KEY``; never shown or sent to a model), so
    the figure is rechecked whenever it goes out. No learner state sent: the
    report exactly as before."""

    if not request.learner_state:
        return dict(report)
    return {**dict(report), LEARNER_STATE_INPUTS_KEY: request.learner_state_inputs}


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
    if request.source_check_id:
        # RW5c (Codex review F3): a rebuild asks afresh, even after a certification
        # bump. Absent otherwise: every other key is unchanged.
        key["source_check_id"] = request.source_check_id
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

        key["sketch"] = {"program_version": S.SKETCH_VERSION, "engine_sha256": ENGINE_SHA256}
    menu = R.rich_menu(tiers)
    if menu is not None:
        key["rich"] = {"tiers_allowed": list(menu),
                       "manim": {"version": S.MANIM_FIG_VERSION, "runtime": rich_runtime}
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
    rich_only = store.reusable(connection, input_hash, RICH_SPEC_VERSIONS) if rich_tiers_enabled(vault) else None
    if (rich_only is not None and not rich_only.get("fuller_of_id") and drawable_now(vault, rich_only)
            and learner_state_withheld(vault, repository, rich_only) is None):
        return rich_only
    # RW5d P2: the same input under the other settings of the panels and of
    # the sketch tier; only a shown figure that can be drawn now.
    for other_key in ([other_hash] if isinstance(other_hash, str) else list(other_hash)):
        other = store.reusable(connection, other_key, SPEC_VERSIONS)
        if (other is not None and other["verification"] in store.SHOWN and drawable_now(vault, other)
                and not source_rejected(vault, repository, other)
                and not _learner_inputs_unrecorded(other)):  # Codex re-review F5: withheld, never reused
            return other
    return None


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
                 find: FindSources | None = None, spawn_rich: SpawnRich | None = None,
                 cancelled: Callable[[], bool] | None = None) -> BuildOutcome:
    """Build one figure (module docstring). Raises :class:`FigureRefused`.

    ``live_vault`` gives the vault as configured now (the sidecar's loaded
    vault; unset, the vault is reloaded from disk): the build's
    :class:`~learnloop.figure_admission.FiguresGate` compares it with the
    start before every physical request and before the row is stored.
    ``find`` (RW5d) is the grounding retrieval (the sources service's, unset).
    ``spawn_rich`` (RW5d P2b) starts a rich job on the durable queue; unset,
    no rich tier is on the author's menu.

    ``cancelled`` (the press's cancel) is asked by the gate at the same
    moments, as a hold: once it answers True the build sends no further
    request and stores nothing. A paid answer already received stays
    checkpointed under the request identity, so the next press of the same
    input recovers it with no call. A build that passed its last check
    before the cancel landed still commits: that figure was paid for and
    finished, and listing it is honest."""

    request = check_request(vault, repository, request)
    if lesson_hosted(request) and not RICH.rich_on_menu(LESSON_TIERS):
        # RW5d P4b: a lesson's tiers name no rich one, so no rich job is
        # started from a lesson, whatever the caller passed.
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
    if cancelled is not None:
        hold = _cancel_hold(cancelled, hold)
    gate = FiguresGate(vault, key_for(request), live_vault=live_vault, hold=hold, repository=repository)
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


#: The hold's reason for a build whose press was cancelled (prose: the gate's record keeps only "held").
_BUILD_CANCELLED = "the figure request was cancelled"


def _cancel_hold(cancelled: Callable[[], bool],
                 other: Callable[[Any], str | None] | None) -> Callable[[Any], str | None]:
    def hold(current: Any) -> str | None:
        if cancelled():
            return _BUILD_CANCELLED
        return other(current) if other is not None else None

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
    # The advanced panels have no switch: every new build is prompted and keyed under their prompt version.
    # The plain one stays in the alternates below, which read figures stored before the panels.
    advanced = True
    sketch = sketch_ready(vault)
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
    if learner:
        # Codex final verify F6: a fresh figure built for a marked row with no
        # record sits under that setting's recorded-inputs key, so each other
        # setting's key is followed by its recorded one (``_reusable``'s
        # shown, drawable-now and never-unrecorded checks apply unchanged).
        other_hash = [key for plain in other_hash for key in (plain, _recorded_input_key(plain))]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if learner and _unrecorded_occupant(vault, connection, input_hash):
            # Codex re-review F5: a marked row with no record holds this
            # input; it is never reused nor given dependencies inferred from
            # this press: a fresh build keeps its own (one hop: it records).
            input_hash = _recorded_input_key(input_hash)
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

    if not rich_tiers_enabled(vault):
        return None
    job = RICH.rich_job_for(RICH.rich_jobs(repository), input_hash=input_hash)
    if job is None or (job.get("payload") or {}).get("fast_figure_id"):
        return None
    state = RICH.job_state(job)
    if state["state"] not in ("pending", "waiting_for_plan"):
        return None
    return BuildOutcome(None, reused=True, rich=_rich_line(request, job, state))


def retry_rich_job(vault: Any, repository: Repository, job_id: str) -> str:
    """Codex review F9: the error code of a rich job that ended with no row
    and may be requeued (failed, not waiting for the plan, never cancelled),
    or :class:`FigureRefused`. The requeued job is the same build (its
    payload and request identity), so a paid answer is recovered, not paid
    for again."""

    if not rich_tiers_enabled(vault):
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
    from learnloop.figures.protection import _withheld

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


def _step_three(vault: Any, repository: Repository, compiled: S.CompiledFigure, context: SourceContext,
                request: FigureRequest, grounding: Grounding | None, gate: FiguresGate) -> SC.Check | None:
    """RW5c's check of a spec that passed steps 1-2, or None with the switch off.
    Whatever goes wrong in it is a closed reason, never ``checked`` and never a
    failed build (G23f); a switch change stops the build as at every other step."""

    if not SC.enabled(vault):
        return None
    gate.check("source_check")
    spans = ([(key[0], key[1], f"{key[0]}:{key[1]}") for key in dict.fromkeys(context.keys)] if context.keys else
             [(str(request.extraction_id), str(span), str(span)) for span in context.span_texts]
             if request.extraction_id else [])
    try:
        return SC.check_figure(vault, repository, compiled, spans=spans,
                               grounding=(grounding or Grounding("anchor")).mode)
    except FiguresChanged:
        raise
    except Exception:  # noqa: BLE001 - a check that cannot run certifies nothing, and costs the figure nothing
        _LOG.warning("figures: the source check could not run", exc_info=True)
        return SC.failed_check(compiled)


def _author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                      author: R.FigureRoute, *, request_id: str, **kwargs: Any) -> BuildOutcome:
    """:func:`_author_attempts_and_store`, then one ``figure_author`` record per attempt (ADR-017),
    written once the build has ended, refused or failed, so a record never changes the build. A
    build stopped by :class:`FiguresChanged` (a ``BaseException``: the switch or the route changed
    under it) writes none, since a switched-off feature writes nothing."""

    attempts = FR.AuthorAttempts()
    try:
        outcome = _author_attempts_and_store(vault, repository, request, context, author, request_id=request_id,
                                             attempts=attempts, **kwargs)
    except Exception as exc:
        attempts.write(repository, request=request, request_id=request_id, model=author.model, error=exc)
        raise
    attempts.write(repository, request=request, request_id=request_id, model=author.model, outcome=outcome)
    return outcome


def _author_attempts_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                               author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int,
                               image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None,
                               input_hash: str, request_id: str, clock: Clock | None, gate: FiguresGate,
                               attempts: FR.AuthorAttempts, advanced: bool = False,
                               grounding: Grounding | None = None, sketch: bool = False,
                               tiers: Sequence[str] | None = None, spawn_rich: SpawnRich | None = None,
                               generation: int = 0) -> BuildOutcome:
    """At most two author calls, the second told the first's problems; then the figure is stored,
    shown or failed. Each attempt's verdict is noted in ``attempts`` (codes only) beside the
    ``problems`` the next prompt carries: a note is a list append, so it never steers the loop.

    :func:`.author_answer.read_answer` reads each answer from plain values; this loop makes the model
    calls and runs the checks a parsed figure needs (numerics, the sealed sketch engine, the source
    check), each behind the gate. What the attempts leave carries to the store: a figure whose only
    fault was its source check stays until a later answer parses a figure of its own."""

    problem = author.problem()
    if problem is not None:
        raise FigureRefused(problem.reason, problem.message)
    grounding = grounding or Grounding("anchor")
    show_me = show_me_input(request)
    images = (image,) if image is not None else ()
    learner = bool(request.learner_state)
    prompt_version = R.author_prompt_version(advanced=advanced, show_me=show_me, sketch=sketch, tiers=tiers,
                                             learner=learner)
    attempts.prompt_version = prompt_version
    # With a rich tier on the menu the contract is V3, whose status is always a tier judgment.
    v3 = tiers is not None
    request.tiers_allowed = tuple(tiers) if v3 else (("grammar", "sketch") if sketch else ("grammar",))
    brief: RICH.RichBrief | None = None
    quick_dropped: str | None = None
    # A rebuild's first attempt is told the difference its source check found (empty otherwise).
    problems: list[str] = list(request.initial_problems)
    compiled: S.CompiledFigure | None = None
    source_check: SC.Check | None = None
    report = V.Report()
    unsupported: tuple[str, str] | None = None
    sketched: K.CompiledSketch | None = None
    sketch_report: Any = None
    verdict: tuple[str, str] | None = None
    for attempt in range(R.MAX_AUTHOR_ATTEMPTS):
        attempts.start(attempt + 1)
        prompt = R.author_prompt(_author_context(request, context, digest, previous, problems, request_id=request_id,
                                                 grounding=grounding),
                                 advanced=advanced, show_me=show_me, sketch=sketch, tiers=tiers, learner=learner,
                                 rich_brief_max=RICH.RICH_BRIEF_MAX)
        try:
            output = author.ask(prompt, R.output_model(sketch=sketch, tiers=tiers), images=images,
                                metadata={"attempt": attempt + 1, "prompt_version": prompt_version})
        except FiguresChanged:
            raise  # the configuration changed: nothing more is asked, nothing stored
        except R.FigureUnavailable as exc:
            attempts.end(FR.code(exc.reason) or "unavailable", status="refused")
            if attempt == 0:
                raise FigureRefused(exc.reason, exc.message) from exc
            break
        except SpendLimitExceeded as exc:
            # The daily envelope refused it before sending (another process
            # spent the rest of the day meanwhile).
            attempts.end("capped", status="refused")
            if attempt == 0:
                raise FigureRefused("capped", f"Today's figure budget is used ({exc}).") from exc
            break
        except Exception as exc:  # noqa: BLE001 - a failed call ends the attempts, honestly labelled
            problems = [f"the figure model failed: {type(exc).__name__}"]
            attempts.end(FR.MODEL_FAILED, error=exc)
            if attempt == 0:
                continue
            break
        last = attempt == R.MAX_AUTHOR_ATTEMPTS - 1
        attempts.fact(author_status=AA.status_of(output))
        reading = AA.read_answer(output, last=last, tiers=tiers, sketch=sketch, grounded=grounding.mode != "none",
                                 advanced=advanced)
        for note in reading.notes:
            attempts.extra(note)
        verdict = reading.verdict or verdict
        found = reading.then
        if isinstance(found, AA.Retry):
            if found.parsed is not None:
                compiled = None
                sketch_report = None if found.parsed == "spec" else sketch_report
            problems = found.problems
            attempts.end(found.rule, problems=len(found.problems) if found.counted else None)
            continue
        if isinstance(found, AA.Unsupported):
            unsupported = (found.kind, found.reason)
            attempts.end(FR.UNSUPPORTED)
            break
        if isinstance(found, AA.Rich):
            # The optional quick figure is verified and shown as any spec or sketch; one that fails is
            # dropped and the brief carries on.
            brief, quick_dropped = found.brief, found.dropped
            compiled, sketched, sketch_report = None, None, None
            if isinstance(found.quick, AA.Spec):
                attempts.fact(predictions_dropped=len(found.quick.dropped))
                report = V.verify_numerics(found.quick.figure)
                report.author_predictions_dropped = found.quick.dropped
                if report.outcome == V.FAILED:
                    quick_dropped = report.reason
                else:
                    source_check = _step_three(vault, repository, found.quick.figure, context, request, grounding,
                                               gate)
                    if source_check is not None and source_check.outcome == SC.DIFFERS:
                        quick_dropped = (source_check.problems or [SC.REJECTED_REASON])[0]
                        source_check = None
                    else:
                        compiled = found.quick.figure
            elif isinstance(found.quick, AA.Sketch):
                try:
                    from learnloop.figures import sketch_verify as SV

                    gate.check("sketch")
                    attempts.fact(predictions_dropped=len(found.quick.dropped))
                    checked = SV.verify_sketch(found.quick.program, span_texts=context.span_texts)
                    checked.author_predictions_dropped = found.quick.dropped
                    if checked.outcome == V.FAILED:
                        quick_dropped = checked.reason
                    else:
                        sketched, sketch_report = found.quick.program, checked
                except K.SketchError as exc:
                    quick_dropped = exc.problems[0] if exc.problems else "the quick sketch is invalid"
                except FiguresChanged:
                    raise
                except Exception as exc:  # noqa: BLE001 - the quick sketch could not be run: dropped
                    quick_dropped = f"the quick sketch could not be run: {type(exc).__name__}"
            if quick_dropped is not None:
                attempts.extra(FR.QUICK_DROPPED)
            break
        if isinstance(found, AA.Sketch):
            compiled, sketched = None, found.program
            attempts.fact(predictions_dropped=len(found.dropped))
            from learnloop.figures import sketch_verify as SV

            gate.check("sketch")
            try:
                sketch_report = SV.verify_sketch(sketched, span_texts=context.span_texts)
                sketch_report.author_predictions_dropped = found.dropped
            except Exception as exc:  # noqa: BLE001 - the engine itself failed: an honest failure, never shown
                problems, sketched = [f"the sketch could not be run: {type(exc).__name__}"], None
                sketch_report = None
                attempts.end(FR.VERIFICATION_FAILED, error=exc)
                continue
            if sketch_report.outcome == V.FAILED:
                problems = list(sketch_report.problems) or [sketch_report.reason]
                sketched = None
                attempts.end(FR.VERIFICATION_FAILED, problems=len(problems))
                continue
            break
        sketched, sketch_report, compiled = None, None, found.figure
        attempts.fact(predictions_dropped=len(found.dropped))
        report = V.verify_numerics(compiled)
        report.author_predictions_dropped = found.dropped
        if report.outcome == V.FAILED:
            problems = [report.reason, *report.structural[1:], *report.invariant_problems[1:]]
            compiled = None
            attempts.end(FR.VERIFICATION_FAILED, problems=len(problems))
            continue
        # A stated claim the source check proves different is one more problem for the next attempt, whose
        # only spend this gate admits; on the last attempt the figure is kept, and withheld where it is shown.
        source_check = _step_three(vault, repository, compiled, context, request, grounding, gate)
        if source_check is not None and source_check.outcome == SC.DIFFERS and not last:
            problems = source_check.problems or [SC.REJECTED_REASON]
            attempts.end(FR.SOURCE_DIFFERS, problems=len(problems))
            continue
        if source_check is not None and source_check.outcome == SC.DIFFERS:
            attempts.extra(FR.SOURCE_DIFFERS)
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
    return _store_quick(vault, repository, request, context, author, compiled=compiled, unsupported=unsupported,
                        problems=problems, report=report, source_check=source_check, verdict=verdict, sketch=sketch,
                        v3=v3, versions=versions, asset_id=asset_id, input_hash=input_hash,
                        prompt_version=prompt_version, figure_id=figure_id, asked=asked, clock=clock, gate=gate,
                        grounding=grounding, rich_spawn=rich_spawn)


def _store_quick(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                 author: R.FigureRoute, *, compiled: S.CompiledFigure | None, unsupported: tuple[str, str] | None,
                 problems: list[str], report: V.Report, source_check: SC.Check | None,
                 verdict: tuple[str, str] | None, sketch: bool, v3: bool, versions: int, asset_id: str | None,
                 input_hash: str, prompt_version: str, figure_id: str, asked: dict[str, Any], clock: Clock | None,
                 gate: FiguresGate, grounding: Grounding, rich_spawn: _RichSpawn | None) -> BuildOutcome:
    """The grammar figure the attempts came to (shown, failed or unsupported), stored with its request, its
    verification and tier judgments and its source check in one transaction; a rich answer's quick figure
    carries the rich job's intent, and the job starts once it is stored."""

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
    row["verification_report"] = _with_learner_inputs(row["verification_report"], request)
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
            if source_check is not None and row["verification"] in store.SHOWN:
                # RW5c (F6, G23i): the check row and its verdict, in this transaction.
                SC.record(connection, figure_id, source_check, trigger="build", created_at=row["created_at"])
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

    if spawn is None or not figures_enabled(vault) or not rich_tiers_enabled(vault):
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
                              "revision": revision, **_inherited_extra(repository, previous)})
    return spawn.only(vault, repository, asked, gate=gate, clock=clock)


def _inherited_extra(repository: Repository, previous: Mapping[str, Any]) -> dict[str, Any]:
    """Codex review F4: a rich revision's job payload carries what the learner
    states its earlier versions' authors were sent were read from
    (:func:`inherited_learner_inputs`); absent when none was sent, so every
    other revision's payload is exactly as before."""

    inherited = inherited_learner_inputs(repository, previous)
    return {INHERITED_LEARNER_INPUTS_KEY: inherited} if inherited else {}


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
        "spec_version": S.SKETCH_VERSION, "model": author.model, "prompt_version": prompt_version,
        "input_hash": input_hash, "created_at": utc_now_iso(clock), "spec_json": None, "kind": None,
        "unsupported_kind": None, "program_version": S.SKETCH_VERSION, "engine_sha256": ENGINE_SHA256,
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
    row["verification_report"] = _with_learner_inputs(row["verification_report"], request)
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


def rebuild_request(vault: Any, repository: Repository, base: Mapping[str, Any]) -> FigureRequest:
    """*Rebuild* of a figure whose stated claim differs (§6.6, Codex review F3):
    a new version through the revision path, never a reuse of the rejected row.
    No note from the learner; the difference is code's text, sent as the first
    attempt's problems, and the check row it answers joins the reuse key."""

    found = SC.current_row(repository, str(base["id"])) if SC.enabled(vault) and SC.grammar_row(base) else None
    if found is None or found["outcome"] != SC.DIFFERS:
        raise FigureRefused("validation_error", "That figure has no difference from the book to rebuild.")
    request = revision_request(repository, base, "")
    request.source_check_id = str(found["id"])
    request.initial_problems = SC.stored_problems(found)
    return request


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


def rich_revision_retry(vault: Any, repository: Repository, job_id: str) -> FigureRequest | None:
    """Codex re-review F14: "try again" on a correction of an animation whose
    job stored a failure (the line :func:`rich_pending` lists): the same
    correction (the figure it corrects, the learner's note), built afresh.
    Its input is the same, and the stored failure starts the next generation,
    so the rich author is asked anew (never the failed answer's checkpoint).
    None for any other job (:func:`retry_rich_job` decides those)."""

    if not rich_tiers_enabled(vault):
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


__all__ = [
    "BuildOutcome",
    "build_figure",
    "rebuild_request",
    "revision_request",
    "ensure_rich_job",
    "resume_rich_intents",
    "retry_rich_job",
]
