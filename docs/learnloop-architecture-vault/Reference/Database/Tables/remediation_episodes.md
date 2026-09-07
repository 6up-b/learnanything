---
title: "remediation_episodes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite remediation_episodes"
  - "table remediation_episodes"
schema_head: 157
table_name: "remediation_episodes"
table_role: "workflow"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "058_remediation_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/058_remediation_episodes.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/remediation.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/guided_redo.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `remediation_episodes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives remediation episode a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `primed_item_id`, `cold_item_id`, `primed_attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Structured misconception repair episodes and delayed cold follow-up tasks.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/058_remediation_episodes.sql`.
- **Schema touched by:** `058_remediation_episodes.sql`, `139_certification_cold_probes.sql`, `150_remediation_delivery_exposure.sql`, `151_cold_measurement_opportunities.sql`, `152_repair_opportunity_before_selection.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `case_kind` | `TEXT` | yes | — | — | Stored value |
| `case_ref` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `passages_shown_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `primed_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cold_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `primed_attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `cold_attempt_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `cold_measurement_opportunity_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

Declared SQLite foreign keys:

- `cold_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `primed_attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_remediation_episodes_cold_measurement_opportunity` on `cold_measurement_opportunity_id`.
- `idx_remediation_episodes_created` on `created_at`, `id`.
- `idx_remediation_episodes_case` on `case_kind`, `case_ref`, `created_at`.
- `sqlite_autoindex_remediation_episodes_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.create_remediation_episode()`
- `Repository.get_or_create_open_remediation_episode()`
- `Repository.open_remediation_episode_for_case()`
- `Repository.open_remediation_episode_for_primed_item()`
- `Repository.open_remediation_episodes_for_item()`
- `Repository.remediation_episode()`
- `Repository.remediation_episodes_created_between()`
- `Repository.remediation_episodes_for_case_refs()`
- `Repository.update_remediation_episode()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/guided_redo.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop_sidecar/handlers/remediation.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_coldness_receipt.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_migrations.py`
- `tests/test_remediation_cold_retry.py`
- `tests/test_causal_cold_outcomes.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_guided_redo.py`
- `tests/test_reveal_ledger.py`
- `tests/test_sidecar_remediation_surfaces.py`

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
CREATE TABLE remediation_episodes (
  id TEXT PRIMARY KEY,
  case_kind TEXT NOT NULL CHECK (case_kind IN ('misconception', 'diagnosis')),
  case_ref TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('diagnosis', 'prescribed', 'treatment', 'cold_scheduled', 'completed', 'abandoned')),
  passages_shown_json TEXT NOT NULL DEFAULT '[]',
  primed_item_id TEXT,
  cold_item_id TEXT,
  primed_attempt_id TEXT REFERENCES practice_attempts(id),
  cold_attempt_id TEXT REFERENCES practice_attempts(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
, cold_measurement_opportunity_id TEXT);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
