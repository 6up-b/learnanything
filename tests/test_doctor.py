from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.doctor import run_doctor
from learnloop.services.proposals import persist_authoring_proposal
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import init_vault
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def test_doctor_clean_fresh_vault(tmp_path):
    vault_root = tmp_path / "vault"
    init_vault(vault_root)

    report = run_doctor(vault_root)

    assert report.clean is True
    assert report.error_count == 0
    assert report.warning_count == 0


def test_doctor_reports_and_fixes_missing_derived_state(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    report = run_doctor(vault_root)

    assert {issue.code for issue in report.issues} == {
        "sql:missing_learning_object_mastery",
        "sql:missing_practice_item_state",
    }

    fixed = run_doctor(vault_root, fix_state=True)

    assert fixed.clean is True
    assert fixed.state_sync is not None
    assert fixed.state_sync.practice_item_states_created == 1
    assert fixed.state_sync.mastery_states_created == 1


def test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=clock,
    )

    report = run_doctor(vault_root)

    assert "sql:derived_state_rebuild_stale" in {issue.code for issue in report.issues}

    rebuild_derived_state(vault, repository, clock=clock)
    rebuilt_report = run_doctor(vault_root)

    assert "sql:derived_state_rebuild_stale" not in {issue.code for issue in rebuilt_report.issues}


def test_doctor_reports_reference_issues_and_json_cli(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.relations_path,
        {
            "schema_version": 1,
            "edges": [
                {
                    "id": "edge_missing",
                    "relation_type": "related",
                    "source": "singular_value_decomposition",
                    "target": "missing_concept",
                    "strength": 1.0,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    runner = CliRunner()

    result = runner.invoke(app, ["doctor", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = {issue["code"] for issue in payload["issues"]}
    assert "concept_edge:missing_target" in codes
    assert "sql:missing_practice_item_state" in codes
    assert payload["clean"] is False

    fixed = runner.invoke(app, ["doctor", "--vault", str(vault_root), "--fix-state", "--json"])

    assert fixed.exit_code == 1
    fixed_payload = json.loads(fixed.output)
    fixed_codes = {issue["code"] for issue in fixed_payload["issues"]}
    assert "sql:missing_practice_item_state" not in fixed_codes
    assert "concept_edge:missing_target" in fixed_codes
    assert fixed_payload["state_sync"]["practice_item_states_created"] == 1


def test_doctor_warns_on_unknown_yaml_key_that_looks_like_typo(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    practice_item = read_yaml(practice_item_path)
    practice_item["promtp"] = "typo"
    write_yaml(practice_item_path, practice_item)

    report = run_doctor(vault_root, fix_state=True)

    typo_issues = [issue for issue in report.issues if issue.code == "yaml:unknown_key_typo"]
    assert len(typo_issues) == 1
    assert "promtp" in typo_issues[0].message
    assert "prompt" in typo_issues[0].message


def test_doctor_warns_on_unaligned_error_event_type(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_unknown_taxonomy",
            "learning_object_id": "lo_svd_definition",
            "error_type": "unknown_taxonomy_entry",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    report = run_doctor(vault_root, fix_state=True)

    assert "errors:unaligned_error_type" in {issue.code for issue in report.issues}


def test_doctor_flags_bad_item_suspicion_after_evidence_gate(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_item_quality_state(
              practice_item_id, bad_item_suspicion, evidence_count,
              suspicion_reasons_json, last_flagged_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("pi_svd_define_001", 0.70, 3, "[]", None, "mvp-0.1", NOW_ISO),
        )
        connection.commit()

    report = run_doctor(vault_root, fix_state=True)

    assert "practice_item:bad_item_suspicion" in {issue.code for issue in report.issues}


def test_doctor_validates_criterion_facet_maps(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(practice_item_path)
    item["evidence_facets"] = ["recall", "formula"]
    item["evidence_weights"] = {"recall": 0.5, "formula": 0.5}
    item["criterion_facet_weights"] = {
        "correctness": {"recall": 2.0},
        "unknown_criterion": {"formula": 1.0},
    }
    write_yaml(practice_item_path, item)

    report = run_doctor(vault_root, fix_state=True)
    codes = {issue.code for issue in report.issues}

    assert "practice_item:criterion_facet_map:auto_normalizable" in codes
    assert "practice_item:criterion_facet_map:blocking" in codes
    assert "practice_item:criterion_facet_map:needs_author_review" in codes
    auto_issue = next(issue for issue in report.issues if issue.code == "practice_item:criterion_facet_map:auto_normalizable")
    assert auto_issue.details == {
        "practice_item_id": "pi_svd_define_001",
        "criterion_id": "correctness",
        "current_sum": 2.0,
        "proposed_criterion_facet_weights": {"correctness": {"recall": 1.0}},
    }
    assert auto_issue.as_dict()["details"] == auto_issue.details


def test_doctor_surfaces_likely_facet_merge_candidates(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(practice_item_path)
    item["evidence_facets"] = ["frobenius-error", "frobenius-error-formula"]
    item["evidence_weights"] = {"frobenius-error": 0.5, "frobenius-error-formula": 0.5}
    write_yaml(practice_item_path, item)

    report = run_doctor(vault_root, fix_state=True)

    issue = next(issue for issue in report.issues if issue.code == "evidence_facet:merge_candidate:auto_propose")
    assert issue.details["canonical_facet_id"] == "frobenius-error"
    assert issue.details["alias_facet_id"] == "frobenius-error-formula"
    assert issue.details["suggested_facets_yaml_alias"] == {
        "id": "frobenius-error",
        "aliases": ["frobenius-error-formula"],
    }


def test_doctor_warns_on_duplicate_diagnostic_practice_proposals(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(
        {
            "summary": "Duplicate diagnostic probes",
            "source_refs": [{"ref_type": "existing_entity", "ref_id": "lo_svd_definition"}],
            "items": [
                _diagnostic_item_payload("diag_a", "pi_diag_a"),
                _diagnostic_item_payload("diag_b", "pi_diag_b"),
            ],
        }
    )
    persist_authoring_proposal(vault_root, proposal, provider="import", clock=FrozenClock(NOW))

    report = run_doctor(vault_root, fix_state=True)

    issue = next(issue for issue in report.issues if issue.code == "proposal:duplicate_diagnostic_practice:needs_review")
    assert issue.entity_id == "lo_svd_definition"
    assert issue.details["target_facets"] == ["recall"]
    assert len(issue.details["proposal_item_ids"]) == 2
    assert issue.details["proposed_practice_item_ids"] == ["pi_diag_a", "pi_diag_b"]


def test_doctor_warns_on_duplicate_learning_objects(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    original = read_yaml(paths.learning_object_path("linear-algebra", "lo_svd_definition"))
    duplicate = dict(original)
    duplicate["id"] = "lo_svd_definition_copy"
    duplicate["title"] = "SVD definition copy"
    write_yaml(paths.learning_object_path("linear-algebra", "lo_svd_definition_copy"), duplicate)

    report = run_doctor(vault_root, fix_state=True)

    issue = next(issue for issue in report.issues if issue.code == "learning_object:merge_candidate:needs_review")
    assert issue.details["canonical_learning_object_id"] == "lo_svd_definition"
    assert issue.details["duplicate_learning_object_id"] == "lo_svd_definition_copy"
    assert issue.details["shared_concept"] == "singular_value_decomposition"


def test_doctor_fix_state_merges_registered_facet_alias_state(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
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
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        for facet_id, alpha, beta in [("recall", 2.0, 3.0), ("svd-recall", 4.0, 5.0)]:
            connection.execute(
                """
                INSERT INTO evidence_facet_recall_state(
                  id, learning_object_id, facet_id, practice_item_id,
                  recall_alpha, recall_beta, recall_mean, recall_variance,
                  independent_evidence_mass, raw_coverage_mass, last_attempt_at,
                  last_error_at, consecutive_failures, algorithm_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"state_{facet_id}",
                    "lo_svd_definition",
                    facet_id,
                    alpha,
                    beta,
                    alpha / (alpha + beta),
                    alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0)),
                    1.0,
                    1.0,
                    NOW_ISO,
                    NOW_ISO,
                    1,
                    "mvp-0.1",
                    NOW_ISO,
                    NOW_ISO,
                ),
            )
        connection.commit()

    run_doctor(vault_root, fix_state=True)

    merged = repository.facet_recall_state("lo_svd_definition", "recall")
    assert merged is not None
    assert merged.recall_alpha == 6.0
    assert merged.recall_beta == 8.0
    assert repository.facet_recall_state("lo_svd_definition", "svd-recall") is None


def _diagnostic_item_payload(client_item_id: str, proposed_entity_id: str) -> dict:
    return {
        "client_item_id": client_item_id,
        "item_type": "practice_item",
        "operation": "create",
        "proposed_entity_id": proposed_entity_id,
        "source_ref_ids": ["lo_svd_definition"],
        "rationale": "Diagnostic recall probe.",
        "review_route": "review_required",
        "payload": {
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe", "open_text", "dont_know"],
            "prompt": f"Diagnostic prompt for {proposed_entity_id}.",
            "expected_answer": "U, Sigma, V transpose.",
            "difficulty": 0.5,
            "difficulty_source": "llm_estimate",
            "retrieval_demand": 0.85,
            "transfer_distance": 0.15,
            "scaffold_level": 0.2,
            "surface_family": "svd_definition_diagnostic",
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "repair_targets": ["recall"],
            "criterion_facet_weights": {"c_recall": {"recall": 1.0}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "c_recall", "points": 4, "description": "Recalls the requested fact."}],
                "fatal_errors": [],
            },
        },
    }
