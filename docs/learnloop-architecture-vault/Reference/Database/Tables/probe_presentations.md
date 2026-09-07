---
title: "probe_presentations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_presentations"
  - "table probe_presentations"
schema_head: 157
table_name: "probe_presentations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
  - "src/learnloop/diagnosis/probe_audit.py"
  - "src/learnloop/diagnosis/probe_blocks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_presentations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe presentation a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `probe_episode_id`, `practice_item_id`, `scheduler_candidate_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.1: durable committed assignment between selection and observation.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`, `029_probe_selection_and_calibration.sql`, `071_probe_robust_cutover.sql`, `123_causal_prior_basis.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `probe_episode_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/probe_episodes\|probe_episodes.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `state_segment_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_family_template_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_family_template_version` | `INTEGER` | no | — | — | Stored value |
| `instrument_card_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `instrument_card_version` | `INTEGER` | no | — | — | Stored value |
| `instrument_card_snapshot_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `target_hypothesis_pairs_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `target_facets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `posterior_at_selection_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `entropy_at_selection` | `REAL` | no | — | — | Stored value |
| `expected_information_gain` | `REAL` | no | — | — | Stored value |
| `selection_policy_version` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `end_reason` | `TEXT` | no | — | — | Stored value |
| `served_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `submitted_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `ended_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `selection_components_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `probe_episode_id` → [[Reference/Database/Tables/probe_episodes|`probe_episodes.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_probe_presentations_item` on `practice_item_id`, `created_at`.
- `idx_probe_presentations_episode` on `probe_episode_id`, `created_at`.
- `sqlite_autoindex_probe_presentations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_probe_presentation_row()`
- `Repository.active_probe_presentation()`
- `Repository.active_probe_presentation_for_session()`
- `Repository.consume_probe_presentation()`
- `Repository.end_probe_presentation()`
- `Repository.list_all_probe_presentations()`
- `Repository.mark_probe_presentation_served()`
- `Repository.probe_observations_for_episode()`
- `Repository.probe_presentation()`
- `Repository.probe_presentations_for_episode()`
- `Repository.record_scheduler_slate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/calibration_sessions.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`
- `src/learnloop/diagnosis/probe_audit.py`
- `src/learnloop/diagnosis/probe_blocks.py`
- `src/learnloop/diagnosis/probe_dialogue.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop/substrate/compat/activity_backfill.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`
- `src/learnloop_sidecar/handlers/practice.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_grade_resolution_pipeline.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_probe_audit.py`
- `tests/test_probe_dialogue.py`
- `tests/test_probe_episodes.py`
- `tests/test_sidecar_contract.py`

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
CREATE TABLE probe_presentations (
  id TEXT PRIMARY KEY,
  probe_episode_id TEXT NOT NULL REFERENCES probe_episodes(id),
  practice_item_id TEXT NOT NULL,
  scheduler_candidate_id TEXT,
  state_segment_id TEXT NOT NULL,
  probe_family_template_id TEXT,
  probe_family_template_version INTEGER,
  instrument_card_id TEXT,
  instrument_card_version INTEGER,
  instrument_card_snapshot_json TEXT,
  target_hypothesis_pairs_json TEXT,
  target_facets_json TEXT,
  posterior_at_selection_json TEXT,
  entropy_at_selection REAL,
  expected_information_gain REAL,
  selection_policy_version TEXT,
  status TEXT NOT NULL CHECK (status IN ('selected', 'served', 'submitted', 'ended')),
  end_reason TEXT CHECK (end_reason IS NULL OR end_reason IN ('expired', 'abandoned', 'invalidated')),
  served_at TEXT,
  submitted_at TEXT,
  expires_at TEXT,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, selection_components_json TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
