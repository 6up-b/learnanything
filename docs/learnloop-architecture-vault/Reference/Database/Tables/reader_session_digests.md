---
title: "reader_session_digests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_session_digests"
  - "table reader_session_digests"
table_name: "reader_session_digests"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "227_reader_session_digests.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/227_reader_session_digests.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/history_card.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/daily_plan/router_reader.py"
  - "src/learnloop/db/stores/reader_digests.py"
  - "src/learnloop/figures/prefetch.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_session_digests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader session digest a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `prompt_version`, `session_key`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/227_reader_session_digests.sql`.
- **Schema touched by:** `227_reader_session_digests.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `session_key` | `TEXT` | yes | — | — | Stored value |
| `visit_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `ended_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `status` | `TEXT` | yes | — | — | Stored value |
| `summary_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `followup_commitment_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `valuation_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `revaluation_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `revalued_on` | `TEXT` | no | — | — | Stored value |
| `narrative_md` | `TEXT` | no | — | — | Stored value |
| `cited_event_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `dismissed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_session_digests_ended` on `ended_at`.
- `idx_reader_session_digests_extraction` on `extraction_id`, `ended_at`.
- `sqlite_autoindex_reader_session_digests_2` on `extraction_id`, `session_key` (unique).
- `sqlite_autoindex_reader_session_digests_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/reader_digests.py`
- `src/learnloop/figures/prefetch.py`

### Direct SQL writers

- `src/learnloop/db/stores/reader_digests.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_reader_digest_narrative.py`
- `tests/test_reader_followups.py`
- `tests/test_reader_followups_review.py`
- `tests/test_reader_followups_round5.py`
- `tests/test_reader_followups_successor.py`
- `tests/test_reader_session_digests_migration.py`

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
CREATE TABLE reader_session_digests (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  session_key TEXT NOT NULL,
  visit_ids_json TEXT NOT NULL DEFAULT '[]',
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('planned', 'incomplete')),
  summary_json TEXT NOT NULL DEFAULT '{}',
  followup_commitment_ids_json TEXT NOT NULL DEFAULT '[]',
  valuation_json TEXT NOT NULL DEFAULT '{}',
  revaluation_json TEXT,
  revalued_on TEXT,
  narrative_md TEXT,
  cited_event_ids_json TEXT,
  model TEXT,
  prompt_version TEXT,
  dismissed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (extraction_id, session_key)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
