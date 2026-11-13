"""Refactor B1 (ADR-017): the decision record, the trace id and the read-only ``why``.

What each group pins:

* the record: written with its id, trace and time filled in; never raising, whatever goes wrong (a prose value,
  an unknown status, a vault below migration 253, a read-only connection), and leaving the caller's transaction as
  it was; holding ids, numbers and codes only (item text planted from the head fixture is refused); append-only;
* the trace: born per sidecar RPC, phone request, MCP tool call and CLI command; carried by copied contexts and
  onto every model call's receipt and every sidecar log event; a post-attempt job gets its own;
* replay: no rebuild, replay or upgrade path reads ``decision_records`` (the import closure and the SQL), the store
  is outside that closure, and a live rebuild neither calls the record's functions nor touches its rows;
* ``why``: a pure read (no state sync, no maintenance, the database unchanged; fail-first: it synced and ran
  maintenance before B1), answering a trace, a record, a subject and ``latest`` from the records and the trace's
  model calls, joined by ``trace_id``.
"""

from __future__ import annotations

import ast
import contextvars
import importlib
import hashlib
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.provenance import DecisionRecord
from tests.helpers import MIGRATION_HEAD_FIXTURE, create_basic_vault
from tests.helpers import allow_below_floor

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture()
def head_db(tmp_path: Path) -> Path:
    root = tmp_path / "head"
    copy_tree_with_databases(MIGRATION_HEAD_FIXTURE, root, database_names=("state.sqlite",))
    allow_below_floor(root)
    return root / "state.sqlite"


def _rows(path: Path, table: str = "decision_records") -> list[tuple]:
    with connect(path, read_only=True) as connection:
        return [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY created_at, id")]


def _write(path: Path, record: DecisionRecord) -> str | None:
    connection = connect(path)
    try:
        written = provenance.write(connection, record)
        connection.commit()
        return written
    finally:
        connection.close()


# -- the leaf ------------------------------------------------------------------------------------------------


def test_provenance_imports_nothing_of_learnloop_but_the_ids():
    tree = ast.parse((SRC / "learnloop" / "provenance.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported |= {node.module} | {f"{node.module}.{alias.name}" for alias in node.names}
    assert {name for name in imported if name.startswith("learnloop")} == {"learnloop", "learnloop.ids"}


# -- the record ----------------------------------------------------------------------------------------------


def test_a_record_is_written_with_its_id_trace_and_time_filled_in(head_db: Path):
    with provenance.trace_scope("TRACE_ONE"):
        record_id = _write(head_db, DecisionRecord(
            kind="plan_block", status="fallback", subject_kind="block", subject_id="blk_1", chosen_ref="item:pi_a",
            decided_by="mixture", rule="chooser_error", alternatives=[{"ref": "item:pi_b", "p": 0.25}],
            facts={"timeout_s": 8, "waited_ms": 8012}, versions={"algorithm_version": "mvp-0.57"},
            detail_table="router_decisions", detail_id="rd_1", error_type="TimeoutError",
            error_where="learnloop.daily_plan.router_runtime:wait:605",
        ))
    assert record_id
    (read,) = provenance.read(connect(head_db, read_only=True), record_id)
    assert read.id == record_id and read.trace_id == "TRACE_ONE" and read.created_at
    assert read.as_dict()["alternatives"] == [{"ref": "item:pi_b", "p": 0.25}]
    assert read.facts == {"timeout_s": 8, "waited_ms": 8012} and read.versions == {"algorithm_version": "mvp-0.57"}
    assert (read.kind, read.status, read.rule, read.detail_table) == (
        "plan_block", "fallback", "chooser_error", "router_decisions")


def test_a_record_outside_every_trace_gets_a_trace_of_its_own(head_db: Path):
    assert provenance.current_trace() is None
    first = _write(head_db, DecisionRecord(kind="slate", status="chosen"))
    second = _write(head_db, DecisionRecord(kind="slate", status="chosen"))
    traces = {row[1] for row in _rows(head_db)}
    assert first and second and len(traces) == 2 and None not in traces


@pytest.mark.parametrize("bad", [
    DecisionRecord(kind="plan_block", status="chosen", facts={"why": "the learner wrote this sentence"}),
    DecisionRecord(kind="plan_block", status="chosen", rule="no measured latency"),
    DecisionRecord(kind="plan_block", status="chosen", alternatives=[{"ref": "x", "text": "a b"}]),
    DecisionRecord(kind="plan_block", status="chosen", facts={"p": float("nan")}),
    DecisionRecord(kind="plan_block", status="chosen", facts={"a sentence key": 1}),
    DecisionRecord(kind="plan_block", status="maybe"),
])
def test_a_record_that_fails_a_check_is_dropped_with_a_warning_never_raised(head_db: Path, bad, caplog):
    with caplog.at_level(logging.WARNING, logger="learnloop.provenance"), provenance.trace_scope("TRACE_BAD"):
        assert _write(head_db, bad) is None
    assert _rows(head_db) == []
    assert any("TRACE_BAD" in message for message in caplog.messages)


def test_item_text_planted_from_the_head_fixture_is_refused(head_db: Path):
    with connect(head_db, read_only=True) as connection:
        stem = connection.execute(
            "SELECT learner_answer_md FROM practice_attempts WHERE learner_answer_md LIKE '% %' LIMIT 1").fetchone()[0]
    record = DecisionRecord(kind="grade", status="chosen", facts={"answer": stem},
                            alternatives=[{"ref": "item:x", "lost_by": stem}])
    assert provenance.check_no_prose(record) == ["alternatives[0].lost_by", "facts.answer"]
    assert _write(head_db, record) is None and _rows(head_db) == []


def test_a_write_never_raises_on_a_vault_below_253_and_leaves_the_callers_transaction(tmp_path: Path, caplog):
    path = tmp_path / "old.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE ledger (id TEXT)")
    connection.commit()
    connection.execute("INSERT INTO ledger VALUES ('kept')")
    with caplog.at_level(logging.WARNING, logger="learnloop.provenance"):
        assert provenance.write(connection, DecisionRecord(kind="slate", status="chosen")) is None
    assert connection.in_transaction
    connection.commit()
    assert connection.execute("SELECT id FROM ledger").fetchall() == [("kept",)]
    assert any("not written" in message for message in caplog.messages)
    assert provenance.read(connection, "latest") == []


def test_a_write_joins_the_callers_transaction_and_its_failure_does_not_undo_the_callers_work(head_db: Path):
    connection = connect(head_db)
    try:
        connection.execute("BEGIN IMMEDIATE")
        assert provenance.write(connection, DecisionRecord(kind="slate", status="chosen", id="REC_ROLLED_BACK"))
        connection.rollback()
        assert _rows(head_db) == []
        connection.execute("BEGIN IMMEDIATE")
        kept = provenance.write(connection, DecisionRecord(kind="slate", status="chosen", id="REC_KEPT"))
        # The same id again: the insert fails inside the savepoint, the first stays.
        assert provenance.write(connection, DecisionRecord(kind="slate", status="chosen", id="REC_KEPT")) is None
        connection.commit()
    finally:
        connection.close()
    assert kept == "REC_KEPT" and [row[0] for row in _rows(head_db)] == ["REC_KEPT"]


def test_a_write_on_a_read_only_connection_is_dropped(head_db: Path):
    with connect(head_db, read_only=True) as connection:
        assert provenance.write(connection, DecisionRecord(kind="slate", status="chosen")) is None


def test_the_store_write_takes_its_own_transaction_or_joins_the_repositorys(head_db: Path):
    from learnloop.db.stores.provenance import write_decision

    repository = Repository.attach(head_db)
    assert write_decision(repository, DecisionRecord(kind="slate", status="chosen", id="REC_OWN"))
    with pytest.raises(RuntimeError, match="caller failed"), repository.atomic():
        assert write_decision(repository, DecisionRecord(kind="slate", status="chosen", id="REC_JOINED"))
        raise RuntimeError("caller failed")
    assert [row[0] for row in _rows(head_db)] == ["REC_OWN"]
    broken = Repository.attach(head_db, read_only=True)
    assert write_decision(broken, DecisionRecord(kind="slate", status="chosen")) is None


def test_alternatives_are_capped_with_the_overflow_counted_per_rule(head_db: Path):
    alternatives = [{"ref": f"item:{index}", "lost_by": "lane_quota" if index % 2 else "excluded_held"}
                    for index in range(60)]
    record_id = _write(head_db, DecisionRecord(kind="slate", status="chosen", alternatives=alternatives))
    (read,) = provenance.read(connect(head_db, read_only=True), record_id)
    assert len(read.alternatives) == provenance.MAX_ALTERNATIVES
    assert read.facts["alternatives_overflow"] == {"lane_quota": 5, "excluded_held": 5}


def test_records_are_append_only(head_db: Path):
    _write(head_db, DecisionRecord(kind="slate", status="chosen", id="REC_1"))
    with connect(head_db) as connection:
        for statement in ("UPDATE decision_records SET rule = 'x'", "DELETE FROM decision_records"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(statement)


def test_where_names_the_raising_frame_and_never_the_message():
    def boom():
        raise ValueError("the learner's answer was: something private")

    with pytest.raises(ValueError) as caught:
        boom()
    location = provenance.where(caught.value)
    assert location.startswith("tests.test_provenance:boom:") and "private" not in location


def test_read_finds_latest_a_trace_a_record_a_subject_and_filters_by_kind(head_db: Path):
    with provenance.trace_scope("TRACE_A"):
        first = _write(head_db, DecisionRecord(kind="plan_block", status="chosen", subject_kind="attempt",
                                               subject_id="att_1", created_at="2026-11-10T10:00:00+00:00"))
        _write(head_db, DecisionRecord(kind="model_answer", status="timeout", parent_id=first,
                                       created_at="2026-11-10T10:00:01+00:00"))
    with provenance.trace_scope("TRACE_B"):
        _write(head_db, DecisionRecord(kind="offer_withdrawn", status="withdrawn", parent_id=first,
                                       created_at="2026-11-10T10:05:00+00:00"))
    connection = connect(head_db, read_only=True)
    assert [r.kind for r in provenance.read(connection, "latest")] == ["offer_withdrawn"]
    assert [r.kind for r in provenance.read(connection, "latest", kind="plan_block")] == ["plan_block"]
    assert [r.kind for r in provenance.read(connection, "TRACE_A")] == ["plan_block", "model_answer"]
    assert [r.kind for r in provenance.read(connection, first)] == ["plan_block", "model_answer"]
    assert [r.kind for r in provenance.read(connection, "TRACE_A", kind="model_answer")] == ["model_answer"]
    assert [r.id for r in provenance.read(connection, "attempt:att_1")] == [first]
    assert provenance.read(connection, "nothing_by_this_id") == []


# -- the trace -----------------------------------------------------------------------------------------------


def test_a_trace_scope_births_nests_and_restores():
    assert provenance.current_trace() is None
    with provenance.trace_scope() as outer:
        assert provenance.current_trace() == outer and len(outer) == 26
        with provenance.trace_scope("INNER") as inner:
            assert provenance.current_trace() == inner == "INNER"
        assert provenance.current_trace() == outer
    assert provenance.current_trace() is None


def test_threads_in_a_copied_context_inherit_the_trace_and_bare_threads_do_not():
    seen: dict[str, Any] = {}
    with provenance.trace_scope("TRACE_T"):
        context = contextvars.copy_context()
        copied = threading.Thread(target=context.run, args=(lambda: seen.update(copied=provenance.current_trace()),))
        bare = threading.Thread(target=lambda: seen.update(bare=provenance.current_trace()))
        copied.start(), bare.start()
        copied.join(), bare.join()
    assert seen == {"copied": "TRACE_T", "bare": None}


def test_a_model_calls_receipt_carries_the_trace_it_started_under(head_db: Path):
    from learnloop.ai.execution import model_call, record_model_calls

    repository = Repository.attach(head_db)

    class Client:
        provider_name = "fake"
        model = "fake-model"

    with record_model_calls(repository, owner_kind="test", owner_id="b1"):
        with provenance.trace_scope("TRACE_CALL"), model_call(Client(), purpose="traced", prompt="p"):
            pass
        with model_call(Client(), purpose="untraced", prompt="p"):
            pass
    with connect(head_db, read_only=True) as connection:
        rows = dict(connection.execute(
            "SELECT purpose, trace_id FROM model_call_receipts WHERE owner_id = 'b1'").fetchall())
    assert rows == {"traced": "TRACE_CALL", "untraced": None}


def _stub_method(monkeypatch, seen: list) -> str:
    from learnloop_sidecar.dto import EmptyParams
    from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec

    def handler(_ctx, _params):
        seen.append(provenance.current_trace())
        return {}

    monkeypatch.setitem(METHOD_REGISTRY, "b1_trace_probe", MethodSpec("b1_trace_probe", EmptyParams, handler))
    return "b1_trace_probe"


def test_each_sidecar_rpc_runs_under_a_trace_of_its_own(monkeypatch):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.server import _handle

    seen: list = []
    method = _stub_method(monkeypatch, seen)
    ctx = SidecarContext()
    for request_id in (1, 2):
        response = _handle(ctx, {"jsonrpc": "2.0", "id": request_id, "method": method, "params": {}})
        assert "error" not in response, response
    assert len(seen) == 2 and None not in seen and seen[0] != seen[1]
    assert provenance.current_trace() is None
    _handle(ctx, {"jsonrpc": "2.0", "id": 3, "method": method, "params": {}}, trace_id="HANDED_IN")
    assert seen[-1] == "HANDED_IN"


def test_a_phone_request_births_its_trace_and_hands_it_to_the_sidecar(monkeypatch):
    import learnloop_sidecar.server as server
    from learnloop_mobile.runtime import HostRuntime

    seen: dict[str, Any] = {}

    class Context:
        def refresh_if_content_changed(self):
            seen["refresh"] = provenance.current_trace()

        def acting_as(self, _origin):
            return contextlib_nullcontext()

    class Worker:
        def loaded_context(self):
            seen["load"] = provenance.current_trace()
            return Context()

    def fake_handle(_ctx, request, *, trace_id=None):
        seen["handed"], seen["inside"] = trace_id, provenance.current_trace()
        return {"jsonrpc": "2.0", "id": request["id"], "result": {}}

    monkeypatch.setattr(server, "_handle", fake_handle)
    HostRuntime._dispatch(Worker(), "get_today_queue", {}, None)
    assert seen["load"] and seen["load"] == seen["refresh"] == seen["handed"] == seen["inside"]
    assert provenance.current_trace() is None


def contextlib_nullcontext():
    from contextlib import nullcontext

    return nullcontext()


def test_each_mcp_tool_call_runs_under_a_trace_of_its_own(monkeypatch):
    from learnloop_mcp.server import ToolCalls

    calls = ToolCalls.__new__(ToolCalls)
    seen: list = []
    monkeypatch.setattr(calls, "_run", lambda *args: seen.append(provenance.current_trace()) or {})
    calls.run("status", {}, None, lambda _call: None)
    calls.run("status", {}, None, lambda _call: None)
    assert len(seen) == 2 and None not in seen and seen[0] != seen[1]
    assert provenance.current_trace() is None


def test_each_post_attempt_job_gets_a_trace_of_its_own():
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

    worker = PostAttemptWorker(autostart=False)
    with provenance.trace_scope("THE_RPC_THAT_WOKE_IT"):
        first = worker._with_busy_retry(provenance.current_trace)
        second = worker._with_busy_retry(provenance.current_trace)
    assert first and second and len({first, second, "THE_RPC_THAT_WOKE_IT"}) == 3


def test_sidecar_log_events_carry_the_trace(caplog):
    from learnloop_sidecar.logging import EVENT_FIELDS_ATTR, log_event

    with caplog.at_level(logging.DEBUG, logger="learnloop.sidecar"):
        with provenance.trace_scope("TRACE_LOG"):
            log_event("b1.probe", method="x")
        log_event("b1.untraced")
    fields = [getattr(record, EVENT_FIELDS_ATTR) for record in caplog.records if record.getMessage().startswith("b1.")]
    assert fields == [{"method": "x", "trace_id": "TRACE_LOG"}, {}]


# -- replay never reaches the table --------------------------------------------------------------------------

#: What rebuilds, replays or upgrades a vault: the live and shadow rebuilds, the replay, the migration coordinator
#: and every successor's upgrade module.
def _replay_roots() -> list[str]:
    roots = ["learnloop.substrate.rebuild_orchestrator", "learnloop.substrate.replay",
             "learnloop.substrate.shadow_rebuild", "learnloop.migration_coordinator", "learnloop.db.migrate"]
    roots += sorted(f"learnloop.{path.stem}" for path in (SRC / "learnloop").glob("*_upgrade.py"))
    return roots


def _module_path(module: str) -> Path:
    base = SRC.joinpath(*module.split("."))
    return base / "__init__.py" if base.is_dir() else base.with_suffix(".py")


#: The registries that classify every table by name: they name it to say a rebuild never clears it (RECEIPT) and
#: AD never reads it (DENIED), and read no row of it.
_REGISTRIES = frozenset({"learnloop.db.table_roles", "learnloop.adaptive_difficulty.protected_tables",
                         "learnloop.adaptive_difficulty.column_classes"})

#: Record writers inside the closure, each with its proof that replay never calls it. The slate's record
#: (refactor B6) is written only by a persisting queue build (``build_due_queue``, statically in the closure through
#: the simulator and the state sync's imports); no rebuild, replay or upgrade builds a queue, and
#: ``test_a_rebuild_never_calls_the_record_and_keeps_its_rows`` refuses it at run time. The store enters the closure
#: through these writers alone.
#:
#: The refusals' records (refactor B5, ``learnloop.refusal_records``) enter it through
#: ``db.stores.router`` (a ledger refusal; the closure reaches the store for ``router.outcomes``' reads, and no replay
#: appends a decision row), ``decider_judgments`` (AD's replay imports the feature audit, which uses the Decider's
#: client and argmax, never ``decide``) and ``figure_admission`` (the gate, which no replay builds); the same test
#: counts their calls during a live rebuild: none.
#:
#: The attempt chain's (refactor B7): the grade's record is written by the attempt step's live branch only
#: (``replace_existing`` False; replay re-applies with it True) and by a regrade; the diagnosis's, its failed steps',
#: the follow-up value's and the failed forecasts' by the diagnosis worker and the post-attempt pipeline, which no
#: rebuild runs; a queued job's by the four enqueues, which no rebuild calls; and the job processors read one
#: ``job_enqueued`` record's trace, which no rebuild leases a job to do. The runtime test counts every write and
#: every trace continuation during a live rebuild: zero.
#:
#: Refactor B8's: ``source_retrieval.deliverable_path`` (the closure reaches it for the curriculum path's reads)
#: writes the daily re-judgment's record from ``refresh_for_plan``, which only the sidecar's plan handler starts and
#: no rebuild calls; the runtime test counts its writes during a live rebuild: zero.
_RECORD_WRITERS = frozenset({
    "learnloop.scheduling.slate_record", "learnloop.refusal_records",
    "learnloop.attempts.grade_records", "learnloop.diagnosis.chain_records",
    "learnloop.db.stores.diagnoses", "learnloop.db.stores.learner_gaps", "learnloop.db.stores.followup_serve",
    "learnloop.diagnosis.split.jobs", "learnloop.diagnosis.text_gaps.jobs",
    "learnloop.source_retrieval.deliverable_path",
})
_STORE = "learnloop.db.stores.provenance"


def test_decision_records_is_unreachable_from_replay():
    import grimp

    graph = grimp.build_graph("learnloop", cache_dir=None)
    closure: set[str] = set()
    for root in _replay_roots():
        closure |= {root} | set(graph.find_upstream_modules(root))
    assert len(closure) > 100  # the closure is real, not an empty graph
    # The store (the write with its own transaction, the trace's calls) is reached only through a declared writer.
    assert "learnloop.cli.app" not in closure
    assert graph.find_modules_that_directly_import(_STORE) & closure <= _RECORD_WRITERS
    # No other module in it names the table, and none reads or writes a record: the leaf's other names (the trace,
    # the dataclass, the code check) are all a replay module may use. A later writer in this closure brings its own
    # proof that replay never calls it, and joins ``_RECORD_WRITERS``.
    naming, using = [], []
    for module in sorted(closure - {"learnloop.provenance", _STORE} - _RECORD_WRITERS):
        path = _module_path(module)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "decision_records" in text and module not in _REGISTRIES:
            naming.append(module)
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "learnloop.provenance":
                using += [f"{module}:{alias.name}" for alias in node.names
                          if alias.name not in {"current_trace", "trace_scope", "DecisionRecord", "STATUSES",
                                                "is_code"}]
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "provenance" \
                    and node.attr in {"write", "write_through", "read", "cap_alternatives", "check_no_prose"}:
                using.append(f"{module}:provenance.{node.attr}")
    assert naming == [] and using == []


def test_a_rebuild_never_calls_the_record_and_keeps_its_rows(tmp_path: Path, monkeypatch):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault

    root = tmp_path / "head"
    copy_tree_with_databases(MIGRATION_HEAD_FIXTURE, root, database_names=("state.sqlite",))
    allow_below_floor(root)
    path = root / "state.sqlite"
    with provenance.trace_scope("TRACE_KEPT"):
        _write(path, DecisionRecord(kind="plan_block", status="chosen", facts={"n": 1}))
    before = _rows(path)

    def refused(*_args, **_kwargs):
        raise AssertionError("replay reached a decision record")

    import learnloop.db.stores.provenance as store

    for name in ("write", "read"):
        monkeypatch.setattr(provenance, name, refused)
    for name in ("write_decision", "trace_model_calls"):
        monkeypatch.setattr(store, name, refused)
    # The writers inside the closure (``_RECORD_WRITERS``) swallow a failed write, so they are counted, not refused.
    import learnloop.scheduling.scheduler as scheduler
    import learnloop.scheduling.slate_record as slate_record

    import learnloop.refusal_records as refusal_records

    slate_calls: list[object] = []
    monkeypatch.setattr(scheduler, "record_slate", lambda *a, **k: slate_calls.append(k))
    monkeypatch.setattr(slate_record, "record_slate", lambda *a, **k: slate_calls.append(k))
    refusal_calls: list[object] = []
    for name in ("write", "write_on"):
        monkeypatch.setattr(refusal_records, name, lambda *a, _name=name, **k: refusal_calls.append((_name, a[1])))
    # The attempt chain's (refactor B7): the grade's writer (looked up at call time by the attempt step and the
    # regrade), the chain's writer, the queued job's writer and the job processors' trace continuation.
    import learnloop.attempts.grade_records as grade_records
    import learnloop.diagnosis.chain_records as chain_records

    chain_calls: list[str] = []
    monkeypatch.setattr(grade_records, "record_grade", lambda *a, **k: chain_calls.append("grade"))
    monkeypatch.setattr(chain_records, "_write", lambda _repo, kind, _build: chain_calls.append(kind))
    monkeypatch.setattr(store, "record_job_enqueued", lambda *a, **k: chain_calls.append("job_enqueued"))
    monkeypatch.setattr(store, "continue_job_trace", lambda *a, **k: chain_calls.append("continue_job_trace"))
    # Refactor B8's: the curriculum path's daily re-judgment record.
    import learnloop.source_retrieval.deliverable_path as deliverable_path

    monkeypatch.setattr(deliverable_path, "_write_refresh_record", lambda *a, **k: chain_calls.append("refresh"))
    rebuild_all_derived_state(load_vault(root), Repository(path))
    assert _rows(path) == before and len(before) == 1
    assert slate_calls == [] and refusal_calls == [] and chain_calls == []


def test_the_table_is_a_receipt_and_denied_to_ad():
    from learnloop.adaptive_difficulty.protected_tables import AD_WRITABLE, DENIED, ROLES
    from learnloop.db.table_roles import TableRole, role_for_table

    assert role_for_table("decision_records") is TableRole.RECEIPT
    assert ROLES["decision_records"] == DENIED and "decision_records" not in AD_WRITABLE


# -- why -----------------------------------------------------------------------------------------------------


def _db_digest(path: Path) -> str:
    with connect(path, read_only=True) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        digest = hashlib.sha256()
        for table in tables:
            for row in sorted(repr(tuple(row)) for row in connection.execute(f'SELECT * FROM "{table}"')):
                digest.update(row.encode())
    return digest.hexdigest()


def test_why_is_a_pure_read(tmp_path: Path, monkeypatch):
    """Fail-first: before B1 ``why`` ran the state sync and startup maintenance, so asking wrote to the vault."""

    cli_app = importlib.import_module("learnloop.cli.app")  # the package's ``app`` attribute is the Typer app
    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    runner = CliRunner()
    assert runner.invoke(app, ["review", "--json", "--vault", str(paths.root)]).exit_code == 0

    def refused(*_args, **_kwargs):
        raise AssertionError("why wrote to the vault")

    monkeypatch.setattr(cli_app, "sync_vault_state", refused)
    monkeypatch.setattr(cli_app, "run_startup_maintenance", refused)
    before = _db_digest(paths.sqlite_path)
    for target in ("pi_svd_define_001", "latest", "attempt:none"):
        result = runner.invoke(app, ["why", target, "--json", "--vault", str(paths.root)])
        assert result.exit_code == 0, result.output
    assert _db_digest(paths.sqlite_path) == before


def test_why_answers_a_trace_from_its_records_and_its_calls_without_payloads(tmp_path: Path):
    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    path = paths.sqlite_path
    with provenance.trace_scope("TRACE_WHY"):
        block = _write(path, DecisionRecord(kind="plan_block", status="fallback", rule="chooser_error",
                                            subject_kind="attempt", subject_id="att_9", facts={"timeout_s": 8},
                                            created_at="2026-11-10T10:00:00+00:00"))
    with connect(path) as connection:
        for call_id, trace in (("call_traced", "TRACE_WHY"), ("call_old", None)):
            connection.execute(
                "INSERT INTO model_call_receipts (id, purpose, owner_kind, owner_id, status, started_at, input_text, "
                "output_text, trace_id) VALUES (?, 'router_llm', 'router', 'bk', 'completed', ?, 'PROMPT', 'ANSWER', ?)",
                (call_id, "2026-11-10T10:00:09+00:00", trace))
        connection.commit()
    runner = CliRunner()
    for target in ("TRACE_WHY", block, "latest", "attempt:att_9"):
        result = runner.invoke(app, ["why", target, "--json", "--vault", str(paths.root)])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["source"] == "decision_records" and payload["traces"] == ["TRACE_WHY"]
        assert [r["id"] for r in payload["records"]] == [block]
        assert [c["id"] for c in payload["model_calls"]] == ["call_traced"]
        assert "PROMPT" not in result.output and "ANSWER" not in result.output
    text = runner.invoke(app, ["why", "TRACE_WHY", "--vault", str(paths.root)])
    assert "chooser_error" in text.output and "call_traced" in text.output
    filtered = json.loads(runner.invoke(app, ["why", "TRACE_WHY", "--kind", "slate", "--json",
                                              "--vault", str(paths.root)]).output)
    assert filtered["records"] == []
    missing = runner.invoke(app, ["why", "no_such_thing", "--json", "--vault", str(paths.root)])
    assert missing.exit_code == 1 and json.loads(missing.output)["error"] == "not_found"


def test_each_cli_command_runs_under_a_trace_that_ends_with_it(tmp_path: Path, monkeypatch):
    cli_app = importlib.import_module("learnloop.cli.app")  # the package's ``app`` attribute is the Typer app
    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    seen: list = []
    real_read = provenance.read

    def spy(connection, target="latest", **kwargs):
        seen.append(provenance.current_trace())
        return real_read(connection, target, **kwargs)

    monkeypatch.setattr(cli_app.provenance, "read", spy)
    runner = CliRunner()
    for _ in range(2):
        assert runner.invoke(app, ["why", "--json", "--vault", str(paths.root)]).exit_code == 0
    assert len(seen) == 2 and None not in seen and seen[0] != seen[1]
    assert provenance.current_trace() is None
