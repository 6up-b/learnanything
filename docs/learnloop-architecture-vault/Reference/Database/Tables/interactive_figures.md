---
title: "interactive_figures"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "423464b380cd6dd56b564ec186dadd50a539c6f5"
source_commit_timestamp: "2026-10-27T17:45:05-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite interactive_figures"
  - "table interactive_figures"
schema_head: 226
table_name: "interactive_figures"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "216_interactive_figures.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/216_interactive_figures.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/figures.py"
  - "src/learnloop/diagnosis/text_gaps/provenance.py"
  - "src/learnloop/diagnosis/text_gaps/sources.py"
  - "src/learnloop/figure_admission.py"
  - "src/learnloop/figures/service.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `interactive_figures`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Keeps each explorable figure version the Reader built (reader workbench RW5a): the declarative figure spec the figure author wrote (never code), what was asked for (the selection, a region of a figure and the block whose crop was sent), how it verified (verified, illustrative, failed or unsupported, with the report) and the reuse key (`input_hash`); a "not right?" version supersedes an earlier one, which is kept. Paid output: never re-run on rebuild, and nothing that grades, schedules or projects reads it. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `asset_id`, `supersedes_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8.5, §11; docs/reviews/reader-workbench-RW5a.md). Numbered 216: AD2+AD3 hold 214 and RW3b 215 (the runner is set-based, so a gap is fine).  interactive_figures (WORKFLOW): one row per built figure version, a paid output never re-run on rebuild. The declarative spec (InteractiveFigureSpecV1, never code), what was asked for (the selection, a figure region, the cropped block, every span sent), how it verified (verified | illustrative | failed | unsupported, with the report), and the reuse key (input_hash). A "not right?" version supersedes an earlier one (supersedes_id, with the learner's revision_note); the earlier one is kept. Replay, rebuild and every scoring, scheduling, projection or serving path never read it.

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/216_interactive_figures.sql`.
- **Schema touched by:** `216_interactive_figures.sql`, `224_figure_requests.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `region_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `asset_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `input_span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/interactive_figures\|interactive_figures.id]] | Stored value |
| `revision_note` | `TEXT` | no | — | — | Stored value |
| `spec_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `spec_version` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | no | — | — | Stored value |
| `verification` | `TEXT` | yes | — | — | Stored value |
| `verification_report_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `unsupported_kind` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `request_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/figure_requests\|figure_requests.id]] | Stored value |
| `goal_text` | `TEXT` | no | — | — | Stored value |
| `grounding` | `TEXT` | yes | `'anchor'` | — | Stored value |
| `input_span_keys_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `tier` | `TEXT` | yes | `'grammar'` | — | Stored value |
| `program_version` | `TEXT` | no | — | — | Stored value |
| `engine_sha256` | `TEXT` | no | — | — | Stored value |
| `runtime_digest` | `TEXT` | no | — | — | Stored value |
| `instrumented_sha256` | `TEXT` | no | — | — | Stored value |
| `media_file_name` | `TEXT` | no | — | — | Stored value |
| `fuller_of_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/interactive_figures\|interactive_figures.id]] | Stored value |
| `checks_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `fuller_of_id` → [[Reference/Database/Tables/interactive_figures|`interactive_figures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `request_id` → [[Reference/Database/Tables/figure_requests|`figure_requests.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `supersedes_id` → [[Reference/Database/Tables/interactive_figures|`interactive_figures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_interactive_figures_request` on `request_id`.
- `idx_interactive_figures_reuse` on `input_hash`, `spec_version` (unique).
- `idx_interactive_figures_supersedes` on `supersedes_id`.
- `idx_interactive_figures_input` on `input_hash`, `created_at`.
- `idx_interactive_figures_extraction` on `extraction_id`, `created_at`.
- `sqlite_autoindex_interactive_figures_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/figures.py`
- `src/learnloop/diagnosis/text_gaps/provenance.py`
- `src/learnloop/diagnosis/text_gaps/sources.py`
- `src/learnloop/figure_admission.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/figures.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_figure_offers.py`
- `tests/test_figure_region.py`
- `tests/test_figure_requests_migration.py`
- `tests/test_figure_revisions.py`
- `tests/test_figure_verification.py`
- `tests/test_figures_codex_review.py`
- `tests/test_figures_final_round.py`
- `tests/test_figures_fix_round2.py`
- `tests/test_figures_migration.py`
- `tests/test_figures_rpc.py`
- `tests/test_figures_rw5b_review.py`
- `tests/test_figures_scope_redesign.py`
- `tests/test_figures_show_me.py`
- `tests/test_figures_show_me_codex_review.py`
- `tests/test_figures_switch_off.py`
- `tests/test_section_coverage_migration.py`

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
CREATE TABLE "interactive_figures" (
  id TEXT PRIMARY KEY,
  extraction_id TEXT,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  region_json TEXT,
  asset_id TEXT,
  input_span_ids_json TEXT NOT NULL DEFAULT '[]',
  origin TEXT NOT NULL CHECK (origin IN ('selection', 'library', 'tutor', 'show_me', 'ask', 'teacher', 'prefetch')),
  supersedes_id TEXT REFERENCES interactive_figures(id),
  revision_note TEXT,
  spec_json TEXT,
  spec_version TEXT NOT NULL,
  kind TEXT CHECK (kind IS NULL OR kind IN ('reconstructed', 'illustrative')),
  verification TEXT NOT NULL CHECK (verification IN ('verified', 'illustrative', 'failed', 'unsupported')),
  verification_report_json TEXT NOT NULL DEFAULT '{}',
  unsupported_kind TEXT,
  model TEXT,
  prompt_version TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  request_id TEXT REFERENCES figure_requests(id),
  goal_text TEXT,
  grounding TEXT NOT NULL DEFAULT 'anchor' CHECK (grounding IN ('anchor', 'retrieved', 'none')),
  input_span_keys_json TEXT NOT NULL DEFAULT '[]',
  tier TEXT NOT NULL DEFAULT 'grammar' CHECK (tier IN ('grammar', 'sketch', 'js_animation', 'manim')),
  program_version TEXT,
  engine_sha256 TEXT,
  runtime_digest TEXT,
  instrumented_sha256 TEXT,
  media_file_name TEXT,
  fuller_of_id TEXT REFERENCES interactive_figures(id),
  checks_json TEXT NOT NULL DEFAULT '[]',
  CHECK (verification NOT IN ('verified', 'illustrative') OR (spec_json IS NOT NULL AND kind IS NOT NULL)),
  CHECK (verification != 'verified' OR kind = 'reconstructed'),
  CHECK (supersedes_id IS NULL OR supersedes_id != id),
  CHECK (extraction_id IS NOT NULL OR request_id IS NOT NULL),
  CHECK (fuller_of_id IS NULL OR fuller_of_id != id)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
