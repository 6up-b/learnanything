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
right?" version, the earlier spec and the learner's note. No learner data.

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
import sqlite3
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from typing import Any

from learnloop.ai.execution import content_key, gate_model_requests
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.figure_admission import FiguresChanged, FiguresGate, figures_enabled
from learnloop.figures import grammar as G
from learnloop.figures import routes as R
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.ids import new_ulid

ORIGINS = ("selection", "library", "tutor")
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
    "illustrative": "AI-built illustration of an interpretation · not checked against the book",
}


class FigureRefused(Exception):
    """A request the Reader may not make (``code``: ``figures_disabled``,
    ``exam_material``, ``region_disabled``, ``revisions_disabled``,
    ``predictions_disabled``, ``not_found``, ``validation_error``, ``no_image_input``,
    ``region_unreadable``) or a route that cannot be called (``capped``,
    ``unpriced``, ``unrouted``, ``unavailable``, ``models_off``)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FigureRequest:
    extraction_id: str
    span_ids: list[str]
    #: ``{span_id, bbox}``: a learner-drawn box over a figure block.
    region: dict[str, Any] | None = None
    origin: str = "selection"
    supersedes_id: str | None = None
    revision_note: str | None = None


@dataclass
class SourceContext:
    passage: list[dict[str, Any]] = field(default_factory=list)
    around: list[dict[str, Any]] = field(default_factory=list)
    #: Every sent span's text (for quote verification).
    span_texts: dict[str, str] = field(default_factory=dict)
    figure_span: str | None = None


def enabled(vault: Any) -> bool:
    """``figures.enabled``: the one predicate (:func:`learnloop.figure_admission.figures_enabled`)."""

    return figures_enabled(vault)


def build_key(vault: Any) -> tuple[Any, ...]:
    """What a build depends on, compared before every request it makes
    (:class:`~learnloop.figure_admission.FiguresGate`): the vault, the switch,
    the author route as configured, the day's cap and the price."""

    from learnloop.practice_index.paid import plan_route

    section = getattr(vault.config, "figures", None)
    return (str(vault.root), figures_enabled(vault), plan_route(vault, R.AUTHOR_TASK, None),
            getattr(section, "max_daily_cost_usd", None), getattr(section, "price_per_million", None))


def _switch(vault: Any, name: str) -> bool:
    return enabled(vault) and bool(getattr(vault.config.figures, name, False))


def predictions_enabled(vault: Any) -> bool:
    return _switch(vault, "predictions_enabled")


def region_enabled(vault: Any) -> bool:
    return _switch(vault, "region_enabled")


def revisions_enabled(vault: Any) -> bool:
    return _switch(vault, "revisions_enabled")


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


def figure_withheld(vault: Any, repository: Repository, figure_id: str) -> bool:
    """Whether a stored figure may not go out now (its row is gone, or any
    span it was built from is held out). Fails closed."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        return True
    return withheld_message(vault, repository, row["extraction_id"], _figure_spans(row)) is not None


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


def property_checks(report: Mapping[str, Any]) -> list[str]:
    """The closed keys of the checks a shown figure passed (§8.3 steps 1-2)."""

    held = {str(entry.get("kind")) for entry in report.get("invariants") or () if entry.get("holds")}
    passed = {"values_finite"} | held
    if report.get("shades"):
        passed.add("shaded_areas")
    return [key for key in PROPERTY_CHECKS if key in passed]


def _label(row: Mapping[str, Any]) -> str:
    verification = row["verification"]
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


def figure_view(vault: Any, repository: Repository, row: Mapping[str, Any], *, versions: int = 1) -> dict[str, Any]:
    """A figure as the Reader shows it. The spec goes out as JSON text (its
    keys are the spec's own), and only for a shown figure. A prediction's
    answer is never sent before the learner answers it. A stored "verified"
    shows as an illustration (:func:`shown_row`)."""

    row = shown_row(row)
    region = row.get("region") or {}
    view: dict[str, Any] = {
        "figure_id": row["id"], "extraction_id": row["extraction_id"], "span_ids": list(row.get("span_ids") or ()),
        # Under the selection's last block; a region's figure (no selected
        # text) under the region's block (Codex review F2).
        "anchor_span_id": (list(row.get("span_ids") or ()) or [region.get("span_id")])[-1],
        "region": row.get("region"),
        "origin": row["origin"], "verification": row["verification"], "kind": row.get("kind"),
        "label": _label(row), "reason": (row.get("verification_report") or {}).get("reason") or None,
        "unsupported_kind": row.get("unsupported_kind"), "supersedes_id": row.get("supersedes_id"),
        "revision_note": row.get("revision_note"), "versions": versions, "created_at": row["created_at"],
        "spec_json": None, "demonstrates": None, "assumptions": [], "predictions": [], "property_checks": [],
    }
    if row["verification"] not in store.SHOWN or not row.get("spec_json"):
        return view
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


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def request_hash(request: FigureRequest, context: SourceContext, image_digest: str | None) -> str:
    return content_key({
        "spec_version": S.SPEC_VERSION, "prompt_version": R.AUTHOR_PROMPT_VERSION,
        "extraction_id": request.extraction_id,
        "span_ids": list(request.span_ids), "region": request.region, "origin": request.origin,
        "passage": context.passage, "around": context.around, "image_sha256": image_digest,
        "supersedes_id": request.supersedes_id, "revision_note": request.revision_note,
    })


def _validated_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest:
    if not enabled(vault):
        raise FigureRefused("figures_disabled", "Explorable figures are switched off (figures.enabled).")
    if request.origin not in ORIGINS:
        raise FigureRefused("validation_error", f"Unknown figure origin {request.origin!r}.")
    spans = [str(span) for span in dict.fromkeys(request.span_ids) if span][:40]
    if not spans and not request.region:
        raise FigureRefused("validation_error", "Select a passage, an equation or a figure first.")
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
    return FigureRequest(extraction_id=str(request.extraction_id), span_ids=spans, region=region,
                         origin=request.origin, supersedes_id=request.supersedes_id, revision_note=note)


def check_request(vault: Any, repository: Repository, request: FigureRequest) -> FigureRequest:
    """Validate a request and refuse held-out material, on the request path,
    before any job or call (the handler's first step; the build repeats it)."""

    request = _validated_request(vault, repository, request)
    spans = [*request.span_ids, *([request.region["span_id"]] if request.region else [])]
    message = withheld_message(vault, repository, request.extraction_id, spans)
    if message is not None:
        raise FigureRefused("exam_material", message)
    if request.supersedes_id is not None:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            base = store.figure(connection, request.supersedes_id)
        if base is None or base["extraction_id"] != request.extraction_id:
            raise FigureRefused("not_found", "That figure is not on this source.")
        if withheld_message(vault, repository, base["extraction_id"], _figure_spans(base)) is not None:
            raise FigureRefused("exam_material", "That figure's passage is held out now.")
    return request


@dataclass
class BuildOutcome:
    view: dict[str, Any]
    reused: bool
    author_calls: int = 0


def _author_context(request: FigureRequest, context: SourceContext, image_digest: str | None,
                    previous: Mapping[str, Any] | None, problems: Sequence[str], *, request_id: str) -> dict[str, Any]:
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
    if previous is not None:
        payload["earlier_version"] = {"spec_json": previous.get("spec_json") or "",
                                      "verification": previous.get("verification")}
        payload["learner_note"] = request.revision_note or ""
    if problems:
        payload["problems_with_the_last_attempt"] = list(problems)[:12]
    return payload


def build_figure(vault: Any, repository: Repository, request: FigureRequest, *, author_client: Any | None = None,
                 clock: Clock | None = None, live_vault: Callable[[], Any] | None = None) -> BuildOutcome:
    """Build one figure (module docstring). Raises :class:`FigureRefused`.

    ``live_vault`` gives the vault as configured now (the sidecar's loaded
    vault; unset, the vault is reloaded from disk): the build's
    :class:`~learnloop.figure_admission.FiguresGate` compares it with the
    start before every physical request and before the row is stored."""

    request = check_request(vault, repository, request)
    context = source_context(vault, repository, request)
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
    input_hash = request_hash(request, context, digest)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reused = store.reusable(connection, input_hash, S.SPEC_VERSION)
        seen = store.latest_for_input(connection, input_hash, S.SPEC_VERSION)
    if reused is not None:
        return _reused(vault, repository, reused)
    # One build per input at a time (Codex review F7): an identical request
    # made while one runs waits for it and takes its figure, with no call.
    with _building(repository, input_hash):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            # Reread inside the lock (fix round 2, F7): a build that committed
            # between the reads above left `reused` empty but `seen` naming
            # its row, so only this read can tell its figure is reusable.
            reused = store.reusable(connection, input_hash, S.SPEC_VERSION)
            latest = store.latest_for_input(connection, input_hash, S.SPEC_VERSION)
            generation = store.builds_for_input(connection, input_hash, S.SPEC_VERSION)
        if reused is not None:
            return _reused(vault, repository, reused)
        if latest is not None and (seen is None or latest["id"] != seen["id"]):
            return _reused(vault, repository, latest)
        # The request's identity is its input and its retry generation, never
        # a fresh id: rerun after a crash between a paid answer and its row,
        # the same prompt recovers that answer (its checkpoint or receipt)
        # with no second request; a stored failure starts the next
        # generation, so "try again" asks afresh.
        request_id = content_key({"input_hash": input_hash, "generation": generation})
        author.bind_owner(f"figure:{request_id}")
        gate = FiguresGate(vault, build_key, live_vault=live_vault)
        try:
            with gate_model_requests(gate):
                return _author_and_store(vault, repository, request, context, author, previous=previous,
                                         versions=versions, image=image, asset_id=asset_id, digest=digest,
                                         input_hash=input_hash, request_id=request_id, clock=clock, gate=gate)
        except FiguresChanged as exc:
            raise FigureRefused("figures_changed", str(exc)) from exc


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


def _reused(vault: Any, repository: Repository, row: Mapping[str, Any]) -> BuildOutcome:
    return BuildOutcome(figure_view(vault, repository, row, versions=_chain_length(repository, str(row["id"]))),
                        reused=True)


def _author_and_store(vault: Any, repository: Repository, request: FigureRequest, context: SourceContext,
                      author: R.FigureRoute, *, previous: Mapping[str, Any] | None, versions: int,
                      image: tuple[str, bytes] | None, asset_id: str | None, digest: str | None, input_hash: str,
                      request_id: str, clock: Clock | None, gate: FiguresGate) -> BuildOutcome:
    problem = author.problem()
    if problem is not None:
        raise FigureRefused(problem.reason, problem.message)
    images = (image,) if image is not None else ()
    problems: list[str] = []
    compiled: S.CompiledFigure | None = None
    report = V.Report()
    output: Any = None
    unsupported: tuple[str, str] | None = None
    for attempt in range(R.MAX_AUTHOR_ATTEMPTS):
        prompt = R.author_prompt(_author_context(request, context, digest, previous, problems, request_id=request_id))
        try:
            output = author.ask(prompt, R.FigureAuthorOutputV1, images=images,
                                metadata={"attempt": attempt + 1, "prompt_version": R.AUTHOR_PROMPT_VERSION})
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
        if str(output.status).strip().lower() == "unsupported":
            unsupported = (" ".join(str(output.unsupported_kind or "").split())[:80] or "something else",
                           " ".join(str(output.unsupported_reason or "").split())[:400])
            break
        try:
            compiled = S.parse_spec(output.spec_json)
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
    row: dict[str, Any] = {
        "id": figure_id, "extraction_id": request.extraction_id, "span_ids": request.span_ids,
        "region": request.region, "asset_id": asset_id,
        # Everything the author was sent, for every later held-out recheck (F1).
        "input_span_ids": list(dict.fromkeys([*context.span_texts, *([asset_id] if asset_id else [])])),
        "origin": request.origin,
        "supersedes_id": request.supersedes_id, "revision_note": request.revision_note,
        "spec_version": S.SPEC_VERSION, "model": author.model, "prompt_version": R.AUTHOR_PROMPT_VERSION,
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
    try:
        with repository.atomic():
            connection = repository.connection()
            store.insert_figure(connection, row)
            append_judgment(connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id,
                            judge="verifier", input_hash=input_hash, verdict=report.outcome,
                            rationale=(report.reason or "")[:400], created_at=row["created_at"])
    except sqlite3.IntegrityError:
        # Another process stored this input's figure first (the reuse index):
        # that one is the figure; this build's paid calls keep their receipts.
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            first = store.reusable(connection, input_hash, S.SPEC_VERSION)
        if first is None:
            raise
        return _reused(vault, repository, first)
    stored = dict(row)
    stored["verification_report"] = row["verification_report"]
    return BuildOutcome(figure_view(vault, repository, stored, versions=versions), reused=False,
                        author_calls=author.made)


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


def list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]:
    """The figures of one source as the Reader shows them: per version chain,
    the newest shown version (else the newest failed or unsupported one), of
    the current spec version, and never one whose passage is held out now."""

    if not enabled(vault):
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return []
        rows = store.figures_for_extraction(connection, extraction_id)
    rows = [row for row in rows if row["spec_version"] == S.SPEC_VERSION]
    by_id = {row["id"]: row for row in rows}
    chains: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        chains.setdefault(_root(by_id, row), []).append(row)
    views = []
    for chain in chains.values():
        shown = [row for row in chain if row["verification"] in store.SHOWN]
        pick = (shown or chain)[-1]
        if withheld_message(vault, repository, pick["extraction_id"], _figure_spans(pick)) is not None:
            continue
        try:
            views.append(figure_view(vault, repository, pick, versions=len(chain)))
        except S.SpecError:
            continue
    return sorted(views, key=lambda view: view["created_at"])


def shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], S.CompiledFigure]:
    """A figure that may be shown now: shown verification, current spec
    version, its passage not held out."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        raise FigureRefused("not_found", "That figure is no longer kept.")
    if row["verification"] not in store.SHOWN or row["spec_version"] != S.SPEC_VERSION or not row.get("spec_json"):
        raise FigureRefused("not_found", "That figure is not shown.")
    if withheld_message(vault, repository, row["extraction_id"], _figure_spans(row)) is not None:
        raise FigureRefused("exam_material", "That figure's passage is held out now.")
    return row, S.parse_spec(row["spec_json"])


# ---------------------------------------------------------------------------
# Predictions (formative)
# ---------------------------------------------------------------------------

def record_prediction(vault: Any, repository: Repository, figure_id: str, index: int, answer: str, *,
                      clock: Clock | None = None, on_queued: Callable[[str], None] | None = None) -> dict[str, Any]:
    """The learner's prediction, its observed before/after readout and
    whether it matched (code decides). Idempotent per (figure, prediction).
    ``on_queued`` hears the learner-text job a missed one queued (the
    sidecar wakes its gap worker with it; Codex review F6)."""

    if not predictions_enabled(vault):
        raise FigureRefused("predictions_disabled", "Figure predictions are switched off (figures.predictions_enabled).")
    row, compiled = shown_figure(vault, repository, figure_id)
    dropped = set((row.get("verification_report") or {}).get("dropped_predictions") or ())
    if not 0 <= int(index) < len(compiled.predictions) or int(index) in dropped:
        raise FigureRefused("validation_error", "That figure has no such prediction.")
    outcome = S.prediction_outcome(compiled, int(index))
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
        "id": PREDICTION_PREFIX + new_ulid(), "figure_id": figure_id, "extraction_id": row["extraction_id"],
        "prediction_index": int(index), "learner_answer": answer,
        "observed": {"kind": outcome["kind"], "before": outcome["before"], "after": outcome["after"],
                     "answer": outcome["answer"], "change": outcome["change"]},
        "matched": answer == outcome["answer"], "explanation_text": None, "created_at": utc_now_iso(clock),
    }
    with repository.atomic():
        store.insert_prediction(repository.connection(), prediction)
    if not prediction["matched"]:
        _queued(_queue_formative(vault, repository, prediction["id"], clock=clock), on_queued)
    return _prediction_view({**prediction, "matched": prediction["matched"]}) or {}


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
        set_now = store.set_explanation(repository.connection(), prediction_id, text)
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
    "LABELS",
    "build_figure",
    "check_request",
    "enabled",
    "figure_view",
    "figure_withheld",
    "list_figures",
    "predictions_enabled",
    "record_explanation",
    "record_prediction",
    "region_enabled",
    "revisions_enabled",
    "shown_figure",
    "withheld_message",
]
