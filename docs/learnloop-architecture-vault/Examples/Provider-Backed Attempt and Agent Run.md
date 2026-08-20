---
title: Provider-Backed Attempt and Agent Run
aliases:
  - Model-Graded Attempt Example
  - Agent Run Receipt Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/cli/app.py
  - src/learnloop/attempts/attempts.py
  - src/learnloop/attempts/grading.py
  - src/learnloop/ai/routing.py
  - tests/test_attempt_ai_flow.py
  - tests/test_agent_runs.py
tags:
  - learnloop/example
  - learnloop/ai
  - learnloop/grading
  - learnloop/persistence
---

# Provider-Backed Attempt and Agent Run

This walkthrough proves the full model-backed grading path: a ready provider receives a feature-owned grading contract, LearnLoop validates the proposal, the accepted attempt is persisted, and an `agent_runs` receipt makes the call auditable. The trust boundary is explained once in [[Process Model Output]]; provider setup lives in [[Configure AI Providers]].

## Prerequisites

- a vault with at least one open-response practice item and rubric;
- a provider profile that is ready for the `grading` route;
- `jq` and `sqlite3` for the inspection steps;
- an honest self-grade to use only if the model call fails.

> [!important] Choose a non-deterministic item
> A plain option-letter response can be graded deterministically and correctly creates no model receipt. Choose an open-text, proof, derivation, or other response whose rubric requires structured grading.

## 1. Confirm the selected provider

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
PROVIDER="codex_low" # replace with a ready profile from config effective

uv run learnloop config effective --json --vault "$VAULT"
uv run learnloop doctor --ai --ai-provider "$PROVIDER" --json --vault "$VAULT"
```

Do not continue until the selected runtime reports ready. For an OpenAI-compatible profile, export the variable named by `api_key_env`; never paste the secret into `learnloop.toml`.

## 2. Choose and inspect an item

```bash
uv run learnloop review --limit 5 --json --vault "$VAULT"

ITEM="<open-text-practice-item-id>"
uv run learnloop show "$ITEM" --json --vault "$VAULT"
```

From `show`, note each rubric criterion id and its maximum. The fallback points in the next step must be a real self-assessment within those bounds; they are not sent downstream as the model's accepted score when provider grading succeeds.

## 3. Submit the provider-backed attempt

```bash
RESULT="/tmp/learnloop-provider-attempt.json"

uv run learnloop attempt "$ITEM" \
  --answer "<your complete answer>" \
  --criterion-points "<criterion-id>=<honest-fallback-points>" \
  --confidence 3 \
  --ai-provider "$PROVIDER" \
  --json --vault "$VAULT" | tee "$RESULT"
```

For multiple criteria, pass one comma-separated value such as `criterion_a=2,criterion_b=1`. A successful model-backed result satisfies:

```bash
jq -e '
  .attempt.agent_run_id != null and
  .attempt.fallback_reason == null and
  (.attempt.grading_source == "codex" or .attempt.grading_source == "ai")
' "$RESULT"
```

If that assertion fails, read `fallback_reason` before interpreting the score. Provider-unavailable paths can use the supplied self-grade for ordinary practice; a call that started and then failed still retains a failed `agent_runs` receipt. Required diagnostic/exam observations fail closed instead of silently becoming self-grades.

## 4. Inspect the call receipt and accepted evidence

```bash
RUN_ID="$(jq -r '.attempt.agent_run_id' "$RESULT")"
ATTEMPT_ID="$(jq -r '.attempt.attempt_id' "$RESULT")"

sqlite3 -readonly "$VAULT/state.sqlite" <<SQL
.headers on
.mode box
SELECT id, purpose, provider, provider_type, model, prompt_version,
       output_schema, status, started_at, completed_at,
       actual_input_tokens, actual_output_tokens, error_message
FROM agent_runs
WHERE id = '$RUN_ID';

SELECT attempt_id, criterion_id, points_awarded, evidence, notes,
       agent_run_id, grader_tier
FROM grading_evidence
WHERE attempt_id = '$ATTEMPT_ID' AND superseded_at IS NULL
ORDER BY criterion_id;

SELECT attempt_id, grading_source, fallback_reason, agent_run_id,
       fatal_errors_json, feedback_md
FROM attempt_feedback_metadata
WHERE attempt_id = '$ATTEMPT_ID';
SQL
```

Expected relationships:

- `agent_runs.status = 'completed'` for the accepted model call;
- `agent_runs.purpose = 'grading'` and `output_schema = 'GradingProposal'`;
- every active `grading_evidence` row points at the same `agent_run_id`;
- `attempt_feedback_metadata.grading_source` is `codex` or `ai` and `fallback_reason` is null.

The model's proposed total is not trusted directly. Domain validation checks criterion ids and bounds, recomputes the total, applies fatal-error caps, resolves evidence anchors, and only then enters the shared write order described at [[Process Model Output#Apply the resolved grade transactionally]].

## 5. Follow the persistent result

```bash
uv run learnloop show "$ITEM" --json --vault "$VAULT"
uv run learnloop why "$ITEM" --json --vault "$VAULT"
```

Use [[Inspect Persistent State#Trace one attempt]] to connect the immutable attempt, criterion evidence, feedback provenance, surprise projection, and current learner/scheduling views.

> [!failure] A receipt is not authority
> `agent_runs` proves what model/protocol/schema ran. It does not license a grade by itself; accepted evidence exists only after feature-owned validation and transactional attempt application.

## Related notes

- [[AI Provider Configuration Recipes]]
- [[AI Architecture#Output trust boundary]]
- [[Process Model Output]]
- [[Manual Attempt and State Inspection]]
