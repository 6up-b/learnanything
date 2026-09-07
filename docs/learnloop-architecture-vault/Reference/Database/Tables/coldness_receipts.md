---
title: "coldness_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite coldness_receipts"
  - "table coldness_receipts"
schema_head: 157
table_name: "coldness_receipts"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "149_coldness_receipts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/149_coldness_receipts.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop_sidecar/handlers/serializers.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `coldness_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each coldness decision so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `followup_task_id`, `remediation_episode_id`, `source_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/149_coldness_receipts.sql`.
- **Schema touched by:** `149_coldness_receipts.sql`, `151_cold_measurement_opportunities.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `lane` | `TEXT` | yes | — | — | Stored value |
| `stage` | `TEXT` | yes | — | — | Stored value |
| `followup_task_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cold_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cold_verification_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `dimensions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `derived_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `telemetry_coverage_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `measurement_opportunity_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_coldness_receipts_measurement_opportunity` on `measurement_opportunity_id`, `created_at`, `id`.
- `uq_coldness_receipts_opportunity_stage` on `measurement_opportunity_id`, `stage` (unique).
- `idx_coldness_receipts_lane` on `lane`, `stage`, `created_at`, `id`.
- `idx_coldness_receipts_episode` on `remediation_episode_id`, `created_at`, `id`.
- `uq_coldness_receipts_verification` on `cold_verification_id` (unique).
- `uq_coldness_receipts_task_stage` on `followup_task_id`, `stage` (unique).
- `sqlite_autoindex_coldness_receipts_1` on `id` (unique).

Database triggers:

- `coldness_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `coldness_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.coldness_receipt()`
- `Repository.coldness_receipt_for_opportunity_stage()`
- `Repository.coldness_receipt_for_task_stage()`
- `Repository.coldness_receipt_for_verification()`
- `Repository.coldness_receipts_for_task()`
- `Repository.insert_coldness_receipt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_coldness_receipt.py`
- `tests/test_causal_cold_outcomes.py`
- `tests/test_certification_cold_probe.py`

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
CREATE TABLE coldness_receipts (
  id TEXT PRIMARY KEY,

  lane TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN ('administration', 'final')),

  followup_task_id TEXT,
  remediation_episode_id TEXT,
  source_attempt_id TEXT,
  -- NULL on the administration snapshot (no attempt yet) and on refusal
  -- receipts whose disposition never had a concrete attempt.
  cold_attempt_id TEXT,
  -- Set exactly when the final receipt accompanies a measured verification.
  cold_verification_id TEXT,

  -- Per-dimension {status: pass|fail|unknown, evidence: {...}} for:
  -- retrieval_delay, exposure_isolation, surface_novelty, selection_basis,
  -- answer_leakage, window_integrity, verification_blinding, unassisted.
  dimensions_json TEXT NOT NULL,
  -- The derived qualification claims plus the disposition outcome and the
  -- administration-receipt link.
  derived_json TEXT NOT NULL,
  -- Scoped absence claim: enumerated scanned ledgers, interval boundaries,
  -- known_unobserved_channels, telemetry_coverage_version.
  telemetry_coverage_json TEXT NOT NULL,

  receipt_version TEXT NOT NULL,
  created_at TEXT NOT NULL, measurement_opportunity_id TEXT,

  -- An administration snapshot precedes any attempt or verification.
  CHECK (
    stage != 'administration'
    OR (cold_attempt_id IS NULL AND cold_verification_id IS NULL)
  )
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
