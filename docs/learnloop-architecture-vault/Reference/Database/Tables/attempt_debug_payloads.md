---
title: "attempt_debug_payloads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attempt_debug_payloads"
  - "table attempt_debug_payloads"
schema_head: 157
table_name: "attempt_debug_payloads"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "007_recall_coverage_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/007_recall_coverage_interventions.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
  - "src/learnloop/diagnosis/guided_redo.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/attempts/grading.py"
  - "src/learnloop/diagnosis/causal_health.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_debug_payloads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attempt debug payload a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/007_recall_coverage_interventions.sql`.
- **Schema touched by:** `007_recall_coverage_interventions.sql`, `126_diagnosis_adjudication.sql`, `130_causal_discriminating_observations.sql`, `133_causal_mechanism_repair_key.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `payload_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_attempt_debug_payloads_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_attempt_diagnosis_receipt()`
- `Repository.attempt_debug_payload()`
- `Repository.record_attempt_outcome()`
- `Repository.record_causal_repair_class_definitions()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`
- `src/learnloop/substrate/replay.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/grading.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/causal_probe_commissioning.py`
- `src/learnloop/diagnosis/diagnosis_adjudication.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/guided_redo.py`
- `src/learnloop/diagnosis/missing_vocabulary.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/learner/recall_calibration.py`
- `src/learnloop/substrate/replay.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/serializers.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_table_roles.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_repair_mapping_p2.py`
- `tests/test_causal_shadow_selection.py`
- `tests/test_deferred_regrade.py`
- `tests/test_error_hunt_items.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_item_parameters.py`
- `tests/test_minimal_repair_selection_a1.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_replay.py`
- `tests/test_reveal_ledger.py`

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
CREATE TABLE attempt_debug_payloads (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  payload_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
