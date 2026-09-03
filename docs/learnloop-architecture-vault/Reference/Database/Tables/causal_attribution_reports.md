---
title: "causal_attribution_reports"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_attribution_reports"
  - "table causal_attribution_reports"
schema_head: 157
table_name: "causal_attribution_reports"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "115_causal_attribution_p0.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/115_causal_attribution_p0.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
  - "src/learnloop/tutor/durable_promotion.py"
  - "src/learnloop_sidecar/handlers/feedback.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_health.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_attribution_reports`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Captures an inspectable analysis result for causal attribution so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `factor_id`, `attempt_id`, `response`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Immutable learner self-report channel for the one-tap unresolved-cause question. Kept separate from interaction_events because that legacy table has a closed kind CHECK.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/115_causal_attribution_p0.sql`.
- **Schema touched by:** `115_causal_attribution_p0.sql`, `126_diagnosis_adjudication.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `factor_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/unresolved_cause_factors\|unresolved_cause_factors.id]] | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `response` | `TEXT` | yes | — | — | Stored value |
| `candidate_index` | `INTEGER` | no | — | — | Stored value |
| `payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `factor_id` → [[Reference/Database/Tables/unresolved_cause_factors|`unresolved_cause_factors.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_attribution_reports_factor` on `factor_id`, `created_at`.
- `sqlite_autoindex_causal_attribution_reports_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.causal_attribution_reports_for_factor()`
- `Repository.insert_causal_attribution_report()`
- `Repository.unresolved_cause_factors_for_attempt()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/probe_targeting.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_diagnosis_adjudication.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_probe_block_end.py`

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
CREATE TABLE causal_attribution_reports (
  id TEXT PRIMARY KEY,
  factor_id TEXT NOT NULL REFERENCES unresolved_cause_factors(id),
  attempt_id TEXT NOT NULL,
  response TEXT NOT NULL,
  candidate_index INTEGER,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
