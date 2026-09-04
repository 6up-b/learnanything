---
title: "goal_contract_drafts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite goal_contract_drafts"
  - "table goal_contract_drafts"
schema_head: 157
table_name: "goal_contract_drafts"
table_role: "workflow"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "068_goal_terminal_contracts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/068_goal_terminal_contracts.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/goal_contracts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `goal_contract_drafts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives goal contract draft a stable database identity so goal progress and held-out certification remain tied to the contract and evidence that produced them. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `predecessor_version_id`, `rejection_reason`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- goal_contract_drafts (§3.4): non-pinnable proposals. A rejected append_authorized_depth_successor or a pre-confirmation body lands here. No version id, no head row -> the type-level guarantee a draft cannot be pinned. ----------------------------------------------------------------------------

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/068_goal_terminal_contracts.sql`.
- **Schema touched by:** `068_goal_terminal_contracts.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `predecessor_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/goal_contract_versions\|goal_contract_versions.id]] | Stored value |
| `proposed_contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `proposed_change_class` | `TEXT` | no | — | — | Stored value |
| `rejection_reason` | `TEXT` | yes | — | — | Stored value |
| `evidence_receipt_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `requires` | `TEXT` | yes | — | — | Stored value |
| `author` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `predecessor_version_id` → [[Reference/Database/Tables/goal_contract_versions|`goal_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gcd_goal` on `goal_id`.
- `sqlite_autoindex_goal_contract_drafts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.goal_contract_drafts_for_goal()`
- `Repository.insert_goal_contract_draft()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/goals/goal_contracts.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_goal_contracts.py`

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
CREATE TABLE goal_contract_drafts (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  predecessor_version_id TEXT REFERENCES goal_contract_versions(id),
  proposed_contract_json TEXT NOT NULL,
  proposed_change_class TEXT,
  rejection_reason TEXT NOT NULL CHECK (rejection_reason IN (
    'outside_envelope', 'unreviewed_edge', 'stale_envelope',
    'predecessor_not_head', 'multiple_edges', 'insufficient_evidence',
    'pre_confirmation_draft'
  )),
  evidence_receipt_json TEXT,
  requires TEXT NOT NULL CHECK (requires IN (
    'learner_confirmed_envelope', 'learner_confirmed_successor', 'exemplar_and_blueprint'
  )),
  author TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
