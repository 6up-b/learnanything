---
title: "familiarity_kernel_features"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite familiarity_kernel_features"
  - "table familiarity_kernel_features"
schema_head: 157
table_name: "familiarity_kernel_features"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "100_kinship_kernel_and_shadow_components.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/100_kinship_kernel_and_shadow_components.sql"
  - "src/learnloop/scheduling/kinship_feature.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `familiarity_kernel_features`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives familiarity kernel feature a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `model_id`, `subject_surface_id`, `kin_surface_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Cached per-surface(-pair) versioned kinship FEATURE scores + calibrated intervals (§8.2 "scores cached as versioned features"). Conditioned ONLY on pre-administration information (exposure history, time, kinship features, angle/task features, surface provenance); the learner's current correctness is NEVER a column here (§8.2, 16.4).

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/100_kinship_kernel_and_shadow_components.sql`.
- **Schema touched by:** `100_kinship_kernel_and_shadow_components.sql`, `101_dual_authority_and_kinship_dedup.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `model_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/familiarity_kernel_models\|familiarity_kernel_models.id]] | Stored value |
| `subject_surface_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `kin_surface_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `outputs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `conditioned_on_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `in_scope` | `INTEGER` | yes | `1` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `model_id` → [[Reference/Database/Tables/familiarity_kernel_models|`familiarity_kernel_models.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_familiarity_kernel_features_self` on `model_id`, `subject_surface_id` (unique).
- `idx_familiarity_kernel_features_subject` on `subject_surface_id`.
- `sqlite_autoindex_familiarity_kernel_features_2` on `model_id`, `subject_surface_id`, `kin_surface_id` (unique).
- `sqlite_autoindex_familiarity_kernel_features_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/kinship_feature.py`

### Direct SQL writers

- `src/learnloop/scheduling/kinship_feature.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_kinship_feature.py`

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
CREATE TABLE familiarity_kernel_features (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES familiarity_kernel_models(id) ON DELETE CASCADE,
  subject_surface_id TEXT NOT NULL,
  kin_surface_id TEXT,
  -- Outputs (§8.2): P(replay materially aided response), independent-evidence discount
  -- interval [lo, hi], rotation-benefit estimate. Stored as one JSON body.
  outputs_json TEXT NOT NULL,
  -- The pre-administration inputs the score was conditioned on (audit / leakage proof).
  conditioned_on_json TEXT NOT NULL,
  in_scope INTEGER NOT NULL DEFAULT 1 CHECK (in_scope IN (0, 1)),
  created_at TEXT NOT NULL,
  UNIQUE(model_id, subject_surface_id, kin_surface_id)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
