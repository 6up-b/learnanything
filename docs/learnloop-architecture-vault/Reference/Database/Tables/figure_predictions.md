---
title: "figure_predictions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "47d547fbf49615c63acfc293b37e60349d38119a"
source_commit_timestamp: "2026-10-27T10:26:00-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite figure_predictions"
  - "table figure_predictions"
schema_head: 225
table_name: "figure_predictions"
table_role: "raw_ledger"
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
  - "src/learnloop/reader/reader_observations.py"
  - "src/learnloop/reader/reader_report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `figure_predictions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records a learner's prediction on an explorable figure (reader workbench RW5a): the answer, the observed readout before and after the prediction's change, whether it matched (decided by code) and the optional "what changed?" line. Formative only: never an attempt or an evidence observation; a missed one is read by learner-text gaps as a `reader_formative` text and listed by "Last time here". Append-only by trigger, its one update setting `explanation_text` once. It supplies replay-stable input rather than a disposable cache. Rows bind `figure_id`, `extraction_id`, `prediction_index`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> figure_predictions (RAW_LEDGER): the learner's prediction on a figure, the observed before/after readout and whether it matched (decided by code), and the optional "what changed?" text. Formative (tier 2, W1): never an attempt, an evidence observation or a field signal; a missed one is read by learner-text gaps as a reader_formative text. extraction_id is the figure's source (RW6a's "Last time here" reads it). Append-only: a row is never deleted, and the only update sets explanation_text once.

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/216_interactive_figures.sql`.
- **Schema touched by:** `216_interactive_figures.sql`, `224_figure_requests.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `figure_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/interactive_figures\|interactive_figures.id]] | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `prediction_index` | `INTEGER` | yes | — | — | Stored value |
| `learner_answer` | `TEXT` | yes | — | — | Stored value |
| `observed_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `matched` | `INTEGER` | yes | — | — | Stored value |
| `explanation_text` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `figure_id` → [[Reference/Database/Tables/interactive_figures|`interactive_figures.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_figure_predictions_extraction` on `extraction_id`, `created_at`.
- `sqlite_autoindex_figure_predictions_2` on `figure_id`, `prediction_index` (unique).
- `sqlite_autoindex_figure_predictions_1` on `id` (unique).

Database triggers:

- `figure_predictions_explanation_once` — schema-enforced lifecycle or immutability constraint.
- `figure_predictions_no_delete` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/figures.py`
- `src/learnloop/diagnosis/text_gaps/provenance.py`
- `src/learnloop/diagnosis/text_gaps/sources.py`
- `src/learnloop/reader/reader_observations.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/figures.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_figure_predictions.py`
- `tests/test_figure_requests_migration.py`
- `tests/test_figures_migration.py`
- `tests/test_figures_rpc.py`
- `tests/test_figures_switch_off.py`

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
CREATE TABLE figure_predictions (
  id TEXT PRIMARY KEY,
  figure_id TEXT NOT NULL REFERENCES interactive_figures(id),
  extraction_id TEXT NOT NULL,
  prediction_index INTEGER NOT NULL CHECK (prediction_index >= 0),
  learner_answer TEXT NOT NULL,
  observed_json TEXT NOT NULL,
  matched INTEGER NOT NULL CHECK (matched IN (0, 1)),
  explanation_text TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (figure_id, prediction_index)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
