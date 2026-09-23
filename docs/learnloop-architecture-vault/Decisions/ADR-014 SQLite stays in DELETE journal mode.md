---
title: ADR-014 SQLite stays in DELETE journal mode
aliases:
  - SQLite journal mode decision
  - WAL decision
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-09-07
decision_status: accepted
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop/db/connection.py
  - src/learnloop/db/migrate.py
  - src/learnloop/substrate/shadow_rebuild.py
  - src/learnloop/substrate/dataset.py
  - scripts/benchmark_sqlite_concurrency.py
  - docs/reviews/artifacts/sqlite-concurrency.json
tags:
  - learnloop/decision
  - learnloop/persistence
  - learnloop/sqlite
---

# ADR-014 SQLite stays in DELETE journal mode

## Context

`state.sqlite` is the single transactional store for evidence, immutable receipts, workflow state and rebuildable projections. `learnloop.db.connection.connect` sets `foreign_keys = ON` and `busy_timeout = 5000` and leaves the journal mode and synchronous level at SQLite's defaults: a rollback journal (`DELETE`) with `synchronous = FULL`. Only fresh-database creation in `migrate._apply_fresh` builds under a `.tmp` name with an in-memory journal and `synchronous = OFF`, fsyncs the finished file once and renames it into place.

In rollback-journal mode a writer excludes readers while it commits, and a writer that spills its page cache holds an exclusive lock until commit. Two costs follow:

- **Reader stalls.** A read that cannot get its shared lock retries until `busy_timeout` and then fails with "database is locked". In the benchmark below, every reader failure was a full 5-second stall.
- **Live rebuild blackout.** A live rebuild runs as one transaction. Measured on a copy of `fixtures/linear_algebra`, readers were locked out for 0.14–0.40 s per rebuild. The blackout grows with vault size, and once it passes the 5 s busy timeout, reads fail (see [[Rebuild Ownership]]).

## Evidence

`scripts/benchmark_sqlite_concurrency.py` creates disposable databases in each mode with `synchronous = FULL` and a 5 s busy timeout. It runs one writer committing 2 KB rows and two readers each holding a 2 ms read snapshot, 200 operations per worker. The run of 2026-09-23 on btrfs (`--directory ~/.cache/pr5-bench`, SQLite 3.50.4; raw output in [sqlite-concurrency.json](../../reviews/artifacts/sqlite-concurrency.json)):

| Mode | Elapsed | Writer p50 / p95 | Reader busy failures | Integrity | Checkpoint |
|---|---:|---:|---|---|---|
| DELETE | 7.94 s | 36.7 / 39.3 ms | 2 (1 per reader), each a 5,000 ms stall | ok | n/a |
| WAL | 1.96 s | 9.4 / 10.0 ms | 0 | ok | PASSIVE moved 599/599 frames; TRUNCATE not busy |

On a filesystem with cheap fsync the two modes are close: the same run on tmpfs measured DELETE 0.44 s and WAL 0.41 s with no busy failures. The gap is therefore mostly the cost of fsync and of reader starvation, and it depends on the disk.

**The benchmark favours WAL.** WAL is about four times faster here, has a quarter of the writer latency, and has no reader stalls.

## Decision

Production keeps the default rollback journal for now. The benchmark is synthetic: it does not show that WAL's extra files and its checkpoint, crash and copy lifecycle are safe for every way LearnLoop opens, copies and publishes a vault database. The reader-stall and rebuild-blackout costs above are accepted until that has been checked.

Test-only settings (`synchronous = OFF`, `journal_mode = MEMORY` from `tests/conftest.py`) never become production configuration.

## What must be verified before switching to WAL

1. **Every file-level copy or publication of `state.sqlite`.** A WAL database's committed data can live in `state.sqlite-wal` until a checkpoint, so copying only the main file loses it. Shadow rebuild (`shadow_rebuild.py`) and dataset export (`dataset.py`) use the SQLite backup API, which is safe. Fresh creation renames a `.tmp` file into place, and that file must not be left in WAL mode with a live `-wal` beside it. Any other copier must also be found and checked: desktop backup or restore, test fixture copies, and user tools.
2. **Read-only opens.** `connect(..., read_only=True)` uses `mode=ro`. In WAL mode a read-only connection needs the `-shm` file or write access to the directory. Check doctor, `data-quality` and the sidecar's read paths on read-only media and on permission-restricted vault directories.
3. **Where vaults live.** WAL requires shared memory, and network filesystems do not support it. File-sync services must never sync a `-wal`/`-shm` pair that is out of step with the main file. The vault's documented locations and the desktop's vault picker need an explicit rule.
4. **Checkpoint behaviour under the real workload.** Long-lived desktop read transactions can stop checkpoints and let the WAL grow. Decide who runs checkpoints (automatic, or explicit after rebuilds and ingest batches) and how large the WAL may grow.
5. **Durability level.** Decide whether WAL runs with `synchronous = FULL` or `NORMAL`. `NORMAL` can lose the most recent commits on power loss, including attempts the learner has already seen acknowledged.
6. **Migration and locking interaction.** Migrations run under the vault lock and toggle `PRAGMA foreign_keys` around table rebuilds (see [[ADR-008 Coordinated atomic migrations and read-only inspection]]). Journal mode is persistent in the file header, so switching needs exclusive access and a one-way upgrade step, and older builds must still be able to open the file.
7. **Tracked fixtures.** Opening `fixtures/*/state.sqlite` in WAL mode would leave `-wal`/`-shm` files in the working tree.
8. **Benchmark on the target platforms.** Re-run `scripts/benchmark_sqlite_concurrency.py` on Windows (on-access scanning) and macOS, and measure a live rebuild of a large vault under both modes.

## Consequences

- A live rebuild blocks readers for its commit window, and a long one can make reads fail with "database is locked". The sidecar maps that error to the retryable `database_busy` code.
- Writers remain serialized by SQLite either way. Repository scopes (`pinned`, `atomic`) keep each unit of work in one transaction.
- Revisit this decision when a vault's live rebuild approaches the busy timeout, or when the checks above have been done.

## Alternatives considered

- **Switch to WAL now.** The numbers favour it, but the copy, read-only and sync-folder behaviour listed above has not been checked.
- **Split telemetry into a second database.** Rejected: it adds a consistency boundary between evidence and the receipts that describe it (see [[Collection and Dataset Contract]]).
- **Raise `busy_timeout`.** This makes stalls longer rather than rarer. The 5 s value matches the benchmark and production.

## Related notes

- [[State and Persistence]]
- [[Rebuild Ownership]]
- [[Collection and Dataset Contract]]
- [[Privacy and Trust Boundaries]]
