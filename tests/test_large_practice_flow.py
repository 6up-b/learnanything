from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_many_open_text_practice_items_schedule_and_record_attempt(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    for index in range(100):
        write_yaml(
            paths.practice_item_path("linear-algebra", f"pi_bulk_open_text_{index:03d}"),
            {
                "schema_version": 1,
                "id": f"pi_bulk_open_text_{index:03d}",
                "learning_object_id": "lo_svd_definition",
                "subjects": None,
                "practice_mode": "constructed_response",
                "attempt_types_allowed": ["open_text"],
                "evidence_facets": ["application"],
                "evidence_weights": {"application": 1.0},
                "prompt": f"Explain SVD application {index}.",
                "expected_answer": "SVD can expose singular directions and support low-rank approximation.",
                "difficulty": 0.55,
                "tags": [],
                "hints": [],
                "hint_policy": {
                    "max_useful_hints": 0,
                    "fsrs_rating_cap_by_hint": {},
                    "mastery_alpha_dampening_by_hint": {},
                },
                "grading_rubric": {
                    "max_points": 4,
                    "criteria": [{"id": "correctness", "points": 4, "description": "Correct SVD application."}],
                    "fatal_errors": [],
                },
                "provenance": {"origin": "human", "source_refs": []},
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )

    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )

    queue = build_due_queue(vault, repository, clock=clock, persist_explanations=True)

    assert len(queue) >= 100
    assert "pi_bulk_open_text_000" in {item.practice_item_id for item in queue}

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_bulk_open_text_000",
            learner_answer_md="SVD gives low-rank approximations by truncating small singular values.",
            attempt_type="open_text",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=clock,
    )

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["attempt_type"] == "open_text"
    assert attempt["practice_item_id"] == "pi_bulk_open_text_000"
