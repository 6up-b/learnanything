---
title: Debug a decision
aliases:
  - Why x and not y
  - learnloop why
  - Debug a Decision Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.57
last_reviewed: 2026-11-10
source_commit: a8b3ab6f6827d33a45b286c6005c248e9de4eb6a
source_commit_timestamp: "2026-11-10T12:48:49-05:00"
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

When LearnLoop chose something you didn't expect (an item, a block, a withdrawn offer, a failed figure, a pre-build), `learnloop why` answers "why x and not y" from what was stored when it decided. It is a pure read: a read-only connection, no state sync, no maintenance. The record design is [[ADR-017 One decision record, one trace id, one entry point]]; what each record kind holds is in [[Inspect Persistent State#Ask why a decision went the way it did]].

## Pick a target

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
uv run learnloop why --json --vault "$VAULT"                         # latest: the newest decision's trace
uv run learnloop why 01J9TRACE0000000000000000 --json --vault "$VAULT"  # a trace id (one learner action)
uv run learnloop why 01J9RECORD000000000000000 --json --vault "$VAULT"  # a record id: that record's trace
uv run learnloop why attempt:att_example --json --vault "$VAULT"      # an attempt's grade, diagnosis, follow-up, evidence
uv run learnloop why block:01J9BLOCK0000000000000000 --json --vault "$VAULT"   # a plan block's decision
uv run learnloop why offer:01J9DECISION000000000000 --json --vault "$VAULT"    # a lesson offer, and its withdrawal
uv run learnloop why figure:fig_example --json --vault "$VAULT"       # a figure's author attempts
uv run learnloop why item:pi_example --json --vault "$VAULT"          # an item: scheduler explanation, slates, exclusion
uv run learnloop why --kind figure_prebuild --first-build --json --vault "$VAULT"
```

`--kind K` keeps one record kind. Without `--json` the same answer prints as lines.

## Read the answer

Each decision appears under `decisions` with the same fields:

| Field | What it answers |
|---|---|
| `chosen`, `rule`, `status` | What won, and why, as a code (`forced_items`, `chooser_error`, `no_measured_latency`) |
| `alternatives` | What lost: each `ref` with its `p` or `score` and `lost_by` (the rule it lost by) |
| `inputs` | The facts as of then: numbers, ids and codes (`timeout_s`, `waited_ms`, `wait_min`, `waits_n`) |
| `decided_by`, `versions`, `seed` | Who decided (`mixture`, `router_llm`, `lane_quota`), with versions and the seed |
| `next`, `outcome` | What came next: records naming this one as their parent; for a router decision, its outcome row |
| `discarded` | Calls of the trace that answered after the decision took its answers (`late_ms`), or never answered |
| `objective_trace` | For a router decision, the router objective trace `learnloop router trace <decision>` prints |

Top-level `model_calls` lists the trace's calls (ids, purposes, statuses, times; never the prompt or the output), and `unclaimed` the router calls whose decision was never made (a key that changed before the serve, an evicted prefetch).

## Old decisions: "reconstructed"

A decision made before its records existed (migration 253, or a boundary arc B had not reached yet) has no record and gets none backfilled. `why` answers it from the rows it left, under `reconstructed`, every answer labelled `"label": "reconstructed"`:

- a router decision id (or `block:`, `offer:`, `decision:`): the `router_decisions` row, each model's status, the mix's alternatives, and its calls joined through the boundary key, each with its output `present` or the reason it's `absent`;
- an offer taken back: the `expired` response, the forced items (from the next decision), the workflows and generation jobs of that window;
- `figure:`: the `interactive_figures` row, its verification reduced to typed codes (`prediction_invalid`), its author calls;
- `--first-build`: the pre-build ledger, the skips before the first build per trigger kind, and the first measured latency.

A field found only by ordering rows in time is listed in that answer's `inferred`. The configured router wait was never stored on old rows: `timeout_s_basis = "not_stored"`, with the vault's setting now in `timeout_s_now`.

## Examples (synthetic ids)

**A router LLM answer that came too late.** `why 01J9TRACE0000000000000000 --json` shows a `plan_block` with `inputs.timeout_s = 8` and `inputs.waited_ms = 8012`, and a child `model_answer` with `decided_by = router_llm`, `status = timeout`. Under `discarded`: `{"call_id": "call_example", "late_ms": 2310}`; the text output says "answered 2.3 s late, discarded". Add `--payload` to see that call's prompt and answer from its receipt.

**An offer withdrawn for a probe.** `why offer:01J9DECISION000000000000 --json` shows `offer_withdrawn` with `rule = forced_items`, `parent_id` the offer's `plan_block`, the forced probe under `alternatives` with its `workflow` and `source_attempt`, and under `next` the `plan_block` that served it.

**Why pre-builds started.** `why --kind figure_prebuild --first-build --json` gives `first_build.last_skip` (`no_measured_latency`), `first_build.first_build` (`sampled_eu_positive`), `changed` (`waits_n: [0, 1]`, `wait_basis: ["none", "author_call"]`), `first_measurement` and `measurement_between: true`.

**A practice item's stored row is malformed.** `why item:pi_example --json` still answers: `source = "unavailable"` with `explanation_error` naming the exception class, where it was raised and the bad rows (`{"table": "followup_tasks", "id": "...", "column": "context_json"}`), never their content.

## Payloads, and the desktop's glass-box view

`--payload` adds each named call's prompt and output from `model_call_receipts`, under the receipts' own retention. It exists only on the desktop CLI. The sidecar's read-only `why.get` RPC (for the UX stage's glass-box view) returns the same answer with every string that is not an id, a number or a code removed and its path listed in `withheld`; it never returns a payload, and it is not on the phone's allowlist.

## Related notes

- [[Inspect Persistent State]]
- [[ADR-017 One decision record, one trace id, one entry point]]
- [[Scheduling and Selection]]
