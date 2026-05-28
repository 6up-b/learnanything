from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.vault.writer import (
    upsert_concept,
    upsert_error_type,
    upsert_learning_object,
    upsert_practice_item,
)

runner = CliRunner()


def _write_content(vault_root) -> None:
    upsert_concept(
        vault_root,
        "singular_value_decomposition",
        {"title": "Singular Value Decomposition", "type": "procedure"},
    )
    upsert_error_type(
        vault_root,
        {
            "id": "conceptual_slip",
            "title": "Conceptual slip",
            "description": "Confuses the core definition.",
            "severity_default": 0.7,
            "is_misconception": True,
        },
    )
    upsert_learning_object(
        vault_root,
        {
            "id": "lo_svd_definition",
            "title": "SVD definition",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "summary": "SVD factorizes a matrix into orthogonal factors and singular values.",
        },
    )
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "U Sigma V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {"id": "conceptual_slip", "description": "Confuses SVD.", "max_grade": 1}
                ],
            },
        },
    )


def test_local_only_learning_loop(tmp_path):
    vault_root = tmp_path / "vault"
    v = ["--vault", str(vault_root)]

    assert runner.invoke(app, ["init", str(vault_root)]).exit_code == 0
    assert runner.invoke(app, ["add-subject", "linear-algebra", "Linear Algebra", *v]).exit_code == 0
    _write_content(vault_root)

    # --fix-state safely syncs derived SQLite state for the newly written content.
    doctor = runner.invoke(app, ["doctor", "--fix-state", "--json", *v])
    assert doctor.exit_code == 0, doctor.output
    assert json.loads(doctor.output)["clean"] is True

    # Cold active LOs with local Practice Items start in probe mode so the
    # learner can establish an initial skill estimate before ordinary review.
    first_review = runner.invoke(app, ["review", "--json", *v])
    assert first_review.exit_code == 0
    first_items = json.loads(first_review.output)["items"]
    assert [item["practice_item_id"] for item in first_items] == ["pi_svd_define_001"]
    assert first_items[0]["components"]["probe_eig"] > 0.0

    attempt = runner.invoke(
        app,
        [
            "attempt",
            "pi_svd_define_001",
            "--answer",
            "It is U Sigma V transpose but I confused a detail.",
            "--criterion-points",
            "correctness=2",
            "--confidence",
            "4",
            "--error-type",
            "conceptual_slip",
            "--json",
            *v,
        ],
    )
    assert attempt.exit_code == 0, attempt.output
    result = json.loads(attempt.output)["attempt"]
    attempt_id = result["attempt_id"]
    assert result["rubric_score"] == 2

    # Inspect every derived row created by the attempt.
    repository = Repository(vault_root / "state.sqlite")
    assert repository.fetch_practice_attempt(attempt_id) is not None
    assert repository.fetch_grading_evidence(attempt_id)
    item_state = repository.practice_item_state("pi_svd_define_001")
    assert item_state.due_at is not None
    assert item_state.stability is not None
    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery.evidence_count == 1
    assert repository.latest_attempt_surprise(attempt_id) is not None
    errors = repository.active_errors_by_learning_object("lo_svd_definition")
    assert errors and errors[0].error_type == "conceptual_slip"

    show = runner.invoke(app, ["show", attempt_id, "--json", *v])
    assert show.exit_code == 0
    shown = json.loads(show.output)["record"]
    assert shown["grading_evidence"]
    assert shown["surprise"] is not None

    why = runner.invoke(app, ["why", "pi_svd_define_001", "--json", *v])
    assert why.exit_code == 0

    # The recent error now boosts the item back into the queue.
    second_review = runner.invoke(app, ["review", "--json", *v])
    assert second_review.exit_code == 0
    items = json.loads(second_review.output)["items"]
    assert [item["practice_item_id"] for item in items] == ["pi_svd_define_001"]
    assert items[0]["components"]["recent_error"] > 0.0

    final_doctor = runner.invoke(app, ["doctor", "--json", *v])
    assert final_doctor.exit_code == 1
    final_payload = json.loads(final_doctor.output)
    assert final_payload["clean"] is False
    assert {issue["code"] for issue in final_payload["issues"]} == {"sql:derived_state_rebuild_stale"}

    rebuild = runner.invoke(app, ["rebuild-derived-state", "--json", *v])
    assert rebuild.exit_code == 0, rebuild.output
    assert json.loads(rebuild.output)["rebuild"]["replayed_attempts"] == 1

    rebuilt_doctor = runner.invoke(app, ["doctor", "--json", *v])
    assert rebuilt_doctor.exit_code == 0, rebuilt_doctor.output
    assert json.loads(rebuilt_doctor.output)["clean"] is True
