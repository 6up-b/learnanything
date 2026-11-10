---
title: Inspect Persistent State
aliases:
  - State SQLite Inspection
  - Inspect Learner State
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-11-10
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop/db/repositories.py
  - src/learnloop/db/table_roles.py
  - src/learnloop/attempts/attempts.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/provenance.py
  - src/learnloop/why/reader.py
  - src/learnloop/why/reconstructed.py
  - src/learnloop/cli/app.py
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

The migration head is the newest file in `migrations/`; version numbers have gaps. A current vault's `MAX(version)` equals it. The tracked fixture `fixtures/migration_head/state.sqlite` always holds the head (its `README.md` names the number), so it is the schema to inspect when no vault is at hand; open it read-only, or copy it with `learnloop.db.copies` first.

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

SELECT status, route_json, completed_at
FROM attempt_completion_work
WHERE attempt_id = '<attempt-id>';

SELECT scheduler_candidate_id, entry_surface, collection_version
FROM submission_intents
WHERE submission_id = (SELECT submission_id FROM practice_attempts
                       WHERE id = '<attempt-id>');
```

A `pending` completion row means post-attempt work was interrupted and is resumed on the next submit with the same submission id; see [[Continue a Learning Cycle]]. The submission intent names the scheduler offer the attempt answered; see [[Collection and Dataset Contract]].

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
uv run learnloop why [latest | <trace-id> | <record-id> | <kind>:<id> | <practice-item-id>] [--kind K] [--first-build] [--payload] --json --vault "$VAULT"
uv run learnloop ingest-batches show <batch-id> --json --vault "$VAULT"
uv run learnloop doctor --json --vault "$VAULT"
uv run learnloop data-quality --vault "$VAULT"
uv run learnloop usage --vault "$VAULT"
```

These resolve filesystem configuration and SQLite state together. `data-quality` always prints JSON from one read-only transaction: collection coverage by version, entry surface and origin, offer and grade links, completion rows, model-call receipts and label exclusions. `usage` summarizes model-call tokens, cost and synthesis budget ratios from the same receipts (see [[Model Usage Report]]). `learnloop dataset-export <new-dir>` writes a full snapshot plus every ledger and receipt table; treat its output as the vault itself (see [[Privacy and Trust Boundaries]]).

## Ask why a decision went the way it did

[[Debug a decision]] is the how-to, with examples; this section is the reference for what each record holds.

`learnloop why` is a pure read ([[ADR-017 One decision record, one trace id, one entry point]]): it attaches read-only and runs no state sync or maintenance, so asking never changes the vault. With no target it answers `latest`: the newest decision record's trace. A trace id, a record id or `<kind>:<id>` (`attempt`, `item`, `block`, `offer`, `figure`, `job`, `presentation`, `decision`, `slate`, `factor`, `goal`, `lesson`) name others; `--kind` keeps one kind. A practice item id still gives that item's scheduler explanation.

Every slate row (a serving queue build with a session) gets one `slate` record, found by `slate:<scheduler_slates.id>`: the head and the rule that put it first, the ranked candidates after it with their selection reward and propensity, and every item the build kept off the slate, counted by rule with up to ten ids each (`facts.exclusions`), plus why the items of an LO whose placement check is due could not be that check (`facts.placement_check_exclusions`). Reads (`persist_explanations=False`: `why`, the knowledge map, the facet chart) and sessionless builds write none. `item:<id>` adds the newest slate records naming the item, with what each says about it (`chosen`, the rule it lost by or was excluded by), and, when the item is not on a slate built now, `excluded_now`: the rule keeping it off, from a build that persists nothing.

For a trace it lists the `decision_records` (kind, status, what won, who decided and the rule, the alternatives and the inputs as numbers and codes) and the trace's model calls, joined by `model_call_receipts.trace_id` (ids, purposes, statuses and times, never the prompt or the output). Every sidecar RPC, phone request, MCP tool call and CLI command runs under one trace, and the sidecar's structured log events carry its `trace_id`, so a log line joins the same rows. Calls before migration 253 have no `trace_id`, and decisions older than their records have no record. `why` answers those from the rows they left (`learnloop.why.reconstructed`, every answer labelled `reconstructed`, under the output's `reconstructed` key): a router decision id, `block:`, `offer:`, `figure:` or `decision:` reads the `router_decisions` row and its calls through its boundary key (`detail_json` names it; the calls' `owner_id` holds it), an offer's `expired` response, an `interactive_figures` row with its author calls, and `--first-build` reads `figure_prefetch_decisions`. Fields found only by ordering rows in time are named in the answer's `inferred` list.

An attempt's chain answers under the submit's trace. `attempt:<id>` gives its `grade` (the verdict class as the rule, the score and maximum, the review reason's code, the grader and its prompt version; never the answer, the rubric's text or the feedback), a `grade_held` child when the grade was held for review as it was applied (the hold itself stays a predicate, `held_grades.py`), its `diagnosis` (status and why, candidate causes by index and prior weight, the prompt version and model), any `diagnosis_step` that failed (the machine-check sweep, the common-repair consultation, the escalation receipt, the learner-text enqueue) and its `followup_value` decision. Every queued job writes `job_enqueued` (`job:<id>`) and runs under the trace that queued it, so the trace also holds the diagnosis's and the follow-up's model calls. A rejected probe value (`probe_value`, `item:<id>`), a causal probe offer's acceptance or refusal (`probe_offer`, `factor:<id>`, naming the learner lane's causal receipt or FG1's router decision) and a forecast that could not be logged (`voi_forecast`) leave records too.

A plan block decision (`plan_block`, with a `model_answer` per component; [[Scheduling and Selection#The daily plan's block router]]) may have been prefetched by an earlier request: its `facts.prefetch_trace` names that trace, and `why` reads that trace's calls too (`prefetch_traces`). Its `created_at` is the moment the decision took its models' answers, so `why` lists under `discarded` each call of those traces for its boundary key that started before it and finished after it (`late_ms`), or hadn't finished when asked (`late_ms` null). The discarded list is computed when `why` runs; nothing extra is written.

A `plan_block` also names the newest attempt as of the decision (`facts.trigger_attempt`), the forced items it placed first with their follow-up workflows and source attempts (`facts.forced`, `workflows`, `source_attempts`), and, under IH2's contest, the open offer it replaces (`superseding_offer_block`, `superseding_offer_decision`). An offer the plan took back or a newer decision replaced has an `offer_withdrawn` record, found by `offer:<router_decisions.id>`: its rule (`forced_items`, `offers_off`, `never_shown`, `superseded_by_decision`), the forced items as its alternatives, and the offer's own `plan_block` as its parent; the next boundary's `plan_block` names the withdrawal as its parent. The day's randomized check block has its own `plan_block` (`decided_by = rules`). A boundary step that raised (the check draw or placement, the lesson offer's builder) is a `failed` child of the boundary's record, with the exception's type and `module:function:line`. Also by subject: `plan_interrupt` (the restraint gate's decision on a mid-block follow-up, `item:<id>`, with `model_answer` children), `ad_slot` (adaptive difficulty unavailable, the incumbent decided: the phase, AD's code and the guard's refusals as verb, table and reader; `ad_guard_denials.jsonl` stays beside the database for `learnloop ad report`), `serve_eligibility` (a planned cold check displaced or served as practice) and `today_offer` (a Today offer published without its router decision, `slate:<id>`).

The same join in SQL:

```sql
SELECT created_at, kind, status, chosen_ref, decided_by, rule, facts_json
FROM decision_records
WHERE trace_id = '<trace-id>'
ORDER BY created_at, id;

SELECT id, purpose, status, started_at, finished_at
FROM model_call_receipts
WHERE trace_id = '<trace-id>'
ORDER BY started_at, id;
```

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
