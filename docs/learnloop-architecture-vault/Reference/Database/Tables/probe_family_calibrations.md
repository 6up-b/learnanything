---
title: "probe_family_calibrations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_family_calibrations"
  - "table probe_family_calibrations"
schema_head: 157
table_name: "probe_family_calibrations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probe_audit.py"
  - "src/learnloop/diagnosis/probe_families.py"
  - "src/learnloop/diagnosis/probe_lifecycle.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_family_calibrations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe family calibration a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `probe_family_template_id`, `probe_family_template_version`, `generator_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §9.7: hierarchical calibration pooled at the family-version level. Synthetic gate outcomes and real learner evidence are separate rows, never merged.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `probe_family_template_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_version` | `INTEGER` | yes | — | — | Stored value |
| `generator_version` | `TEXT` | no | — | — | Stored value |
| `grader_version` | `TEXT` | no | — | — | Stored value |
| `evidence_source` | `TEXT` | yes | — | — | Stored value |
| `parameter_posterior_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `sample_size` | `INTEGER` | yes | `0` | — | Stored value |
| `effective_sample_size` | `REAL` | no | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_family_calibrations_scope` on `probe_family_template_id`, `probe_family_template_version`, `evidence_source` (unique).
- `sqlite_autoindex_probe_family_calibrations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.probe_family_calibration()`
- `Repository.probe_family_calibrations_for_family()`
- `Repository.upsert_probe_family_calibration()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/probe_audit.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/probe_families.py`
- `src/learnloop/diagnosis/probe_lifecycle.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_table_roles.py`
- `tests/test_characterization_probe_family_em.py`
- `tests/test_probe_llm_instances.py`

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
CREATE TABLE probe_family_calibrations (
  id TEXT PRIMARY KEY,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
  generator_version TEXT,
  grader_version TEXT,
  evidence_source TEXT NOT NULL CHECK (evidence_source IN ('synthetic_gate', 'real_learner', 'reviewed_human')),
  parameter_posterior_json TEXT NOT NULL,
  sample_size INTEGER NOT NULL DEFAULT 0 CHECK (sample_size >= 0),
  effective_sample_size REAL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
