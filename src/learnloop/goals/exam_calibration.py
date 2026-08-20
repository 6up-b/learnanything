"""Exam calibration: did the model's pre-exam predictions come true?

Pairs frozen ``exam_predictions`` with the outcomes of the ``exam_attempt``
attempts they were applied to, and scores calibration two ways:

  * **Item predictions** — ``predicted_correctness`` vs the applied exam
    attempt's realized correctness: n, Brier, log loss, and a 10-bin reliability
    table (mean predicted vs mean observed per bin).
  * **Facet projections** — the frozen projected-at-due recall per scope facet
    vs the realized facet outcome (the mean correctness of exam items testing
    that facet — a documented approximation, since one exam item is one
    correlated observation of its facets).

Only completed sessions contribute (an answered item without an applied
attempt has no outcome yet).
"""

from __future__ import annotations

from math import log
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

_EPS = 1e-6
_BIN_COUNT = 10
MINIMUM_CURVE_N = 30
_ANSWER_CONFIDENCE_PROBABILITY = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.70, 5: 0.90}


def _reliability_table(pairs: list[tuple[float, float]], *, bins: int = _BIN_COUNT) -> dict[str, Any]:
    """n / Brier / log loss / equal-width reliability table for (predicted, observed) pairs."""

    n = len(pairs)
    if n == 0:
        return {"n": 0, "brier": None, "log_loss": None, "bins": []}
    brier = sum((predicted - observed) ** 2 for predicted, observed in pairs) / n
    log_loss = 0.0
    for predicted, observed in pairs:
        p = min(max(predicted, _EPS), 1.0 - _EPS)
        o = min(max(observed, 0.0), 1.0)
        log_loss += -(o * log(p) + (1.0 - o) * log(1.0 - p))
    log_loss /= n

    buckets: list[dict[str, Any]] = []
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        # Last bin is closed on the right so predicted == 1.0 lands somewhere.
        members = [
            (predicted, observed)
            for predicted, observed in pairs
            if (lower <= predicted < upper) or (index == bins - 1 and predicted == 1.0)
        ]
        if members:
            mean_predicted = sum(p for p, _ in members) / len(members)
            mean_observed = sum(o for _, o in members) / len(members)
        else:
            mean_predicted = None
            mean_observed = None
        buckets.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(members),
                "mean_predicted": mean_predicted,
                "mean_observed": mean_observed,
            }
        )
    return {"n": n, "brier": brier, "log_loss": log_loss, "bins": buckets}


def calibration_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """Pooled prediction-outcome calibration across all completed exam sessions."""

    predictions = repository.all_exam_predictions()

    item_pairs: list[tuple[float, float]] = []
    facet_pairs: list[tuple[float, float]] = []
    facet_by_id: dict[str, list[tuple[float, float]]] = {}

    # Cache answers per session so each is read once.
    answers_by_session: dict[str, dict[str, dict[str, Any]]] = {}

    for prediction in predictions:
        session_id = prediction["session_id"]
        if session_id not in answers_by_session:
            answers_by_session[session_id] = {
                answer["practice_item_id"]: answer
                for answer in repository.exam_answers(session_id)
            }
        answer = answers_by_session[session_id].get(prediction["practice_item_id"])
        if answer is None or not answer.get("attempt_id"):
            continue
        attempt = repository.fetch_practice_attempt(answer["attempt_id"])
        if attempt is None or attempt.get("correctness") is None:
            continue
        outcome = float(attempt["correctness"])
        item_pairs.append((float(prediction["predicted_correctness"]), outcome))

        for facet_id, snapshot in (prediction.get("facet_projection") or {}).items():
            projected = snapshot.get("projected_recall")
            if projected is None:
                continue
            facet_pairs.append((float(projected), outcome))
            facet_by_id.setdefault(facet_id, []).append((float(projected), outcome))

    facet_breakdown = {
        facet_id: {
            "n": len(pairs),
            "mean_projected": sum(p for p, _ in pairs) / len(pairs),
            "mean_observed": sum(o for _, o in pairs) / len(pairs),
        }
        for facet_id, pairs in sorted(facet_by_id.items())
    }

    items = _reliability_table(item_pairs)
    items["minimum_n"] = MINIMUM_CURVE_N
    items["curve_available"] = items["n"] >= MINIMUM_CURVE_N

    duel_rows = repository.calibration_duel_pairs()
    learner_brier = None
    model_brier = None
    if duel_rows:
        learner_brier = sum(
            (_ANSWER_CONFIDENCE_PROBABILITY[int(row["answer_confidence"])] - float(row["correctness"])) ** 2
            for row in duel_rows
        ) / len(duel_rows)
        model_brier = sum(
            (float(row["model_predicted_correctness"]) - float(row["correctness"])) ** 2
            for row in duel_rows
        ) / len(duel_rows)

    return {
        "version": 1,
        "items": items,
        "facets": {
            **_reliability_table(facet_pairs),
            "by_facet": facet_breakdown,
        },
        "duel": {
            "n": len(duel_rows),
            "learner_brier": learner_brier,
            "model_brier": model_brier,
        },
    }
