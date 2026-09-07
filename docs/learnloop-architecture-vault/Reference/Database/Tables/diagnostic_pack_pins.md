---
title: "diagnostic_pack_pins"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite diagnostic_pack_pins"
  - "table diagnostic_pack_pins"
schema_head: 157
table_name: "diagnostic_pack_pins"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "083_diagnostic_pack_and_triage.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/083_diagnostic_pack_and_triage.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/curriculum/golden_path_run.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `diagnostic_pack_pins`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives diagnostic pack pin a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `run_id`, `pack_id`, `goal_contract_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Pack pin: at diagnostic entry the run pins exactly one reviewed pack against the goal-contract HEAD version then current (§5.2) plus the opened probe episode. One pin per run (UNIQUE) -- the pack composition never re-pins mid-run.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/083_diagnostic_pack_and_triage.sql`.
- **Schema touched by:** `083_diagnostic_pack_and_triage.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/golden_path_runs\|golden_path_runs.id]] | Stored value |
| `pack_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/diagnostic_packs\|diagnostic_packs.id]] | Stored value |
| `goal_contract_version_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `visible_cap` | `INTEGER` | yes | — | — | Stored value |
| `pinned_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `pack_id` → [[Reference/Database/Tables/diagnostic_packs|`diagnostic_packs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `run_id` → [[Reference/Database/Tables/golden_path_runs|`golden_path_runs.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_diag_pins_pack` on `pack_id`.
- `sqlite_autoindex_diagnostic_pack_pins_2` on `run_id` (unique).
- `sqlite_autoindex_diagnostic_pack_pins_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.diagnostic_pack_pin_for_run()`
- `Repository.pin_diagnostic_pack()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_run.py`
- `src/learnloop/diagnosis/diagnostic_pack.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnostic_pack.py`
- `tests/test_p2_acceptance.py`

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
CREATE TABLE diagnostic_pack_pins (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  pack_id TEXT NOT NULL REFERENCES diagnostic_packs(id),
  goal_contract_version_id TEXT NOT NULL,
  probe_episode_id TEXT,
  visible_cap INTEGER NOT NULL,
  pinned_at TEXT NOT NULL,
  UNIQUE(run_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
