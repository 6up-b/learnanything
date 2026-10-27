---
title: "retrieval_feedback"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0843991f2b18f27dbcfa32509c74e214a072eab8"
source_commit_timestamp: "2026-10-27T17:51:02-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite retrieval_feedback"
  - "table retrieval_feedback"
schema_head: 226
table_name: "retrieval_feedback"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "220_retrieval_spaces.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/220_retrieval_spaces.sql"
  - "src/learnloop/db/stores/retrieval_spaces.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/source_retrieval/feedback.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `retrieval_feedback`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives retrieval feedback a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `receipt_id`, `owner_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> RECEIPT, append-only: what one search delivered and the signals that later fell on it (§9.2). One 'query' row per logged search (its spaces, their availability and reasons, the served and the would-be learned weights, the exploration draw and its propensities, the RNG seed); one 'delivered' row per delivered span (its rank in every contributing list and its position); a 'cited', 'opened' or 'anchored' row per signal, naming the query receipt it answers. No "not relevant" button exists: learner text and actions are the signals.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/220_retrieval_spaces.sql`.
- **Schema touched by:** `220_retrieval_spaces.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `event` | `TEXT` | yes | — | — | Stored value |
| `consumer` | `TEXT` | yes | — | — | Stored value |
| `query_kind` | `TEXT` | yes | — | — | Stored value |
| `owner_id` | `TEXT` | yes | `''` | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `position` | `INTEGER` | no | — | — | Stored value |
| `payload_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `retrieval_feedback_owner` on `consumer`, `owner_id`, `event`.
- `retrieval_feedback_receipt` on `receipt_id`, `event`.
- `sqlite_autoindex_retrieval_feedback_1` on `id` (unique).

Database triggers:

- `retrieval_feedback_no_delete` — schema-enforced lifecycle or immutability constraint.
- `retrieval_feedback_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/retrieval_spaces.py`
- `src/learnloop/source_retrieval/feedback.py`

### Direct SQL writers

- `src/learnloop/db/stores/retrieval_spaces.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_retrieval_spaces_migration.py`

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
CREATE TABLE retrieval_feedback (
  id TEXT PRIMARY KEY,
  receipt_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN ('query', 'delivered', 'cited', 'opened', 'anchored')),
  consumer TEXT NOT NULL,
  query_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL DEFAULT '',
  extraction_id TEXT,
  span_id TEXT,
  position INTEGER CHECK (position IS NULL OR position >= 1),
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK ((event = 'query') = (span_id IS NULL))
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
