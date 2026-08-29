---
title: "facet_merges"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite facet_merges"
  - "table facet_merges"
schema_head: 156
table_name: "facet_merges"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "037_canonical_facet_state.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/037_canonical_facet_state.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/facet_state_reader.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
  - "src/learnloop/learner/facet_evidence_timeline.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `facet_merges`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives facet merge a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It supplies replay-stable input rather than a disposable cache. Rows bind `retired_facet_id`, `surviving_facet_id`, `proposal_item_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Pre-lock reviewed facet merges only (§3.4). Replay and projections resolve facet ids through aliases + this map; observations are never rewritten and no beta mass is ever hand-migrated. Resolution is transitive to the terminal survivor; a row that would create a cycle is rejected at write time (in the repository), so this table can always be resolved to a fixed point.

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/037_canonical_facet_state.sql`.
- **Schema touched by:** `037_canonical_facet_state.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `retired_facet_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surviving_facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `merged_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `proposal_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `rationale` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_facet_merges_1` on `retired_facet_id` (unique).

## Who calls it

### Repository access surface

- `Repository.facet_merge_map()`
- `Repository.insert_facet_merge()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/learner/facet_state_reader.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop_sidecar/handlers/facet_detail.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_measurement_rank.py`
- `tests/test_migrations.py`
- `tests/test_conjunctive_instruments.py`
- `tests/test_km2_canonical.py`

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
CREATE TABLE facet_merges (
  retired_facet_id TEXT PRIMARY KEY,
  surviving_facet_id TEXT NOT NULL,
  merged_at TEXT NOT NULL,
  proposal_item_id TEXT,
  rationale TEXT
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
