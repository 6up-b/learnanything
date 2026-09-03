---
title: "activity_card_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_card_state"
  - "table activity_card_state"
schema_head: 157
table_name: "activity_card_state"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "075_card_lineage_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/075_card_lineage_state.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/card_lineage.py"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
  - "src/learnloop/substrate/shadow_rebuild.py"
  - "src/learnloop/curriculum/depth_transition.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_card_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores authoritative scheduling state for the newer card-lineage substrate, including its co-located review stream. It supplies replay-stable input rather than a disposable cache. Rows bind `learner_id`, `card_lineage_id`, `lapse_episode_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/075_card_lineage_state.sql`.
- **Schema touched by:** `075_card_lineage_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learner_id` | `TEXT` | yes | `'local'` | — | Application-validated soft reference |
| `card_lineage_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/card_lineages\|card_lineages.id]] | Stored value |
| `scheduler_algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `model_label` | `TEXT` | yes | — | — | Stored value |
| `difficulty` | `REAL` | no | — | — | Stored value |
| `stability` | `REAL` | no | — | — | Stored value |
| `retrievability` | `REAL` | no | — | — | Stored value |
| `due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `last_eligible_review_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `lapse_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `active` | `INTEGER` | yes | `1` | — | Stored value |
| `projection_head_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `card_lineage_id` → [[Reference/Database/Tables/card_lineages|`card_lineages.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_acs_lineage` on `card_lineage_id`.
- `sqlite_autoindex_activity_card_state_2` on `learner_id`, `card_lineage_id`, `scheduler_algorithm_version` (unique).
- `sqlite_autoindex_activity_card_state_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_card_state()`
- `Repository.record_depth_transition_atomic()`
- `Repository.upsert_activity_card_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/depth_transition.py`
- `src/learnloop/substrate/card_lineage.py`
- `src/learnloop/substrate/compat/substrate_cutover.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_administration_adapters.py`
- `tests/test_canonical_projection_rollout.py`
- `tests/test_card_lineage.py`
- `tests/test_commitment_arcs.py`
- `tests/test_depth_transition.py`
- `tests/test_event_sufficiency.py`
- `tests/test_journey6.py`
- `tests/test_progression.py`
- `tests/test_substrate_cutover.py`
- `tests/test_table_roles.py`

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
CREATE TABLE activity_card_state (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL DEFAULT 'local',
  card_lineage_id TEXT NOT NULL REFERENCES card_lineages(id) ON DELETE CASCADE,
  scheduler_algorithm_version TEXT NOT NULL,
  -- FSRS is permitted only for stable literal-recall-like contracts (§3.8); other
  -- P1 cards carry a card-level projection labelled provisional_stage_v1 -- NEVER
  -- mislabelled as an FSRS retention estimate.
  model_label TEXT NOT NULL CHECK (model_label IN ('fsrs', 'provisional_stage_v1')),
  difficulty REAL,
  stability REAL,
  retrievability REAL,
  due_at TEXT,
  last_eligible_review_at TEXT,
  lapse_episode_id TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  -- Projection head (§3.8): the rebuildable summary, so a corrupted legacy cache
  -- never alters an authoritative rebuild (§9.5).
  projection_head_json TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE(learner_id, card_lineage_id, scheduler_algorithm_version)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
