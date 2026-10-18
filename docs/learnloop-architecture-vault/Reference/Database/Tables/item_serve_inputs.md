---
title: "item_serve_inputs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "e1bd8231b9fc476af862ae4c67d30b54cf98429d"
source_commit_timestamp: "2026-10-18T19:32:15-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite item_serve_inputs"
  - "table item_serve_inputs"
schema_head: 213
table_name: "item_serve_inputs"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "213_adaptive_difficulty_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/213_adaptive_difficulty_receipts.sql"
  - "src/learnloop/adaptive_difficulty/data_check.py"
  - "src/learnloop/adaptive_difficulty/serve.py"
  - "src/learnloop/adaptive_difficulty/serve_inputs.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/ad_receipts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_serve_inputs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item serve input a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `plan_presentation_id`, `probe_presentation_id`, `scheduler_candidate_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §7.5: the features and signals an AD decision or update reads, frozen when the item is served. One row per presentation of a never-attempted item, written in the serve transaction beside the in-process forecast receipts. A later audit, re-audit, recalibration or item edit never rewrites a row.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/213_adaptive_difficulty_receipts.sql`.
- **Schema touched by:** `213_adaptive_difficulty_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `presentation_kind` | `TEXT` | yes | — | — | Stored value |
| `plan_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `served_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `stamped_features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `task_feature_schema` | `TEXT` | no | — | — | Stored value |
| `audit_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `resolved_features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `signals_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `z_v1_recalibration` | `TEXT` | no | — | — | Stored value |
| `pre_exposed` | `INTEGER` | yes | — | — | Stored value |
| `resolution_version` | `TEXT` | yes | — | — | Stored value |
| `loadings_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `coupling_version` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_serve_inputs_plan` on `plan_presentation_id`.
- `idx_item_serve_inputs_item` on `practice_item_id`, `served_at`.
- `sqlite_autoindex_item_serve_inputs_2` on `receipt_key` (unique).
- `sqlite_autoindex_item_serve_inputs_1` on `id` (unique).

Database triggers:

- `item_serve_inputs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `item_serve_inputs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/data_check.py`
- `src/learnloop/adaptive_difficulty/serve.py`
- `src/learnloop/adaptive_difficulty/serve_inputs.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_fakes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_migration.py`
- `tests/test_ad1_outside_and_cli.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_architecture.py`

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
CREATE TABLE item_serve_inputs (
  id TEXT PRIMARY KEY,
  -- Idempotency: <presentation kind>:<presentation id>.
  receipt_key TEXT NOT NULL UNIQUE,
  presentation_kind TEXT NOT NULL
    CHECK (presentation_kind IN ('plan_presentation', 'probe_presentation', 'scheduler_candidate')),
  plan_presentation_id TEXT,
  probe_presentation_id TEXT,
  scheduler_candidate_id TEXT,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  -- The served revision (also written to practice_item_snapshots, INSERT OR
  -- IGNORE, migration 164).
  content_hash TEXT NOT NULL,
  served_at TEXT NOT NULL,
  -- x_i as stamped on the served revision (p1_launch@1), null when it has none.
  stamped_features_json TEXT,
  task_feature_schema TEXT,
  -- Per audited dimension: {judgment_id, value} of the audit that had answered
  -- before the serve, or null.
  audit_json TEXT NOT NULL,
  -- The tuple AD reads: the audit where it answered, else the stamped value.
  resolved_features_json TEXT,
  -- z_i: per signal {value, available, receipt_id, received_at, why}.
  signals_json TEXT NOT NULL,
  z_v1_recalibration TEXT,
  -- §5.3: the item's reveal sum before the serve already reached the
  -- auto-prime threshold (excluded from the update and from scoring alike).
  pre_exposed INTEGER NOT NULL CHECK (pre_exposed IN (0, 1)),
  resolution_version TEXT NOT NULL,
  -- From the AD2/AD3 successor on: the loadings in force and the coupling
  -- version (§5.10). Null in AD1.
  loadings_json TEXT,
  coupling_version TEXT,
  created_at TEXT NOT NULL,
  CHECK (
    (presentation_kind = 'plan_presentation' AND plan_presentation_id IS NOT NULL)
    OR (presentation_kind = 'probe_presentation' AND probe_presentation_id IS NOT NULL)
    OR (presentation_kind = 'scheduler_candidate' AND scheduler_candidate_id IS NOT NULL)
  )
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
