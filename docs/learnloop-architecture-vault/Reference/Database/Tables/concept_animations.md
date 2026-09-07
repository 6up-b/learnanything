---
title: "concept_animations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite concept_animations"
  - "table concept_animations"
schema_head: 157
table_name: "concept_animations"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "114_concept_animations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/114_concept_animations.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/concept_animation.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop_sidecar/handlers/animation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `concept_animations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks requested and rendered concept-animation artifacts. It supplies replay-stable input rather than a disposable cache. Rows bind `concept_id`, `learning_object_id`, `batch_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> AI-generated Manim explainer animations (spec_fork_features §2). One row per generation request: the durable status machine, the candidate scene code (kept on failure for debugging, with a capped stderr tail), provenance of the authoring model, and the content-addressed mp4 once rendered. Videos live at media/animations/sha256-<hex>.mp4 under the vault root and are served over the llmedia:// scheme — bytes never cross the RPC channel.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/114_concept_animations.sql`.
- **Schema touched by:** `114_concept_animations.sql`, `157_concept_animation_renderer.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `concept_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `scene_code` | `TEXT` | no | — | — | Stored value |
| `scene_class` | `TEXT` | no | — | — | Stored value |
| `title` | `TEXT` | no | — | — | Stored value |
| `narration_md` | `TEXT` | no | — | — | Stored value |
| `video_hash` | `TEXT` | no | — | — | Stored value |
| `video_file_name` | `TEXT` | no | — | — | Stored value |
| `duration_seconds` | `REAL` | no | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `quality` | `TEXT` | no | — | — | Stored value |
| `repair_attempted` | `INTEGER` | yes | `0` | — | Stored value |
| `failure_stage` | `TEXT` | no | — | — | Stored value |
| `failure_reason` | `TEXT` | no | — | — | Stored value |
| `render_stderr` | `TEXT` | no | — | — | Stored value |
| `batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `renderer` | `TEXT` | yes | `'manim'` | — | Stored value |
| `storyboard_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `video_job_ids` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_concept_animations_concept` on `concept_id`, `status`, `created_at`.
- `sqlite_autoindex_concept_animations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.concept_animation()`
- `Repository.concept_animations_for_concept()`
- `Repository.insert_concept_animation()`
- `Repository.pending_concept_animations()`
- `Repository.update_concept_animation()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/concept_animation.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop_sidecar/handlers/animation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_concept_animation_service.py`
- `tests/test_concept_animation_store.py`
- `tests/test_sidecar_animation.py`

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
CREATE TABLE concept_animations (
  id TEXT PRIMARY KEY,
  concept_id TEXT NOT NULL,
  learning_object_id TEXT,
  status TEXT NOT NULL CHECK (
    status IN ('queued', 'generating', 'validating', 'rendering', 'completed', 'failed', 'cancelled')
  ),
  scene_code TEXT,
  scene_class TEXT,
  title TEXT,
  narration_md TEXT,
  video_hash TEXT,
  video_file_name TEXT,
  duration_seconds REAL,
  provider TEXT,
  model TEXT,
  prompt_version TEXT,
  quality TEXT,
  repair_attempted INTEGER NOT NULL DEFAULT 0,
  failure_stage TEXT,
  failure_reason TEXT,
  render_stderr TEXT,
  batch_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
, renderer TEXT NOT NULL DEFAULT 'manim', storyboard_json TEXT, video_job_ids TEXT);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
