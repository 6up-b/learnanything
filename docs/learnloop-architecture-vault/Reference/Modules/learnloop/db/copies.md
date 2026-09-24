---
title: "learnloop.db.copies"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/copies.py"
source_paths:
  - "src/learnloop/db/copies.py"
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
  - "learnloop.db.copies module"
  - "src/learnloop/db/copies.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.copies`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.copies` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Copies of SQLite databases and of directory trees that contain them.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD df970cd96725b112447395846bb53a0164a5853c` |
| Commit timestamp | `2026-09-23T20:46:40-04:00` |

## Public API

- `class DatabaseCopyTimeout(TimeoutError)` ([source](../../../../../../src/learnloop/db/copies.py), line 38) — The source stayed locked past the backup deadline; nothing was copied.
- `backup_database(source_path: Path, destination_path: Path, *, busy_deadline_s: float | None=None) -> None` ([source](../../../../../../src/learnloop/db/copies.py), line 42) — Write a transactionally consistent copy of a database to a new file.
- `is_database_file_name(name: str, database_names: Collection[str]=()) -> bool` ([source](../../../../../../src/learnloop/db/copies.py), line 92)
- `is_companion_file_name(name: str, database_names: Collection[str]=()) -> bool` ([source](../../../../../../src/learnloop/db/copies.py), line 96)
- `copy_tree_without_databases(source_root: Path, destination_root: Path, *, database_names: Collection[str]=(), ignore: IgnoreFunction | None=None, dirs_exist_ok: bool=False) -> list[Path]` ([source](../../../../../../src/learnloop/db/copies.py), line 103) — Copy a directory tree, leaving out every database and companion file.
- `copy_tree_with_databases(source_root: Path, destination_root: Path, *, database_names: Collection[str]=(), ignore: IgnoreFunction | None=None, dirs_exist_ok: bool=False) -> list[Path]` ([source](../../../../../../src/learnloop/db/copies.py), line 137) — Copy a directory tree, copying each database through the backup API.

### Module constants

- `DATABASE_SUFFIX` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 25)
- `BACKUP_BUSY_DEADLINE_S` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 27)
- `_BUSY_RETRY_SLEEP_S` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 28)
- `_SQLITE_BUSY` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 30)
- `_SQLITE_LOCKED` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 31)
- `_RETRIED_STATUSES` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 32)
- `COMPANION_SUFFIXES` ([src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py), line 33)

### Explicit exports

`__all__` declares:

- `BACKUP_BUSY_DEADLINE_S`
- `COMPANION_SUFFIXES`
- `DatabaseCopyTimeout`
- `backup_database`
- `copy_tree_with_databases`
- `copy_tree_without_databases`
- `is_companion_file_name`
- `is_database_file_name`

## Internal implementation anchors

- `_remove_database_files(database_path: Path) -> None` ([source](../../../../../../src/learnloop/db/copies.py), line 87)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `copy_tree_without_databases`; statically calls `copy_tree_without_databases`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `backup_database`; statically calls `backup_database`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `backup_database`; statically calls `backup_database`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `copy_tree_with_databases`, `copy_tree_without_databases`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `backup_database`; statically calls `backup_database`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `copy_tree_with_databases`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `pathlib`, `shutil`, `sqlite3`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]], [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_export_gives_up_on_a_source_locked_after_its_probe_and_removes_the_export`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_backup_copies_commits_that_a_byte_copy_of_the_main_file_loses`
  - `test_backup_gives_up_on_a_source_locked_after_its_probe_and_removes_the_copy`
  - `test_backup_refuses_to_overwrite_an_existing_file`
  - `test_tree_copy_backs_up_databases_and_never_copies_companions`
  - `test_tree_copy_without_databases_leaves_out_configured_names`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_tracked_fixture_databases.py](../../../../../../tests/test_tracked_fixture_databases.py) — direct import
  - `test_tracked_fixture_databases_are_rollback_mode_without_companions`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/copies.py](../../../../../../src/learnloop/db/copies.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
