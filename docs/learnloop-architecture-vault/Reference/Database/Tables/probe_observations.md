---
title: "probe_observations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_observations"
  - "table probe_observations"
schema_head: 156
table_name: "probe_observations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
  - "src/learnloop/diagnosis/probe_audit.py"
  - "src/learnloop/diagnosis/probe_blocks.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_observations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records observations used to evaluate probe so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `entropy_before`, `entropy_after`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.1: one observation per accepted diagnostic attempt (unique on attempt_id).

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`, `031_block_end_and_longform.sql`, `071_probe_robust_cutover.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `posterior_before_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `posterior_after_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `entropy_before` | `REAL` | yes | — | — | Stored value |
| `entropy_after` | `REAL` | yes | — | — | Stored value |
| `realized_information_gain` | `REAL` | yes | — | — | Stored value |
| `independent_evidence_discount` | `REAL` | no | — | — | Stored value |
| `contamination_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `grader_channel_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `updates_belief` | `INTEGER` | yes | `1` | — | Stored value |
| `eligible_for_completion` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_probe_observations_attempt` on `attempt_id` (unique).
- `sqlite_autoindex_probe_observations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_probe_observation()`
- `Repository.probe_observation_for_attempt()`
- `Repository.probe_observations_for_episode()`
- `Repository.qualifying_probe_observation_count()`
- `Repository.qualifying_probe_observation_count_for_session()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/calibration_sessions.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`
- `src/learnloop/diagnosis/probe_audit.py`
- `src/learnloop/diagnosis/probe_blocks.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_probe_audit.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_characterization_probe_regrade.py`
- `tests/test_characterization_probe_replay.py`
- `tests/test_characterization_probe_submission.py`
- `tests/test_probe_attempt_updates.py`
- `tests/test_probe_dialogue.py`
- `tests/test_probe_episodes.py`
- `tests/test_probe_longform_families.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_probe_policy.py`
- `tests/test_probe_robust_cutover.py`

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
CREATE TABLE probe_observations (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id),
  posterior_before_json TEXT NOT NULL,
  posterior_after_json TEXT NOT NULL,
  entropy_before REAL NOT NULL,
  entropy_after REAL NOT NULL,
  realized_information_gain REAL NOT NULL,
  independent_evidence_discount REAL,
  contamination_json TEXT,
  grader_channel_json TEXT,
  updates_belief INTEGER NOT NULL DEFAULT 1 CHECK (updates_belief IN (0, 1)),
  eligible_for_completion INTEGER NOT NULL DEFAULT 0 CHECK (eligible_for_completion IN (0, 1)),
  created_at TEXT NOT NULL
, features_json TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
