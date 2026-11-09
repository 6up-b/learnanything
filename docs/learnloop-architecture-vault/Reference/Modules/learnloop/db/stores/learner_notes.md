---
title: "learnloop.db.stores.learner_notes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/learner_notes.py"
source_paths:
  - "src/learnloop/db/stores/learner_notes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.learner_notes module"
  - "src/learnloop/db/stores/learner_notes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.learner_notes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.learner_notes` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Deliverable curriculum C2's tables (migration 229): ``learner_notes`` (snapshots of the learner's notes, taken only when linked) and ``learner_note_links`` (the model's proposals and the learner's links and hides).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/learner_notes.py](../../../../../../../src/learnloop/db/stores/learner_notes.py) |
| Source lines | 306 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 33)
- `snapshot(connection: sqlite3.Connection, note_key: str, content_hash: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 52)
- `insert_note(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 58) — Store a snapshot once per (note, content hash); returns the stored row's id.
- `notes_by_id(connection: sqlite3.Connection, note_ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 68)
- `latest_note(connection: sqlite3.Connection, note_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 76)
- `latest_notes(connection: sqlite3.Connection, note_keys: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 82) — The newest snapshot of each note, by note key (creation order: not what a note shows, which is :func:`current_notes`).
- `current_notes(connection: sqlite3.Connection, task: str, note_keys: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 131) — The snapshot each note shows now, by note key (Codex re-review F13, round 3): the one named by the note's newest current-snapshot marker (``judgment_ledger`` task ``task``, ``right_id`` the snapshot's id).
- `current_fences(connection: sqlite3.Connection, task: str, note_keys: Iterable[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 141) — Each note's fence (C2 ruling R6): the read token of its newest current-snapshot marker (``""`` with none, or with a marker written before R6).
- `newest_read_token(connection: sqlite3.Connection, task: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 153) — The newest read token any current-snapshot marker carries, over every note (``""`` with none): the floor a new read's token is minted above (Codex review F2), so a token persisted while the clock ran ahead, before a restart, never fences off later reads.
- `note_count(connection: sqlite3.Connection) -> int` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 165)
- `insert_link(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 171)
- `links(connection: sqlite3.Connection, *, extraction_id: str | None=None, learning_object_ids: Iterable[str] | None=None, note_key: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 175) — Link rows, oldest first, narrowed by reading, LO or note (all of them with no filter).
- `links_by_id(connection: sqlite3.Connection, link_ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 197) — Link rows by id (append-only: a row read later says what it said when it was shown).
- `learner_rows_for(connection: sqlite3.Connection, note_keys: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 208) — The learner's own rows on these notes (their links and hides), oldest first.
- `ai_rows_for_state(connection: sqlite3.Connection, learning_object_id: str, state_key: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 219)
- `judged(connection: sqlite3.Connection, task: str, learning_object_id: str, state_key: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 225) — Was this topic's candidate state judged (the model's verdict rows in the ledger)?
- `topic_key(goal_id: str, learning_object_id: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 233) — A deliverable's topic as a shown-state marker names it.
- `current_states(connection: sqlite3.Connection, task: str, learning_object_ids: Iterable[str]) -> dict[tuple[str, str], str]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 239) — The candidate state each deliverable's topic shows now, by (goal, LO) (Codex review F7): the newest shown-state marker per topic, appended whenever the topic's candidate state changes (a state judged now, one judged before and reused, or no candidates).
- `takes_quoting_notes(connection: sqlite3.Connection, prefix: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 261) — RW4d takes written from a note (*use as my take*), counted by their quote's prefix.
- `link_counts(connection: sqlite3.Connection) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 273) — Aggregates for the report: rows by authorship and status (never a note's text).

### Module constants

- `NOTE_COLUMNS` ([src/learnloop/db/stores/learner_notes.py](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 22)
- `LINK_COLUMNS` ([src/learnloop/db/stores/learner_notes.py](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 26)

### Explicit exports

`__all__` declares:

- `LINK_COLUMNS`
- `NOTE_COLUMNS`
- `ai_rows_for_state`
- `insert_link`
- `current_notes`
- `current_fences`
- `current_states`
- `judged`
- `latest_notes`
- `topic_key`
- `takes_quoting_notes`
- `insert_note`
- `latest_note`
- `learner_rows_for`
- `link_counts`
- `links`
- `links_by_id`
- `newest_read_token`
- `note_count`
- `notes_by_id`
- `snapshot`
- `tables_present`

## Internal implementation anchors

- `_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 39)
- `_insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 44)
- `_read_token(rationale: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 97) — A marker's read token (C2 R6): the monotonic token its read took when it started.
- `_markers(connection: sqlite3.Connection, task: str, note_keys: Iterable[str]) -> dict[str, tuple[str, dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/learner_notes.py), line 109) — Each note's newest current-snapshot marker, in append order: (its read token, the snapshot it names).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `module`; statically calls `links`, `tables_present`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; statically calls `current_fences`, `current_notes`, `current_states`, `insert_link`, `insert_note`, `judged`, `learner_rows_for`, `link_counts`, `links`, `newest_read_token`, `notes_by_id`, `tables_present`, `takes_quoting_notes`, `topic_key`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `module`; statically calls `links`, `links_by_id`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]], [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]], [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../../tests/test_followups_batch5_recap_dependencies.py) — direct import
  - `test_f2_the_note_dependency_outlives_a_later_link_change`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing`
- [tests/test_notes_linked.py](../../../../../../../tests/test_notes_linked.py) — direct import
  - `test_legacy_tend_snapshots_stay_readable`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/learner_notes.py](../../../../../../../src/learnloop/db/stores/learner_notes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
