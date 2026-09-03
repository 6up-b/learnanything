---
title: "misconception_disposition_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite misconception_disposition_events"
  - "table misconception_disposition_events"
schema_head: 157
table_name: "misconception_disposition_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "116_measurement_contract_corrections.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/116_measurement_contract_corrections.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/learner/surfaced_beliefs.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/content/authoring/persona_gate.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/content/synthesis/facet_candidates.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `misconception_disposition_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of misconception disposition so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `misconception_id`, `replacement_misconception_id`, `disposition`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Migration 115 used `misconceptions.status = resolved` as the only backwards-compatible way to remove an invalid first-error promotion from legacy active-state queries. Record its actual lifecycle meaning separately: the learner did not learn it; the diagnosis was demoted. This event stream is the semantic authority and leaves the original row/audit trace intact.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/116_measurement_contract_corrections.sql`.
- **Schema touched by:** `116_measurement_contract_corrections.sql`, `132_surfaced_belief_corrections.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `misconception_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/misconceptions\|misconceptions.id]] | Stored value |
| `disposition` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `replacement_misconception_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

Declared SQLite foreign keys:

- `misconception_id` → [[Reference/Database/Tables/misconceptions|`misconceptions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_misconception_disposition_events_at` on `created_at`, `id`.
- `idx_misconception_disposition_events_case` on `misconception_id`, `created_at`, `id`.
- `sqlite_autoindex_misconception_disposition_events_1` on `id` (unique).

Database triggers:

- `misconception_disposition_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `misconception_disposition_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.active_misconception_facet_ids()`
- `Repository.insert_misconception_disposition()`
- `Repository.misconception()`
- `Repository.misconception_dispositions()`
- `Repository.misconceptions_for_concepts()`
- `Repository.misconceptions_for_learning_object()`
- `Repository.surfaced_belief_withdrawals()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/content/authoring/persona_gate.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/content/synthesis/facet_candidates.py`
- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/diagnostic_gate.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/probe_hypotheses.py`
- `src/learnloop/diagnosis/probe_instance_generation.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/learner/independence_audit.py`
- `src/learnloop/learner/learner_review_feed.py`
- `src/learnloop/learner/surfaced_beliefs.py`
- `src/learnloop/tutor/durable_promotion.py`
- `src/learnloop/tutor/promotions.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_scoreboard.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_guided_redo.py`
- `tests/test_km4_taxonomy.py`
- `tests/test_misconception_registry.py`
- `tests/test_misconception_transitions_intake.py`
- `tests/test_probe_block_end.py`
- `tests/test_repositories.py`
- `tests/test_sidecar_adjudication.py`
- `tests/test_surfaced_belief_corrections.py`

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
CREATE TABLE misconception_disposition_events (
  id TEXT PRIMARY KEY,
  misconception_id TEXT NOT NULL REFERENCES misconceptions(id),
  disposition TEXT NOT NULL CHECK (disposition IN ('demoted', 'superseded')),
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
, replacement_misconception_id TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
