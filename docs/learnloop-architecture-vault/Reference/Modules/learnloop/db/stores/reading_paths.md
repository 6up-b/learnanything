---
title: "learnloop.db.stores.reading_paths"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/reading_paths.py"
source_paths:
  - "src/learnloop/db/stores/reading_paths.py"
source_commit: "c54ecedfa5118e990dee937eeb7741f8ccb4eb45"
source_commit_timestamp: "2026-10-25T12:09:24-04:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.reading_paths module"
  - "src/learnloop/db/stores/reading_paths.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.reading_paths`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.reading_paths` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reader workbench RW7a's tables (migration 217): ``reader_path_sections`` and ``reader_path_depths`` (WORKFLOW, append-only by trigger; display only).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/reading_paths.py](../../../../../../../src/learnloop/db/stores/reading_paths.py) |
| Source lines | 97 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c54ecedfa5118e990dee937eeb7741f8ccb4eb45` |
| Commit timestamp | `2026-10-25T12:09:24-04:00` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 23)
- `insert_depth(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 35)
- `latest_depth(connection: sqlite3.Connection, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 41)
- `insert_section(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 48)
- `judged(connection: sqlite3.Connection, extraction_id: str, depth: str, state_key: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 55) — The judge's rows for exactly this state (the cache hit).
- `latest_judged(connection: sqlite3.Connection, extraction_id: str, depth: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 63) — The judge's rows of the newest state judged at this depth (shown while a newer state is being judged).
- `overrides(connection: sqlite3.Connection, extraction_id: str, depth: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 75) — The newest learner override per section at this depth (kept across re-judgments); ``none`` is a cleared one.

### Module constants

- `SECTION_COLUMNS` ([src/learnloop/db/stores/reading_paths.py](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 16)
- `DEPTH_COLUMNS` ([src/learnloop/db/stores/reading_paths.py](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 20)

### Explicit exports

`__all__` declares:

- `DEPTH_COLUMNS`
- `SECTION_COLUMNS`
- `insert_depth`
- `insert_section`
- `judged`
- `latest_depth`
- `latest_judged`
- `overrides`
- `tables_present`

## Internal implementation anchors

- `_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/reading_paths.py), line 30)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; statically calls `insert_depth`, `insert_section`, `judged`, `latest_depth`, `latest_judged`, `overrides`, `tables_present`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_deliverable_path.py](../../../../../../../tests/test_deliverable_path.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]
- [tests/test_followups_batch6_prefetch_next_section.py](../../../../../../../tests/test_followups_batch6_prefetch_next_section.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]
- [tests/test_plan_follows_path.py](../../../../../../../tests/test_plan_follows_path.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../../tests/test_reader_rw6b_p2_landing.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]
- [tests/test_reading_paths.py](../../../../../../../tests/test_reading_paths.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]
- [tests/test_rw7b_codex_review_fixes.py](../../../../../../../tests/test_rw7b_codex_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/reading_paths.py](../../../../../../../src/learnloop/db/stores/reading_paths.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
