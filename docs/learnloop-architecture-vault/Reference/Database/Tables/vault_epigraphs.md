---
title: "vault_epigraphs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c454e125fe262787a0ed6f452214e48b2525cf0b"
source_commit_timestamp: "2026-09-03T19:48:19-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite vault_epigraphs"
  - "table vault_epigraphs"
schema_head: 158
table_name: "vault_epigraphs"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "158_vault_epigraphs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/158_vault_epigraphs.sql"
  - "src/learnloop/ai/routing.py"
  - "src/learnloop/content/synthesis/source_append.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/content/synthesis/vault_epigraphs.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/epigraphs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `vault_epigraphs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives vault epigraph a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `subject_id`, `source_set_id`, `synthesis_run_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/158_vault_epigraphs.sql`.
- **Schema touched by:** `158_vault_epigraphs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `subject_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `synthesis_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `mode` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `text` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `ordinal` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_vault_epigraphs_run` on `synthesis_run_id`.
- `idx_vault_epigraphs_subject_recent` on `subject_id`, `created_at`, `ordinal`.
- `sqlite_autoindex_vault_epigraphs_1` on `id` (unique).

Database triggers:

- `vault_epigraphs_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.insert_vault_epigraphs()`
- `Repository.recent_vault_epigraphs()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/synthesis/vault_epigraphs.py`
- `src/learnloop_sidecar/handlers/epigraphs.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/structured_ai.py`
- `tests/test_provider_resolution_parity.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_vault_epigraphs.py`
- `tests/test_sidecar_epigraphs.py`
- `tests/test_source_append.py`
- `tests/test_source_set_synthesis.py`

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
CREATE TABLE vault_epigraphs (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  source_set_id TEXT,
  synthesis_run_id TEXT,
  mode TEXT NOT NULL CHECK (mode IN ('bootstrap', 'append')),
  kind TEXT NOT NULL CHECK (kind IN ('quote', 'haiku')),
  text TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  ordinal INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
