---
title: "grader_calibration_models"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grader_calibration_models"
  - "table grader_calibration_models"
schema_head: 157
table_name: "grader_calibration_models"
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
  - "src/learnloop/curriculum/golden_path_assessment.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grader_calibration_models`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grader calibration model a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `parent_model_id`, `outcome_schema_id`, `grading_prompt_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Grader calibration models (§3.2). IMMUTABLE. One row per model version. The identity tuple + scope + backoff chain fix the model's place in the partial-pooling lattice; the Dirichlet alpha rows (below) hold the joint mass. ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`, `070_p0_measurement_hardening.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `grader_provider` | `TEXT` | no | — | — | Stored value |
| `grader_model_revision` | `TEXT` | no | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `grader_output_schema_version` | `TEXT` | no | — | — | Stored value |
| `grader_identity_hash` | `TEXT` | no | — | — | Stored value |
| `semver` | `TEXT` | yes | — | — | Stored value |
| `parent_model_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/grader_calibration_models\|grader_calibration_models.id]] | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `scope_level` | `TEXT` | yes | — | — | Stored value |
| `outcome_schema_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/outcome_schemas\|outcome_schemas.id]] | Stored value |
| `outcome_schema_version` | `INTEGER` | no | — | — | Stored value |
| `domain` | `TEXT` | no | — | — | Stored value |
| `length_bucket` | `TEXT` | no | — | — | Stored value |
| `backoff_chain_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | — | — | Stored value |
| `count_heuristic_prior` | `INTEGER` | yes | `0` | — | Stored value |
| `count_planted_sim` | `INTEGER` | yes | `0` | — | Stored value |
| `count_exploratory_em` | `INTEGER` | yes | `0` | — | Stored value |
| `count_adjudicated_anchor` | `INTEGER` | yes | `0` | — | Stored value |
| `count_held_out_evaluation` | `INTEGER` | yes | `0` | — | Stored value |
| `prequential_log_loss` | `REAL` | no | — | — | Stored value |
| `multiclass_brier` | `REAL` | no | — | — | Stored value |
| `reliability_bins_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `sample_count` | `INTEGER` | no | — | — | Stored value |
| `eval_time_range_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `prior_concentration` | `REAL` | no | — | — | Stored value |
| `provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `evidence_manifest_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `outcome_schema_id` → [[Reference/Database/Tables/outcome_schemas|`outcome_schemas.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `parent_model_id` → [[Reference/Database/Tables/grader_calibration_models|`grader_calibration_models.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gcm_content_hash` on `content_hash` (unique).
- `idx_gcm_lookup` on `scope_level`, `grader_identity_hash`, `domain`, `length_bucket`.
- `idx_gcm_schema` on `outcome_schema_id`, `outcome_schema_version`.
- `idx_gcm_identity` on `grader_identity_hash`.
- `idx_gcm_scope` on `scope_level`.
- `sqlite_autoindex_grader_calibration_models_2` on `scope_level`, `grader_identity_hash`, `outcome_schema_id`, `outcome_schema_version`, `domain`, `length_bucket`, `semver` (unique).
- `sqlite_autoindex_grader_calibration_models_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.calibration_models_by_hashes()`
- `Repository.fetch_calibration_model()`
- `Repository.find_calibration_model_by_hash()`
- `Repository.find_calibration_models()`
- `Repository.insert_calibration_model()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/effective_observation.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/grader_calibration.py`
- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/db/repositories.py`
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
CREATE TABLE grader_calibration_models (
  id TEXT PRIMARY KEY,
  -- grader identity tuple (§3.2): provider + model/revision + grading prompt
  -- version + output schema version, decomposed AND as a canonical hash.
  grader_provider TEXT,
  grader_model_revision TEXT,
  grading_prompt_version TEXT,
  grader_output_schema_version TEXT,
  grader_identity_hash TEXT,             -- NULL at global scope
  semver TEXT NOT NULL,
  parent_model_id TEXT REFERENCES grader_calibration_models(id),
  content_hash TEXT NOT NULL,
  -- scope + ordered backoff chain (§3.2 fixed parent order):
  scope_level TEXT NOT NULL CHECK (scope_level IN
    ('global', 'grader_identity', 'outcome_schema', 'domain', 'length_bucket')),
  outcome_schema_id TEXT REFERENCES outcome_schemas(id),
  outcome_schema_version INTEGER,
  domain TEXT,
  length_bucket TEXT CHECK (length_bucket IS NULL OR length_bucket IN ('0','1-50','51-200','201+')),
  backoff_chain_json TEXT NOT NULL,      -- ordered ancestor model ids, most-general first
  status TEXT NOT NULL CHECK (status IN
    ('heuristic', 'simulation_validated', 'live_calibrated')),
  -- disjoint source counts (§3.2):
  count_heuristic_prior INTEGER NOT NULL DEFAULT 0,
  count_planted_sim INTEGER NOT NULL DEFAULT 0,
  count_exploratory_em INTEGER NOT NULL DEFAULT 0,
  count_adjudicated_anchor INTEGER NOT NULL DEFAULT 0,
  count_held_out_evaluation INTEGER NOT NULL DEFAULT 0,
  -- prequential metrics (§3.2), NULL until an evaluation manifest exists:
  prequential_log_loss REAL,
  multiclass_brier REAL,
  reliability_bins_json TEXT,
  sample_count INTEGER,
  eval_time_range_json TEXT,
  prior_concentration REAL,
  provenance_json TEXT,
  evidence_manifest_json TEXT,           -- required for live_calibrated (§3.2)
  created_at TEXT NOT NULL,
  UNIQUE(scope_level, grader_identity_hash, outcome_schema_id, outcome_schema_version,
         domain, length_bucket, semver)
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
