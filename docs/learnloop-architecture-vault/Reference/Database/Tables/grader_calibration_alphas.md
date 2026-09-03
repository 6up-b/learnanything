---
title: "grader_calibration_alphas"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grader_calibration_alphas"
  - "table grader_calibration_alphas"
schema_head: 157
table_name: "grader_calibration_alphas"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/effective_observation.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/attempts/grader_calibration.py"
  - "src/learnloop/diagnosis/probe_robust.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grader_calibration_alphas`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grader calibration alpha a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `model_id`, `true_class`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Dirichlet alpha rows (§3.2): one per (model, true class Z), holding the alpha vector over the JOINT emission E=(G, conf_bucket). Marginalizing conf gives the reported class-confusion P(G|Z). Immutable with the model. ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `model_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/grader_calibration_models\|grader_calibration_models.id]] | Stored value |
| `true_class` | `TEXT` | yes | — | — | Stored value |
| `alpha_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `model_id` → [[Reference/Database/Tables/grader_calibration_models|`grader_calibration_models.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gca_model` on `model_id`.
- `sqlite_autoindex_grader_calibration_alphas_2` on `model_id`, `true_class` (unique).
- `sqlite_autoindex_grader_calibration_alphas_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.calibration_alphas_by_model_ids()`
- `Repository.fetch_calibration_alphas()`
- `Repository.insert_calibration_model()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/effective_observation.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/grader_calibration.py`
- `src/learnloop/diagnosis/probe_robust.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`
- `tests/test_event_sufficiency.py`
- `tests/test_observation_ledger_bulk.py`

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
CREATE TABLE grader_calibration_alphas (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL REFERENCES grader_calibration_models(id) ON DELETE CASCADE,
  true_class TEXT NOT NULL,              -- Z
  alpha_json TEXT NOT NULL,              -- {"G|conf_bucket": alpha}
  created_at TEXT NOT NULL,
  UNIQUE(model_id, true_class)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
