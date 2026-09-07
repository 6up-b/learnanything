---
title: "parameter_registry"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite parameter_registry"
  - "table parameter_registry"
schema_head: 157
table_name: "parameter_registry"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "069_parameter_registry.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/069_parameter_registry.sql"
  - "src/learnloop/cli/registry.py"
  - "src/learnloop/content/sources/block_health.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/familiarity.py"
  - "src/learnloop/ops/vault_upgrade.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/params/sensitivity_certificates.py"
  - "src/learnloop/cli/grading.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `parameter_registry`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives parameter registry a stable database identity so schema changes and reviewed mutations remain reproducible and auditable. It supplies replay-stable input rather than a disposable cache. Rows bind `sensitivity_certificate_id`, `promotion_evidence_id`, `evidence_manifest_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P0.5 calibration discipline (spec_p0_measurement_correctness §6): per-vault effective state of the code-authored parameter registry, the frozen per-algorithm-version manifests replay reads, the sim-sweep sensitivity certificates required for `active` lifecycle, and the bind-event logs mandated for `dormant` constraint parameters. Definitions live in code (services/parameter_registry.py); this file stores only the time-varying, per-vault projection + immutable evidence/manifest rows. Additive. No FK to vault-owned ids (repo convention); references are stored as plain ids. (b) Per-vault effective-state projection. Rewritten by registry_service.refresh; a projection, never raw history -> safe to UPSERT (like goal_contract_heads).

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/069_parameter_registry.sql`.
- **Schema touched by:** `069_parameter_registry.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `path` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `param_class` | `TEXT` | yes | — | — | Stored value |
| `effective_value_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `effective_value_hash` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `lifecycle` | `TEXT` | yes | — | — | Stored value |
| `rationale` | `TEXT` | yes | — | — | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `owner` | `TEXT` | yes | — | — | Stored value |
| `sensitivity_certificate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `promotion_evidence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `evidence_manifest_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `redundancy_proof_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `last_review_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_parameter_registry_1` on `path` (unique).

## Who calls it

### Repository access surface

- `Repository.parameter_registry_entries()`
- `Repository.parameter_registry_entry()`
- `Repository.upsert_parameter_registry_entry()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/grading.py`
- `src/learnloop/cli/registry.py`
- `src/learnloop/params/parameter_registry.py`
- `src/learnloop/params/sensitivity_certificates.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_constraint_engine.py`
- `tests/test_grading_cli.py`
- `tests/test_kinship_feature.py`
- `tests/test_open_world_gate.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_registry_audit.py`
- `tests/test_sensitivity_certificates.py`
- `tests/test_table_roles.py`

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
CREATE TABLE parameter_registry (
  path TEXT PRIMARY KEY,               -- stable key, matches the code REGISTRY
  kind TEXT NOT NULL CHECK (kind IN ('decision','structural')),
  param_class TEXT NOT NULL,
  effective_value_json TEXT NOT NULL,  -- resolved value (scalar/tuple/map)
  effective_value_hash TEXT NOT NULL,  -- _canonical_hash of the value
  source TEXT NOT NULL CHECK (source IN
    ('default','vault_override','fitted','model_artifact')),
  status TEXT NOT NULL CHECK (status IN
    ('heuristic','simulation_validated','live_calibrated')),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('active','dormant','deleted')),
  rationale TEXT NOT NULL,
  scope TEXT NOT NULL,
  owner TEXT NOT NULL,
  -- evidence refs (§6, U-022 v2 -- two-artifact split):
  --  * sensitivity_certificate_id: the COVERAGE certificate (descriptive) required
  --    for EVERY active decision parameter; documents where in the swept range
  --    decisions flip. Finding flip points does NOT invalidate it.
  --  * promotion_evidence_id: the sim-derived PROMOTION EVIDENCE (normative) that
  --    gates status heuristic -> simulation_validated (carries the decision_stable
  --    refusal). Both ids reference parameter_sensitivity_certificates rows.
  --  * evidence_manifest_id: activated real-outcome manifest gating -> live_calibrated.
  --  * redundancy_proof_id: redundancy proof gating -> deleted.
  -- Stored as ids, not blobs.
  sensitivity_certificate_id TEXT,
  promotion_evidence_id TEXT,
  evidence_manifest_id TEXT,
  redundancy_proof_id TEXT,
  last_review_at TEXT,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
