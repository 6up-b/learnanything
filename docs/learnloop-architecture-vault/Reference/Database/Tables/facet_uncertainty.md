---
title: "facet_uncertainty"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite facet_uncertainty"
  - "table facet_uncertainty"
schema_head: 156
table_name: "facet_uncertainty"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "learner-state"
introduced_in: "012_facet_diagnostic_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/012_facet_diagnostic_state.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/learner/facet_diagnostics.py"
  - "src/learnloop/tutor/tutor_qa.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/learner-state"
---

# `facet_uncertainty`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Gives facet uncertainty a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `learning_object_id`, `facet_id`, `opened_by_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/012_facet_diagnostic_state.sql`.
- **Schema touched by:** `012_facet_diagnostic_state.sql`, `037_canonical_facet_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `hypothesis_marginal` | `TEXT` | yes | — | — | Stored value |
| `uncertainty` | `REAL` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `opened_by_attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `opened_reason` | `TEXT` | yes | — | — | Stored value |
| `last_evidence_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `opened_by_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_facet_uncertainty_lo_status` on `learning_object_id`, `status`, `uncertainty`.
- `sqlite_autoindex_facet_uncertainty_2` on `learning_object_id`, `facet_id` (unique).
- `sqlite_autoindex_facet_uncertainty_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._guard_legacy_facet_write()`
- `Repository._upsert_facet_uncertainty_state()`
- `Repository.facet_uncertainty_state()`
- `Repository.facet_uncertainty_states()`
- `Repository.find_record()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/learner/facet_state_reader.py`
- `src/learnloop/substrate/replay.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_item_parameters.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Compatibility retirement requires production-vault telemetry and an explicit owner decision; code detachment and schema changes are separate gates.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE facet_uncertainty (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  facet_id TEXT NOT NULL,
  hypothesis_marginal TEXT NOT NULL,
  uncertainty REAL NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('open', 'resolving', 'resolved')),
  opened_by_attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  opened_reason TEXT NOT NULL CHECK (
    opened_reason IN ('low_facet_outcome', 'hedged_confidence', 'repeated_facet_failure')
  ),
  last_evidence_at TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (learning_object_id, facet_id)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
