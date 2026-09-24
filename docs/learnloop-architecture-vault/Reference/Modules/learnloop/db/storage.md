---
title: "learnloop.db.storage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/storage.py"
source_paths:
  - "src/learnloop/db/storage.py"
source_commit: "8a3586fadb840cea61417b11816fd9c346e2d0fd"
source_commit_timestamp: "2026-09-23T18:49:46-04:00"
source_worktree_state: "clean"
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
  - "learnloop.db.storage module"
  - "src/learnloop/db/storage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.storage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.storage` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Side-effect-free facts about where and how a SQLite database is stored.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py) |
| Source lines | 188 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8a3586fadb840cea61417b11816fd9c346e2d0fd` |
| Commit timestamp | `2026-09-23T18:49:46-04:00` |

## Public API

- `class MountEntry` ([source](../../../../../../src/learnloop/db/storage.py), line 52)
  - `network_or_fuse(self) -> bool` (line 58; public)
- `class DatabaseStorage` ([source](../../../../../../src/learnloop/db/storage.py), line 63) — Journal mode, WAL size and filesystem of one database file.
  - `as_dict(self) -> dict[str, Any]` (line 70; public)
- `is_network_or_fuse_filesystem(filesystem_type: str) -> bool` ([source](../../../../../../src/learnloop/db/storage.py), line 80)
- `header_journal_mode(sqlite_path: Path) -> str` ([source](../../../../../../src/learnloop/db/storage.py), line 85) — ``"wal"``, ``"rollback"``, or ``"unknown"`` from the file header alone.
- `wal_size_bytes(sqlite_path: Path) -> int` ([source](../../../../../../src/learnloop/db/storage.py), line 103)
- `read_mount_table(mounts_file: Path=DEFAULT_MOUNTS_FILE) -> list[MountEntry] | None` ([source](../../../../../../src/learnloop/db/storage.py), line 118) — Parsed mount table, or ``None`` where there is none to read (non-Linux).
- `mount_for_path(path: Path, mounts: list[MountEntry]) -> MountEntry | None` ([source](../../../../../../src/learnloop/db/storage.py), line 142) — The mount with the longest mount point containing ``path``.
- `inspect_database_storage(sqlite_path: Path, *, mounts_file: Path=DEFAULT_MOUNTS_FILE) -> DatabaseStorage` ([source](../../../../../../src/learnloop/db/storage.py), line 162)

### Module constants

- `NETWORK_FILESYSTEM_TYPES` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 19)
- `_HEADER_SIZE` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 43)
- `_WAL_FORMAT_VERSION` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 44)
- `_ROLLBACK_FORMAT_VERSION` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 45)
- `_SQLITE_MAGIC` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 46)
- `DEFAULT_MOUNTS_FILE` ([src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py), line 48)

### Explicit exports

`__all__` declares:

- `DEFAULT_MOUNTS_FILE`
- `DatabaseStorage`
- `MountEntry`
- `NETWORK_FILESYSTEM_TYPES`
- `header_journal_mode`
- `inspect_database_storage`
- `is_network_or_fuse_filesystem`
- `mount_for_path`
- `read_mount_table`
- `wal_size_bytes`

## Internal implementation anchors

- `_unescape_mount_field(field: str) -> str` ([source](../../../../../../src/learnloop/db/storage.py), line 111)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `DatabaseStorage`, `inspect_database_storage`; statically calls `inspect_database_storage`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `sys`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_production_lane_and_live_backup_preserve_committed_state`
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_a_long_read_transaction_delays_checkpoints_only_until_it_ends`
  - `test_affected_sqlite_leaves_databases_in_rollback_mode_and_doctor_says_why`
  - `test_checkpoint_is_a_no_op_for_a_rollback_database`
  - `test_connect_sets_production_pragmas_and_never_changes_the_journal_mode`
  - `test_fixed_sqlite_switches_to_wal_and_doctor_is_quiet`
  - `test_fresh_database_is_created_in_wal_mode_without_companion_files`
  - `test_idle_connection_elsewhere_does_not_block_the_switch`
  - `test_migration_switches_an_existing_rollback_database_to_wal`
  - `test_read_only_open_in_a_read_only_directory_reads_commits_still_in_the_wal`
  - `test_read_only_reports_work_in_a_read_only_vault_whose_wal_files_exist`
  - `test_switch_fails_clearly_and_leaves_the_mode_unchanged_while_a_reader_is_open`
  - `test_switch_in_a_read_only_directory_names_the_directory_and_changes_nothing`
  - `test_switch_on_a_read_only_file_names_the_file_and_changes_nothing`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_doctor_warns_when_the_vault_is_on_a_network_mount`
  - `test_finished_ingest_batch_truncates_the_wal`
  - `test_header_journal_mode_reads_the_file_format_bytes`
  - `test_live_rebuild_truncates_the_wal_it_grew`
  - `test_mount_table_parsing_picks_the_deepest_mount_and_unescapes_spaces`
  - `test_network_and_fuse_filesystems_are_recognised`
  - `test_sim_run_vault_keeps_commits_still_in_the_source_wal`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_tracked_fixture_databases.py](../../../../../../tests/test_tracked_fixture_databases.py) — direct import
  - `test_tracked_fixture_databases_are_rollback_mode_without_companions`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/storage.py](../../../../../../src/learnloop/db/storage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
