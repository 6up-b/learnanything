---
title: Manual Attempt and State Inspection
aliases:
  - Manual Grading Example
  - Attempt Persistence Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - fixtures/linear_algebra/learnloop.toml
  - fixtures/linear_algebra/subjects/vector-spaces/practice-items/pi_what_makes_function_axiom_strategy.yaml
  - src/learnloop/attempts/attempts.py
  - src/learnloop/attempts/grading.py
  - tests/test_cli_attempt.py
  - tests/test_attempt_write_order.py
tags:
  - learnloop/example
  - learnloop/attempt
  - learnloop/grading
  - learnloop/persistence
---

# Manual Attempt and State Inspection

This executable example copies the repository's linear-algebra fixture to temporary storage, upgrades the copy to mvp-0.9, self-grades one ordinary item, and traces every persisted layer. It never mutates `fixtures/linear_algebra`.

## Prerequisites

- repository root as current directory
- `uv sync --extra dev` already completed
- `sqlite3` available

## 1. Make an isolated vault copy

```bash
DEMO_ROOT="$(mktemp -d)"
VAULT="$DEMO_ROOT/linear-algebra"
cp -a fixtures/linear_algebra "$VAULT"

uv run learnloop init "$VAULT"
uv run learnloop upgrade --to mvp-0.9 --vault "$VAULT"
uv run learnloop doctor --json --vault "$VAULT"
```

`init` completes missing scaffold such as the empty `rubrics/` directory without replacing fixture files. The fixture starts at mvp-0.8; the immediate-successor upgrade is required for this mvp-0.9 documentation run. Because it is historical test data, doctor can still report legacy-config and content-quality warnings; require `error_count: 0` before continuing rather than expecting this fixture to be warning-free.

## 2. Read the live item contract

```bash
ITEM=pi_what_makes_function_axiom_strategy
uv run learnloop show "$ITEM" --json --vault "$VAULT"
```

Confirm:

- allowed type is `open_text`;
- the decisive criterion is `crit_function_decisive_test`;
- that criterion is worth 4 points;
- the item is ordinary constructed response, not a qualifying diagnostic/exam.

## 3. Submit an explicit self-grade

```bash
uv run learnloop attempt "$ITEM" \
  --answer "Take a=0 and nonzero f(t)=1. The rule gives 0⊙f=f rather than the zero function, so the scalar identity fails." \
  --criterion-points crit_function_decisive_test=4 \
  --confidence 4 \
  --attempt-type open_text \
  --ai-provider manual \
  --json --vault "$VAULT"
```

A verified run returned correctness `1.0`, rubric score `4`, grading source `self`, fallback reason `provider_unavailable`, and a new due/scheduling result. Save the returned `attempt_id`:

```bash
ATTEMPT=<attempt-id-from-response>
```

> [!warning] Criterion ids are contractual
> Never invent a criterion id or copy this one to another item. `show` is the authority for allowed criteria and maxima.

## 4. Trace raw receipt, evidence, and provenance

```bash
sqlite3 -readonly "$VAULT/state.sqlite" <<SQL
.headers on
.mode box
SELECT id, practice_item_id, rubric_score, correctness,
       confidence, attempt_type, submission_id
FROM practice_attempts WHERE id = '$ATTEMPT';

SELECT criterion_id, points_awarded, local_grader_id, grader_tier
FROM grading_evidence
WHERE attempt_id = '$ATTEMPT' AND superseded_at IS NULL;

SELECT grading_source, fallback_reason, agent_run_id
FROM attempt_feedback_metadata WHERE attempt_id = '$ATTEMPT';

SELECT surprise_direction, bayesian_surprise, algorithm_version
FROM attempt_surprise WHERE attempt_id = '$ATTEMPT';
SQL
```

Expected relationships:

```text
practice_attempts.id
  ├─ grading_evidence.attempt_id       local_grader_id=self
  ├─ attempt_feedback_metadata         grading_source=self
  └─ attempt_surprise                  DERIVED mvp-0.9 projection
```

The absence of `agent_run_id` is expected in explicit manual mode: no model client was called. See [[Process Model Output#Observable state]] for role meanings.

## 5. Inspect user-facing state

```bash
uv run learnloop show "$ATTEMPT" --json --vault "$VAULT"
uv run learnloop why "$ITEM" --json --vault "$VAULT"
```

These supported views combine file contracts and state. SQL remains provenance-level inspection only.

## 6. Dispose of the isolated copy

The demo vault lives under the printed `$DEMO_ROOT`. Remove it only after confirming it contains no work you intend to keep; the repository fixture is untouched.

^manual-attempt-example
