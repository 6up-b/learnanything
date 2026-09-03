---
title: "lo_probe_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite lo_probe_state"
  - "table lo_probe_state"
schema_head: 157
table_name: "lo_probe_state"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/learner-state"
---

# `lo_probe_state`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Maintains the decision-facing current projection for lo probe so learner-facing mastery and capability decisions use a reproducible evidence projection. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `learning_object_id`, `probe_phase_id`, `hypothesis_set_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `028_probe_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `learning_object_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `probe_phase_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_attempts_completed` | `INTEGER` | yes | `0` | — | Stored value |
| `probe_attempts_target` | `INTEGER` | yes | `3` | — | Stored value |
| `families_converged_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `entered_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completion_reason` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_lo_probe_state_1` on `learning_object_id` (unique).

## Who calls it

### Repository access surface

- `Repository.find_record()`
- `Repository.probe_state()`
- `Repository.probe_states()`
- `Repository.upsert_probe_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop/substrate/state_sync.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_contract_commissioning.py`
- `tests/test_irt_end_to_end.py`
- `tests/test_probe_attempt_updates.py`
- `tests/test_probe_belief_posterior.py`
- `tests/test_probe_migration.py`
- `tests/test_state_sync.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_practice_leakage.py`
- `tests/test_probe_entry.py`
- `tests/test_self_attributed_misconceptions.py`
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
CREATE TABLE lo_probe_state (
  learning_object_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'complete', 'skipped_by_claim')),
  probe_phase_id TEXT,
  hypothesis_set_id TEXT,
  probe_attempts_completed INTEGER NOT NULL DEFAULT 0 CHECK (probe_attempts_completed >= 0),
  probe_attempts_target INTEGER NOT NULL DEFAULT 3 CHECK (probe_attempts_target >= 0),
  families_converged_json TEXT,
  entered_at TEXT,
  completed_at TEXT,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
, completion_reason TEXT);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
