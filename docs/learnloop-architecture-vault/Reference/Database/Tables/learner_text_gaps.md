---
title: "learner_text_gaps"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "2954a443a3e8d5db528ffc0f1fa00d4fe44c4177"
source_commit_timestamp: "2026-10-16T04:23:47-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite learner_text_gaps"
  - "table learner_text_gaps"
schema_head: 206
table_name: "learner_text_gaps"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "182_learner_text_gaps.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/182_learner_text_gaps.sql"
  - "src/learnloop/ai/disclosures.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/cli/gaps.py"
  - "src/learnloop/cli/probability_arms.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/daily_plan/router_card.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `learner_text_gaps`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives learner text gap a stable database identity so learner-facing mastery and capability decisions use a reproducible evidence projection. It supplies replay-stable input rather than a disposable cache. Rows bind `source_id`, `attempt_id`, `practice_item_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/182_learner_text_gaps.sql`.
- **Schema touched by:** `182_learner_text_gaps.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_kind` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `anchor_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_text` | `TEXT` | yes | — | — | Stored value |
| `chooser` | `TEXT` | yes | — | — | Stored value |
| `context_judge` | `TEXT` | yes | — | — | Stored value |
| `context_kind` | `TEXT` | no | — | — | Stored value |
| `decider_kind` | `TEXT` | no | — | — | Stored value |
| `decider_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `named_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `action` | `TEXT` | yes | — | — | Stored value |
| `target_kind` | `TEXT` | no | — | — | Stored value |
| `target_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `match_basis` | `TEXT` | no | — | — | Stored value |
| `edge_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_concept_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `seed_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `seed_status` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `pipeline_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `learner_text_gaps_created_lo` on `created_learning_object_id`.
- `learner_text_gaps_target` on `target_kind`, `target_id`.
- `learner_text_gaps_created` on `created_at`, `id`.
- `sqlite_autoindex_learner_text_gaps_2` on `source_kind`, `source_id` (unique).
- `sqlite_autoindex_learner_text_gaps_1` on `id` (unique).

Database triggers:

- `learner_text_gaps_no_delete` — schema-enforced lifecycle or immutability constraint.
- `learner_text_gaps_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/router_card.py`
- `src/learnloop/db/stores/learner_gaps.py`
- `src/learnloop/diagnosis/split/history.py`
- `src/learnloop/field/signals.py`
- `src/learnloop/learner_context.py`

### Direct SQL writers

- `src/learnloop/db/stores/learner_gaps.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/mcp_world.py`
- `tests/test_decider_landing.py`
- `tests/test_hypothesis_reference_contract.py`
- `tests/test_learner_text_gaps.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_learner_text_gaps_flow.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_learner_text_gaps_review.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_tools.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_probability_cli.py`
- `tests/test_tier1_decider.py`

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
CREATE TABLE learner_text_gaps (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK (source_kind IN ('tutor_question', 'stuck_answer', 'diagnosis')),
  -- question_events.id | practice_attempts.id | attempt_diagnoses.id
  source_id TEXT NOT NULL,
  attempt_id TEXT,
  practice_item_id TEXT,
  -- The LO the text is about (the item's LO, a note's single related LO).
  anchor_learning_object_id TEXT,
  -- The asking item's subject: every target is grounded in it.
  subject_id TEXT,
  learner_text TEXT NOT NULL,
  chooser TEXT NOT NULL CHECK (chooser IN ('context_model', 'decider')),
  -- Who read it in context: the tutor, the diagnoser, or the stuck-text reader.
  context_judge TEXT NOT NULL CHECK (context_judge IN ('tutor', 'diagnoser', 'gap_reader')),
  context_kind TEXT,
  decider_kind TEXT,
  decider_json TEXT NOT NULL DEFAULT '{}',
  kind TEXT NOT NULL CHECK (kind IN ('prerequisite', 'misconception', 'slip', 'wording', 'none', 'unread')),
  named_json TEXT NOT NULL DEFAULT '{}',
  action TEXT NOT NULL CHECK (action IN (
    'matched_prerequisite', 'created_prerequisite', 'unmatched_prerequisite',
    'belief_sighting', 'belief_candidate', 'belief_registry_path', 'unplaced',
    'signal_only', 'unnamed', 'none', 'failed'
  )),
  target_kind TEXT CHECK (target_kind IS NULL OR target_kind IN ('learning_object', 'durable', 'candidate')),
  target_id TEXT,
  target_subject_id TEXT,
  match_basis TEXT,
  edge_id TEXT,
  created_concept_id TEXT,
  created_learning_object_id TEXT,
  seed_practice_item_id TEXT,
  seed_status TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  algorithm_version TEXT NOT NULL,
  pipeline_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_kind, source_id)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
