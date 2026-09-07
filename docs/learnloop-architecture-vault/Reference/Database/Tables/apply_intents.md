---
title: "apply_intents"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite apply_intents"
  - "table apply_intents"
schema_head: 157
table_name: "apply_intents"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/content/proposals/patches.py"
  - "src/learnloop/ops/maintenance_feed.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `apply_intents`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Provides write-ahead recovery state for multi-file proposal application. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `proposed_patch_id`, `status`, `rolled_back_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10.2 Write-ahead apply intents: the durable record that closes crashes (the vault mutation lock closes races). An accepted dependency closure plus its target file contents/hashes and DB side-effect plan commit to SQLite FIRST; YAML is then staged/fsynced/atomically renamed; the intent is marked applied. Startup/doctor recovery completes or rolls back any intent left mid-flight, and application is idempotent.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/044_provenance_manifests_apply_intents.sql`.
- **Schema touched by:** `044_provenance_manifests_apply_intents.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `proposed_patch_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `item_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `targets_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `db_plan_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'pending'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `applied_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `rolled_back_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_apply_intents_status` on `status`.
- `sqlite_autoindex_apply_intents_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.apply_intent()`
- `Repository.insert_apply_intent()`
- `Repository.mark_apply_intent_applied()`
- `Repository.mark_apply_intent_rolled_back()`
- `Repository.pending_apply_intents()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/ops/maintenance_feed.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_apply_write_ahead.py`
- `tests/test_doctor.py`
- `tests/test_migrations.py`
- `tests/test_source_append.py`

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
CREATE TABLE apply_intents (
  id TEXT PRIMARY KEY,
  proposed_patch_id TEXT NOT NULL,
  item_ids_json TEXT NOT NULL,       -- accepted closure item ids, in apply order
  targets_json TEXT NOT NULL,        -- [{rel_path, pre_hash, post_content, post_hash}]
  db_plan_json TEXT NOT NULL,        -- per-item change batch / content event / links
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'applied', 'rolled_back')
  ),
  created_at TEXT NOT NULL,
  applied_at TEXT,
  rolled_back_at TEXT
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
