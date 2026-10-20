---
title: "learner_gap_commitments"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "f0c85f2f7d750a4a8b407d4e0936bfd5f1f64501"
source_commit_timestamp: "2026-10-19T22:55:20-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_gap_commitments"
  - "table learner_gap_commitments"
schema_head: 214
table_name: "learner_gap_commitments"
table_role: "receipt"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "182_learner_text_gaps.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/182_learner_text_gaps.sql"
  - "src/learnloop/db/stores/learner_gaps.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_gap_commitments`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives learner gap commitment a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `gap_id`, `learning_object_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> A created prerequisite's light commitment: its seed item is one delayed check (pass: maintenance; fail: learning). Placement reads each row as a decision with source learner_text_gap; an undone creation's row is ignored.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/182_learner_text_gaps.sql`.
- **Schema touched by:** `182_learner_text_gaps.sql`, `208_learner_text_source_kinds.sql`, `212_hint_feedback_source_kind.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `gap_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/learner_text_gaps\|learner_text_gaps.id]] | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `first_review_due` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `gap_id` → [[Reference/Database/Tables/learner_text_gaps|`learner_text_gaps.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `learner_gap_commitments_lo` on `learning_object_id`, `created_at`, `id`.
- `sqlite_autoindex_learner_gap_commitments_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/learner_gaps.py`

### Direct SQL writers

- `src/learnloop/db/stores/learner_gaps.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_hint_feedback_widening.py`
- `tests/test_learner_text_source_widening.py`
- `tests/test_mvp016_upgrade.py`

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
CREATE TABLE learner_gap_commitments (
  id TEXT PRIMARY KEY,
  gap_id TEXT NOT NULL REFERENCES learner_text_gaps(id),
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT,
  first_review_due TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
