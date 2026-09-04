---
title: "followup_tasks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite followup_tasks"
  - "table followup_tasks"
schema_head: 157
table_name: "followup_tasks"
table_role: "workflow"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "058_remediation_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/058_remediation_episodes.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/certification_cold_probe.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop_sidecar/handlers/knowledge_map.py"
  - "src/learnloop_sidecar/handlers/sessions.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/followups.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `followup_tasks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives followup task a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_attempt_id`, `remediation_episode_id`, `selected_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/058_remediation_episodes.sql`.
- **Schema touched by:** `058_remediation_episodes.sql`, `124_causal_probe_decisions.sql`, `139_certification_cold_probes.sql`, `151_cold_measurement_opportunities.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `case_kind` | `TEXT` | yes | — | — | Stored value |
| `case_ref` | `TEXT` | yes | — | — | Stored value |
| `source_attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `remediation_episode_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/remediation_episodes\|remediation_episodes.id]] | Stored value |
| `not_before` | `TEXT` | yes | — | — | Stored value |
| `expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `status` | `TEXT` | yes | — | — | Stored value |
| `selected_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `consumed_attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `context_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `measurement_opportunity_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

Declared SQLite foreign keys:

- `consumed_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `remediation_episode_id` → [[Reference/Database/Tables/remediation_episodes|`remediation_episodes.id`]]; on delete `CASCADE`, on update `NO ACTION`.
- `source_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_followup_tasks_measurement_opportunity` on `measurement_opportunity_id`.
- `uq_followup_tasks_certification_probe` on `case_ref` (unique).
- `idx_followup_tasks_kind_lo` on `kind`, `learning_object_id`, `status`.
- `idx_followup_tasks_kind_case` on `kind`, `case_ref`.
- `idx_followup_tasks_item` on `selected_item_id`, `status`.
- `idx_followup_tasks_due` on `status`, `not_before`, `expires_at`.
- `sqlite_autoindex_followup_tasks_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_followup_task_for_item()`
- `Repository.attach_followup_task_measurement_opportunity()`
- `Repository.consume_followup_task()`
- `Repository.consumed_followup_task_for_attempt()`
- `Repository.create_followup_task()`
- `Repository.deactivate_practice_item_serving()`
- `Repository.defer_followup_task()`
- `Repository.due_followup_tasks()`
- `Repository.expire_followup_task()`
- `Repository.expired_cold_retry_tasks_without_outcome()`
- `Repository.followup_task()`
- `Repository.followup_task_for_case()`
- `Repository.followup_tasks_of_kind()`
- `Repository.open_followup_tasks_of_kind()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/sessions.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/context.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_cold_outcomes.py`
- `tests/test_coldness_receipt.py`
- `tests/test_remediation_cold_retry.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_certification_cold_probe.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_followup_diagnostic_selection.py`
- `tests/test_guided_redo.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_item_authoring.py`
- `tests/test_reveal_ledger.py`
- `tests/test_scheduler.py`

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
CREATE TABLE "followup_tasks" (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('cold_retry', 'certification_cold_probe')),
  case_kind TEXT NOT NULL CHECK (
    case_kind IN ('misconception', 'diagnosis', 'certification')
  ),
  -- For `certification` this is the certificate id (a content hash over LO +
  -- blueprint/recipe + certified cells), which is what makes "one probe per
  -- certificate, ever" a UNIQUE-indexable fact instead of a caller convention.
  case_ref TEXT NOT NULL,
  source_attempt_id TEXT REFERENCES practice_attempts(id),
  remediation_episode_id TEXT REFERENCES remediation_episodes(id) ON DELETE CASCADE,
  not_before TEXT NOT NULL,
  expires_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'served', 'consumed', 'expired')),
  selected_item_id TEXT,
  consumed_attempt_id TEXT REFERENCES practice_attempts(id),
  context_json TEXT,
  learning_object_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, measurement_opportunity_id TEXT);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
