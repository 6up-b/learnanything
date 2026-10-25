---
title: "ad_attempt_trace"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "2842badae10079a99be05e4d28c4e3cdc4112d87"
source_commit_timestamp: "2026-10-24T22:53:15-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ad_attempt_trace"
  - "table ad_attempt_trace"
schema_head: 219
table_name: "ad_attempt_trace"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/replay.py"
  - "src/learnloop/db/stores/ad_serving.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `ad_attempt_trace`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ad attempt trace a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `attempt_id`, `input_status`, `view`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.6 step 6 (DERIVED; the AD replayer): per eligible attempt and view, the prior and posterior moments of η, the predicted category probabilities, the information gained, the input status, and, for the subject view, each grid point's marginal likelihood and weight.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** `adaptive_difficulty`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `view` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `input_status` | `TEXT` | yes | — | — | Stored value |
| `category` | `INTEGER` | no | — | — | Stored value |
| `prior_mean` | `REAL` | no | — | — | Stored value |
| `prior_var` | `REAL` | no | — | — | Stored value |
| `post_mean` | `REAL` | no | — | — | Stored value |
| `post_var` | `REAL` | no | — | — | Stored value |
| `p_categories_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `information` | `REAL` | no | — | — | Stored value |
| `points_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_ad_attempt_trace_1` on `attempt_id`, `view` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad23_contract.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_architecture.py`
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
CREATE TABLE ad_attempt_trace (
  attempt_id TEXT NOT NULL,
  view TEXT NOT NULL,
  input_status TEXT NOT NULL CHECK (input_status IN ('frozen', 'exact', 'reconstructed_current', 'excluded')),
  category INTEGER,
  prior_mean REAL,
  prior_var REAL,
  post_mean REAL,
  post_var REAL,
  p_categories_json TEXT,
  information REAL,
  points_json TEXT,
  detail_json TEXT NOT NULL,
  PRIMARY KEY (attempt_id, view)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
