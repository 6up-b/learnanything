---
title: "causal_cold_outcomes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_cold_outcomes"
  - "table causal_cold_outcomes"
schema_head: 156
table_name: "causal_cold_outcomes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "145_causal_cold_outcomes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/145_causal_cold_outcomes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
  - "src/learnloop/diagnosis/guided_redo.py"
  - "src/learnloop_sidecar/handlers/serializers.py"
  - "src/learnloop_sidecar/handlers/sessions.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_cold_outcomes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the measured outcome and lineage for causal cold so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `followup_task_id`, `remediation_episode_id`, `source_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/145_causal_cold_outcomes.sql`.
- **Schema touched by:** `145_causal_cold_outcomes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `outcome` | `TEXT` | yes | — | — | Stored value |
| `followup_task_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `case_kind` | `TEXT` | no | — | — | Stored value |
| `case_ref` | `TEXT` | no | — | — | Stored value |
| `source_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `cold_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `cold_verification_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `servable_opportunity` | `INTEGER` | yes | — | — | Stored value |
| `duration_state` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `store_version` | `TEXT` | yes | — | — | Stored value |
| `scheduled_not_before` | `TEXT` | no | — | — | Stored value |
| `scheduled_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_cold_outcomes_episode` on `remediation_episode_id`, `created_at`, `id`.
- `idx_causal_cold_outcomes_outcome` on `outcome`, `created_at`, `id`.
- `uq_causal_cold_outcomes_task` on `followup_task_id` (unique).
- `sqlite_autoindex_causal_cold_outcomes_1` on `id` (unique).

Database triggers:

- `causal_cold_outcomes_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_cold_outcomes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_cold_outcome()`
- `Repository.causal_cold_outcome_for_task()`
- `Repository.causal_cold_outcomes()`
- `Repository.expired_cold_retry_tasks_without_outcome()`
- `Repository.insert_causal_cold_outcome()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/sessions.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/causal_selection_audit.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_cold_outcomes.py`
- `tests/test_guided_redo.py`
- `tests/test_coldness_receipt.py`

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
CREATE TABLE causal_cold_outcomes (
  -- Content hash over (task, episode, source attempt, cold attempt, outcome):
  -- replaying the same terminal event is one row, so recording may run inside
  -- `apply_attempt` and per-attempt sweeps without double-counting.
  id TEXT PRIMARY KEY,

  outcome TEXT NOT NULL CHECK (outcome IN (
    'cold_success',
    'cold_failure',
    'right_censored_expired',
    'learner_declined',
    'unmeasurable_no_held_out_surface',
    'unmeasurable_unservable_surface',
    'same_surface',
    'contaminated_or_assisted',
    'chronology_invalid',
    'missing_chain'
  )),

  -- NULL exactly for schedule-time refusals: "no independent surface existed,
  -- so no task was ever created" is itself a disposition.
  followup_task_id TEXT,
  remediation_episode_id TEXT,
  case_kind TEXT,
  case_ref TEXT,
  source_attempt_id TEXT,
  cold_attempt_id TEXT,
  repair_class_id TEXT,
  hypothesis_ids_json TEXT NOT NULL DEFAULT '[]',

  -- Set exactly when the disposition is a measured verification; the paired
  -- row in `causal_cold_verifications` stays the authority on the three
  -- support channels.
  cold_verification_id TEXT,

  -- §4.3: was there a genuine independent serving opportunity? Gates
  -- right-censoring below.
  servable_opportunity INTEGER NOT NULL CHECK (servable_opportunity IN (0, 1)),

  -- Duration availability is orthogonal to the outcome (spec §4.3 lists
  -- `missing_duration` as a state; here it is a flag so `cold_failure with
  -- missing duration` is representable without a second row). NULL when there
  -- is no cold attempt to time.
  duration_state TEXT CHECK (
    duration_state IS NULL OR duration_state IN ('captured', 'missing')
  ),

  detail_json TEXT NOT NULL,
  store_version TEXT NOT NULL,
  scheduled_not_before TEXT,
  scheduled_expires_at TEXT,
  created_at TEXT NOT NULL,

  -- Measured outcomes carry their verification; nothing else may.
  CHECK (
    (outcome IN ('cold_success', 'cold_failure'))
    = (cold_verification_id IS NOT NULL)
  ),
  -- Only a genuinely-servable opportunity right-censors (spec §4.3).
  CHECK (outcome != 'right_censored_expired' OR servable_opportunity = 1),
  -- Consume-time dispositions are about a concrete attempt.
  CHECK (
    outcome NOT IN (
      'cold_success', 'cold_failure', 'same_surface',
      'contaminated_or_assisted', 'chronology_invalid'
    )
    OR cold_attempt_id IS NOT NULL
  )
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
