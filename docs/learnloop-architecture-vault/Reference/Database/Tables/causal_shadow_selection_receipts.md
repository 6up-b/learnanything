---
title: "causal_shadow_selection_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_shadow_selection_receipts"
  - "table causal_shadow_selection_receipts"
schema_head: 157
table_name: "causal_shadow_selection_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "146_causal_shadow_selection.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/146_causal_shadow_selection.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_shadow_selection_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each causal shadow selection decision so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_receipt_id`, `factor_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/146_causal_shadow_selection.sql`.
- **Schema touched by:** `146_causal_shadow_selection.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_receipt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `factor_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `incumbent_decision` | `TEXT` | yes | — | — | Stored value |
| `incumbent_reason` | `TEXT` | yes | — | — | Stored value |
| `shadow_verdict` | `TEXT` | yes | — | — | Stored value |
| `likelihood_regime` | `TEXT` | yes | — | — | Stored value |
| `loss_table_regime` | `TEXT` | yes | — | — | Stored value |
| `prior_basis` | `TEXT` | no | — | — | Stored value |
| `would_change_candidate` | `INTEGER` | no | — | — | Stored value |
| `would_change_measure_vs_repair` | `INTEGER` | no | — | — | Stored value |
| `would_change_repair` | `INTEGER` | no | — | — | Stored value |
| `baselines_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `body_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `shadow_policy_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_shadow_selection_regime` on `likelihood_regime`, `created_at`, `id`.
- `idx_causal_shadow_selection_factor` on `factor_id`, `created_at`, `id`.
- `sqlite_autoindex_causal_shadow_selection_receipts_2` on `decision_receipt_id` (unique).
- `sqlite_autoindex_causal_shadow_selection_receipts_1` on `id` (unique).

Database triggers:

- `causal_shadow_selection_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_shadow_selection_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_shadow_selection_receipt()`
- `Repository.causal_shadow_selection_receipts()`
- `Repository.insert_causal_shadow_selection_receipt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_diagnostic_selector.py`
- `src/learnloop/diagnosis/causal_selection_audit.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_shadow_selection.py`

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
CREATE TABLE causal_shadow_selection_receipts (
  id TEXT PRIMARY KEY,

  -- Exactly one shadow per live decision receipt: the live receipt is the
  -- decision's identity, and re-running the same decision writes a new live
  -- receipt (they are deliberately never deduplicated) with its own shadow.
  decision_receipt_id TEXT NOT NULL UNIQUE,

  factor_id TEXT NOT NULL,
  learning_object_id TEXT,
  attempt_id TEXT,
  candidate_id TEXT,

  -- The live P2 verdict this shadow rode along with.
  incumbent_decision TEXT NOT NULL,
  incumbent_reason TEXT NOT NULL,

  -- 'measure' | 'stop' | 'abstain' from the formal selector, or 'unavailable'
  -- when its inputs did not exist (the honest early state).
  shadow_verdict TEXT NOT NULL CHECK (shadow_verdict IN (
    'measure', 'stop', 'abstain', 'unavailable'
  )),

  -- §6.2 arms. 'arm_a_calibrated' is reserved (no calibrated channel exists
  -- yet); 'arm_b_noiseless_partition' is the declared-emission upper bound;
  -- 'arm_c_structural' may license skips only; 'none' = no instrument.
  likelihood_regime TEXT NOT NULL CHECK (likelihood_regime IN (
    'arm_a_calibrated', 'arm_b_noiseless_partition', 'arm_c_structural', 'none'
  )),
  loss_table_regime TEXT NOT NULL,
  prior_basis TEXT,

  -- NULL = not evaluable (an arm was unavailable), never a silent 0.
  would_change_candidate INTEGER CHECK (
    would_change_candidate IS NULL OR would_change_candidate IN (0, 1)
  ),
  would_change_measure_vs_repair INTEGER CHECK (
    would_change_measure_vs_repair IS NULL
    OR would_change_measure_vs_repair IN (0, 1)
  ),
  would_change_repair INTEGER CHECK (
    would_change_repair IS NULL OR would_change_repair IN (0, 1)
  ),

  baselines_json TEXT NOT NULL,
  body_json TEXT NOT NULL,
  shadow_policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
