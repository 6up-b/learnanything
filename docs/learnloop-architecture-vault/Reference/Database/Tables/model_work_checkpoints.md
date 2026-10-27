---
title: "model_work_checkpoints"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "436b3cec90ff96f82f1c03d5a3d1a02eded67014"
source_commit_timestamp: "2026-10-27T13:58:58-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite model_work_checkpoints"
  - "table model_work_checkpoints"
schema_head: 225
table_name: "model_work_checkpoints"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "160_model_call_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/160_model_call_receipts.sql"
  - "src/learnloop/adaptive_difficulty/claims.py"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/ai/spend.py"
  - "src/learnloop/content/facet_identity/judge.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/daily_plan/router_teach_back.py"
  - "src/learnloop/db/stores/model_calls.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `model_work_checkpoints`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves validated inventory windows and synthesis passes under content hashes so interrupted jobs reuse completed model work. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `cache_key`, `purpose`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/160_model_call_receipts.sql`.
- **Schema touched by:** `160_model_call_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `cache_key` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `result_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `usage_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_model_work_checkpoints_1` on `cache_key` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/router_teach_back.py`
- `src/learnloop/db/stores/model_calls.py`
- `src/learnloop/db/stores/practice_index.py`

### Direct SQL writers

- `src/learnloop/db/stores/model_calls.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad1_fix_round4.py`
- `tests/test_ad1_fix_round5.py`
- `tests/test_approach_maps.py`
- `tests/test_glm_ocr.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_hint_outcome.py`
- `tests/test_ingestion_checkpoints.py`
- `tests/test_model_work_checkpoints.py`
- `tests/test_practice_index_dossiers.py`
- `tests/test_practice_index_find.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_recurrence_benchmarks.py`
- `tests/test_source_ingestion_v2lite.py`
- `tests/test_t6_followup_review.py`
- `tests/test_workbench_text_gaps.py`

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
CREATE TABLE model_work_checkpoints (
  cache_key TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  result_json TEXT NOT NULL,
  usage_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
