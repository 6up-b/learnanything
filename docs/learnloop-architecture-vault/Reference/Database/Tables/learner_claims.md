---
title: "learner_claims"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite learner_claims"
  - "table learner_claims"
schema_head: 156
table_name: "learner_claims"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/learner/learner_profile.py"
  - "src/learnloop/learner/mastery.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/content/authoring/rung_variants.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_claims`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores learner-supplied prior claims, including the optional initialization-wizard claim. It supplies replay-stable input rather than a disposable cache. Rows bind `scope_id`, `claim_type`, `scope_type`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `027_question_promotions.sql`, `109_rung_variant_claim_source.sql`, `112_learner_report_claim_source.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `claim_type` | `TEXT` | yes | — | — | Stored value |
| `scope_type` | `TEXT` | yes | — | — | Stored value |
| `scope_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `evidence_family` | `TEXT` | no | — | — | Stored value |
| `claimed_level` | `REAL` | yes | — | — | Stored value |
| `prior_pseudo_count` | `REAL` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_learner_claims_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_learner_claims()`
- `Repository.find_record()`
- `Repository.insert_learner_claim()`
- `Repository.learner_claims()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/learner/learner_profile.py`
- `src/learnloop/learner/mastery.py`
- `src/learnloop/sim/diagnostic_validation.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_init.py`
- `tests/test_question_promotions.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_agent_runs.py`
- `tests/test_anti_double_count.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_graph_correction.py`
- `tests/test_measurement_state_labels.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`
- `tests/test_state_sync.py`
- `tests/test_tutor_promotion_w2.py`

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
CREATE TABLE "learner_claims" (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL CHECK (
    claim_type IN ('background_familiarity', 'prior_coursework', 'self_rating')
  ),
  scope_type TEXT NOT NULL CHECK (
    scope_type IN ('concept', 'learning_object', 'subject', 'domain', 'global')
  ),
  scope_id TEXT,
  evidence_family TEXT,
  claimed_level REAL NOT NULL CHECK (claimed_level >= 0.0 AND claimed_level <= 1.0),
  prior_pseudo_count REAL NOT NULL CHECK (prior_pseudo_count >= 0.0),
  source TEXT NOT NULL CHECK (
    source IN (
      'init_wizard', 'manual_cli', 'imported', 'tutor_gap_declaration',
      'rung_variant_request', 'learner_report'
    )
  ),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
