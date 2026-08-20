---
title: "golden_path_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite golden_path_runs"
  - "table golden_path_runs"
schema_head: 156
table_name: "golden_path_runs"
table_role: "workflow"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "082_golden_path_runs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/082_golden_path_runs.sql"
  - "src/learnloop/curriculum/golden_path_run.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_assessment.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/curriculum/golden_path_restoration.py"
  - "src/learnloop/curriculum/pattern_ladder.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `golden_path_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for golden path so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learner_id`, `goal_id`, `commitment_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/082_golden_path_runs.sql`.
- **Schema touched by:** `082_golden_path_runs.sql`, `083_diagnostic_pack_and_triage.sql`, `087_golden_path_artifacts.sql`, `101_dual_authority_and_kinship_dedup.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | yes | — | — | Stored value |
| `learner_id` | `TEXT` | yes | `'local'` | — | Application-validated soft reference |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitments\|commitments.id]] | Stored value |
| `commitment_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/commitment_versions\|commitment_versions.id]] | Stored value |
| `source_rev` | `TEXT` | yes | — | — | Stored value |
| `unit_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `blueprint_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/task_blueprint_versions\|task_blueprint_versions.id]] | Stored value |
| `goal_contract_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/goal_contract_versions\|goal_contract_versions.id]] | Stored value |
| `depth_policy_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_policy_versions\|depth_policy_versions.id]] | Stored value |
| `depth_envelope_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_envelope_versions\|depth_envelope_versions.id]] | Stored value |
| `initial_milestone` | `TEXT` | yes | — | — | Stored value |
| `reserved_reservation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `reserved_surface_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `reserved_support_hash` | `TEXT` | no | — | — | Stored value |
| `mode` | `TEXT` | yes | `'certifying'` | — | Stored value |
| `orchestration_policy_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `decision_param_manifest_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `visible_caps_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `current_state` | `TEXT` | yes | `'draft'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `depth_envelope_version_id` → [[Reference/Database/Tables/depth_envelope_versions|`depth_envelope_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `depth_policy_version_id` → [[Reference/Database/Tables/depth_policy_versions|`depth_policy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `goal_contract_version_id` → [[Reference/Database/Tables/goal_contract_versions|`goal_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `blueprint_version_id` → [[Reference/Database/Tables/task_blueprint_versions|`task_blueprint_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_version_id` → [[Reference/Database/Tables/commitment_versions|`commitment_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_id` → [[Reference/Database/Tables/commitments|`commitments.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gpr_state` on `current_state`.
- `idx_gpr_goal` on `goal_id`.
- `idx_gpr_commitment` on `commitment_id`.
- `sqlite_autoindex_golden_path_runs_2` on `receipt_key` (unique).
- `sqlite_autoindex_golden_path_runs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_golden_path_run_event()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.golden_path_run()`
- `Repository.golden_path_run_by_receipt()`
- `Repository.golden_path_run_for_goal()`
- `Repository.golden_path_runs_all()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_assessment.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/curriculum/golden_path_restoration.py`
- `src/learnloop/curriculum/golden_path_run.py`
- `src/learnloop/curriculum/pattern_ladder.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/scheduling/controller_cutover.py`
- `src/learnloop_sidecar/handlers/golden_path.py`
- `src/learnloop_sidecar/handlers/ladder.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_golden_path_assessment.py`
- `tests/test_golden_path_confirm.py`
- `tests/test_golden_path_run.py`
- `tests/test_p2_acceptance.py`
- `tests/test_diagnostic_pack.py`
- `tests/test_golden_path_fixture.py`

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
CREATE TABLE golden_path_runs (
  id TEXT PRIMARY KEY,
  receipt_key TEXT NOT NULL,
  learner_id TEXT NOT NULL DEFAULT 'local',
  goal_id TEXT NOT NULL,
  commitment_id TEXT NOT NULL REFERENCES commitments(id),
  commitment_version_id TEXT NOT NULL REFERENCES commitment_versions(id),
  source_rev TEXT NOT NULL,
  unit_id TEXT NOT NULL,
  blueprint_version_id TEXT NOT NULL REFERENCES task_blueprint_versions(id),
  goal_contract_version_id TEXT NOT NULL REFERENCES goal_contract_versions(id),
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  initial_milestone TEXT NOT NULL,
  -- Reserved fresh held-out assessment (§8.1). Bare TEXT: reservation/surface rows
  -- live in the P0 activity substrate; the pin is the confirmed contract support.
  reserved_reservation_id TEXT,
  reserved_surface_id TEXT,
  reserved_support_hash TEXT,
  -- `certifying` requires entry-gate items 7-8 at confirmation; otherwise the run
  -- is minted `practice_only` and makes no terminal claim (§1.1, A.3.4).
  mode TEXT NOT NULL DEFAULT 'certifying'
    CHECK (mode IN ('certifying', 'practice_only')),
  orchestration_policy_json TEXT,
  decision_param_manifest_json TEXT,
  visible_caps_json TEXT,
  -- Denormalized cache of the projected head state; rebuildable from events.
  current_state TEXT NOT NULL DEFAULT 'draft'
    CHECK (current_state IN (
      'draft', 'ready', 'measuring', 'triaging', 'instructing', 'completing',
      'practicing', 'integrating', 'awaiting_delayed_check', 'ready_to_assess',
      'assessing', 'restoring', 'deepening', 'maintaining', 'complete', 'paused',
      'practice_only', 'needs_review', 'abandoned')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(receipt_key)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
