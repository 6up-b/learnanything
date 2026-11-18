"""A figure's predictions: the learner's answer, what the figure shows before and after, and whether it matched.

:func:`record_prediction` keeps the learner's answer to one of a shown figure's predictions (:mod:`.listing`'s
:func:`~learnloop.figures.listing.shown_figure`), decided by code (the spec's outcome, or the sketch engine's run for a
sketch), once per figure and prediction; a missed one queues the learner-text reading. :func:`record_explanation`
keeps the optional "what changed, and why?" once, read with a missed answer. Both are formative. This module imports
the listing, the view and the request, nothing of the build.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.figure_admission import predictions_enabled
from learnloop.figures import sketch as K
from learnloop.figures import spec as S
from learnloop.figures.listing import shown_figure
from learnloop.figures.request import FigureRefused, prediction_home
from learnloop.figures.view import _code_owned_labels, _coded_answer, _prediction_view
from learnloop.ids import new_ulid


EXPLANATION_CHARS = 600
ANSWER_CHARS = 120
PREDICTION_PREFIX = "fpr_"


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
    # RW5c: under code-owned labels an area prediction's choices go out as the
    # shades' element ids; the stored answer stays the shade's own label.
    coded = _code_owned_labels(vault, repository, row, compiled) if outcome.get("kind") == "area" and isinstance(
        compiled, S.CompiledFigure) else None
    if coded is not None:
        answer = next((label for label, element in coded.items() if element == answer), "")

    def delivered(found: Mapping[str, Any] | None) -> dict[str, Any]:
        view = _prediction_view(found) or {}
        return _coded_answer(view, coded) if coded is not None and view else view

    if answer not in outcome["choices"]:
        raise FigureRefused("validation_error", "Pick one of the prediction's answers.")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        existing = store.prediction_for(connection, figure_id, int(index))
    if existing is not None:
        return delivered(existing)
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
    return delivered({**prediction, "matched": prediction["matched"]})


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
    row, compiled = shown_figure(vault, repository, str(found["figure_id"]))
    observed = found.get("observed") or {}
    coded = _code_owned_labels(vault, repository, row, compiled) if observed.get("kind") == "area" and isinstance(
        compiled, S.CompiledFigure) else None
    with repository.atomic():
        set_now = store.set_explanation(repository.connection(), prediction_id, text, at=utc_now_iso(clock))
    if set_now and not found["matched"]:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_figure_explanation

        _queued(enqueue_figure_explanation(vault, repository, prediction_id=prediction_id, clock=clock), on_queued)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        view = _prediction_view(store.prediction(connection, prediction_id)) or {}
    return _coded_answer(view, coded) if coded is not None and view else view


def _queue_formative(vault: Any, repository: Repository, prediction_id: str, *, clock: Clock | None) -> str | None:
    from learnloop.diagnosis.text_gaps.jobs import enqueue_figure_prediction

    return enqueue_figure_prediction(vault, repository, prediction_id=prediction_id, clock=clock)


def _queued(job_id: str | None, on_queued: Callable[[str], None] | None) -> None:
    if job_id and on_queued is not None:
        on_queued(job_id)


__all__ = [
    "ANSWER_CHARS",
    "EXPLANATION_CHARS",
    "PREDICTION_PREFIX",
    "record_explanation",
    "record_prediction",
]
