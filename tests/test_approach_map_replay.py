"""Adaptive hints H1 and H2a, G-H10: rebuild and replay make zero model and
embedding calls with ``approach_maps`` and ``help_assists`` populated (H2a:
server-written hints folded into an attempt too), and never read
``approach_maps`` (spec_adaptive_hints_v1 standing constraint H6, §9 "No
DERIVED table, so no replayer", §11 G-H10).

The vault carries a stored map (built by a fake), a merged version, authored
hint reveals and graded attempts. Every model and embedding client
constructor is forbidden during the rebuild and the shadow replay; an SQLite
authorizer refuses any read of ``approach_maps`` on every connection opened
meanwhile; the derived state equals a rebuild of a copy with both tables
dropped; and the map rows are unchanged afterwards. Fakes only.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import learnloop.db.connection as db_connection
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop.hints import map_builder as MB
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import ITEM, TRACE_CONTRACT, MapFake, add_attempt, map_vault, rows


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _populate(tmp_path: Path):
    paths = map_vault(tmp_path, trace_contract=TRACE_CONTRACT)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.approach_map_client = MapFake()
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})  # builds on serve
    assert MB.wait_for_background_builds(30)
    for index in (0, 1):
        _call(ctx, "practice.record_hint_reveal", {"sessionId": session_id, "practiceItemId": ITEM,
                                                   "submissionId": "k1", "authoredIndex": index, "answerMd": ""})
    # Adaptive hints H2a (G-H10 extended): two server-written hints, one of
    # them worked help, counted into the attempt by the submit's fold.
    from tests.hint_fakes import ChooserFake, WriterFake, prefer

    ctx.hints_inline = True
    for option, level in (("next_step@L3", None), ("worked_chunk@L4", 4)):
        ctx.hint_writer_client = WriterFake()
        ctx.hint_chooser_client = ChooserFake(prefer(option, 0.99))
        params = {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k1",
                  "answerMd": "F(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) + 1"}
        if level is not None:
            params["takenLevel"] = level
        assert _call(ctx, "practice.request_hint", params)["result"]["status"] == "ready"
    _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "F(x) = x^2, so P(X ≤ 1/2) = 1/4.",
        "attemptType": "hinted_attempt", "hintsUsed": 2, "submissionId": "k1",
        "selfGrade": {"criterionPoints": {"cdf": 2, "value": 2}, "confidence": 4}})
    add_attempt(paths.sqlite_path, "a_correct", created_at="2026-10-18T08:00:00+00:00")
    merged = MB.merge_learner_routes(load_vault(paths.root), Repository.attach(paths.sqlite_path), ITEM,
                                     client=MapFake())
    assert merged.status == "merged", merged
    assert len(rows(paths.sqlite_path)) == 2
    assists = rows(paths.sqlite_path, "help_assists")
    assert len(assists) == 4 and sum(1 for row in assists if row["counted_by"] == "server" and row["shown"]) == 2
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT hints_used, primed FROM practice_attempts WHERE submission_id = 'k1'"
                                  ).fetchone() == (3, 1)
    return paths


def _forbid_clients(monkeypatch) -> None:
    from learnloop.ai import client
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

    def forbidden(*args, **kwargs):
        raise AssertionError("replay must not construct a model or embedding client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.diagnosis.split.jobs.default_embedding_client", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "__init__", forbidden)
    monkeypatch.setattr(MB, "_route_client", forbidden)
    monkeypatch.setattr(MB, "build_map", forbidden)
    monkeypatch.setattr(MB, "merge_learner_routes", forbidden)
    # Adaptive hints H2a: neither hint route is ever asked by replay.
    from learnloop.hints import chooser as hint_chooser
    from learnloop.hints import service as hint_service
    from learnloop.hints import writer as hint_writer

    monkeypatch.setattr(hint_writer.WriterRoute, "ask", forbidden)
    monkeypatch.setattr(hint_chooser, "ask", forbidden)
    monkeypatch.setattr(hint_service, "request_hint", forbidden)


def _refuse_map_reads(monkeypatch, reads: list[str]) -> None:
    """Every SQLite connection opened from here on refuses to read approach_maps."""

    original = db_connection.sqlite3.connect

    def authorize(action, first, _second, _database, _source):
        if action == sqlite3.SQLITE_READ and first == "approach_maps":
            reads.append(first)
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_authorizer(authorize)
        return connection

    monkeypatch.setattr(db_connection.sqlite3, "connect", connect)


def test_rebuild_and_replay_call_no_model_and_never_read_approach_maps(tmp_path, monkeypatch):
    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.db.table_roles import TableRole, tables_for_role
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths = _populate(tmp_path)
    maps_before = rows(paths.sqlite_path)
    assists_before = rows(paths.sqlite_path, "help_assists")
    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot(database: Path):
        with closing(sqlite3.connect(database)) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                    for table in derived}

    # The same vault with both tables gone: if rebuild needed them it would differ or fail.
    gone = tmp_path / "gone"
    copy_tree_with_databases(paths.root, gone)
    with closing(sqlite3.connect(gone / "state.sqlite")) as connection:
        connection.execute("DROP TABLE approach_maps")
        connection.execute("DROP TABLE help_assists")
        connection.commit()
    reads: list[str] = []
    with monkeypatch.context() as patch:
        _forbid_clients(patch)
        _refuse_map_reads(patch, reads)
        rebuild_all_derived_state(load_vault(paths.root), Repository.attach(paths.sqlite_path))
        rebuild_all_derived_state(load_vault(gone), Repository.attach(gone / "state.sqlite"))
        result = shadow_rebuild(load_vault(paths.root), assignments=())
        assert result is not None
    assert reads == []
    assert snapshot(paths.sqlite_path) == snapshot(gone / "state.sqlite")
    assert rows(paths.sqlite_path) == maps_before
    assert rows(paths.sqlite_path, "help_assists") == assists_before


def test_the_read_refusal_would_catch_a_replay_that_read_maps(tmp_path, monkeypatch):
    """The authorizer itself: a read of approach_maps on a new connection is refused and seen."""

    paths = _populate(tmp_path)
    reads: list[str] = []
    with monkeypatch.context() as patch:
        _refuse_map_reads(patch, reads)
        with closing(db_connection.connect(paths.sqlite_path, read_only=True)) as connection:
            try:
                connection.execute("SELECT COUNT(*) FROM approach_maps").fetchone()
            except sqlite3.DatabaseError:
                pass
            else:  # pragma: no cover - the refusal is the point
                raise AssertionError("the authorizer did not refuse the read")
    assert reads == ["approach_maps"]


def test_approach_maps_has_no_replayer_and_is_never_cleared():
    from learnloop.db.table_roles import TableRole, role_for_table, tables_for_role

    assert role_for_table("approach_maps") is TableRole.WORKFLOW
    assert "approach_maps" not in tables_for_role(TableRole.DERIVED)
    source = (Path(__file__).resolve().parents[1] / "src" / "learnloop" / "substrate").rglob("*.py")
    for path in source:
        text = path.read_text(encoding="utf-8")
        assert "approach_maps" not in text and "learnloop.hints" not in text, path
