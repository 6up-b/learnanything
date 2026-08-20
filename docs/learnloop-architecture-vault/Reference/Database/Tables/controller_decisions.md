---
title: "controller_decisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite controller_decisions"
  - "table controller_decisions"
schema_head: 156
table_name: "controller_decisions"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `controller_decisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives controller decision a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `snapshot_id`, `session_id`, `commitment_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One staged decision. Points to exactly one snapshot; names the ONE staged rule that fired and the ONE canonical action/subtype; carries the full inspectable trace. `mode` is 'shadow' for all of P4 steps 1-2 (the staged policy logs a recommendation beside the legacy scheduler; live authority is the §14.2 cutover). `receipt_key` gives retry-after-commit idempotency (§3.2, §14.4): a replayed decision returns the standing row, never a different candidate.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`, `098_controller_randomization_and_outcomes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `receipt_key` | `TEXT` | no | — | — | Stored value |
| `snapshot_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/controller_snapshots\|controller_snapshots.id]] | Stored value |
| `snapshot_hash` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `mode` | `TEXT` | yes | `'shadow'` | — | Stored value |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `staged_rule` | `TEXT` | yes | — | — | Stored value |
| `action` | `TEXT` | yes | — | — | Stored value |
| `subtype` | `TEXT` | no | — | — | Stored value |
| `attention_block_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/attention_blocks\|attention_blocks.id]] | Stored value |
| `chosen_candidate_ref` | `TEXT` | no | — | — | Stored value |
| `stop_reason` | `TEXT` | no | — | — | Stored value |
| `constraint_manifest_hash` | `TEXT` | no | — | — | Stored value |
| `decision_params_hash` | `TEXT` | no | — | — | Stored value |
| `policy_version` | `TEXT` | no | — | — | Stored value |
| `comparator_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `trace_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attention_block_id` → [[Reference/Database/Tables/attention_blocks|`attention_blocks.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `snapshot_id` → [[Reference/Database/Tables/controller_snapshots|`controller_snapshots.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_controller_decisions_receipt` on `receipt_key` (unique).
- `idx_controller_decisions_commitment` on `commitment_id`, `created_at`.
- `idx_controller_decisions_session` on `session_id`, `created_at`.
- `idx_controller_decisions_snapshot` on `snapshot_id`.
- `sqlite_autoindex_controller_decisions_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_prequential.py`

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
CREATE TABLE controller_decisions (
  id TEXT PRIMARY KEY,
  receipt_key TEXT,
  snapshot_id TEXT NOT NULL REFERENCES controller_snapshots(id),
  snapshot_hash TEXT NOT NULL,
  session_id TEXT,
  mode TEXT NOT NULL DEFAULT 'shadow' CHECK (mode IN ('shadow', 'live')),
  commitment_id TEXT,
  staged_rule TEXT NOT NULL,
  action TEXT NOT NULL
    CHECK (action IN (
      'measure_diagnostic', 'instruct', 'practice', 'assess_terminal',
      'maintain', 'expand_model', 'stop'
    )),
  subtype TEXT,
  attention_block_id TEXT REFERENCES attention_blocks(id),
  chosen_candidate_ref TEXT,
  stop_reason TEXT,
  constraint_manifest_hash TEXT,
  decision_params_hash TEXT,
  policy_version TEXT,
  -- The legacy scheduler weighted-sum outputs, recorded for comparison ONLY. Never
  -- authority for the staged choice (design §B4; the demoted `_priority`/
  -- `score_selection_reward`).
  comparator_json TEXT,
  trace_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
