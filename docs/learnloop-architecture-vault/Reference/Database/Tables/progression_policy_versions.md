---
title: "progression_policy_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite progression_policy_versions"
  - "table progression_policy_versions"
schema_head: 157
table_name: "progression_policy_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "074_activity_contract_extensions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/074_activity_contract_extensions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/scheduling/progression_policy.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `progression_policy_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of progression policy so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `content_hash`, `policy_slug`, `version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 3 (spec_p1_shared_substrate §3.6, §3.7): extend the P0 (migration 065) immutable family/card contracts via side tables keyed by the P0 version id (owner decision A.1 -- never ALTER or rename the immutable P0 version rows; they stay byte-frozen for replay). Adds the immutable progression_policy_versions object (owner decision A.2) that the family construction rule (ActivityFamily = commitment target x ActivityPattern version x progression policy) references as its third factor.

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/074_activity_contract_extensions.sql`.
- **Schema touched by:** `074_activity_contract_extensions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `policy_slug` | `TEXT` | yes | — | — | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `body_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_progression_policy_versions_3` on `content_hash` (unique).
- `sqlite_autoindex_progression_policy_versions_2` on `policy_slug`, `version` (unique).
- `sqlite_autoindex_progression_policy_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_progression_policy_version()`
- `Repository.progression_policy_version()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/progression_policy.py`
- `src/learnloop/substrate/activities.py`

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
CREATE TABLE progression_policy_versions (
  id TEXT PRIMARY KEY,
  policy_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- angle progression order, prerequisite evidence per pattern role, orthogonal-next
  -- behavior, sibling success-propagation shrinkage, family-stage prior update (§5.4/§5.5).
  body_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(policy_slug, version),
  UNIQUE(content_hash)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
