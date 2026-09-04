---
title: "measurement_contract_corrections"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite measurement_contract_corrections"
  - "table measurement_contract_corrections"
schema_head: 157
table_name: "measurement_contract_corrections"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "116_measurement_contract_corrections.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/116_measurement_contract_corrections.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/attempts/measurement_corrections.py"
  - "src/learnloop/substrate/state_sync.py"
  - "src/learnloop_sidecar/context.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `measurement_contract_corrections`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Appends governed corrections to measurement contract without rewriting history so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `correction_set_id`, `source_practice_item_id`, `source_contract_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P0b authoring honesty (§5.7): an attempted PracticeItem is superseded by a newly-authored item and immutable contract snapshot. Historical observations may be reinterpreted only by an explicitly named projection version.

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/116_measurement_contract_corrections.sql`.
- **Schema touched by:** `116_measurement_contract_corrections.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `correction_set_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_contract_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/assessment_contract_versions\|assessment_contract_versions.id]] | Stored value |
| `corrected_practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `corrected_contract_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/assessment_contract_versions\|assessment_contract_versions.id]] | Stored value |
| `consuming_projection_version` | `TEXT` | yes | — | — | Stored value |
| `historical_evidence_policy` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `correction_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `corrected_contract_version_id` → [[Reference/Database/Tables/assessment_contract_versions|`assessment_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_contract_version_id` → [[Reference/Database/Tables/assessment_contract_versions|`assessment_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_measurement_contract_corrections_projection` on `source_contract_version_id`, `consuming_projection_version`.
- `idx_measurement_contract_corrections_source_item` on `source_practice_item_id`, `created_at`, `id`.
- `sqlite_autoindex_measurement_contract_corrections_2` on `source_contract_version_id`, `consuming_projection_version` (unique).
- `sqlite_autoindex_measurement_contract_corrections_1` on `id` (unique).

Database triggers:

- `measurement_contract_corrections_no_delete` — schema-enforced lifecycle or immutability constraint.
- `measurement_contract_corrections_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.append_measurement_contract_corrections()`
- `Repository.effective_assessment_contract_version()`
- `Repository.measurement_contract_corrections()`
- `Repository.superseded_measurement_item_ids()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/observation_ledger.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/measurement_corrections.py`
- `src/learnloop/substrate/state_sync.py`
- `src/learnloop_sidecar/context.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_measurement_corrections.py`
- `tests/test_migrations.py`

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
CREATE TABLE measurement_contract_corrections (
  id TEXT PRIMARY KEY,
  correction_set_id TEXT NOT NULL,
  source_practice_item_id TEXT NOT NULL,
  source_contract_version_id TEXT NOT NULL
    REFERENCES assessment_contract_versions(id),
  corrected_practice_item_id TEXT NOT NULL,
  corrected_contract_version_id TEXT NOT NULL
    REFERENCES assessment_contract_versions(id),
  consuming_projection_version TEXT NOT NULL,
  historical_evidence_policy TEXT NOT NULL
    CHECK (historical_evidence_policy IN ('preserve_original', 'reinterpret_measurement')),
  reason TEXT NOT NULL,
  correction_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(source_contract_version_id, consuming_projection_version)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
