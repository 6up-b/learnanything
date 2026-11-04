---
title: "hypothesis_marks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "094836387e8580ee3996941f4e181b109942c8dc"
source_commit_timestamp: "2026-11-04T11:35:15-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite hypothesis_marks"
  - "table hypothesis_marks"
schema_head: 242
table_name: "hypothesis_marks"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "242_hypothesis_marks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/242_hypothesis_marks.sql"
  - "src/learnloop/ai/disclosures.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/daily_plan/router_card.py"
  - "src/learnloop/db/stores/hypothesis_marks.py"
  - "src/learnloop/diagnosis/split/history.py"
  - "src/learnloop/followup_run/marks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `hypothesis_marks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives hypothesis mark a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `learning_object_id`, `diagnosis_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
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
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `diagnosis_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `factor_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `workflow_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `hypothesis_key` | `TEXT` | no | — | — | Stored value |
| `mark` | `TEXT` | yes | — | — | Stored value |
| `free_text` | `TEXT` | no | — | — | Stored value |
| `display_position` | `INTEGER` | no | — | — | Stored value |
| `display_order_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `order_seed` | `TEXT` | no | — | — | Stored value |
| `order_version` | `TEXT` | no | — | — | Stored value |
| `surface` | `TEXT` | yes | — | — | Stored value |
| `probe_answered` | `INTEGER` | yes | — | — | Stored value |
| `probe_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_outcome_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `hypothesis_marks_learning_object` on `learning_object_id`, `created_at`, `id`.
- `hypothesis_marks_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_hypothesis_marks_1` on `id` (unique).

Database triggers:

- `hypothesis_marks_no_delete` — schema-enforced lifecycle or immutability constraint.
- `hypothesis_marks_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_architecture.py`
- `tests/test_followup_fg1c_r1_exposure_independence.py`
- `tests/test_hypothesis_marks.py`
- `tests/test_hypothesis_marks_context.py`
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
CREATE TABLE hypothesis_marks (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  diagnosis_id TEXT,
  factor_id TEXT,
  workflow_id TEXT,
  -- The causal_hypotheses row marked; null for None of these. hypothesis_key is its stable
  -- identity (the row's episode_key), so a later version of the same cause is the same cause.
  hypothesis_version_id TEXT,
  hypothesis_key TEXT,
  mark TEXT NOT NULL CHECK (mark IN ('my_gap', 'partly', 'not_it', 'none_of_these', 'cleared')),
  free_text TEXT,
  -- The list as displayed when this was marked; position is 1-based, null for None of these.
  display_position INTEGER CHECK (display_position IS NULL OR display_position >= 1),
  display_order_json TEXT NOT NULL,
  order_seed TEXT,
  order_version TEXT,
  surface TEXT NOT NULL CHECK (length(trim(surface)) > 0),
  probe_answered INTEGER NOT NULL CHECK (probe_answered IN (0, 1)),
  probe_attempt_id TEXT,
  probe_outcome_json TEXT,
  created_at TEXT NOT NULL,
  CHECK (free_text IS NULL OR mark = 'none_of_these'),
  CHECK (mark <> 'none_of_these' OR hypothesis_version_id IS NULL),
  CHECK (mark NOT IN ('my_gap', 'partly', 'not_it') OR hypothesis_version_id IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
