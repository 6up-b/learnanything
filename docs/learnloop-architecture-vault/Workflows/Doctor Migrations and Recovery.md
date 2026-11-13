---
title: Doctor Migrations and Recovery
aliases:
  - Vault Recovery Workflow
  - Migration and Doctor Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: e1153c01d0c6e29e6c4f97f1f4fa1e5214914f73
source_commit_timestamp: "2026-09-23T18:50:00-04:00"
source_paths:
  - src/learnloop/ops/doctor.py
  - src/learnloop/db/storage.py
  - src/learnloop/db/checkpoint.py
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

Plain doctor opens SQLite read-only. It does not create a missing database, probe an AI provider, apply migrations, or sync state files. It works on a vault in a read-only directory while the `-wal` and `-shm` files exist, for example while the desktop app has the vault open. Without them, it reports `sqlite:unreadable` with a message saying to allow creating files in the vault directory or to read a consistent copy (see [[State and Persistence#Journal mode and durability]]). A non-clean result exits with status 1, so in automation retain and inspect its JSON instead of discarding output on nonzero exit.

### Storage report

Doctor reads the state database's journal mode from its header, the `-wal` size from the file system, and, on Linux, the filesystem type from `/proc/mounts`. It opens nothing to do so. The JSON carries them as `storage`:

```json
"storage": {
  "journal_mode": "wal",
  "wal_bytes": 0,
  "filesystem_type": "btrfs",
  "mount_point": "/home",
  "network_or_fuse": false
}
```

Text output prints the same facts on one line before the issues, for example `storage: journal_mode=wal wal_bytes=0 filesystem=btrfs`. `journal_mode` is `rollback` for a database that no migration has switched yet. `filesystem_type` and `mount_point` are null outside Linux.

To include provider composition/readiness:

```bash
uv run learnloop doctor --ai --json --vault "$VAULT"
```

An unavailable optional provider can coexist with a structurally clean vault; inspect `ai_runtime` separately from `clean`.

`uv run learnloop doctor --data-quality --vault "$VAULT"` prints the collection-coverage report of `learnloop data-quality` and returns without running the doctor checks, so `--fix-state` and `--ai` have no effect with it. See [[Collection and Dataset Contract#Commands]].

## Interpret severity before acting

| Finding | First action |
|---|---|
| unknown TOML key or invalid reference | correct the owning file/config with a backup |
| pending SQL migration | use the locked `--fix-state` path |
| incomplete apply intent/state sync (`apply_intents:pending`) | reopen the vault in the app (it recovers at bind) or use `--fix-state`, then re-run plain doctor |
| `apply_intents:conflicted` error | a proposal apply stopped because a file it would write changed since; the newer file was kept and accepts and undos are refused. Look at the named files, then settle it from Maintain (see [[#Proposal apply recovery]]) |
| nonzero deprecated-table row telemetry | stop and escalate; preserve rows |
| stale/missing derived rebuild marker | shadow compare, then justified live rebuild |
| AI auth/readiness error | [[Configure AI Providers]] |
| failed durable import | resume its batch, not global state repair |
| `sqlite:wal_unavailable` warning | the linked SQLite lacks the WAL-reset fix; install a newer Python patch release (`uv python install`, then `uv sync`), then `--fix-state` |
| `storage:network_filesystem` warning | move the vault to a local disk ([[State and Persistence#Where a vault may live]]) |
| `sqlite:wal_large` warning (`-wal` above 64 MiB) | close other LearnLoop windows, then `--fix-state`, which checkpoints |
| migration fails with `JournalModeSwitchError` | act on the cause the message names: close another process holding a transaction, or restore write access to the database file, its companions or its directory |

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

`--fix-state` acquires the cross-process vault lock, applies pending migrations atomically (on a SQLite with the WAL-reset fix, the first migration after upgrading switches a rollback-journal database to WAL), runs a best-effort `TRUNCATE` checkpoint, attaches the database writable, performs supported state synchronization, merges eligible legacy aliases, and resumes recoverable apply intents idempotently (never over a file changed since the intent; see [[#Proposal apply recovery]]).

> [!warning] Back up a closed vault
> Step 2 copies the vault folder. Do it only after step 1, when no LearnLoop process has the database open; otherwise the copy can miss commits that are still in `state.sqlite-wal`. See [[State and Persistence#Copying and backing up a vault]].

> [!important] Migration atomicity
> A migration receipt and its body commit together. If the process dies mid-migration, neither is retained; the next coordinated open can safely apply that version again.

Normal repository startup uses the same migration coordinator and lock. `--fix-state` is useful when ordinary startup cannot finish or when an operator needs an explicit repair receipt.

## Proposal apply recovery

Accepting proposal items writes YAML through a write-ahead intent (`apply_intents`, `content/proposals/apply_protocol.py`): the intent commits first with each target file's pre-image hash and new content, the files are renamed into place one at a time, then derived state is synced, the database effects and the content recalibration run, and the intent is marked applied last. A crash anywhere before that mark leaves the intent `pending` (refactor K3.5, `docs/reviews/refactor-k3.5.md`).

- **Who recovers.** The sidecar finishes pending intents at every primary bind, right after facet-identity recovery and before ingest binds or state syncs, so the app never serves a half-applied vault; `doctor --fix-state` does the same. The phone host attaches as a secondary and leaves recovery to the primary. With nothing pending, recovery is one query and takes no lock.
- **Never over a newer file.** Recovery writes a target only while the file still holds its pre-image (or no file, for a new one) or already holds the new content. Anything else means the file changed after the intent: nothing of that intent is written, the intent becomes `conflicted` with the files that differ, and the newer files stay.
- **Accepts and undos wait.** While an intent is `pending` or `conflicted`, every accept is refused, and so is every reject or undo (the inbox's reject and delete, the CLI `reject`, a book card's Undo, which is refused before it moves the book's generation or cancels its builds): `OutstandingApplyIntentError`, whose sidecar code is `apply_intent_outstanding`, because the vault may be half-applied and a revert would write over files the intent still owns.
- **Settling a conflict.** Plain doctor and `--fix-state` report `apply_intents:conflicted` as an error and never write over it. The Maintain screen's feed shows the notice `apply_conflicted` with **Keep the files as they are**, which sets the intent aside (`set_aside`): the files stay as they are, its database effects are never performed and its proposal items stay pending for review. A pending intent's notice (`append_partially_complete`, left only when bind recovery failed) offers **Complete pending apply**. Both buttons call the sidecar's `resolve_apply_intent`; its `complete` resolution also re-checks a conflicted intent, finishing it once every named file is back at its pre-image or new content (no button offers that yet).

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
- `schema_migrations` head (currently 165);
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
