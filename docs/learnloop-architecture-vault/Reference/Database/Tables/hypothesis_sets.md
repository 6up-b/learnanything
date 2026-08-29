---
title: "hypothesis_sets"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite hypothesis_sets"
  - "table hypothesis_sets"
schema_head: 156
table_name: "hypothesis_sets"
table_role: "compat"
functionality_status: "legacy-preserved"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/probes.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/legacy-preserved"
  - "learnloop/domain/learner-state"
---

# `hypothesis_sets`

> [!warning] Legacy Preserved
> Frozen compatibility state remains readable for older vaults and is not a deletion candidate.

## Why it exists

Gives hypothesis set a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `learning_object_id`, `probe_phase_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `legacy-preserved`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `121_causal_probe_coherence.sql`, `123_causal_prior_basis.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_phase_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypotheses_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `prior_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `prior_basis` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_hypothesis_sets_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_hypothesis_sets_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.fetch_hypothesis_set()`
- `Repository.find_record()`
- `Repository.insert_hypothesis_set()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_diagnostic_selector.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
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
CREATE TABLE hypothesis_sets (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  probe_phase_id TEXT,
  hypotheses_json TEXT NOT NULL,
  prior_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
, prior_basis TEXT);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
