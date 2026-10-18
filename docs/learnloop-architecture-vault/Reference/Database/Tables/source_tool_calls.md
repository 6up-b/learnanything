---
title: "source_tool_calls"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "d03b6bba09389c9eb2b610b4500f5d31341ffa9e"
source_commit_timestamp: "2026-10-18T17:30:53-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_tool_calls"
  - "table source_tool_calls"
schema_head: 213
table_name: "source_tool_calls"
table_role: "receipt"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "192_source_tool_calls.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/192_source_tool_calls.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/instructional/tools.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_tool_calls`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Receipts for the typed source tools (canonical sources S4): a request row per validated request from the tutor, the router or an external agent (its stored caller context, derived policy, validated arguments and dropped ids, refused when it leaked the answer or arrived during a cold administration) and a run row per execution naming the request (result refs, keys, source versions, model, latency). Append-only. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `parent_id`, `ledger_id`, `row_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Canonical sources S4 (spec_source_practice_and_probes_v1.md §10.4): the typed tool interface's receipts. Append-only: a validated request writes a `request` row; running it writes a `run` row naming the request as its parent. Nothing is updated in place, and nothing here is evidence, mastery, FSRS or scheduler state.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/192_source_tool_calls.sql`.
- **Schema touched by:** `192_source_tool_calls.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `parent_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_tool_calls\|source_tool_calls.id]] | Stored value |
| `row_kind` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `caller_kind` | `TEXT` | yes | — | — | Stored value |
| `caller_ref` | `TEXT` | no | — | — | Stored value |
| `context_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `tool` | `TEXT` | yes | — | — | Stored value |
| `arguments_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `dropped_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `ledger_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `result_ref` | `TEXT` | no | — | — | Stored value |
| `result_keys_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `source_versions_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `latency_ms` | `INTEGER` | no | — | — | Stored value |
| `cost_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_id` → [[Reference/Database/Tables/source_tool_calls|`source_tool_calls.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_tool_calls_caller` on `caller_kind`, `caller_ref`, `created_at`.
- `idx_source_tool_calls_parent` on `parent_id`.
- `sqlite_autoindex_source_tool_calls_1` on `id` (unique).

Database triggers:

- `source_tool_calls_no_delete` — schema-enforced lifecycle or immutability constraint.
- `source_tool_calls_no_update` — schema-enforced lifecycle or immutability constraint.

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
CREATE TABLE source_tool_calls (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES source_tool_calls(id),
  row_kind TEXT NOT NULL CHECK (row_kind IN ('request', 'run')),
  created_at TEXT NOT NULL,
  caller_kind TEXT NOT NULL CHECK (caller_kind IN ('tutor', 'router', 'agent')),
  caller_ref TEXT,
  -- The stored caller context the policy was derived from (re-read at run time,
  -- so the policy cannot change between the answer and the run).
  context_json TEXT NOT NULL,
  policy TEXT NOT NULL,
  tool TEXT NOT NULL CHECK (tool IN ('find_practice', 'find_sources', 'compare_sources', 'find_facets',
                                     'practice_availability')),
  arguments_json TEXT NOT NULL,
  dropped_json TEXT NOT NULL DEFAULT '[]',
  ledger_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('requested', 'refused', 'ran', 'failed')),
  result_ref TEXT,
  result_keys_json TEXT NOT NULL DEFAULT '[]',
  source_versions_json TEXT NOT NULL DEFAULT '{}',
  model TEXT,
  prompt_version TEXT,
  latency_ms INTEGER,
  cost_json TEXT,
  CHECK ((row_kind = 'request' AND parent_id IS NULL AND status IN ('requested', 'refused'))
         OR (row_kind = 'run' AND parent_id IS NOT NULL AND status IN ('ran', 'failed')))
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
