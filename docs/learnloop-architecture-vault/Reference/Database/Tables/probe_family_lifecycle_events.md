---
title: "probe_family_lifecycle_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_family_lifecycle_events"
  - "table probe_family_lifecycle_events"
schema_head: 157
table_name: "probe_family_lifecycle_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "030_probe_pilot_and_policy.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/030_probe_pilot_and_policy.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probe_lifecycle.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_family_lifecycle_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves the ordered lifecycle transitions for probe family so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `probe_family_template_id`, `from_status`, `to_status`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §9.7 lifecycle (Checkpoint 4.7): every family-version status transition is persisted with the metric evidence that justified it, so trusted/revise/ retire decisions stay auditable after the fact.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/030_probe_pilot_and_policy.sql`.
- **Schema touched by:** `030_probe_pilot_and_policy.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `probe_family_template_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_version` | `INTEGER` | yes | — | — | Stored value |
| `from_status` | `TEXT` | yes | — | — | Stored value |
| `to_status` | `TEXT` | yes | — | — | Stored value |
| `reason_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_family_lifecycle_family` on `probe_family_template_id`, `probe_family_template_version`, `created_at`.
- `sqlite_autoindex_probe_family_lifecycle_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_probe_family_lifecycle_event()`
- `Repository.probe_family_lifecycle_events()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/probe_lifecycle.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_probe_lifecycle.py`

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
CREATE TABLE probe_family_lifecycle_events (
  id TEXT PRIMARY KEY,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL CHECK (to_status IN ('draft', 'provisional', 'trusted', 'retired')),
  reason_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
