---
title: "missing_vocabulary_notes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite missing_vocabulary_notes"
  - "table missing_vocabulary_notes"
schema_head: 157
table_name: "missing_vocabulary_notes"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "134_missing_vocabulary_notes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/134_missing_vocabulary_notes.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/missing_vocabulary.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `missing_vocabulary_notes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives missing vocabulary note a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It supplies replay-stable input rather than a disposable cache. Rows bind `learning_object_id`, `practice_item_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/134_missing_vocabulary_notes.sql`.
- **Schema touched by:** `134_missing_vocabulary_notes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `abstention_reason` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `error_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `criterion_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `trace_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `item_context_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `selected_repair_class_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `repair_equivalence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `grading_prompt_version` | `TEXT` | no | — | — | Stored value |
| `decision_policy_version` | `TEXT` | no | — | — | Stored value |
| `repair_policy_version` | `TEXT` | no | — | — | Stored value |
| `grader_model` | `TEXT` | no | — | — | Stored value |
| `grader_provider` | `TEXT` | no | — | — | Stored value |
| `grader_provider_revision` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `note_version` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_missing_vocabulary_notes_repair` on `repair_equivalence_id`, `created_at`.
- `idx_missing_vocabulary_notes_lo` on `learning_object_id`, `abstention_reason`, `created_at`.
- `idx_missing_vocabulary_notes_source` on `source`, `created_at`, `id`.
- `sqlite_autoindex_missing_vocabulary_notes_1` on `id` (unique).

Database triggers:

- `missing_vocabulary_notes_no_delete` — schema-enforced lifecycle or immutability constraint.
- `missing_vocabulary_notes_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.insert_missing_vocabulary_notes()`
- `Repository.missing_vocabulary_notes()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/missing_vocabulary.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_missing_vocabulary_notes.py`

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
CREATE TABLE missing_vocabulary_notes (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL CHECK (source IN (
    -- The diagnostician declined to name a cause (§2 A5).
    'diagnostic_abstention',
    -- An authored item declined to name canonical facets (§5.8 rule 4).
    'authoring_facet_abstention'
  )),
  -- The typed refusal itself. For diagnosis this is the grader's
  -- `abstention_reason`; for authoring it is the criterion's
  -- `measurement_status` (`no_canonical_facet` / `item_local`).
  abstention_reason TEXT NOT NULL,

  learning_object_id TEXT,
  practice_item_id TEXT,
  -- Present for the diagnostic arm; null for authoring, which abstains before
  -- any attempt exists.
  attempt_id TEXT,
  error_event_id TEXT,
  criterion_id TEXT,

  -- What could not be named: the learner work / divergence anchor for the
  -- diagnostic arm, the criterion text for the authoring arm.
  trace_json TEXT NOT NULL DEFAULT '{}',
  item_context_json TEXT NOT NULL DEFAULT '{}',

  -- The repair the episode selected despite the abstention. Phase D clusters by
  -- repair equivalence, so the cross-episode id (migration 133) is stored
  -- alongside the episode-scoped one.
  selected_repair_class_id TEXT,
  repair_equivalence_id TEXT,

  grading_prompt_version TEXT,
  decision_policy_version TEXT,
  repair_policy_version TEXT,
  grader_model TEXT,
  grader_provider TEXT,
  grader_provider_revision TEXT,
  agent_run_id TEXT,

  note_version TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
