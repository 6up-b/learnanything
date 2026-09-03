---
title: "commitment_arc_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_arc_events"
  - "table commitment_arc_events"
schema_head: 157
table_name: "commitment_arc_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "095_commitment_arcs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/095_commitment_arcs.sql"
  - "src/learnloop/curriculum/commitment_arcs.py"
  - "src/learnloop/db/repositories.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_arc_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of commitment arc so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `arc_id`, `event_ordinal`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/095_commitment_arcs.sql`.
- **Schema touched by:** `095_commitment_arcs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `arc_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitment_arcs\|commitment_arcs.id]] | Stored value |
| `event_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `receipt_key` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `arc_id` → [[Reference/Database/Tables/commitment_arcs|`commitment_arcs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_commitment_arc_events_receipt` on `arc_id`, `receipt_key` (unique).
- `idx_commitment_arc_events_arc` on `arc_id`, `event_ordinal`.
- `sqlite_autoindex_commitment_arc_events_2` on `arc_id`, `event_ordinal` (unique).
- `sqlite_autoindex_commitment_arc_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_commitment_arc_event()`
- `Repository.commitment_arc_events()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/commitment_arcs.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_commitment_arcs.py`
- `tests/test_p3_journeys.py`

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
CREATE TABLE commitment_arc_events (
  id TEXT PRIMARY KEY,
  arc_id TEXT NOT NULL REFERENCES commitment_arcs(id),
  event_ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL
    CHECK (kind IN (
      'arc_created', 'arc_version_appended', 'stage_reached',
      'transition_requested', 'transition_committed', 'transition_declined',
      'arc_paused', 'arc_resumed', 'envelope_shrink_requested', 'policy_changed',
      'prime_offered', 'prime_answered'
    )),
  detail_json TEXT,
  -- Idempotency for at-most-once transition requests (§10.2): a replayed decision
  -- receipt is a no-op.
  receipt_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(arc_id, event_ordinal)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
