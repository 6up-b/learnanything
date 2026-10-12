"""Slice 2 T6: the ``source_block_fts`` keyword index (migrations 175-176, DERIVED)."""
from __future__ import annotations

from contextlib import closing
import sqlite3

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    match_expression,
    query_terms,
    rebuild_source_block_fts,
    search_blocks,
    section_header_titles,
)
from learnloop.db.table_roles import TABLE_ROLES, TableRole, fts5_shadow_table_names, user_table_names
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.substrate.rebuild_orchestrator import derived_table_owners
from tests.source_retrieval_fakes import BOOK, seed_source


def _rows(path) -> list[tuple]:
    with closing(connect(path, read_only=True)) as connection:
        return sorted(tuple(row) for row in connection.execute(
            "SELECT rowid, text, extraction_id, span_id FROM source_block_fts"))


def test_triggers_index_every_written_block_except_page_furniture(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    seed_source(repository, source_id="src", revision_id="rev", extraction_id="ext",
                title="Notes", units=BOOK)
    rows = _rows(repository.sqlite_path)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = connection.execute(
            "SELECT rowid, text, extraction_id, span_id, block_type FROM source_document_blocks").fetchall()
    assert rows == sorted((b[0], b[1], b[2], b[3]) for b in blocks if b[4] != "PageHeader")
    assert all(row[3] != "s999" for row in rows)  # the running header is furniture


def test_replacing_a_runs_blocks_replaces_its_index_rows(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    seed_source(repository, source_id="src", revision_id="rev", extraction_id="ext",
                title="Notes", units=BOOK)
    replacement = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u", label="Only", ordinal=0, semantic_hash="sha256:u", span_ids=["n1"])],
        blocks=[DocumentBlock.build(span_id="n1", block_type="Text", text="Gram-Schmidt orthonormalization",
                                    ordinal=1, page=1)],
        assets=[], health=ExtractionHealth())
    repository.persist_document_ir("ext", replacement)
    assert [(row[2], row[3]) for row in _rows(repository.sqlite_path)] == [("ext", "n1")]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert [m.span_id for m in search_blocks(connection, "orthonormalization")] == ["n1"]
        assert search_blocks(connection, "determinant") == []


def test_rebuild_reproduces_the_trigger_maintained_index(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    seed_source(repository, source_id="src", revision_id="rev", extraction_id="ext",
                title="Notes", units=BOOK)
    before = _rows(repository.sqlite_path)
    with repository.connection() as connection:
        connection.execute("DELETE FROM source_block_fts WHERE span_id = 's2'")
        connection.execute("INSERT INTO source_block_fts(rowid, text, extraction_id, span_id) "
                           "VALUES (424242, 'orphan', 'gone', 'gone')")
        report = rebuild_source_block_fts(connection)
        connection.commit()
    assert report["written"] == len(before)
    assert _rows(repository.sqlite_path) == before


def test_queries_are_sanitized_stemmed_scoped_and_ranked(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    seed_source(repository, source_id="src", revision_id="rev", extraction_id="ext",
                title="Notes", units=BOOK)
    seed_source(repository, source_id="src2", revision_id="rev2", extraction_id="ext2", title="Other",
                units={"u": ("Misc", [("Eigenvalues appear in Markov chains too.", 1)])}, furniture=False)
    # Operators, quotes and column filters are inert text, never FTS syntax.
    assert match_expression('eigen" OR text:* NEAR(') == '"eigen" OR "text" OR "near"'
    assert match_expression("the of and") is None
    assert match_expression("eigenv", prefix_last=True) == '"eigenv"*'
    assert query_terms("Why are THE eigenvalues real?") == ["eigenvalues", "real"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stemmed = search_blocks(connection, "eigenvalue roots")  # porter: eigenvalue ~ eigenvalues
        assert stemmed and stemmed[0].span_id == "s2"
        scoped = search_blocks(connection, "eigenvalues", extraction_ids=["ext2"])
        assert {(m.extraction_id, m.span_id) for m in scoped} == {("ext2", "s2")}
        assert search_blocks(connection, "eigenvalues", extraction_ids=[]) == []
        prefix = search_blocks(connection, "orthog", prefix_last=True)
        assert {m.span_id for m in prefix} >= {"s11", "s12", "s13"}
        assert section_header_titles(connection, "ext")["/page/3/SectionHeader/1"] == "Chapter 5 Eigenvalues"


def test_the_index_is_derived_with_one_owner_and_its_shadow_tables_are_not_tables(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    assert TABLE_ROLES["source_block_fts"] is TableRole.DERIVED
    assert derived_table_owners()["source_block_fts"] == ("source_block_fts",)
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        shadows = fts5_shadow_table_names(connection)
        names = user_table_names(connection)
    assert {"source_block_fts_data", "source_block_fts_idx", "source_block_fts_docsize",
            "source_block_fts_config", "source_block_fts_content"} == shadows
    assert "source_block_fts" in names and not (names & shadows)


def test_the_umbrella_rebuild_restores_the_index_without_any_model_or_embedding_call(tmp_path, monkeypatch):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault
    from tests.source_retrieval_fakes import build_retrieval_vault

    def refuse(*_args, **_kwargs):
        raise AssertionError("replay must not build a model or embedding client")

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    before = _rows(repository.sqlite_path)
    with repository.connection() as connection:
        connection.execute("DELETE FROM source_block_fts")
        connection.commit()
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", refuse)
    result = rebuild_all_derived_state(load_vault(paths.root), repository)
    fts = next(r for r in result.replayers if r.name == "source_block_fts")
    assert fts.rows_processed == len(before) and _rows(repository.sqlite_path) == before


def test_a_delete_never_removes_another_blocks_index_row(tmp_path):
    """Review F14: rowids renumbered under the index (a table rebuild) must not
    make a delete remove the wrong row; doctor reports the drift and the
    replayer repairs it."""

    from learnloop.db.stores.source_block_fts import fts_drift
    from learnloop.ops.doctor import _check_source_block_fts

    repository = Repository(tmp_path / "s.sqlite")
    seed_source(repository, source_id="src", revision_id="rev", extraction_id="ext", title="Notes", units=BOOK)
    with repository.connection() as connection:
        (first, first_span), (second, second_span) = connection.execute(
            "SELECT rowid, span_id FROM source_document_blocks WHERE block_type = 'Text' "
            "ORDER BY rowid LIMIT 2").fetchall()
        text = connection.execute("SELECT text FROM source_document_blocks WHERE rowid = ?", (second,)).fetchone()[0]
        # Simulate renumbering: the second block's index row now sits at the first block's rowid.
        connection.execute("DELETE FROM source_block_fts WHERE rowid IN (?, ?)", (first, second))
        connection.execute("INSERT INTO source_block_fts(rowid, text, extraction_id, span_id) VALUES (?,?,?,?)",
                           (first, text, "ext", second_span))
        connection.execute("DELETE FROM source_document_blocks WHERE rowid = ?", (first,))
        connection.commit()
    assert ("ext", second_span) in {(row[2], row[3]) for row in _rows(repository.sqlite_path)}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert fts_drift(connection) == {"stale": 1, "missing": 1}
    issues = []
    _check_source_block_fts(repository, issues)
    assert [issue.code for issue in issues] == ["sql:source_block_fts_drift"]
    assert "rebuild-derived-state" in issues[0].message
    with repository.connection() as connection:
        rebuild_source_block_fts(connection)
        connection.commit()
        assert fts_drift(connection) == {"stale": 0, "missing": 0}
    issues = []
    _check_source_block_fts(repository, issues)
    assert issues == []


_EARLIER_175_DELETE_PATHS = (
    "CREATE TRIGGER source_block_fts_after_delete AFTER DELETE ON source_document_blocks "
    "BEGIN DELETE FROM source_block_fts WHERE rowid = OLD.rowid; END",
    "CREATE TRIGGER source_block_fts_after_update AFTER UPDATE OF extraction_id, span_id, block_type, text "
    "ON source_document_blocks BEGIN DELETE FROM source_block_fts WHERE rowid = OLD.rowid; "
    "INSERT OR REPLACE INTO source_block_fts(rowid, text, extraction_id, span_id) "
    "SELECT NEW.rowid, NEW.text, NEW.extraction_id, NEW.span_id "
    "WHERE NEW.block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents'); END",
)


def _trigger_sql(path) -> dict[str, str]:
    with closing(connect(path, read_only=True)) as connection:
        return {str(name): str(sql) for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'source_block_fts_%'")}


def test_a_vault_that_applied_the_earlier_175_gets_the_identity_delete_paths(tmp_path):
    """Re-review F20: 175 was edited in place and migrations carry no checksum,
    so a vault with the earlier rowid-only delete paths is repaired by 176."""

    from learnloop.db.migrate import apply_migrations

    repository = Repository(tmp_path / "s.sqlite")
    with repository.connection() as connection:
        connection.execute("DROP TRIGGER source_block_fts_after_delete")
        connection.execute("DROP TRIGGER source_block_fts_after_update")
        for statement in _EARLIER_175_DELETE_PATHS:
            connection.execute(statement)
        connection.execute("DELETE FROM schema_migrations WHERE version > 175")
        connection.commit()
    assert "OLD.extraction_id" not in _trigger_sql(repository.sqlite_path)["source_block_fts_after_delete"]
    applied = apply_migrations(repository.sqlite_path)
    assert [migration.version for migration in applied][:1] == [176]
    triggers = _trigger_sql(repository.sqlite_path)
    assert set(triggers) == {"source_block_fts_after_insert", "source_block_fts_after_delete",
                             "source_block_fts_after_update"}
    for name in ("source_block_fts_after_delete", "source_block_fts_after_update"):
        assert "extraction_id = OLD.extraction_id AND span_id = OLD.span_id" in triggers[name]
    # And they behave: a renumbered rowid never deletes another block's row.
    seed_source(Repository(repository.sqlite_path), source_id="src", revision_id="rev", extraction_id="ext",
                title="Notes", units=BOOK)
    with repository.connection() as connection:
        (first, _), (second, second_span) = connection.execute(
            "SELECT rowid, span_id FROM source_document_blocks WHERE block_type = 'Text' "
            "ORDER BY rowid LIMIT 2").fetchall()
        text = connection.execute("SELECT text FROM source_document_blocks WHERE rowid = ?", (second,)).fetchone()[0]
        connection.execute("DELETE FROM source_block_fts WHERE rowid IN (?, ?)", (first, second))
        connection.execute("INSERT INTO source_block_fts(rowid, text, extraction_id, span_id) VALUES (?,?,?,?)",
                           (first, text, "ext", second_span))
        connection.execute("DELETE FROM source_document_blocks WHERE rowid = ?", (first,))
        connection.commit()
    assert ("ext", second_span) in {(row[2], row[3]) for row in _rows(repository.sqlite_path)}


def test_a_fresh_vault_has_the_same_triggers_through_176(tmp_path):
    repository = Repository(tmp_path / "s.sqlite")
    triggers = _trigger_sql(repository.sqlite_path)
    for name in ("source_block_fts_after_delete", "source_block_fts_after_update"):
        assert "extraction_id = OLD.extraction_id AND span_id = OLD.span_id" in triggers[name]
