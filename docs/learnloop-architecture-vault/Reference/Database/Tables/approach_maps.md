---
title: "approach_maps"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "20ac907c9c767c8c6df62b6c8adf7de84d56c01e"
source_commit_timestamp: "2026-10-21T11:25:06-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite approach_maps"
  - "table approach_maps"
schema_head: 214
table_name: "approach_maps"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "211_approach_maps.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/211_approach_maps.sql"
  - "src/learnloop/ai/disclosures.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/stores/approach_maps.py"
  - "src/learnloop/hints/map_builder.py"
  - "src/learnloop/hints/map_report.py"
  - "src/learnloop/hints/map_seeds.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `approach_maps`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives approach map a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `practice_item_id`, `family_id`, `supersedes_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/211_approach_maps.sql`.
- **Schema touched by:** `210_help_assists.sql`, `211_approach_maps.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_hash` | `TEXT` | yes | — | — | Stored value |
| `family_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `map_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `seeds_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `seeds_hash` | `TEXT` | yes | — | — | Stored value |
| `structure_hash` | `TEXT` | yes | — | — | Stored value |
| `validation_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `verified_goal` | `INTEGER` | yes | — | — | Stored value |
| `trigger` | `TEXT` | yes | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/approach_maps\|approach_maps.id]] | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/approach_maps|`approach_maps.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_approach_maps_family` on `family_id`, `created_at`.
- `idx_approach_maps_item` on `practice_item_id`, `version`.
- `sqlite_autoindex_approach_maps_3` on `practice_item_id`, `practice_item_hash`, `seeds_hash` (unique).
- `sqlite_autoindex_approach_maps_2` on `practice_item_id`, `version` (unique).
- `sqlite_autoindex_approach_maps_1` on `id` (unique).

Database triggers:

- `approach_maps_no_delete` — schema-enforced lifecycle or immutability constraint.
- `approach_maps_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/approach_maps.py`
- `src/learnloop/hints/report_adaptive.py`

### Direct SQL writers

- `src/learnloop/db/stores/approach_maps.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/approach_map_fakes.py`
- `tests/test_approach_map_boundaries.py`
- `tests/test_approach_map_replay.py`
- `tests/test_approach_maps.py`
- `tests/test_approach_maps_schema.py`
- `tests/test_architecture.py`
- `tests/test_help_assists_schema.py`
- `tests/test_library_asks_migration.py`

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
CREATE TABLE approach_maps (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  -- The item revision the map was built for (vault/hashes.py).
  practice_item_hash TEXT NOT NULL,
  family_id TEXT,
  -- 1, 2, ... per item, across revisions.
  version INTEGER NOT NULL CHECK (version >= 1),
  -- ApproachMapV1, as validated (code-marked leak nodes included).
  map_json TEXT NOT NULL,
  -- Which trace contract, skeletons, source spans, attempts, authored hints
  -- and family template the map was built from.
  seeds_json TEXT NOT NULL,
  -- The revision keys: every seed (seeds_hash), and the item-side seeds that
  -- practice_item_hash does not cover (structure_hash: the trace contract,
  -- the PF skeletons and the authored hints). A serve builds a map when no
  -- row matches the item's current practice_item_hash and structure_hash.
  seeds_hash TEXT NOT NULL,
  structure_hash TEXT NOT NULL,
  validation_json TEXT NOT NULL,
  -- 1 when the goal agrees with the expected answer by exact key; 0 when no
  -- exact key exists or the agreement cannot be decided (the builder's
  -- declaration, stored as unverified).
  verified_goal INTEGER NOT NULL CHECK (verified_goal IN (0, 1)),
  -- What built this version: a serve (background), an inline build (H2's
  -- hint path), the owner's CLI backfill, or a learner-route merge.
  trigger TEXT NOT NULL CHECK (trigger IN ('serve', 'inline', 'cli', 'merge')),
  model TEXT,
  prompt_version TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  supersedes_id TEXT REFERENCES approach_maps(id),
  CHECK (supersedes_id IS NULL OR supersedes_id != id),
  UNIQUE (practice_item_id, version),
  UNIQUE (practice_item_id, practice_item_hash, seeds_hash)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
