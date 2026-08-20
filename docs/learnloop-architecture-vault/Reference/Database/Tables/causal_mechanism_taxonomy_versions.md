---
title: "causal_mechanism_taxonomy_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_mechanism_taxonomy_versions"
  - "table causal_mechanism_taxonomy_versions"
schema_head: 156
table_name: "causal_mechanism_taxonomy_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "119_causal_mechanism_taxonomy.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/119_causal_mechanism_taxonomy.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_mechanism_taxonomy_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of causal mechanism taxonomy so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `source_head_hash`, `algorithm`, `min_cluster_size`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Causal-attribution P1 (§6.4): mechanism taxonomies are explicit, content-addressed batch artifacts.  They do not rewrite hypothesis history and are never minted from the attempt-materialization hot path.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/119_causal_mechanism_taxonomy.sql`.
- **Schema touched by:** `119_causal_mechanism_taxonomy.sql`, `133_causal_mechanism_repair_key.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `algorithm` | `TEXT` | yes | — | — | Stored value |
| `min_cluster_size` | `INTEGER` | yes | — | — | Stored value |
| `source_head_hash` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `taxonomy_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_mechanism_taxonomy_status` on `status`, `created_at`, `id`.
- `sqlite_autoindex_causal_mechanism_taxonomy_versions_1` on `id` (unique).

Database triggers:

- `causal_mechanism_taxonomy_versions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_mechanism_taxonomy_versions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_mechanism_taxonomy_version()`
- `Repository.insert_causal_mechanism_taxonomy_version()`
- `Repository.latest_active_causal_mechanism_taxonomy()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`

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
CREATE TABLE causal_mechanism_taxonomy_versions (
  id TEXT PRIMARY KEY,
  algorithm TEXT NOT NULL,
  min_cluster_size INTEGER NOT NULL CHECK (min_cluster_size >= 2),
  source_head_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'active')),
  taxonomy_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
