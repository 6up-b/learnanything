---
title: "surface_fingerprint_memberships"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite surface_fingerprint_memberships"
  - "table surface_fingerprint_memberships"
schema_head: 156
table_name: "surface_fingerprint_memberships"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "077_familiarity_namespace.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/077_familiarity_namespace.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/familiarity.py"
  - "src/learnloop/scheduling/kinship_feature.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `surface_fingerprint_memberships`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives surface fingerprint membership a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `surface_id`, `value_hash`, `namespace`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P1 step 6 (spec_p1_shared_substrate §4.1, §4.2, §3.9): one namespaced familiarity ledger. P0's activity_exposure_events (migration 065) stays THE authoritative exact-exposure ledger; P1 adds, ALONGSIDE it, normalized fingerprint-group memberships + a separate soft-kinship feature vector + surface authoring. familiarity_projection_v1 reads exposure UNION memberships.  Standing rule 5 / §4.1: namespaces are NEVER interchangeable -- a value `svd-1` in source_example cannot collide with `svd-1` in solution_recipe. A surface may belong to MANY groups; selecting the first non-empty field is forbidden (this replaces the legacy canonical_projection first-field bug). Salience signals are never learner evidence: warmth discounts/withholds evidence, it never mints it.

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
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `surface_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/activity_surfaces\|activity_surfaces.id]] | Stored value |
| `namespace` | `TEXT` | yes | — | — | Stored value |
| `value_hash` | `TEXT` | yes | — | — | Stored value |
| `provenance` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | no | — | — | Stored value |
| `confidence` | `REAL` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `surface_id` → [[Reference/Database/Tables/activity_surfaces|`activity_surfaces.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_sfm_surface` on `surface_id`.
- `idx_sfm_ns_value` on `namespace`, `value_hash`.
- `sqlite_autoindex_surface_fingerprint_memberships_2` on `surface_id`, `namespace`, `value_hash` (unique).
- `sqlite_autoindex_surface_fingerprint_memberships_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.fingerprint_memberships_for_surface()`
- `Repository.record_fingerprint_membership()`
- `Repository.surfaces_sharing_membership()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/learner/familiarity.py`
- `src/learnloop/scheduling/kinship_feature.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_familiarity.py`

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
CREATE TABLE surface_fingerprint_memberships (
  id TEXT PRIMARY KEY,
  surface_id TEXT NOT NULL REFERENCES activity_surfaces(id) ON DELETE CASCADE,
  namespace TEXT NOT NULL CHECK (namespace IN (
    'surface_hash', 'shared_stimulus', 'source_example', 'solution_recipe',
    'parameter_template', 'verbatim_target', 'external_artifact')),
  value_hash TEXT NOT NULL,
  provenance TEXT,
  -- status: 'known' | 'unknown' (§4.1: missing/unverifiable fingerprint -> unknown,
  -- never silently 'novel'). Left free-text so a degraded tutor-exposure can mark it.
  status TEXT,
  confidence REAL,
  created_at TEXT NOT NULL,
  -- One membership per (surface, namespace, value): a surface joins a group once.
  UNIQUE(surface_id, namespace, value_hash)
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
