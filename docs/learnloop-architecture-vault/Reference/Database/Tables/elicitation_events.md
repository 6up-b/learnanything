---
title: "elicitation_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite elicitation_events"
  - "table elicitation_events"
schema_head: 157
table_name: "elicitation_events"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "operations"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop_sidecar/handlers/inspector.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/operations"
---

# `elicitation_events`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Preserves an append-only chronology of elicitation so maintenance and optional operational work remains inspectable without becoming learner-state authority. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `session_id`, `selected_practice_item_id`, `hypothesis_set_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `011_training_dataset_logging.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selected_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `policy` | `TEXT` | yes | — | — | Stored value |
| `candidate_scores_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `entropy_before` | `REAL` | no | — | — | Stored value |
| `expected_information_gain` | `REAL` | no | — | — | Stored value |
| `selected_reason` | `TEXT` | no | — | — | Stored value |
| `hypothesis_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_set_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `trigger` | `TEXT` | no | — | — | Stored value |
| `fallback_outcome` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_elicitation_events_session` on `session_id`, `selected_practice_item_id`.
- `sqlite_autoindex_elicitation_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.elicitation_events()`
- `Repository.find_record()`
- `Repository.insert_elicitation_event()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_scheduler_probe_eig.py`
- `tests/test_state_sync.py`
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
CREATE TABLE elicitation_events (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  selected_practice_item_id TEXT,
  target_scope_json TEXT,
  policy TEXT NOT NULL CHECK (policy IN ('probe_eig')),
  candidate_scores_json TEXT,
  entropy_before REAL,
  expected_information_gain REAL,
  selected_reason TEXT,
  hypothesis_set_id TEXT,
  hypothesis_set_json TEXT,
  trigger TEXT CHECK (
    trigger IS NULL OR trigger IN ('probe_phase_routine', 'probe_phase_local_pi_inadequate')
  ),
  fallback_outcome TEXT CHECK (
    fallback_outcome IS NULL OR fallback_outcome IN ('existing_pi', 'existing_pi_inadequate')
  ),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
