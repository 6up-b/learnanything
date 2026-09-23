from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.outcome_contract import COLLECTION_VERSION, retention_exclusions
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.data_quality import data_quality_report
from learnloop.substrate.dataset import export_dataset, split_assignments
from learnloop.substrate.dataset import outcome_records
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault, seed_due_item


def test_exact_offer_survives_refresh_recovery_and_dataset_export(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    clock = FrozenClock(NOW)
    session = repository.create_session(clock=clock)
    first = build_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))[0]
    repository.finalize_scheduler_offer(first.scheduler_slate_id, [first.scheduler_candidate_id])
    repository.bind_submission_offer(submission_id="stable", session_id=session, practice_item_id=first.practice_item_id, scheduler_candidate_id=first.scheduler_candidate_id)
    later = build_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))[0]
    restored = repository.bind_submission_offer(submission_id="stable", session_id=session, practice_item_id=first.practice_item_id, scheduler_candidate_id=None)
    assert restored == first.scheduler_candidate_id != later.scheduler_candidate_id
    result = complete_self_graded_attempt(vault, repository, AttemptDraft(practice_item_id=first.practice_item_id, learner_answer_md="A factorization", session_id=session, submission_id="stable", scheduler_candidate_id=restored, entry_surface="desktop_practice", evidence_origin="human"), SelfGradeInput(criterion_points={"correctness": 4}, confidence=3), clock=clock)
    run_post_attempt_pipeline(vault, repository, result=result, session_id=session, clock=clock)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["scheduler_candidate_id"] == first.scheduler_candidate_id
    assert repository.scheduler_slate_candidates(later.scheduler_slate_id)[0]["chosen_attempt_id"] is None
    features = repository.decision_features(decision_id=first.scheduler_candidate_id, decision_type="selection")
    assert features is not None
    repository.record_decision_features(decision_id=first.scheduler_candidate_id, decision_type="selection", ability_vector={"changed_after_action": True}, algorithm_version="new")
    assert repository.decision_features(decision_id=first.scheduler_candidate_id, decision_type="selection") == features
    with repository.connection() as connection, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM decision_features WHERE decision_id=?", (first.scheduler_candidate_id,))
    with pytest.raises(ValueError, match="evidence"):
        repository.record_false_remediation(attempt_id=result.attempt_id, value=True, evidence_refs=[], author_kind="human", verifier_version="test-v1")
    adjudication = repository.record_false_remediation(attempt_id=result.attempt_id, value=False, evidence_refs=[{"table": "practice_attempts", "id": result.attempt_id}], author_kind="human", verifier_version="test-v1")
    report = data_quality_report(paths.sqlite_path)
    assert report["attempt_cohorts"][0]["exact_offer_links"] == 1
    assert not any(report["current_version_violations"].values())
    output = tmp_path / "dataset"
    manifest = export_dataset(paths.sqlite_path, output)
    assert manifest["snapshot_sha256"] == hashlib.sha256((output / "snapshot.sqlite").read_bytes()).hexdigest()
    assert manifest["schema_migrations"][-1]["version"] >= 162
    labels = [json.loads(line) for line in (output / "outcome_contract.jsonl").read_text().splitlines()]
    assert labels[0]["R_next"]["status"] == "pending"
    assert labels[0]["R_cold"][0]["status"] == "unavailable"
    assert labels[0]["F"]["adjudication_id"] == adjudication
    assert labels[0]["F"]["author_kind"] == "human"
    assert manifest["inclusion"]["projection_tables_are_training_inputs"] is False


def test_final_offer_refuses_filtered_and_cross_session_candidates(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    session = repository.create_session(clock=FrozenClock(NOW))
    item = build_due_queue(vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id=session))[0]
    repository.finalize_scheduler_offer(item.scheduler_slate_id, [])
    with pytest.raises(ValueError, match="offer"):
        repository.bind_submission_offer(submission_id="filtered", session_id=session, practice_item_id=item.practice_item_id, scheduler_candidate_id=item.scheduler_candidate_id)
    assert repository.scheduler_slate_candidates(item.scheduler_slate_id)[0]["was_returned"] == 0


@pytest.mark.parametrize(("change", "reason"), [({"outcome_hints_used": 1}, "hinted"), ({"outcome_primed": 1}, "primed"), ({"elapsed_seconds": 10}, "insufficient_delay"), ({"intervening_attempt_count": 1}, "intervening_practice"), ({"outcome_session_id": "source"}, "same_session"), ({"outcome_primed": None}, "priming_unknown")])
def test_retention_contract_rejects_contaminated_or_unobserved_labels(change, reason):
    row = {"label_value": 1, "outcome_hints_used": 0, "outcome_primed": 0, "elapsed_seconds": 86400, "source_session_id": "source", "outcome_session_id": "later", "intervening_attempt_count": 0}
    assert retention_exclusions(row) == []
    row.update(change)
    assert reason in retention_exclusions(row)


def _split_rows(count, *, lineage):
    """One human attempt per day; `lineage(index)` gives each item's contract."""
    attempts = [{"id": f"{index:02d}", "practice_item_id": f"item{index}", "learning_object_id": f"lo{index}", "created_at": f"2026-01-{index + 1:02d}T00:00:00Z", "evidence_origin": "human"} for index in range(count)]
    contracts = [{"practice_item_id": row["practice_item_id"], "contract_json": json.dumps(lineage(index))} for index, row in enumerate(attempts)]
    return attempts, contracts


def _blueprint(name):
    return {"recipes": [{"blueprint_id": name}]}


def test_split_assignments_quarantine_content_families_across_time_boundaries():
    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint("shared" if index in {0, 19} else f"bp{index}"))
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts)}
    assert assignments["00"]["group_hash"] == assignments["19"]["group_hash"]
    assert assignments["00"]["split"] == assignments["19"]["split"] == "quarantined_boundary_overlap"
    assert max(key for key, row in assignments.items() if row["split"] == "train") < min(key for key, row in assignments.items() if row["split"] == "test")


def test_split_assignments_never_join_families_through_a_surface_format_label():
    attempts, contracts = _split_rows(20, lineage=lambda index: {**_blueprint(f"bp{index}"), "surface_family": "verbal_option_recognition"})
    assignments = split_assignments(attempts, contracts)
    assert len({row["group_hash"] for row in assignments}) == 20
    assert not any(row["split"] == "quarantined_boundary_overlap" for row in assignments)


def test_independent_content_families_both_land_in_splits():
    # Family A is practised early, family B late; neither crosses a cutoff.
    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint("family-a" if index < 10 else f"bp{index}"))
    for attempt in attempts[:10]:
        attempt["learning_object_id"] = "lo_a"
    for attempt in attempts[17:]:
        attempt["learning_object_id"] = "lo_b"
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts)}
    assert {assignments[f"{index:02d}"]["split"] for index in range(10)} == {"train"}
    assert {assignments[f"{index:02d}"]["split"] for index in range(17, 20)} == {"test"}
    assert assignments["00"]["group_hash"] != assignments["19"]["group_hash"]


def test_source_spans_join_learning_objects_into_one_family():
    attempts, contracts = _split_rows(2, lineage=lambda index: {})
    links = [{"entity_type": "learning_object", "entity_id": row["learning_object_id"], "source_id": "src", "revision_id": "rev", "locator": "span:ext/s1", "status": "current"} for row in attempts]
    joined = split_assignments(attempts, contracts, links)
    assert joined[0]["group_hash"] == joined[1]["group_hash"]
    assert all(row["content_provenance"] for row in joined)
    unlinked = split_assignments(attempts, contracts)
    assert {row["split"] for row in unlinked} == {"unavailable_provenance"}


def test_non_human_attempts_do_not_quarantine_a_human_family():
    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint(f"bp{index}"))
    simulated = {"id": "sim", "practice_item_id": "item0", "learning_object_id": "lo0", "created_at": "2026-02-01T00:00:00Z", "evidence_origin": "simulator"}
    assignments = {row["attempt_id"]: row for row in split_assignments([*attempts, simulated], contracts)}
    assert assignments["00"]["split"] == "train"
    assert assignments["sim"]["split"] == "unavailable_origin"
    assert assignments["sim"]["group_hash"] == assignments["00"]["group_hash"]


def test_split_assignments_are_independent_of_input_order():
    import random

    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint(f"bp{index % 4}"))
    expected = split_assignments(attempts, contracts)
    shuffled_attempts, shuffled_contracts = list(attempts), list(contracts)
    random.Random(7).shuffle(shuffled_attempts)
    random.Random(8).shuffle(shuffled_contracts)
    assert split_assignments(shuffled_attempts, shuffled_contracts) == expected


def test_split_on_a_copy_of_the_linear_algebra_fixture_finds_real_families(tmp_path):
    import shutil
    from pathlib import Path

    from learnloop.substrate.data_quality import rows, table_names
    from learnloop.substrate.dataset import _split_source_links

    copy = tmp_path / "state.sqlite"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra" / "state.sqlite", copy)
    connection = sqlite3.connect(copy)
    connection.row_factory = sqlite3.Row
    try:
        attempts = rows(connection, "practice_attempts", columns=("id", "practice_item_id", "learning_object_id", "created_at"))
        for attempt in attempts:
            attempt["evidence_origin"] = "human"
        assignments = split_assignments(attempts, rows(connection, "assessment_contract_versions"), _split_source_links(connection, table_names(connection)))
    finally:
        connection.close()
    learning_objects = {attempt["learning_object_id"] for attempt in attempts}
    assert len({row["group_hash"] for row in assignments}) >= len(learning_objects) - 2
    assert not any(row["split"] == "unavailable_provenance" for row in assignments)
    assert any(row["split"] == "train" for row in assignments)


@pytest.mark.durability
def test_production_lane_and_live_backup_preserve_committed_state(tmp_path):
    from threading import Event, Thread
    paths = create_basic_vault(tmp_path / "vault")
    connection = connect(paths.sqlite_path)
    assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    connection.execute("CREATE TABLE backup_pair(id INTEGER PRIMARY KEY, value INTEGER)")
    connection.executemany("INSERT INTO backup_pair VALUES (?,0)", [(1,), (2,)])
    connection.commit()
    connection.close()
    stop = Event()
    started = Event()
    failures = []
    def write():
        connection = connect(paths.sqlite_path)
        try:
            started.set()
            while not stop.is_set():
                with connection:
                    connection.execute("UPDATE backup_pair SET value=value+1")
                stop.wait(0.003)
        except BaseException as exc:
            failures.append(exc)
        finally:
            connection.close()
    thread = Thread(target=write)
    thread.start()
    try:
        assert started.wait(2)
        export_dataset(paths.sqlite_path, tmp_path / "live-export")
    finally:
        stop.set()
        thread.join(10)
    assert not thread.is_alive() and not failures
    with sqlite3.connect(tmp_path / "live-export" / "snapshot.sqlite") as snapshot:
        values = [row[0] for row in snapshot.execute("SELECT value FROM backup_pair")]
        assert values[0] == values[1]
        assert snapshot.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_export_preserves_censored_repair_disposition_as_distinct_from_failure(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    result = complete_self_graded_attempt(vault, repository, AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="A factorization", evidence_origin="human"), SelfGradeInput(criterion_points={"correctness": 4}, confidence=3))
    repository.insert_causal_cold_outcome(outcome_id="expired", outcome="right_censored_expired", followup_task_id="expired-task", remediation_episode_id=None, case_kind=None, case_ref=None, source_attempt_id=result.attempt_id, cold_attempt_id=None, repair_class_id=None, hypothesis_ids=[], cold_verification_id=None, servable_opportunity=True, duration_state=None, detail={"reason": "expired"}, store_version="test-v1", scheduled_not_before=None, scheduled_expires_at=None)
    with repository.connection() as connection:
        label = outcome_records(connection)[0]
    assert label["R_cold"] == [{"causal_outcome_id": "expired", "followup_task_id": "expired-task", "status": "right_censored_expired", "value": None, "verification_id": None, "label_kind": "repair_disposition"}]
    assert data_quality_report(paths.sqlite_path)["cold_terminal_dispositions"] == {"right_censored_expired": 1}


def _self_graded_attempt(paths, repository, *, clock=None, evidence_origin="human"):
    vault = load_vault(paths.root)
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="A factorization", evidence_origin=evidence_origin),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
        clock=clock or FrozenClock(NOW),
    )


def test_adjudication_rejects_a_missing_attempt_with_a_value_error(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    attempt = _self_graded_attempt(paths, repository)
    with pytest.raises(ValueError, match="does not exist"):
        repository.record_false_remediation(attempt_id="att_typo", value=True, evidence_refs=[{"table": "practice_attempts", "id": attempt.attempt_id}], author_kind="human", verifier_version="test-v1")


@pytest.mark.parametrize("reference", [{"table": ["practice_attempts"], "id": "x"}, {"table": "practice_attempts", "id": 7}, "practice_attempts"])
def test_adjudication_rejects_malformed_evidence_references(tmp_path, reference):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    attempt = _self_graded_attempt(paths, repository)
    with pytest.raises(ValueError, match="evidence reference"):
        repository.record_false_remediation(attempt_id=attempt.attempt_id, value=True, evidence_refs=[reference], author_kind="human", verifier_version="test-v1")


def test_adjudication_accepts_evidence_keyed_by_a_non_id_primary_key(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    clock = FrozenClock(NOW)
    session = repository.create_session(clock=clock)
    offer = build_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))[0]
    repository.finalize_scheduler_offer(offer.scheduler_slate_id, [offer.scheduler_candidate_id])
    repository.bind_submission_offer(submission_id="sub-1", session_id=session, practice_item_id=offer.practice_item_id, scheduler_candidate_id=offer.scheduler_candidate_id)
    attempt = _self_graded_attempt(paths, repository)
    references = [{"table": "submission_intents", "id": "sub-1"}, {"table": "scheduler_offer_receipts", "id": offer.scheduler_slate_id}]
    adjudication = repository.record_false_remediation(attempt_id=attempt.attempt_id, value=True, evidence_refs=references, author_kind="human", verifier_version="test-v1")
    assert adjudication
    with pytest.raises(ValueError, match=r"submission_intents\.submission_id='missing' does not exist"):
        repository.record_false_remediation(attempt_id=attempt.attempt_id, value=True, evidence_refs=[{"table": "submission_intents", "id": "missing"}], author_kind="human", verifier_version="test-v1")
    with repository.connection() as connection:
        receipt_version = connection.execute("SELECT collection_version FROM scheduler_offer_receipts").fetchone()[0]
    assert receipt_version == COLLECTION_VERSION


def _final_receipt(repository, receipt_id, *, source_attempt_id, derived, cold_attempt_id=None):
    repository.insert_coldness_receipt(receipt_id=receipt_id, lane="repair_cold_retry", stage="final", followup_task_id=None, remediation_episode_id=None, source_attempt_id=source_attempt_id, cold_attempt_id=cold_attempt_id, cold_verification_id=None, dimensions={}, derived=derived, telemetry_coverage={}, receipt_version="test-v1")


def test_cold_receipt_status_keeps_unscorable_and_dispositions_distinct(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    attempt = _self_graded_attempt(paths, repository)
    _final_receipt(repository, "a-qualified-unscored", source_attempt_id=attempt.attempt_id, derived={"qualifies_as_cold_retrieval": True})
    _final_receipt(repository, "b-expired", source_attempt_id=attempt.attempt_id, derived={"qualifies_as_cold_retrieval": None, "outcome": "right_censored_expired"})
    _final_receipt(repository, "c-qualified-scored", source_attempt_id=attempt.attempt_id, cold_attempt_id=attempt.attempt_id, derived={"qualifies_as_cold_retrieval": True, "outcome": "cold_success"})
    _final_receipt(repository, "d-unqualified", source_attempt_id=attempt.attempt_id, derived={"qualifies_as_cold_retrieval": False})
    with repository.connection() as connection:
        label = outcome_records(connection)[0]
    statuses = {record["receipt_id"]: record["status"] for record in label["R_cold"]}
    assert statuses == {"a-qualified-unscored": "unscorable", "b-expired": "right_censored_expired", "c-qualified-scored": "observed", "d-unqualified": "unqualified"}


def test_failed_export_leaves_no_manifest_and_no_partial_directory(tmp_path, monkeypatch):
    import learnloop.substrate.dataset as dataset

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)

    def fail(connection):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(dataset, "outcome_records", fail)
    output = tmp_path / "dataset"
    with pytest.raises(sqlite3.OperationalError):
        export_dataset(paths.sqlite_path, output)
    assert not output.exists()


def test_manifest_is_published_by_atomic_rename(tmp_path, monkeypatch):
    import os

    import learnloop.substrate.dataset as dataset

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    replaced = []
    real_replace = os.replace

    def observe_replace(source, destination):
        # The final name must not exist until the complete file is renamed onto it.
        assert not os.path.exists(destination)
        assert json.loads(open(source, encoding="utf-8").read())["artifacts"]
        replaced.append((os.path.basename(source), os.path.basename(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(dataset.os, "replace", observe_replace)
    output = tmp_path / "dataset"
    manifest = export_dataset(paths.sqlite_path, output)
    assert replaced == [("manifest.json.tmp", "manifest.json")]
    assert json.loads((output / "manifest.json").read_text()) == json.loads(json.dumps(manifest))
    assert not (output / "manifest.json.tmp").exists()
    for name, artifact in manifest["artifacts"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == artifact["sha256"]


def _cli(*args):
    from typer.testing import CliRunner

    from learnloop.cli import app

    return CliRunner().invoke(app, [str(arg) for arg in args])


def _evidence_file(tmp_path, references):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(references), encoding="utf-8")
    return path


def test_adjudicate_cli_records_through_the_locked_vault_opener(tmp_path, monkeypatch):
    import learnloop.vault.repository as vault_repository

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    attempt = _self_graded_attempt(paths, repository)
    migrated = []
    real_migrate = vault_repository.migrate_vault

    def spy(*args, **kwargs):
        migrated.append(args[0])
        return real_migrate(*args, **kwargs)

    monkeypatch.setattr(vault_repository, "migrate_vault", spy)
    evidence = _evidence_file(tmp_path, [{"table": "practice_attempts", "id": attempt.attempt_id}])
    result = _cli("adjudicate-remediation", attempt.attempt_id, "--false-remediation", "--evidence", evidence, "--verifier-version", "test-v1", "--vault", paths.root)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["adjudication_id"]
    assert migrated == [paths.root]


@pytest.mark.parametrize(("attempt_id", "references", "message"), [
    ("att_typo", None, "does not exist"),
    (None, [{"table": ["practice_attempts"], "id": "x"}], "string table"),
    (None, [{"table": "submission_intents", "id": "missing"}], "does not exist"),
    (None, {"table": "practice_attempts"}, "JSON list"),
])
def test_adjudicate_cli_reports_bad_input_without_a_traceback(tmp_path, attempt_id, references, message):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    attempt = _self_graded_attempt(paths, repository)
    evidence = _evidence_file(tmp_path, references if references is not None else [{"table": "practice_attempts", "id": attempt.attempt_id}])
    result = _cli("adjudicate-remediation", attempt_id or attempt.attempt_id, "--false-remediation", "--evidence", evidence, "--verifier-version", "test-v1", "--vault", paths.root)
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert message in result.stderr


def test_dataset_export_cli_reports_sqlite_errors_and_removes_partial_output(tmp_path, monkeypatch):
    import learnloop.substrate.dataset as dataset

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)

    def locked(connection):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(dataset, "outcome_records", locked)
    output = tmp_path / "dataset"
    result = _cli("dataset-export", output, "--vault", paths.root)
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "database is locked" in result.stderr
    assert not output.exists()


def test_dataset_export_cli_refuses_an_existing_output_directory(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    output = tmp_path / "dataset"
    output.mkdir()
    (output / "keep.txt").write_text("mine", encoding="utf-8")
    result = _cli("dataset-export", output, "--vault", paths.root)
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "mine"
