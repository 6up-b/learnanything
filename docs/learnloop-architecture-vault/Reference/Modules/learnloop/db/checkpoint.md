---
title: "learnloop.db.checkpoint"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/checkpoint.py"
source_paths:
  - "src/learnloop/db/checkpoint.py"
source_commit: "workspace/uncommitted @ HEAD df970cd96725b112447395846bb53a0164a5853c"
source_commit_timestamp: "2026-09-23T20:46:40-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.checkpoint module"
  - "src/learnloop/db/checkpoint.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.checkpoint`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.checkpoint` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Explicit WAL checkpoints after large writes.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/checkpoint.py](../../../../../../src/learnloop/db/checkpoint.py) |
| Source lines | 81 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD df970cd96725b112447395846bb53a0164a5853c` |
| Commit timestamp | `2026-09-23T20:46:40-04:00` |

## Public API

- `class CheckpointResult` ([source](../../../../../../src/learnloop/db/checkpoint.py), line 33) — ``PRAGMA wal_checkpoint`` output: busy flag, frames in the log, frames copied.
- `checkpoint_wal(sqlite_path: Path, *, reason: str, busy_timeout_ms: int=CHECKPOINT_BUSY_TIMEOUT_MS) -> CheckpointResult | None` ([source](../../../../../../src/learnloop/db/checkpoint.py), line 41) — Run ``PRAGMA wal_checkpoint(TRUNCATE)``; ``None`` when it could not run.

### Module constants

- `_LOG` ([src/learnloop/db/checkpoint.py](../../../../../../src/learnloop/db/checkpoint.py), line 27)
- `CHECKPOINT_BUSY_TIMEOUT_MS` ([src/learnloop/db/checkpoint.py](../../../../../../src/learnloop/db/checkpoint.py), line 29)

### Explicit exports

`__all__` declares:

- `CHECKPOINT_BUSY_TIMEOUT_MS`
- `CheckpointResult`
- `checkpoint_wal`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `checkpoint_wal`; statically calls `checkpoint_wal`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `checkpoint_wal`; statically calls `checkpoint_wal`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `checkpoint_wal`; statically calls `checkpoint_wal`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `checkpoint_wal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `logging`, `pathlib`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_a_long_read_transaction_delays_checkpoints_only_until_it_ends`
  - `test_checkpoint_is_a_no_op_for_a_rollback_database`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/checkpoint.py](../../../../../../src/learnloop/db/checkpoint.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
