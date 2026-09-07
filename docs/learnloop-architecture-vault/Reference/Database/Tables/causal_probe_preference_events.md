---
title: "causal_probe_preference_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_probe_preference_events"
  - "table causal_probe_preference_events"
schema_head: 157
table_name: "causal_probe_preference_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "124_causal_probe_decisions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/124_causal_probe_decisions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_probe_preference_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of causal probe preference so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `session_id`, `scope`, `scope_ref`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/124_causal_probe_decisions.sql`.
- **Schema touched by:** `124_causal_probe_decisions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `scope_ref` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `preference` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_probe_preference_session` on `session_id`, `created_at`, `id`.
- `idx_causal_probe_preference_scope` on `scope`, `scope_ref`, `created_at`, `id`.
- `sqlite_autoindex_causal_probe_preference_events_1` on `id` (unique).

Database triggers:

- `causal_probe_preference_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_probe_preference_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_probe_preference()`
- `Repository.record_causal_probe_preference()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_orchestrator.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE causal_probe_preference_events (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK (
    scope IN ('factor', 'learning_object', 'session')
  ),
  scope_ref TEXT NOT NULL,
  session_id TEXT,
  preference TEXT NOT NULL CHECK (
    preference IN ('allow', 'decline', 'teach_now', 'no_more_diagnostics')
  ),
  source TEXT NOT NULL,
  expires_at TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
