---
title: "probe_generation_needs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_generation_needs"
  - "table probe_generation_needs"
schema_head: 157
table_name: "probe_generation_needs"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
  - "src/learnloop/diagnosis/probe_coverage.py"
  - "src/learnloop/diagnosis/probe_instance_generation.py"
  - "src/learnloop/scheduling/state_signals.py"
  - "src/learnloop/diagnosis/probe_blocks.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_generation_needs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues an identified supply gap for probe generation so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `probe_episode_id`, `learning_object_id`, `target_key`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10: one durable, deduplicated generation need per episode target.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`, `045_synthesis_generation_needs.sql`, `147_diagnostic_surface_generation_needs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `probe_episode_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `target_key` | `TEXT` | yes | — | — | Stored value |
| `missing_capability` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_generation_needs_lo` on `learning_object_id`, `status`.
- `sqlite_autoindex_probe_generation_needs_2` on `probe_episode_id`, `target_key` (unique).
- `sqlite_autoindex_probe_generation_needs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.probe_generation_needs()`
- `Repository.resolve_probe_generation_need()`
- `Repository.upsert_probe_generation_need()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/diagnostic_surface_supply.py`
- `src/learnloop/diagnosis/probe_blocks.py`
- `src/learnloop/diagnosis/probe_coverage.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probe_instance_generation.py`
- `src/learnloop/scheduling/state_signals.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_probe_block_end.py`
- `tests/test_probe_episodes.py`
- `tests/test_probe_pool_empty.py`
- `tests/test_probe_surface_mint.py`
- `tests/test_state_signals.py`

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
CREATE TABLE probe_generation_needs (
  id TEXT PRIMARY KEY,
  probe_episode_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  target_key TEXT NOT NULL,
  missing_capability TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (probe_episode_id, target_key)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
