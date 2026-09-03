---
title: "causal_probe_candidate_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_probe_candidate_events"
  - "table causal_probe_candidate_events"
schema_head: 157
table_name: "causal_probe_candidate_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "121_causal_probe_coherence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/121_causal_probe_coherence.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_probe_candidate_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of causal probe candidate so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `candidate_id`, `from_status`, `to_status`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/121_causal_probe_coherence.sql`.
- **Schema touched by:** `121_causal_probe_coherence.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `candidate_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/causal_probe_candidates\|causal_probe_candidates.id]] | Stored value |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `from_status` | `TEXT` | no | — | — | Stored value |
| `to_status` | `TEXT` | yes | — | — | Stored value |
| `actor` | `TEXT` | no | — | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `candidate_id` → [[Reference/Database/Tables/causal_probe_candidates|`causal_probe_candidates.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_probe_candidate_events` on `candidate_id`, `seq`.
- `sqlite_autoindex_causal_probe_candidate_events_2` on `candidate_id`, `seq` (unique).
- `sqlite_autoindex_causal_probe_candidate_events_1` on `id` (unique).

Database triggers:

- `causal_probe_candidate_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_probe_candidate_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_probe_candidate_events()`
- `Repository.insert_causal_probe_candidate()`
- `Repository.update_causal_probe_candidate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_probe_coherence.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_probe_commissioning.py`

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
CREATE TABLE causal_probe_candidate_events (
  id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES causal_probe_candidates(id),
  seq INTEGER NOT NULL CHECK (seq >= 1),
  from_status TEXT,
  to_status TEXT NOT NULL CHECK (
    to_status IN ('candidate', 'registered', 'reviewed', 'active', 'rejected')
  ),
  actor TEXT,
  reason TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(candidate_id, seq)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
