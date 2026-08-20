---
title: "causal_blind_prediction_bundles"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_blind_prediction_bundles"
  - "table causal_blind_prediction_bundles"
schema_head: 156
table_name: "causal_blind_prediction_bundles"
table_role: "receipt"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "121_causal_probe_coherence.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/121_causal_probe_coherence.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_blind_prediction_bundles`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives causal blind prediction bundle a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `hypothesis_id`, `practice_item_id`, `generation_agent_run_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Causal-attribution P2 (§7): immutable blind predictions, shared manipulation audits, a review ladder for generated probes, explicit contamination eligibility, and delayed cold-verification receipts.  These records attach to the P1 causal-hypothesis home by id; they never copy mutable hypothesis prose.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/121_causal_probe_coherence.sql`.
- **Schema touched by:** `121_causal_probe_coherence.sql`, `123_causal_prior_basis.sql`, `140_causal_probe_blind_input_contract.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `hypothesis_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/causal_hypotheses\|causal_hypotheses.id]] | Stored value |
| `hypothesis_version` | `INTEGER` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `predictions_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `generated_without_observation` | `INTEGER` | yes | `1` | — | Stored value |
| `model_revision` | `TEXT` | yes | — | — | Stored value |
| `outcome_schema_version` | `TEXT` | yes | — | — | Stored value |
| `generation_agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `blind_input_contract_version` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `hypothesis_id` → [[Reference/Database/Tables/causal_hypotheses|`causal_hypotheses.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_causal_blind_prediction_item` on `practice_item_id`, `hypothesis_id`, `created_at`.
- `sqlite_autoindex_causal_blind_prediction_bundles_1` on `id` (unique).

Database triggers:

- `causal_blind_prediction_bundles_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_blind_prediction_bundles_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_blind_prediction_bundle()`
- `Repository.causal_blind_prediction_bundles()`
- `Repository.insert_causal_blind_prediction_bundle()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_diagnostic_selector.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p2.py`

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
CREATE TABLE causal_blind_prediction_bundles (
  id TEXT PRIMARY KEY,
  hypothesis_id TEXT NOT NULL REFERENCES causal_hypotheses(id),
  hypothesis_version INTEGER NOT NULL CHECK (hypothesis_version >= 1),
  practice_item_id TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  predictions_json TEXT NOT NULL,
  generated_without_observation INTEGER NOT NULL DEFAULT 1
    CHECK (generated_without_observation = 1),
  model_revision TEXT NOT NULL CHECK (length(trim(model_revision)) > 0),
  outcome_schema_version TEXT NOT NULL
    CHECK (length(trim(outcome_schema_version)) > 0),
  generation_agent_run_id TEXT,
  created_at TEXT NOT NULL
  -- No UNIQUE over the blind input.  `id` is the content hash of (hypothesis,
  -- version, item, input_hash, predictions, cohort), so the primary key already
  -- dedupes an identical regeneration exactly.  A UNIQUE over the input alone
  -- instead forbids recording a SECOND, differing sample from the same blind
  -- input -- and INSERT OR IGNORE would drop it silently.  Recording every
  -- sample is the case this append-only substrate exists to support: a probe is
  -- classified against the bundle ids PINNED when it was minted, never against
  -- whichever bundle happens to be newest.
, blind_input_contract_version TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
