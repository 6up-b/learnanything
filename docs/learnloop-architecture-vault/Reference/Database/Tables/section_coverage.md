---
title: "section_coverage"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "72208d5a50777166e4f6d036a3f61805212debf1"
source_commit_timestamp: "2026-10-27T13:01:42-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite section_coverage"
  - "table section_coverage"
schema_head: 225
table_name: "section_coverage"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "222_section_coverage.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/222_section_coverage.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/cli/curriculum.py"
  - "src/learnloop/db/stores/section_coverage.py"
  - "src/learnloop/source_retrieval/section_coverage.py"
  - "src/learnloop_sidecar/handlers/correspondents.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `section_coverage`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives section coverage a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `section_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/222_section_coverage.sql`.
- **Schema touched by:** `222_section_coverage.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `treatment` | `TEXT` | no | — | — | Stored value |
| `roles_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `assumes_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `notation_md` | `TEXT` | no | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `candidate_rank` | `INTEGER` | no | — | — | Stored value |
| `learner_override` | `TEXT` | no | — | — | Stored value |
| `learner_text` | `TEXT` | no | — | — | Stored value |
| `section_hash` | `TEXT` | yes | — | — | Stored value |
| `lo_hash` | `TEXT` | yes | — | — | Stored value |
| `state_key` | `TEXT` | yes | — | — | Stored value |
| `ledger_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_section_coverage_lo` on `learning_object_id`, `created_at`.
- `idx_section_coverage_section` on `extraction_id`, `section_id`, `created_at`.
- `idx_section_coverage_judged` on `learning_object_id`, `state_key`, `extraction_id`, `section_id` (unique).
- `sqlite_autoindex_section_coverage_1` on `id` (unique).

Database triggers:

- `section_coverage_no_delete` — schema-enforced lifecycle or immutability constraint.
- `section_coverage_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/section_coverage.py`

### Direct SQL writers

- `src/learnloop/db/stores/section_coverage.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_section_coverage.py`
- `tests/test_section_coverage_migration.py`
- `tests/test_section_coverage_review.py`
- `tests/test_section_coverage_rpcs.py`

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
CREATE TABLE section_coverage (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  treatment TEXT CHECK (treatment IS NULL OR treatment IN ('introduces', 'develops', 'applies', 'mentions', 'not_about')),
  roles_json TEXT NOT NULL DEFAULT '[]',
  assumes_json TEXT NOT NULL DEFAULT '[]',
  notation_md TEXT,
  origin TEXT NOT NULL CHECK (origin IN ('provenance', 'retrieval', 'learner')),
  candidate_rank INTEGER,
  learner_override TEXT CHECK (learner_override IS NULL OR learner_override IN ('is_about', 'not_about', 'none')),
  learner_text TEXT,
  section_hash TEXT NOT NULL,
  lo_hash TEXT NOT NULL,
  state_key TEXT NOT NULL,
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (learner_override IS NOT NULL OR treatment IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
