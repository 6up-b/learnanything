---
title: "followup_value_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b329520d92f0372fccfa1b9cce597bd70afe1c60"
source_commit_timestamp: "2026-10-26T15:34:17-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite followup_value_decisions"
  - "table followup_value_decisions"
schema_head: 222
table_name: "followup_value_decisions"
table_role: "receipt"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "201_followup_value_decisions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/201_followup_value_decisions.sql"
  - "src/learnloop/db/stores/followup_value.py"
  - "src/learnloop/diagnosis/voi_stopping.py"
  - "src/learnloop/evsi_calibration/live_report.py"
  - "src/learnloop/scheduling/voi_forecasts.py"
  - "src/learnloop/voi_stopping_upgrade.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `followup_value_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Keeps one immutable receipt per follow-up decision the value-of-information rule takes part in (mvp-0.21): each decision on a source attempt gets its own id and ordinal (an automatic decision and a later manual follow-up, or a recorded generation need and a later queue), with the value decision's forecasts in `decision_json` (NULL when no candidate was valued), so no later decision overwrites an earlier one and no rebuild clears them. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `source_attempt_id`, `learning_object_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/201_followup_value_decisions.sql`.
- **Schema touched by:** `201_followup_value_decisions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `decision_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `decision_outcome` | `TEXT` | yes | — | — | Stored value |
| `verdict` | `TEXT` | no | — | — | Stored value |
| `manual_override` | `INTEGER` | yes | `0` | — | Stored value |
| `recommended_ref` | `TEXT` | no | — | — | Stored value |
| `served_ref` | `TEXT` | no | — | — | Stored value |
| `need_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `candidate_count` | `INTEGER` | yes | `0` | — | Stored value |
| `forecast_version` | `TEXT` | no | — | — | Stored value |
| `decision_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_followup_value_decisions_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_followup_value_decisions_2` on `source_attempt_id`, `decision_ordinal` (unique).
- `sqlite_autoindex_followup_value_decisions_1` on `id` (unique).

Database triggers:

- `followup_value_decisions_immutable_delete` — schema-enforced lifecycle or immutability constraint.
- `followup_value_decisions_immutable_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/followup_value.py`
- `src/learnloop/evsi_calibration/live_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/followup_value.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_voi_stopping.py`
- `tests/test_voi_v2.py`

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
CREATE TABLE followup_value_decisions (
  id TEXT PRIMARY KEY,
  source_attempt_id TEXT NOT NULL,
  -- 1, 2, ... per source attempt, in decision order.
  decision_ordinal INTEGER NOT NULL CHECK (decision_ordinal >= 1),
  learning_object_id TEXT NOT NULL,
  session_id TEXT,
  -- queued_diagnostic | queued_non_diagnostic_review |
  -- suppressed_voi_value_below_minutes_cost | created_need_for_generation |
  -- created_need_no_discriminator
  decision_outcome TEXT NOT NULL,
  -- The value decision's verdict; NULL when no candidate was valued.
  verdict TEXT CHECK (verdict IS NULL OR verdict IN ('continue', 'stop')),
  manual_override INTEGER NOT NULL DEFAULT 0 CHECK (manual_override IN (0, 1)),
  recommended_ref TEXT,
  served_ref TEXT,
  need_id TEXT,
  candidate_count INTEGER NOT NULL DEFAULT 0 CHECK (candidate_count >= 0),
  forecast_version TEXT,
  decision_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_attempt_id, decision_ordinal)
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
