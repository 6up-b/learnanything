---
title: "parameter_sensitivity_certificates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite parameter_sensitivity_certificates"
  - "table parameter_sensitivity_certificates"
schema_head: 157
table_name: "parameter_sensitivity_certificates"
table_role: "receipt"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "069_parameter_registry.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/069_parameter_registry.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/params/sensitivity_certificates.py"
  - "src/learnloop/params/parameter_registry.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `parameter_sensitivity_certificates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives parameter sensitivity certificate a stable database identity so schema changes and reviewed mutations remain reproducible and auditable. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `covered_value_hash`, `sim_report_hash`, `path`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Sim-sweep artifacts (§3): each row shows where in the plausible range a decision flips. Stores BOTH roles (distinguished by which registry column references them): COVERAGE certificates (required for every active decision param; flip points are informational) and PROMOTION EVIDENCE (decision_stable=1 gates promotion). Immutable.

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/069_parameter_registry.sql`.
- **Schema touched by:** `069_parameter_registry.sql`, `100_kinship_kernel_and_shadow_components.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `path` | `TEXT` | yes | — | — | Stored value |
| `covered_value_hash` | `TEXT` | yes | — | — | Stored value |
| `plausible_range_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `flip_points_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `decision_stable` | `INTEGER` | yes | — | — | Stored value |
| `scenario_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `sim_report_hash` | `TEXT` | yes | — | — | Stored value |
| `produced_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_psc_path` on `path`.
- `sqlite_autoindex_parameter_sensitivity_certificates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_sensitivity_certificate()`
- `Repository.sensitivity_certificates_for_path()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/params/parameter_registry.py`
- `src/learnloop/params/sensitivity_certificates.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_kinship_feature.py`
- `tests/test_shadow_components.py`

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
CREATE TABLE parameter_sensitivity_certificates (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  covered_value_hash TEXT NOT NULL,    -- the effective value this cert certifies
  plausible_range_json TEXT NOT NULL,  -- {low, high} swept
  flip_points_json TEXT NOT NULL,      -- values at which a decision flipped
  decision_stable INTEGER NOT NULL CHECK (decision_stable IN (0,1)),
  scenario_json TEXT NOT NULL,         -- {profile, seed, days, vault_fixture}
  sim_report_hash TEXT NOT NULL,       -- SweepReport content hash (repro)
  produced_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
