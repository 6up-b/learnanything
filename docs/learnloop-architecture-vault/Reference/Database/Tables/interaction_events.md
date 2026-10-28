---
title: "interaction_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ca2c0b7e37edfb7cc303e8a6ae97cdcf99124ffd"
source_commit_timestamp: "2026-10-27T18:06:05-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite interaction_events"
  - "table interaction_events"
schema_head: 226
table_name: "interaction_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "065_activity_lineage_substrate.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/065_activity_lineage_substrate.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/reading.py"
  - "src/learnloop/adaptive_difficulty/report.py"
  - "src/learnloop/attempts/salience_firewall.py"
  - "src/learnloop/cli/field_classification.py"
  - "src/learnloop/cli/surfaces.py"
  - "src/learnloop/content/authoring/exercise_authoring.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/content/authoring/rung_variants.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/diagnosis/probe_remint.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `interaction_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of interaction so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `subject_id`, `administration_id`, `surface_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- Interaction events envelope (§3.8): the Layer-5 corpus. EXPLICITLY NOT an extension of content_events (which stays a closed content-mutation audit). "Log now, model later": ships before any consumer. Day-one kinds: attempt_duration, retirement_reason, affect_tap. P3 adds reading-event kinds to the SAME table. Declared before retirement_records, which references it. ----------------------------------------------------------------------------

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/065_activity_lineage_substrate.sql`.
- **Schema touched by:** `065_activity_lineage_substrate.sql`, `086_reader_dialogue.sql`, `091_interaction_events_reader_envelope.sql`, `103_learner_item_authoring_kinds.sql`, `115_causal_attribution_p0.sql`, `203_chat_mcp_interaction_events.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `subject_type` | `TEXT` | no | — | — | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `administration_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `surface_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `affect_tap_kind` | `TEXT` | no | — | — | Stored value |
| `attempt_duration_ms` | `INTEGER` | no | — | — | Stored value |
| `payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `occurred_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `received_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `actor` | `TEXT` | no | — | — | Stored value |
| `client_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `visit_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `payload_schema_version` | `TEXT` | no | — | — | Stored value |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `render_view_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `locator_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `annotation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `activity_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `payload_hash` | `TEXT` | no | — | — | Stored value |
| `client_idempotency_key` | `TEXT` | no | — | — | Stored value |
| `privacy_locality` | `TEXT` | no | — | — | Stored value |
| `consent_context` | `TEXT` | no | — | — | Stored value |
| `producer_version` | `TEXT` | no | — | — | Stored value |
| `app_version` | `TEXT` | no | — | — | Stored value |
| `policy_version` | `TEXT` | no | — | — | Stored value |
| `supersedes_event_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_interaction_events_client_key` on `client_idempotency_key` (unique).
- `idx_interaction_events_session` on `session_id`.
- `idx_interaction_events_source` on `source_id`.
- `idx_interaction_events_admin` on `administration_id`.
- `idx_interaction_events_subject` on `subject_type`, `subject_id`.
- `idx_interaction_events_kind` on `kind`, `created_at`.
- `sqlite_autoindex_interaction_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_interaction_event()`
- `Repository.capture_local_transaction()`
- `Repository.delete_source_artifact()`
- `Repository.interaction_events_for_attempt()`
- `Repository.reader_interaction_events()`

### Direct SQL readers

- `src/learnloop/adaptive_difficulty/material_view.py`
- `src/learnloop/cli/field_classification.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/source_service.py`
- `src/learnloop/db/stores/workbench.py`
- `src/learnloop/ops/pf_reports.py`
- `src/learnloop/reader/reader_report.py`
- `src/learnloop/reader/reader_sessions.py`
- `src/learnloop/scheduling/action_loss.py`
- `src/learnloop/workbench/ladder.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/exercise_authoring.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/content/authoring/rung_variants.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/diagnosis/probe_remint.py`
- `src/learnloop/reader/reader_capture.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/reader/reader_observations.py`
- `src/learnloop/reader/reader_quick_check.py`
- `src/learnloop/reader/recap.py`
- `src/learnloop/remote/telemetry.py`
- `src/learnloop/substrate/activities.py`
- `src/learnloop/substrate/compat/activity_backfill.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ad_ingest_fakes.py`
- `tests/recap_fixtures.py`
- `tests/test_activity_substrate.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad_protected_readings.py`
- `tests/test_compare_keep_switch_off.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_exam_protection.py`
- `tests/test_figures_rpc.py`
- `tests/test_grading_cli.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_interaction_signals.py`
- `tests/test_mcp_tools.py`
- `tests/test_reader_active_reading.py`
- `tests/test_reader_branches.py`
- `tests/test_reader_capture.py`
- `tests/test_reader_cues.py`
- `tests/test_reader_dialogue.py`

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
CREATE TABLE "interaction_events" (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN
    ('attempt_duration', 'retirement_reason', 'affect_tap',
     -- U-033 reader-dialogue kinds (migration 086, §7.6):
     'reader_question_presented', 'reader_question_skipped',
     'reader_answer_submitted', 'learner_question_asked',
     'reader_answer_mode_set', 'reader_disposition_chosen',
     'reader_source_restored',
     -- P3 launch reader/reading event kinds (§8.1):
     'reader_view_opened', 'reader_view_closed', 'reader_mode_changed',
     'reader_span_visible', 'reader_scroll', 'reader_dwell',
     'reader_selection', 'reader_highlight', 'reader_annotation_edited',
     'reader_action_invoked', 'reader_capture_acknowledged',
     'reader_job_queued', 'reader_job_completed',
     'reader_proposal_accepted', 'reader_proposal_edited', 'reader_proposal_rejected',
     'reader_authoring_coach_response',
     'reader_depth_policy_confirmed', 'reader_depth_envelope_confirmed',
     'reader_depth_envelope_changed', 'reader_milestone_reached',
     'reader_automatic_edge_committed', 'reader_automatic_edge_blocked',
     'reader_automatic_depth_paused', 'reader_question_control',
     -- Learner-owned item authoring lifecycle (migration 103):
     'learner_item_authored', 'learner_item_edited',
     'learner_item_retired', 'learner_item_split',
     -- Chat frontend C1a (migration 203): one row per MCP tool call a chat
     -- host made (ChatGPT, Claude, or a local stdio client).
     'chat_tool_call')),
  subject_type TEXT,
  subject_id TEXT,
  administration_id TEXT,
  surface_id TEXT,
  attempt_id TEXT,
  affect_tap_kind TEXT CHECK (affect_tap_kind IS NULL OR affect_tap_kind IN (
    'cue_gave_it_away', 'ambiguous', 'misgraded', 'felt_rote',
    'not_worth_my_attention', 'meaningful_connection', 'wanted_more_depth'
  )),
  attempt_duration_ms INTEGER
    CHECK (attempt_duration_ms IS NULL OR attempt_duration_ms >= 0),
  payload_json TEXT,
  origin TEXT NOT NULL
    CHECK (origin IN ('learner', 'system', 'owner_tooling', 'chat_host')),
  created_at TEXT NOT NULL,
  occurred_at TEXT,
  received_at TEXT,
  actor TEXT,
  client_id TEXT,
  session_id TEXT,
  visit_id TEXT,
  payload_schema_version TEXT,
  source_id TEXT,
  revision_id TEXT,
  render_view_id TEXT,
  locator_json TEXT,
  annotation_id TEXT,
  commitment_id TEXT,
  activity_id TEXT,
  payload_hash TEXT,
  client_idempotency_key TEXT,
  privacy_locality TEXT,
  consent_context TEXT,
  producer_version TEXT,
  app_version TEXT,
  policy_version TEXT,
  supersedes_event_id TEXT
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]
