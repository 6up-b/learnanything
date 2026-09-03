---
title: "task_blueprint_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite task_blueprint_versions"
  - "table task_blueprint_versions"
schema_head: 157
table_name: "task_blueprint_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "081_task_blueprints.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/081_task_blueprints.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/curriculum/golden_path_restoration.py"
  - "src/learnloop/curriculum/task_blueprints.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `task_blueprint_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of task blueprint so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `blueprint_id`, `authoring_version`, `model_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Immutable, content-addressed version. `spec_json` carries the full §3.2 shape (facets + closed P1 capability vocab, solution recipes all_of/any_of + optional integration component, TaskFeature ranges + administration conditions, invariants + permitted variation axes, response/outcome/rubric/fatal-errors, failure-signature->triage map, source neighborhoods, target-distribution support + weights, ordered reviewed depth-milestone DAG, leakage boundaries). A version advances draft -> reviewed -> active; a material edit mints a SUCCESSOR version (append-only), it never mutates a reviewed row.

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/081_task_blueprints.sql`.
- **Schema touched by:** `081_task_blueprints.sql`, `082_golden_path_runs.sql`, `083_diagnostic_pack_and_triage.sql`, `085_surface_pool.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `blueprint_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/task_blueprints\|task_blueprints.id]] | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'draft'` | — | Stored value |
| `spec_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `canonical_hash` | `TEXT` | yes | — | — | Stored value |
| `authoring_version` | `TEXT` | yes | `'stub-1'` | — | Stored value |
| `model_version` | `TEXT` | no | — | — | Stored value |
| `provenance_version` | `TEXT` | yes | `'owner-review-1'` | — | Stored value |
| `reviewed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `activated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `blueprint_id` → [[Reference/Database/Tables/task_blueprints|`task_blueprints.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_tbv_status` on `status`.
- `idx_tbv_blueprint` on `blueprint_id`, `version`.
- `sqlite_autoindex_task_blueprint_versions_3` on `blueprint_id`, `content_hash` (unique).
- `sqlite_autoindex_task_blueprint_versions_2` on `blueprint_id`, `version` (unique).
- `sqlite_autoindex_task_blueprint_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.confirm_golden_path_atomic()`
- `Repository.register_task_blueprint_version()`
- `Repository.reviewed_reading_question_placements()`
- `Repository.task_blueprint_version()`
- `Repository.task_blueprint_versions_for()`
- `Repository.transition_task_blueprint_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/curriculum/golden_path_restoration.py`
- `src/learnloop/curriculum/task_blueprints.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop_sidecar/handlers/golden_path.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_golden_path_confirm.py`
- `tests/test_golden_path_fixture.py`
- `tests/test_task_blueprints.py`

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
CREATE TABLE task_blueprint_versions (
  id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL REFERENCES task_blueprints(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'reviewed', 'active', 'retired')),
  spec_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  authoring_version TEXT NOT NULL DEFAULT 'stub-1',
  model_version TEXT,
  provenance_version TEXT NOT NULL DEFAULT 'owner-review-1',
  reviewed_at TEXT,
  activated_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(blueprint_id, version),
  UNIQUE(blueprint_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
