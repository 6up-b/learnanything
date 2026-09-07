---
title: "golden_path_artifacts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite golden_path_artifacts"
  - "table golden_path_artifacts"
schema_head: 157
table_name: "golden_path_artifacts"
table_role: "receipt"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "087_golden_path_artifacts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/087_golden_path_artifacts.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/curriculum/golden_path_restoration.py"
  - "src/learnloop/curriculum/golden_path_run.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
  - "src/learnloop/scheduling/controller_cutover.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `golden_path_artifacts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Identifies durable output artifacts produced for golden path so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `run_id`, `administration_id`, `seq`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/087_golden_path_artifacts.sql`.
- **Schema touched by:** `087_golden_path_artifacts.sql`, `101_dual_authority_and_kinship_dedup.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/golden_path_runs\|golden_path_runs.id]] | Stored value |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `administration_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `payload_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `idempotency_key` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `run_id` → [[Reference/Database/Tables/golden_path_runs|`golden_path_runs.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gpa_run_kind` on `run_id`, `kind`.
- `idx_gpa_run` on `run_id`, `seq`.
- `sqlite_autoindex_golden_path_artifacts_3` on `run_id`, `idempotency_key` (unique).
- `sqlite_autoindex_golden_path_artifacts_2` on `run_id`, `seq` (unique).
- `sqlite_autoindex_golden_path_artifacts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_golden_path_artifact()`
- `Repository.golden_path_artifacts_for()`
- `Repository.latest_golden_path_artifact()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/curriculum/golden_path_restoration.py`
- `src/learnloop/curriculum/golden_path_run.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`
- `src/learnloop/scheduling/controller_cutover.py`
- `src/learnloop_sidecar/handlers/golden_path_assessment.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_controller_cutover.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_p2_acceptance.py`

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
CREATE TABLE "golden_path_artifacts" (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN (
    'assessment_result',
    'restoration',
    'boundary_diff',
    'baseline_boundary',
    'diagnostic_segment_closed',
    'milestone',
    'depth_invitation',
    'depth_accept',
    'depth_decline',
    'staged_veto_deferred')),  -- P4 §14.2/audit M4: live-bridge staged-veto deferral marker
  administration_id TEXT,
  payload_json TEXT NOT NULL,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
