---
title: "causal_hypotheses"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_hypotheses"
  - "table causal_hypotheses"
schema_head: 157
table_name: "causal_hypotheses"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "118_causal_attribution_p1.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/118_causal_attribution_p1.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
  - "src/learnloop/diagnosis/failure_triage.py"
  - "src/learnloop/diagnosis/probe_blocks.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/cli/app.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_hypotheses`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives causal hypothese a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `supersedes_id`, `attempt_id`, `error_event_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Causal-attribution P1 (§6.1): the single durable home for causal hypothesis statements.  Rows are immutable episode/version records; a changed interpretation appends a successor version instead of rewriting the observation that produced the earlier one.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/118_causal_attribution_p1.sql`.
- **Schema touched by:** `118_causal_attribution_p1.sql`, `119_causal_mechanism_taxonomy.sql`, `120_causal_projection_indexes.sql`, `121_causal_probe_coherence.sql`, `125_causal_repair_mapping_provenance.sql`, `126_diagnosis_adjudication.sql`, `133_causal_mechanism_repair_key.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `episode_key` | `TEXT` | yes | — | — | Stored value |
| `version` | `INTEGER` | yes | `1` | — | Stored value |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/causal_hypotheses\|causal_hypotheses.id]] | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `error_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `cause_scope` | `TEXT` | yes | — | — | Stored value |
| `statement` | `TEXT` | yes | — | — | Stored value |
| `statement_normalized` | `TEXT` | yes | — | — | Stored value |
| `mechanism` | `TEXT` | no | — | — | Stored value |
| `operation` | `TEXT` | no | — | — | Stored value |
| `target_ref_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `applicability_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `postdictive_claims_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `evidence_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `generation_agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `model` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `repair_class_basis` | `TEXT` | no | — | — | Stored value |
| `repair_class_unresolved_reason` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/causal_hypotheses|`causal_hypotheses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_hypotheses_repair_gap` on `learning_object_id`, `repair_class_unresolved_reason`.
- `idx_causal_hypotheses_projection` on `learning_object_id`, `statement_normalized`, `status`, `episode_key`, `version`.
- `idx_causal_hypotheses_operation` on `operation`.
- `idx_causal_hypotheses_statement` on `learning_object_id`, `statement_normalized`, `version`.
- `idx_causal_hypotheses_lo_status` on `learning_object_id`, `status`, `created_at`, `id`.
- `idx_causal_hypotheses_attempt` on `attempt_id`, `created_at`, `id`.
- `sqlite_autoindex_causal_hypotheses_2` on `episode_key`, `version` (unique).
- `sqlite_autoindex_causal_hypotheses_1` on `id` (unique).

Database triggers:

- `causal_hypotheses_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_hypotheses_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository._projected_causal_candidates()`
- `Repository.all_causal_hypotheses()`
- `Repository.append_causal_hypothesis()`
- `Repository.causal_hypotheses_for_attempt()`
- `Repository.causal_hypotheses_for_learning_object()`
- `Repository.causal_hypotheses_with_operations()`
- `Repository.causal_hypothesis()`
- `Repository.find_record()`
- `Repository.latest_causal_hypothesis_for_episode()`
- `Repository.open_unresolved_cause_factors()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/causal_probe_commissioning.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/diagnosis/guided_redo.py`
- `src/learnloop/diagnosis/probe_targeting.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/tutor/durable_promotion.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/knowledge_map.py`
- `src/learnloop_sidecar/handlers/measurement.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_repair_mapping_p2.py`
- `tests/test_causal_trace_consistency_p2.py`
- `tests/test_failure_triage_causal_gate.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_migration.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_probe_commissioning.py`
- `tests/test_causal_shadow_selection.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_km2_write_path.py`
- `tests/test_minimal_repair_selection_a1.py`

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
CREATE TABLE causal_hypotheses (
  id TEXT PRIMARY KEY,
  episode_key TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  supersedes_id TEXT REFERENCES causal_hypotheses(id),
  -- Goal-series rewind can remove post-checkpoint attempt projections. The
  -- causal audit row remains immutable, so this is an id reference rather
  -- than a cascading/restricting FK.
  attempt_id TEXT NOT NULL,
  -- Error events are replay-replaced in the legacy derived-state path. Keep
  -- their immutable identifier without an FK that would block that rebuild.
  error_event_id TEXT,
  learning_object_id TEXT NOT NULL,
  cause_scope TEXT NOT NULL CHECK (
    cause_scope IN (
      'learner_state',
      'transient_execution',
      'interaction_context',
      'item_contract',
      'grader_interpretation',
      'unknown'
    )
  ),
  statement TEXT NOT NULL CHECK (length(trim(statement)) > 0),
  statement_normalized TEXT NOT NULL,
  mechanism TEXT,
  operation TEXT,
  target_ref_json TEXT,
  applicability_json TEXT,
  postdictive_claims_json TEXT,
  evidence_json TEXT,
  repair_class_id TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('candidate', 'validated', 'retired', 'demoted', 'open_set')
  ),
  generation_agent_run_id TEXT,
  model TEXT,
  created_at TEXT NOT NULL, repair_class_basis TEXT, repair_class_unresolved_reason TEXT,
  UNIQUE(episode_key, version)
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
