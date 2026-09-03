---
title: "activity_family_authoring"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite activity_family_authoring"
  - "table activity_family_authoring"
schema_head: 157
table_name: "activity_family_authoring"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "activity-substrate"
introduced_in: "074_activity_contract_extensions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/074_activity_contract_extensions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/activities.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/activity-substrate"
---

# `activity_family_authoring`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives activity family authoring a stable database identity so activity identity, versions, surfaces, exposure, and lineage remain stable across authoring changes. It supplies replay-stable input rather than a disposable cache. Rows bind `family_version_id`, `commitment_id`, `commitment_target_version_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Family-version authoring pins, keyed by the P0 immutable family version id. Additive: the 065 activity_family_versions row is never altered.

It belongs to the **activity substrate** navigation family. The family context lives in [[Database Catalog#Activity Substrate]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

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
| `family_version_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/activity_family_versions\|activity_family_versions.id]] | Stored value |
| `commitment_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/commitments\|commitments.id]] | Stored value |
| `commitment_target_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/commitment_target_versions\|commitment_target_versions.id]] | Stored value |
| `authoring_purpose` | `TEXT` | yes | — | — | Stored value |
| `pattern_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/activity_pattern_versions\|activity_pattern_versions.id]] | Stored value |
| `progression_policy_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/progression_policy_versions\|progression_policy_versions.id]] | Stored value |
| `goal_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `depth_policy_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_policy_versions\|depth_policy_versions.id]] | Stored value |
| `depth_envelope_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/depth_envelope_versions\|depth_envelope_versions.id]] | Stored value |
| `served_milestone_edges_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `cross_purpose_links_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `angle_inventory_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `coverage_targets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `evidence_cap_policy_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `mint_policy_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `retirement_policy_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'draft'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `depth_envelope_version_id` → [[Reference/Database/Tables/depth_envelope_versions|`depth_envelope_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `depth_policy_version_id` → [[Reference/Database/Tables/depth_policy_versions|`depth_policy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `progression_policy_version_id` → [[Reference/Database/Tables/progression_policy_versions|`progression_policy_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `pattern_version_id` → [[Reference/Database/Tables/activity_pattern_versions|`activity_pattern_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_target_version_id` → [[Reference/Database/Tables/commitment_target_versions|`commitment_target_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `commitment_id` → [[Reference/Database/Tables/commitments|`commitments.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `family_version_id` → [[Reference/Database/Tables/activity_family_versions|`activity_family_versions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_afa_commitment` on `commitment_id`.
- `sqlite_autoindex_activity_family_authoring_1` on `family_version_id` (unique).

## Who calls it

### Repository access surface

- `Repository.activity_family_authoring()`
- `Repository.activity_family_authoring_purposes()`
- `Repository.set_activity_family_authoring_status()`
- `Repository.upsert_activity_family_authoring()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/activities.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_contract_extensions.py`

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
CREATE TABLE activity_family_authoring (
  family_version_id TEXT PRIMARY KEY
    REFERENCES activity_family_versions(id) ON DELETE CASCADE,
  commitment_id TEXT REFERENCES commitments(id),
  commitment_target_version_id TEXT REFERENCES commitment_target_versions(id),
  authoring_purpose TEXT NOT NULL CHECK (authoring_purpose IN (
    'diagnostic', 'instructional', 'practice', 'assessment')),
  pattern_version_id TEXT REFERENCES activity_pattern_versions(id),
  progression_policy_version_id TEXT REFERENCES progression_policy_versions(id),
  goal_contract_version_id TEXT,           -- evaluated at authoring, bare TEXT (068-owned)
  depth_policy_version_id TEXT REFERENCES depth_policy_versions(id),
  depth_envelope_version_id TEXT REFERENCES depth_envelope_versions(id),
  served_milestone_edges_json TEXT,
  -- typed cross-purpose links (diagnoses_for/teaches_for/practices_for/assesses_for);
  -- links families, never re-labels a card/surface identity (invariant 2, §3.6).
  cross_purpose_links_json TEXT,
  angle_inventory_json TEXT,
  coverage_targets_json TEXT,
  evidence_cap_policy_id TEXT,
  mint_policy_json TEXT,
  retirement_policy_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'retired')),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Activity Substrate|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
