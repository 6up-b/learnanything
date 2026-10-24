---
title: "judgment_ledger"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "40fbcac235d562ca079d4d342bf788123321b5c8"
source_commit_timestamp: "2026-10-24T14:22:21-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite judgment_ledger"
  - "table judgment_ledger"
schema_head: 218
table_name: "judgment_ledger"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "166_embedding_substrate_and_judgments.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/166_embedding_substrate_and_judgments.sql"
  - "src/learnloop/adaptive_difficulty/__init__.py"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/data_check.py"
  - "src/learnloop/adaptive_difficulty/feature_audit.py"
  - "src/learnloop/adaptive_difficulty/outside.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/reading.py"
  - "src/learnloop/adaptive_difficulty/relatedness.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `judgment_ledger`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives judgment ledger a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `supersedes_id`, `left_id`, `right_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/166_embedding_substrate_and_judgments.sql`.
- **Schema touched by:** `166_embedding_substrate_and_judgments.sql`, `168_activity_family_membership.sql`, `169_practice_index.sql`, `174_pf_generation.sql`, `175_decider_judgments_and_receipt_labels.sql`, `176_recurrence_groups.sql`, `182_learner_text_gaps.sql`, `183_facet_identity_actions.sql`, `197_facet_registry_saves.sql`, `202_router_staged_frame.sql`, `209_library_asks.sql`, `213_adaptive_difficulty_receipts.sql`, `214_adaptive_difficulty_serving.sql`, `215_reader_discovered_cues.sql`, `217_reader_reading_paths.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `supersedes_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `task` | `TEXT` | yes | — | — | Stored value |
| `left_kind` | `TEXT` | yes | — | — | Stored value |
| `left_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `right_kind` | `TEXT` | no | — | — | Stored value |
| `right_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `judge` | `TEXT` | yes | — | — | Stored value |
| `judge_model` | `TEXT` | no | — | — | Stored value |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `input_hash` | `TEXT` | yes | — | — | Stored value |
| `verdict` | `TEXT` | yes | — | — | Stored value |
| `score` | `REAL` | no | — | — | Stored value |
| `rationale` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `judgment_ledger_question` on `task`, `left_kind`, `left_id`, `right_kind`, `right_id`.
- `sqlite_autoindex_judgment_ledger_1` on `id` (unique).

Database triggers:

- `judgment_ledger_no_delete` — schema-enforced lifecycle or immutability constraint.
- `judgment_ledger_no_update` — schema-enforced lifecycle or immutability constraint.
- `judgment_ledger_validate_insert` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/data_check.py`
- `src/learnloop/ai/agreement.py`
- `src/learnloop/attempts/grading_support.py`
- `src/learnloop/attempts/stuck.py`
- `src/learnloop/cli/families.py`
- `src/learnloop/content/authoring/source_exercise_import.py`
- `src/learnloop/content/facet_identity/actions.py`
- `src/learnloop/content/facet_identity/judge.py`
- `src/learnloop/content/facet_identity/span_support.py`
- `src/learnloop/content/pipeline/add_source.py`
- `src/learnloop/content/pipeline/exam_marking.py`
- `src/learnloop/content/proposals/method_statement_judge.py`
- `src/learnloop/content/proposals/required_method_override.py`
- `src/learnloop/db/stores/families.py`
- `src/learnloop/db/stores/pf.py`
- `src/learnloop/db/stores/practice_index.py`
- `src/learnloop/db/stores/reader_cue_links.py`
- `src/learnloop/db/stores/recurrence.py`
- `src/learnloop/db/stores/source_service.py`
- `src/learnloop/decider_judgments.py`
- `src/learnloop/diagnosis/offline_review/links.py`
- `src/learnloop/diagnosis/offline_review/report.py`
- `src/learnloop/diagnosis/offline_review/runner.py`
- `src/learnloop/diagnosis/recurrence/guard.py`
- `src/learnloop/diagnosis/recurrence/report.py`
- `src/learnloop/diagnosis/split/jobs.py`
- `src/learnloop/diagnosis/split/reports.py`
- `src/learnloop/diagnosis/text_gaps/judges.py`
- `src/learnloop/diagnosis/text_gaps/pipeline.py`
- `src/learnloop/diagnosis/text_gaps/report.py`
- `src/learnloop/diagnosis/text_gaps/tier1.py`
- `src/learnloop/field/probability_prep.py`
- `src/learnloop/hints/map_builder.py`
- `src/learnloop/hints/map_report.py`
- `src/learnloop/hints/outcome.py`
- `src/learnloop/hints/report_adaptive.py`
- `src/learnloop/hints/report_workbench.py`
- `src/learnloop/hints/workbench.py`
- `src/learnloop/matching/judge.py`
- `src/learnloop/ops/contamination/judge.py`
- `src/learnloop/ops/contamination/report.py`
- `src/learnloop/ops/family_proposals.py`
- `src/learnloop/ops/graph_nomination_report.py`
- `src/learnloop/ops/pf_calls.py`
- `src/learnloop/ops/pf_publish.py`
- `src/learnloop/ops/pf_reports.py`
- `src/learnloop/placement/decisions.py`
- `src/learnloop/reader/reader_cues.py`
- `src/learnloop/reader/reader_intent.py`
- `src/learnloop/reader/reader_quick_check.py`
- `src/learnloop/source_retrieval/passage_cues.py`
- `src/learnloop/source_retrieval/reading_paths.py`
- `src/learnloop/source_retrieval/role_labeller.py`
- `src/learnloop/substrate/families.py`
- `src/learnloop/substrate/intervention_outcomes.py`
- `src/learnloop/workbench/help_outcomes.py`

### Direct SQL writers

- `src/learnloop/db/stores/judgments.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_fakes.py`
- `tests/approach_map_fakes.py`
- `tests/hint_fakes.py`
- `tests/passage_cue_fakes.py`
- `tests/recurrence_fakes.py`
- `tests/test_activity_families.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_fix_round4.py`
- `tests/test_ad1_fix_round5.py`
- `tests/test_ad1_fix_round6.py`
- `tests/test_ad1_fix_round9.py`
- `tests/test_ad1_outside_and_cli.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_ad1_send_guard.py`
- `tests/test_ad3_reading.py`
- `tests/test_ad3_relatedness.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_projection.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ai_compare.py`

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
CREATE TABLE "judgment_ledger" (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    supersedes_id TEXT REFERENCES judgment_ledger(id),
    task TEXT NOT NULL,
    left_kind TEXT NOT NULL,
    left_id TEXT NOT NULL,
    right_kind TEXT,
    right_id TEXT,
    judge TEXT NOT NULL CHECK(judge IN ('llm', 'verifier', 'owner', 'diagnoser', 'learner_card', 'exact_key', 'decider')),
    judge_model TEXT,
    prompt_version TEXT,
    input_hash TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score REAL,
    rationale TEXT NOT NULL,
    CHECK((right_kind IS NULL) = (right_id IS NULL)),
    CHECK(supersedes_id IS NULL OR supersedes_id != id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
