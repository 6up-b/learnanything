from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.outcome_contract import retention_exclusions
from learnloop.scheduling.scheduler import SELECTION_FEATURE_SCHEMA, SchedulerSession, build_due_queue
from learnloop.scheduling.selection_rewards import item_demand_vector
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


def test_selection_decision_features_reference_the_item_and_stay_compact(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    clock = FrozenClock(NOW)
    session = repository.create_session(clock=clock)
    offered = build_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))[0]
    features = repository.decision_features(decision_id=offered.scheduler_candidate_id, decision_type="selection")
    item = vault.practice_items[offered.practice_item_id]
    learning_object = vault.learning_object_for_item(item)
    demand = features["item_demand_vector"]
    # The item is referenced by id and snapshot hash, and only the demand
    # fields the selector scores are kept.
    assert demand["practice_item_id"] == item.id
    assert demand["content_hash"] == hashlib.sha256(
        json.dumps(item.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert {key: value for key, value in demand.items() if key not in {"practice_item_id", "content_hash"}} == item_demand_vector(vault, item, learning_object, None).as_dict()
    assert "prompt" not in demand and "expected_answer" not in demand
    assert features["ability_vector"]["learning_object_id"] == learning_object.id
    assert {"lo_mastery", "facet_recall_mean_by_facet", "mastery"} <= set(features["ability_vector"])
    assert features["context"] == {"feature_schema": SELECTION_FEATURE_SCHEMA}
    with connect(paths.sqlite_path) as connection:
        largest_row = connection.execute(
            "SELECT MAX(LENGTH(ability_vector_json) + LENGTH(item_demand_vector_json) + LENGTH(context_json)) FROM decision_features WHERE decision_type = 'selection'"
        ).fetchone()[0]
    assert largest_row < 2048


def test_scored_item_text_is_snapshotted_once_per_revision_and_exported(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    clock = FrozenClock(NOW)
    session = SchedulerSession(session_id=repository.create_session(clock=clock))

    def snapshots() -> list[sqlite3.Row]:
        with connect(paths.sqlite_path) as connection:
            return connection.execute(
                "SELECT * FROM practice_item_snapshots ORDER BY practice_item_id, created_at"
            ).fetchall()

    def scored_item_ids() -> set[str]:
        with connect(paths.sqlite_path) as connection:
            rows = connection.execute(
                "SELECT item_demand_vector_json FROM decision_features WHERE decision_type = 'selection'"
            ).fetchall()
        return {json.loads(row[0])["practice_item_id"] for row in rows}

    for _ in range(5):
        offered = build_due_queue(vault, repository, clock=clock, session=session)[0]
    assert sorted(row["practice_item_id"] for row in snapshots()) == sorted(scored_item_ids())

    item = vault.practice_items[offered.practice_item_id]
    vault.practice_items[item.id] = item.model_copy(update={"prompt": item.prompt + " (edited)"})
    build_due_queue(vault, repository, clock=clock, session=session)
    revisions = [row for row in snapshots() if row["practice_item_id"] == item.id]
    assert len(revisions) == 2
    assert {json.loads(row["item_json"])["prompt"] for row in revisions} == {item.prompt, item.prompt + " (edited)"}
    for row in revisions:
        assert hashlib.sha256(row["item_json"].encode("utf-8")).hexdigest() == row["content_hash"]
    with connect(paths.sqlite_path) as connection, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("DELETE FROM practice_item_snapshots")

    # Every exported selection feature joins back to the exact scored text.
    output = tmp_path / "dataset"
    manifest = export_dataset(paths.sqlite_path, output)
    assert "practice_item_snapshots" in manifest["inclusion"]["tables"]
    exported = {
        row["content_hash"]: row
        for row in map(json.loads, (output / "practice_item_snapshots.jsonl").read_text().splitlines())
    }
    features = [json.loads(line) for line in (output / "decision_features.jsonl").read_text().splitlines()]
    selection = [row for row in features if row["decision_type"] == "selection"]
    assert len(selection) == 6 * len(scored_item_ids())
    for row in selection:
        demand = json.loads(row["item_demand_vector_json"])
        assert exported[demand["content_hash"]]["practice_item_id"] == demand["practice_item_id"]

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


def test_split_assignments_quarantine_source_families_across_time_boundaries():
    attempts = [{"id": str(index), "practice_item_id": f"item{index}", "learning_object_id": f"lo{index}", "created_at": f"2026-01-{index + 1:02d}T00:00:00Z", "evidence_origin": "human"} for index in range(20)]
    contracts = [{"practice_item_id": row["practice_item_id"], "contract_json": json.dumps({"surface_family": "shared" if index in {0, 19} else f"family{index}"})} for index, row in enumerate(attempts)]
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts)}
    assert assignments["0"]["group_hash"] == assignments["19"]["group_hash"]
    assert assignments["0"]["split"] == assignments["19"]["split"] == "quarantined_boundary_overlap"
    assert max(int(key) for key, row in assignments.items() if row["split"] == "train") < min(int(key) for key, row in assignments.items() if row["split"] == "test")


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
