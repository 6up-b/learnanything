---
title: "activity_surface_authoring"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_surface_authoring"
  - "table activity_surface_authoring"
schema_head: 156
table_name: "activity_surface_authoring"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "077_familiarity_namespace.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/077_familiarity_namespace.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/surface_mint.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_surface_authoring`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity surface authoring a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `surface_id`, `anchor_surface_id`, `candidate_batch_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/077_familiarity_namespace.sql`.
- **Schema touched by:** `077_familiarity_namespace.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `surface_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `surface_policy` | `TEXT` | no | — | — | Stored value |
| `generator_provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `anchor_surface_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `candidate_batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `seed` | `TEXT` | no | — | — | Stored value |
| `angle_coords_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `task_features_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `gate_decision_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `reviewer` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | no | — | — | Stored value |
| `pinned_by_learner` | `INTEGER` | yes | `0` | — | Stored value |
| `authorship_provenance_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `rotation_eligible` | `INTEGER` | yes | `0` | — | Stored value |
| `cache_state` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `anchor_surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_asa_anchor` on `anchor_surface_id`.
- `sqlite_autoindex_activity_surface_authoring_1` on `surface_id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_surface_authoring()`
- `Repository.upsert_activity_surface_authoring()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/surface_mint.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_surface_mint.py`

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
CREATE TABLE activity_surface_authoring (
  surface_id TEXT PRIMARY KEY REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  surface_policy TEXT CHECK (surface_policy IS NULL OR surface_policy IN ('fixed', 'rotating')),
  generator_provenance_json TEXT,
  anchor_surface_id TEXT REFERENCES activity_surfaces(id),
  candidate_batch_id TEXT,
  seed TEXT,
  angle_coords_json TEXT,
  task_features_json TEXT,
  gate_decision_json TEXT,
  reviewer TEXT,
  status TEXT,
  -- A learner-authored surface is PINNED: it stays exactly as written until
  -- edited/retired (§3.9); sibling cards may provide transfer checks.
  pinned_by_learner INTEGER NOT NULL DEFAULT 0 CHECK (pinned_by_learner IN (0, 1)),
  authorship_provenance_json TEXT,
  rotation_eligible INTEGER NOT NULL DEFAULT 0 CHECK (rotation_eligible IN (0, 1)),
  cache_state TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
