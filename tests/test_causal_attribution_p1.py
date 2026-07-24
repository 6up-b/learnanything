from __future__ import annotations

import json
import sqlite3

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.causal_attribution import (
    SympyVerifierAdapter,
    TestExecutionVerifierAdapter,
    causal_episode_for_attempt,
    claim_checked_feedback,
    materialize_causal_episode,
    mint_causal_mechanism_taxonomy,
    record_causal_diagnosis_contest,
    select_minimal_repair,
    validate_repair_candidate,
)
from learnloop.services.replay import replay_learning_object
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.serializers import attempt_detail

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _attempt(
    vault,
    repository,
    attempt_id: str,
    *,
    operation: str = "transpose_confusion",
    statement: str = "The learner may be treating Q and Q transpose as identical.",
    candidate_causes: list[dict] | None = None,
):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Q was used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement=statement,
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation=operation,
                        first_divergence={
                            "anchor_kind": "span",
                            "criterion_id": "correctness",
                            "quote": "Q",
                        },
                        model_reported_causal_confidence=0.65,
                        candidate_causes=candidate_causes
                        or [
                            {
                                "statement": statement,
                                "cause_scope": "learner_state",
                                "target_ref": {
                                    "kind": "facet_capability",
                                    "facet_id": "recall",
                                    "capability": "retrieval",
                                },
                            }
                        ],
                        postdictive_claims=[
                            {
                                "criterion_id": "correctness",
                                "must": "not_full_credit",
                            }
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "insert_transpose",
                        "rationale": "Preserve the factorization and repair only the transpose.",
                        "target_refs": [
                            {
                                "kind": "facet_capability",
                                "facet_id": "recall",
                                "capability": "retrieval",
                            }
                        ],
                        "expected_minutes": 2.0,
                        "answer_reveal_budget": 0.5,
                        "repaired_trace": {
                            "learner_work_prefix": "U Sigma ",
                            "repair_insertion_point": {
                                "anchor_kind": "span",
                                "criterion_id": "correctness",
                                "quote": "Q",
                            },
                            "minimal_edit": "replace Q with Q^T",
                            "regenerated_work": "",
                            "repaired_answer_md": "U Sigma Q^T",
                            "changed_latent_claims": [
                                "the right singular-vector factor is transposed"
                            ],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            ),
        ),
        clock=FrozenClock(NOW),
    )


def test_attempt_materializes_append_only_hypothesis_and_receipt(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    result = _attempt(vault, repository, "att_p1")
    episode = causal_episode_for_attempt(repository, result.attempt_id)

    assert episode is not None
    assert len(episode["hypotheses"]) == 1
    hypothesis = episode["hypotheses"][0]
    assert hypothesis["cause_scope"] == "learner_state"
    assert hypothesis["mechanism"] is None  # one operation has not earned a taxonomy
    receipt = episode["receipt"]
    assert receipt["permitted_uses"] == [
        "learner_feedback",
        "routing",
        "probe_selection",
    ]
    assert "posterior" not in receipt
    assert receipt["repair_selection"]["selected"]["repair_class"]["operator"] == (
        "insert_transpose"
    )
    assert receipt["repair_selection"]["selected"]["minimality"][
        "latent_change_cost"
    ] == 1
    assert receipt["support_authority"] == "unavailable_single_attempt"
    assert receipt["support_scores"][hypothesis["id"]] is None
    assert receipt["model_reported_support_proposals"][
        hypothesis["id"]
    ] == 0.65

    before = repository.causal_hypotheses_for_attempt(
        result.attempt_id, latest_only=False
    )
    materialize_causal_episode(
        vault,
        repository,
        attempt_id=result.attempt_id,
        repair_suggestions=result.repair_suggestions,
        clock=FrozenClock(NOW),
    )
    after = repository.causal_hypotheses_for_attempt(
        result.attempt_id, latest_only=False
    )
    assert [value["id"] for value in after] == [value["id"] for value in before]

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE causal_hypotheses SET statement = 'rewritten' WHERE id = ?",
                (hypothesis["id"],),
            )


def test_mechanism_taxonomy_is_earned_from_recurring_operations(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    first = _attempt(vault, repository, "att_operation_1")
    second = _attempt(
        vault,
        repository,
        "att_operation_2",
        statement="The learner may omit transpose markers on orthogonal factors.",
    )

    heads_before = repository.causal_hypotheses_with_operations()
    taxonomy = mint_causal_mechanism_taxonomy(
        repository, activate=True, clock=FrozenClock(NOW)
    )
    heads_after = repository.causal_hypotheses_with_operations()

    assert taxonomy["status"] == "active"
    assert taxonomy["taxonomy"]["clusters"][0]["id"] == (
        "operation:transpose_confusion"
    )
    assert len(taxonomy["assignments"]) == 2
    assert heads_after == heads_before
    assert all(value["version"] == 1 for value in heads_after)

    materialize_causal_episode(
        vault,
        repository,
        attempt_id=second.attempt_id,
        repair_suggestions=second.repair_suggestions,
        clock=FrozenClock(NOW),
    )
    episode = causal_episode_for_attempt(repository, second.attempt_id)
    assert episode is not None
    assert episode["receipt"]["mechanism_taxonomy_version_id"] == taxonomy["id"]
    assert episode["hypotheses"][0]["mechanism"] == (
        "operation:transpose_confusion"
    )
    assert repository.causal_hypotheses_for_attempt(
        second.attempt_id, latest_only=False
    ) == [
        value
        for value in heads_before
        if value["attempt_id"] == second.attempt_id
    ]


def test_candidate_reordering_does_not_change_episode_identity(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    causes = [
        {
            "statement": "The learner may confuse Q with Q transpose.",
            "cause_scope": "learner_state",
            "target_ref": {
                "kind": "facet_capability",
                "facet_id": "recall",
                "capability": "retrieval",
            },
        },
        {
            "statement": "The notation may have obscured the transpose.",
            "cause_scope": "interaction_context",
            "target_ref": {
                "kind": "answer_span",
                "quote": "Q",
            },
        },
    ]
    result = _attempt(
        vault,
        repository,
        "att_candidate_reorder",
        candidate_causes=causes,
    )
    before = repository.causal_hypotheses_for_attempt(
        result.attempt_id, latest_only=False
    )
    event = repository.error_events_for_attempt(result.attempt_id)[0]
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT repair_plan_json FROM error_events WHERE id = ?",
            (event["id"],),
        ).fetchone()
        plan = json.loads(row["repair_plan_json"])
        plan["candidate_causes"] = list(
            reversed(plan["candidate_causes"])
        )
        connection.execute(
            "UPDATE error_events SET repair_plan_json = ? WHERE id = ?",
            (json.dumps(plan, sort_keys=True), event["id"]),
        )
        connection.commit()

    materialize_causal_episode(
        vault,
        repository,
        attempt_id=result.attempt_id,
        repair_suggestions=result.repair_suggestions,
        clock=FrozenClock(NOW),
    )
    after = repository.causal_hypotheses_for_attempt(
        result.attempt_id, latest_only=False
    )

    assert [value["episode_key"] for value in after] == [
        value["episode_key"] for value in before
    ]
    assert [value["version"] for value in after] == [1, 1]


def test_common_repair_cover_requires_explicit_target_match(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _attempt(
        vault,
        repository,
        "att_no_false_cover",
        candidate_causes=[
            {
                "statement": "The learner may confuse the transpose.",
                "cause_scope": "learner_state",
                "target_ref": {
                    "kind": "facet_capability",
                    "facet_id": "recall",
                    "capability": "retrieval",
                },
            },
            {
                "statement": "The prompt notation may be unclear.",
                "cause_scope": "item_contract",
                "target_ref": {
                    "kind": "answer_span",
                    "quote": "Q",
                },
            },
        ],
    )

    episode = causal_episode_for_attempt(repository, result.attempt_id)
    assert episode is not None
    cover = episode["receipt"]["common_repair_cover"]
    assert cover["covers_plausible_set"] is False
    assert [value["covered"] for value in cover["matrix"]] == [
        True,
        False,
    ]


def test_structural_selector_rejects_repairs_that_damage_a_passed_target():
    safe = {
        "practice_mode": "repair",
        "operator": "repair_failed_step",
        "target_refs": [{"kind": "criterion", "criterion_id": "failed"}],
        "expected_minutes": 3,
        "repaired_trace": {
            "learner_work_prefix": "good work\n",
            "minimal_edit": "fix final line",
            "repaired_answer_md": "good work\nfixed",
            "changed_latent_claims": ["one"],
            "changed_checkpoint_ids": ["last"],
        },
    }
    unsafe = {
        "practice_mode": "repair",
        "operator": "reteach_everything",
        "target_refs": [{"kind": "criterion", "criterion_id": "passed"}],
        "expected_minutes": 1,
        "repaired_trace": {
            "learner_work_prefix": "",
            "minimal_edit": "replace all work",
            "repaired_answer_md": "replacement",
            "changed_latent_claims": [],
            "changed_checkpoint_ids": [],
        },
    }

    selected = select_minimal_repair(
        [unsafe, safe],
        protected_refs=[{"kind": "criterion", "criterion_id": "passed"}],
    )

    assert selected["selected"]["repair_class"]["operator"] == "repair_failed_step"
    assert any(
        "demonstrated_capability_not_preserved" in value["reasons"]
        for value in selected["rejected"]
    )


def test_structural_selector_rejects_incomplete_zero_cost_repair():
    incomplete = {
        "practice_mode": "repair",
        "operator": "mystery_fix",
        "target_refs": [{"kind": "criterion", "criterion_id": "failed"}],
        "expected_minutes": 1,
    }
    auditable = {
        "practice_mode": "repair",
        "operator": "local_fix",
        "target_refs": [{"kind": "criterion", "criterion_id": "failed"}],
        "expected_minutes": 2,
        "repaired_trace": {
            "minimal_edit": "replace one term",
            "repaired_answer_md": "2*x",
            "changed_latent_claims": ["coefficient"],
            "changed_checkpoint_ids": [],
        },
    }

    selected = select_minimal_repair([incomplete, auditable])

    assert selected["selected"]["repair_class"]["operator"] == "local_fix"
    assert any(
        "incomplete_trace_present" in value["reasons"]
        for value in selected["rejected"]
    )


def test_backend_validator_owns_symbolic_verification_verdict():
    suggestion = {
        "practice_mode": "repair",
        "operator": "combine_terms",
        "target_refs": [{"kind": "criterion", "criterion_id": "algebra"}],
        "repaired_trace": {
            "minimal_edit": "combine x + x",
            "repaired_answer_md": "x + x",
            "changed_latent_claims": ["coefficient"],
            "changed_checkpoint_ids": [],
        },
        "verification_request": {"kind": "symbolic_equality"},
        "verification_status": "contradicted",
        "invalid_rule": True,
    }

    validation = validate_repair_candidate(
        suggestion, expected_answer="2*x"
    )
    selected = select_minimal_repair(
        [suggestion], expected_answer="2*x"
    )

    assert validation.verification.status == "verified"
    assert selected["selected"] is not None
    assert selected["selected"]["suggestion"]["repair_validation"][
        "authority"
    ] == "learnloop_validator"
    assert "verification_status" not in selected["selected"]["suggestion"]


def test_verifier_adapters_preserve_typed_outcomes():
    math = SympyVerifierAdapter()
    assert math.verify("x + x", "2*x").status == "verified"
    assert math.verify("x + 1", "x + 2").status == "contradicted"
    assert math.verify("(", "x").status == "parse_failed"
    assert (
        math.verify(
            "sqrt(x**2)",
            "x",
            required_assumptions=("x_nonnegative",),
        ).status
        == "assumption_missing"
    )
    tests = TestExecutionVerifierAdapter()
    assert tests.verify(returncode=0, tests_collected=2).status == "verified"
    assert tests.verify(returncode=1, tests_collected=2).status == "contradicted"
    assert tests.verify(returncode=0, tests_collected=0).status == (
        "assumption_missing"
    )


def test_feedback_overlay_and_cli_are_receipt_checked(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _attempt(vault, repository, "att_causal_show")

    overlay = claim_checked_feedback(vault, repository, result.attempt_id)
    assert overlay is not None
    assert overlay["causal_hypotheses"][0]["label"] == (
        "Possible explanation — not yet confirmed"
    )
    assert overlay["demonstrated_criteria"] == []
    assert "slipped" in overlay["contest_action"]["reasons"]
    assert "notation_confused" in overlay["contest_action"]["reasons"]
    assert overlay["repaired_trace"] is None
    assert overlay["repaired_trace_withheld_reason"] == (
        "contamination_status_not_authorized"
    )
    assert overlay["contest_action"]["available"] is True
    assert overlay["contest_action"]["factor_id"] is None
    detail = attempt_detail(vault, repository, result.attempt_id)
    assert detail["causalEpisode"]["receipt"]["id"] == overlay["receipt_id"]
    assert (
        detail["feedback"]["causalFeedback"]["receiptId"]
        == overlay["receipt_id"]
    )
    assert detail["causalEpisode"]["hypotheses"][0]["causeScope"] == (
        "learner_state"
    )
    assert detail["causalEpisode"]["receipt"]["repairSelection"]["selected"][
        "repairClass"
    ]["operator"] == "insert_transpose"

    shown = CliRunner().invoke(
        app,
        [
            "show",
            result.attempt_id,
            "--causal",
            "--vault",
            str(paths.root),
        ],
    )
    assert shown.exit_code == 0, shown.output
    assert "causal episode" in shown.output
    assert "candidate causes" in shown.output
    assert "insert_transpose" in shown.output

    contested = record_causal_diagnosis_contest(
        vault,
        repository,
        attempt_id=result.attempt_id,
        response="diagnosis_wrong",
        clock=FrozenClock(NOW),
    )
    assert contested["response"] == "diagnosis_wrong"
    assert contested["factor_id"]
    assert claim_checked_feedback(vault, repository, result.attempt_id)[
        "contest_action"
    ]["available"] is False


def test_feedback_overlay_fails_closed_without_learner_permission(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _attempt(vault, repository, "att_feedback_not_permitted")
    payload = repository.attempt_debug_payload(result.attempt_id)
    assert payload is not None
    payload["causal_attribution"]["diagnosis_receipt"][
        "permitted_uses"
    ] = ["routing"]
    with repository.connection() as connection:
        connection.execute(
            """
            UPDATE attempt_debug_payloads SET payload_json = ?
             WHERE attempt_id = ?
            """,
            (json.dumps(payload, sort_keys=True), result.attempt_id),
        )
        connection.commit()

    assert claim_checked_feedback(
        vault, repository, result.attempt_id
    ) is None


def test_new_candidate_surface_is_projection_not_duplicate_table(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _attempt(vault, repository, "att_candidate_projection")

    candidates = repository.misconception_candidates_for_learning_object(
        "lo_svd_definition"
    )
    assert len(candidates) == 1
    assert candidates[0]["projection"] == "causal_hypotheses"
    with repository.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM misconception_candidates"
        ).fetchone()[0]
    assert count == 0


def test_projected_candidate_rejects_unsupported_legacy_mutation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _attempt(vault, repository, "att_candidate_read_only")
    candidate = repository.misconception_candidates_for_learning_object(
        "lo_svd_definition"
    )[0]

    with pytest.raises(
        ValueError, match="projected causal candidates are read-only"
    ):
        repository.update_misconception_candidate(
            candidate["id"], severity=0.9
        )


def test_replay_preserves_immutable_receipt_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _attempt(vault, repository, "att_receipt_replay")
    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source="self",
        feedback_md=result.feedback_md,
        repair_suggestions=result.repair_suggestions,
        clock=FrozenClock(NOW),
    )
    before = repository.attempt_debug_payload(result.attempt_id)[
        "causal_attribution"
    ]

    replay_learning_object(
        vault,
        repository,
        "lo_svd_definition",
    )

    after = repository.attempt_debug_payload(result.attempt_id)[
        "causal_attribution"
    ]
    assert [value["id"] for value in after["diagnosis_receipts"]] == [
        value["id"] for value in before["diagnosis_receipts"]
    ]
    assert after["diagnosis_receipt"]["id"] == before["diagnosis_receipt"]["id"]


def test_reusing_receipt_persists_it_as_current_without_duplicate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _attempt(vault, repository, "att_receipt_repoint")
    attribution = repository.attempt_debug_payload(result.attempt_id)[
        "causal_attribution"
    ]
    original = dict(attribution["diagnosis_receipt"])
    alternate = {**original, "id": "dr_alternate"}
    repository.append_attempt_diagnosis_receipt(
        result.attempt_id, alternate
    )

    repository.append_attempt_diagnosis_receipt(
        result.attempt_id, original
    )

    after = repository.attempt_debug_payload(result.attempt_id)[
        "causal_attribution"
    ]
    assert after["diagnosis_receipt"]["id"] == original["id"]
    assert [receipt["id"] for receipt in after["diagnosis_receipts"]] == [
        original["id"],
        alternate["id"],
    ]
