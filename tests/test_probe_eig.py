from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probes import (
    Hypothesis,
    HypothesisSet,
    build_hypothesis_set,
    conditional_distribution,
    probe_eig_component,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _insert_error(repository: Repository, error_type: str = "conceptual_slip", severity: float = 0.7) -> None:
    repository.insert_error_event(
        {
            "id": f"err_{error_type}",
            "learning_object_id": "lo_svd_definition",
            "error_type": error_type,
            "severity": severity,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def _add_non_fatal_item(vault_root) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_svd_no_fatal",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "List the factors of SVD.",
            "expected_answer": "U, Sigma, V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(NOW),
    )


def test_conditional_distribution_is_normalized_for_every_hypothesis():
    known = ["conceptual_slip"]
    for hypothesis in [
        Hypothesis(label="mastered"),
        Hypothesis(label="unfamiliar"),
        Hypothesis(label="misconception:conceptual_slip", error_type="conceptual_slip"),
    ]:
        distribution = conditional_distribution(
            hypothesis,
            fatal_error_ids={"conceptual_slip"},
            known_error_types=known,
        )
        assert sum(distribution.values()) == pytest.approx(1.0)


def test_probe_eig_higher_when_item_probes_active_misconception(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_non_fatal_item(vault_root)
    repository = Repository(paths.sqlite_path)
    _insert_error(repository)
    loaded = load_vault(vault_root)

    hypothesis_set = build_hypothesis_set(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert any(h.error_type == "conceptual_slip" for h in hypothesis_set.hypotheses)

    probing = probe_eig_component(hypothesis_set, loaded.practice_items["pi_svd_define_001"])
    non_probing = probe_eig_component(hypothesis_set, loaded.practice_items["pi_svd_no_fatal"])

    assert probing > non_probing > 0.0


def test_probe_eig_is_deterministic_and_normalized():
    hypothesis_set = HypothesisSet(
        learning_object_id="lo_svd_definition",
        hypotheses=[
            Hypothesis(label="mastered"),
            Hypothesis(label="unfamiliar"),
            Hypothesis(label="misconception:conceptual_slip", error_type="conceptual_slip"),
        ],
        prior={"mastered": 0.4, "unfamiliar": 0.3, "misconception:conceptual_slip": 0.3},
    )

    from learnloop.vault.models import PracticeItem, Rubric, RubricFatalError

    item = PracticeItem(
        id="pi_probe",
        learning_object_id="lo_svd_definition",
        practice_mode="short_answer",
        prompt="probe?",
        expected_answer="x",
        grading_rubric=Rubric(
            max_points=4,
            criteria=[],
            fatal_errors=[RubricFatalError(id="conceptual_slip", description="d", max_grade=1)],
        ),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )

    first = probe_eig_component(hypothesis_set, item)
    second = probe_eig_component(hypothesis_set, item)
    assert first == second
    # Normalized by log(|H|) so it stays in a sane range.
    assert 0.0 < first <= 1.0
