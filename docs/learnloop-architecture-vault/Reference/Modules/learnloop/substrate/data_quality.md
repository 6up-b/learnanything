---
title: "learnloop.substrate.data_quality"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/data_quality.py"
source_paths:
  - "src/learnloop/substrate/data_quality.py"
source_commit: "97d74d1da8b0077e7cbaa42c9d934d5ba1106c3b"
source_commit_timestamp: "2026-09-23T15:31:55-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.data_quality module"
  - "src/learnloop/substrate/data_quality.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.data_quality`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.data_quality` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Read-only dataset diagnostics over a consistent SQLite read transaction.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/data_quality.py](../../../../../../src/learnloop/substrate/data_quality.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `97d74d1da8b0077e7cbaa42c9d934d5ba1106c3b` |
| Commit timestamp | `2026-09-23T15:31:55-04:00` |

## Public API

- `table_names(connection: sqlite3.Connection) -> set[str]` ([source](../../../../../../src/learnloop/substrate/data_quality.py), line 23)
- `rows(connection: sqlite3.Connection, table: str, *, columns: tuple[str, ...] | None=None, where: str='') -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/data_quality.py), line 31) — Read a table as dicts, optionally narrowed to the named columns.
- `data_quality_report(sqlite_path: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/data_quality.py), line 49)
- `inspect_collection(connection: sqlite3.Connection, *, splits: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/data_quality.py), line 55) — Coverage report over one connection.

### Module constants

- `_ATTEMPT_COLUMNS` ([src/learnloop/substrate/data_quality.py](../../../../../../src/learnloop/substrate/data_quality.py), line 16)
- `_CANDIDATE_COLUMNS` ([src/learnloop/substrate/data_quality.py](../../../../../../src/learnloop/substrate/data_quality.py), line 20)

## Internal implementation anchors

- `_quote(identifier: str) -> str` ([source](../../../../../../src/learnloop/substrate/data_quality.py), line 27)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `data_quality_report`; statically calls `data_quality_report`
- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `data_quality_report`; statically calls `data_quality_report`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `inspect_collection`, `rows`, `table_names`; statically calls `inspect_collection`, `rows`, `table_names`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`, `retention_exclusions`; calls `retention_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]], [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_doors_without_a_completion_phase_are_not_counted_as_interrupted`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_data_quality_report_outside_an_export_names_no_split_policy`
  - `test_exact_offer_survives_refresh_recovery_and_dataset_export`
  - `test_export_preserves_censored_repair_disposition_as_distinct_from_failure`
  - `test_scored_item_text_is_snapshotted_once_per_revision_and_exported`

## Modification guidance

- Change data quality policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/data_quality.py](../../../../../../src/learnloop/substrate/data_quality.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
