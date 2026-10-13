---
title: "diagnosis_context_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "28da3101f65026ca0d14ca21946d7c2c92e97469"
source_commit_timestamp: "2026-10-13T00:28:21-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite diagnosis_context_receipts"
  - "table diagnosis_context_receipts"
schema_head: 182
table_name: "diagnosis_context_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "170_blind_grading_diagnosis_split.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/170_blind_grading_diagnosis_split.sql"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/diagnosis/recurrence/report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `diagnosis_context_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each diagnosis context decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `diagnosis_id`, `context_as_of_attempt_id`, `context_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Exactly what one diagnosis was shown (the audit record; replay never re-assembles a context).

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
| `diagnosis_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/attempt_diagnoses\|attempt_diagnoses.id]] | Stored value |
| `context_hash` | `TEXT` | no | — | — | Stored value |
| `context_as_of_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `lagged_attempts` | `INTEGER` | no | — | — | Stored value |
| `failure_attempt_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `success_attempt_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `hypothesis_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `registry_candidate_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `prerequisite_refs_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `retrieval_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `anchoring_suspect` | `INTEGER` | yes | `0` | — | Stored value |
| `validated_citations_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `diagnosis_id` → [[Reference/Database/Tables/attempt_diagnoses|`attempt_diagnoses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_diagnosis_context_receipts_2` on `diagnosis_id` (unique).
- `sqlite_autoindex_diagnosis_context_receipts_1` on `id` (unique).

Database triggers:

- `diagnosis_context_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnosis_context_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/diagnoses.py`
- `src/learnloop/db/stores/recurrence.py`
- `src/learnloop/diagnosis/recurrence/report.py`

### Direct SQL writers

- `src/learnloop/db/stores/diagnoses.py`

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
CREATE TABLE diagnosis_context_receipts (
  id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL UNIQUE REFERENCES attempt_diagnoses(id),
  context_hash TEXT,
  context_as_of_attempt_id TEXT,
  lagged_attempts INTEGER,
  failure_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  success_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  hypothesis_ids_json TEXT NOT NULL DEFAULT '[]',
  registry_candidate_ids_json TEXT NOT NULL DEFAULT '[]',
  prerequisite_refs_json TEXT NOT NULL DEFAULT '[]',
  retrieval_json TEXT NOT NULL DEFAULT '{}',
  anchoring_suspect INTEGER NOT NULL DEFAULT 0 CHECK (anchoring_suspect IN (0, 1)),
  validated_citations_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
