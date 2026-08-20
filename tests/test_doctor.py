from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.ops.doctor import run_doctor
from learnloop.diagnosis.error_taxonomy_map import MECHANISM_TAXONOMY_CARD_JSON
from learnloop.content.proposals.proposals import persist_authoring_proposal
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
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
    assert report.deprecated_table_row_counts == {
        "learner_theta": 0,
        "source_exam_profiles": 0,
        "source_locator_schemes": 0,
    }
    assert report.as_dict()["deprecated_table_row_counts"] == (
        report.deprecated_table_row_counts
    )


def test_doctor_escalates_nonempty_deprecated_tables_without_mutating_them(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO source_exam_profiles(
              id, scope_kind, scope_id, profile_hash, profile_json, created_at
            ) VALUES ('profile', 'source_set', 'set', 'hash', '{}', ?)
            """,
            (NOW_ISO,),
        )
        connection.execute(
            """
            INSERT INTO source_locator_schemes(locator, scheme, detected_at)
            VALUES ('page:1', 'page', ?)
            """,
            (NOW_ISO,),
        )
        connection.execute(
            """
            INSERT INTO learner_theta(
              id, domain, evidence_family, practice_mode, theta_mean,
              theta_variance, algorithm_version, updated_at
            ) VALUES ('theta', 'linear-algebra', 'recall', NULL, 0.0, 1.0, 'mvp-0.6', ?)
            """,
            (NOW_ISO,),
        )

    report = run_doctor(vault_root)

    assert report.deprecated_table_row_counts == {
        "learner_theta": 1,
        "source_exam_profiles": 1,
        "source_locator_schemes": 1,
    }
    deprecated = [
        issue
        for issue in report.issues
        if issue.code == "sqlite:deprecated_table_not_empty"
    ]
    assert {issue.entity_id for issue in deprecated} == {
        "learner_theta",
        "source_exam_profiles",
        "source_locator_schemes",
    }
    assert all(issue.severity == "warning" for issue in deprecated)
    assert all(issue.details["action"] == "stop_and_escalate" for issue in deprecated)
    with repository.connection() as connection:
        assert {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in report.deprecated_table_row_counts
        } == report.deprecated_table_row_counts


def test_doctor_warns_for_legacy_codex_and_retired_settings(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    with (vault_root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write(
            """

[codex]
provider = "sdk"
auth_mode = "chatgpt"

[forecasts]
default_horizon_days = 99

[probe.episode]
self_graded_evidence_weight = 0.99

[probe.dialogue]
max_turns = 8

[recall_coverage]
facet_recall_prior_pseudo_count = 99
coverage_epsilon = 0.5

[ingest.audio]
provider = "openrouter"
transcription_model = "vendor/audio-model"
timeout_seconds = 412

[ingest.budgets]
evidence_span_input_tokens = 1
"""
        )

    report = run_doctor(vault_root)

    codes = [issue.code for issue in report.issues]
    assert "config:legacy_codex_translated" in codes
    assert "config:legacy_audio_transcription_translated" in codes
    assert "config:retired_auth_mode" in codes
    settings = {
        issue.details["setting"]
        for issue in report.issues
        if issue.code == "config:retired_setting"
    }
    assert settings == {
        "forecasts",
        "probe.episode.self_graded_evidence_weight",
        "probe.dialogue.max_turns",
        "recall_coverage.facet_recall_prior_pseudo_count",
        "recall_coverage.coverage_epsilon",
        "ingest.budgets.evidence_span_input_tokens",
    }
    assert paths.config_path.read_text(encoding="utf-8").count("auth_mode") == 1
    translated = next(
        issue
        for issue in report.issues
        if issue.code == "config:legacy_audio_transcription_translated"
    )
    assert translated.details == {
        "from": "ingest.audio.provider",
        "to": "ai.providers.openrouter_transcription",
        "route": "ai.routing.transcription",
        "action": "rewrite_config",
    }


def test_plain_doctor_reports_pre_044_migrations_without_touching_database(tmp_path):
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "conic-sections"
    vault_root = tmp_path / "conic-sections"
    shutil.copytree(fixture_root, vault_root)
    sqlite_path = vault_root / "state.sqlite"
    before = hashlib.sha256(sqlite_path.read_bytes()).digest()
    with sqlite3.connect(sqlite_path) as connection:
        assert connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0] < 44

    report = run_doctor(vault_root)

    assert "sqlite:migrations_missing" in {issue.code for issue in report.issues}
    assert hashlib.sha256(sqlite_path.read_bytes()).digest() == before
    with sqlite3.connect(sqlite_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'apply_intents'"
        ).fetchone() is None


def test_plain_doctor_does_not_create_a_missing_database(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    paths.sqlite_path.unlink()

    report = run_doctor(vault_root)

    assert "sqlite:missing" in {issue.code for issue in report.issues}
    assert not paths.sqlite_path.exists()


def test_plain_doctor_reports_an_unreadable_database_without_rewriting_it(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    broken = b"not a sqlite database"
    paths.sqlite_path.write_bytes(broken)

    report = run_doctor(vault_root)

    assert "sqlite:unreadable" in {issue.code for issue in report.issues}
    assert paths.sqlite_path.read_bytes() == broken


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


def test_doctor_resolves_legacy_error_event_through_causal_taxonomy(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    error_types = read_yaml(paths.error_types_path)
    error_types["error_types"].extend(
        {
            "id": card["id"],
            "title": card["title"],
            "description": card["use_when"],
            "related_concepts": [],
            "severity_default": card["severity_default"],
            "is_misconception": card["is_misconception"],
            "tags": ["canonical_mechanism"],
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
        for card in MECHANISM_TAXONOMY_CARD_JSON
    )
    write_yaml(paths.error_types_path, error_types)
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_legacy_conceptual_slip",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    report = run_doctor(vault_root, fix_state=True)

    assert not [
        issue
        for issue in report.issues
        if issue.code == "errors:unaligned_error_type"
        and issue.entity_id == "err_legacy_conceptual_slip"
    ]


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


def test_doctor_does_not_merge_unrelated_equal_length_facet_ids(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    practice_item_path = paths.practice_item_path(
        "linear-algebra", "pi_svd_define_001"
    )
    item = read_yaml(practice_item_path)
    item["evidence_facets"] = ["clarity", "scaling"]
    item["evidence_weights"] = {"clarity": 0.5, "scaling": 0.5}
    write_yaml(practice_item_path, item)

    report = run_doctor(vault_root, fix_state=True)

    assert not [
        issue
        for issue in report.issues
        if issue.code.startswith("evidence_facet:merge_candidate")
    ]


def test_doctor_does_not_merge_opposite_registered_facet_contracts(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    facets = read_yaml(paths.facets_path)
    facets["facets"].extend(
        [
            {
                "id": "embedding_direction",
                "kind": "definition",
                "claim": "The embedding maps a token id into model space.",
                "aliases": [],
                "status": "proposed",
                "version": 1,
                "provenance": {"origin": "manual", "source_refs": []},
            },
            {
                "id": "unembedding_direction",
                "kind": "definition",
                "claim": "The output map projects model space into vocabulary logits.",
                "aliases": [],
                "status": "proposed",
                "version": 1,
                "provenance": {"origin": "manual", "source_refs": []},
            },
        ]
    )
    write_yaml(paths.facets_path, facets)
    practice_item_path = paths.practice_item_path(
        "linear-algebra", "pi_svd_define_001"
    )
    item = read_yaml(practice_item_path)
    item["evidence_facets"] = [
        "embedding_direction",
        "unembedding_direction",
    ]
    item["evidence_weights"] = {
        "embedding_direction": 0.5,
        "unembedding_direction": 0.5,
    }
    write_yaml(practice_item_path, item)

    report = run_doctor(vault_root, fix_state=True)

    assert not [
        issue
        for issue in report.issues
        if issue.code.startswith("evidence_facet:merge_candidate")
    ]


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
