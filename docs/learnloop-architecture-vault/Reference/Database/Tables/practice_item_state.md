---
title: "practice_item_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_item_state"
  - "table practice_item_state"
schema_head: 156
table_name: "practice_item_state"
table_role: "compat"
functionality_status: "active-historical-seam"
domain_family: "operations"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/content/proposals/patches.py"
  - "src/learnloop/content/synthesis/coverage_rollup.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/probe_remint.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/content/authoring/practice_generation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/compat"
  - "learnloop/status/active-historical-seam"
  - "learnloop/domain/operations"
---

# `practice_item_state`

> [!warning] Active Historical Seam
> Still read and written while activity_card_state is only a partial successor.

## Why it exists

Preserves the still-used historical practice-item scheduling seam while card state remains a partial successor. It keeps an older vault or replay contract readable while new writes use the refactored path. Rows bind `practice_item_id`, `content_hash`, `difficulty`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Compat]].

## Persistence and lifecycle contract

- **Role:** `compat` — Frozen compatibility state retained for old vaults or an incomplete replacement seam.
- **Functionality status:** `active-historical-seam`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `075_card_lineage_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `difficulty` | `REAL` | no | — | — | Stored value |
| `stability` | `REAL` | no | — | — | Stored value |
| `retrievability` | `REAL` | no | — | — | Stored value |
| `due_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `active` | `INTEGER` | yes | `1` | — | Stored value |
| `content_hash` | `TEXT` | no | — | — | Stored value |
| `last_attempt_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_state_due` on `active`, `due_at`.
- `sqlite_autoindex_practice_item_state_1` on `practice_item_id` (unique).

## Who calls it

### Repository access surface

- `Repository._upsert_practice_item_state_record()`
- `Repository.deactivate_practice_item_serving()`
- `Repository.find_record()`
- `Repository.practice_item_state()`
- `Repository.practice_item_states()`
- `Repository.record_attempt_outcome()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`
- `Repository.set_practice_item_active()`
- `Repository.upsert_practice_item_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/content/synthesis/coverage_rollup.py`
- `src/learnloop/curriculum/golden_path_compose.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/diagnostic_surface_supply.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/probe_dialogue.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probe_instance_generation.py`
- `src/learnloop/diagnosis/probe_lifecycle.py`
- `src/learnloop/diagnosis/probe_remint.py`
- `src/learnloop/diagnosis/remediation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_attempts.py`
- `tests/test_card_lineage.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_debug_advance.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_local.py`
- `tests/test_e2e_tui.py`
- `tests/test_evaluation.py`
- `tests/test_event_sufficiency.py`
- `tests/test_exam_seeding.py`
- `tests/test_hot_path_eligibility_cutover.py`
- `tests/test_item_authoring.py`
- `tests/test_measurement_corrections.py`
- `tests/test_patch_applier.py`
- `tests/test_probe_remint.py`
- `tests/test_probe_surface_mint.py`
- `tests/test_review_log.py`
- `tests/test_scheduler_requested_floor.py`

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
CREATE TABLE practice_item_state (
  practice_item_id TEXT PRIMARY KEY,
  difficulty REAL,
  stability REAL,
  retrievability REAL,
  due_at TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  content_hash TEXT,
  last_attempt_at TEXT,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Compat|compat policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
