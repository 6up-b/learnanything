---
title: "family_evidence_cap_policies"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite family_evidence_cap_policies"
  - "table family_evidence_cap_policies"
schema_head: 157
table_name: "family_evidence_cap_policies"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "curriculum"
introduced_in: "079_progression_and_lapse.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/079_progression_and_lapse.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/scheduling/progression.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/curriculum"
---

# `family_evidence_cap_policies`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins the policy definition used for family evidence cap so curriculum progression is versioned and can explain which commitment, depth, and blueprint governed an activity. It supplies replay-stable input rather than a disposable cache. Rows bind `content_hash`, `policy_slug`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **curriculum** navigation family. The family context lives in [[Database Catalog#Curriculum]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/079_progression_and_lapse.sql`.
- **Schema touched by:** `079_progression_and_lapse.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `policy_slug` | `TEXT` | yes | — | — | Stored value |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `caps_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_family_evidence_cap_policies_2` on `policy_slug`, `version` (unique).
- `sqlite_autoindex_family_evidence_cap_policies_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.ensure_family_evidence_cap_policy()`
- `Repository.family_evidence_cap_policy()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/progression.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_progression.py`

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
CREATE TABLE family_evidence_cap_policies (
  id TEXT PRIMARY KEY,
  policy_slug TEXT NOT NULL,
  version INTEGER NOT NULL,
  -- caps: max effective independent mass per target x capability x angle neighborhood
  -- and the tight_kinship_threshold that defines a cluster (§4.3, A.4). Every numeric
  -- knob here is a registered heuristic decision parameter.
  caps_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(policy_slug, version)
);
```

## Related notes

- [[Database Catalog#Curriculum|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
