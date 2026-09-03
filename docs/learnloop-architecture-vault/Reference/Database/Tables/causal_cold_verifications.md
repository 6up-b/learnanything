---
title: "causal_cold_verifications"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_cold_verifications"
  - "table causal_cold_verifications"
schema_head: 157
table_name: "causal_cold_verifications"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "121_causal_probe_coherence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/121_causal_probe_coherence.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/certification_cold_probe.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_cold_verifications`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives causal cold verification a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `source_attempt_id`, `cold_attempt_id`, `repair_class_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/121_causal_probe_coherence.sql`.
- **Schema touched by:** `121_causal_probe_coherence.sql`, `139_certification_cold_probes.sql`, `145_causal_cold_outcomes.sql`, `149_coldness_receipts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `cold_attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `repair_class_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `hypothesis_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `source_surface_family` | `TEXT` | yes | — | — | Stored value |
| `cold_surface_family` | `TEXT` | yes | — | — | Stored value |
| `avoided_affordances_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `success` | `INTEGER` | yes | — | — | Stored value |
| `capability_update_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `diagnosis_support_update_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `repair_effect_support_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_cold_verification_source` on `source_attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_causal_cold_verifications_2` on `cold_attempt_id` (unique).
- `sqlite_autoindex_causal_cold_verifications_1` on `id` (unique).

Database triggers:

- `causal_cold_verifications_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_cold_verifications_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_cold_verification_for_attempt()`
- `Repository.insert_causal_cold_verification()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_certification_cold_probe.py`
- `tests/test_guided_redo.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_coldness_receipt.py`

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
CREATE TABLE causal_cold_verifications (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL,
  cold_attempt_id TEXT NOT NULL UNIQUE,
  repair_class_id TEXT NOT NULL,
  hypothesis_ids_json TEXT NOT NULL,
  source_surface_family TEXT NOT NULL,
  cold_surface_family TEXT NOT NULL,
  avoided_affordances_json TEXT NOT NULL,
  success INTEGER NOT NULL CHECK (success IN (0, 1)),
  capability_update_json TEXT NOT NULL,
  diagnosis_support_update_json TEXT NOT NULL,
  repair_effect_support_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (source_attempt_id != cold_attempt_id),
  CHECK (source_surface_family != cold_surface_family)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
