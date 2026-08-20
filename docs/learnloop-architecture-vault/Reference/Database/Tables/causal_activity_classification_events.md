---
title: "causal_activity_classification_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite causal_activity_classification_events"
  - "table causal_activity_classification_events"
schema_head: 156
table_name: "causal_activity_classification_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "122_causal_activity_events.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/122_causal_activity_events.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `causal_activity_classification_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of causal activity classification so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `policy_version`, `seq`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> P2 §4.2: causal activity classification becomes an append-only EVENT log.  Migration 121 gave `causal_activity_classifications` an `attempt_id` PRIMARY KEY, and the repository raised ValueError when a second writer disagreed. Two writers already exist on the attempt hot path (attempts.apply_attempt records `repair_activity` for a primed draft; probe_episodes records the diagnostic class), so a primed probe, a replay, or a backfill raised INSIDE attempt application. Conflicts are now recorded, not rejected: the current classification is derived by CONTAMINATION_PRECEDENCE (most contaminated wins) in services/causal_activity_policy.py.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/122_causal_activity_events.sql`.
- **Schema touched by:** `122_causal_activity_events.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `contamination_class` | `TEXT` | yes | — | — | Stored value |
| `near_clone` | `INTEGER` | yes | `0` | — | Stored value |
| `near_clone_basis` | `TEXT` | no | — | — | Stored value |
| `closes_pre_intervention_segment` | `INTEGER` | yes | `0` | — | Stored value |
| `eligible_for_fsrs` | `INTEGER` | yes | `0` | — | Stored value |
| `eligible_for_certification` | `INTEGER` | yes | `0` | — | Stored value |
| `source` | `TEXT` | yes | `'unknown'` | — | Stored value |
| `policy_version` | `TEXT` | yes | `'causal_activity_v1'` | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `causal_activity_classification_events_fact` on `attempt_id`, `source`, `contamination_class`, `near_clone` (unique).
- `causal_activity_classification_events_seq` on `attempt_id`, `seq` (unique).
- `sqlite_autoindex_causal_activity_classification_events_1` on `id` (unique).

Database triggers:

- `causal_activity_classification_events_no_delete` — schema-enforced lifecycle or immutability constraint.
- `causal_activity_classification_events_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.all_causal_activity_classifications()`
- `Repository.causal_activity_classification()`
- `Repository.causal_activity_classification_events()`
- `Repository.record_causal_activity_classification()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/substrate/canonical_projection.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_activity_policy.py`
- `tests/test_causal_repair_mapping_p2.py`
- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_probe_episodes.py`
- `tests/test_receipt_exactness.py`

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
CREATE TABLE causal_activity_classification_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  contamination_class TEXT NOT NULL CHECK (
    contamination_class IN (
      'pure_diagnostic',
      'instructional_diagnostic',
      'repair_activity',
      'verification'
    )
  ),
  near_clone INTEGER NOT NULL DEFAULT 0 CHECK (near_clone IN (0, 1)),
  near_clone_basis TEXT,
  closes_pre_intervention_segment INTEGER NOT NULL DEFAULT 0
    CHECK (closes_pre_intervention_segment IN (0, 1)),
  eligible_for_fsrs INTEGER NOT NULL DEFAULT 0 CHECK (eligible_for_fsrs IN (0, 1)),
  eligible_for_certification INTEGER NOT NULL DEFAULT 0
    CHECK (eligible_for_certification IN (0, 1)),
  source TEXT NOT NULL DEFAULT 'unknown',
  policy_version TEXT NOT NULL DEFAULT 'causal_activity_v1',
  detail_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
