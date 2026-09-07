---
title: "causal_discriminating_observations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_discriminating_observations"
  - "table causal_discriminating_observations"
schema_head: 157
table_name: "causal_discriminating_observations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "130_causal_discriminating_observations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/130_causal_discriminating_observations.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_commissioning.py"
  - "src/learnloop/diagnosis/failure_triage.py"
  - "src/learnloop/diagnosis/scoreboard.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_discriminating_observations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records observations used to evaluate causal discriminating so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `factor_id`, `attempt_id`, `probe_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/130_causal_discriminating_observations.sql`.
- **Schema touched by:** `130_causal_discriminating_observations.sql`, `155_observation_admissibility.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `factor_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `probe_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `presentation_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `hypothesis_set_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `blind_bundle_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `outcome` | `TEXT` | yes | — | — | Stored value |
| `classified_as_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `supports_open_set` | `INTEGER` | yes | — | — | Stored value |
| `feature_source` | `TEXT` | yes | — | — | Stored value |
| `observed_features_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `declared_keys_observed` | `INTEGER` | yes | — | — | Stored value |
| `admitted` | `INTEGER` | yes | — | — | Stored value |
| `admission_reason` | `TEXT` | yes | — | — | Stored value |
| `support_authority` | `TEXT` | no | — | — | Stored value |
| `support_scores_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `resolved_factor` | `INTEGER` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `decision_policy_version` | `TEXT` | yes | — | — | Stored value |
| `formula_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `channel` | `TEXT` | no | — | — | Stored value |
| `admissible_as_independent` | `INTEGER` | no | — | — | Stored value |
| `inadmissibility_reason` | `TEXT` | no | — | — | Stored value |
| `contaminating_reveal_event_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_causal_discriminating_observation_channel` on `channel`, `created_at`, `id`.
- `idx_causal_discriminating_observation_presentation` on `presentation_id`, `created_at`, `id`.
- `idx_causal_discriminating_observation_attempt` on `attempt_id`, `created_at`, `id`.
- `idx_causal_discriminating_observation_factor` on `factor_id`, `created_at`, `id`.
- `sqlite_autoindex_causal_discriminating_observations_1` on `id` (unique).

Database triggers:

- `causal_discriminating_observations_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_discriminating_observations_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.causal_discriminating_observation()`
- `Repository.causal_discriminating_observations()`
- `Repository.insert_causal_discriminating_observation()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_health.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/diagnosis/scoreboard.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_probe_commissioning.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_failure_triage_causal_gate.py`
- `tests/test_scoreboard.py`

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
CREATE TABLE causal_discriminating_observations (
  id TEXT PRIMARY KEY,

  factor_id TEXT NOT NULL,
  -- The attempt whose DIAGNOSIS this observation bears on (the factor's own
  -- attempt), not the attempt that answered the probe.  `failure_triage` keys
  -- its causal-support overlay on this.
  attempt_id TEXT,
  -- The attempt that ANSWERED the probe, when one exists.  Null for an
  -- out-of-band classification (a replayed transcript, an adjudicated review).
  probe_attempt_id TEXT,

  presentation_id TEXT NOT NULL,
  hypothesis_set_id TEXT NOT NULL,
  candidate_id TEXT,
  -- The bundle ids PINNED at presentation time.  Recording them makes the row
  -- replayable: the append-only bundle substrate guarantees the same ids
  -- resolve to the same predictions forever.
  blind_bundle_ids_json TEXT NOT NULL,

  outcome TEXT NOT NULL CHECK (outcome IN (
    'matched_single',
    'matched_multiple',
    'no_bundle_matched',
    'all_bundles_matched',
    'cohort_mismatch',
    'unparsed_features'
  )),
  classified_as_json TEXT NOT NULL,
  supports_open_set INTEGER NOT NULL CHECK (supports_open_set IN (0, 1)),

  -- Where the observed feature vector came from.  `unknown` is the fail-closed
  -- default and is deliberately representable: a sensor that cannot say what it
  -- is must not be silently promoted to a deterministic one.
  feature_source TEXT NOT NULL CHECK (feature_source IN (
    'deterministic',
    'model_extracted',
    'learner_declared',
    'unknown'
  )),
  observed_features_json TEXT NOT NULL,
  -- Whether the observation covered every declared key of the bundles it was
  -- matched against.  An exact-key matcher reports "no bundle matched" both
  -- when the declared feature was measured and differed AND when it was never
  -- measured at all; only the first is open-set evidence.
  declared_keys_observed INTEGER NOT NULL CHECK (declared_keys_observed IN (0, 1)),

  admitted INTEGER NOT NULL CHECK (admitted IN (0, 1)),
  admission_reason TEXT NOT NULL,
  support_authority TEXT,
  support_scores_json TEXT NOT NULL,
  resolved_factor INTEGER NOT NULL CHECK (resolved_factor IN (0, 1)),

  detail_json TEXT NOT NULL,
  decision_policy_version TEXT NOT NULL,
  formula_version TEXT NOT NULL,
  created_at TEXT NOT NULL, channel TEXT, admissible_as_independent INTEGER, inadmissibility_reason TEXT, contaminating_reveal_event_id TEXT,

  -- An unadmitted observation grants no authority and resolves nothing.
  CHECK (admitted = 1 OR (support_authority IS NULL AND resolved_factor = 0))
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
