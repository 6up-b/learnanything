---
title: "hypothesis_list_exposures"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_list_exposures"
  - "table hypothesis_list_exposures"
table_name: "hypothesis_list_exposures"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "242_hypothesis_marks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/242_hypothesis_marks.sql"
  - "src/learnloop/db/stores/hypothesis_marks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `hypothesis_list_exposures`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives hypothesis list exposure a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `factor_id`, `diagnosis_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/242_hypothesis_marks.sql`.
- **Schema touched by:** `242_hypothesis_marks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `factor_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `diagnosis_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `workflow_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `hypothesis_version_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `order_seed` | `TEXT` | no | — | — | Stored value |
| `order_version` | `TEXT` | no | — | — | Stored value |
| `probe_answered` | `INTEGER` | yes | — | — | Stored value |
| `probe_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `shown_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `hypothesis_list_exposures_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_hypothesis_list_exposures_1` on `id` (unique).

Database triggers:

- `hypothesis_list_exposures_no_delete` — schema-enforced lifecycle or immutability constraint.
- `hypothesis_list_exposures_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_followup_fg1c_r1_exposure_independence.py`
- `tests/test_followup_fg1d_panel_read.py`
- `tests/test_hypothesis_marks.py`
- `tests/test_hypothesis_marks_migration.py`

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
CREATE TABLE hypothesis_list_exposures (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  factor_id TEXT,
  diagnosis_id TEXT,
  workflow_id TEXT,
  surface TEXT NOT NULL CHECK (length(trim(surface)) > 0),
  -- Ids of causal_hypotheses rows (each one version), in the order on screen.
  hypothesis_version_ids_json TEXT NOT NULL,
  -- Set when the order was shuffled for this list; null when a surface kept its own order.
  order_seed TEXT,
  order_version TEXT,
  probe_answered INTEGER NOT NULL CHECK (probe_answered IN (0, 1)),
  probe_attempt_id TEXT,
  shown_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
