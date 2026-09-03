---
title: "commitments"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite commitments"
  - "table commitments"
schema_head: 157
table_name: "commitments"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "072_commitments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/072_commitments.sql"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/curriculum/commitment_arcs.py"
  - "src/learnloop/curriculum/commitments.py"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
  - "src/learnloop/curriculum/depth_rungs.py"
  - "src/learnloop/curriculum/depth_transition.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/curriculum/golden_path_restoration.py"
  - "src/learnloop/content/authoring/rung_variants.py"
  - "src/learnloop/reader/reader_authoring.py"
  - "src/learnloop/reader/reader_capture.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `commitments`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives commitment a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `learner_id`, `created_action`, `idempotency_key`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/072_commitments.sql`.
- **Schema touched by:** `072_commitments.sql`, `074_activity_contract_extensions.sql`, `079_progression_and_lapse.sql`, `080_mint_fencing_and_commitment_idempotency.sql`, `082_golden_path_runs.sql`, `088_source_render_views.sql`, `095_commitment_arcs.sql`, `099_controller_ownership.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learner_id` | `TEXT` | yes | `'local'` | — | Application-validated soft reference |
| `created_action` | `TEXT` | yes | — | — | Stored value |
| `idempotency_key` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_commitments_idempotency` on `learner_id`, `created_action`, `idempotency_key` (unique).
- `idx_commitments_learner_action` on `learner_id`, `created_action`.
- `sqlite_autoindex_commitments_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.commitment()`
- `Repository.commitments_targeting()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.create_commitment()`
- `Repository.find_commitment_by_idempotency()`
- `Repository.find_commitment_candidate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/curriculum/commitments.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/reader/reader_authoring.py`
- `src/learnloop/reader/reader_capture.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/scheduling/staged_policy.py`
- `src/learnloop/scheduling/state_signals.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_commitment_arcs.py`
- `tests/test_commitments.py`
- `tests/test_constraint_engine.py`
- `tests/test_controller_ownership.py`
- `tests/test_controller_snapshot.py`
- `tests/test_cross_seam_exposure.py`
- `tests/test_depth_transition.py`
- `tests/test_dispersion.py`
- `tests/test_dual_authority_administration.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_golden_path_confirm.py`
- `tests/test_journey6.py`
- `tests/test_reader_authoring.py`
- `tests/test_reader_capture.py`
- `tests/test_reentry_short_session.py`
- `tests/test_source_deletion.py`
- `tests/test_staged_policy.py`
- `tests/test_state_signals.py`
- `tests/test_reader_dialogue.py`

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
CREATE TABLE commitments (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL DEFAULT 'local',
  created_action TEXT NOT NULL CHECK (created_action IN
    ('help_me_remember', 'test_me_later', 'select_exemplar', 'create_quest')),
  -- idempotency key (§3.1): learner + normalized target set + action + client key.
  -- NULL when the caller supplied no client key (then a matching commitment is a
  -- merge candidate, never a silent merge).
  idempotency_key TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
