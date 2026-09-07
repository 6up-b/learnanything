---
title: "misconception_candidates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite misconception_candidates"
  - "table misconception_candidates"
schema_head: 157
table_name: "misconception_candidates"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "047_compositional_misconceptions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/047_compositional_misconceptions.sql"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/error_hunt.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `misconception_candidates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds candidates for misconception while policy selects or reviews one so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learning_object_id`, `concept_id`, `promoted_misconception_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10.3 promotion discipline: under mvp-0.7 a one-off ambiguous failure does NOT mint a durable misconception. The candidate belief stays here as a distribution over surfaces/events until a promotion condition is met (repeats on an independent surface / high-confidence first-error trace / contrast probe reproduces the predicted signature / maps to a validated registry belief), at which point a durable `misconceptions` row is inserted and linked back. `status` is app-validated (candidate | promoted); no SQL CHECK so it stays extensible without the table-rebuild dance.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/047_compositional_misconceptions.sql`.
- **Schema touched by:** `047_compositional_misconceptions.sql`, `115_causal_attribution_p0.sql`, `143_instrument_classes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `concept_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `statement` | `TEXT` | yes | — | — | Stored value |
| `statement_normalized` | `TEXT` | yes | — | — | Stored value |
| `signature` | `TEXT` | no | — | — | Stored value |
| `mechanism` | `TEXT` | no | — | — | Stored value |
| `operation` | `TEXT` | no | — | — | Stored value |
| `target_facet` | `TEXT` | no | — | — | Stored value |
| `confused_with_facet` | `TEXT` | no | — | — | Stored value |
| `facet_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `source_error_event_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `surface_families_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `item_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `occurrence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `severity` | `REAL` | yes | `0` | — | Stored value |
| `status` | `TEXT` | yes | `'candidate'` | — | Stored value |
| `promoted_misconception_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `promotion_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_misconception_candidates_norm` on `learning_object_id`, `statement_normalized`.
- `idx_misconception_candidates_lo_status` on `learning_object_id`, `status`.
- `sqlite_autoindex_misconception_candidates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_misconception_candidate()`
- `Repository.misconception_candidate_by_id()`
- `Repository.misconception_candidate_by_normalized()`
- `Repository.misconception_candidates_for_learning_object()`
- `Repository.update_misconception_candidate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_factor_deferral.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/error_hunt.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/learner/independence_audit.py`
- `src/learnloop/tutor/durable_promotion.py`
- `src/learnloop_sidecar/handlers/remediation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_error_hunt_items.py`
- `tests/test_km4_taxonomy.py`

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
CREATE TABLE misconception_candidates (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  concept_id TEXT,
  statement TEXT NOT NULL,
  statement_normalized TEXT NOT NULL,
  signature TEXT,
  mechanism TEXT,
  operation TEXT,
  target_facet TEXT,
  confused_with_facet TEXT,
  facet_ids_json TEXT,
  source_error_event_ids_json TEXT,
  surface_families_json TEXT,
  item_ids_json TEXT,
  occurrence_count INTEGER NOT NULL DEFAULT 0,
  severity REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'candidate',
  promoted_misconception_id TEXT,
  promotion_reason TEXT,
  created_at TEXT,
  updated_at TEXT
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
