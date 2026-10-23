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
         "epoch", "derived_by_position", "reading_payload"}
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


def test_every_column_of_every_readable_table_is_metadata_or_content(tmp_path):
    """Round 5 (class 2): every column of every table an operation can read (``ROLES``: an
    unclassified table is unreadable inside one) is ``metadata`` or ``content``, exactly once, and
    the registry names no column the head schema lacks; a migration adding a column to such a table
    fails here until it is classified. The verify's two neutral tables carry their content columns
    as content (failed before: there was no column registry)."""

    from learnloop.adaptive_difficulty import column_classes as C

    schema = _schema(tmp_path)
    paths = ad23_vault(tmp_path / "virtual", items=("pi_e1",))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        for table in ("json_each", "sqlite_master", "sqlite_temp_master"):
            schema[table] = [str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")]
    assert sorted(C._CLASSES) == sorted(T.ROLES)
    for table, (metadata, content) in C._CLASSES.items():
        meta, text = metadata.split(), content.split()
        assert not set(meta) & set(text) and len(set(meta)) == len(meta) and len(set(text)) == len(text), table
        assert sorted(meta + text) == sorted(schema[table]), (
            table, sorted(set(schema[table]) - set(meta + text)), sorted(set(meta + text) - set(schema[table])))
    assert C.column_class("model_call_receipts", "input_text") == C.CONTENT
    assert C.column_class("model_call_receipts", "output_text") == C.CONTENT
    assert C.column_class("model_call_receipts", "cost") == C.METADATA
    assert C.column_class("assessment_contract_versions", "contract_json") == C.CONTENT
    assert C.column_class("assessment_contract_versions", "practice_item_id") == C.METADATA


def test_every_derived_column_has_a_treatment(tmp_path):
    """Round 7: every column classified ``derived_by_position`` (a visible row's value ingest derived
    from other rows) names how AD reads it: recomputed by a named projection function that exists,
    or unread with a reason; and every treatment names a derived column."""

    import importlib

    derived = {(table, column) for table, columns in T.COLUMNS.items() for column, kind in columns.items()
               if kind == T.DERIVED}
    assert derived and derived == set(T.DERIVED_TREATMENT)
    for key, treatment in T.DERIVED_TREATMENT.items():
        kind, _sep, rest = treatment.partition(":")
        assert kind in ("chokepoint", "unread"), (key, treatment)
        assert rest.strip(), (key, "a treatment says how")
    from learnloop.adaptive_difficulty.material_view import MaterialView

    assert callable(MaterialView.document_ir) and callable(MaterialView.reading_withheld)
    assert importlib.import_module("learnloop.adaptive_difficulty.material_view")
    assert {("source_document_blocks", "role_hint"), ("source_document_blocks", "section_path_json")} <= derived


def test_every_table_with_a_reading_reference_is_a_reading_or_item_provenance(tmp_path):
    """Round 8 (Option B): every registry table that references a reading (an ``extraction``,
    ``span``, ``spans`` or ``section`` kind, a reading payload, a reading receipt's source, or a
    self rule over a reading's rows) is a READING table, whose references resolve against the
    reading, or named ITEM_PROVENANCE with why; a migration adding one fails here until classified."""

    reading_kinds = {"extraction", "span", "spans", "section", "reading_payload", "source"}
    self_reading = {"reader_authored_questions", "question_events", "ad_dose_offers"}
    referencing = {table for table, columns in T.COLUMNS.items()
                   if any(kind.partition("@")[0] in reading_kinds for kind in columns.values())} | self_reading
    assert referencing <= T.READING | set(T.ITEM_PROVENANCE), sorted(referencing - T.READING - set(T.ITEM_PROVENANCE))
    assert not T.READING & set(T.ITEM_PROVENANCE)
    assert all(reason.strip() for reason in T.ITEM_PROVENANCE.values())
    assert T.READING <= set(T.COLUMNS)
