---
title: "learnloop.db.stores.section_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/section_coverage.py"
source_paths:
  - "src/learnloop/db/stores/section_coverage.py"
source_commit: "28c697869e348eba290381ac6155c5704df2e707"
source_commit_timestamp: "2026-10-25T17:16:18-04:00"
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
  - "learnloop.db.stores.section_coverage module"
  - "src/learnloop/db/stores/section_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.section_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.section_coverage` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Deliverable curriculum C0a's table (migration 222): ``section_coverage`` (WORKFLOW, append-only by trigger; display and retrieval context only).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/section_coverage.py](../../../../../../../src/learnloop/db/stores/section_coverage.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `28c697869e348eba290381ac6155c5704df2e707` |
| Commit timestamp | `2026-10-25T17:16:18-04:00` |

## Public API

- `table_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 22)
- `insert(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 41)
- `judged(connection: sqlite3.Connection, learning_object_id: str, state_key: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 47) — The judge's rows for exactly this LO and state (the cache hit).
- `judged_states(connection: sqlite3.Connection, learning_object_ids: Iterable[str]) -> dict[str, list[list[dict[str, Any]]]]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 55) — Per LO, every judgment's judge rows (one list per state key), newest judgment first; each list in candidate order.
- `learning_objects_named(connection: sqlite3.Connection, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 75) — Every LO any row (judge or learner) names for this section, oldest first.
- `corrections(connection: sqlite3.Connection, *, learning_object_ids: Iterable[str] | None=None, sections: Iterable[tuple[str, str]] | None=None) -> dict[tuple[str, str, str], dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 83) — The newest learner row per (reading, section, LO) (``none`` is a cleared one), for these LOs or these sections.
- `counts(connection: sqlite3.Connection) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 106) — Aggregates only (for reports): judge rows, learner rows, LOs judged.

### Module constants

- `COLUMNS` ([src/learnloop/db/stores/section_coverage.py](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 15)

### Explicit exports

`__all__` declares:

- `COLUMNS`
- `corrections`
- `counts`
- `insert`
- `judged`
- `judged_states`
- `learning_objects_named`
- `table_present`

## Internal implementation anchors

- `_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/section_coverage.py), line 27)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `judged_states`, `table_present`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; statically calls `corrections`, `insert`, `judged`, `judged_states`, `learning_objects_named`, `table_present`

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

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_section_coverage.py](../../../../../../../tests/test_section_coverage.py) — direct import
  - `test_the_table_is_append_only`
- [tests/test_section_coverage_review.py](../../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_rr_f10_a_crash_after_the_proposals_is_recovered_from_the_ledger`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/section_coverage.py](../../../../../../../src/learnloop/db/stores/section_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
