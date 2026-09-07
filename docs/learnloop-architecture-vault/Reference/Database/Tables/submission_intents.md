---
title: "submission_intents"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
last_verified: "2026-09-07"
aliases:
  - "state.sqlite submission_intents"
  - "table submission_intents"
schema_head: 163
table_name: "submission_intents"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "161_collection_contract.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/161_collection_contract.sql"
  - "src/learnloop/db/stores/collection.py"
  - "src/learnloop/substrate/data_quality.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `submission_intents`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Binds a durable retry identity to the exact session, practice item and offered scheduler candidate before the attempt is committed. It supplies replay-stable input rather than a disposable cache. Rows bind `submission_id`, `session_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/161_collection_contract.sql`.
- **Schema touched by:** `161_collection_contract.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `submission_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/sessions\|sessions.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/scheduler_slate_candidates\|scheduler_slate_candidates.id]] | Stored value |
| `entry_surface` | `TEXT` | yes | — | — | Stored value |
| `viewing_status` | `TEXT` | yes | `'unknown'` | — | Stored value |
| `collection_version` | `TEXT` | yes | `'learnloop-events-v1'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `scheduler_candidate_id` → [[Reference/Database/Tables/scheduler_slate_candidates|`scheduler_slate_candidates.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `session_id` → [[Reference/Database/Tables/sessions|`sessions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_submission_intents_1` on `submission_id` (unique).

Database triggers:

- `submission_intents_immutable_delete` — schema-enforced lifecycle or immutability constraint.
- `submission_intents_immutable_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/collection.py`

### Direct SQL writers

- `src/learnloop/db/stores/collection.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

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
CREATE TABLE submission_intents (
  submission_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  practice_item_id TEXT NOT NULL,
  scheduler_candidate_id TEXT REFERENCES scheduler_slate_candidates(id),
  entry_surface TEXT NOT NULL,
  viewing_status TEXT NOT NULL DEFAULT 'unknown',
  collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
