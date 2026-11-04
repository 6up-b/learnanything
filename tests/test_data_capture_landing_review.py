"""Data capture A1-A6: the final verify's two findings, each reproduced first (landing ruling R1).

F1 reopened: an answer's label depended on whether Today had swept the Reader's activity. Monday's practice, Wednesday
10:00's completed section, 10:30's correct answer read ``observed`` 1.0 before a sweep and ``pending`` after one, so a
report or a rebuild brought back the false cold label. F11: a broad check on A and B, answered on B, closed A's measurement.
Fakes only; no network.
"""

from __future__ import annotations

import ast
from datetime import timedelta
import hashlib
import json
from pathlib import Path

from learnloop import delayed_completion as DC
from learnloop.curriculum import commitments as C
from learnloop.daily_plan import measurement as M
from learnloop.data_capture import reading_exposures as RE
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import data_capture as store
from learnloop.ops import capture_report as CR
from learnloop.router import outcomes as RO
from learnloop.router.first_delayed_success import trajectories
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.test_data_capture_a2_measurement import _answer, _arranged_wait, _due_measurement, _events, _objectives
from tests.test_data_capture_codex_rereview import _complete_section, _count, _map_sections, _other_item
from tests.test_data_capture_codex_review import _warm_answer
from tests.test_router_g4_restraint import DECIDER_ONLY

AD_OFF = "[adaptive_difficulty]\nenabled = false\n"
ROOT = Path(__file__).resolve().parent.parent


def _in_session(env, item, lo, session, *, correctness=1.0):
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type,"
            " hints_used, correctness, manual_review, created_at, session_id, primed, evidence_origin)"
            " VALUES (?,?,?,?,?,0,?,0,?,?,0,'human')",
            (f"att_{item}_{env.now_iso()}", item, lo, "short_answer", "independent_attempt", correctness, env.now_iso(), session))
        connection.commit()


def _monday_wednesday(tmp_path, monkeypatch, *, read=True):
    """Monday's practice in one session, Wednesday 10:00's section (when ``read``), and 10:30's correct answer in another."""

    env, decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _map_sections(monkeypatch, lo)
    env.clock.advance(1)
    _in_session(env, _other_item(env, objective), lo, "monday", correctness=0.4)
    env.clock.instant = env.clock.instant + timedelta(days=2)
    if read:
        _complete_section(env)
    env.clock.advance(30)
    _in_session(env, objective["practice_item_id"], lo, "wednesday")
    env.clock.advance(1)
    return env, decision_id, objective


def _derive(env):
    with env.repository.connection() as connection:
        return {row["decision_id"]: row for row in RO.derive_router_outcomes(
            connection, outcome_version=RO.OUTCOME_VERSION_V3,
            reader_exposures=RE.read(connection, env.vault, env.repository))}


def _metric(env, lo):
    with env.repository.connection() as connection:
        found, _facts = trajectories(connection, env.vault, success_correctness=0.8, as_of=env.now_iso(),
                                     reader_exposures=RE.read(connection, env.vault, env.repository))
    return next(row for row in found if row.learning_object_id == lo)


def _warm_completion(env, objective, decision_id):
    with env.repository.connection() as connection:
        attempt = connection.execute("SELECT id FROM practice_attempts WHERE session_id = 'wednesday'").fetchone()[0]
        decided = connection.execute("SELECT created_at FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()[0]
        return RO.answer_completion(connection, attempt, decided_at=decided,
                                    reader_exposures=RE.read(connection, env.vault, env.repository))


# -- F1: one read ---------------------------------------------------------------------------------------------------


def test_f1_the_warm_answer_is_not_delayed_with_no_sweep_having_run(tmp_path, monkeypatch):
    """Reproduced first: ``observed`` 1.0 and a first delayed success before the sweep, ``pending`` after it."""

    env, decision_id, objective = _monday_wednesday(tmp_path, monkeypatch)
    assert not env.vault.config.adaptive_difficulty.enabled and _count(env, "reading_exposure_receipts") == 0
    assert _warm_completion(env, objective, decision_id).status == DC.NOT_DELAYED
    outcome = _derive(env)[decision_id]
    assert outcome["r_cold_status"] == "pending" and outcome["r_cold_value"] is None
    assert not _metric(env, objective["learning_object_id"]).reached
    assert _count(env, "reading_exposure_receipts") == 0, "the read writes nothing"


def test_f1_with_no_section_read_the_same_answer_is_the_cold_success(tmp_path, monkeypatch):
    """The other side of the same case, so the test above is about the reading."""

    env, decision_id, objective = _monday_wednesday(tmp_path, monkeypatch, read=False)
    assert _warm_completion(env, objective, decision_id).status == DC.COMPLETED
    assert _derive(env)[decision_id]["r_cold_status"] == "observed"
    assert _metric(env, objective["learning_object_id"]).reached


def test_f1_derivation_metric_and_report_read_the_same_before_and_after_the_sweep(tmp_path, monkeypatch):
    env, decision_id, objective = _monday_wednesday(tmp_path, monkeypatch)
    lo = objective["learning_object_id"]

    def everything():
        with env.repository.connection() as connection:
            section = CR.outcome_section(connection, env.vault, env.repository)
            exposures = RE.read(connection, env.vault, env.repository)
            time = CR.time_section(connection, env.vault, env.repository, as_of=env.now_iso(), success_correctness=0.8)
        for volatile in ("reading_exposure_receipts", "reader_exposures_not_yet_swept"):
            section.pop(volatile)
        return exposures, _derive(env), _metric(env, lo), section, time

    before = everything()
    with env.repository.connection() as connection:
        assert len(RE.not_yet_swept(connection, env.vault, env.repository)) == 1
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    with env.repository.connection() as connection:
        assert RE.not_yet_swept(connection, env.vault, env.repository) == []
    after = everything()
    assert before == after


def test_f1_the_report_says_what_is_on_record_and_what_is_not_yet(tmp_path, monkeypatch):
    env, _decision_id, _objective = _monday_wednesday(tmp_path, monkeypatch)
    with env.repository.connection() as connection:
        section = CR.outcome_section(connection, env.vault, env.repository)
    assert section["reading_exposure_receipts"] == 0 and section["reader_exposures_not_yet_swept"] == 1


def test_f1_a_rebuild_with_no_sweep_cannot_bring_back_the_cold_label(tmp_path, monkeypatch):
    env, decision_id, _objective = _monday_wednesday(tmp_path, monkeypatch)
    rebuild_all_derived_state(env.vault, env.repository, clock=env.clock, require_complete_attempt_coverage=False)
    with env.repository.connection() as connection:
        row = dict(connection.execute("SELECT * FROM router_outcomes WHERE decision_id = ?", (decision_id,)).fetchone())
    assert row["r_cold_status"] == "pending" and row["r_cold_value"] is None
    assert _count(env, "reading_exposure_receipts") == 0, "a rebuild freezes nothing"


def test_f1_settle_judges_the_answer_by_the_read_when_the_sweep_failed(tmp_path, monkeypatch):
    env, decision_id, objective = _monday_wednesday(tmp_path, monkeypatch, read=False)
    # Past the check's date, answered the half hour after a section no sweep recorded.
    env.clock.instant = env.clock.instant + timedelta(days=30)
    _complete_section(env)
    env.clock.advance(30)
    _in_session(env, objective["practice_item_id"], objective["learning_object_id"], "later")
    env.clock.advance(1)
    monkeypatch.setattr(RE, "sweep_quietly", lambda *_a, **_k: 0)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert "answered" not in {event["state"] for event in events}
    assert M.ANSWER_NOT_DELAYED in {event["reason"] for event in events}


def test_f1_an_answer_waits_when_the_read_cannot_judge_it(tmp_path, monkeypatch):
    env, decision_id, objective = _due_measurement(tmp_path)
    _in_session(env, objective["practice_item_id"], objective["learning_object_id"], "later")
    env.clock.advance(1)

    def boom(*_args, **_kwargs):
        raise RuntimeError("unreadable")

    monkeypatch.setattr(RE, "read", boom)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "answered" not in {event["state"] for event in _events(env)[decision_id]}
    monkeypatch.undo()
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "answered" in {event["state"] for event in _events(env)[decision_id]}


def test_f1_activity_stamped_long_before_the_newest_receipt_is_read_though_the_sweep_leaves_it(tmp_path, monkeypatch):
    """A row stamped past the sweep's overlap, committed after a later row was swept: the read has it either way."""

    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _map_sections(monkeypatch, lo)
    old = env.now_iso()
    env.clock.instant = env.clock.instant + timedelta(days=5)
    _complete_section(env, section="new")
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("INSERT INTO reader_section_progress(extraction_id, section_id, completed_at, updated_at)"
                           " VALUES ('x', 'late', ?, ?)", (old, old))
    with env.repository.connection() as connection:
        assert [at[:19] for _lo, at in RE.not_yet_swept(connection, env.vault, env.repository)] == [old[:19]]
        before = RE.read(connection, env.vault, env.repository)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0, "past the sweep's window (R6)"
    with env.repository.connection() as connection:
        assert RE.read(connection, env.vault, env.repository) == before, "the live read still has it"


def test_f1_a_section_no_lo_named_until_later_reads_the_same_swept_or_not(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    monkeypatch.setattr(RE, "_section_los", lambda *_a: [])
    _complete_section(env)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0, "no LO yet: nothing to record"
    _map_sections(monkeypatch, objective["learning_object_id"])
    RE._clear_mapping_cache()  # the vault's content changed, in the real thing
    env.clock.instant = env.clock.instant + timedelta(days=5)
    with env.repository.connection() as connection:
        assert len(RE.not_yet_swept(connection, env.vault, env.repository)) == 1
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1


def test_f1_the_read_is_read_only_under_a_read_only_repository(tmp_path, monkeypatch):
    env, _decision_id, objective = _monday_wednesday(tmp_path, monkeypatch)
    path = env.repository.sqlite_path

    def digest():
        with connect(path) as connection:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    before = digest()
    repository = Repository.attach(path, read_only=True)
    connection = connect(path, read_only=True)
    try:
        exposures = RE.read(connection, env.vault, repository)
    finally:
        connection.close()
    assert [lo for lo, _at in exposures] == [objective["learning_object_id"]]
    assert digest() == before


def test_f1_below_the_receipts_table_the_read_is_activity_alone(tmp_path, monkeypatch):
    env, _decision_id, objective = _monday_wednesday(tmp_path, monkeypatch)
    monkeypatch.setattr(store, "reading_exposures_present", lambda _connection: False)
    with env.repository.connection() as connection:
        assert [lo for lo, _at in RE.not_yet_swept(connection, env.vault, env.repository)] == [objective["learning_object_id"]]


def test_f1_for_version_reads_only_at_version_3(tmp_path, monkeypatch):
    env, _decision_id, _objective = _monday_wednesday(tmp_path, monkeypatch)
    with env.repository.connection() as connection:
        assert RE.for_version(connection, env.vault, env.repository, RO.OUTCOME_VERSION) is None
        assert RE.for_version(connection, env.vault, env.repository, RO.OUTCOME_VERSION_V3)


def test_f1_every_production_derivation_passes_the_read():
    """A caller that forgets falls back to the stored receipts alone: the false cold label, quietly. So each names it."""

    names = {"derive_router_outcomes", "rebuild_router_outcomes", "trajectories", "answer_completion"}
    found: list[str] = []
    for path in (ROOT / "src" / "learnloop").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", getattr(node.func, "attr", None))
                if name in names and node.args:
                    found.append(path.name)
                    assert any(keyword.arg == "reader_exposures" for keyword in node.keywords), f"{path}:{node.lineno}"
    # The caller list, so a renamed function can't empty this test.
    assert {"capture_report.py", "router.py", "router_retrieval.py", "measurement.py", "scoreboard.py",
            "rebuild_orchestrator.py"} <= set(found)


# -- F11: a shared check measures the frozen objective ---------------------------------------------------------------


def _other_lo_item(env, lo):
    return next(item for item in env.vault.practice_items.values() if item.learning_object_id != lo)


def _broad_check(env, items, *, days=30):
    return C.create_commitment(
        env.repository, action="test_me_later", intent_text="check once, broad",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item, "role": "required"} for item in items],
        depth_preset="keep_in_touch", client_idempotency_key=f"broad:{sorted(items)}",
        due_hint=(env.clock.now() + timedelta(days=days)).date().isoformat(), reason="test", provenance={}, clock=env.clock,
    ).id


def test_f11_a_warm_answers_replacement_never_shares_a_check_that_b_can_answer(tmp_path):
    """Reproduced first: the broad check was shared, and B's answer wrote ``answered`` on A's measurement."""

    env, decision_id, objective = _due_measurement(tmp_path)
    lo = objective["learning_object_id"]
    other = _other_lo_item(env, lo)
    mine = _other_item(env, objective)
    broad = _broad_check(env, [mine, other.id])
    _warm_answer(env, objective, warm_item=mine)
    M.settle(env.vault, env.repository, clock=env.clock)
    early = next(event for event in _events(env)[decision_id] if event["reason"] == M.ANSWER_NOT_DELAYED)
    replacement = json.loads(early["detail_json"])["replacement_commitment_id"]
    assert replacement and replacement != broad
    env.clock.instant = env.clock.instant + timedelta(days=45)
    _answer(env, other.id, other.learning_object_id)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "answered" not in {event["state"] for event in _events(env)[decision_id]}, "B's answer measures nothing of A"


def test_f11_a_new_decision_never_shares_a_check_that_b_can_answer(tmp_path):
    env, _first_id, objective = _arranged_wait(tmp_path)
    lo = objective["learning_object_id"]
    other = _other_lo_item(env, lo)
    broad = _broad_check(env, [_other_item(env, objective), other.id])
    env.clock.advance(1)
    with env.repository.atomic(), env.repository.connection() as connection:
        arranged = M._arrange(env.vault, env.repository, M.freeze_followup(lo, support=["insert_now", "continue_current"]),
                              decision_id="d9", exclude=(), clock=env.clock)
    assert arranged.commitment_id != broad


def test_f11_a_check_wholly_on_the_objective_is_still_shared(tmp_path):
    env, _first_id, objective = _arranged_wait(tmp_path)
    lo = objective["learning_object_id"]
    with env.repository.atomic():
        arranged = M._arrange(env.vault, env.repository, M.freeze_followup(lo, support=["insert_now", "continue_current"]),
                              decision_id="d9", exclude=(), clock=env.clock)
    assert arranged.measurement == M.SHARED and arranged.commitment_id == objective["commitment_id"]


def _shared_broad_answered_on_b(tmp_path):
    """A check that named A's item when it was shared, and later B's too (its other target's commitment closed)."""

    env, decision_id, objective = _due_measurement(tmp_path)
    lo = objective["learning_object_id"]
    other = _other_lo_item(env, lo)
    broad = _broad_check(env, [_other_item(env, objective), other.id], days=1)
    return env, decision_id, objective, broad, other


def test_f11_an_answer_on_another_objective_never_records_answered_and_the_duty_stays(tmp_path):
    env, decision_id, objective, broad, other = _shared_broad_answered_on_b(tmp_path)
    # Recorded as it would be had it been shared before B joined: the settle-time check is what stands here.
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("DROP TRIGGER decision_objectives_no_update")
        connection.execute("UPDATE decision_objectives SET commitment_id = ? WHERE decision_id = ?", (broad, decision_id))
    env.clock.instant = env.clock.instant + timedelta(days=5)
    _answer(env, other.id, other.learning_object_id)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert "answered" not in {event["state"] for event in events}
    lost = next(event for event in events if event["reason"] == M.ANSWER_OTHER_OBJECTIVE)
    detail = json.loads(lost["detail_json"])
    assert lost["state"] == "unavailable" and detail["replacement_commitment_id"], "one replacement carries the duty"
    assert detail["answered_learning_object_id"] == other.learning_object_id
    assert RO.measurement_state(_objectives(env)[decision_id], events)["state"] == "scheduled"
    # That replacement, answered on the objective after its date, is the measurement.
    env.clock.instant = env.clock.instant + timedelta(days=60)
    lo = objective["learning_object_id"]
    _in_session(env, detail["practice_item_id"], lo, "much_later")
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "answered" in {event["state"] for event in _events(env)[decision_id]}


# -- the sweep on the foreground path (final scoped verify, finding 1, ruling R6) -------------------------------------


def _unmapped_sections(env, count, *, at=None):
    with env.repository.atomic(), env.repository.connection() as connection:
        for index in range(count):
            connection.execute(
                "INSERT INTO reader_section_progress(extraction_id, section_id, completed_at, updated_at) VALUES (?,?,?,?)",
                ("x", f"unmapped{index}", at or env.now_iso(), at or env.now_iso()))


def _count_mappings(monkeypatch):
    calls = {"sections": 0, "spans": 0}

    def section(*_args, **_kwargs):
        calls["sections"] += 1
        return []

    def span(*_args, **_kwargs):
        calls["spans"] += 1
        return []

    monkeypatch.setattr("learnloop.section_map.learning_objects_for_section", section)
    monkeypatch.setattr("learnloop.section_map.learning_objects_for_span", span)
    return calls


def test_r6_a_repeat_sweep_with_nothing_new_makes_no_mapping_call(tmp_path, monkeypatch):
    """Reproduced first: 100 mapping calls on every sweep of 100 unmapped sections, with no receipt written."""

    env, _decision_id, _objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    _unmapped_sections(env, 100)
    calls = _count_mappings(monkeypatch)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    assert calls["sections"] == 100, "the first look maps them"
    calls["sections"] = 0
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    assert calls == {"sections": 0, "spans": 0}, "a repeat maps nothing, empty results included"


def test_r6_the_cached_mapping_follows_coverage_and_content(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _complete_section(env)
    calls = _count_mappings(monkeypatch)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0 and calls["sections"] == 1
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0 and calls["sections"] == 1
    _name_on_coverage(env, lo)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1, "a coverage row is a new revision"
    assert calls["sections"] == 2
    # The vault's content is a revision too. (That one section is on record now, so another asks.)
    _complete_section(env, section="other")
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0 and calls["sections"] == 3
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0 and calls["sections"] == 3
    env.vault.learning_objects[lo].status = "archived"
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0 and calls["sections"] == 4


def test_r6_with_receipts_on_record_the_window_leaves_old_unmapped_sections_alone_in_a_new_process(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _unmapped_sections(env, 100, at=env.now_iso())
    env.clock.instant = env.clock.instant + timedelta(days=5)
    _complete_section(env, section="named")
    monkeypatch.setattr(RE, "_section_los", lambda _vault, _repo, _extraction, section: [lo] if section == "named" else [])
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    RE._clear_mapping_cache()
    monkeypatch.undo()
    calls = _count_mappings(monkeypatch)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    assert calls == {"sections": 0, "spans": 0}


def test_r6_the_foreground_read_does_not_list_the_whole_history(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _unmapped_sections(env, 100, at=env.now_iso())
    env.clock.instant = env.clock.instant + timedelta(days=5)
    _complete_section(env, section="named")
    monkeypatch.setattr(RE, "_section_los", lambda _vault, _repo, _extraction, section: [lo] if section == "named" else [])
    RE.sweep(env.vault, env.repository, clock=env.clock)
    RE._clear_mapping_cache()
    monkeypatch.undo()
    calls = _count_mappings(monkeypatch)
    with env.repository.connection() as connection:
        found = RE.read(connection, env.vault, env.repository, since=RE.recent_since(connection))
    assert calls == {"sections": 0, "spans": 0} and [row[0] for row in found] == [lo]


def test_r6_a_transient_mapping_failure_is_not_cached_as_empty(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _complete_section(env)

    def boom(*_args, **_kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(RE, "_section_los", boom)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    monkeypatch.setattr(RE, "_section_los", lambda *_a: [lo])
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1


def test_r6_a_sweep_with_nothing_to_write_takes_no_write_lock(tmp_path, monkeypatch):
    env, _decision_id, _objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    opened = []
    real = env.repository.atomic

    def counted():
        opened.append(1)
        return real()

    monkeypatch.setattr(env.repository, "atomic", counted)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    assert not opened


def _name_on_coverage(env, lo, *, extraction="x", section="sec"):
    connection = connect(env.repository.sqlite_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")  # the row's judgment is not what this reads
        connection.execute(
            "INSERT INTO section_coverage(id, extraction_id, section_id, learning_object_id, treatment, origin, section_hash,"
            " lo_hash, state_key, ledger_id, model, prompt_version, created_at)"
            " VALUES (?,?,?,?, 'develops', 'retrieval', 'h', 'h', 'k', 'l', 'm', 'v', ?)",
            (f"cov_{lo}_{env.now_iso()}", extraction, section, lo, env.now_iso()))
        connection.commit()
    finally:
        connection.close()


# -- a recorded LO does not hide one coverage names later (final scoped verify, finding 2) -------------------------------


def test_finding2_coverage_named_after_the_sweep_is_an_exposure_too(tmp_path, monkeypatch):
    """Sol's case. Reproduced first: ``completed``, an observed cold outcome, and a first delayed success on B."""

    env, decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    b = objective["learning_object_id"]
    a = next(lo for lo in env.vault.learning_objects if lo != b)
    env.clock.advance(1)
    _in_session(env, _other_item(env, objective), b, "monday", correctness=0.4)
    env.clock.instant = env.clock.instant + timedelta(days=2)
    monkeypatch.setattr(RE, "_section_los", lambda *_a: [a])
    _complete_section(env)
    env.clock.advance(5)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    env.clock.advance(10)
    _name_on_coverage(env, b)
    env.clock.advance(15)
    _in_session(env, objective["practice_item_id"], b, "wednesday")
    env.clock.advance(1)
    assert _warm_completion(env, objective, decision_id).status == DC.NOT_DELAYED
    assert _derive(env)[decision_id]["r_cold_status"] == "pending"
    assert not _metric(env, b).reached
    before = _derive(env)
    RE.sweep(env.vault, env.repository, clock=env.clock)
    assert _derive(env) == before
