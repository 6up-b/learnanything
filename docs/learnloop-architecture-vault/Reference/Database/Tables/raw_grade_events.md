---
title: "raw_grade_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite raw_grade_events"
  - "table raw_grade_events"
schema_head: 157
table_name: "raw_grade_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/ai/schemas.py"
  - "src/learnloop/cli/grading.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/attempts/effective_observation.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/substrate/compat/card_outcome_replay.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `raw_grade_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of raw grade so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `administration_id`, `observation_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Raw grade events (§3.3). Append-only. One per grader pass over a response. ----------------------------------------------------------------------------

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
| `administration_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `observation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_observations\|activity_observations.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `response_ref` | `TEXT` | no | — | — | Stored value |
| `role` | `TEXT` | yes | — | — | Stored value |
| `grader_provider` | `TEXT` | no | — | — | Stored value |
| `grader_model_revision` | `TEXT` | no | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `grader_output_schema_version` | `TEXT` | no | — | — | Stored value |
| `grader_identity_hash` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `raw_output_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `criterion_evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `observed_class` | `TEXT` | yes | — | — | Stored value |
| `model_confidence` | `REAL` | no | — | — | Stored value |
| `confidence_bucket` | `TEXT` | yes | — | — | Stored value |
| `criterion_observed_classes_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `response_classifier_version` | `TEXT` | yes | — | — | Stored value |
| `criterion_classifier_version` | `TEXT` | no | — | — | Stored value |
| `context_features_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `exact_word_count` | `INTEGER` | yes | — | — | Stored value |
| `declared_length_bucket` | `TEXT` | yes | — | — | Stored value |
| `predecessor_event_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/raw_grade_events\|raw_grade_events.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `predecessor_event_id` → [[Reference/Database/Tables/raw_grade_events|`raw_grade_events.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `observation_id` → [[Reference/Database/Tables/activity_observations|`activity_observations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_rge_attempt` on `attempt_id`.
- `idx_rge_observation` on `observation_id`.
- `idx_rge_admin` on `administration_id`.
- `sqlite_autoindex_raw_grade_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_raw_grade_event()`
- `Repository.raw_grade_event()`
- `Repository.raw_grade_events_by_ids()`
- `Repository.raw_grade_events_for_observation()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/effective_observation.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/cli/grading.py`
- `src/learnloop/substrate/compat/card_outcome_replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`
- `tests/test_grading_cli.py`
- `tests/test_event_sufficiency.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_probe_robust_cutover.py`
- `tests/test_unresolved_cause_gate.py`

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
CREATE TABLE raw_grade_events (
  id TEXT PRIMARY KEY,
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  observation_id TEXT REFERENCES activity_observations(id),
  attempt_id TEXT,
  response_ref TEXT,
  role TEXT NOT NULL CHECK (role IN
    ('primary', 'recheck', 'independent_confirmation', 'human_grade')),
  grader_provider TEXT,
  grader_model_revision TEXT,
  grading_prompt_version TEXT,
  grader_output_schema_version TEXT,
  grader_identity_hash TEXT,
  agent_run_id TEXT,
  raw_output_json TEXT NOT NULL,
  criterion_evidence_json TEXT,
  observed_class TEXT NOT NULL,          -- G
  model_confidence REAL,                 -- raw numeric grader_confidence (NEVER multiplied)
  confidence_bucket TEXT NOT NULL CHECK (confidence_bucket IN
    ('unknown','low','medium','high')),
  criterion_observed_classes_json TEXT,
  response_classifier_version TEXT NOT NULL,
  criterion_classifier_version TEXT,
  context_features_json TEXT NOT NULL,
  exact_word_count INTEGER NOT NULL,
  declared_length_bucket TEXT NOT NULL CHECK (declared_length_bucket IN ('0','1-50','51-200','201+')),
  predecessor_event_id TEXT REFERENCES raw_grade_events(id),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
