from __future__ import annotations

from collections import Counter
from datetime import timedelta
import hashlib
import json
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.outcome_contract import COLLECTION_VERSION, retention_exclusions
from learnloop.scheduling.scheduler import SELECTION_FEATURE_SCHEMA, SchedulerSession, build_due_queue
from learnloop.scheduling.selection_rewards import item_demand_vector
from learnloop.substrate.data_quality import data_quality_report
from learnloop.substrate.dataset import DEFAULT_EMBARGO, export_dataset, parse_embargo, split_assignments
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


@pytest.mark.parametrize(("change", "reason"), [({"outcome_hints_used": 1}, "hinted"), ({"outcome_primed": 1}, "primed"), ({"elapsed_seconds": 10}, "insufficient_delay"), ({"elapsed_seconds": float("nan")}, "insufficient_delay"), ({"elapsed_seconds": float("inf")}, "insufficient_delay"), ({"intervening_attempt_count": 1}, "intervening_practice"), ({"outcome_session_id": "source"}, "same_session"), ({"outcome_primed": None}, "priming_unknown")])
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
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts, policy="content")}
    assert assignments["00"]["group_hash"] == assignments["19"]["group_hash"]
    assert assignments["00"]["split"] == assignments["19"]["split"] == "quarantined_boundary_overlap"
    assert max(key for key, row in assignments.items() if row["split"] == "train") < min(key for key, row in assignments.items() if row["split"] == "test")


def test_split_assignments_never_join_families_through_a_surface_format_label():
    attempts, contracts = _split_rows(20, lineage=lambda index: {**_blueprint(f"bp{index}"), "surface_family": "verbal_option_recognition"})
    assignments = split_assignments(attempts, contracts, policy="content")
    assert len({row["group_hash"] for row in assignments}) == 20
    assert not any(row["split"] == "quarantined_boundary_overlap" for row in assignments)


def test_independent_content_families_both_land_in_splits():
    # Family A is practised early, family B late; neither crosses a cutoff.
    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint("family-a" if index < 10 else f"bp{index}"))
    for attempt in attempts[:10]:
        attempt["learning_object_id"] = "lo_a"
    for attempt in attempts[17:]:
        attempt["learning_object_id"] = "lo_b"
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts, policy="content")}
    assert {assignments[f"{index:02d}"]["split"] for index in range(10)} == {"train"}
    assert {assignments[f"{index:02d}"]["split"] for index in range(17, 20)} == {"test"}
    assert assignments["00"]["group_hash"] != assignments["19"]["group_hash"]


def test_source_spans_join_learning_objects_into_one_family():
    attempts, contracts = _split_rows(2, lineage=lambda index: {})
    links = [{"entity_type": "learning_object", "entity_id": row["learning_object_id"], "source_id": "src", "revision_id": "rev", "locator": "span:ext/s1", "status": "current"} for row in attempts]
    joined = split_assignments(attempts, contracts, links, policy="content")
    assert joined[0]["group_hash"] == joined[1]["group_hash"]
    assert all(row["content_provenance"] for row in joined)
    for policy in ("content", "temporal"):
        unlinked = split_assignments(attempts, contracts, policy=policy)
        assert {row["split"] for row in unlinked} == {"unavailable_provenance"}


def test_non_human_attempts_do_not_quarantine_a_human_family():
    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint(f"bp{index}"))
    simulated = {"id": "sim", "practice_item_id": "item0", "learning_object_id": "lo0", "created_at": "2026-02-01T00:00:00Z", "evidence_origin": "simulator"}
    assignments = {row["attempt_id"]: row for row in split_assignments([*attempts, simulated], contracts, policy="content")}
    assert assignments["00"]["split"] == "train"
    assert assignments["sim"]["split"] == "unavailable_origin"
    assert assignments["sim"]["group_hash"] == assignments["00"]["group_hash"]


def test_non_human_attempts_do_not_move_a_learning_objects_temporal_cutoffs():
    attempts, contracts = _two_learning_object_history()
    expected = split_assignments(attempts, contracts, embargo=timedelta(0))
    simulated = {"id": "sim", "practice_item_id": "a-item0", "learning_object_id": "lo_a", "created_at": "2026-03-01T00:00:00Z", "evidence_origin": "simulator"}
    assignments = split_assignments([*attempts, simulated], contracts, embargo=timedelta(0))
    assert [row for row in assignments if row["attempt_id"] != "sim"] == expected
    assert next(row for row in assignments if row["attempt_id"] == "sim")["split"] == "unavailable_origin"


def _two_learning_object_history():
    """Two learning objects practised on the same ten days, each item once.

    `lo_a` is practised at midnight and `lo_b` at noon, and every item has its
    own blueprint, so each learning object's history is one content family.
    """
    attempts = []
    for day in range(10):
        for learning_object, hour in (("lo_a", "00"), ("lo_b", "12")):
            prefix = learning_object[-1]
            attempts.append({
                "id": f"{prefix}{day}",
                "practice_item_id": f"{prefix}-item{day}",
                "learning_object_id": learning_object,
                "created_at": f"2026-01-{day + 1:02d}T{hour}:00:00Z",
                "evidence_origin": "human",
            })
    contracts = [{"practice_item_id": row["practice_item_id"], "contract_json": json.dumps(_blueprint(row["practice_item_id"]))} for row in attempts]
    return attempts, contracts


def _splits_by_learning_object(assignments):
    by_learning_object = {"a": Counter(), "b": Counter()}
    for row in assignments:
        by_learning_object[row["attempt_id"][0]][row["split"]] += 1
    return by_learning_object


def test_temporal_policy_splits_each_learning_objects_own_history():
    attempts, contracts = _two_learning_object_history()
    assignments = split_assignments(attempts, contracts, policy="temporal", embargo=timedelta(0))
    by_id = {row["attempt_id"]: row for row in assignments}
    # Ten distinct days per learning object: 7 train, 1 validation, 2 test.
    assert _splits_by_learning_object(assignments) == {
        "a": Counter(train=7, validation=1, test=2),
        "b": Counter(train=7, validation=1, test=2),
    }
    assert [by_id[f"a{day}"]["split"] for day in range(10)] == ["train"] * 7 + ["validation"] + ["test"] * 2
    assert by_id["a0"]["group_hash"] == hashlib.sha256(b"lo:lo_a").hexdigest()
    assert len({row["group_hash"] for row in assignments}) == 2


def test_temporal_policy_default_embargo_quarantines_holdouts_near_training():
    attempts, contracts = _two_learning_object_history()
    assignments = split_assignments(attempts, contracts)
    assert DEFAULT_EMBARGO == timedelta(days=7)
    # Days 8 to 10 are within seven days of the last training attempt on day 7.
    assert _splits_by_learning_object(assignments) == {
        "a": Counter(train=7, quarantined_embargo=3),
        "b": Counter(train=7, quarantined_embargo=3),
    }


def test_content_policy_quarantines_learning_objects_revisited_across_cutoffs():
    attempts, contracts = _two_learning_object_history()
    assignments = split_assignments(attempts, contracts, policy="content")
    assert _splits_by_learning_object(assignments) == {
        "a": Counter(quarantined_boundary_overlap=10),
        "b": Counter(quarantined_boundary_overlap=10),
    }
    assert len({row["group_hash"] for row in assignments}) == 2


@pytest.mark.parametrize(("embargo_seconds", "expected"), [
    (86400, "validation"),
    (86400 + 1, "quarantined_embargo"),
    (86400 - 1, "validation"),
], ids=["exactly_at_embargo", "just_inside_embargo", "just_outside_embargo"])
def test_temporal_embargo_boundary(embargo_seconds, expected):
    # The validation attempt on day 8 is exactly one day after the last training attempt.
    attempts, contracts = _two_learning_object_history()
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts, embargo=timedelta(seconds=embargo_seconds))}
    assert assignments["a6"]["split"] == "train"
    assert assignments["a7"]["chronological_split"] == "validation"
    assert assignments["a7"]["split"] == expected


def test_temporal_policy_keeps_equal_timestamps_in_one_bucket():
    attempts, contracts = _two_learning_object_history()
    # Days 7 and 8 of lo_a (indexes 6 and 7) become one batch at a single instant.
    batch_time = "2026-01-07T00:00:00Z"
    for attempt in attempts:
        if attempt["id"] in {"a6", "a7"}:
            attempt["created_at"] = batch_time
    assignments = {row["attempt_id"]: row for row in split_assignments(attempts, contracts, embargo=timedelta(0))}
    assert assignments["a6"]["chronological_split"] == assignments["a7"]["chronological_split"]


@pytest.mark.parametrize("policy", ["content", "temporal"])
def test_split_assignments_are_independent_of_input_order(policy):
    import random

    attempts, contracts = _split_rows(20, lineage=lambda index: _blueprint(f"bp{index % 4}"))
    for index, attempt in enumerate(attempts):
        attempt["learning_object_id"] = f"lo{index % 3}"
    expected = split_assignments(attempts, contracts, policy=policy, embargo=timedelta(days=1))
    shuffled_attempts, shuffled_contracts = list(attempts), list(contracts)
    random.Random(7).shuffle(shuffled_attempts)
    random.Random(8).shuffle(shuffled_contracts)
    assert split_assignments(shuffled_attempts, shuffled_contracts, policy=policy, embargo=timedelta(days=1)) == expected


def test_split_assignments_are_independent_of_the_python_hash_seed():
    import os
    import subprocess
    import sys

    attempts, contracts = _two_learning_object_history()
    script = (
        "import json, sys\n"
        "from datetime import timedelta\n"
        "from learnloop.substrate.dataset import split_assignments\n"
        "attempts, contracts = json.load(sys.stdin)\n"
        "print(json.dumps({policy: split_assignments(attempts, contracts, policy=policy, embargo=timedelta(hours=30)) for policy in ('content', 'temporal')}, sort_keys=True))\n"
    )
    outputs = set()
    for seed in ("0", "1", "4242"):
        environment = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run([sys.executable, "-c", script], input=json.dumps([attempts, contracts]), capture_output=True, text=True, env=environment, check=True)
        outputs.add(result.stdout)
    assert len(outputs) == 1


def test_temporal_cutoffs_use_exact_integer_percentiles():
    # 90 distinct days: 70% is 63 training days and 85% is 76, which float
    # truncation of 90 * 0.7 (62.99...) would round down to 62.
    attempts = [
        {"id": f"{day:03d}", "practice_item_id": f"item{day}", "learning_object_id": "lo", "created_at": (NOW + timedelta(days=day)).isoformat(), "evidence_origin": "human"}
        for day in range(90)
    ]
    contracts = [{"practice_item_id": row["practice_item_id"], "contract_json": json.dumps(_blueprint("bp"))} for row in attempts]
    assignments = split_assignments(attempts, contracts, embargo=timedelta(0))
    assert Counter(row["split"] for row in assignments) == Counter(train=63, validation=13, test=14)


def test_temporal_split_reads_offsetless_timestamps_as_utc_on_any_host():
    import os
    import subprocess
    import sys

    # Read as UTC, the offsetless attempt (10:00) precedes the aware one
    # (12:00Z). Read in Los Angeles local time it would be 18:00Z and follow it.
    attempts = [
        {"id": "naive", "practice_item_id": "item-naive", "learning_object_id": "lo", "created_at": "2026-01-01T10:00:00", "evidence_origin": "human"},
        {"id": "aware", "practice_item_id": "item-aware", "learning_object_id": "lo", "created_at": "2026-01-01T12:00:00Z", "evidence_origin": "human"},
    ]
    contracts = [{"practice_item_id": row["practice_item_id"], "contract_json": json.dumps(_blueprint("bp"))} for row in attempts]
    script = (
        "import json, sys\n"
        "from datetime import timedelta\n"
        "from learnloop.substrate.dataset import split_assignments\n"
        "attempts, contracts = json.load(sys.stdin)\n"
        "print(json.dumps({row['attempt_id']: row['split'] for row in split_assignments(attempts, contracts, embargo=timedelta(0))}, sort_keys=True))\n"
    )
    outputs = set()
    for zone in ("UTC", "America/Los_Angeles", "Asia/Tokyo"):
        environment = {**os.environ, "TZ": zone}
        result = subprocess.run([sys.executable, "-c", script], input=json.dumps([attempts, contracts]), capture_output=True, text=True, env=environment, check=True)
        outputs.add(result.stdout)
    assert len(outputs) == 1
    assert json.loads(outputs.pop()) == {"naive": "train", "aware": "test"}


@pytest.mark.parametrize(("text", "seconds"), [("7d", 604800), ("36h", 129600), ("90m", 5400), ("30s", 30), ("0", 0), ("1.5d", 129600)])
def test_parse_embargo_reads_durations(text, seconds):
    assert parse_embargo(text) == timedelta(seconds=seconds)


@pytest.mark.parametrize("text", ["7", "-1d", "week", "7 days", "", "1000000000d", "9" * 400 + "s"])
def test_parse_embargo_refuses_other_text(text):
    with pytest.raises(ValueError, match="duration"):
        parse_embargo(text)


def test_split_assignments_refuse_an_unknown_policy_or_negative_embargo():
    attempts, contracts = _two_learning_object_history()
    with pytest.raises(ValueError, match="policy"):
        split_assignments(attempts, contracts, policy="random")
    with pytest.raises(ValueError, match="negative"):
        split_assignments(attempts, contracts, embargo=timedelta(seconds=-1))


def _linear_algebra_fixture_split_inputs(tmp_path):
    """Attempts, contracts and source links from a copy of the fixture, with
    every attempt treated as human because the fixture predates evidence origin."""
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
        return attempts, rows(connection, "assessment_contract_versions"), _split_source_links(connection, table_names(connection))
    finally:
        connection.close()


def test_content_split_on_a_copy_of_the_linear_algebra_fixture_finds_real_families(tmp_path):
    attempts, contracts, links = _linear_algebra_fixture_split_inputs(tmp_path)
    assignments = split_assignments(attempts, contracts, links, policy="content")
    learning_objects = {attempt["learning_object_id"] for attempt in attempts}
    assert len({row["group_hash"] for row in assignments}) >= len(learning_objects) - 2
    assert Counter(row["split"] for row in assignments) == Counter(train=23, quarantined_boundary_overlap=47)


def test_temporal_split_on_a_copy_of_the_linear_algebra_fixture_has_holdouts(tmp_path):
    attempts, contracts, links = _linear_algebra_fixture_split_inputs(tmp_path)

    def counts(embargo):
        return Counter(row["split"] for row in split_assignments(attempts, contracts, links, policy="temporal", embargo=embargo))

    assert counts(timedelta(0)) == Counter(train=45, validation=10, test=15)
    assert counts(timedelta(days=1)) == Counter(train=45, quarantined_embargo=21, validation=1, test=3)
    # The fixture's whole history spans under six days, so the seven-day
    # default embargo quarantines every held-out attempt.
    assert counts(DEFAULT_EMBARGO) == Counter(train=45, quarantined_embargo=25)


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


@pytest.mark.parametrize(("arguments", "policy", "parameters"), [
    ((), "temporal", {"embargo_seconds": 604800}),
    (("--embargo", "36h"), "temporal", {"embargo_seconds": 129600}),
    (("--split-policy", "content"), "content", {}),
])
def test_dataset_export_records_the_split_policy(tmp_path, arguments, policy, parameters):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    _self_graded_attempt(paths, repository)
    output = tmp_path / "dataset"
    result = _cli("dataset-export", output, *arguments, "--vault", paths.root)
    assert result.exit_code == 0, result.output
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_version"] == 2
    assert manifest["split_policy"] == policy
    assert manifest["split_parameters"] == parameters
    assert "A dataset_version 1 manifest has no split_policy field; its split_assignments use the content policy." in manifest["splits"]
    assert "supports claims about" in manifest["splits"] and "does not support claims about" in manifest["splits"]
    splits = manifest["missingness"]["splits"]
    assert splits["split_policy"] == policy
    assert splits["parameters"] == parameters
    assert sum(splits["counts"].values()) == manifest["artifacts"]["split_assignments.jsonl"]["rows"] == 1
    assert json.loads(result.stdout)["split_policy"] == policy


@pytest.mark.parametrize(("arguments", "message"), [
    (("--split-policy", "random"), "Split policy"),
    (("--embargo", "a week"), "duration"),
    (("--embargo", "1000000000d"), "too large"),
])
def test_dataset_export_cli_refuses_a_bad_split_option_before_writing(tmp_path, arguments, message):
    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    output = tmp_path / "dataset"
    result = _cli("dataset-export", output, *arguments, "--vault", paths.root)
    assert result.exit_code == 1
    assert message in result.stderr
    assert not output.exists()


def test_data_quality_report_outside_an_export_names_no_split_policy(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    assert "splits" not in data_quality_report(paths.sqlite_path)


def test_writers_stamp_the_current_collection_version(tmp_path, monkeypatch):
    import learnloop.db.repositories as repositories
    import learnloop.db.stores.collection as collection_store

    monkeypatch.setattr(repositories, "COLLECTION_VERSION", "learnloop-events-test")
    monkeypatch.setattr(collection_store, "COLLECTION_VERSION", "learnloop-events-test")
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    vault = load_vault(paths.root)
    clock = FrozenClock(NOW)
    session = repository.create_session(clock=clock)
    offer = build_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))[0]
    repository.finalize_scheduler_offer(offer.scheduler_slate_id, [offer.scheduler_candidate_id])
    attempt = _self_graded_attempt(paths, repository)
    with repository.connection() as connection:
        versions = {
            "slate": connection.execute("SELECT collection_version FROM scheduler_slates WHERE id=?", (offer.scheduler_slate_id,)).fetchone()[0],
            "offer": connection.execute("SELECT collection_version FROM scheduler_offer_receipts WHERE slate_id=?", (offer.scheduler_slate_id,)).fetchone()[0],
            "attempt": connection.execute("SELECT collection_version FROM practice_attempts WHERE id=?", (attempt.attempt_id,)).fetchone()[0],
        }
    assert versions == {"slate": "learnloop-events-test", "offer": "learnloop-events-test", "attempt": "learnloop-events-test"}
