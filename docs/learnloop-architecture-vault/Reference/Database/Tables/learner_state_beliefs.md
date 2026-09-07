---
title: "learner_state_beliefs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite learner_state_beliefs"
  - "table learner_state_beliefs"
schema_head: 157
table_name: "learner_state_beliefs"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/diagnosis/probes.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/learner-state"
---

# `learner_state_beliefs`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Gives learner state belief a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `scope_id`, `scope_type`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `subject` | `TEXT` | no | — | — | Stored value |
| `scope_type` | `TEXT` | yes | — | — | Stored value |
| `scope_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `belief_key` | `TEXT` | yes | — | — | Stored value |
| `mean` | `REAL` | yes | — | — | Stored value |
| `variance` | `REAL` | yes | — | — | Stored value |
| `evidence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `last_surprise` | `REAL` | no | — | — | Stored value |
| `last_evidence_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `stale_after_days` | `INTEGER` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_learner_state_beliefs_scope` on `subject`, `scope_type`, `scope_id`.
- `idx_learner_state_beliefs_unique` on `scope_type`, `scope_id`, `belief_key` (unique).
- `sqlite_autoindex_learner_state_beliefs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.find_record()`
- `Repository.state_beliefs()`
- `Repository.upsert_state_belief()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_probe_belief_posterior.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
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
CREATE TABLE learner_state_beliefs (
  id TEXT PRIMARY KEY,
  subject TEXT,
  scope_type TEXT NOT NULL CHECK (scope_type IN ('error_type', 'misconception')),
  scope_id TEXT NOT NULL,
  belief_key TEXT NOT NULL,
  mean REAL NOT NULL,
  variance REAL NOT NULL CHECK (variance >= 0.0),
  evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  last_surprise REAL,
  last_evidence_at TEXT,
  stale_after_days INTEGER,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
