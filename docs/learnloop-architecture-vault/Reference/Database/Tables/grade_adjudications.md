---
title: "grade_adjudications"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite grade_adjudications"
  - "table grade_adjudications"
schema_head: 157
table_name: "grade_adjudications"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "066_grader_channel.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/066_grader_channel.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/attempts/grade_resolution.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grade_adjudications`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grade adjudication a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `observation_id`, `administration_id`, `resulting_interpretation_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Grade adjudications (§3.3). Append-only. Appends a new interpretation and triggers projection rebuilds; never overwrites prior rows. ----------------------------------------------------------------------------

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/066_grader_channel.sql`.
- **Schema touched by:** `066_grader_channel.sql`, `126_diagnosis_adjudication.sql`, `156_projection_ledger_indexes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `observation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_observations\|activity_observations.id]] | Stored value |
| `administration_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_administrations\|activity_administrations.id]] | Stored value |
| `reviewed_raw_event_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `adjudicator_source` | `TEXT` | yes | — | — | Stored value |
| `resolved_class` | `TEXT` | no | — | — | Stored value |
| `resolved_distribution_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `rationale` | `TEXT` | no | — | — | Stored value |
| `provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `bounded_trust_weight` | `REAL` | no | — | — | Stored value |
| `resulting_interpretation_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/grade_interpretations\|grade_interpretations.id]] | Stored value |
| `superseded_adjudication_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/grade_adjudications\|grade_adjudications.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `superseded_adjudication_id` → [[Reference/Database/Tables/grade_adjudications|`grade_adjudications.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `resulting_interpretation_id` → [[Reference/Database/Tables/grade_interpretations|`grade_interpretations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `administration_id` → [[Reference/Database/Tables/activity_administrations|`activity_administrations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `observation_id` → [[Reference/Database/Tables/activity_observations|`activity_observations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gadj_observation` on `observation_id`, `created_at`, `id`.
- `idx_gadj_admin` on `administration_id`.
- `sqlite_autoindex_grade_adjudications_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_grade_adjudication()`

### Direct SQL readers

- `src/learnloop/db/stores/observation_ledger.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/grade_resolution.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`

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
CREATE TABLE grade_adjudications (
  id TEXT PRIMARY KEY,
  observation_id TEXT REFERENCES activity_observations(id),
  administration_id TEXT NOT NULL REFERENCES activity_administrations(id),
  reviewed_raw_event_ids_json TEXT NOT NULL,
  adjudicator_source TEXT NOT NULL CHECK (adjudicator_source IN
    ('human_owner','independent_expert','learner_clarification','deterministic_key')),
  resolved_class TEXT,
  resolved_distribution_json TEXT,
  rationale TEXT,
  provenance_json TEXT,
  bounded_trust_weight REAL,             -- <1 for learner_clarification (§3.3/§4.4)
  resulting_interpretation_id TEXT REFERENCES grade_interpretations(id),
  superseded_adjudication_id TEXT REFERENCES grade_adjudications(id),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
