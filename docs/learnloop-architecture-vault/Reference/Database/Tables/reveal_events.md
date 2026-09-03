---
title: "reveal_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite reveal_events"
  - "table reveal_events"
schema_head: 157
table_name: "reveal_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "154_reveal_ledger.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/154_reveal_ledger.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/attempts/reveal_ledger.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/tutor/tutor_qa.py"
  - "src/learnloop/scheduling/scheduler.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `reveal_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of reveal so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `learning_object_id`, `remediation_episode_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/154_reveal_ledger.sql`.
- **Schema touched by:** `154_reveal_ledger.sql`, `155_observation_admissibility.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_kind` | `TEXT` | yes | — | — | Stored value |
| `amount` | `REAL` | yes | — | — | Stored value |
| `basis` | `TEXT` | no | — | — | Stored value |
| `question_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reveal_events_episode` on `remediation_episode_id`.
- `idx_reveal_events_item_created` on `practice_item_id`, `created_at`, `id`.
- `sqlite_autoindex_reveal_events_1` on `id` (unique).

Database triggers:

- `reveal_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reveal_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.insert_reveal_event()`
- `Repository.reveal_events()`
- `Repository.reveal_events_for_target()`
- `Repository.total_reveal_amount()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/reveal_ledger.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/scheduling/scheduler.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_coldness_receipt.py`
- `tests/test_reveal_ledger.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_remediation_cold_retry.py`
- `tests/test_scheduler.py`
- `tests/test_sidecar_remediation_surfaces.py`

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
CREATE TABLE reveal_events (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  remediation_episode_id TEXT,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN (
      'tutor_answer',
      'repair_display',
      'guided_redo',
      'source_review'
    )
  ),
  amount REAL NOT NULL CHECK (amount >= 0.0 AND amount <= 1.0),
  basis TEXT,
  question_event_id TEXT,
  attempt_id TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
