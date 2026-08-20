---
title: "synthesis_shard_results"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite synthesis_shard_results"
  - "table synthesis_shard_results"
schema_head: 156
table_name: "synthesis_shard_results"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "064_synthesis_shard_results.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/064_synthesis_shard_results.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `synthesis_shard_results`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives synthesis shard result a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `manifest_hash`, `shard_key`, `shard_ordinal`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Durable per-shard synthesis checkpoints. A completed shard's model output is persisted keyed by its full input identity (prompt version, provider/model, brief, registry, exam profile, shard inventories, shard position), so a retried synthesis reuses finished shards at zero model cost instead of re-paying every call. Keyed by content, not manifest hash: retries with revised token ceilings mint a new manifest but keep identical shard inputs.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/064_synthesis_shard_results.sql`.
- **Schema touched by:** `064_synthesis_shard_results.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `shard_key` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `manifest_hash` | `TEXT` | no | — | — | Stored value |
| `shard_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `shard_count` | `INTEGER` | yes | — | — | Stored value |
| `output_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_synthesis_shard_results_manifest` on `manifest_hash`.
- `sqlite_autoindex_synthesis_shard_results_1` on `shard_key` (unique).

## Who calls it

### Repository access surface

- `Repository.save_synthesis_shard_result()`
- `Repository.synthesis_shard_result()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/synthesis/source_set_synthesis.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_synthesis_runs_repo.py`

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
CREATE TABLE synthesis_shard_results (
  shard_key TEXT PRIMARY KEY,
  manifest_hash TEXT,
  shard_ordinal INTEGER NOT NULL,
  shard_count INTEGER NOT NULL,
  output_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
