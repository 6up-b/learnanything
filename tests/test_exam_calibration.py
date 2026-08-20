from __future__ import annotations

import pytest

from learnloop.goals.exam_calibration import calibration_report
from learnloop.vault.loader import load_vault

from tests.helpers import NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"


def _insert_pair(repository, *, session_id, index, predicted, outcome, projected=None, facet="recall"):
    """Insert one prediction + applied exam attempt + answer with known values."""

    item_id = f"pi_{session_id}_{index}"
    attempt_id = f"att_{session_id}_{index}"
    facet_projection = None
    if projected is not None:
        facet_projection = {facet: {"projected_recall": projected, "current_recall": projected, "target_recall": 0.8}}
    repository.insert_exam_predictions(
        [
            {
                "id": f"pred_{session_id}_{index}",
                "session_id": session_id,
                "practice_item_id": item_id,
                "predicted_correctness": predicted,
                "facet_projection": facet_projection,
                "created_at": NOW_ISO,
            }
        ]
    )
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              rubric_score, correctness, created_at
            )
            VALUES (?, ?, ?, 'short_answer', 'exam_attempt', ?, ?, ?)
            """,
            (attempt_id, item_id, LO_ID, int(round(outcome * 4)), outcome, NOW_ISO),
        )
        connection.commit()
    repository.upsert_exam_answer(
        {
            "session_id": session_id,
            "practice_item_id": item_id,
            "answer_md": "x",
            "rubric_score": int(round(outcome * 4)),
            "correctness": outcome,
            "attempt_id": attempt_id,
        }
    )


def _session(repository, session_id, item_ids):
    repository.insert_exam_session(
        {
            "id": session_id,
            "goal_id": "goal_linear_algebra_ml",
            "status": "completed",
            "item_order": item_ids,
            "report": None,
            "started_at": NOW_ISO,
            "updated_at": NOW_ISO,
            "completed_at": NOW_ISO,
        }
    )


def test_known_pairs_produce_known_brier_and_bins(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)

    pairs = [(0.9, 1.0), (0.8, 1.0), (0.2, 0.0), (0.1, 0.0)]
    _session(repository, "sess1", [f"pi_sess1_{i}" for i in range(len(pairs))])
    for index, (predicted, outcome) in enumerate(pairs):
        _insert_pair(repository, session_id="sess1", index=index, predicted=predicted, outcome=outcome, projected=predicted)

    report = calibration_report(vault, repository)
    items = report["items"]
    assert items["n"] == 4
    # Brier = mean((p-o)^2) = (0.01 + 0.04 + 0.04 + 0.01)/4
    assert items["brier"] == pytest.approx(0.025)

    populated = {(b["lower"], b["count"], b["mean_predicted"], b["mean_observed"]) for b in items["bins"] if b["count"]}
    assert populated == {
        (0.9, 1, 0.9, 1.0),
        (0.8, 1, 0.8, 1.0),
        (0.2, 1, 0.2, 0.0),
        (0.1, 1, 0.1, 0.0),
    }
    # 10 bins total, four populated.
    assert len(items["bins"]) == 10
    assert sum(1 for b in items["bins"] if b["count"]) == 4


def test_facet_projection_calibration(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)

    # Projected recall vs realized facet outcome (item correctness on that facet).
    pairs = [(0.9, 1.0), (0.7, 0.0)]
    _session(repository, "sessF", [f"pi_sessF_{i}" for i in range(len(pairs))])
    for index, (projected, outcome) in enumerate(pairs):
        _insert_pair(repository, session_id="sessF", index=index, predicted=projected, outcome=outcome, projected=projected, facet="recall")

    report = calibration_report(vault, repository)
    facets = report["facets"]
    assert facets["n"] == 2
    # Brier over (projected, outcome): (0.01 + 0.49)/2 = 0.25
    assert facets["brier"] == pytest.approx(0.25)
    assert facets["by_facet"]["recall"]["n"] == 2
    assert facets["by_facet"]["recall"]["mean_projected"] == pytest.approx(0.8)
    assert facets["by_facet"]["recall"]["mean_observed"] == pytest.approx(0.5)


def test_empty_calibration_is_defined(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)
    report = calibration_report(vault, repository)
    assert report["items"]["n"] == 0
    assert report["items"]["brier"] is None
    assert report["facets"]["n"] == 0
