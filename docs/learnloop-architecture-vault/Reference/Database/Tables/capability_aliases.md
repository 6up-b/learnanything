---
title: "capability_aliases"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite capability_aliases"
  - "table capability_aliases"
schema_head: 157
table_name: "capability_aliases"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "073_activity_patterns_and_features.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/073_activity_patterns_and_features.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activity_patterns.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `capability_aliases`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maps legacy capability names to their canonical registry identity so old evidence remains interpretable after vocabulary changes. It supplies replay-stable input rather than a disposable cache. Rows bind `registry_version`, `legacy_value`, `canonical`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 2 (spec_p1_shared_substrate §3.3, §3.4, §3.5): the closed capability vocabulary alias registry, the immutable TaskFeature schema, and the curated ActivityPattern registry with U-035 `learning_process` routing metadata.  `learning_process` is closed-vocabulary controller-side routing metadata: it is surfaced in the "why this activity?" DTO but is categorically excluded from any evidence/projection input path (§3.5, U-035). It lives ONLY on the pattern version row; no projection selects it (enforced by test).

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/073_activity_patterns_and_features.sql`.
- **Schema touched by:** `073_activity_patterns_and_features.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `registry_version` | `INTEGER` | yes | — | — | Stored value |
| `legacy_value` | `TEXT` | yes | — | — | Stored value |
| `canonical` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_capability_aliases_2` on `registry_version`, `legacy_value` (unique).
- `sqlite_autoindex_capability_aliases_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.capability_alias()`
- `Repository.upsert_capability_alias()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/activity_patterns.py`

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
CREATE TABLE capability_aliases (
  id TEXT PRIMARY KEY,
  registry_version INTEGER NOT NULL,
  legacy_value TEXT NOT NULL,
  -- NULL canonical => legacy_unmapped: fails NEW authoring, visible in replay only.
  canonical TEXT CHECK (canonical IS NULL OR canonical IN (
    'retrieval', 'schema_interpretation', 'procedure_execution',
    'method_selection', 'coordination')),
  created_at TEXT NOT NULL,
  UNIQUE(registry_version, legacy_value)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
