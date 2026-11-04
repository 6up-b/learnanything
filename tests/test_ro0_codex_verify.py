"""RO0's Codex verify (job ``20261104-165216-3b1KmL``) reopened F1 and F7; the landing's rulings R1 and R2 fix them.

R1: a receipt field added to an existing row is never written in that row's own insert. The row is inserted with its
predecessor's fields, and the receipt fields follow in their own savepoint; refused, the row stands with them null and a
warning. Codex's reproduction (a trigger refusing any insert that carries an RO0 column) is the test that fails on any RO0
column written in an existing table's insert; a trigger refusing the fill is the test that the pick, the answer and the
source opening succeed when the receipt is refused. Both at mvp-0.43, 0.44 and 0.45.

See ``docs/reviews/router-ro0-codex-review.md``, "Codex verify".
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from learnloop.algorithm_versions import (
    DATA_CAPTURE_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION,
)
from learnloop.clock import FrozenClock
from learnloop.daily_plan import measurement as M
from learnloop.daily_plan.engine import build_plan, learner_pick
from learnloop.db.repositories import Repository
from learnloop.db.stores import data_capture as capture_store
from learnloop.db.stores import plan_presentations as presentations
from learnloop.router_objective import cold_timing as CT
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime
from tests.test_data_capture_a2_measurement import _objectives, _picker, _reading_decision, _reading_env
from tests.test_question_context import FakeTutorClient

SRC = Path(__file__).resolve().parents[1] / "src"
VERSIONS = [LESSON_SUGGESTIONS_ALGORITHM_VERSION, DATA_CAPTURE_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION]
#: Every column RO0 writes on a table that existed before it: migration 242's eight, and the generating-process fields
#: (row 2 and row 3's ``question_opportunity``) RO0 now fills on the pending question.
RO0_COLUMNS: dict[str, tuple[str, ...]] = {
    "question_events": ("reveal_state_json", "hints_used_before", "scaffold_level", "preceding_tutor_move", "learner_mode",
                        "question_opportunity"),
    "plan_presentations": ("ask_available",),
    "source_exposure_events": ("initiator", "initiator_block_id", "initiator_session_id", "initiator_visit_id"),
    "decision_objectives": ("delay_json",),
    "decision_measurement_events": ("non_service_type", "delay_json"),
}
INSERT, FILL = "insert", "fill"
KEY = "workbench_admission:wbs_r1"


def _install(repository: Repository, mode: str) -> None:
    """``insert``: Codex's reproduction, an insert carrying any RO0 column is refused. ``fill``: the receipt is."""

    with repository.connection() as connection:
        for table, columns in RO0_COLUMNS.items():
            if mode == INSERT:
                for column in columns:
                    connection.execute(
                        f"CREATE TRIGGER refuse_insert_{table}_{column} BEFORE INSERT ON {table} "
                        f"WHEN NEW.{column} IS NOT NULL BEGIN SELECT RAISE(ABORT, 'an RO0 column in the insert'); END")
            else:
                connection.execute(
                    f"CREATE TRIGGER refuse_fill_{table} BEFORE UPDATE OF {', '.join(columns)} ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'the receipt refused'); END")
        connection.commit()


def _one(repository: Repository, sql: str, params: tuple = ()) -> dict:
    with repository.connection() as connection:
        row = connection.execute(sql, params).fetchone()
    assert row is not None, sql
    return dict(row)


def _refused(caplog) -> bool:
    return any("refused" in record.getMessage() for record in caplog.records)


# -- R1: the keyed pick -----------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", [INSERT, FILL])
@pytest.mark.parametrize("version", VERSIONS)
def test_r1_a_keyed_pick_stands_whatever_its_presentations_receipt_meets(tmp_path, caplog, version, mode):
    env = mixture_env(tmp_path, fake_runtime(), version=version)
    _install(env.repository, mode)
    plan = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    item = plan.items()[0].practice_item_id
    _record, step = learner_pick(env, item, idempotency_key=KEY)
    assert step["presentation_id"], "the keyed pick and its required presentation stand"
    row = _one(env.repository, "SELECT * FROM plan_presentations WHERE id = ?", (step["presentation_id"],))
    if mode == INSERT:
        assert row["ask_available"] == 1, "written after the row, not in its insert"
        assert not _refused(caplog)
    else:
        assert row["ask_available"] is None and _refused(caplog)


# -- R1: the answer ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", [INSERT, FILL])
@pytest.mark.parametrize("version", VERSIONS)
def test_r1_an_answer_stands_whatever_its_questions_receipt_meets(tmp_path, caplog, version, mode):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    _install(repository, mode)
    calls: list[int] = []

    class Counting(FakeTutorClient):
        def run_tutor_qa(self, context):
            calls.append(1)
            return super().run_tutor_qa(context)

    result = ask_question(vault, repository, Counting(), context="practice", question_md="Why?",
                          practice_item_id="pi_svd_define_001", session_id="s1", clock=FrozenClock(NOW),
                          question_context={"learner_mode": "work_in_steps"})
    event = repository.question_event(result["event_id"])
    assert calls == [1] and event["question_md"] == "Why?" and event["answer_md"], "the question and its answer stand"
    filled = {column: event[column] for column in RO0_COLUMNS["question_events"]}
    if mode == INSERT:
        assert event["reveal_state_json"] and event["hints_used_before"] == 0 and event["learner_mode"] == "work_in_steps"
        assert event["question_opportunity"] == "practice" and event["scaffold_level"] == "none"
        assert not _refused(caplog)
    else:
        assert set(filled.values()) == {None} and _refused(caplog)


# -- R1: the source opening ----------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", [INSERT, FILL])
@pytest.mark.parametrize("version", VERSIONS)
def test_r1_a_source_opening_stands_whatever_its_initiators_receipt_meets(tmp_path, caplog, version, mode):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers.provenance import SpanViewInput, get_span_view_handler
    from tests.helpers import seed_explanatory_source

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    seeded = seed_explanatory_source(vault.root, repository)
    session = repository.create_session()
    _install(repository, mode)
    ctx = SidecarContext()
    ctx.load(vault.root, maintenance=False)
    view = get_span_view_handler(ctx, SpanViewInput(extraction_id="ext_cited", span_id=seeded["span_id"], context="reader",
                                                    initiator="plan", block_id="b9", visit_id="v9"))
    assert view, "the opening's reply"
    rows = repository.source_exposure_events(extraction_id="ext_cited")
    assert len(rows) == 1 and rows[0]["context"] == "reader", "the opening and its coldness exposure stand"
    got = tuple(rows[0][column] for column in RO0_COLUMNS["source_exposure_events"])
    if mode == INSERT:
        assert got == ("plan", "b9", session, "v9") and not _refused(caplog)
    else:
        assert got == (None, None, None, None) and _refused(caplog)


# -- R1: a check's delay and an unserved check's type (data capture's tables, mvp-0.44 on) -------------------


@pytest.mark.parametrize("mode", [INSERT, FILL])
@pytest.mark.parametrize("version", [DATA_CAPTURE_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION])
def test_r1_an_arranged_check_keeps_its_objective_whatever_its_delay_meets(tmp_path, monkeypatch, caplog, version, mode):
    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"), version=version)
    _install(env.repository, mode)
    _reading_decision(env)
    arranged = [row for row in _objectives(env).values() if row["measurement"] == "arranged"]
    assert arranged, "the objective stands"
    stored = _one(env.repository, "SELECT delay_json FROM decision_objectives WHERE decision_id = ?",
                  (arranged[0]["decision_id"],))["delay_json"]
    if mode == INSERT:
        assert json.loads(stored)["version"] == CT.DELAY_VERSION and not _refused(caplog)
    else:
        assert stored is None and _refused(caplog)


@pytest.mark.parametrize("mode", [INSERT, FILL])
@pytest.mark.parametrize("version", [DATA_CAPTURE_ALGORITHM_VERSION, LATEST_ALGORITHM_VERSION])
def test_r1_an_unserved_check_keeps_its_state_whatever_its_type_meets(tmp_path, monkeypatch, caplog, version, mode):
    env = _reading_env(tmp_path, monkeypatch, choice=_picker("reading", "new:"), los=("lo_with_no_item",), version=version)
    monkeypatch.setattr(M.D, "candidates", lambda *_args, **_kwargs: [])
    _install(env.repository, mode)
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    _reading_decision(env)
    with env.repository.connection() as connection:
        rows = connection.execute(
            "SELECT reason, non_service_type FROM decision_measurement_events WHERE state = 'unavailable'").fetchall()
    assert rows, "the unavailable state stands"
    if mode == INSERT:
        assert all(row[1] == CT.non_service_type(row[0]) for row in rows) and not _refused(caplog)
    else:
        assert all(row[1] is None for row in rows) and _refused(caplog)


# -- R1: every writer, at the store ------------------------------------------------------------------------


def _parents(connection) -> None:
    connection.execute(
        "INSERT INTO router_decisions(id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, log_version, "
        "snapshot_hash, candidates_json, exclusions_json, candidate_count, propensity_kind, detail_json, created_at) "
        "VALUES ('d1', 'k1', 'plan_block', 'plan', 'live', 'rule', 'v', 'l', 'h', '[]', '[]', 0, 'not_served', '{}', "
        "'2026-11-04T10:00:00Z')")
    connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                       "VALUES ('b1', 'practice', 5, 'h', '2026-11-04T10:00:00Z')")


def _store_rows(repository: Repository) -> None:
    """Each writer of a table RO0 extends, called once with its RO0 fields."""

    repository.insert_question_event({"id": "q1", "context": "practice", "practice_item_id": "pi_svd_define_001",
                                      "question_md": "Q", "reveal_state_json": "{}", "hints_used_before": 2,
                                      "scaffold_level": "1", "preceding_tutor_move": "none", "learner_mode": "work_in_steps",
                                      "question_opportunity": "practice"})
    repository.insert_source_exposure_event({"id": "x1", "context": "reader", "extraction_id": "e1", "span_id": "s1",
                                             "initiator": "plan", "initiator_block_id": "b1", "initiator_session_id": "s1",
                                             "initiator_visit_id": "v1"})
    with repository.atomic(), repository.connection() as connection:
        _parents(connection)
        presentations.insert_plan_presentation(connection, {
            "id": "p1", "block_id": "b1", "practice_item_id": "pi_svd_define_001", "origin": "chooser",
            "served_at": "2026-11-04T10:00:00Z", "ask_available": 1})
        assert capture_store.insert_objective(connection, {
            "decision_id": "d1", "decision_kind": "plan_block", "objective_version": "o", "source": "s", "scope_json": "{}",
            "arm": "a", "support_json": "{}", "measurement": "arranged", "pick_json": "{}", "created_at": "2026-11-04T10:00:00Z",
            "delay_json": '{"days": 3}'})
        assert capture_store.insert_measurement_event(connection, decision_id="d1", state="unavailable", reason="no_question",
                                                      at="2026-11-04T10:00:00Z", non_service_type="structurally_refused",
                                                      delay='{"days": 3}')


def _store_values(repository: Repository) -> dict[str, tuple]:
    keys = {"question_events": ("id", "q1"), "plan_presentations": ("id", "p1"), "source_exposure_events": ("id", "x1"),
            "decision_objectives": ("decision_id", "d1"), "decision_measurement_events": ("decision_id", "d1")}
    out = {}
    with repository.connection() as connection:
        for table, (key, value) in keys.items():
            row = connection.execute(f"SELECT {', '.join(RO0_COLUMNS[table])} FROM {table} WHERE {key} = ?", (value,)).fetchone()
            assert row is not None, f"{table}: the row stands"
            out[table] = tuple(row)
    return out


def test_r1_no_writer_puts_an_ro0_column_in_its_rows_insert(tmp_path, caplog):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _install(repository, INSERT)
    _store_rows(repository)
    assert _store_values(repository) == {
        "question_events": ("{}", 2, "1", "none", "work_in_steps", "practice"),
        "plan_presentations": (1,),
        "source_exposure_events": ("plan", "b1", "s1", "v1"),
        "decision_objectives": ('{"days": 3}',),
        "decision_measurement_events": ("structurally_refused", '{"days": 3}'),
    }, "every receipt field arrives, after its row"
    assert not _refused(caplog)


def test_r1_every_writer_leaves_its_row_standing_when_the_receipt_is_refused(tmp_path, caplog):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _install(repository, FILL)
    _store_rows(repository)
    values = _store_values(repository)
    assert all(set(found) == {None} for found in values.values()), values
    assert sum("refused" in record.getMessage() for record in caplog.records) == len(RO0_COLUMNS)


_INSERT_RE = re.compile(r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)", re.IGNORECASE)


def test_r1_these_five_writers_are_the_only_inserts_into_the_tables_ro0_extends():
    found = set()
    for path in sorted(SRC.rglob("*.py")):
        for table in _INSERT_RE.findall(path.read_text(encoding="utf-8")):
            if table in RO0_COLUMNS:
                found.add((str(path.relative_to(SRC)), table))
    assert found == {
        ("learnloop/db/repositories.py", "question_events"),
        ("learnloop/db/repositories.py", "source_exposure_events"),
        ("learnloop/db/stores/plan_presentations.py", "plan_presentations"),
        ("learnloop/db/stores/data_capture.py", "decision_objectives"),
        ("learnloop/db/stores/data_capture.py", "decision_measurement_events"),
    }, "a new writer must follow R1 and join the store-level tests above"


# -- R1: the append-only tables allow exactly the fill -------------------------------------------------------


_APPEND_ONLY = ("plan_presentations", "decision_objectives", "decision_measurement_events")


def test_r1_an_append_only_tables_trigger_names_every_column_it_holds(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with Repository(paths.sqlite_path).connection() as connection:
        for table in _APPEND_ONLY:
            sql = connection.execute("SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
                                     (f"{table}_no_update",)).fetchone()[0]
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
            missing = [column for column in columns if not re.search(rf"\bOLD\.{column}\b", sql)]
            assert not missing, f"{table}: a column the update guard does not name: {missing}"


def test_r1_the_append_only_tables_refuse_every_update_but_the_one_fill(tmp_path):
    import sqlite3

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _store_rows_without_receipts(repository)
    with repository.connection() as connection:
        refused = [
            "UPDATE plan_presentations SET origin = 'x' WHERE id = 'p1'",
            "UPDATE plan_presentations SET ask_available = 1, origin = 'x' WHERE id = 'p1'",
            "UPDATE decision_objectives SET arm = 'x' WHERE decision_id = 'd1'",
            "UPDATE decision_objectives SET delay_json = '{}', arm = 'x' WHERE decision_id = 'd1'",
            "UPDATE decision_measurement_events SET reason = 'x' WHERE decision_id = 'd1'",
            "UPDATE decision_measurement_events SET delay_json = '{}', reason = 'x' WHERE decision_id = 'd1'",
        ]
        for sql in refused:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(sql)
        for sql in ("UPDATE plan_presentations SET ask_available = 0 WHERE id = 'p1'",
                    "UPDATE decision_objectives SET delay_json = '{}' WHERE decision_id = 'd1'",
                    "UPDATE decision_measurement_events SET non_service_type = 'policy_refused', delay_json = '{}' "
                    "WHERE decision_id = 'd1'"):
            connection.execute(sql)
        for sql in ("UPDATE plan_presentations SET ask_available = 1 WHERE id = 'p1'",
                    "UPDATE decision_objectives SET delay_json = '{\"a\": 1}' WHERE decision_id = 'd1'",
                    "UPDATE decision_measurement_events SET non_service_type = 'learner_declined' WHERE decision_id = 'd1'",
                    "DELETE FROM plan_presentations WHERE id = 'p1'"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(sql)
        connection.rollback()


def _store_rows_without_receipts(repository: Repository) -> None:
    with repository.atomic(), repository.connection() as connection:
        _parents(connection)
        presentations.insert_plan_presentation(connection, {
            "id": "p1", "block_id": "b1", "practice_item_id": "pi_svd_define_001", "origin": "chooser",
            "served_at": "2026-11-04T10:00:00Z"})
        capture_store.insert_objective(connection, {
            "decision_id": "d1", "decision_kind": "plan_block", "objective_version": "o", "source": "s", "scope_json": "{}",
            "arm": "a", "support_json": "{}", "measurement": "arranged", "pick_json": "{}", "created_at": "2026-11-04T10:00:00Z"})
        capture_store.insert_measurement_event(connection, decision_id="d1", state="unavailable", reason="no_question",
                                               at="2026-11-04T10:00:00Z")
