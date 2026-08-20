---
title: "intervention_needs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite intervention_needs"
  - "table intervention_needs"
schema_head: 156
table_name: "intervention_needs"
table_role: "workflow"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "007_recall_coverage_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/007_recall_coverage_interventions.sql"
  - "src/learnloop/attempts/post_attempt.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `intervention_needs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues an identified supply gap for intervention so learner-facing mastery and capability decisions use a reproducible evidence projection. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `attempt_id`, `learning_object_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/007_recall_coverage_interventions.sql`.
- **Schema touched by:** `007_recall_coverage_interventions.sql`, `014_intervention_diagnostic_focus.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `desired_intent` | `TEXT` | yes | — | — | Stored value |
| `trigger_reason` | `TEXT` | yes | — | — | Stored value |
| `target_facets_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `error_types_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `priority` | `REAL` | yes | `0.5` | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `blocked_reason` | `TEXT` | yes | — | — | Stored value |
| `candidate_requirements_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `diagnostic_focus_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_intervention_needs_pending` on `status`, `learning_object_id`, `priority`, `created_at`.
- `sqlite_autoindex_intervention_needs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_intervention_need_target_facets()`
- `Repository.find_record()`
- `Repository.intervention_need()`
- `Repository.intervention_need_for_attempt()`
- `Repository.intervention_needs_for_diagnostic_proposal()`
- `Repository.pending_gap_need_for_facets()`
- `Repository.pending_intervention_needs()`
- `Repository.update_intervention_need_diagnostic_focus()`
- `Repository.update_intervention_need_status()`
- `Repository.upsert_intervention_need()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_cli_generate_practice.py`
- `tests/test_migrations.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_diagnostic_generation.py`
- `tests/test_difficulty_band_guards.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_followups.py`
- `tests/test_misconception_routing.py`
- `tests/test_persona_gate.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_question_promotions.py`
- `tests/test_question_signal.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_show.py`
- `tests/test_sidecar_contract.py`
- `tests/test_source_ingestion.py`

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
CREATE TABLE intervention_needs (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  learning_object_id TEXT NOT NULL,
  practice_item_id TEXT,
  desired_intent TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  target_facets_json TEXT NOT NULL,
  error_types_json TEXT,
  priority REAL NOT NULL DEFAULT 0.5,
  status TEXT NOT NULL CHECK (status IN ('pending', 'fulfilled', 'dismissed', 'stale')),
  blocked_reason TEXT NOT NULL,
  candidate_requirements_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, diagnostic_focus_json TEXT);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
