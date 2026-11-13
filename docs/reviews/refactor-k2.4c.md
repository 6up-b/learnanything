# Refactor K2.4c: one synthesis run, two modes: the append through the shard runner

Branch `refactor/k2.4c-append-shard-runner`, based on main `cb8bcb9a7f` (K2.4a, the shared tail, and K2.4b, the
shared head, landed). Step K2.4c of arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in
`docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.2 (K2.4, last of three sub-steps). Part A is structure track:
an append that fits one call today makes byte-identical model requests afterwards, writes the same rows and returns
the same result. Part B (splitting an oversized append instead of refusing it) is a design only, at the end.

## Step 0: the append's call beside the shard runner

The append's call is `ask` in `_append` (`content/synthesis/source_append.py`, A below) through `_run_reconciliation`
and `_AppendCall`; bootstrap's is `ask` in `_create_study_map` through `_run_synthesis`
(`content/synthesis/source_set_synthesis.py`, S below). Both are called by the shared tail `finish_synthesis_run`
(S:2718-2840) as its `ask`, with their saved answers dropped through its `drop_answers`. Line numbers are at the base
`cb8bcb9a7f`.

| # | Stage | Bootstrap: the shard runner (S) | Append: `_AppendCall` (A) | Difference |
|---|---|---|---|---|
| 1 | Entry | `ask` S:2231-2240 runs `_run_synthesis` under `declared_budgets(run.token_budget)` S:2232 | `ask` A:513-520 runs `_run_reconciliation` A:586-613 with no `declared_budgets` | bootstrap's root receipts record its budgets (`budget_json`, `ai/execution.py:513-524`); an append's record none |
| 2 | Units of work | `_shards(inputs.unit_inventories, synthesis_shard_input_tokens)` S:3175, S:536-552: one or more shards, each a base pass and at most one span round | one unit: the new inventories, whole (`run.context[0]`, A:504), a base call and at most one span round | the append never splits; `_shards([])` is `[[]]`, so both make one call on empty input |
| 3 | Context | `SourceSetSynthesisContext(mode="bootstrap", brief, unit_inventories=shard, exam_profile, registry_index, resolved_spans, shard_ordinal, shard_count, one_facet_per_skill)` S:3190-3196, S:3278-3283; the registry index read once per run S:3174 | `AppendReconciliationContext(source_set_id, subject_id, change_kind, brief, new_inventories, neighborhood, exam_profile, revision_diff, resolved_spans, one_facet_per_skill)` A:590-595, A:606-611; `shard_ordinal` and `shard_count` left at their defaults 0 and 1 | the mode's context; the append's per-run values (change kind, revision diff) are `_append`'s parameters, not on `SynthesisRun` |
| 4 | Request | `request_source_set_synthesis` S:137-147: `execute_structured_operation(purpose="source_set_synthesis", prompt=source_set_synthesis_prompt(context), result_model=SourceSetSynthesis)` | `request_append_reconciliation` A:84-94: purpose `"append_reconciliation"`, `append_reconciliation_prompt`, `AppendReconciliation` | the mode's request; both prompts render `asdict(context)` (`ai_contracts.py:1046-1053`) |
| 5 | Checkpoint | `_synthesis_pass_key(prompt, schema, settings)` (purpose `synthesis_pass`), `ModelCheckpoint(repository, key, "synthesis_pass", SourceSetSynthesis.model_validate)` S:3184-3188, S:3335-3343 | `append_checkpoint_key(prompt, settings)` = `_synthesis_pass_key(..., AppendReconciliation schema, purpose="append_reconciliation")` A:103-110 (pinned, `tests/identity_pins_helpers.py` K3.4), `ModelCheckpoint(..., "append_reconciliation", AppendReconciliation.model_validate)` A:133-136 | purpose and schema; the same key shape |
| 6 | Settings | `{**model_settings(client or transport), "provider": run.provider, "model": run.model}` S:3182 | the same from the run's client A:508 | none (both pass the run's client) |
| 7 | Input estimate | `(len(prompt) + len(json.dumps(schema))) // 4`, at least 1, S:3186 | the same A:138 | none |
| 8 | Shard rows | a completed shard is filed in `synthesis_shard_results` under its base pass's key (S:3290-3301), read before the preflight; a one-request shard is answered from its row (S:3208-3216, S:3241-3256) | none | an append writes no shard row |
| 9 | Input ceiling | before any pass: every uncached base pass against `synthesis_total_input_ceiling` (`check_base_passes` S:3096-3105, S:3218); before each pass, cumulative with the later base passes reserved (`check_next_pass_input` S:3107-3112); `budget_exceeded` | each request alone against `append_input_ceiling`, after its checkpoint misses (A:141-142); the span round is not added to its base call; typed `append_input_over_ceiling` with a diagnostic (A:166-183) | the ceiling, its arithmetic and the refusal |
| 10 | Output limit | `generation_limit(min(synthesis_shard_output_tokens, synthesis_output_tokens - spent))`, exhausted: `budget_exceeded` (S:3114-3120, S:3227-3230) | `generation_limit(append_output_tokens)` for each request, not reduced by the first (A:143) | the request's `output_budget_tokens` |
| 11 | Output check | fresh pass: the larger of the estimate and the provider's reported output against the pass limit (`UsageMeter`, S:3228-3238); every answer, reused too: the estimate against `synthesis_shard_output_tokens` (S:3264, S:3287); the merged total after each shard and at the end (S:3304, S:3324) | every answer, reused too: the estimate (`_result_tokens`) against `append_output_tokens`, "Append reconciliation exceeded its output budget." (A:150-151) | the append ignores the provider's report and has no total |
| 12 | Save | before the output check, usage `{input_tokens_estimate, output_tokens_estimate}` (S:3233-3236) | the same (`answer_stored`, A:146-148) | none |
| 13 | Span round | if the answer has `span_requests`: `_resolve_span_requests(max_count=synthesis_span_request_max_count, char_cap=synthesis_span_char_cap)`, then the same request with the resolved spans (S:3267-3287); hashes kept (S:3289) | the same round and caps (A:597-612); hashes dropped (`_hashes`, A:601) | K2-12: the run records no `resolved_span_hashes` |
| 14 | Saved answers | `_SavedAnswers` S:3136-3163: each pass (and shard row) served, fresh or reused; `discard` drops each while it is still the stored form, then forgets them | `_AppendCall.answers` A:128-129, `discard_answers` A:154-163: the same drop, never forgotten | K2-15: after a rejected match the append's later drop names the first attempt's answers again |
| 15 | After the passes | each shard's ids namespaced `shard_N__` (S:3254, S:3302), shards merged, same-title concepts consolidated, graph structuring (a further checkpointed model call), merged output check, usage record (S:3306-3332) | the brief's preset (`_within_preset` A:519, A:867-889) as review diagnostics | the mode's; an append's single answer is the candidate as the model wrote it |
| 16 | Usage record | `{calls, input_tokens_estimate, output_tokens_charged, shard_count, reused_shards}` plus structuring's, as `SynthesisAnswer.usage` (S:3325-3332) | none (`SynthesisAnswer.usage` is None) | K2-11: an append's run records only the facet-identity plan |
| 17 | Metering | a `UsageMeter` per fresh pass (reads, never drains, `ai/usage.py:131-153`); the tail drains after `ask` (`meters_the_model_call`) | none; drained at `finish_agent_run` | K2-13 (the tail's, unchanged here) |
| 18 | Progress | `_notify` per shard and span round | none (`run.progress` is None for an append) | none |
| 19 | When answers are dropped | the tail: after a rejected match (S:2777-2779) and on the mode's gate failure (S:2785-2788); a budget failure keeps them | the same calls | none |
| 20 | Failure mid-call | the exception leaves `ask` into the tail's arms: both run rows failed; a metered run adds what was spent since its last drain | the same arms; the client drained once, by `finish_agent_run` | K2-13 only |

### Is Part A possible?

Yes. Every difference above is a value the mode supplies or a rule the mode keeps; none is in the shared mechanics,
which are the same in both: checkpoint read before anything is paid, an input preflight, a generation limit, the
call, the answer saved before its output check, one span round on the same caps, the served answers recorded for a
drop. The append's call is one shard of the runner (its new inventories) with no shard row, no namespacing, no merge
and no structuring, under the append's request, checkpoint, context and budget rule.

Where the bytes or keys would move if the append went through `_run_synthesis` as it stands, and what keeps each:

| Would move | Because | Kept by |
|---|---|---|
| prompt bytes, request purpose, result schema | bootstrap's request and context (rows 3, 4) | the mode's request, prompt, result model and context builder; the append's context sets `shard_ordinal` 0 and `shard_count` 1, its defaults, so `asdict` is equal |
| checkpoint key and its stored purpose | `synthesis_pass` and bootstrap's schema (row 5) | the mode's key function (the append's stays `append_checkpoint_key`, the pinned site) and purpose |
| the request's `output_budget_tokens` | the shard and total output arithmetic (row 10); the span round's limit would shrink by the base call's charge | the mode's budget rule: the append's limit is `append_output_tokens` for every request |
| the receipts' `budget_json` | `declared_budgets` (row 1) | a kept mode field |
| client ids in every row | `shard_1__` namespacing (row 15) | the mode's runner is unsharded |
| new `synthesis_shard_results` rows | row 8 | unsharded: no shard row read or written |
| an extra model request | graph structuring (row 15) | the mode's after-pass step (append: its preset) |
| `synthesis_runs.actual_usage`, `resolved_span_hashes_json` | rows 13, 16 | kept mode fields (K2-11, K2-12) |
| which append refuses, with which code | cumulative vs per-request ceiling, reported vs estimated output (rows 9, 11) | the mode's budget rule |

Nothing in the list needs a tag, a switch or a shadow comparison: no key or request moves.
