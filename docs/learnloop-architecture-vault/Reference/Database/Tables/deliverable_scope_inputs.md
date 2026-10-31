---
title: "deliverable_scope_inputs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "f2a2fa37e3e3a974b999480df9a9b931675db2e0"
source_commit_timestamp: "2026-10-31T16:30:38-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite deliverable_scope_inputs"
  - "table deliverable_scope_inputs"
schema_head: 228
table_name: "deliverable_scope_inputs"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "228_deliverable_curriculum.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/228_deliverable_curriculum.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/deliverables.py"
  - "src/learnloop/source_retrieval/deliverables.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `deliverable_scope_inputs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives deliverable scope input a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `goal_id`, `extraction_id`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/228_deliverable_curriculum.sql`.
- **Schema touched by:** `228_deliverable_curriculum.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `text_md` | `TEXT` | no | — | — | Stored value |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `context_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_deliverable_scope_inputs_goal` on `goal_id`, `created_at`.
- `sqlite_autoindex_deliverable_scope_inputs_1` on `id` (unique).

Database triggers:

- `deliverable_scope_inputs_no_delete` — schema-enforced lifecycle or immutability constraint.
- `deliverable_scope_inputs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/deliverables.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_deliverable_codex_review.py`
- `tests/test_deliverable_curriculum_migration.py`
- `tests/test_deliverable_scope.py`

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
CREATE TABLE deliverable_scope_inputs (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('text', 'topic_list', 'passage', 'correction', 'depth')),
  text_md TEXT,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  context_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK (kind <> 'passage' OR extraction_id IS NOT NULL),
  CHECK (kind = 'passage' OR text_md IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
