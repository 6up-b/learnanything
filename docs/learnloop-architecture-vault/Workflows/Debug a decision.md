---
title: Debug a decision
aliases:
  - Why x and not y
  - learnloop why
  - Debug a Decision Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/why/reader.py
  - src/learnloop/why/reconstructed.py
  - src/learnloop/provenance.py
  - src/learnloop/db/stores/provenance.py
  - src/learnloop/cli/app.py
  - src/learnloop_sidecar/handlers/why.py
  - tests/test_why_cases.py
  - tests/test_why_reader.py
  - tests/test_why_real_cases.py
tags:
  - learnloop/workflow
  - learnloop/debugging
  - learnloop/decision
---

# Debug a decision

Start with `learnloop why` when a queue item, plan block, probe, build or figure needs an explanation. It opens SQLite read-only and runs no maintenance or state sync. The CLI and the desktop's `why.get` use the same [[Reference/Modules/learnloop/why/reader|reader]]. [[ADR-017 One decision record, one trace id, one entry point]] defines the record. [[Inspect Persistent State#Ask why a decision went the way it did|Inspect Persistent State]] shows how to follow its detail pointers.

## Pick a target

Use the vault path and a real ID from the relevant view or receipt. With no target, `why` starts from the latest decision. A record ID finds its trace. The same trace can span the original request and the background work it started.

```bash
learnloop why --json --vault "$VAULT"
learnloop why "$TRACE_ID" --json --vault "$VAULT"
learnloop why "attempt:$ATTEMPT_ID" --json --vault "$VAULT"
learnloop why "block:$BLOCK_ID" --json --vault "$VAULT"
learnloop why "offer:$OFFER_ID" --json --vault "$VAULT"
learnloop why "item:$ITEM_ID" --json --vault "$VAULT"
learnloop why "figure:$FIGURE_ID" --json --vault "$VAULT"
learnloop why "job:$JOB_ID" --json --vault "$VAULT"
```

A bare practice item ID also gives its scheduler explanation. `--kind` narrows the answer to a particular record kind. Use the latest `figure_request` when a press produced no figure ID. Use the planner's job ID as the trace target for a Study Map build.

## Read the answer

Open `decisions` for what won, the rule code, the alternatives and why they lost, and the inputs and versions recorded at the time. Use the record's detail pointer for richer domain rows. A router choice can include the objective trace and an outcome derived at read time. `next` follows child records. For the selection and serving boundaries see [[Scheduling and Selection]].

A plan decision can point back to the prefetch trace. `model_calls` shows the receipt IDs, purposes, statuses and times. `discarded` includes calls whose result did not reach the decision in time. `unclaimed` identifies router calls whose boundary was never served. The configured timeout and the time between prefetch start and decision are separate inputs.

Records survive payload pruning. A pruned record keeps its identity and carries the `payload_pruned` flag, with no retained alternatives. See [[Reference/Database/Tables/decision_records|decision records]] for the row contract.

## Follow the boundary that made the choice

| Question | Where to look |
|---|---|
| Why did Today choose a different block? | The `plan_block` record gives the rule and mixture support. Its `model_answer` children show failures and timeouts. For a withdrawn offer, follow `offer_withdrawn` to the forcing items and the next block. |
| Why did this item disappear from the queue? | `item:<id>` can show its scheduler explanation, slate history and current exclusion. A malformed stored row can make the explanation unavailable. The response identifies the failing table, row and column when available. |
| What did a Study Map build include or apply? | The planner trace carries `ingest_build_scope`, `ingest_inventory_choice` and `ingest_auto_apply` at the boundaries the job reached. Their inputs name the scope, selected inventory rows or applied and waiting proposal items. See [[Build a Study Map]]. |
| Why did Show me do nothing? | `figure_request` gives the refusal code, reuse match, or rich job reference when recorded. A reused figure has status `chosen` and rule `reused`. Check `figure_admission` for a gate hold and `figure_withheld` for a figure refused at delivery or listing. |
| Why did a video stop? | On the job trace, read `figure_rich_author` for attempt verdicts and `figure_rich_stop` when an execution stopped without producing a row. A requeue keeps the earlier stop records. See [[Concepts/Figures|Figures]]. |
| When did figure prebuilds start? | `learnloop why --kind figure_prebuild --first-build --json --vault "$VAULT"` compares the first build with the preceding skips and the first measured latency. |

## Probe answers and failed hooks

Use `why attempt:<id>` for the grade, diagnosis and follow-up trail. A pinned causal answer the classifier declines leaves an excluded `probe_classification` record with a rule code. A successful classification leaves a discriminating observation. Repeating the classifier for the same attempt is silent. An existing observation belonging to another or an unknown attempt gives `already_observed`. Ordinary unpinned diagnostic answers go through the episode posterior.

A failed `diagnosis_step` records the exception class and location. Grade-keyed hooks carry `phase=grade_keyed`, and their failure leaves the attempt complete. An evaluator stop records its earlier passing rules in the episode row's `completion_detail_json.rules_passed`; direct controls omit the rules they did not evaluate. See [[Diagnosis and Remediation#What why can answer]].

## Old decisions

The reader reconstructs supported router, offer, figure and prebuild cases from the rows they left. Each reconstructed answer is labelled `reconstructed`. Its `inferred` field identifies conclusions pieced together from timing and neighboring rows. The current router timeout can appear separately as `timeout_s_now` when the decision-time value is unknown. The reader never backfills a decision record, and an older target can have no answer.

## Payloads and the desktop view

The CLI's `--payload` adds stored prompts and outputs for named call receipts under their own retention. The desktop RPC returns the sanitized view with withheld paths listed, and offers no payload flag. `why.get` is outside the phone allowlist. Use [[Reference/Modules/learnloop_sidecar/handlers/why|the sidecar handler reference]] for the RPC boundary.
