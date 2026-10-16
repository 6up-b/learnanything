---
title: "retrieval_interventions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "495c7437f178f8517038fe9a1bfc85db7da29664"
source_commit_timestamp: "2026-10-15T23:28:03-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite retrieval_interventions"
  - "table retrieval_interventions"
schema_head: 206
table_name: "retrieval_interventions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "193_retrieval_interventions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/193_retrieval_interventions.sql"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/instructional/interventions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `retrieval_interventions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Appends one row when a retrieved asset is shown or served (canonical sources S5): a cited or opened passage, a comparison shown, ranked remediation passages delivered, a proposal picked, a need fulfilled from the sources and served. References only (assets with revisions, targets, the valuation's state hashes, the valued candidate's predicted outcome distribution and minutes, impressions, the independence verdict at valuation and serving time); reports read it, nothing serves from it. It supplies replay-stable input rather than a disposable cache. Rows bind `tool_call_id`, `proposal_id`, `question_event_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Canonical sources S5 (spec_source_practice_and_probes_v1.md §11): retrieval in the evidence loop, reports only. Nothing reads these tables to serve. One row when a retrieved asset is SHOWN or SERVED (never when it is merely retrieved): a passage offer opened or a tutor answer citing retrieved spans, a remediation passage delivered, a comparison shown, a proposal picked, an imported source exercise served, a need fulfilled from the sources and served. Append-only facts (RAW_LEDGER): references, not copies.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/193_retrieval_interventions.sql`.
- **Schema touched by:** `193_retrieval_interventions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `caller_kind` | `TEXT` | no | — | — | Stored value |
| `caller_ref` | `TEXT` | no | — | — | Stored value |
| `intent` | `TEXT` | no | — | — | Stored value |
| `policy` | `TEXT` | no | — | — | Stored value |
| `tool_call_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `proposal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `question_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `router_decision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `assets_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `targets_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `state_ref_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `valuation_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `exposure_event_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `impression_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `reading_exposure_label` | `TEXT` | no | — | — | Stored value |
| `eligibility_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `seconds_since_related_exposure` | `REAL` | no | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `algorithm_version` | `TEXT` | no | — | — | Stored value |
| `design` | `TEXT` | no | — | — | Stored value |
| `seed` | `TEXT` | no | — | — | Stored value |
| `propensity` | `REAL` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_retrieval_interventions_proposal` on `proposal_id`.
- `idx_retrieval_interventions_created` on `created_at`.
- `sqlite_autoindex_retrieval_interventions_1` on `id` (unique).

Database triggers:

- `retrieval_interventions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `retrieval_interventions_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/source_service.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE retrieval_interventions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('source_passage', 'source_exercise', 'practice_pick', 'comparison',
                                     'remediation_passage')),
  caller_kind TEXT,
  caller_ref TEXT,
  intent TEXT,
  policy TEXT,
  tool_call_id TEXT,
  proposal_id TEXT,
  question_event_id TEXT,
  remediation_episode_id TEXT,
  -- R1's learner_pick row for the pick, when the router_decisions table exists.
  router_decision_id TEXT,
  assets_json TEXT NOT NULL DEFAULT '{}',
  targets_json TEXT NOT NULL DEFAULT '{}',
  state_ref_json TEXT NOT NULL DEFAULT '{}',
  -- A valued check: predicted EIG/EVSI, the likelihood regime and basis, the
  -- predicted outcome distribution P(E) and the predicted minutes.
  valuation_json TEXT,
  exposure_event_ids_json TEXT NOT NULL DEFAULT '[]',
  impression_ids_json TEXT NOT NULL DEFAULT '[]',
  reading_exposure_label TEXT,
  -- The independence verdict at valuation time and again at serving time.
  eligibility_json TEXT,
  seconds_since_related_exposure REAL,
  session_id TEXT,
  attempt_id TEXT,
  algorithm_version TEXT,
  -- Reserved; randomization is deferred (spec §19). NULL in v1.
  design TEXT,
  seed TEXT,
  propensity REAL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
