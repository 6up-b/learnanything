---
title: Goals Exams and Certification Workflow
aliases:
  - Goal and Held-Out Exam Workflow
  - Certification Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/cli/app.py
  - src/learnloop/content/authoring/practice_generation.py
  - src/learnloop/goals/goal_contracts.py
  - src/learnloop/goals/goal_projection.py
  - src/learnloop/goals/exam_pool.py
  - src/learnloop/goals/exam_session.py
  - src/learnloop/goals/exam_readiness.py
  - src/learnloop/goals/certification.py
  - src/learnloop_sidecar/handlers/goals.py
  - src/learnloop_sidecar/handlers/exams.py
  - tests/test_sidecar_goals.py
  - tests/test_sidecar_exams.py
  - tests/test_exam_session.py
tags:
  - learnloop/workflow
  - learnloop/goals
  - learnloop/exams
  - learnloop/certification
---

# Goals Exams and Certification Workflow

A goal defines intended scope, target recall, and timing. **Ready** is a current forecast; **Demonstrated** requires qualifying held-out or cold evidence. The interpretation of those states belongs to [[Learning System]]; this workflow creates, populates, and evaluates the contract without collapsing the distinction.

## Prerequisites

- active learning objects/facets for the goal scope
- a ready authoring provider if generating missing practice
- a ready grading provider for held-out exam answers
- a healthy mvp-0.9 vault

## 1. Create the goal in the desktop wizard

On **Today**, open the Goal Wizard and complete its four stages:

1. **What** — title, optional intent sentence, and concepts/facets.
2. **How well** — target recall (the UI starts at `0.85`).
3. **By when** — a due date or open-ended goal; inspect the live feasibility result.
4. **Exam** — optionally request a held-out exam and item count (the UI starts at 20), and optionally generate practice.

Goal ids are stable slugs. The active projection is written to `profile/goals.yaml` schema v2, while versioned goal-contract records preserve edits in SQLite.

> [!important] Scope invariant
> Normal goal creation requires scope that resolves to active learning objects. A title alone is not a measurable goal contract.

Creation does not immediately reserve held-out items. Reservation is deferred until the exam is prepared, so the authoring path can first create enough fresh material.

## 2. Populate missing practice

Take the goal id from the wizard or `profile/goals.yaml`:

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
GOAL=<goal-id>

uv run learnloop populate-goal "$GOAL" \
  --dry-run --json --vault "$VAULT"

uv run learnloop populate-goal "$GOAL" \
  --json --vault "$VAULT"
```

The dry run reports proposed coverage without accepting content. The normal command generates required practice and auto-accepts by default; add `--review` when a human review gate is desired.

Observable state includes the authoring `agent_runs` receipt, a persisted proposal/review/apply trail, and—when auto-accepted—new goal-scoped practice-item files. `populate-goal` does **not** create `ingest_batches` or `ingest_jobs`; content generation is not canonical-source ingestion. None of these artifacts becomes learner evidence until an item is actually presented and answered.

## 3. Inspect readiness

```bash
uv run learnloop exam-readiness \
  --subject linear-algebra \
  --total-items 20 \
  --json --vault "$VAULT"
```

This command is deterministic and makes no model call. The goal surface additionally reports uncovered/material gaps, feasibility, pace, and Ready versus Demonstrated.

## 4. Reserve and start a held-out exam

```bash
uv run learnloop exam reserve \
  --goal "$GOAL" --item-count 20 --json --vault "$VAULT"

uv run learnloop exam start \
  --goal "$GOAL" --json --vault "$VAULT"
```

Save the returned session id and ordered item ids. Reserved items enter `exam_pool_items` and are quarantined from ordinary practice. Starting again resumes an existing open exam rather than creating competing sessions.

> [!warning] Holdout integrity
> Never practice, preview answers for, or manually reclassify reserved exam items. Their value comes from being unseen. If the pool is insufficient, generate fresh material instead of borrowing practiced items.

## 5. Answer every item without feedback

```bash
uv run learnloop exam answer <exam-item-id> \
  --session <exam-session-id> \
  --answer "Your answer here" \
  --ai-provider codex \
  --json --vault "$VAULT"
```

Repeat for the next item returned by the session. Exam answers are AI-graded only; self-grade options are deliberately refused. No criterion feedback is shown mid-exam.

## 6. Finish and interpret

```bash
uv run learnloop exam finish \
  --session <exam-session-id> \
  --json --vault "$VAULT"
```

Finish applies the deferred grading/evidence effects and then returns the report. `exam_sessions`, `exam_answers`, predictions, pool status, normal attempt/evidence rows, and post-attempt effects form the durable trace.

Use the result as evidence toward Demonstrated; do not relabel a forecast as certification merely because the current readiness projection is high.

## Certification after practice

Qualifying work can schedule cold certification probes. These are kept distinct from warm practice and primed attempts, and their completion/passing counts remain separate in session summaries. Operator commands such as cold-probe schedule/audit inspect that pipeline; the decision rules are authoritative in [[Goals and Certification#Certification]].

> [!info] Historical exam seeding
> `seed-exam-attempts` imports explicit backdated outcome data as discounted `exam_evidence` and rebuilds in event-time order. Use [[Goal and Exam Session]] for a worked live exam. Do not use seeding to manufacture a current held-out result.

## Observable files and tables

| Area | Observation |
|---|---|
| goal projection | `profile/goals.yaml` |
| versioned contract | goal contract draft/head/version tables |
| generation | ingest batches/jobs and generated item files |
| holdout | `exam_pool_items` |
| administration | `exam_sessions`, `exam_answers`, `exam_predictions` |
| certification | cold-probe opportunity/outcome receipts |

Exact ownership and ACTIVE/DORMANT status are in [[Database Catalog]].

## Related notes

- [[Learning System]]
- [[Goal and Exam Session]]
- [[Process Model Output]]
- [[Scheduling and Selection]]
