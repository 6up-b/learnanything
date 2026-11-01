"""Curriculum C1 (spec_deliverable_curriculum_v1 §7.6): the memo of the plan's fresh reading choice.

C1's invariant (Codex review fix round 2): *while the plan's reading block has no reading
history, the plan's reading is whatever a fresh build would choose right now* (C1's nearest
fresh deliverable, else RW7b's path, else the order, under the current switches and the
current freshness). The engine re-derives that choice on each reconcile of a plan whose
receipt is C1's (``engine._reading_follows_fresh_choice``). Deriving it reads the library,
the coverage and the learner context, so a plain plan read must not redo it on every call
(Codex review fix round 2, Low 6): this module memoizes it on a cheap **fingerprint** of its
inputs, read without a model call.

* **Taken before the inputs.** The engine takes the fingerprint before it gathers any input
  of the choice, so a write that lands while the choice is computed (a judgment, a coverage
  row, a section read) changes the *next* fingerprint and the choice is computed again; a
  stale memo entry can never outlive the write that made it stale.
* **Conservative.** An input it is unsure of is included: a needless recompute costs time,
  a missed input a stale plan. Every table the choice reads (and the ledgers whose rows its
  inputs derive from) contributes ``COUNT(*)`` and ``MAX(rowid)``, plus ``MAX(updated_at)``
  where the table has one; section progress, which is upserted in place, contributes its
  sums too. The engine adds the switches, the vault's goals, each deliverable's days left,
  the local and UTC dates and DL1's daily minutes (``parts``).
* **One vault object.** An entry also holds a weak reference to the loaded vault it was
  computed for: the desktop sidecar replaces that object on every reload (config, goals,
  learning objects and source sets are its files), so another object never hits.

No weight, margin or threshold: the memo changes when a choice is computed, never what it
is (a hit returns exactly what the computation returned for the same inputs).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import threading
import weakref
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Tables whose rows the fresh reading choice reads, directly or through the inputs it
#: derives (the deliverable path's state key and rows, RW7b's per-book path, the order, the
#: exam predicate, DL2's intent, the learning-object statuses): the tables a traced choice
#: read (``sqlite3`` authorizer over C1's fixtures: a fresh path, a stale one, an intent),
#: plus the ledgers those statuses derive from (attempts, the judgment ledger whose newest
#: id names the newest judgment). ``COUNT(*)`` and ``MAX(rowid)`` of each, and
#: ``MAX(updated_at)`` where the column exists. Not here: ``daily_plans`` and ``sessions``,
#: which the choice reads only for DL1's daily minutes (the engine passes that value), and
#: which the plan's own reads write.
FINGERPRINT_TABLES: tuple[str, ...] = (
    # C0b/C1: the deliverables, their inputs, the judge's and the learner's path rows, and
    # the judgment ledger (the newest judgment id).
    "deliverable_scope_resolutions", "deliverable_scope_inputs", "deliverable_path_sections", "judgment_ledger",
    # C0a: section coverage; RW7b: per-book path depths and rows.
    "section_coverage", "reader_path_depths", "reader_path_sections",
    # The library: sources, extractions, units held out or selected, the as-you-read imports.
    "source_artifacts", "source_revisions", "source_extraction_runs", "source_unit_selections",
    "source_held_out_signal_marks", "source_objects", "source_object_versions", "source_object_citations",
    "entity_source_links", "synthesis_manifests", "synthesis_runs", "library_asks",
    # DL2's intent and its commitments; assumptions; learner gaps.
    "commitments", "commitment_versions", "commitment_target_versions", "commitment_events",
    "assumption_decisions", "assumption_returns", "learner_gap_commitments", "learner_gap_check_advances",
    "learner_text_gap_reversals",
    # The statuses' evidence (demonstrated, learning): attempts and the derived state.
    "practice_attempts", "learning_object_mastery", "facet_capability_evidence", "fitted_parameters",
)
#: Large tables written once per extraction (a book's units, blocks and assets): their
#: newest rowid only (a deletion goes with its extraction run, counted above).
TAIL_TABLES: tuple[str, ...] = ("source_document_units", "source_document_blocks", "source_document_assets")
#: Tables rewritten in place, or deleted and reinserted, whose rowids need not move: their
#: sums too. Section progress is upserted (spans only grow, stamps set once); mastery is
#: upserted; capability evidence is deleted and reinserted on a rebuild. The reader events
#: the choice reads (answers, closed views, actions) by their kind's index.
_CONTENT_SQL: tuple[tuple[str, str], ...] = (
    ("reader_section_progress",
     "SELECT COUNT(*), COALESCE(MAX(rowid), 0), MAX(updated_at), TOTAL(spans_seen), TOTAL(span_count), "
     "COUNT(completed_at), COUNT(revealed_at) FROM reader_section_progress"),
    ("learning_object_mastery",
     "SELECT TOTAL(evidence_count), TOTAL(logit_mean), TOTAL(logit_variance), MAX(last_evidence_at) "
     "FROM learning_object_mastery"),
    ("facet_capability_evidence",
     "SELECT TOTAL(certification_credit), TOTAL(direct_positive_mass), TOTAL(direct_negative_mass), "
     "TOTAL(embedded_positive_mass), TOTAL(embedded_negative_mass), TOTAL(unexercised_supporting_mass) "
     "FROM facet_capability_evidence"),
    ("interaction_events",
     "SELECT COUNT(*), COALESCE(MAX(rowid), 0) FROM interaction_events WHERE kind >= 'reader_' AND kind < 'reader`'"),
)


def _columns(connection: sqlite3.Connection, table: str) -> set[str] | None:
    rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {str(row[1]) for row in rows} if rows else None


def _read(connection: sqlite3.Connection, sql: str) -> list[Any]:
    """One counter row. A counter that cannot be read (an older schema, a locked page)
    reads as a value no later read repeats: the memo misses rather than trusts it."""

    try:
        return list(connection.execute(sql).fetchone())
    except sqlite3.Error:
        return ["unreadable", os.urandom(16).hex()]


def table_counters(connection: sqlite3.Connection) -> list[Any]:
    """Cheap counters over every table the choice reads (no JSON parsing, no model)."""

    parts: list[Any] = []
    for table in FINGERPRINT_TABLES:
        columns = _columns(connection, table)
        if columns is None:
            parts.append([table, None])
            continue
        stamp = ", MAX(updated_at)" if "updated_at" in columns else ""
        parts.append([table, *_read(connection, f'SELECT COUNT(*), COALESCE(MAX(rowid), 0){stamp} FROM "{table}"')])
    for table in TAIL_TABLES:
        if _columns(connection, table) is None:
            parts.append([table, None])
            continue
        parts.append([table, *_read(connection, f'SELECT COALESCE(MAX(rowid), 0) FROM "{table}"')])
    for table, sql in _CONTENT_SQL:
        if _columns(connection, table) is None:
            parts.append([f"{table}:content", None])
            continue
        parts.append([f"{table}:content", *_read(connection, sql)])
    return parts


def fingerprint(repository: Any, parts: Mapping[str, Any]) -> str:
    """The fingerprint of the choice's inputs: the caller's ``parts`` and the table counters."""

    with repository.connection() as connection:
        counters = table_counters(connection)
    payload = {"parts": parts, "tables": counters}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Remembered:
    """A memoized choice: the reading (a ``ReadingTarget`` or None) and its path receipt."""

    reading: Any
    receipt: dict[str, Any] | None


@dataclass
class _Entry:
    fingerprint: str
    vault: weakref.ReferenceType[Any]
    reading: Any
    receipt: str | None


_LOCK = threading.Lock()
#: One entry per database (the latest choice computed for it in this process).
_MEMO: dict[str, _Entry] = {}


def _key(repository: Any) -> str:
    path = getattr(repository, "sqlite_path", None)
    return str(Path(path).resolve()) if path is not None else f"repository:{id(repository)}"


def _vault_ref(vault: Any) -> weakref.ReferenceType[Any] | None:
    try:
        return weakref.ref(vault)
    except TypeError:  # an object that takes no weak reference never hits
        return None


def recall(repository: Any, vault: Any, fingerprint_: str) -> Remembered | None:
    """The choice remembered for this database, vault object and fingerprint, else None.
    Copies: a caller may change what it gets without changing the memo."""

    with _LOCK:
        entry = _MEMO.get(_key(repository))
    if entry is None or entry.fingerprint != fingerprint_ or entry.vault() is not vault:
        return None
    return Remembered(reading=entry.reading, receipt=json.loads(entry.receipt) if entry.receipt is not None else None)


def remember(repository: Any, vault: Any, fingerprint_: str, reading: Any, receipt: Mapping[str, Any] | None) -> None:
    """Keep the choice computed for this fingerprint (replacing the database's previous one)."""

    ref = _vault_ref(vault)
    if ref is None:
        return
    entry = _Entry(fingerprint=fingerprint_, vault=ref, reading=copy.copy(reading),
                   receipt=json.dumps(receipt, sort_keys=False) if receipt is not None else None)
    with _LOCK:
        _MEMO[_key(repository)] = entry


def forget(repository: Any | None = None) -> None:
    """Drop the memo (one database's entry, or every entry)."""

    with _LOCK:
        if repository is None:
            _MEMO.clear()
        else:
            _MEMO.pop(_key(repository), None)


__all__ = ["FINGERPRINT_TABLES", "TAIL_TABLES", "Remembered", "fingerprint", "forget", "recall", "remember", "table_counters"]
