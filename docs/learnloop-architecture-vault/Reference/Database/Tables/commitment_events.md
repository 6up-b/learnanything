---
title: "commitment_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitment_events"
  - "table commitment_events"
schema_head: 156
table_name: "commitment_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/curriculum/commitments.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/depth_rungs.py"
  - "src/learnloop/curriculum/depth_transition.py"
  - "src/learnloop/scheduling/controller_snapshot.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitment_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of commitment so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `commitment_id`, `commitment_version_id`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `commitment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitments\|commitments.id]] | Stored value |
| `commitment_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/commitment_versions\|commitment_versions.id]] | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `commitment_version_id` → [[Reference/Database/Tables/commitment_versions|`commitment_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_id` → [[Reference/Database/Tables/commitments|`commitments.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_commitment_events_commitment` on `commitment_id`, `created_at`.
- `sqlite_autoindex_commitment_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_commitment_version_rows()`
- `Repository.append_commitment_event()`
- `Repository.commitment_events_for()`
- `Repository.record_depth_transition_atomic()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/commitments.py`
- `src/learnloop/curriculum/depth_rungs.py`
- `src/learnloop/curriculum/depth_transition.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/scheduling/controller_snapshot.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_p2_acceptance.py`
- `tests/test_commitment_arcs.py`
- `tests/test_commitments.py`
- `tests/test_depth_transition.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_journey6.py`

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
CREATE TABLE commitment_events (
  id TEXT PRIMARY KEY,
  commitment_id TEXT NOT NULL REFERENCES commitments(id) ON DELETE CASCADE,
  commitment_version_id TEXT REFERENCES commitment_versions(id),
  kind TEXT NOT NULL CHECK (kind IN (
    'created', 'version_appended', 'disposition_changed', 'depth_policy_changed',
    'depth_envelope_changed', 'depth_milestone_reached', 'depth_transition_committed',
    'target_added', 'target_removed', 'family_attached', 'family_detached',
    'paused', 'resumed', 'retired')),
  detail_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
