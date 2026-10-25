---
title: "diagnosis_would_merge_log"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "a5c36443023a87678721d241d47d6fe4b45fc108"
source_commit_timestamp: "2026-10-25T17:00:22-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite diagnosis_would_merge_log"
  - "table diagnosis_would_merge_log"
schema_head: 222
table_name: "diagnosis_would_merge_log"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/db/stores/diagnoses.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `diagnosis_would_merge_log`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnosis would merge log a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `diagnosis_id`, `hypothesis_id`, `model_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §9.5 shadow would-merge log: the nearest prior hypotheses for one newly minted hypothesis, next to its exact-key group. Never read by routing.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/170_blind_grading_diagnosis_split.sql`.
- **Schema touched by:** `170_blind_grading_diagnosis_split.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `diagnosis_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/attempt_diagnoses\|attempt_diagnoses.id]] | Stored value |
| `hypothesis_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `model_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `exact_key` | `TEXT` | yes | — | — | Stored value |
| `exact_group_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `neighbors_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `diagnosis_id` → [[Reference/Database/Tables/attempt_diagnoses|`attempt_diagnoses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_diagnosis_would_merge_log_2` on `hypothesis_id`, `model_id` (unique).
- `sqlite_autoindex_diagnosis_would_merge_log_1` on `id` (unique).

Database triggers:

- `diagnosis_would_merge_log_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnosis_would_merge_log_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`

### Direct SQL writers

None found by exact static reference scan.

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
CREATE TABLE diagnosis_would_merge_log (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT REFERENCES attempt_diagnoses(id),
  hypothesis_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  exact_key TEXT NOT NULL,
  exact_group_ids_json TEXT NOT NULL DEFAULT '[]',
  neighbors_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  UNIQUE (hypothesis_id, model_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
