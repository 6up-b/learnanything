---
title: "causal_probe_decision_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_probe_decision_receipts"
  - "table causal_probe_decision_receipts"
schema_head: 157
table_name: "causal_probe_decision_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "124_causal_probe_decisions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/124_causal_probe_decisions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/diagnosis/scoreboard.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_probe_decision_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes each decision, its inputs, and its reason for causal probe so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `factor_id`, `learning_object_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/124_causal_probe_decisions.sql`.
- **Schema touched by:** `124_causal_probe_decisions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_fingerprint` | `TEXT` | yes | — | — | Stored value |
| `factor_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `misconception_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `decision` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `repair_status` | `TEXT` | yes | — | — | Stored value |
| `decision_policy_version` | `TEXT` | yes | — | — | Stored value |
| `formula_version` | `TEXT` | yes | — | — | Stored value |
| `inputs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `parameters_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `hypothesis_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `repair_class_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `blind_bundle_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `machine_check_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_probe_decision_receipt_decision` on `decision`, `created_at`, `id`.
- `idx_causal_probe_decision_receipt_factor` on `factor_id`, `created_at`, `id`.
- `sqlite_autoindex_causal_probe_decision_receipts_1` on `id` (unique).

Database triggers:

- `causal_probe_decision_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_probe_decision_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_probe_decision_receipt()`
- `Repository.causal_probe_decision_receipts()`
- `Repository.insert_causal_probe_decision_receipt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/scoreboard.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_orchestrator.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_shadow_selection.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_probe_block_end.py`
- `tests/test_scoreboard.py`

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
CREATE TABLE causal_probe_decision_receipts (
  id TEXT PRIMARY KEY,
  decision_fingerprint TEXT NOT NULL,
  factor_id TEXT NOT NULL,
  learning_object_id TEXT,
  attempt_id TEXT,
  misconception_id TEXT,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  repair_status TEXT NOT NULL CHECK (
    repair_status IN (
      'started',
      'needs_disambiguation',
      'deferred_machine_checks',
      'safe_common_repair_available',
      'blocked_pending_review'
    )
  ),
  decision_policy_version TEXT NOT NULL,
  formula_version TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  hypothesis_ids_json TEXT NOT NULL,
  repair_class_ids_json TEXT NOT NULL,
  candidate_id TEXT,
  blind_bundle_ids_json TEXT NOT NULL,
  machine_check_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
