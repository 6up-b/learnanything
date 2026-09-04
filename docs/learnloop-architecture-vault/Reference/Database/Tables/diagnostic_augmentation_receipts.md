---
title: "diagnostic_augmentation_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_augmentation_receipts"
  - "table diagnostic_augmentation_receipts"
schema_head: 157
table_name: "diagnostic_augmentation_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "144_diagnostic_augmentation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/144_diagnostic_augmentation.sql"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_augmentation_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each diagnostic augmentation decision so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `grading_prompt_version`, `grader_provider`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One receipt per live graded attempt.  This is telemetry/provenance for the four Phase-C rungs; replay does not call a model and therefore never creates or rewrites one.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/144_diagnostic_augmentation.sql`.
- **Schema touched by:** `144_diagnostic_augmentation.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `grading_prompt_version` | `TEXT` | yes | — | — | Stored value |
| `grader_provider` | `TEXT` | no | — | — | Stored value |
| `grader_model` | `TEXT` | no | — | — | Stored value |
| `c1_repair_before_structure` | `INTEGER` | yes | — | — | Stored value |
| `c2_verifier_observations_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `c3_sample_count` | `INTEGER` | yes | — | — | Stored value |
| `c3_agreement_support` | `REAL` | yes | — | — | Stored value |
| `c3_disagreement_causes_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `c4_history_attempt_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `hypotheses_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `revert_criteria_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_diagnostic_augmentation_receipts_2` on `attempt_id` (unique).
- `sqlite_autoindex_diagnostic_augmentation_receipts_1` on `id` (unique).

Database triggers:

- `diagnostic_augmentation_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `diagnostic_augmentation_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.diagnostic_augmentation_receipt_for_attempt()`
- `Repository.diagnostic_augmentation_receipt_rows()`
- `Repository.insert_diagnostic_augmentation_receipt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/diagnosis/diagnostic_augmentation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_agent_run_tokens.py`
- `tests/test_coldness_receipt.py`
- `tests/test_diagnostic_augmentation.py`

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
CREATE TABLE diagnostic_augmentation_receipts (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE,
  grading_prompt_version TEXT NOT NULL,
  grader_provider TEXT,
  grader_model TEXT,
  c1_repair_before_structure INTEGER NOT NULL
    CHECK (c1_repair_before_structure IN (0, 1)),
  c2_verifier_observations_json TEXT NOT NULL,
  c3_sample_count INTEGER NOT NULL CHECK (c3_sample_count >= 1),
  c3_agreement_support REAL NOT NULL
    CHECK (c3_agreement_support >= 0.0 AND c3_agreement_support <= 1.0),
  c3_disagreement_causes_json TEXT NOT NULL,
  c4_history_attempt_ids_json TEXT NOT NULL,
  hypotheses_json TEXT NOT NULL,
  revert_criteria_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
