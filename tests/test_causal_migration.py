from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_migration import migrate_legacy_causal_basis

from tests.helpers import NOW_ISO, create_basic_vault


def test_migrate_legacy_causal_basis_appends_canonical_version(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_legacy",
            "attempt_id": None,
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.8,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    original = repository.append_causal_hypothesis(
        episode_key="legacy:err_legacy",
        attempt_id="attempt_legacy",
        error_event_id="err_legacy",
        learning_object_id="lo_svd_definition",
        cause_scope="learner_state",
        statement="Believes SVD has no right singular-vector factor.",
        statement_normalized="believes svd has no right singular-vector factor.",
        evidence={"error_type": "conceptual_slip"},
        status="candidate",
    )

    report = migrate_legacy_causal_basis(repository)
    migrated = repository.latest_causal_hypothesis_for_episode(
        "legacy:err_legacy"
    )

    assert report.migrated == 1
    assert migrated is not None
    assert migrated["version"] == 2
    assert migrated["supersedes_id"] == original["id"]
    assert migrated["mechanism"] == "conceptual_schema_error"
    assert migrated["evidence"]["error_type"] == "conceptual_slip"
    assert migrate_legacy_causal_basis(repository).already_canonical == 1


def test_migrate_legacy_causal_basis_leaves_unknown_detector_unresolved(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    original = repository.append_causal_hypothesis(
        episode_key="legacy:fatal_signature",
        attempt_id="attempt_legacy",
        learning_object_id="lo_svd_definition",
        cause_scope="unknown",
        statement="The response omitted a required output.",
        statement_normalized="the response omitted a required output.",
        evidence={"error_type": "fatal_missing_output"},
        status="open_set",
    )

    report = migrate_legacy_causal_basis(repository)

    assert report.migrated == 0
    assert report.unresolved_hypothesis_ids == (original["id"],)
    assert repository.latest_causal_hypothesis_for_episode(
        "legacy:fatal_signature"
    )["version"] == 1
