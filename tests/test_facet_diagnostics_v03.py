from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.learner.facet_diagnostics import lo_relative_coverage, mastery_diagnostic_view
from learnloop.diagnosis.followups import evaluate_intervention_followup
from learnloop.content.authoring.practice_generation import build_diagnostic_practice_plan
from learnloop.diagnosis.probes import facet_expected_information_gain
from learnloop.learner.recall_coverage import resolve_coverage
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault


def _add_item(root, item_id: str, facets: list[str], *, repair_targets: list[str] | None = None) -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "repair_targets": repair_targets or [],
            "prompt": f"Probe {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": 0.5,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Conceptual slip.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _wrong_attempt(loaded, repository):
    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", 2.0, 1.0, 3, NOW_ISO, ALGORITHM_VERSION, NOW_ISO)
    )
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="wrong"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )


def test_subthreshold_noisy_item_creates_single_facet_generation_need_and_logs_slate(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_noisy_recall", ["recall", "unrelated_a", "unrelated_b"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="negative",
        bayesian_surprise=1.0,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.9,
        target_facets=["recall"],
        available_minutes=30,
    )

    assert decision.triggered is False
    need = repository.intervention_need_for_attempt(result.attempt_id)
    assert need["target_facets"] == ["recall"]
    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    slate = features["context"]["candidate_slate"]
    noisy = next(row for row in slate if row["practice_item_id"] == "pi_noisy_recall")
    assert noisy["gate_passed"] is False
    assert noisy["filtered_reason"] == "subthreshold_overlap"
    assert noisy["target_precision"] == pytest.approx(1 / 3)
    assert features["context"]["generation_need_id"] == need["id"]
    plan = build_diagnostic_practice_plan(loaded, repository, learning_object_id=result.learning_object_id)
    assert plan.targets[0].need_id == need["id"]
    assert plan.targets[0].target_facets == ["recall"]


def test_single_facet_probe_passes_gate_even_with_multiple_open_facets(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_clean_recall", ["recall"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)
    for facet, uncertainty in {"alpha": 0.7, "beta": 0.6}.items():
        repository.upsert_facet_uncertainty_state(
            {
                "learning_object_id": result.learning_object_id,
                "facet_id": facet,
                "hypothesis_marginal": {f"facet_solid:{facet}": 0.4, f"facet_absent:{facet}": 0.6},
                "uncertainty": uncertainty,
                "status": "open",
                "opened_by_attempt_id": result.attempt_id,
                "opened_reason": "low_facet_outcome",
                "last_evidence_at": NOW_ISO,
                "algorithm_version": ALGORITHM_VERSION,
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            }
        )

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="negative",
        bayesian_surprise=1.0,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.9,
        target_facets=["recall", "alpha", "beta"],
        available_minutes=30,
    )

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_clean_recall"
    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    clean = next(row for row in features["context"]["candidate_slate"] if row["practice_item_id"] == "pi_clean_recall")
    assert clean["dominant_target_facet"] == "recall"
    assert clean["diagnostic_gate_facets"] == ["alpha", "beta", "recall"]
    assert clean["diagnostic_gate_source"] == "failed-set"
    assert clean["target_precision"] == 1.0
    assert clean["gate_passed"] is True
    assert "recall" in features["ability_vector"]["facet_hypothesis_prior"]
    assert "recall" in features["item_demand_vector"]["per_facet_eig"]
    assert "recall" in features["ability_vector"]["realized_facet_uncertainty_drop"]


def test_open_facet_restriction_makes_disjoint_correct_attempt_zero_weight(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_other_facet", ["other"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    first = _wrong_attempt(loaded, repository)

    second = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_other_facet", learner_answer_md="correct"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    debug = repository.attempt_debug_payload(second.attempt_id)
    assert debug["lo_relative_coverage"] == 0.0
    assert debug["observation_weight"] == 0.0
    assert repository.facet_uncertainty_state(first.learning_object_id, "recall").status in {"open", "resolving"}


def test_hedged_learner_confidence_opens_uncertainty_even_with_partial_credit(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)

    result = apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft("pi_svd_define_001", "I think it is U Sigma V transpose."),
            attempt_id="attempt_hedged_partial",
            grade=ResolvedGrade(
                rubric_score=3,
                criterion_points={"correctness": 3.0},
                evidence_rows=[
                    {
                        "id": "evidence_hedged_partial",
                        "criterion_id": "correctness",
                        "points_awarded": 3.0,
                        "evidence": "Partial but hedged.",
                        "notes": None,
                        "local_grader_id": "self",
                        "grader_tier": 1,
                        "learner_confidence": "hedged",
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    state = repository.facet_uncertainty_state(result.learning_object_id, "recall")
    assert state is not None
    assert state.opened_reason == "hedged_confidence"
    assert state.uncertainty >= loaded.config.facet_diagnostic.hedge_uncertainty_floor


def test_tiny_authored_facet_share_does_not_earn_per_facet_coverage(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    upsert_practice_item(
        root,
        {
            "id": "pi_tiny_share",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall", "other"],
            "evidence_weights": {"recall": 0.05, "other": 0.95},
            "prompt": "Mostly other.",
            "expected_answer": "Answer.",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    item = loaded.practice_items["pi_tiny_share"]
    coverage = resolve_coverage(
        item,
        loaded.rubric_for_item(item),
        attempt_type="independent_attempt",
        hints_used=0,
        learner_answer_md="engaged",
    )

    value, trace = lo_relative_coverage(
        loaded,
        repository,
        learning_object_id="lo_svd_definition",
        normalized_facet_weights=coverage.normalized_facet_weights,
        effective_item_coverage=1.0,
    )

    assert trace["per_facet_coverage"]["recall"] == 0.0
    assert trace["per_facet_coverage"]["other"] == 1.0
    assert value == pytest.approx(0.5)


def test_variance_floor_blocks_confidence_before_required_facet_breadth(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_other_required", ["other"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    for index in range(5):
        complete_self_graded_attempt(
            loaded,
            repository,
            AttemptDraft("pi_svd_define_001", f"correct {index}"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW),
        )

    mastery = repository.mastery_state("lo_svd_definition")
    assert mastery.logit_variance >= 0.25
    debug = repository.attempt_debug_payload(
        repository.list_recent_attempts_by_learning_object("lo_svd_definition", limit=1)[0]["id"]
    )
    assert debug["covered_required_fraction"] == pytest.approx(0.5)
    assert debug["mastery_variance_floor"] == pytest.approx(0.25)


def test_full_breadth_multi_facet_attempt_keeps_coverage_scale_at_one(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_full_breadth", ["recall", "alpha", "beta"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    item = loaded.practice_items["pi_full_breadth"]
    coverage = resolve_coverage(
        item,
        loaded.rubric_for_item(item),
        attempt_type="independent_attempt",
        hints_used=0,
        learner_answer_md="engaged",
    )

    value, trace = lo_relative_coverage(
        loaded,
        repository,
        learning_object_id="lo_svd_definition",
        normalized_facet_weights=coverage.normalized_facet_weights,
        effective_item_coverage=1.0,
    )

    assert value == pytest.approx(1.0)
    assert trace["per_facet_coverage"] == {"alpha": 1.0, "beta": 1.0, "recall": 1.0}


def test_facet_eig_is_zero_for_unsupported_candidate_and_positive_for_isolating_probe():
    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.5}

    assert facet_expected_information_gain(
        marginal,
        facet_id="recall",
        candidate_facet_support={"other"},
        fatal_error_ids=set(),
    ) == pytest.approx(0.0)
    assert facet_expected_information_gain(
        marginal,
        facet_id="recall",
        candidate_facet_support={"recall"},
        fatal_error_ids=set(),
    ) > 0.0


def test_facet_uncertainty_rebuilds_from_attempts_and_grading_evidence(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)
    before = repository.facet_uncertainty_state(result.learning_object_id, "recall")

    rebuild_derived_state(loaded, repository, learning_object_ids=[result.learning_object_id], clock=FrozenClock(NOW))

    after = repository.facet_uncertainty_state(result.learning_object_id, "recall")
    assert after is not None
    assert after.hypothesis_marginal == pytest.approx(before.hypothesis_marginal)
    assert after.uncertainty == pytest.approx(before.uncertainty)


def test_mastery_diagnostic_view_distinguishes_known_gap_from_unexamined(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_other_required", ["other"])
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)
    repository.upsert_facet_uncertainty_state(
        {
            "learning_object_id": result.learning_object_id,
            "facet_id": "recall",
            "hypothesis_marginal": {"facet_solid:recall": 0.01, "facet_absent:recall": 0.99},
            "uncertainty": 0.05,
            "status": "resolved",
            "opened_by_attempt_id": result.attempt_id,
            "opened_reason": "low_facet_outcome",
            "last_evidence_at": NOW_ISO,
            "algorithm_version": ALGORITHM_VERSION,
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    view = mastery_diagnostic_view(loaded, repository, result.learning_object_id)
    states = {facet["facet_id"]: facet["state"] for facet in view["facets"]}

    assert states["recall"] == "known_gap"
    assert states["other"] == "unexamined"


def test_diagnostic_plan_carries_grader_repair_rationales(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="negative",
        bayesian_surprise=1.0,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.9,
        target_facets=["recall"],
        available_minutes=30,
    )
    assert decision.need_id is not None

    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source="codex",
        repair_suggestions=[
            {"practice_mode": "targeted_review", "rationale": "Contrast symmetric and orthogonal matrices."},
            {"practice_mode": "worked_example", "rationale": "Study a full proof deriving the dot product identity."},
            {"rationale": "   "},
        ],
    )

    plan = build_diagnostic_practice_plan(loaded, repository, learning_object_id=result.learning_object_id)
    target = plan.targets[0]
    assert target.repair_rationales == [
        {"rationale": "Contrast symmetric and orthogonal matrices.", "practice_mode": "targeted_review"},
        {"rationale": "Study a full proof deriving the dot product identity.", "practice_mode": "worked_example"},
    ]
    assert "repair_rationales" in target.as_dict()


def test_need_target_builder_freezes_structured_repair_focus(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    loaded = load_vault(root)
    repository = Repository(paths.sqlite_path)
    result = _wrong_attempt(loaded, repository)
    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source="codex",
        repair_suggestions=[
            {
                "practice_mode": "targeted_review",
                "rationale": "Contrast the definition with a supporting mechanism.",
                "target_evidence_families": ["supporting_mechanism"],
            }
        ],
    )

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="negative",
        bayesian_surprise=1.0,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.9,
        target_facets=["recall"],
        available_minutes=30,
    )

    assert decision.need_id is not None
    need = repository.intervention_need_for_attempt(result.attempt_id)
    assert need["target_facets"] == ["recall", "supporting_mechanism"]
    assert need["diagnostic_focus"]["primary_target_facet"] == "recall"
    assert need["diagnostic_focus"]["diagnostic_gate_source"] == "enriched"
    assert need["diagnostic_focus"]["repair_rationales"] == [
        {
            "rationale": "Contrast the definition with a supporting mechanism.",
            "practice_mode": "targeted_review",
            "target_evidence_families": ["supporting_mechanism"],
        }
    ]

    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    assert features["context"]["diagnostic_focus"] == need["diagnostic_focus"]
    plan = build_diagnostic_practice_plan(loaded, repository, learning_object_id=result.learning_object_id)
    target = plan.targets[0]
    assert target.target_facets == ["recall", "supporting_mechanism"]
    assert target.diagnostic_focus == need["diagnostic_focus"]
    assert target.repair_rationales[0]["target_evidence_families"] == ["supporting_mechanism"]
