---
title: "learnloop.db.stores.collection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/collection.py"
source_paths:
  - "src/learnloop/db/stores/collection.py"
source_commit: "a75d8d53c0301a2ef01724da4f02bdbcb87df51a"
source_commit_timestamp: "2026-09-23T13:00:04-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.collection module"
  - "src/learnloop/db/stores/collection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.collection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.collection` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Immutable entry-point provenance for versioned local data collection.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py) |
| Source lines | 124 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a75d8d53c0301a2ef01724da4f02bdbcb87df51a` |
| Commit timestamp | `2026-09-23T13:00:04-04:00` |

## Public API

- `class CollectionStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 41)
  - `finalize_scheduler_offer(self, slate_id: str | None, candidate_ids: list[str], *, entry_surface: str='desktop_queue') -> None` (line 42; public)
  - `record_false_remediation(self, *, attempt_id: str, value: bool, evidence_refs: list[dict[str, str]], author_kind: str, verifier_version: str) -> str` (line 60; public)
  - `bind_submission_offer(self, *, submission_id: str | None, session_id: str, practice_item_id: str, scheduler_candidate_id: str | None, entry_surface: str='desktop_practice') -> str | None` (line 77; public) — Return the scheduler offer a submission answers, binding it on first use.

### Module constants

- `_EVIDENCE_ROLES` ([src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py), line 12)

## Internal implementation anchors

- `_single_primary_key(connection: sqlite3.Connection, table: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 15) — The table's one primary-key column, or None for rowid or composite keys.
- `_check_evidence_reference(connection: sqlite3.Connection, reference: object) -> None` ([source](../../../../../../../src/learnloop/db/stores/collection.py), line 22)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CollectionStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `TABLE_ROLES`, `TableRole`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_collection_dataset.py](../../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_writers_stamp_the_current_collection_version`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/collection.py](../../../../../../../src/learnloop/db/stores/collection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
