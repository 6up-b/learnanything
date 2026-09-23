---
title: ADR-015 SQLite runs in WAL mode with synchronous FULL
aliases:
  - WAL decision
  - SQLite journal mode decision
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-09-23
decision_status: accepted
supersedes: ADR-014 SQLite stays in DELETE journal mode
last_reviewed: 2026-09-23
source_commit: e1153c01d0c6e29e6c4f97f1f4fa1e5214914f73
source_commit_timestamp: "2026-09-23T18:50:00-04:00"
source_paths:
  - src/learnloop/db/connection.py
  - src/learnloop/db/migrate.py
  - src/learnloop/db/copies.py
  - src/learnloop/db/checkpoint.py
  - src/learnloop/db/storage.py
  - src/learnloop/migration_coordinator.py
  - src/learnloop/ops/doctor.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/substrate/shadow_rebuild.py
  - src/learnloop/substrate/dataset.py
  - src/learnloop/content/pipeline/runner.py
  - scripts/benchmark_sqlite_concurrency.py
  - docs/reviews/artifacts/sqlite-concurrency.json
  - tests/test_sqlite_wal.py
  - tests/test_sqlite_wal_lifecycle.py
  - tests/test_sqlite_file_copies.py
  - tests/test_tracked_fixture_databases.py
tags:
  - learnloop/decision
  - learnloop/persistence
  - learnloop/sqlite
---

# ADR-015 SQLite runs in WAL mode with synchronous FULL

## Context

[[ADR-014 SQLite stays in DELETE journal mode]] kept the rollback journal and listed eight checks that had to be done before switching to WAL. Under the rollback journal a writer that spills its page cache holds an exclusive lock until commit, so readers stall for up to the 5 s busy timeout and then fail, and a live rebuild blacks out every reader for part of its transaction. The owner decided to switch, on condition that each check is either done in code with a test or recorded here as pending with its reason.

## Decision

- **WAL with `synchronous = FULL`.** Every vault database runs in WAL mode. Writable connections set `synchronous = FULL`, so each commit is fsynced before it is acknowledged.
- **One-way switch in the migration path.** `apply_migrations` switches an existing database once, before its pending migrations, on the connection it migrates with. Application opens reach it through `migrate_vault` under the vault lock. `connect()` never changes the mode.
- **Fresh databases are WAL from the start.** `_apply_fresh` switches the finished `.tmp` build to WAL and closes its only connection before the rename. That close checkpoints the build and removes its `-wal` and `-shm`.
- **Copies use the backup API.** Every copy of a database that may be live goes through `learnloop.db.copies`.
- **Explicit checkpoints after bursts.** SQLite's automatic checkpoint stays on. Explicit `TRUNCATE` checkpoints run after live rebuilds, finished ingest batches and `doctor --fix-state`.

`tests/conftest.py` keeps the fast lane on `journal_mode = MEMORY` and `synchronous = OFF`, and the fast lane skips the switch. The `durability` marker and `--durable-sqlite` run the production path: WAL with `synchronous = FULL`.

## The eight checks

| # | Check | Status | Where |
|---|---|---|---|
| 1 | Every file-level copy or publication | Done | `db/copies.py`; `tests/test_sqlite_file_copies.py` |
| 2 | Read-only opens | Done on Linux | `connect(read_only=True)`; `tests/test_sqlite_wal.py` |
| 3 | Where vaults live | Partly done | doctor `storage:network_filesystem`; [[State and Persistence#Where a vault may live]] |
| 4 | Checkpoint behaviour | Done | `db/checkpoint.py`; doctor storage line |
| 5 | Durability level | Decided: FULL | `connect()` |
| 6 | Migration and locking | Done | `migrate.switch_to_wal`; `tests/test_sqlite_wal.py` |
| 7 | Tracked fixtures | Done | `.gitignore`; `tests/test_tracked_fixture_databases.py`; session-end check in `tests/conftest.py` |
| 8 | Benchmark on target platforms | Linux done; Windows and macOS pending | [sqlite-concurrency.json](../../reviews/artifacts/sqlite-concurrency.json) |

### 1. File-level copies

In WAL mode a committed transaction can sit in `state.sqlite-wal` until a checkpoint. A byte copy of the main file alone can therefore drop acknowledged commits, and copying the main file and its `-wal` during a write can pair pages from two different moments.

- **Backup API.** `backup_database` copies a database in one backup step, which reads a single snapshot. `copy_tree_with_databases` and `copy_tree_without_databases` never byte-copy a `*.sqlite` file, the configured `storage.sqlite_path` name, or a `-wal`, `-shm` or `-journal` companion.
- **Callers.** The goal-series and scoreboard scratch replays, `prepare_run_vault` for simulations, the proposal staging tree and the test template vault use these helpers.
- **Other copiers.** Shadow rebuild already used the backup API, and its isolation digest now covers the main file followed by its `-wal`. Dataset export switches its published `snapshot.sqlite` to a rollback journal, so the export is one self-contained file.
- **Guard test.** `tests/test_sqlite_file_copies.py` finds every `copyfile`, `copy2`, `copytree` and `shutil.copy` call under `src/`, `tests/` and `scripts/`. It fails unless the file is listed with its audited call count and the reason the copy is safe.
- **Desktop shell.** The Rust shell has no database copier. Its vault watcher only reacts to `.yaml`, `.yml`, `.md`, `.toml` and `.json` files, so `-wal` and `-shm` changes do not trigger reloads.
- **Pending: user copies.** A person who copies a vault folder while LearnLoop is running can still copy a mismatched pair. The rule is in [[State and Persistence#Copying and backing up a vault]]. There is no desktop backup or restore feature to check.

### 2. Read-only opens

A read-only connection to a WAL database needs the `-shm` file, or write access to the directory so it can create one.

- **Fallback to `immutable=1`.** `connect(read_only=True)` opens with `mode=ro` and probes with one read. Only when that read fails because the directory is read-only, and no non-empty `-wal` exists, does it reopen with `immutable=1`. Neither a WAL writer nor a rollback writer can work in that directory, so the database cannot change while it is open.
- **Uncheckpointed WAL in a read-only directory.** If the directory is read-only and the `-wal` holds commits, the open fails with a message to use a writable copy. With `immutable=1` those commits would be silently missing.
- **Tested.** `tests/test_sqlite_wal.py` runs doctor, `data-quality` and `usage` against a vault directory set to mode 555. It also opens a database whose `-wal` and `-shm` are absent, and one whose `-wal` holds a commit that has not been checkpointed.
- **Sidecar.** The sidecar needs a writable vault. It migrates, syncs state and writes evidence, so a read-only vault fails at load with an operating-system or SQLite error. It has no separate read path.
- **Leftover files.** A read-only connection cannot delete the `-wal` and `-shm` it creates, so they stay beside the database after it closes. The next writer reuses them.
- **Pending.** Tests used `chmod` on Linux, not real read-only media, and macOS and Windows are not tested.

### 3. Where vaults live

WAL keeps its index in a memory-mapped `-shm` file that every connection shares. Network filesystems do not share that memory between hosts.

- **Doctor warning.** On Linux, doctor reads `/proc/mounts` and warns with `storage:network_filesystem` when the database is on NFS, SMB/CIFS, 9p, virtiofs, another network filesystem or any FUSE mount. On other platforms it skips the check.
- **Sync folders.** The rule for sync folders is in [[State and Persistence#Where a vault may live]].
- **Pending.** The desktop vault picker applies no rule and needs a change in the desktop app. Mount detection on macOS and Windows is not implemented.

### 4. Checkpoints

- **Explicit TRUNCATE checkpoints.** The automatic `PASSIVE` checkpoint runs every 1000 pages but never shrinks the `-wal`. `checkpoint_wal` runs `PRAGMA wal_checkpoint(TRUNCATE)` on its own short-lived connection with a 250 ms busy timeout. It runs after `rebuild_live_derived_state` (the `rebuild-derived-state` command), when an ingest batch becomes terminal, and in `doctor --fix-state`. A busy result is logged at INFO and does not raise; the next checkpoint catches up.
- **Doctor.** Doctor reports the `-wal` size in its `storage` block and on a text line. It warns with `sqlite:wal_large` above 64 MiB.
- **Long readers.** A test holds a read transaction open while 200 commits land. The checkpoint reports busy while the reader is open, and once it ends the next checkpoint empties the `-wal`.
- **Queue builds.** Twenty persisted queue builds on a copy of `fixtures/linear_algebra`, with a reader connection open throughout, grew the `-wal` by about 12 KB per build, to 288 KB. The `TRUNCATE` checkpoint then emptied it without waiting.

### 5. Durability level

`synchronous = FULL`. The follow-up option is `NORMAL`, under which WAL commits are not fsynced; the `-wal` is synced only at checkpoints. An application crash loses nothing under `NORMAL`, and the database stays consistent after power loss. However, the most recent commits can roll back after a power loss or OS crash. Those include attempts, grades and model-call receipts that the learner or a provider bill has already seen acknowledged. `NORMAL` would lower writer latency by removing one fsync per commit. That gain has not been measured for this workload, and it must be weighed against losing acknowledged evidence before the owner chooses it.

### 6. Migration and locking

- **The switch.** `switch_to_wal` reads the current mode and returns if it is already WAL. Otherwise it sets it, outside any transaction. Idle connections elsewhere do not block the switch. A connection holding a read or write transaction does: after the busy timeout, `JournalModeSwitchError` names the cause and leaves the header unchanged. A filesystem that refuses WAL raises the same error.
- **Connections close explicitly.** Migration connections are closed explicitly, not left to the garbage collector.
- **Orphaned companions.** A `-wal`, `-shm` or `-journal` left beside a missing database is deleted before a fresh database is created, because SQLite would replay its frames into the new file.
- **Opens without the lock.** `Repository(path)` still migrates without the vault lock. Once a vault has been opened by any locked entry point it is already WAL, so this path never switches.
- **Older builds.** SQLite has opened WAL files since 3.7.0, so older LearnLoop builds still open a converted vault. They do run their byte-copy scratch replays, which can miss commits that are still in the `-wal`. This affects only those scratch results, never the live database.
- **Minimum SQLite version.** `connect()` checks the runtime SQLite version once and fails below 3.22.0, the first release that reads a WAL database read-only without write access to its `-shm`.
- **Back to rollback.** To return a vault to a rollback journal, close every LearnLoop process and run `sqlite3 state.sqlite 'PRAGMA journal_mode=DELETE'`. The next migration switches it back.

### 7. Tracked fixtures

- **Ignored companions.** `.gitignore` ignores `*.sqlite-wal` and `*.sqlite-shm` everywhere.
- **Tests copy first.** Every writable use of a tracked fixture copies it first. `applied_versions` reads `fixtures/migration_head_165/state.sqlite` in place, but only read-only and on a rollback-mode file, which creates no companions.
- **Fixture checks.** `tests/test_tracked_fixture_databases.py` asserts that every fixture database has a rollback header and no companion files. `tests/conftest.py` records the same state at session start and fails the run if it has changed at session end.
- **Headers stay rollback.** Tracked fixture headers are not converted. A copy converts when it is migrated.

### 8. Benchmark

The 2026-09-23 run on btrfs (`--iterations 200 --directory ~/.cache/pr5-wal-bench --fixture fixtures/linear_algebra`, SQLite 3.50.4, Linux) is in [sqlite-concurrency.json](../../reviews/artifacts/sqlite-concurrency.json).

| Mode | Elapsed | Writer p50 / p95 | Reader busy failures |
|---|---:|---:|---|
| DELETE | 7.95 s | 36.6 / 45.5 ms | 2 (1 per reader), each a 5,000 ms stall |
| WAL | 2.07 s | 9.5 / 12.4 ms | 0; PASSIVE moved 599/599 frames, TRUNCATE not busy |

The live-rebuild measurement used a copy of `fixtures/linear_algebra` (46 MB database) with a read-only reader polling every 1 ms, over three consecutive rebuilds per mode:

| Mode | Rebuild time | Longest reader blackout |
|---|---:|---:|
| DELETE | 0.81–0.85 s | 0.466, 0.227, 0.198 s |
| WAL | 0.78 s | 0.013, 0.011, 0.013 s |

The earlier DELETE measurement was 0.40, 0.16 and 0.14 s. Under WAL the remaining gap is the reader thread waiting for Python's interpreter lock while the rebuild runs in the same process, not a database lock. The three WAL rebuilds grew the `-wal` to 7.2 MB, and a TRUNCATE checkpoint emptied it in 17 ms.

Windows (on-access scanning) and macOS runs are pending.

## Consequences

- **Readers do not wait for writers.** Readers keep their snapshot while a writer commits, and a live rebuild no longer blacks out readers.
- **Writers are still serialized.** Repository scopes (`pinned`, `atomic`) still keep each unit of work in one transaction.
- **Companion files.** `state.sqlite-wal` and `state.sqlite-shm` exist beside the database while any connection is open. Closing the last writable connection checkpoints and removes them. A vault folder must not be copied or synced while LearnLoop runs (see [[State and Persistence#Copying and backing up a vault]]).
- **Network and FUSE mounts.** Vaults on network or FUSE mounts are unsupported, and doctor warns about them.
- **Migration can refuse.** The first migration after upgrading can fail with `JournalModeSwitchError` if another process holds a transaction on the database. Closing it and retrying finishes the switch.

## Alternatives considered

- **Stay in DELETE mode.** Rejected: its reader stalls and the rebuild blackout grow with vault size, and every check above could be done.
- **WAL with `synchronous = NORMAL`.** Deferred: see check 5.
- **Switch the mode in `connect()`.** Rejected: every open would contend for the exclusive lock the switch needs, and an open that fails to switch would leave the mode depending on which process opened first.

## Related notes

- [[ADR-014 SQLite stays in DELETE journal mode]]
- [[ADR-008 Coordinated atomic migrations and read-only inspection]]
- [[State and Persistence]]
- [[Rebuild Ownership]]
- [[Doctor Migrations and Recovery]]
- [[Collection and Dataset Contract]]
