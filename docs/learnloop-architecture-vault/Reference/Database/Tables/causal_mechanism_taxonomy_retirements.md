---
title: "causal_mechanism_taxonomy_retirements"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_mechanism_taxonomy_retirements"
  - "table causal_mechanism_taxonomy_retirements"
schema_head: 157
table_name: "causal_mechanism_taxonomy_retirements"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "133_causal_mechanism_repair_key.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/133_causal_mechanism_repair_key.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_mechanism_taxonomy_retirements`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives causal mechanism taxonomy retirement a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `taxonomy_version_id`, `reason`, `retired_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> RETIRING THE WRONG-KEY TAXONOMIES.  Migration 119 makes taxonomy versions and their assignments append-only, so the assignments minted under `exact_operation_v1` cannot be rewritten and must not be deleted: receipts pin a taxonomy version id, and replaying one has to resolve the taxonomy that actually labelled it.  Retirement is therefore a sibling append-only fact rather than a status edit: pinned reads keep working, and `latest_active_causal_mechanism_taxonomy` -- the only path by which a NEW receipt acquires a taxonomy -- skips retired versions.  Until a fresh `learnloop build-causal-taxonomy --activate` runs, new receipts carry no taxonomy version, which is the honest state: no active taxonomy exists.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/133_causal_mechanism_repair_key.sql`.
- **Schema touched by:** `133_causal_mechanism_repair_key.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `taxonomy_version_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/causal_mechanism_taxonomy_versions\|causal_mechanism_taxonomy_versions.id]] | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `retired_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `taxonomy_version_id` → [[Reference/Database/Tables/causal_mechanism_taxonomy_versions|`causal_mechanism_taxonomy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_causal_mechanism_taxonomy_retirements_1` on `taxonomy_version_id` (unique).

Database triggers:

- `causal_mechanism_taxonomy_retirements_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_mechanism_taxonomy_retirements_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.latest_active_causal_mechanism_taxonomy()`
- `Repository.retire_causal_mechanism_taxonomy_version()`
- `Repository.retired_causal_mechanism_taxonomy_versions()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`

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
CREATE TABLE causal_mechanism_taxonomy_retirements (
  taxonomy_version_id TEXT PRIMARY KEY
    REFERENCES causal_mechanism_taxonomy_versions(id),
  reason TEXT NOT NULL,
  retired_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
