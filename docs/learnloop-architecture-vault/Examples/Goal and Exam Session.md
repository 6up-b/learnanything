---
title: Goal and Exam Session
aliases:
  - Held-Out Exam Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/goals/exam_pool.py
  - src/learnloop/goals/exam_session.py
  - src/learnloop/goals/exam_readiness.py
  - src/learnloop_sidecar/handlers/goals.py
  - src/learnloop_sidecar/handlers/exams.py
  - tests/test_sidecar_goals.py
  - tests/test_sidecar_exams.py
tags:
  - learnloop/example
  - learnloop/goals
  - learnloop/exams
---

# Goal and Exam Session

This example uses the desktop for goal creation and CLI for an auditable held-out administration. Replace every placeholder with the actual wizard/command response. The semantics of Ready versus Demonstrated are in [[Goals and Certification]].

## Prerequisites

- `$VAULT` points to a healthy mvp-0.9 vault with an applied study map
- goal scope has active learning objects/facets
- authoring and grading routes pass `doctor --ai`

## 1. Create the contract

In the desktop **Today** Goal Wizard:

1. title it “Vector-space proof fluency”;
2. select the relevant active concepts/facets;
3. choose target recall `0.85`;
4. choose a realistic due date;
5. request a 10-item held-out exam;
6. enable generated practice if the feasibility view reports material gaps.

After saving, inspect:

```bash
rg -n 'Vector-space proof fluency|target_recall' "$VAULT/profile/goals.yaml"
```

Set the returned slug/id:

```bash
GOAL=<goal-id>
```

## 2. Preview and populate gaps

```bash
uv run learnloop populate-goal "$GOAL" \
  --dry-run --json --vault "$VAULT"
```

Review proposed coverage and cost. Then either keep review control:

```bash
uv run learnloop populate-goal "$GOAL" \
  --review --json --vault "$VAULT"
```

or omit `--review` for the current auto-accept default. Generated questions are content, not evidence.

## 3. Check deterministic readiness

```bash
uv run learnloop exam-readiness \
  --subject vector-spaces \
  --total-items 10 \
  --json --vault "$VAULT"
```

Resolve insufficient fresh material before reservation.

## 4. Reserve and start

```bash
uv run learnloop exam reserve \
  --goal "$GOAL" --item-count 10 --json --vault "$VAULT"

uv run learnloop exam start \
  --goal "$GOAL" --json --vault "$VAULT"
```

Save `session_id` and the first returned item id:

```bash
SESSION=<exam-session-id>
ITEM=<first-exam-item-id>
```

Observable: `exam_pool_items` contains reserved/quarantined items and `exam_sessions` has one open administration.

## 5. Answer without mid-exam feedback

```bash
uv run learnloop exam answer "$ITEM" \
  --session "$SESSION" \
  --answer "A closed-book answer in the required form." \
  --ai-provider codex \
  --json --vault "$VAULT"
```

Repeat using the next item returned. Do not pass self-grade fields; the command returns a typed refusal because held-out answers are AI-graded only.

## 6. Finish once all items are answered

```bash
uv run learnloop exam finish \
  --session "$SESSION" --json --vault "$VAULT"
```

Only now is feedback/reporting revealed and deferred attempt effects applied. Inspect administration receipts:

```bash
sqlite3 -readonly "$VAULT/state.sqlite" <<SQL
.headers on
.mode box
SELECT id, goal_id, status, started_at, completed_at
FROM exam_sessions WHERE id = '$SESSION';
SELECT session_id, practice_item_id, attempt_id, answered_at
FROM exam_answers WHERE session_id = '$SESSION';
SQL
```

Before scripting these queries, use `.schema exam_sessions` and `.schema exam_answers`; [[Database Catalog]] is authoritative if columns change.

> [!important] Interpret honestly
> A successful session contributes held-out evidence. Certification still depends on the goal contract and qualifying evidence rules; follow [[Goals Exams and Certification Workflow#Certification after practice]].

^goal-exam-example
