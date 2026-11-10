"""Reader RW5d P3: the figure trace the diagnoser reads at Submit (spec_reader_show_me_figures_v1 §11.2, §11.4b).

When an attempt used a figure (a ``help_assists`` figure row of its
submission or attached to it), the split diagnoser's context gains, for this
attempt only, each figure's goal (who wrote it), what it demonstrates, its
tier and the learner's predictions made under that attempt's figure row
(``figure_predictions.assist_id``, migration 232) with the observed answer and
their "what changed?" text, as they stood at its Submit (Codex review F7),
under the prompt-version suffix :data:`SUFFIX` (the
``+workbench-v1`` precedent). Every other attempt's context renders and
hashes exactly as before. Never the figure's program (§11.4b).

Read by SQL (``interactive_figures``, ``figure_predictions``), never through
the figure package or its store (``evidence-never-reads-figures``); a figure
any passage of which is held out now is left out (the text-gap path's one
predicate, ``figure_prediction_withheld``). Figures are help, never
evidence: the grade is the blind grader's, and the grader never sees any of
this (SM5).
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import closing
import json
from typing import Any

from learnloop.db.connection import connect

SUFFIX = "+figures-v1"
NOTE = (
    "The learner opened the interactive figures below while working this attempt (help, never evidence: each "
    "counted as one hint, and the grade is the blind grader's). A prediction is what the learner expected before "
    "changing the figure; the observed answer is what the figure showed; 'what changed' is their own words."
)
#: Prompt-size bounds (never judgments).
MAX_FIGURES = 6
TEXT_CHARS = 600


def _json(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _demonstrates(spec_json: Any) -> str:
    data = _json(spec_json, {})
    return str(data.get("demonstrates") or "")[:TEXT_CHARS] if isinstance(data, Mapping) else ""


def _by(stamp: Any, cutoff: str | None) -> bool:
    """Whether a row written at ``stamp`` is at or before the attempt's Submit
    (no cutoff on record: every linked row)."""

    return cutoff is None or (stamp is not None and str(stamp) <= cutoff)


def figure_trace_for_attempt(vault: Any, repository: Any, attempt: Mapping[str, Any]) -> dict[str, Any] | None:
    """The figures an attempt used, or None (no figure row, the switch off,
    or every figure held out now)."""

    from learnloop.diagnosis.text_gaps.sources import figure_prediction_withheld
    from learnloop.figure_admission import help_kind_enabled

    if vault is None or not help_kind_enabled(vault):
        return None
    attempt_id = str(attempt.get("id") or "")
    # The attempt's Submit: what the learner wrote on a figure after it is not this attempt's.
    cutoff = str(attempt.get("created_at") or "") or None
    submission = attempt.get("submission_id")
    item_id = str(attempt.get("practice_item_id") or "")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
            "('help_assists', 'interactive_figures', 'figure_predictions')")}
        if tables != {"help_assists", "interactive_figures", "figure_predictions"}:
            return None
        if "figure_id" not in {row[1] for row in connection.execute("PRAGMA table_info(help_assists)")}:
            return None
        rows = connection.execute(
            "SELECT id, figure_id, hint_kind, request FROM help_assists WHERE assist_kind = 'figure' AND shown = 1 "
            "AND figure_id IS NOT NULL AND (attempt_id = ? OR (attempt_id IS NULL AND submission_id = ? "
            "AND practice_item_id = ?)) ORDER BY COALESCE(shown_at, requested_at), rowid",
            (attempt_id, str(submission or ""), item_id)).fetchall()
        linked = "assist_id" in {row[1] for row in connection.execute("PRAGMA table_info(figure_predictions)")}
        figures: list[dict[str, Any]] = []
        seen: set[str] = set()
        for assist_id, first_figure, hint_kind, request in rows:
            # Codex review F7: only the predictions made under THIS attempt's
            # figure row (linked when recorded), as they stood at its Submit:
            # one made or explained later never changes this attempt's trace.
            made = connection.execute(
                "SELECT figure_id, prediction_index, learner_answer, observed_json, matched, explanation_text, "
                "explained_at, created_at FROM figure_predictions WHERE assist_id = ? ORDER BY created_at, "
                "prediction_index", (assist_id,)).fetchall() if linked else []
            made = [entry for entry in made if _by(entry[7], cutoff)]
            # The figure the row opened and each version a linked prediction was made on.
            for figure_id in dict.fromkeys([str(first_figure), *(str(entry[0]) for entry in made)]):
                if figure_id in seen or len(figures) >= MAX_FIGURES:
                    continue
                seen.add(figure_id)
                found = connection.execute(
                    "SELECT f.id AS figure_id, f.extraction_id, f.span_ids_json, f.region_json, f.asset_id, "
                    "f.input_span_ids_json, f.input_span_keys_json, f.goal_text, f.spec_json, f.tier, f.kind, "
                    "r.goal_author FROM interactive_figures AS f LEFT JOIN figure_requests AS r "
                    "ON r.id = f.request_id WHERE f.id = ?", (figure_id,)).fetchone()
                if found is None:
                    continue
                names = ("figure_id", "extraction_id", "span_ids_json", "region_json", "asset_id",
                         "input_span_ids_json", "input_span_keys_json", "goal_text", "spec_json", "tier", "kind",
                         "goal_author")
                figure = dict(zip(names, found, strict=True))
                predictions = [
                    {"prompt_index": int(index), "learner_answer": str(answer or "")[:TEXT_CHARS],
                     "observed_answer": str((_json(observed, {}) or {}).get("answer") or "")[:TEXT_CHARS],
                     "matched": bool(matched),
                     **({"what_changed": str(explanation)[:TEXT_CHARS]}
                        if explanation and explained_at and _by(explained_at, cutoff) else {})}
                    for on, index, answer, observed, matched, explanation, explained_at, _created in made
                    if str(on) == figure_id]
                figures.append({"figure": figure, "how": "chooser" if hint_kind == "explore_figure" else "asked",
                                "predictions": predictions})
    trace: list[dict[str, Any]] = []
    for entry in figures:
        figure = entry["figure"]
        if figure_prediction_withheld(vault, repository, figure) is not None:
            continue
        trace.append({
            "order": len(trace) + 1,
            "how": entry["how"],
            "goal": str(figure.get("goal_text") or "")[:TEXT_CHARS] or None,
            "goal_author": figure.get("goal_author") if figure.get("goal_text") else None,
            "tier": str(figure.get("tier") or "grammar"),
            "kind": figure.get("kind"),
            "demonstrates": _demonstrates(figure.get("spec_json")),
            "predictions": entry["predictions"],
        })
    if not trace:
        return None
    return {"note": NOTE, "figures": trace}


__all__ = ["MAX_FIGURES", "NOTE", "SUFFIX", "TEXT_CHARS", "figure_trace_for_attempt"]
