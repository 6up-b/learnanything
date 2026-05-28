from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    complete_self_graded_attempt,
    compute_attempt_application,
)
from learnloop.services.followups import evaluate_attempt_intervention_followup, evaluate_intervention_followup
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault


def test_dont_know_keeps_full_coverage_and_updates_facet_recall(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="I do not know",
            attempt_type="dont_know",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["effective_coverage"] == 1.0
    assert debug["coverage_trace"]["source"] == "evidence_weights"
    assert debug["reliability_trace"]["grader_confidence_factor"] == 1.0
    assert debug["facet_outcomes"] == {"recall": 0.0}
    assert debug["ability_transition"]["transition_type"] == "expected_skill_gain"
    assert debug["ability_transition"]["expected_skill_gain"] > 0.0
    assert debug["ability_transition"]["target_facets"] == ["recall"]
    assert debug["ability_transition"]["applied_to_belief_counts"] is False
    assert debug["ability_transition"]["applied_to_mastery"] is False
    assert debug["ability_transition"]["applied_to_facet_recall"] is False
    transition = repository.ability_transition_event(result.attempt_id)
    assert transition is not None
    assert transition["transition_type"] == "expected_skill_gain"
    assert transition["expected_skill_gain"] == debug["ability_transition"]["expected_skill_gain"]
    assert transition["target_facets"] == ["recall"]
    assert transition["applied_to_belief_counts"] is False
    assert transition["applied_to_mastery"] is False
    assert transition["applied_to_facet_recall"] is False

    event = repository.error_events_for_attempt(result.attempt_id)[0]
    assert event["error_type"] == "recall_failure"
    assert event["severity"] >= 0.60

    aggregate = repository.facet_recall_state("lo_svd_definition", "recall")
    item_local = repository.facet_recall_state("lo_svd_definition", "recall", "pi_svd_define_001")
    assert aggregate is not None
    assert item_local is not None
    assert aggregate.recall_beta > 1.0
    assert aggregate.raw_coverage_mass == 1.0
    assert aggregate.independent_evidence_mass == 1.0
    assert aggregate.consecutive_failures == 1


def test_hinted_dont_know_is_scaffold_failure_and_dampens_coverage_only_from_surface_policy(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _set_hint_coverage_dampening(paths, {"1": 0.8})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="I still do not know",
            attempt_type="dont_know",
            hints_used=1,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    debug = result.debug_payload
    assert debug["effective_coverage"] == 0.8
    assert debug["coverage_trace"]["coverage_modifiers"]["hint_surface_factor"] == 0.8
    assert debug["reliability_trace"]["hint_mastery_factor"] == 0.5
    assert repository.error_events_for_attempt(result.attempt_id)[0]["error_type"] == "scaffold_failure"


def test_zero_score_independent_attempt_uses_rubric_coverage_and_confidence_as_reliability(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["recall", "formula"]
    item["evidence_weights"] = {}
    item["criterion_facet_weights"] = {"correctness": {"recall": 2.0, "formula": 1.0}}
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    application = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft("pi_svd_define_001", "wrong answer", attempt_type="independent_attempt"),
            attempt_id="attempt_zero_score_rubric_coverage",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.4,
                confidence=2,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    debug = application.attempt_debug_payload
    assert debug["coverage_trace"]["source"] == "rubric"
    assert debug["effective_coverage"] == 0.75
    assert debug["coverage_trace"]["covered_facets"] == {"formula": 0.25, "recall": 0.5}
    assert debug["reliability_trace"]["grader_confidence_factor"] == 0.4
    assert debug["reliability_trace"]["observation_reliability"] == 0.4
    assert debug["observation_weight"] == 0.30000000000000004
    assert debug["facet_outcomes"] == {"formula": 0.0, "recall": 0.0}


def test_blank_independent_attempt_is_damped_and_flagged_for_manual_review(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=5),
        clock=FrozenClock(NOW),
    )

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    debug = repository.attempt_debug_payload(result.attempt_id)
    assert result.manual_review_reason == "blank_answer"
    assert attempt["manual_review"] is True
    assert attempt["manual_review_reason"] == "blank_answer"
    assert debug["coverage_trace"]["coverage_modifiers"]["response_engagement_factor"] == 0.5
    assert debug["effective_coverage"] == 0.5
    assert debug["reliability_trace"]["observation_reliability"] == 1.0


def test_repeated_failure_triggers_intervention_need_without_surprise(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    first = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    second = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    decision = evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=second.attempt_id,
        learning_object_id=second.learning_object_id,
        practice_item_id=second.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=0.0,
        grader_confidence=1.0,
        error_event_written=True,
        max_error_severity=repository.error_events_for_attempt(second.attempt_id)[0]["severity"],
        target_facets=["recall"],
        lo_independent_evidence_mass=2.0,
        clock=FrozenClock(NOW),
    )

    assert decision.triggered is False
    assert decision.intent == "repair"
    assert decision.need_id is not None
    assert "repeated_same_item_failure" in ",".join(decision.triggered_actions)
    assert repository.pending_intervention_needs("lo_svd_definition")[0]["target_facets"] == ["recall"]


def test_high_unfamiliar_probe_posterior_records_intervention_need(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.config.scheduler.followup.tau_followup_nats = 99.0
    vault.config.scheduler.followup.tau_severe_error = 2.0
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=5),
        clock=FrozenClock(NOW),
    )

    decision = evaluate_attempt_intervention_followup(vault, repository, result=result, clock=FrozenClock(NOW))
    need = repository.pending_intervention_needs("lo_svd_definition")[0]

    assert decision.need_id == need["id"]
    assert decision.intent == "probe"
    assert need["trigger_reason"] == "high_unfamiliar_posterior"
    assert need["blocked_reason"] == "no_suitable_item"
    assert need["target_facets"] == ["recall"]
    assert f"intervention_followup:high_unfamiliar_posterior:{result.practice_item_id}" in decision.triggered_actions


def test_second_same_facet_failure_counts_across_different_items(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    first_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    second_item = read_yaml(first_item_path)
    second_item["id"] = "pi_svd_define_002"
    second_item["prompt"] = "State the key pieces of an SVD factorization."
    second_item["expected_answer"] = "U, singular values, and V transpose."
    second_item["created_at"] = "2026-05-19T12:00:01Z"
    second_item["updated_at"] = "2026-05-19T12:00:01Z"
    write_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_002"), second_item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    second = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_002", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    second_event = repository.error_events_for_attempt(second.attempt_id)[0]
    second_debug = repository.attempt_debug_payload(second.attempt_id)
    assert second_event["severity"] >= 0.80
    assert second_debug["severity_traces"]["recall_failure"]["recent_same_item_failures"] == 0
    assert second_debug["severity_traces"]["recall_failure"]["recent_same_facet_failures"] == 1

    decision = evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=second.attempt_id,
        learning_object_id=second.learning_object_id,
        practice_item_id=second.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=0.0,
        grader_confidence=1.0,
        error_event_written=True,
        max_error_severity=second_event["severity"],
        target_facets=["recall"],
        lo_independent_evidence_mass=2.0,
        clock=FrozenClock(NOW),
    )

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_001"
    assert "intervention_followup:repeated_same_facet_failure:pi_svd_define_002" in decision.triggered_actions


def test_error_attribution_targets_unmapped_facet_before_whole_item_fallback(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["concept", "numeric"]
    item["evidence_weights"] = {"concept": 0.5, "numeric": 0.5}
    item["criterion_facet_weights"] = {"correctness": {"concept": 1.0}}
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    application = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft("pi_svd_define_001", "Correct concept, arithmetic slip.", attempt_type="independent_attempt"),
            attempt_id="attempt_targeted_numeric_error",
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[
                    GradeAttribution(
                        "conceptual_slip",
                        0.6,
                        target_evidence_families=["numeric"],
                    )
                ],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    assert application.attempt_debug_payload["facet_outcomes"] == {"concept": 1.0, "numeric": 0.0}


def test_error_attribution_target_facets_are_canonicalized_before_facet_outcomes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.facets_path,
        {
            "schema_version": 1,
            "facets": [
                {
                    "id": "numeric",
                    "title": "Numeric Work",
                    "aliases": ["arithmetic"],
                    "description": None,
                    "tags": [],
                },
                {
                    "id": "concept",
                    "title": "Concept",
                    "aliases": [],
                    "description": None,
                    "tags": [],
                },
            ],
        },
    )
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["concept", "numeric"]
    item["evidence_weights"] = {"concept": 0.5, "numeric": 0.5}
    item["criterion_facet_weights"] = {"correctness": {"concept": 1.0}}
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    application = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft("pi_svd_define_001", "Correct concept, arithmetic slip.", attempt_type="independent_attempt"),
            attempt_id="attempt_alias_targeted_error",
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[
                    GradeAttribution(
                        "conceptual_slip",
                        0.6,
                        target_evidence_families=["arithmetic"],
                    )
                ],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    assert application.attempt_debug_payload["facet_outcomes"] == {"concept": 1.0, "numeric": 0.0}


def test_rubric_criterion_names_infer_targeted_facet_outcomes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = [
        "identify_retained_vs_discarded_singular_values",
        "compute_spectral_error_from_sigma",
        "compute_frobenius_error_from_sigma",
        "justify_with_truncated_svd",
    ]
    item["evidence_weights"] = {}
    item.pop("criterion_facet_weights", None)
    item["grading_rubric"] = {
        "max_points": 4,
        "criteria": [
            {
                "id": "c_identify_discarded_values",
                "points": 1.0,
                "description": "Identifies discarded singular values.",
            },
            {
                "id": "c_spectral_error",
                "points": 1.0,
                "description": "States the spectral-norm error.",
            },
            {
                "id": "c_frobenius_error",
                "points": 1.0,
                "description": "States the Frobenius-norm error.",
            },
            {
                "id": "c_justification",
                "points": 1.0,
                "description": "Justifies the truncated SVD norm rule.",
            },
        ],
        "fatal_errors": [],
    }
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    application = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                "pi_svd_define_001",
                "I do not remember how to find the spectral norm, but Frobenius is sqrt(5).",
            ),
            attempt_id="attempt_missing_spectral_norm",
            grade=ResolvedGrade(
                rubric_score=3,
                criterion_points={
                    "c_identify_discarded_values": 1.0,
                    "c_spectral_error": 0.0,
                    "c_frobenius_error": 1.0,
                    "c_justification": 1.0,
                },
                evidence_rows=[],
                error_attributions=[GradeAttribution("recall_failure", 0.4)],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=FrozenClock(NOW),
    )

    assert application.attempt_debug_payload["facet_outcomes"] == {
        "identify_retained_vs_discarded_singular_values": 1.0,
        "compute_spectral_error_from_sigma": 0.0,
        "compute_frobenius_error_from_sigma": 1.0,
        "justify_with_truncated_svd": 1.0,
    }


def test_intervention_need_targets_failed_facet_not_whole_item(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = [
        "identify_retained_vs_discarded_singular_values",
        "compute_spectral_error_from_sigma",
        "compute_frobenius_error_from_sigma",
        "justify_with_truncated_svd",
    ]
    item["evidence_weights"] = {}
    item.pop("criterion_facet_weights", None)
    item["grading_rubric"] = {
        "max_points": 4,
        "criteria": [
            {"id": "c_identify_discarded_values", "points": 1.0, "description": "Identifies discarded singular values."},
            {"id": "c_spectral_error", "points": 1.0, "description": "States the spectral-norm error."},
            {"id": "c_frobenius_error", "points": 1.0, "description": "States the Frobenius-norm error."},
            {"id": "c_justification", "points": 1.0, "description": "Justifies the truncated SVD norm rule."},
        ],
        "fatal_errors": [],
    }
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know.", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=5),
        clock=FrozenClock(NOW),
    )
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            "pi_svd_define_001",
            "I do not remember how to find the spectral norm, but Frobenius is sqrt(5).",
        ),
        SelfGradeInput(
            criterion_points={
                "c_identify_discarded_values": 1.0,
                "c_spectral_error": 0.0,
                "c_frobenius_error": 1.0,
                "c_justification": 1.0,
            },
            confidence=5,
            error_type="recall_failure",
        ),
        clock=FrozenClock(NOW),
    )

    decision = evaluate_attempt_intervention_followup(vault, repository, result=result, clock=FrozenClock(NOW))
    needs = repository.pending_intervention_needs("lo_svd_definition")

    assert decision.intent in {"probe", "repair"}
    assert needs[0]["target_facets"] == ["compute_spectral_error_from_sigma"]


def test_bad_item_suspicion_uses_prior_snapshot_not_current_attempt_update(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    repository.upsert_mastery_state(
        MasteryState(
            "lo_svd_definition",
            2.5,
            1.0,
            5,
            "2026-05-24T12:00:00Z",
            vault.config.algorithms.algorithm_version,
            "2026-05-24T12:00:00Z",
        )
    )

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    debug = repository.attempt_debug_payload(result.attempt_id)
    quality = repository.practice_item_quality_state("pi_svd_define_001")
    assert quality is not None
    assert quality.bad_item_suspicion > 0.0
    assert "failure_despite_high_lo_state" in quality.suspicion_reasons
    assert debug["prior_bad_item_suspicion"] == 0.0
    assert debug["severity_traces"]["recall_failure"]["bad_item_suspicion_mitigation"] == 0.0


def test_facet_aliases_are_canonicalized_before_recall_updates(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.facets_path,
        {
            "schema_version": 1,
            "facets": [
                {
                    "id": "recall",
                    "title": "Recall",
                    "aliases": ["svd-recall"],
                    "description": None,
                    "tags": [],
                }
            ],
        },
    )
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["svd-recall"]
    item["evidence_weights"] = {"svd-recall": 1.0}
    item["criterion_facet_weights"] = {"correctness": {"svd-recall": 1.0}}
    item["repair_targets"] = ["svd-recall"]
    write_yaml(item_path, item)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    loaded_item = vault.practice_items["pi_svd_define_001"]
    assert loaded_item.evidence_facets == ["recall"]
    assert loaded_item.evidence_weights == {"recall": 1.0}
    assert loaded_item.criterion_facet_weights == {"correctness": {"recall": 1.0}}
    assert loaded_item.repair_targets == ["recall"]

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    assert repository.facet_recall_state("lo_svd_definition", "recall") is not None
    assert repository.facet_recall_state("lo_svd_definition", "svd-recall") is None
    assert repository.fetch_practice_attempt(result.attempt_id)["evidence_facets"] == ["recall"]


def test_intervention_needs_canonicalize_target_facets_for_dedup(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.facets_path,
        {
            "schema_version": 1,
            "facets": [
                {
                    "id": "recall",
                    "title": "Recall",
                    "aliases": ["svd-recall"],
                    "description": None,
                    "tags": [],
                }
            ],
        },
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    first = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    second = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_svd_define_001", "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    first_decision = evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=first.attempt_id,
        learning_object_id=first.learning_object_id,
        practice_item_id=first.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=0.0,
        grader_confidence=1.0,
        error_event_written=True,
        max_error_severity=1.0,
        repeated_same_item_failure=True,
        repeated_same_facet_failure=False,
        target_facets=["svd-recall"],
        lo_independent_evidence_mass=2.0,
        clock=FrozenClock(NOW),
    )
    second_decision = evaluate_intervention_followup(
        vault,
        repository,
        attempt_id=second.attempt_id,
        learning_object_id=second.learning_object_id,
        practice_item_id=second.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=0.0,
        grader_confidence=1.0,
        error_event_written=True,
        max_error_severity=1.0,
        repeated_same_item_failure=True,
        repeated_same_facet_failure=False,
        target_facets=["recall"],
        lo_independent_evidence_mass=2.0,
        clock=FrozenClock(NOW),
    )

    assert first_decision.need_id == second_decision.need_id
    needs = repository.pending_intervention_needs("lo_svd_definition")
    assert len(needs) == 1
    assert needs[0]["target_facets"] == ["recall"]


def test_facet_recall_alias_merge_sums_beta_state(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        for row in [
            ("agg_canonical", "lo_svd_definition", "recall", None, 2.0, 3.0, 1.5, 2.0, "2026-05-18T12:00:00Z", "2026-05-18T12:00:00Z", 1),
            ("agg_alias", "lo_svd_definition", "svd-recall", None, 4.0, 5.0, 2.5, 3.0, "2026-05-19T12:00:00Z", "2026-05-19T12:00:00Z", 2),
            ("item_canonical", "lo_svd_definition", "recall", "pi_svd_define_001", 1.0, 2.0, 1.0, 1.0, "2026-05-18T12:00:00Z", None, 0),
            ("item_alias", "lo_svd_definition", "svd-recall", "pi_svd_define_001", 3.0, 4.0, 2.0, 2.0, "2026-05-19T12:00:00Z", "2026-05-19T12:00:00Z", 3),
        ]:
            alpha, beta = row[4], row[5]
            mean = alpha / (alpha + beta)
            variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
            connection.execute(
                """
                INSERT INTO evidence_facet_recall_state(
                  id, learning_object_id, facet_id, practice_item_id,
                  recall_alpha, recall_beta, recall_mean, recall_variance,
                  independent_evidence_mass, raw_coverage_mass, last_attempt_at,
                  last_error_at, consecutive_failures, algorithm_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    alpha,
                    beta,
                    mean,
                    variance,
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    "mvp-0.1",
                    "2026-05-17T12:00:00Z",
                    "2026-05-19T12:00:00Z",
                ),
            )
        connection.commit()

    merged = repository.merge_facet_recall_aliases(
        {"svd-recall": "recall"},
        algorithm_version="mvp-0.1",
        clock=FrozenClock(NOW),
    )

    assert merged == 2
    aggregate = repository.facet_recall_state("lo_svd_definition", "recall")
    item = repository.facet_recall_state("lo_svd_definition", "recall", "pi_svd_define_001")
    assert repository.facet_recall_state("lo_svd_definition", "svd-recall") is None
    assert repository.facet_recall_state("lo_svd_definition", "svd-recall", "pi_svd_define_001") is None
    assert aggregate is not None
    assert aggregate.recall_alpha == 6.0
    assert aggregate.recall_beta == 8.0
    assert aggregate.independent_evidence_mass == 4.0
    assert aggregate.raw_coverage_mass == 5.0
    assert aggregate.consecutive_failures == 2
    assert aggregate.last_attempt_at == "2026-05-19T12:00:00Z"
    assert item is not None
    assert item.recall_alpha == 4.0
    assert item.recall_beta == 6.0
    assert item.independent_evidence_mass == 3.0
    assert item.raw_coverage_mass == 3.0
    assert item.consecutive_failures == 3


def _set_hint_coverage_dampening(paths: VaultPaths, mapping: dict[str, float]) -> None:
    path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    data = read_yaml(path)
    data["hint_policy"]["coverage_surface_dampening_by_hint"] = mapping
    write_yaml(path, data)
