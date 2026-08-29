---
title: "p2_ladder_stages"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite p2_ladder_stages"
  - "table p2_ladder_stages"
schema_head: 156
table_name: "p2_ladder_stages"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "084_pattern_ladder.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/084_pattern_ladder.sql"
  - "src/learnloop/curriculum/pattern_ladder.py"
  - "src/learnloop/db/repositories.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `p2_ladder_stages`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives p2 ladder stage a stable database identity so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `policy_id`, `stage_key`, `ordinal`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The ordered rungs of one ladder policy, each declaring the §7.2 observable entry/exit criteria, its immutable P1 pattern family + purpose, and whether it records scaffold use / requires a cold unhinted response. `ordinal` groups alternate rungs (example_study | example_comparison share an ordinal); the run climbs by ordinal. `mints_certification` is 0 on every rung.

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/084_pattern_ladder.sql`.
- **Schema touched by:** `084_pattern_ladder.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `policy_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/p2_ladder_policies\|p2_ladder_policies.id]] | Stored value |
| `stage_key` | `TEXT` | yes | — | — | Stored value |
| `ordinal` | `INTEGER` | yes | — | — | Stored value |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `run_state` | `TEXT` | yes | — | — | Stored value |
| `pattern_family` | `TEXT` | yes | — | — | Stored value |
| `entry_criteria` | `TEXT` | yes | — | — | Stored value |
| `exit_criteria` | `TEXT` | yes | — | — | Stored value |
| `mints_certification` | `INTEGER` | yes | `0` | — | Stored value |
| `requires_cold` | `INTEGER` | yes | `0` | — | Stored value |
| `records_scaffold` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `policy_id` → [[Reference/Database/Tables/p2_ladder_policies|`p2_ladder_policies.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_p2_ladder_stages_policy` on `policy_id`, `ordinal`.
- `sqlite_autoindex_p2_ladder_stages_2` on `policy_id`, `stage_key` (unique).
- `sqlite_autoindex_p2_ladder_stages_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ladder_stages_for_policy()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/pattern_ladder.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE p2_ladder_stages (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES p2_ladder_policies(id) ON DELETE CASCADE,
  stage_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('instructional', 'practice')),
  run_state TEXT NOT NULL,
  pattern_family TEXT NOT NULL,
  entry_criteria TEXT NOT NULL,
  exit_criteria TEXT NOT NULL,
  mints_certification INTEGER NOT NULL DEFAULT 0,
  requires_cold INTEGER NOT NULL DEFAULT 0,
  records_scaffold INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(policy_id, stage_key)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
