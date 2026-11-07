---
title: "figure_source_checks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "a95e354cf34338a9ddf45cbeb79e5cf3451229de"
source_commit_timestamp: "2026-11-07T03:01:14-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite figure_source_checks"
  - "table figure_source_checks"
schema_head: 249
table_name: "figure_source_checks"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "238_figure_source_checks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/238_figure_source_checks.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/figures.py"
  - "src/learnloop/figure_admission.py"
  - "src/learnloop/figures/source_check.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `figure_source_checks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives figure source check a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `figure_id`, `judgment_id`, `certification_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/238_figure_source_checks.sql`.
- **Schema touched by:** `238_figure_source_checks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `figure_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/interactive_figures\|interactive_figures.id]] | Stored value |
| `certification_version` | `INTEGER` | yes | — | — | Stored value |
| `trigger` | `TEXT` | yes | — | — | Stored value |
| `outcome` | `TEXT` | yes | — | — | Stored value |
| `definitions_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `elements_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `reasons_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `harness_sha256` | `TEXT` | yes | — | — | Stored value |
| `reader_version` | `TEXT` | yes | — | — | Stored value |
| `sympy_version` | `TEXT` | yes | `''` | — | Stored value |
| `duration_ms` | `INTEGER` | no | — | — | Stored value |
| `judgment_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `judgment_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `figure_id` → [[Reference/Database/Tables/interactive_figures|`interactive_figures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_figure_source_checks_figure` on `figure_id`, `certification_version`, `created_at`.
- `sqlite_autoindex_figure_source_checks_1` on `id` (unique).

Database triggers:

- `figure_source_checks_no_delete` — schema-enforced lifecycle or immutability constraint.
- `figure_source_checks_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/figures.py`

### Direct SQL writers

- `src/learnloop/db/stores/figures.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/rw5c_golden_source.py`
- `tests/test_rw5c_judgments.py`
- `tests/test_rw5c_migration.py`
- `tests/test_rw5c_never_evidence.py`
- `tests/test_rw5c_recheck.py`
- `tests/test_rw5c_source_check.py`
- `tests/test_rw5c_switch_off.py`

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
CREATE TABLE figure_source_checks (
  id TEXT PRIMARY KEY,
  figure_id TEXT NOT NULL REFERENCES interactive_figures(id),
  certification_version INTEGER NOT NULL CHECK (certification_version >= 1),
  "trigger" TEXT NOT NULL CHECK ("trigger" IN ('build', 'recheck')),
  outcome TEXT NOT NULL CHECK (outcome IN ('checked', 'differs', 'undecided', 'not_checkable')),
  definitions_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(definitions_json)),
  elements_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(elements_json)),
  reasons_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(reasons_json)),
  harness_sha256 TEXT NOT NULL,
  reader_version TEXT NOT NULL,
  sympy_version TEXT NOT NULL DEFAULT '',
  duration_ms INTEGER,
  judgment_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
