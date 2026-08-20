---
title: Recovery and Rebuild Drill
aliases:
  - Non-Destructive Recovery Example
  - Shadow Rebuild Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/bootstrap.py
  - src/learnloop/ops/doctor.py
  - src/learnloop/substrate/shadow_rebuild.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - tests/test_doctor.py
  - tests/test_shadow_rebuild.py
tags:
  - learnloop/example
  - learnloop/recovery
  - learnloop/rebuild
  - learnloop/operations
---

# Recovery and Rebuild Drill

This drill initializes a disposable mvp-0.9 vault, records pre/post hashes, and runs an isolated candidate replay. It demonstrates the recovery evidence you should demand before considering a live rebuild.

## Prerequisites

- repository root as current directory
- no need to close the normal desktop, because the drill uses a disposable copy

## 1. Create the disposable incident vault

```bash
DRILL_ROOT="$(mktemp -d)"
VAULT="$DRILL_ROOT/vault"

uv run learnloop init "$VAULT" \
  --subject "Rebuild Drill" \
  --starting-level new_to_this
```

Record the live-copy database hash:

```bash
sha256sum "$VAULT/state.sqlite"
```

## 2. Capture read-only health

```bash
uv run learnloop doctor --json --vault "$VAULT"
sqlite3 -readonly "$VAULT/state.sqlite" \
  'SELECT MAX(version) AS migration_head FROM schema_migrations;'
```

Save the complete doctor JSON. Do not use `--fix-state` when the read-only result is already clean.

## 3. Run an unchanged-baseline shadow rebuild

```bash
uv run learnloop rebuild --shadow --json --vault "$VAULT"
sha256sum "$VAULT/state.sqlite"
```

Require:

```json
{
  "shadow_rebuild": {
    "mode": "shadow",
    "live_database": {"unchanged": true},
    "rebuild": {"unaccounted_attempt_ids": []}
  }
}
```

The two shell hashes must also match.

## 4. Compare a candidate override

```bash
uv run learnloop rebuild --shadow \
  --set mastery.irt.eb_difficulty_enabled=true \
  --json --vault "$VAULT"
```

The verified empty-vault check reported the override under `applied_overrides`, zero learner-state diff counts, no unaccounted attempts, and identical live hashes. When applying the same procedure to a backed-up vault with history, inspect each mastery/facet/schedule change rather than expecting zero.

> [!important] Pass condition
> The drill succeeds when the candidate diff is explainable, every raw attempt is accounted for, and the live database is unchanged—not when the candidate happens to improve a metric.

## 5. Practice the repair decision

- clean doctor + explainable shadow diff → no repair required;
- pending migrations/apply intent → backed-up `doctor --fix-state` path;
- stale derived marker with accounted replay → consider backed-up live rebuild;
- deprecated tables with rows or unaccounted attempts → stop and escalate.

Use [[Doctor Migrations and Recovery#Repair path]] for the mutating branch and [[Rebuild and Shadow Compare#Run a live rebuild only when justified]] for the replay branch.

## 6. Retain or dispose

Keep the copied vault and JSON as incident evidence if this rehearses a real change. Otherwise remove the `$DRILL_ROOT` directory only after confirming it is the temporary path printed by `mktemp`.

^recovery-drill-pass-condition
