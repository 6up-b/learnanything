---
title: "family_proposals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "87c9b9a4a94630287dd2e9fa6ecb7cd6544f9f1a"
source_commit_timestamp: "2026-10-21T10:09:53-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite family_proposals"
  - "table family_proposals"
schema_head: 217
table_name: "family_proposals"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "168_activity_family_membership.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/168_activity_family_membership.sql"
  - "src/learnloop/cli/families.py"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/db/stores/families.py"
  - "src/learnloop/ops/family_proposals.py"
  - "src/learnloop/substrate/families.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `family_proposals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives family proposal a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `family_id`, `state`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Authored family identity remains activity_families; regrouping never edits cards.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/168_activity_family_membership.sql`.
- **Schema touched by:** `168_activity_family_membership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `family_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `state` | `TEXT` | yes | — | — | Stored value |
| `plan_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_family_proposals_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/substrate/families.py`

### Direct SQL writers

- `src/learnloop/db/stores/families.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/source_service_fakes.py`
- `tests/test_activity_families.py`
- `tests/test_family_proposals.py`
- `tests/test_integration_daily_loop_field.py`
- `tests/test_output_budget.py`

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
CREATE TABLE family_proposals (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('applying','applied','undoing','undone','rejected')),
  plan_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
