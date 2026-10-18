---
title: "instructional_impressions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "0ead90ec9fe16acc8f363dcd6ff72f6d83d843df"
source_commit_timestamp: "2026-10-18T17:46:52-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite instructional_impressions"
  - "table instructional_impressions"
schema_head: 212
table_name: "instructional_impressions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "187_source_service_callers.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/187_source_service_callers.sql"
  - "src/learnloop/db/stores/source_service.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `instructional_impressions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records which find_practice proposal candidates a surface actually rendered (canonical sources S0): retrieved, displayed and served stay three records. Read only by the exposure rule (an earlier impression of a prompt excludes it from the independent intents within the cold retrieval delay) and by S5's intervention records; deliberately not activity_exposure_events, whose rendered rows burn a surface. Append-only. It supplies replay-stable input rather than a disposable cache. Rows bind `proposal_id`, `practice_item_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> What reached the screen: one row per proposal candidate a surface rendered. Retrieved, displayed and served stay three separate records (the proposal row, this impression, the pick or attempt). Deliberately NOT activity_exposure_events: `rendered` there is a once-ever burn boundary for held-out use, and a glimpse in a strip must not burn a surface. Read only by the exposure rule (an earlier impression of a prompt excludes it from the independent intents within the cold retrieval delay) and by S5's records.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/187_source_service_callers.sql`.
- **Schema touched by:** `187_source_service_callers.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `caller_kind` | `TEXT` | no | — | — | Stored value |
| `caller_ref` | `TEXT` | no | — | — | Stored value |
| `proposal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `candidate_kind` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `shown_fields_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_instructional_impressions_proposal` on `proposal_id`.
- `idx_instructional_impressions_extraction` on `extraction_id`, `created_at`.
- `idx_instructional_impressions_item` on `practice_item_id`, `created_at`.
- `sqlite_autoindex_instructional_impressions_1` on `id` (unique).

Database triggers:

- `instructional_impressions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `instructional_impressions_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_proposal_impressions.py`

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
CREATE TABLE instructional_impressions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  surface TEXT NOT NULL CHECK (surface IN ('tutor_strip', 'plan', 'dl3_box', 'reader', 'other')),
  caller_kind TEXT,
  caller_ref TEXT,
  proposal_id TEXT NOT NULL,
  candidate_kind TEXT NOT NULL CHECK (candidate_kind IN ('item', 'source_exercise')),
  practice_item_id TEXT,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  shown_fields_json TEXT NOT NULL,
  session_id TEXT,
  CHECK (
    (candidate_kind = 'item' AND practice_item_id IS NOT NULL)
    OR (candidate_kind = 'source_exercise' AND extraction_id IS NOT NULL)
  )
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
