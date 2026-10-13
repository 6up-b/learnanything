---
title: "source_comparisons"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "befc484502be9e48b5dcedb929eb0838b672c850"
source_commit_timestamp: "2026-10-13T18:03:47-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_comparisons"
  - "table source_comparisons"
schema_head: 199
table_name: "source_comparisons"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "189_source_comparisons.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/189_source_comparisons.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/source_retrieval/compare.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_comparisons`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds compare_sources results (canonical sources S3): each source's quote-verified contributions and pairwise relations under the caller's policy, the dropped lines and pins, the uncompared and unverified sources, and the manifest. No consensus field; reused for an identical query, policy and source set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `prompt_version`, `query_hash`, `query_md`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Canonical sources S3 (spec_source_practice_and_probes_v1.md §9.6): stored syntopic comparisons. A paid output (one comparison call over verified counterparts), never re-run on rebuild, reused when the same caller reopens the same comparison. It holds no consensus: per-source contributions, quote-verified pair relations and what was dropped or left uncompared.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/189_source_comparisons.sql`.
- **Schema touched by:** `189_source_comparisons.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `query_hash` | `TEXT` | yes | — | — | Stored value |
| `query_md` | `TEXT` | yes | — | — | Stored value |
| `requested_perspectives_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `counterpart_keys_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `comparison_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `dropped_lines_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `dropped_pins_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `unverified_sources_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `caller_context_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `ledger_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `caller` | `TEXT` | yes | — | — | Stored value |
| `caller_ref` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_comparisons_query` on `query_hash`, `created_at`.
- `sqlite_autoindex_source_comparisons_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/source_service.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

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
CREATE TABLE source_comparisons (
  id TEXT PRIMARY KEY,
  query_hash TEXT NOT NULL,
  query_md TEXT NOT NULL,
  requested_perspectives_json TEXT NOT NULL DEFAULT '[]',
  counterpart_keys_json TEXT NOT NULL DEFAULT '[]',
  comparison_json TEXT NOT NULL,
  dropped_lines_json TEXT NOT NULL DEFAULT '[]',
  dropped_pins_json TEXT NOT NULL DEFAULT '[]',
  unverified_sources_json TEXT NOT NULL DEFAULT '[]',
  policy TEXT NOT NULL CHECK (policy IN ('reading', 'assisted_practice', 'post_attempt')),
  caller_context_json TEXT NOT NULL,
  model TEXT,
  prompt_version TEXT NOT NULL,
  ledger_ids_json TEXT NOT NULL DEFAULT '[]',
  caller TEXT NOT NULL,
  caller_ref TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
