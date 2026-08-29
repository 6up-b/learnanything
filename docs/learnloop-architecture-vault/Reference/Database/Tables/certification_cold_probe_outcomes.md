---
title: "certification_cold_probe_outcomes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite certification_cold_probe_outcomes"
  - "table certification_cold_probe_outcomes"
schema_head: 156
table_name: "certification_cold_probe_outcomes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "139_certification_cold_probes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/139_certification_cold_probes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/certification_cold_probe.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `certification_cold_probe_outcomes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the measured outcome and lineage for certification cold probe so goal progress and held-out certification remain tied to the contract and evidence that produced them. It supplies replay-stable input rather than a disposable cache. Rows bind `certificate_id`, `learning_object_id`, `blueprint_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/139_certification_cold_probes.sql`.
- **Schema touched by:** `139_certification_cold_probes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `certificate_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `blueprint_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `recipe_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `certificate_receipt_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `certified_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `followup_task_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `scheduled_not_before` | `TEXT` | yes | — | — | Stored value |
| `scheduled_expires_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `horizon_days` | `REAL` | yes | — | — | Stored value |
| `window_days` | `REAL` | yes | — | — | Stored value |
| `probe_practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `probe_surface_group` | `TEXT` | yes | — | — | Stored value |
| `excluded_surface_groups_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `held_out_basis` | `TEXT` | yes | — | — | Stored value |
| `avoided_affordances_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `verdict` | `TEXT` | yes | — | — | Stored value |
| `indeterminate_reason` | `TEXT` | no | — | — | Stored value |
| `success` | `INTEGER` | no | — | — | Stored value |
| `correctness` | `REAL` | no | — | — | Stored value |
| `success_threshold` | `REAL` | yes | — | — | Stored value |
| `assisted` | `INTEGER` | yes | — | — | Stored value |
| `certificate_state_at_probe` | `TEXT` | yes | — | — | Stored value |
| `store_version` | `TEXT` | yes | — | — | Stored value |
| `policy_version` | `TEXT` | yes | — | — | Stored value |
| `certification_algorithm_version` | `TEXT` | no | — | — | Stored value |
| `parameters_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `grading_source` | `TEXT` | no | — | — | Stored value |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `grader_model` | `TEXT` | no | — | — | Stored value |
| `grader_provider` | `TEXT` | no | — | — | Stored value |
| `grader_provider_revision` | `TEXT` | no | — | — | Stored value |
| `grading_agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_certification_cold_probe_outcome_slices` on `horizon_days`, `grader_model`, `created_at`.
- `idx_certification_cold_probe_outcome_verdict` on `verdict`, `created_at`, `id`.
- `idx_certification_cold_probe_outcome_lo` on `learning_object_id`, `created_at`, `id`.
- `uq_certification_cold_probe_outcome_certificate` on `certificate_id` (unique).
- `uq_certification_cold_probe_outcome_attempt` on `probe_attempt_id` (unique).
- `sqlite_autoindex_certification_cold_probe_outcomes_1` on `id` (unique).

Database triggers:

- `certification_cold_probe_outcomes_no_delete` — schema-enforced lifecycle or immutability constraint.
- `certification_cold_probe_outcomes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.certification_cold_probe_outcome_for_attempt()`
- `Repository.certification_cold_probe_outcomes()`
- `Repository.insert_certification_cold_probe_outcome()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/goals/certification_cold_probe.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_certification_cold_probe.py`

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
CREATE TABLE certification_cold_probe_outcomes (
  -- Content hash over (certificate id, probe task, probe attempt): the same
  -- probe recorded twice is one row, so the live path may run inside
  -- `apply_attempt` and a replay of the same attempt cannot double-count a
  -- ground-truth label.
  id TEXT PRIMARY KEY,

  -- WHICH CERTIFICATE. No FK to a certificates table because none exists yet:
  -- §5.3 receipts are plan item 8.4. Until then the certificate is derived from
  -- the capability ledger and SNAPSHOTTED here (`certificate_receipt_json`), so
  -- this row keeps meaning something after the ledger moves. When 8.4 lands, the
  -- stored receipt id goes in `certificate_id` unchanged -- it is already the
  -- content hash of the same tuple.
  certificate_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  blueprint_id TEXT NOT NULL,
  recipe_id TEXT NOT NULL,
  -- The §5.3 receipt as it stood when the probe was scheduled: which cells were
  -- certified, at what credit, from which surface groups, measured-vs-inferred.
  -- "A certificate that cannot distinguish these is not one" (standing
  -- constraint 9).
  certificate_receipt_json TEXT NOT NULL,
  certified_at TEXT,

  -- THE SCHEDULE. `horizon_days` / `window_days` are recorded per row because
  -- they are fitted parameters (scope `certification_cold_probe`): a rate
  -- computed across a horizon change must be sliceable by horizon.
  followup_task_id TEXT NOT NULL,
  scheduled_not_before TEXT NOT NULL,
  scheduled_expires_at TEXT,
  horizon_days REAL NOT NULL,
  window_days REAL NOT NULL,

  -- THE PROBE. `excluded_surface_groups_json` is the held-out claim: the surface
  -- groups the certifying evidence came from. `probe_surface_group` must not be
  -- among them, and the CHECK below refuses to record `held` when it is.
  probe_practice_item_id TEXT NOT NULL,
  probe_attempt_id TEXT NOT NULL,
  probe_surface_group TEXT NOT NULL,
  excluded_surface_groups_json TEXT NOT NULL,
  held_out_basis TEXT NOT NULL CHECK (
    held_out_basis IN ('distinct_surface_group', 'shared_surface_group', 'unknown')
  ),
  -- Affordances the certifying evidence had that this probe does not, in the
  -- `causal_cold_verifications.avoided_affordances_json` vocabulary, so a P4
  -- reader can union the two cold-outcome channels.
  avoided_affordances_json TEXT NOT NULL,

  -- THE VERDICT.
  verdict TEXT NOT NULL CHECK (verdict IN ('held', 'failed', 'indeterminate')),
  -- Required exactly when the verdict is `indeterminate`, forbidden otherwise:
  -- an abstention whose reason is not recorded is indistinguishable from a
  -- missing row, and "not yet measured" is the arm this metric exists to keep
  -- separate from "passed".
  indeterminate_reason TEXT CHECK (
    indeterminate_reason IS NULL
    OR indeterminate_reason IN (
      'assisted_probe',
      'surface_not_held_out',
      'certificate_withdrawn',
      'grade_unavailable'
    )
  ),
  -- Denormalized 0/1 so the metric is one SQL aggregate and cannot drift from
  -- the verdict vocabulary; NULL on `indeterminate` (no label).
  success INTEGER CHECK (success IS NULL OR success IN (0, 1)),
  correctness REAL,
  success_threshold REAL NOT NULL,
  assisted INTEGER NOT NULL CHECK (assisted IN (0, 1)),
  certificate_state_at_probe TEXT NOT NULL CHECK (
    certificate_state_at_probe IN ('active', 'withdrawn')
  ),

  -- VERSION PINS, following `diagnosis_adjudications` (126). A label that
  -- cannot name the policy, the parameter set, and the grader that produced it
  -- is not reusable once any of the three moves -- and all three move inside a
  -- single Stage 6 week.
  store_version TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  certification_algorithm_version TEXT,
  parameters_json TEXT NOT NULL,
  grading_source TEXT,
  grading_prompt_version TEXT,
  grader_model TEXT,
  grader_provider TEXT,
  grader_provider_revision TEXT,
  grading_agent_run_id TEXT,
  created_at TEXT NOT NULL,

  -- The verdict partitions on the abstention reason in both directions.
  CHECK (
    (verdict = 'indeterminate' AND indeterminate_reason IS NOT NULL AND success IS NULL)
    OR
    (verdict IN ('held', 'failed') AND indeterminate_reason IS NULL AND success IS NOT NULL)
  ),
  CHECK (verdict != 'held' OR success = 1),
  CHECK (verdict != 'failed' OR success = 0),
  -- A scored verdict requires a genuinely held-out surface and an unassisted
  -- probe. Both failure modes have their own `indeterminate_reason`, so this
  -- CHECK cannot silently discard a probe -- it forces it into the abstention
  -- arm where the denominator can see it.
  CHECK (verdict = 'indeterminate' OR held_out_basis = 'distinct_surface_group'),
  CHECK (verdict = 'indeterminate' OR assisted = 0),
  CHECK (verdict = 'indeterminate' OR certificate_state_at_probe = 'active')
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
