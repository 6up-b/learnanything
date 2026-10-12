---
title: "practice_item_snapshots"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "125a83ccdd63d8ad8e233fbdbf49d8d5f6d8b659"
source_commit_timestamp: "2026-10-12T16:52:41-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite practice_item_snapshots"
  - "table practice_item_snapshots"
schema_head: 172
table_name: "practice_item_snapshots"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "164_item_snapshots_and_adjudication_fk.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/164_item_snapshots_and_adjudication_fk.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/field/item_content.py"
  - "src/learnloop/field/outcomes.py"
  - "src/learnloop/scheduling/scheduler.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `practice_item_snapshots`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Keeps one content-addressed copy of every practice-item revision the scheduler scored, keyed by the SHA-256 of its canonical JSON, so selection decision features can be joined to the exact item text after the vault item changes. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `practice_item_id`, `content_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Content-addressed copy of every practice-item revision the scheduler scored. Selection decision features reference the item by content_hash (SHA-256 of item_json exactly), and the vault keeps only the current revision, so this is the only record of the text behind an older decision. Written with INSERT OR IGNORE: one row per distinct revision, never per candidate.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/164_item_snapshots_and_adjudication_fk.sql`.
- **Schema touched by:** `164_item_snapshots_and_adjudication_fk.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `content_hash` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `item_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `practice_item_snapshots_item` on `practice_item_id`.
- `sqlite_autoindex_practice_item_snapshots_1` on `content_hash` (unique).

Database triggers:

- `practice_item_snapshots_immutable_delete` — schema-enforced lifecycle or immutability constraint.
- `practice_item_snapshots_immutable_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.record_scheduler_slate()`

### Direct SQL readers

- `src/learnloop/field/item_content.py`
- `src/learnloop/field/outcomes.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/scheduler.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_collection_dataset.py`
- `tests/test_facet_outcome_view.py`
- `tests/test_migrations.py`
- `tests/test_success_head_cli.py`
- `tests/test_probe_episodes.py`

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
CREATE TABLE practice_item_snapshots (
  content_hash TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  item_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
