---
title: Process Model Output
aliases:
  - Grading and Validation Workflow
  - Attempt Output Processing
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - src/learnloop/attempts/attempts.py
  - src/learnloop/attempts/grading.py
  - src/learnloop/attempts/ai_contracts.py
  - src/learnloop/attempts/post_attempt.py
  - src/learnloop/attempts/completion_lock.py
  - src/learnloop/db/stores/completion.py
  - src/learnloop/ai/execution.py
  - tests/test_attempt_completion.py
  - src/learnloop/ai/transport.py
  - tests/test_attempt_write_order.py
  - tests/test_attempt_ai_flow.py
  - tests/test_codex_grading_validation.py
  - tests/test_post_attempt_pipeline.py
tags:
  - learnloop/workflow
  - learnloop/grading
  - learnloop/ai
  - learnloop/attempt
---

# Process Model Output

LearnLoop never treats a model response as learner state. It resolves the assessment contract, obtains a grading proposal, validates and normalizes it on the server, then sends the accepted grade through one attempt-application path. See [[AI Architecture]] for provider mechanics and [[Learning System]] for how evidence affects mastery.

## End-to-end branch

```mermaid
flowchart TD
    A[Answer + assessment contract] --> B{Deterministic grade possible?}
    B -->|yes| D[Deterministic proposal]
    B -->|no| C{Required provider ready?}
    C -->|yes| M[Structured model call]
    M --> V[Server validation and normalization]
    C -->|no, ordinary practice| S[Explicit self-grade fallback]
    C -->|no, diagnostic/exam| X[Typed failure; no fabricated grade]
    D --> P[Attempt application]
    V -->|valid| P
    V -->|invalid, ordinary + supplied score| S
    V -->|invalid, required route| X
    S --> P
    P --> W[Receipt → evidence → derived state → post-attempt]
```

All accepted paths converge before persistence. Required observations fail closed; they do not silently become self-reports. ^grading-convergence

## 1. Resolve the assessment contract

Before a provider call, the grading service resolves:

- the exact practice item and allowed answer type;
- rubric criteria and maximum points;
- assessment purpose, including diagnostic/exam restrictions;
- reveal-ledger state, which can force an attempt to be primed;
- item/facet identifiers allowed in evidence.

Option-letter items can be graded deterministically. This avoids a model call without weakening the same downstream evidence contract.

## 2. Record the call receipt, then call the provider

For provider-backed grading, an `agent_runs` row is inserted in `running` state before transport begins. Under a model-call observer (every sidecar RPC, durable ingest jobs, and CLI practice grading), each model operation also writes a `model_call_receipts` row in `started` state before the paid request; the finish write is best-effort, so a lost finish leaves the receipt `started` with unknown usage. The feature sends a typed `GradingContext` and expects a typed `GradingProposal`; transport handles provider protocol and bounded JSON repair as described in [[AI Architecture#Output trust boundary]].

> [!important] Audit invariant
> A timeout, invalid payload, or provider error must still leave an inspectable agent-run outcome. There is no invisible call between the answer and the grade.

## 3. Validate server-side

The validator, not the model:

- verifies attempt and practice-item ids;
- rejects duplicate or unknown rubric criteria;
- enforces each criterion's point bounds;
- recalculates the total from criterion evidence;
- applies fatal-error caps;
- accepts only known facets and criteria;
- recomputes quoted-evidence offsets and safely degrades bad localization;
- rejects structural invalidity rather than guessing.

The model's total is retained for audit, but it does not override the sum of validated criterion points.

## Apply the resolved grade transactionally

`apply_attempt` runs in one repository transaction. `AttemptApplication` materializes the receipt, grade, evidence/error records and derived state inputs before repository persistence. The write order is as follows (`tests/test_attempt_write_order.py` asserts steps 1–4 before post-attempt completion):

1. receipt;
2. grade;
3. criterion evidence and error records;
4. derived learner state;
5. the grade's `attempt_feedback_metadata` row (grading source, fallback reason, grading run, repair suggestions), written before causal materialization and episode accounting because a block this attempt closes normalizes the whole block inside the same transaction and reads the grading run from that row;
6. the attempt's `attempt_completion_work` row, which saves the result and the probe episode the attempt was applied under.

Doors with no completion phase (exam seeding, simulators, recall calibration, observation imports, rung-variant requests) set `awaits_completion=False`; their completion row is written `completed` at apply time, so a `pending` row always means an interrupted completion.

## Post-attempt completion

`run_post_attempt_pipeline` completes an applied attempt exactly once. It holds the per-database completion lock (`attempt-completion.lock`, re-entrant per thread, 120 s wait) for the whole sequence and returns immediately when the completion row is already `completed`:

1. **One transaction:** certification cold-probe scheduling and the attempt feedback metadata row (both idempotent, so a resumed completion may repeat them).
2. **No transaction:** misconception normalization and resolution, which may call the grading provider; a diagnostic answer inside a block that is still measuring defers this to the block-end hook.
3. **One transaction:** intervention and causal follow-up evaluation, the final learner route (from the recorded apply-time probe episode), and the completion mark.

A process that stops between apply and the completion mark leaves a `pending` row; retrying the same submission id resumes from step 1 with the saved grade, as described in [[Continue a Learning Cycle#After a lost submission response]]. Exam attempts use the same evidence-side processing but defer feedback until the exam finishes.

## Manual ordinary-practice example

Inspect the item first so criterion ids and maxima come from the live contract:

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
ITEM=pi_what_makes_function_axiom_strategy

uv run learnloop show "$ITEM" --json --vault "$VAULT"

uv run learnloop attempt "$ITEM" \
  --answer "Take scalar a=0 and nonzero f(t)=1; then 0⊙f=f, so the vector-space axiom fails." \
  --criterion-points crit_function_decisive_test=4 \
  --confidence 4 \
  --attempt-type open_text \
  --ai-provider manual \
  --json \
  --vault "$VAULT"
```

The result should identify the new attempt, normalized score/correctness, scheduling update, and `grading_source: "self"` with `fallback_reason: "provider_unavailable"`. Criterion ids are item-specific; never copy the example id to another item.

For the full inspection sequence, use [[Manual Attempt and State Inspection]].

For a ready-provider path that verifies `agent_run_id`, distinguishes success from fallback, and joins the persisted call receipt to criterion evidence, follow [[Provider-Backed Attempt and Agent Run]].

## Failure handling

| Failure | Ordinary practice | Diagnostic, held-out exam, required teach-back grade |
|---|---|---|
| provider unavailable | explicit self-grade if supplied | fail closed |
| timeout/transport error | typed fallback if allowed | fail closed |
| structurally invalid proposal | reject; fallback only if allowed | fail closed |
| bad quote offsets only | retain valid grade, degrade localization | same validation rule |

> [!failure] Evidence inflation trap
> Do not modify adapters to coerce an invalid model total or unknown criterion into a passing grade. Change the feature schema/prompt and validator together, add a regression test, and preserve the failed `agent_runs` receipt.

## Observable state

- raw attempt: `practice_attempts`
- criterion evidence: `grading_evidence`
- call receipt: `agent_runs`
- source/fallback/feedback: `attempt_feedback_metadata`
- saved result and completion state: `attempt_completion_work`
- per-request model calls: `model_call_receipts`
- derived surprise and learner state: DERIVED-role tables listed in [[Database Catalog]]

Trace them safely in [[Inspect Persistent State#Trace one attempt]].

## Related notes

- [[AI Architecture]]
- [[Learning System]]
- [[State and Persistence]]
- [[Configure AI Providers]]
