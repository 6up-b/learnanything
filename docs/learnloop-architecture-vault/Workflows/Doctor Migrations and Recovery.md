---
title: Doctor Migrations and Recovery
aliases:
  - Vault Recovery Workflow
  - Migration and Doctor Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/ops/doctor.py
  - src/learnloop/migration_coordinator.py
  - src/learnloop/db/migrate.py
  - src/learnloop/vault/loader.py
  - src/learnloop/cli/app.py
  - tests/test_doctor.py
  - tests/test_migration_coordinator.py
  - tests/test_migrations.py
tags:
  - learnloop/workflow
  - learnloop/doctor
  - learnloop/migrations
  - learnloop/recovery
---

# Doctor Migrations and Recovery

`doctor` is the supported triage surface for vault layout, configuration, references, content contracts, SQLite state, migration status, stale projection markers, deprecated-row telemetry, and optional AI readiness. Recovery should preserve receipts and provenance; storage ownership is explained in [[State and Persistence]].

## Read-only diagnosis

Close or pause active work, then run:

```bash
VAULT="$HOME/LearnLoop/linear-algebra"

uv run learnloop doctor --json --vault "$VAULT"
```

Plain doctor opens SQLite read-only. It does not create a missing database, probe an AI provider, apply migrations, or sync state files. A non-clean result exits with status 1, so in automation retain and inspect its JSON instead of discarding output on nonzero exit.

To include provider composition/readiness:

```bash
uv run learnloop doctor --ai --json --vault "$VAULT"
```

An unavailable optional provider can coexist with a structurally clean vault; inspect `ai_runtime` separately from `clean`.

## Interpret severity before acting

| Finding | First action |
|---|---|
| unknown TOML key or invalid reference | correct the owning file/config with a backup |
| pending SQL migration | use the locked `--fix-state` path |
| incomplete apply intent/state sync | use `--fix-state`, then re-run plain doctor |
| nonzero deprecated-table row telemetry | stop and escalate; preserve rows |
| stale/missing derived rebuild marker | shadow compare, then justified live rebuild |
| AI auth/readiness error | [[Configure AI Providers]] |
| failed durable import | resume its batch, not global state repair |

> [!failure] Deprecated does not mean disposable
> A deprecated table with rows is evidence that compatibility migration or operator review is incomplete. Doctor deliberately reports `stop_and_escalate`; never delete those rows to make the check green.

## Repair path

1. Stop desktop, TUI, and sidecar writers.
2. Copy the entire vault to a separate backup location.
3. Save the plain-doctor JSON.
4. Run the mutation-enabled repair once:

```bash
uv run learnloop doctor --fix-state --json --vault "$VAULT"
```

5. Re-run plain doctor:

```bash
uv run learnloop doctor --json --vault "$VAULT"
```

`--fix-state` acquires the cross-process vault lock, applies pending migrations atomically, attaches the database writable, performs supported state synchronization, merges eligible legacy aliases, and resumes recoverable apply intents idempotently.

> [!important] Migration atomicity
> A migration receipt and its body commit together. If the process dies mid-migration, neither is retained; the next coordinated open can safely apply that version again.

Normal repository startup uses the same migration coordinator and lock. `--fix-state` is useful when ordinary startup cannot finish or when an operator needs an explicit repair receipt.

## Derived-state recovery

If doctor is clean structurally but identifies projection drift:

```bash
uv run learnloop rebuild --shadow --json --vault "$VAULT"
```

Require `live_database.unchanged: true`, review replay accounting, and only then consider the backed-up live path in [[Rebuild and Shadow Compare#Run a live rebuild only when justified]].

## Algorithm upgrades are separate

SQL migration makes storage readable by current code. `upgrade` changes the vault-wide knowledge/learning algorithm version and may project content/state under new semantics:

```bash
uv run learnloop upgrade --to mvp-0.9 --vault "$VAULT"
```

Upgrades are atomic and immediate-successor only:

```text
mvp-0.6 → mvp-0.7 → mvp-0.8 → mvp-0.9
```

Do not edit `algorithm_version` in TOML to skip a projection. Freshly initialized vaults are already mvp-0.9.

## Incident evidence to retain

- vault backup location and timestamp;
- doctor JSON before and after;
- command/version (`uv run learnloop --help`, Git commit);
- `schema_migrations` head (currently 156);
- related batch, attempt, agent-run, proposal, or rebuild-marker ids;
- sidecar logs when the issue crossed the desktop bridge.

## Recovery boundaries

- ingestion checkpoint failure → [[Import Canonical Sources#Resume, cancel, and retry]]
- session/checkpoint interruption → [[Continue a Learning Cycle]]
- invalid provider output → [[Process Model Output#Failure handling]]
- reproducible projection change → [[Rebuild and Shadow Compare]]
- file/database ownership questions → [[State and Persistence]] and [[Database Catalog]]

## Worked drill

[[Recovery and Rebuild Drill]] gives a non-destructive sequence suitable for rehearsing operator handoff.
