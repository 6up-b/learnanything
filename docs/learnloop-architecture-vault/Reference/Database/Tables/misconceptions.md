---
title: "misconceptions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite misconceptions"
  - "table misconceptions"
schema_head: 157
table_name: "misconceptions"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "025_misconception_registry.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/025_misconception_registry.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/cli/sim.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/content/authoring/persona_gate.py"
  - "src/learnloop/content/synthesis/facet_candidates.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `misconceptions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives misconception a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learning_object_id`, `concept_id`, `promotion_reason`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Content-bearing misconceptions (spec_misconception_diagnostics.md §1). A misconception is a normalized, first-class belief record scoped to a learning object; error_events remain the raw per-attempt evidence and now carry a nullable link back to the registry row that normalized them.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/025_misconception_registry.sql`.
- **Schema touched by:** `025_misconception_registry.sql`, `047_compositional_misconceptions.sql`, `056_misconception_transitions.sql`, `115_causal_attribution_p0.sql`, `116_measurement_contract_corrections.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `concept_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `statement` | `TEXT` | yes | — | — | Stored value |
| `signature` | `TEXT` | no | — | — | Stored value |
| `facet_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `severity` | `REAL` | yes | `0` | — | Stored value |
| `status` | `TEXT` | yes | `'active'` | — | Stored value |
| `source_error_event_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `mechanism` | `TEXT` | no | — | — | Stored value |
| `operation` | `TEXT` | no | — | — | Stored value |
| `target_facet` | `TEXT` | no | — | — | Stored value |
| `confused_with_facet` | `TEXT` | no | — | — | Stored value |
| `trigger_conditions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `expected_signatures_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `first_divergence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `non_applicable_controls_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `promotion_reason` | `TEXT` | no | — | — | Stored value |
| `correction_statement` | `TEXT` | no | — | — | Stored value |
| `correction_source_span_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_misconceptions_target_facet` on `target_facet`.
- `idx_misconceptions_concept` on `concept_id`.
- `idx_misconceptions_lo_status` on `learning_object_id`, `status`.
- `sqlite_autoindex_misconceptions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_misconception_facet_ids()`
- `Repository.insert_misconception()`
- `Repository.misconception()`
- `Repository.misconceptions_for_concepts()`
- `Repository.misconceptions_for_learning_object()`
- `Repository.surfaced_belief_withdrawals()`
- `Repository.update_misconception()`

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

- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_cli_commands.py`
- `tests/test_codex_http_client.py`
- `tests/test_diagnostic_gate.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_guided_redo.py`
- `tests/test_hypothesis_sets.py`
- `tests/test_independent_group_counting.py`
- `tests/test_km4_taxonomy.py`
- `tests/test_migrations.py`
- `tests/test_misconception_registry.py`
- `tests/test_p2_acceptance.py`
- `tests/test_primed_attempts.py`
- `tests/test_scoreboard.py`
- `tests/test_self_attributed_misconceptions.py`
- `tests/test_sidecar_adjudication.py`
- `tests/test_simulation.py`
- `tests/test_structured_transport_parity.py`
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
CREATE TABLE misconceptions (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  concept_id TEXT,
  statement TEXT NOT NULL,
  signature TEXT,
  facet_ids_json TEXT,
  severity REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolving', 'resolved')),
  source_error_event_ids_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  resolved_at TEXT
, mechanism TEXT, operation TEXT, target_facet TEXT, confused_with_facet TEXT, trigger_conditions_json TEXT, expected_signatures_json TEXT, first_divergence_json TEXT, non_applicable_controls_json TEXT, promotion_reason TEXT, correction_statement TEXT, correction_source_span_ids_json TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
