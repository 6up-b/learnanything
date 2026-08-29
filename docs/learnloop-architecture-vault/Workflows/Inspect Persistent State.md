---
title: Inspect Persistent State
aliases:
  - State SQLite Inspection
  - Inspect Learner State
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/db/repositories.py
  - src/learnloop/db/table_roles.py
  - src/learnloop/attempts/attempts.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - tests/test_attempt_write_order.py
  - tests/test_rebuild_orchestrator.py
tags:
  - learnloop/workflow
  - learnloop/persistence
  - learnloop/sqlite
  - learnloop/debugging
---

# Inspect Persistent State

This workflow answers “what was durably recorded?” without changing the vault. Table meanings and ACTIVE/DORMANT status are authoritative in [[Database Catalog]]; persistence roles and replay policy are explained in [[State and Persistence]].

## Safety first

Close LearnLoop writers when doing extended inspection. Open SQLite read-only:

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
sqlite3 -readonly "$VAULT/state.sqlite"
```

Inside the shell, useful display settings are:

```sql
.headers on
.mode box
.timeout 5000
```

> [!warning] No manual updates
> Never `UPDATE`, `DELETE`, or hand-insert into state tables. Receipts, foreign keys, file projections, replay order, and derived markers form a larger contract than one row. Use product commands or [[Doctor Migrations and Recovery]].

## Confirm schema and recent activity

```sql
SELECT MAX(version) AS migration_head FROM schema_migrations;

SELECT id, started_at, ended_at, energy, available_minutes
FROM sessions
ORDER BY started_at DESC
LIMIT 5;

SELECT id, practice_item_id, learning_object_id, correctness,
       rubric_score, confidence, created_at
FROM practice_attempts
ORDER BY created_at DESC, id DESC
LIMIT 10;
```

Migration head is currently `156`; migration version numbers have gaps.

## Trace one attempt

Replace `<attempt-id>` with the id returned by `learnloop attempt` or the desktop submission:

```sql
SELECT id, practice_item_id, learning_object_id, attempt_type,
       rubric_score, correctness, confidence, session_id,
       submission_id, created_at
FROM practice_attempts
WHERE id = '<attempt-id>';

SELECT criterion_id, points_awarded, evidence, notes,
       agent_run_id, local_grader_id, grader_tier
FROM grading_evidence
WHERE attempt_id = '<attempt-id>'
  AND superseded_at IS NULL
ORDER BY criterion_id;

SELECT grading_source, fallback_reason, agent_run_id,
       fatal_errors_json, feedback_md
FROM attempt_feedback_metadata
WHERE attempt_id = '<attempt-id>';

SELECT surprise_direction, bayesian_surprise
FROM attempt_surprise
WHERE attempt_id = '<attempt-id>';
```

This joins the raw receipt, accepted criterion evidence, feedback provenance, and one derived result without implying that any single table is the whole attempt. ^attempt-trace

## Inspect current learner projections

```sql
SELECT learning_object_id, logit_mean, logit_variance,
       evidence_count, updated_at
FROM learning_object_mastery
ORDER BY updated_at DESC
LIMIT 20;

SELECT practice_item_id, due_at, stability, difficulty, updated_at
FROM practice_item_state
ORDER BY updated_at DESC
LIMIT 20;
```

Column names can evolve. Before scripting a query, compare with:

```sql
.schema learning_object_mastery
.schema practice_item_state
```

Derived rows are reproducible projections, not primary evidence. If they look stale, do not edit them; compare using [[Rebuild and Shadow Compare]].

## Inspect canonical import receipts

```sql
SELECT id, workflow_type, status, subject_id, created_at, finished_at
FROM ingest_batches
ORDER BY created_at DESC
LIMIT 10;

SELECT id, batch_id, job_type, status, phase, attempt_count,
       started_at, finished_at
FROM ingest_jobs
ORDER BY created_at DESC
LIMIT 20;

SELECT id, revision_id, extractor, extractor_version,
       status, created_at, completed_at
FROM source_extraction_runs
ORDER BY created_at DESC
LIMIT 10;
```

If a column differs in the current schema, use `.schema <table>` and [[Database Catalog#How to use this catalog]] rather than assuming an older query is writable guidance.

## Use product-level views when possible

SQL is best for provenance debugging. For stable supported output prefer:

```bash
uv run learnloop show <identifier> --json --vault "$VAULT"
uv run learnloop why <practice-item-id> --json --vault "$VAULT"
uv run learnloop ingest-batches show <batch-id> --json --vault "$VAULT"
uv run learnloop doctor --json --vault "$VAULT"
```

These resolve filesystem configuration and SQLite state together.

## Decide the next action

- evidence is correct and projections are plausible → [[Continue a Learning Cycle]];
- only derived projections are suspect → [[Rebuild and Shadow Compare]];
- schema/layout/reference checks fail → [[Doctor Migrations and Recovery]];
- grading provenance is unexpected → [[Process Model Output#Failure handling]].

## Related notes

- [[State and Persistence]]
- [[Database Catalog]]
- [[Rebuild and Shadow Compare]]
- [[Manual Attempt and State Inspection]]
