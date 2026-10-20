---
title: "item_fingerprints"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "bdb5ef8e72b8eab44fb9b3cb87ae1f82b8cd9421"
source_commit_timestamp: "2026-10-19T22:49:44-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite item_fingerprints"
  - "table item_fingerprints"
schema_head: 213
table_name: "item_fingerprints"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "174_pf_generation.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/174_pf_generation.sql"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/db/stores/pf.py"
  - "src/learnloop/ops/embedding_compare.py"
  - "src/learnloop/ops/pf_generation.py"
  - "src/learnloop/ops/pf_publish.py"
  - "src/learnloop/substrate/item_fingerprints.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_fingerprints`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item fingerprint a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `practice_item_id`, `fingerprint_version`, `value_hash`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> DERIVED: deterministic symbolic fingerprints of practice-family items, one row per namespaced key (077 namespaces; never interchangeable). Rebuilt from vault content, persisted skeletons and family generator hashes; no model call, no generator execution.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/174_pf_generation.sql`.
- **Schema touched by:** `174_pf_generation.sql`.
- **Rebuild owner:** `item_fingerprints`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `namespace` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `component` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `value_hash` | `TEXT` | yes | — | — | Stored value |
| `item_content_hash` | `TEXT` | yes | — | — | Stored value |
| `fingerprint_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_item_fingerprints_value` on `namespace`, `value_hash`.
- `sqlite_autoindex_item_fingerprints_1` on `practice_item_id`, `namespace`, `component` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/pf.py`

### Direct SQL writers

- `src/learnloop/db/stores/pf.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_item_fingerprints.py`
- `tests/test_rebuild_orchestrator.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE item_fingerprints (
  practice_item_id TEXT NOT NULL,
  namespace TEXT NOT NULL CHECK (namespace IN (
    'surface_hash', 'shared_stimulus', 'source_example', 'solution_recipe',
    'parameter_template', 'verbatim_target', 'external_artifact')),
  component TEXT NOT NULL,
  value_hash TEXT NOT NULL,
  item_content_hash TEXT NOT NULL,
  fingerprint_version TEXT NOT NULL,
  PRIMARY KEY (practice_item_id, namespace, component)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
