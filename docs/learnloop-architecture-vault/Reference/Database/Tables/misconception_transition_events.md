---
title: "misconception_transition_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite misconception_transition_events"
  - "table misconception_transition_events"
schema_head: 156
table_name: "misconception_transition_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "056_misconception_transitions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/056_misconception_transitions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/diagnosis/misconceptions.py"
  - "src/learnloop/learner/session_learning_diff.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `misconception_transition_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of misconception transition so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `misconception_id`, `from_status`, `to_status`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/056_misconception_transitions.sql`.
- **Schema touched by:** `056_misconception_transitions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `misconception_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/misconceptions\|misconceptions.id]] | Stored value |
| `from_status` | `TEXT` | no | — | — | Stored value |
| `to_status` | `TEXT` | yes | — | — | Stored value |
| `at` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `misconception_id` → [[Reference/Database/Tables/misconceptions|`misconceptions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_misconception_transition_events_case` on `misconception_id`, `at`, `id`.
- `sqlite_autoindex_misconception_transition_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_misconception()`
- `Repository.misconception_transition_counts_between()`
- `Repository.misconception_transition_events()`
- `Repository.update_misconception()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/learner/session_learning_diff.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_misconception_transitions_intake.py`
- `tests/test_causal_cold_outcomes.py`
- `tests/test_cli_json.py`
- `tests/test_coldness_receipt.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_diagnostic_gate.py`
- `tests/test_diagnostic_generation.py`
- `tests/test_error_hunt_items.py`
- `tests/test_guided_redo.py`
- `tests/test_hypothesis_surface_wiring.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_km4_taxonomy.py`
- `tests/test_misconception_registry.py`
- `tests/test_misconception_routing.py`
- `tests/test_persona_gate.py`
- `tests/test_probe_remint.py`
- `tests/test_remediation_cold_retry.py`
- `tests/test_repositories.py`
- `tests/test_reveal_ledger.py`
- `tests/test_scoreboard.py`

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
CREATE TABLE misconception_transition_events (
  id TEXT PRIMARY KEY,
  misconception_id TEXT NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
  from_status TEXT CHECK (from_status IS NULL OR from_status IN ('active', 'resolving', 'resolved')),
  to_status TEXT NOT NULL CHECK (to_status IN ('active', 'resolving', 'resolved')),
  at TEXT NOT NULL,
  source TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
