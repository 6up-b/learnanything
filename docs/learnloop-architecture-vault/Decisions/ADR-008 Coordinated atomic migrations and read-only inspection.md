---
title: ADR-008 Coordinated atomic migrations and read-only inspection
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/migration_coordinator.py
  - src/learnloop/db/migrate.py
  - src/learnloop/db/connection.py
  - src/learnloop/ops/doctor.py
tags:
  - learnloop/decision
  - learnloop/migration
  - learnloop/persistence
---

# ADR-008 Coordinated atomic migrations and read-only inspection

## Context

Relocatable SQLite paths cannot identify the vault lock by themselves. Concurrent app opens can race migrations, `executescript` breaks outer transaction assumptions, and a diagnostic that constructs a normal repository can mutate the database merely by inspecting it.

## Decision

Application opens supply vault root plus DB path to a lock-taking migration coordinator, then attach. Incremental migration body and receipt are one transaction; FK rebuilds restore enforcement. Plain doctor attaches physically read-only and reports pending work without migrating.

## Consequences

- Normal CLI/TUI/sidecar opens serialize correctly.
- Path-only `Repository(path)` remains a documented compatibility constructor, not the preferred app open path.
- Doctor `--fix` is an explicit mutation boundary.

## Enforcement

Two-process normal-open race, process-death rollback, real migration-153 interruption, read-only pre-044 hash, missing-DB preservation, FK and trigger parsing tests. See [[State and Persistence#Open modes and migrations]].

