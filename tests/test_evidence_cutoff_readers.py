"""Each census reader against its cutoff preset on a real vault: the reader's admitted ids, their order, the
corrections it shows and its exceptions are what the preset says (``learnloop.db.evidence_cutoff``).

- the diagnoser's history (``VaultHistoryStore``) and ``Cutoff.history_v1``: an imported exam (occurred before it
  was received), two attempts in one second, a record written at exactly the target's completion, the availability
  switch on and off, missing, malformed and empty receipts; a regrade, a hold and its release, a causal hypothesis
  version and a mutable status, each alone; a delayed read of one target equal to the live one at fixed
  corrections, and what later corrections change;
- the planted-history store (``StaticHistoryStore``) and ``Cutoff.corrected_before``;
- adaptive difficulty's replay (``replay.load_events``) and ``Cutoff.ad_replay``, the learner field's rows
  (``field.outcomes.load_attempt_rows``) and ``Cutoff.completed_by``: equal-time inclusion.

Fakes only; no model call.
"""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import sqlite3
from typing import Any

import pytest

from learnloop.db.evidence_cutoff import Cutoff

from tests.diagnosis_split_helpers import at, build_diagnosis_vault, seed_history
from tests.helpers import append_config_toml

OFF = "[router_objective]\navailable_at_reads = false\n"


def iso(hours: float) -> str:
    return at(hours).isoformat().replace("+00:00", "Z")


def _rows(sqlite_path: Any) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT id, created_at, received_at, attempt_type FROM practice_attempts ORDER BY created_at, id")]


def _write(sqlite_path: Any, sql: str, *params: Any) -> None:
    with closing(sqlite3.connect(sqlite_path)) as connection, connection:
        connection.execute(sql, params)


def _history(tmp_path, *, switch: bool = True):
    paths = build_diagnosis_vault(tmp_path / "vault")
    if not switch:
        append_config_toml(paths.root, OFF)
    seed_history(paths)
    return paths


def _store(paths):
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.vault.loader import load_vault

    return VaultHistoryStore(load_vault(paths.root), Repository(paths.sqlite_path))


def _preset_for(store, target: str, rows: list[dict[str, Any]], switch: bool) -> Cutoff:
    row = next(row for row in rows if row["id"] == target)
    received = row["received_at"] if switch and row["received_at"] else None
    return Cutoff.history_v1(target, store.ref(target).completed_at, known_at=received, available_at_reads=switch)


def _measuring(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from learnloop.diagnosis.split.history import NON_MEASURING_ATTEMPT_TYPES

    return [row for row in rows if row["attempt_type"] not in NON_MEASURING_ATTEMPT_TYPES]


def _assert_history_matches_preset(paths, switch: bool) -> None:
    """At every target: the store's admitted ids and order are the preset's over the raw rows, and its lagged
    count is every other measuring attempt the preset leaves out."""

    store = _store(paths)
    rows = _measuring(_rows(paths.sqlite_path))
    for target in [row["id"] for row in rows]:
        cutoff = _preset_for(store, target, rows, switch)
        stated = store.cutoff(store.ref(target))  # the preset the store says it reads under
        assert {**stated.to_dict(), "times": None} == {**cutoff.to_dict(), "times": None}
        assert stated.history_known_cutoff() == cutoff.history_known_cutoff()
        admitted = [row["id"] for row in rows
                    if cutoff.admits(row["created_at"], row["received_at"], attempt_id=row["id"])]
        assert [attempt.attempt_id for attempt in store.attempts_before(store.ref(target))] == admitted, target
        others = [row for row in rows if row["id"] != target]
        assert store.lagged_attempts(store.ref(target)) == len(others) - len(admitted), target


# -- the attempt boundary ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("switch", [True, False], ids=["available_at_reads", "switch_off"])
def test_history_admits_by_the_preset_with_an_imported_exam_and_an_equal_second(tmp_path, switch):
    paths = _history(tmp_path, switch=switch)
    # An imported exam: att_04 happened at hour 0.5 and became known at hour 8 (after att_06 at hour 5).
    _write(paths.sqlite_path, "UPDATE practice_attempts SET created_at = ?, received_at = ?, "
           "received_at_source = 'recorded' WHERE id = 'att_04_unrelated_fail'", iso(0.5), iso(8))
    # Two attempts in one second: att_03 is moved to att_06's second; the id breaks the tie.
    _write(paths.sqlite_path, "UPDATE practice_attempts SET created_at = ? WHERE id = 'att_03_svd_pass'", iso(5))
    _assert_history_matches_preset(paths, switch)
    store = _store(paths)
    before_06 = [a.attempt_id for a in store.attempts_before(store.ref("att_06_svd_fail"))]
    assert "att_03_svd_pass" in before_06  # same second, smaller id
    assert "att_06_svd_fail" not in [a.attempt_id for a in store.attempts_before(store.ref("att_03_svd_pass"))]
    assert ("att_04_unrelated_fail" in before_06) is (not switch)  # not yet known at att_06 with the switch on
    assert "att_04_unrelated_fail" in [a.attempt_id for a in store.attempts_before(store.ref("att_07_svd_future"))]


@pytest.mark.parametrize("switch", [True, False], ids=["available_at_reads", "switch_off"])
def test_an_imported_target_is_decided_at_its_receipt(tmp_path, switch):
    paths = _history(tmp_path, switch=switch)
    # The target itself is the import: it happened at hour 1.5 and became known at hour 6.
    _write(paths.sqlite_path, "UPDATE practice_attempts SET created_at = ?, received_at = ? "
           "WHERE id = 'att_03_svd_pass'", iso(1.5), iso(6))
    _assert_history_matches_preset(paths, switch)
    store = _store(paths)
    # Attempts after its occurrence but before its receipt sort after it in the attempt order: out either way.
    assert [a.attempt_id for a in store.attempts_before(store.ref("att_03_svd_pass"))] == [
        "att_01_transpose_fail", "att_02_svd_fail"]


@pytest.mark.parametrize("switch", [True, False], ids=["available_at_reads", "switch_off"])
@pytest.mark.parametrize("receipt", ["", "not-a-time", None], ids=["empty", "malformed", "missing"])
def test_missing_malformed_and_empty_receipts(tmp_path, switch, receipt):
    """The loaded-row availability time: an empty or unreadable receipt sets no known time, so the attempt is
    admitted by its order alone (the SQL form would read an empty receipt as the empty string: see
    ``test_the_sql_form_reads_an_empty_receipt_as_text``)."""

    paths = _history(tmp_path, switch=switch)
    _write(paths.sqlite_path, "UPDATE practice_attempts SET received_at = ? WHERE id = 'att_04_unrelated_fail'",
           receipt)
    _assert_history_matches_preset(paths, switch)
    store = _store(paths)
    assert "att_04_unrelated_fail" in [a.attempt_id for a in store.attempts_before(store.ref("att_06_svd_fail"))]


def test_the_sql_form_reads_an_empty_receipt_as_text(tmp_path):
    """Characterization (the sheet's open row on cutoff compatibility): ``attempt_time_sql`` is
    ``COALESCE(received_at, created_at)``, which keeps an empty receipt, and ``''`` sorts before every time, so the
    SQL readers admit such a row at any cutoff while ``known_at`` over a loaded row falls back to ``created_at``.
    The attempt writer stores a blank receipt as NULL (``db/repositories.py``), so no written row has one."""

    from learnloop.db.attempt_availability import AVAILABLE_AT_SQL, known_at
    from types import SimpleNamespace

    config = SimpleNamespace(router_objective=SimpleNamespace(available_at_reads=True))
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT, received_at TEXT)")
        connection.execute("INSERT INTO practice_attempts VALUES ('late', '2026-06-01T00:00:00Z', '')")
        admitted = connection.execute(
            f"SELECT id FROM practice_attempts WHERE {AVAILABLE_AT_SQL} < ?", ("2026-05-05T09:00:00Z",)).fetchall()
    assert admitted == [("late",)]
    row = {"created_at": "2026-06-01T00:00:00Z", "received_at": ""}
    assert known_at(row, config) == "2026-06-01T00:00:00Z"
    assert not Cutoff.as_known_at("2026-05-05T09:00:00Z").admits(row["created_at"], row["received_at"])


# -- records -------------------------------------------------------------------------------------------------------


def _hypothesis_version(paths, *, id: str, written: str, version_delta: int = 1, status: str = "validated") -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection, connection:
        connection.row_factory = sqlite3.Row
        first = dict(connection.execute(
            "SELECT * FROM causal_hypotheses WHERE attempt_id = 'att_02_svd_fail' ORDER BY version LIMIT 1"
        ).fetchone())
        row = {**first, "id": id, "version": first["version"] + version_delta, "supersedes_id": first["id"],
               "status": status, "created_at": written}
        connection.execute(f"INSERT INTO causal_hypotheses ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                           list(row.values()))
    return first


def test_a_record_written_at_exactly_the_targets_completion_is_not_shown(tmp_path):
    paths = _history(tmp_path)
    target_time = iso(5)  # att_06's completion
    first = _hypothesis_version(paths, id="ch_at_completion", written=target_time)
    store = _store(paths)
    target = store.ref("att_06_svd_fail")
    cutoff = Cutoff.history_v1("att_06_svd_fail", target.completed_at)
    assert not cutoff.written_before(target_time)
    shown = {record.id for record in store.hypotheses_before(target, _lo_ids(store))}
    assert first["id"] in shown and "ch_at_completion" not in shown
    # A later version written one second earlier is the one shown (a causal hypothesis's version is read as of
    # then: the latest written before the cutoff).
    earlier = (at(5) - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    _hypothesis_version(paths, id="ch_before_completion", written=earlier, version_delta=2)
    assert cutoff.written_before(earlier)
    store = _store(paths)
    shown = {record.id for record in store.hypotheses_before(target, _lo_ids(store))}
    assert "ch_before_completion" in shown and first["id"] not in shown and "ch_at_completion" not in shown


def _lo_ids(store) -> list[str]:
    return sorted({attempt.learning_object_id for attempt in store.all_attempts()})


def _snapshot(store, target: str) -> dict[str, Any]:
    ref = store.ref(target)
    los = _lo_ids(store)
    return {
        "attempts": [(a.attempt_id, a.score, a.failed_criteria, a.passed_criteria) for a in store.attempts_before(ref)],
        "hypotheses": [(h.id, h.status, h.last_updated) for h in store.hypotheses_before(ref, los)],
        "registry": [(r.id, r.status, r.occurrence_count) for r in store.registry_before(ref, None)],
        "repairs": [(r.repair_class_id, r.hypothesis_ids, r.cold_successes, r.cold_failures)
                    for r in store.repairs_before(ref, None)],
    }


def test_a_delayed_read_equals_the_live_one_at_fixed_corrections(tmp_path):
    """What the target admits is fixed by the target: later attempts, records written later, a later causal
    version and a later learner mark leave the read of att_06 as it was. Only the receipt's lagged count (attempts
    after it) grows."""

    from tests.diagnosis_split_helpers import seed_attempt, transpose_error

    paths = _history(tmp_path)
    live_store = _store(paths)
    target = live_store.ref("att_06_svd_fail")
    live, live_lagged = _snapshot(live_store, "att_06_svd_fail"), live_store.lagged_attempts(target)
    # Later: a causal version and a cold verification written after att_06, and another attempt.
    _hypothesis_version(paths, id="ch_later", written=iso(7))
    _write(paths.sqlite_path,
           "INSERT INTO causal_cold_verifications (id, source_attempt_id, cold_attempt_id, repair_class_id, "
           "hypothesis_ids_json, source_surface_family, cold_surface_family, avoided_affordances_json, success, "
           "capability_update_json, diagnosis_support_update_json, repair_effect_support_json, created_at) "
           "VALUES ('ccv_late', 'att_02_svd_fail', 'att_03_svd_pass', 'rc_transpose', '[]', 'svd_compute', "
           "'svd_compute_b', '[]', 1, '{}', '{}', '{}', ?)", iso(7))
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    seed_attempt(load_vault(paths.root), Repository(paths.sqlite_path), attempt_id="att_08_svd_later",
                 item_id="pi_svd_compute_001", answer="A = U Sigma V once more", when=at(11),
                 points={"setup": 2, "result": 0}, error=transpose_error(quote="U Sigma V once more"))
    delayed_store = _store(paths)
    assert _snapshot(delayed_store, "att_06_svd_fail") == live
    assert delayed_store.lagged_attempts(delayed_store.ref("att_06_svd_fail")) == live_lagged + 1


def test_a_regrade_is_read_now_by_an_earlier_target(tmp_path):
    """Corrections now (``history_v1``): a regrade of att_02 written after att_06 changes att_02's criteria in
    att_06's history; nothing else in it moves."""

    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository

    paths = _history(tmp_path)
    before = _snapshot(_store(paths), "att_06_svd_fail")
    Repository(paths.sqlite_path).insert_regrade_evidence(
        attempt_id="att_02_svd_fail",
        new_evidence_rows=[{"id": "ge_regrade_result", "criterion_id": "result", "points_awarded": 2.0,
                            "evidence": "regraded", "notes": None, "agent_run_id": None, "local_grader_id": "test",
                            "grader_tier": 1, "created_at": iso(9)}],
        superseded_by_evidence_id="ge_regrade_result", supersede_tiers=(1,), clock=FrozenClock(at(9)))
    after = _snapshot(_store(paths), "att_06_svd_fail")
    changed = [(b, a) for b, a in zip(before["attempts"], after["attempts"], strict=True) if b != a]
    assert [(b[0], b[2], a[2]) for b, a in changed] == [("att_02_svd_fail", ("result",), ())]
    assert {key: value for key, value in after.items() if key != "attempts"} == {
        key: value for key, value in before.items() if key != "attempts"}
    assert Cutoff.history_v1("att_06_svd_fail", iso(5)).corrections == "now"


def test_a_hold_and_its_release_are_read_now(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    from tests.held_grade_evidence_helpers import _hold_by_regrade

    paths = _history(tmp_path)
    repository = Repository(paths.sqlite_path)
    before = dict((row[0], row[1]) for row in _snapshot(_store(paths), "att_06_svd_fail")["attempts"])
    assert before["att_03_svd_pass"] is not None
    _hold_by_regrade(load_vault(paths.root), repository, "att_03_svd_pass", at(8))
    held = dict((row[0], row[1]) for row in _snapshot(_store(paths), "att_06_svd_fail")["attempts"])
    assert held["att_03_svd_pass"] is None  # held, read now, though placed after att_06
    assert {k: v for k, v in held.items() if k != "att_03_svd_pass"} == {
        k: v for k, v in before.items() if k != "att_03_svd_pass"}
    # A later blind record without the hold releases it, again for every earlier target.
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.clock import FrozenClock

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items["pi_svd_compute_002"])
    repository.insert_blind_grade_record(
        attempt_id="att_03_svd_pass", agent_run_id=None, grading_prompt_version="blind-test",
        output_schema_version="BlindGradingProposal", context_hash="ctx-release",
        record={"practice_item_id": "pi_svd_compute_002", "rubric_score": 4, "max_points": rubric.max_points,
                "criteria": [], "error_attributions": [], "fatal_errors": [], "grading_support": {}},
        clock=FrozenClock(at(9)))
    released = dict((row[0], row[1]) for row in _snapshot(_store(paths), "att_06_svd_fail")["attempts"])
    assert released["att_03_svd_pass"] is not None


def test_a_mutable_status_is_read_now(tmp_path):
    """An unresolved factor's status changed after the target shows its current value in the target's history
    (no status history is read), beside its creation time as ``last_updated``: a pair that may never have
    coexisted, which ``as_known_at`` would report approximate (``unresolved_cause_factors.status``)."""

    paths = _history(tmp_path)
    _write(paths.sqlite_path,
           "INSERT INTO unresolved_cause_factors (id, attempt_id, candidate_causes_json, status, algorithm_version, "
           "created_at, updated_at) VALUES ('ucf_02', 'att_02_svd_fail', '[]', 'open', 'test', ?, ?)",
           iso(1.5), iso(1.5))
    store = _store(paths)
    los = _lo_ids(store)
    (before,) = [h for h in store.hypotheses_before(store.ref("att_06_svd_fail"), los) if h.id == "ucf_02"]
    assert (before.status, before.last_updated) == ("open", iso(1.5))
    _write(paths.sqlite_path, "UPDATE unresolved_cause_factors SET status = 'resolved', updated_at = ? "
           "WHERE id = 'ucf_02'", iso(9))
    store = _store(paths)
    (after,) = [h for h in store.hypotheses_before(store.ref("att_06_svd_fail"), los) if h.id == "ucf_02"]
    assert (after.status, after.last_updated) == ("resolved", iso(1.5))
    cutoff = Cutoff.as_known_at(iso(5), attempt_id="att_06_svd_fail", fields=("unresolved_cause_factors.status",))
    assert [entry.field for entry in cutoff.approximate] == ["unresolved_cause_factors.status"]


def test_the_planted_history_store_is_corrected_before(tmp_path):
    """``StaticHistoryStore`` orders attempts by ``(created_at, id)`` and admits those strictly before the target,
    with no known-time gate: the ``corrected_before`` preset."""

    from learnloop.diagnosis.split.history import StaticHistoryStore

    paths = _history(tmp_path)
    store = _store(paths)
    planted = StaticHistoryStore(attempts=store.all_attempts())
    rows = {row["id"]: row for row in _rows(paths.sqlite_path)}
    for attempt in planted.attempts:
        target = planted.ref(attempt.attempt_id)
        cutoff = Cutoff.corrected_before(target.attempt_id, target.completed_at)
        assert planted.cutoff(target) == cutoff
        expected = [a.attempt_id for a in planted.attempts
                    if cutoff.admits(a.completed_at, rows[a.attempt_id]["received_at"], attempt_id=a.attempt_id)]
        assert [a.attempt_id for a in planted.attempts_before(target)] == expected
        assert planted.lagged_attempts(target) == len(planted.attempts) - 1 - len(expected)


# -- adaptive difficulty and the field: equal-time inclusion ------------------------------------------------------


def test_ad_replay_and_field_rows_admit_an_attempt_at_exactly_as_of(tmp_path):
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.db.connection import connect
    from learnloop.db.repositories import Repository
    from learnloop.field.outcomes import load_attempt_rows
    from learnloop.vault.loader import load_vault

    from tests.ad23_fakes import ad23_vault, answer

    items = ("pi_a1", "pi_a2", "pi_a3")
    paths = ad23_vault(tmp_path, items=items)
    ids = [answer(paths, item) for item in items]
    stamps = ["2026-10-12T09:00:00Z", "2026-10-12T09:00:00Z", "2026-10-12T09:00:01Z"]
    for attempt_id, stamp in zip(ids, stamps, strict=True):
        _write(paths.sqlite_path, "UPDATE practice_attempts SET created_at = ? WHERE id = ?", stamp, attempt_id)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    for as_of in ("2026-10-12T08:59:59Z", "2026-10-12T09:00:00Z", "2026-10-12T09:00:00.5Z", "2026-10-12T09:00:01Z",
                  None):
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            events = RP.load_events(connection, vault, repository, as_of=as_of)
            field_rows = load_attempt_rows(connection, vault, as_of=as_of)
        ordered = sorted(zip(stamps, ids, strict=True))
        ad_expected = [i for stamp, i in ordered if Cutoff.ad_replay(as_of).admits(stamp)]
        field_expected = [i for stamp, i in ordered if Cutoff.completed_by(as_of).admits(stamp)]
        assert [event.attempt_id for event in events.attempts] == ad_expected, as_of
        assert [row.attempt_id for row in field_rows] == field_expected, as_of
    # Exactly at as_of is in for both; the two attempts of one second are both in.
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository, as_of="2026-10-12T09:00:00Z")
    assert sorted(event.attempt_id for event in events.attempts) == sorted(ids[:2])
