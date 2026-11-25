---
title: "attempt_grade_curves"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite attempt_grade_curves"
  - "table attempt_grade_curves"
table_name: "attempt_grade_curves"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "274_attempt_grade_curves.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/274_attempt_grade_curves.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/grade_curves.py"
  - "src/learnloop/db/writer_fence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_grade_curves`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attempt grade curve a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `algorithm_version`, `epoch_key`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The effective mastery curve for one applied grading epoch. A surprise row belongs to one attempt, so activation can reconstruct at most its current epoch.

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/274_attempt_grade_curves.sql`.
- **Schema touched by:** `274_attempt_grade_curves.sql`, `275_writer_fence.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `epoch_key` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `grading_revision` | `INTEGER` | no | — | — | Stored value |
| `item_a` | `REAL` | no | — | — | Stored value |
| `item_b` | `REAL` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `provenance` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_attempt_grade_curves_1` on `attempt_id`, `epoch_key` (unique).

Database triggers:

- `attempt_grade_curves_no_delete` — schema-enforced lifecycle or immutability constraint.
- `attempt_grade_curves_no_replace` — schema-enforced lifecycle or immutability constraint.
- `attempt_grade_curves_no_update` — schema-enforced lifecycle or immutability constraint.
- `writer_fence_attempt_grade_curves_insert` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/grade_curves.py`

### Direct SQL writers

- `src/learnloop/db/stores/grade_curves.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/grade_curves_migration_helpers.py`
- `tests/test_grade_curves_capture_integrity.py`
- `tests/test_grade_curves_migration.py`
- `tests/test_grading_cli.py`
- `tests/test_lesson_weight_facts.py`
- `tests/test_teacher_te5_grade_curves.py`
- `tests/test_writer_fence.py`
- `tests/writer_fence_helpers.py`

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
CREATE TABLE attempt_grade_curves (
    attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
    epoch_key TEXT NOT NULL,
    grading_revision INTEGER,
    item_a REAL,
    item_b REAL,
    algorithm_version TEXT NOT NULL,
    provenance TEXT NOT NULL CHECK (provenance IN ('graded', 'reconstructed_at_upgrade', 'missing_at_upgrade')),
    PRIMARY KEY (attempt_id, epoch_key),
    CHECK ((grading_revision IS NULL AND (epoch_key = 'no_evidence' OR epoch_key GLOB 'legacy:*'))
        OR (grading_revision IS NOT NULL AND epoch_key = 'revision:' || grading_revision)),
    CHECK ((provenance = 'missing_at_upgrade' AND item_a IS NULL AND item_b IS NULL)
        OR (provenance <> 'missing_at_upgrade' AND typeof(item_a) = 'real' AND typeof(item_b) = 'real'))
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
