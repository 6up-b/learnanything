---
title: "recurrence_escalations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c3d703cd008912c13937c0b95a689b69989e76e6"
source_commit_timestamp: "2026-10-12T22:21:10-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite recurrence_escalations"
  - "table recurrence_escalations"
schema_head: 177
table_name: "recurrence_escalations"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "176_recurrence_groups.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/176_recurrence_groups.sql"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/diagnosis/recurrence/report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `recurrence_escalations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives recurrence escalation a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `attempt_id`, `diagnosis_id`, `repair_suggestion_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> What an escalated repair showed (§3.7), written once when the diagnosis is applied: the group, the earlier answers cited as evidence, the repair chosen and whether its operator differs from the group's earlier repairs. attempt_id has no foreign key, like the other append-only ledgers (164).

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/176_recurrence_groups.sql`.
- **Schema touched by:** `176_recurrence_groups.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `diagnosis_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `group_key` | `TEXT` | yes | — | — | Stored value |
| `recurrence_count` | `INTEGER` | yes | — | — | Stored value |
| `earlier_attempt_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `repair_suggestion_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `repair_operator` | `TEXT` | no | — | — | Stored value |
| `prior_operators_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `different_approach` | `INTEGER` | yes | — | — | Stored value |
| `repair_source` | `TEXT` | yes | `'diagnosis'` | — | Stored value |
| `repair_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `generation_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `recurrence_escalations_group` on `group_key`, `created_at`.
- `sqlite_autoindex_recurrence_escalations_2` on `attempt_id`, `diagnosis_id` (unique).
- `sqlite_autoindex_recurrence_escalations_1` on `id` (unique).

Database triggers:

- `recurrence_escalations_no_delete` — schema-enforced lifecycle or immutability constraint.
- `recurrence_escalations_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/recurrence.py`

### Direct SQL writers

- `src/learnloop/db/stores/recurrence.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_recurrence_live.py`

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
CREATE TABLE recurrence_escalations (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  diagnosis_id TEXT NOT NULL,
  group_key TEXT NOT NULL,
  recurrence_count INTEGER NOT NULL CHECK (recurrence_count >= 1),
  earlier_attempt_ids_json TEXT NOT NULL DEFAULT '[]',
  repair_suggestion_id TEXT,
  repair_operator TEXT,
  prior_operators_json TEXT NOT NULL DEFAULT '[]',
  different_approach INTEGER NOT NULL CHECK (different_approach IN (0, 1)),
  -- Where the shown repair came from: one of the diagnosis's own repairs, a
  -- repair written at escalation time with a different operator and
  -- representation (its payload in repair_json), or none.
  repair_source TEXT NOT NULL DEFAULT 'diagnosis'
    CHECK (repair_source IN ('diagnosis', 'generated', 'none')),
  repair_json TEXT,
  -- The escalated-repair request: whether it ran, and why it was not used.
  generation_json TEXT NOT NULL DEFAULT '{}',
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (attempt_id, diagnosis_id),
  CHECK ((repair_source = 'generated') = (repair_json IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
