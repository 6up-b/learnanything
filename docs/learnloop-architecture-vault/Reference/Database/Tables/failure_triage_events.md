---
title: "failure_triage_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite failure_triage_events"
  - "table failure_triage_events"
schema_head: 157
table_name: "failure_triage_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "083_diagnostic_pack_and_triage.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/083_diagnostic_pack_and_triage.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/failure_triage.py"
  - "src/learnloop/diagnosis/causal_health.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `failure_triage_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of failure triage so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `run_id`, `attempt_id`, `route_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Append-only triage decision ledger (§6.1). Each row records one triage action: the initial evaluation ('triaged'), a tier-two learner/owner selection ('decided'), or an override of a prior route ('overridden'). Every row snapshots the inputs, the resolved route id or provisional distribution, the goal-contract HEAD version it evaluated, and any override actor -- the audit trace of §6.1.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/083_diagnostic_pack_and_triage.sql`.
- **Schema touched by:** `083_diagnostic_pack_and_triage.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `run_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/golden_path_runs\|golden_path_runs.id]] | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `tier` | `TEXT` | yes | — | — | Stored value |
| `decisive` | `INTEGER` | yes | `0` | — | Stored value |
| `route_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selected_reason` | `TEXT` | no | — | — | Stored value |
| `distribution_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `alternatives_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `inputs_snapshot_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `routing_prior_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `override_actor` | `TEXT` | no | — | — | Stored value |
| `override_reason` | `TEXT` | no | — | — | Stored value |
| `anchor_sample_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `auto_committed` | `INTEGER` | yes | `0` | — | Stored value |
| `goal_contract_head_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `idempotency_key` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `run_id` → [[Reference/Database/Tables/golden_path_runs|`golden_path_runs.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_triage_events_run` on `run_id`, `seq`.
- `sqlite_autoindex_failure_triage_events_3` on `run_id`, `idempotency_key` (unique).
- `sqlite_autoindex_failure_triage_events_2` on `run_id`, `seq` (unique).
- `sqlite_autoindex_failure_triage_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_failure_triage_event()`
- `Repository.failure_triage_event()`
- `Repository.failure_triage_events_for()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/failure_triage.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_p2_acceptance.py`
- `tests/test_failure_triage.py`
- `tests/test_failure_triage_causal_gate.py`

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
CREATE TABLE failure_triage_events (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES golden_path_runs(id) ON DELETE CASCADE,
  attempt_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('triaged', 'decided', 'overridden')),
  tier TEXT NOT NULL CHECK (tier IN ('one', 'two')),
  decisive INTEGER NOT NULL DEFAULT 0,
  route_id TEXT,
  selected_reason TEXT,
  distribution_json TEXT,
  alternatives_json TEXT,
  inputs_snapshot_json TEXT,
  routing_prior_json TEXT,
  override_actor TEXT,
  override_reason TEXT,
  anchor_sample_id TEXT,
  auto_committed INTEGER NOT NULL DEFAULT 0,
  goal_contract_head_version_id TEXT,
  seq INTEGER NOT NULL,
  -- Idempotency fence (§12.6): a retried triage()/decide()/override() with the same
  -- key returns the existing event instead of appending a duplicate ledger row.
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(run_id, seq),
  UNIQUE(run_id, idempotency_key)
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
