---
title: "activity_card_authoring"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_card_authoring"
  - "table activity_card_authoring"
schema_head: 156
table_name: "activity_card_authoring"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "074_activity_contract_extensions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/074_activity_contract_extensions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/surface_mint.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_card_authoring`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity card authoring a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `card_version_id`, `family_version_id`, `pattern_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Card-version authoring pins, keyed by the P0 immutable card version id.

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/074_activity_contract_extensions.sql`.
- **Schema touched by:** `074_activity_contract_extensions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `card_version_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/activity_card_versions\|activity_card_versions.id]] | Stored value |
| `family_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_family_versions\|activity_family_versions.id]] | Stored value |
| `pattern_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_pattern_versions\|activity_pattern_versions.id]] | Stored value |
| `task_feature_schema_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/task_feature_schema_versions\|task_feature_schema_versions.id]] | Stored value |
| `task_features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `capability` | `TEXT` | no | — | — | Stored value |
| `outcome_schema_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `outcome_schema_version` | `INTEGER` | no | — | — | Stored value |
| `surface_policy` | `TEXT` | no | — | — | Stored value |
| `surface_variation_bounds_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `angle_identity_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `generator_version` | `TEXT` | no | — | — | Stored value |
| `gate_policy_version` | `TEXT` | no | — | — | Stored value |
| `expected_burden_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `calibration_metadata_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `task_feature_schema_version_id` → [[Reference/Database/Tables/task_feature_schema_versions|`task_feature_schema_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `pattern_version_id` → [[Reference/Database/Tables/activity_pattern_versions|`activity_pattern_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `family_version_id` → [[Reference/Database/Tables/activity_family_versions|`activity_family_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `card_version_id` → [[Reference/Database/Tables/activity_card_versions|`activity_card_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_aca_family` on `family_version_id`.
- `sqlite_autoindex_activity_card_authoring_1` on `card_version_id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_card_authoring()`
- `Repository.activity_card_authoring_for_family()`
- `Repository.upsert_activity_card_authoring()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/surface_mint.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_contract_extensions.py`

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
CREATE TABLE activity_card_authoring (
  card_version_id TEXT PRIMARY KEY
    REFERENCES activity_card_versions(id) ON DELETE CASCADE,
  family_version_id TEXT REFERENCES activity_family_versions(id),
  pattern_version_id TEXT REFERENCES activity_pattern_versions(id),
  task_feature_schema_version_id TEXT REFERENCES task_feature_schema_versions(id),
  task_features_json TEXT,
  capability TEXT CHECK (capability IS NULL OR capability IN (
    'retrieval', 'schema_interpretation', 'procedure_execution',
    'method_selection', 'coordination')),
  outcome_schema_id TEXT,                  -- 066-owned, bare
  outcome_schema_version INTEGER,
  surface_policy TEXT CHECK (surface_policy IS NULL OR surface_policy IN ('fixed', 'rotating')),
  surface_variation_bounds_json TEXT,
  angle_identity_json TEXT,
  generator_version TEXT,
  gate_policy_version TEXT,
  expected_burden_json TEXT,
  calibration_metadata_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
