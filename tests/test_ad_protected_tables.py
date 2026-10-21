"""AD23 redesign, step 2: the AD guard's registry (``adaptive_difficulty.protected_tables``).

* every column of every protected table in the head schema is classified (a value or a reference of
  a known kind), and nothing else: a migration adding a column to a protected table fails here until
  the column is classified;
* every classified table exists in the head schema; AD's writable tables, the carve-out tables and
  the named incumbent readers are what they say they are.

That every table an operation reads is classified is the guard's own check (an unclassified table is
refused): ``test_ad_guard.py``'s zero-denial pipeline.
"""

from __future__ import annotations

import importlib
from contextlib import closing

from learnloop.adaptive_difficulty import protected_tables as T
from learnloop.db.connection import connect

from tests.ad23_fakes import ad23_vault

KINDS = {"value", "item", "revision", "attempt", "presentation", "note", "reader_question", "question_event",
         "facet", "dose_draw", "selection", "receipt", "administration", "surface", "extraction", "self",
         "epoch"}
WITH_COLUMN = {"span", "section", "spans", "entity", "served_item", "source", "plan_detail"}


def _schema(tmp_path) -> dict[str, list[str]]:
    paths = ad23_vault(tmp_path, items=("pi_e1",))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        tables = [str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {table: [str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")]
                for table in tables}


def test_every_column_of_every_protected_table_is_classified(tmp_path):
    schema = _schema(tmp_path)
    protected = sorted(table for table, role in T.ROLES.items() if role == T.PROTECTED)
    assert sorted(T.COLUMNS) == protected
    for table in protected:
        assert table in schema, table
        assert sorted(T.COLUMNS[table]) == sorted(schema[table]), (
            table, sorted(set(schema[table]) - set(T.COLUMNS[table])), sorted(set(T.COLUMNS[table]) - set(schema[table])))
        for column, kind in T.COLUMNS[table].items():
            base, sep, arg = kind.partition("@")
            if sep:
                assert base in WITH_COLUMN and arg in schema[table], (table, column, kind)
            else:
                assert base in KINDS, (table, column, kind)


def test_every_ad_owned_table_ad_reads_has_an_epoch_rule(tmp_path):
    """Round 2, class 3b: every AD-owned artefact table (AD writes it, and the rules read it) says
    how its rows carry the protection epoch they were computed under, or why nothing in it was
    computed from a projection; a stamped table has the stamp's column, classified ``epoch``."""

    schema = _schema(tmp_path)
    owned = sorted(table for table in T.AD_WRITABLE if T.ROLES.get(table) == T.PROTECTED)
    assert owned and set(owned) <= set(T.EPOCH), sorted(set(owned) - set(T.EPOCH))
    for table, rule in T.EPOCH.items():
        kind, _sep, rest = rule.partition(":")
        assert kind in ("column", "json", "free"), (table, rule)
        if kind == "column":
            assert T.COLUMNS[table][rest] == "epoch", (table, rule)
        elif kind == "json":
            column = rest.split(":", 1)[0]
            assert column in schema[table], (table, rule)
        else:
            assert rest.strip(), (table, "a free table names why")


def test_the_registry_names_real_tables_and_roles(tmp_path):
    schema = _schema(tmp_path)
    for table in T.ROLES:
        assert table in schema or table in ("json_each", "sqlite_master", "sqlite_temp_master"), table
    assert T.AD_WRITABLE <= set(schema)
    for table in T.CARVE_OUTS:
        assert T.ROLES[table] == T.DENIED, table
    assert set(T.ENTITY_KINDS.values()) <= KINDS
    for module in sorted(T.INCUMBENT_READERS):
        importlib.import_module(module)
    # The predicate's own inputs are readable only while it is computed; AD's tables are protected.
    assert {T.ROLES[t] for t in ("source_unit_selections", "source_held_out_signal_marks", "exam_pool_items")} == {
        T.PREDICATE}
    assert all(T.ROLES[t] == T.PROTECTED for t in T.AD_WRITABLE if t.startswith("ad_"))
