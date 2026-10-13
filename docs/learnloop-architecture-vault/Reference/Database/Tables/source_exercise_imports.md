---
title: "source_exercise_imports"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ee3115d5879761a347e6e0fa2d57e889fd0d46ac"
source_commit_timestamp: "2026-10-13T10:46:27-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_exercise_imports"
  - "table source_exercise_imports"
schema_head: 192
table_name: "source_exercise_imports"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "185_source_exercise_imports.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/185_source_exercise_imports.sql"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/instructional/exposure.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_exercise_imports`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks each textbook exercise imported as practice (canonical sources S1): the caller and proposal, the exercise's extraction, spans and revision, the authored item, the answer-key ladder's status and label, any family attachment and the intervention need it fulfilled. Workflow state for the interactive import's time box and background check; certification reads the key through reference_key_checks. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `proposal_id`, `extraction_id`, `source_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Canonical sources S1 (spec_source_practice_and_probes_v1.md §7.5): textbook exercises as practice candidates, their answer-key checks, and the attempt-time certification gate for unverified keys (C3, §7.3a). One row per import of a source exercise: a paid output (authoring, the verifier ladder, the family judge) never re-run on rebuild. Workflow state: `status` moves authoring -> checking -> written | rejected | failed.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/185_source_exercise_imports.sql`.
- **Schema touched by:** `185_source_exercise_imports.sql`, `188_source_first_needs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `proposal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `label` | `TEXT` | no | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `content_hash` | `TEXT` | no | — | — | Stored value |
| `key_status` | `TEXT` | no | — | — | Stored value |
| `verification_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `validation_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `facet_basis` | `TEXT` | no | — | — | Stored value |
| `family_proposal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `caller` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `need_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_exercise_imports_region` on `extraction_id`, `created_at`.
- `idx_source_exercise_imports_item` on `practice_item_id`.
- `sqlite_autoindex_source_exercise_imports_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/content/authoring/source_exercise_import.py`
- `src/learnloop/db/stores/source_service.py`
- `src/learnloop/instructional/exposure.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_service.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_learner_pick_proposal.py`
- `tests/test_source_exercise_rpcs.py`

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
CREATE TABLE source_exercise_imports (
  id TEXT PRIMARY KEY,
  proposal_id TEXT,
  extraction_id TEXT NOT NULL,
  span_ids_json TEXT NOT NULL,
  source_id TEXT,
  revision_id TEXT,
  label TEXT,
  practice_item_id TEXT,
  -- reference_content_hash of the item as written (NULL until written).
  content_hash TEXT,
  key_status TEXT CHECK (key_status IS NULL OR key_status IN (
    'book_solution', 'checked', 'panel_agrees', 'panel_agrees_unconfirmed',
    'checking', 'model_answer', 'disputed'
  )),
  verification_json TEXT NOT NULL DEFAULT '{}',
  validation_json TEXT NOT NULL DEFAULT '{}',
  facet_basis TEXT CHECK (facet_basis IS NULL OR facet_basis IN ('authored', 'lo_fallback')),
  family_proposal_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('authoring', 'checking', 'written', 'rejected', 'failed')),
  reason TEXT,
  caller TEXT NOT NULL CHECK (caller IN ('learner', 'reader', 'harvest', 'need')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, need_id TEXT);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
