---
title: "controller_shadow_predictions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_shadow_predictions"
  - "table controller_shadow_predictions"
schema_head: 156
table_name: "controller_shadow_predictions"
table_role: "receipt"
functionality_status: "dormant-shadow"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/scheduling/controller_store.py"
  - "src/learnloop/scheduling/open_world_gate.py"
  - "src/learnloop/scheduling/prequential.py"
  - "src/learnloop/scheduling/shadow_components.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/dormant-shadow"
  - "learnloop/domain/scheduling"
---

# `controller_shadow_predictions`

> [!warning] Dormant Shadow
> Executable telemetry only; schema-enforced authority is always none.

## Why it exists

Stores non-authoritative controller predictions; a schema CHECK fixes authority to 'none'. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `scorer_kind`, `model_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Scorer/kernel output with NO authority (invariant 3, §7). Joins to the exact predecision snapshot hash; a record that cannot join is marked unusable, never allowed to influence a live decision.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `dormant-shadow`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`, `100_kinship_kernel_and_shadow_components.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/controller_decisions\|controller_decisions.id]] | Stored value |
| `snapshot_hash` | `TEXT` | yes | — | — | Stored value |
| `scorer_kind` | `TEXT` | yes | — | — | Stored value |
| `model_version` | `TEXT` | no | — | — | Stored value |
| `authority` | `TEXT` | yes | `'none'` | — | Stored value |
| `prediction_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `usable` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `decision_id` → [[Reference/Database/Tables/controller_decisions|`controller_decisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_controller_shadow_predictions_snapshot` on `snapshot_hash`.
- `idx_controller_shadow_predictions_decision` on `decision_id`.
- `sqlite_autoindex_controller_shadow_predictions_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`
- `src/learnloop/scheduling/prequential.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_shadow_components.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE controller_shadow_predictions (
  id TEXT PRIMARY KEY,
  decision_id TEXT REFERENCES controller_decisions(id),
  snapshot_hash TEXT NOT NULL,
  scorer_kind TEXT NOT NULL,
  model_version TEXT,
  authority TEXT NOT NULL DEFAULT 'none' CHECK (authority IN ('none')),
  prediction_json TEXT NOT NULL,
  usable INTEGER NOT NULL DEFAULT 1 CHECK (usable IN (0, 1)),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
