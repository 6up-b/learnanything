---
title: "contrast_pair_servings"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite contrast_pair_servings"
  - "table contrast_pair_servings"
schema_head: 157
table_name: "contrast_pair_servings"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "143_instrument_classes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/143_instrument_classes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/contrast_pairs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `contrast_pair_servings`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives contrast pair serving a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `practice_item_id`, `counterpart_item_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/143_instrument_classes.sql`.
- **Schema touched by:** `143_instrument_classes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `pair_key` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `serve_position` | `INTEGER` | yes | — | — | Stored value |
| `counterpart_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `randomization_seed` | `TEXT` | yes | — | — | Stored value |
| `randomization_value` | `REAL` | yes | — | — | Stored value |
| `separated` | `INTEGER` | yes | — | — | Stored value |
| `adjacency_basis` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_contrast_pair_servings_pair` on `pair_key`, `created_at`.
- `sqlite_autoindex_contrast_pair_servings_2` on `practice_item_id`, `session_id` (unique).
- `sqlite_autoindex_contrast_pair_servings_1` on `id` (unique).

Database triggers:

- `contrast_pair_servings_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.contrast_pair_serving_rows()`
- `Repository.insert_contrast_pair_serving()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/contrast_pairs.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_contrast_pairs.py`

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
CREATE TABLE contrast_pair_servings (
  id TEXT PRIMARY KEY,
  -- The pair identity: `contrast_of` resolves both members to one key (the
  -- lexicographically smaller item id), so the two rows of one pair join.
  pair_key TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  -- 0 = offered first in this session's queue, 1 = offered second.  An integer
  -- rather than a boolean `served_first`, so a pair that somehow acquires a third
  -- member is representable as data instead of silently mis-recorded.
  serve_position INTEGER NOT NULL CHECK (serve_position >= 0),
  -- The other member, so a single row is readable without a self-join.
  counterpart_item_id TEXT NOT NULL,
  session_id TEXT,
  -- The deterministic seed the coin flip was drawn from, and the flip's result.
  -- Stored together so an auditor can both recompute the draw and count the
  -- realized balance across sessions -- the two different ways this can fail.
  randomization_seed TEXT NOT NULL,
  randomization_value REAL NOT NULL CHECK (
    randomization_value >= 0.0 AND randomization_value <= 1.0
  ),
  -- Whether the two members were separated in the queue rather than served
  -- adjacent.  §3.A4 forbids adjacency "unless the surfaces differ enough that
  -- the manipulation is not salient": a visible contrast measures "spots the
  -- manipulation", a facet nobody has.  Recorded rather than assumed, because the
  -- separation is a scheduling outcome and a queue too short to separate them is
  -- a real state.
  separated INTEGER NOT NULL CHECK (separated IN (0, 1)),
  -- Why adjacency was permitted or could not be avoided.  Closed vocabulary with
  -- an explicit abstention arm, per the standing "no new enum without an
  -- abstention arm" rule.
  adjacency_basis TEXT NOT NULL CHECK (adjacency_basis IN (
    'separated_by_interleaving',
    'surfaces_differ_sufficiently',
    'queue_too_short_to_separate',
    'unknown'
  )),
  created_at TEXT NOT NULL,
  -- One serving record per (item, session).  Re-planning the same session's
  -- queue -- which `build_due_queue` does on every call -- must not multiply the
  -- record, and the first decision is the one the learner saw.
  UNIQUE(practice_item_id, session_id)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
