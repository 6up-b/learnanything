---
title: "assumption_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "8bb003daebe1bc05c564017fea6dcaa17ae78317"
source_commit_timestamp: "2026-10-20T15:55:44-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite assumption_decisions"
  - "table assumption_decisions"
schema_head: 213
table_name: "assumption_decisions"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "172_placement_assumptions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/172_placement_assumptions.sql"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/db/stores/placement.py"
  - "src/learnloop/placement/decisions.py"
  - "src/learnloop/placement/report.py"
  - "src/learnloop/placement/state.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `assumption_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives assumption decision a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `learning_object_id`, `quick_check_session_id`, `trigger_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Slice A Phase 6 (learner field F2, mvp-0.11): starting new material without ceremony. Receipts only: nothing here is evidence, mastery or certification. One row per "assumed known (not tested)" decision. Append-only. The first review's outcome is joined from practice_attempts by report 3 and by the serving read, never written back here.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/172_placement_assumptions.sql`.
- **Schema touched by:** `172_placement_assumptions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source` | `TEXT` | yes | — | — | Stored value |
| `trigger_kind` | `TEXT` | yes | — | — | Stored value |
| `trigger_ref` | `TEXT` | no | — | — | Stored value |
| `p` | `REAL` | no | — | — | Stored value |
| `interval_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `q_used` | `REAL` | no | — | — | Stored value |
| `theta_known` | `REAL` | no | — | — | Stored value |
| `predictor` | `TEXT` | yes | — | — | Stored value |
| `predictor_version` | `TEXT` | yes | — | — | Stored value |
| `first_review_due` | `TEXT` | yes | — | — | Stored value |
| `quick_check_session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `config_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `inputs_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `assumption_decisions_lo` on `learning_object_id`, `created_at`, `id`.
- `sqlite_autoindex_assumption_decisions_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/placement/decisions.py`
- `src/learnloop/placement/state.py`

### Direct SQL writers

- `src/learnloop/db/stores/placement.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_assumed_known.py`
- `tests/test_mvp011_upgrade.py`

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
CREATE TABLE assumption_decisions (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('self_report','fast_track','predictor','quick_check')),
  -- What fired it: i_know_this | too_easy | fast_track_rule | quick_check_result | predictor_rule.
  trigger_kind TEXT NOT NULL,
  -- The item, LO list, attempt ids or calibration session that triggered it.
  trigger_ref TEXT,
  -- P(theta_L > theta_known) under the active predictor; NULL for self-reports.
  p REAL CHECK (p IS NULL OR (p >= 0 AND p <= 1)),
  -- 80% interval of theta_L (logit), as JSON [low, high]; NULL when untested.
  interval_json TEXT,
  q_used REAL CHECK (q_used IS NULL OR (q_used > 0 AND q_used < 1)),
  theta_known REAL,
  predictor TEXT NOT NULL,
  predictor_version TEXT NOT NULL,
  first_review_due TEXT NOT NULL,
  quick_check_session_id TEXT,
  algorithm_version TEXT NOT NULL,
  -- The placement config in force and every input the rule read (G8).
  config_json TEXT NOT NULL,
  inputs_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
