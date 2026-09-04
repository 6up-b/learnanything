---
title: "probe_item_calibrations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_item_calibrations"
  - "table probe_item_calibrations"
schema_head: 157
table_name: "probe_item_calibrations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "030_probe_pilot_and_policy.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/030_probe_pilot_and_policy.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probe_families.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_item_calibrations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe item calibration a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `probe_family_template_id`, `probe_family_template_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Probe/EIG redesign Checkpoints 4 and 5 (spec_probe_eig_redesign.md): empirical pilot, hierarchical item calibration, regrade agreement, family lifecycle audit trail, and contextual question-event telemetry. §9.7: item-instance residual layer under the family-version posterior. Generated instances inherit the family posterior; item-specific estimates shrink strongly toward it until sufficient real evidence exists. Synthetic and real evidence stay separate rows, exactly like the family level.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/030_probe_pilot_and_policy.sql`.
- **Schema touched by:** `030_probe_pilot_and_policy.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_version` | `INTEGER` | yes | — | — | Stored value |
| `grader_version` | `TEXT` | no | — | — | Stored value |
| `evidence_source` | `TEXT` | yes | — | — | Stored value |
| `parameter_posterior_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `sample_size` | `INTEGER` | yes | `0` | — | Stored value |
| `effective_sample_size` | `REAL` | no | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_item_calibrations_scope` on `practice_item_id`, `probe_family_template_id`, `probe_family_template_version`, `evidence_source` (unique).
- `sqlite_autoindex_probe_item_calibrations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.probe_item_calibration()`
- `Repository.upsert_probe_item_calibration()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/probe_families.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

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
CREATE TABLE probe_item_calibrations (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  probe_family_template_id TEXT NOT NULL,
  probe_family_template_version INTEGER NOT NULL,
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
