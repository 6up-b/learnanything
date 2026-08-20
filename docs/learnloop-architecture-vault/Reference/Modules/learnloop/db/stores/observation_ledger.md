---
title: "learnloop.db.stores.observation_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/observation_ledger.py"
source_paths:
  - "src/learnloop/db/stores/observation_ledger.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.stores.observation_ledger module"
  - "src/learnloop/db/stores/observation_ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.observation_ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.observation_ledger` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Bulk read models for the canonical evidence projection.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/observation_ledger.py](../../../../../../../src/learnloop/db/stores/observation_ledger.py) |
| Source lines | 283 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `load_canonical_observation_ledger(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/observation_ledger.py), line 29) — Load attempts plus live grading evidence in two queries.
- `load_authoritative_observation_ledger(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/observation_ledger.py), line 108) — Load the P0 authoritative ledger with a fixed six-query budget.
- `load_effective_assessment_contracts(connection: sqlite3.Connection, source_version_ids: Iterable[str], *, projection_version: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/observation_ledger.py), line 243) — Resolve immutable contract snapshots for a replay in one bulk query.

### Module constants

- `_LATEST_OBSERVATIONS` ([src/learnloop/db/stores/observation_ledger.py](../../../../../../../src/learnloop/db/stores/observation_ledger.py), line 95)

## Internal implementation anchors

- `_loads(value: str | None, default: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/observation_ledger.py), line 23)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `load_authoritative_observation_ledger`, `load_canonical_observation_ledger`, `load_effective_assessment_contracts`; statically calls `load_authoritative_observation_ledger`, `load_canonical_observation_ledger`, `load_effective_assessment_contracts`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_observation_ledger_bulk.py](../../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_observation_ledgers_have_constant_query_budget_and_stable_order`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/observation_ledger.py](../../../../../../../src/learnloop/db/stores/observation_ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
