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

## Part A: what each difference became

| Row | Outcome |
|---|---|
| 1 | Kept: `SynthesisMode.declares_its_budgets` (bootstrap true, append false). The tail wraps the runner in `declared_budgets(run.token_budget)` when it is set. Drift: bootstrap's declaration (Sep 23) predates the append's limits (K3.4), which never declared theirs. Ledger K2-17 (new). |
| 2 | `SynthesisCall.shards(run)`: bootstrap `_shards` over every scope unit's inventory; append one unit, `run.context.new_inventories`. |
| 3 | `SynthesisCall.contexts(run)` returns the pass context builder `(shard, ordinal, shard_count, resolved_spans)`. The append's sets `shard_ordinal=0, shard_count=1`, the fields' defaults, so `asdict` and the prompt bytes are unchanged. The append's per-run values travel in `_AppendContext` (new inventories, neighbourhood context, change kind, revision diff), the run's `context`. |
| 4, 5 | `SynthesisCall.request`, `prompt`, `result_model`, `checkpoint_key`, `checkpoint_purpose`. The append's key is still `append_checkpoint_key` (the pinned identity site); bootstrap's is `_bootstrap_pass_key`, `_synthesis_pass_key` over its schema. |
| 6, 7, 12, 13, 18, 19, 20 | Once, in `_run_synthesis`. |
| 8 | `SynthesisCall.sharded`: a sharded mode files and reads shard rows and namespaces its shards' ids; the append is unsharded, so it reads and writes no shard row and keeps the model's ids. |
| 9, 10, 11 | `SynthesisCall.spend(budgets, unlimited)`: bootstrap's `_SynthesisBudget`; the append's `_AppendBudget` holds each request alone to `append_input_ceiling` (the same typed refusal, built by the same `_over_ceiling`), gives every request `append_output_tokens` as its limit, and checks every answer's own size against it (`check_shard_output`), with no pass, merged or reported-output check. The budget object gained one method, `check_pass_output` (bootstrap's fresh-pass charge check, moved out of the runner), and `check_base_passes` takes the list of unpaid base passes (bootstrap sums them; the append checks each). |
| 13 | The hashes are collected for both; kept: `SynthesisMode.records_resolved_span_hashes` (append false). K2-12 stays open. |
| 14 | One store, `_SavedAnswers`, created by the tail; kept: `SynthesisMode.forgets_dropped_answers` (append false), passed to `discard(forget=)`. K2-15 stays open. |
| 15 | `SynthesisCall.after_passes`: bootstrap's `_structure_merged` (consolidation, graph structuring, the merged check); the append's `_within_the_brief` (the preset, its review records as the answer's diagnostics). |
| 16 | The runner builds the usage record for both; kept: `SynthesisMode.records_call_usage` (append false). K2-11 stays open. |
| 17 | Unchanged (`meters_the_model_call`, K2-13). |

**Why K2-12, K2-15 (and K2-11) stay open.** The brief closes a row only if its difference is gone and the goldens show
the append's rows unchanged. Recording the hashes writes `resolved_span_hashes_json` on every append run (`[]` without
a span round: `complete_synthesis_run` writes any non-None value), and recording the call's usage changes every
proposal-writing append's `actual_usage`. Forgetting dropped answers changes which checkpoint an append leaves when
another run saves the identical answer between its two attempts: the new golden `append_rejected_match_then_gate_failure`
records exactly that (the re-saved span-round answer is deleted today; forgotten, it would remain). Each is one boolean
to flip in the behaviour track, with the golden that moves named in its ledger row.

## The shape

- **`_run_synthesis(run, mode, answers) -> SynthesisAnswer`**, the one model-call path, called by `finish_synthesis_run`
  (which creates the `_SavedAnswers` and drops them). Its mechanics are bootstrap's, line for line; the mode supplies
  values through `mode.call`.
- **`SynthesisCall`** (new, frozen): `request`, `prompt`, `result_model`, `checkpoint_key`, `checkpoint_purpose`,
  `shards`, `contexts`, `spend`, `sharded`, `after_passes`. `BOOTSTRAP_CALL` and `APPEND_CALL`, each beside its mode's
  row. A record of values and functions, like `SynthesisMode` itself (no class hierarchy, no registry).
- **`SynthesisMode`** gains `call`, `epigraph_digest` (bootstrap: the rows' digest; append: topped up from its new
  inventories and neighbourhood, which replaces the tail's branch on `run.context is None`), and four kept booleans:
  `records_call_usage` (K2-11), `records_resolved_span_hashes` (K2-12), `declares_its_budgets` (K2-17),
  `forgets_dropped_answers` (K2-15). It loses nothing: no field was made unnecessary by the single path.
- **`SynthesisRun`** gains `unlimited_token_budget`; its `context` (and `RunScope.context`) is the mode's own value,
  the append's `_AppendContext`.
- **`finish_synthesis_run(run, mode, *, apply)`**: `ask` and `drop_answers` are gone as parameters. `apply` is the only
  per-run callable left (the mode's apply step), with the head's `decide_scope` (K2.4b).
- **`BOOTSTRAP`** moved below the shard runner in `source_set_synthesis.py`, since its call names the runner's helpers.

## Deletion proofs (strategy §2.1)

- **`source_append._AppendCall`** and **`source_append._run_reconciliation`** (`75969ada6f`): their one caller was
  `_append`'s `ask`. `git grep -nw` over `src`, `tests`, `scripts`, `apps`, `learnloop_sidecar` and `learnloop_mobile`
  finds no other reference; both are private, so no `importlib`, Typer, `METHOD_REGISTRY`, `MODULE_INVENTORY` or
  `_reg_const` entry names them; no frontend, replay, rebuild or upgrade path calls a model. The generated module
  references named them and are regenerated below. No test patched or imported either.
- **`finish_synthesis_run`'s `ask` and `drop_answers` parameters, `_append`'s and `_create_study_map`'s `ask`
  closures, `_run_synthesis`'s old parameters**: private to the two modules; the only callers are the two
  orchestrators, changed in the same commit.
- **Kept on purpose:** `request_append_reconciliation` (`tests/test_structured_transport_parity.py` calls it, and it is
  the append's request), `append_checkpoint_key` (the K3.4 identity pin names it), `_over_ceiling` and
  `APPEND_INPUT_OVER_CEILING` (the refusal Part A keeps).
- The append module no longer imports `ModelCheckpoint`, `generation_limit`, `model_settings`, `json`,
  `_resolve_span_requests` or `SynthesisAnswer`; `source_set_synthesis` no longer imports `digest_for_append`. Each is
  still defined where it was and used there.

## Goldens (P-golden)

Five cases added to `tests/test_synthesis_tail_golden.py` at the base, before any source change (`696c9e326e`,
`b79d5527ef`), and unchanged by the move, with the 20 earlier cases. The new cases also record every request as sent
(result model, schema digest, `output_budget_tokens`, timeout, reasoning effort, isolation) and the receipt each opened
(its schema hash and the budgets declared on it), through `_record_sent`, so a call path that sent anything else would
fail them; the earlier 20 files are untouched (the extra record is only in the new cases).

| Case | Covers |
|---|---|
| `append_span_round` | a span round under `append_input_ceiling = 7,620`: each request alone fits (about 7,559 and 7,616 tokens), their sum does not, so both are sent; both checkpoints, the span round's request, the result's `span_request_count`, no hashes on the run |
| `append_rerun_reuses_saved_answers` | `append_output_tokens = 200`: the span round's answer (about 399) is saved, then fails the run (`budget_exceeded`, both rows failed); the rerun under the default budget makes no append request and persists |
| `append_rejected_match_then_gate_failure` | a rerun after the whole append (a call and its span round) was rejected: the saved answers reproduce it and are dropped; while the fresh call runs another run saves the span round's answer again; the fresh answer, an exam-only reword, fails the gates and is dropped (K2-15's race: the re-saved answer is deleted) |
| `append_fails_part_way` | the provider raises on the span round: the first answer stays saved, both rows failed, the agent run records the 200/20 tokens the client reported |
| `bootstrap_sent_span_round` | a bootstrap with a span round, recorded as sent: both passes' output limits and the budgets declared on their receipts |

Nominations on were not added: they change only the neighbourhood's content (the head's, K2.4b), which reaches the call
through the same context builder; `test_graph_nomination_ingest` covers the path and passes.

All 25 passed under `PYTHONHASHSEED` 0-7 and `-n 4` at the base; at the tip they pass unchanged.

## Measures

| | base `cb8bcb9a7f` | tip |
|---|---|---|
| `source_set_synthesis.py` lines | 4,183 | 4,279 |
| `source_append.py` lines | 1,146 | 1,146 |
| both | 5,329 | 5,425 |
| `_run_synthesis` | 167 | 145 |
| `finish_synthesis_run` | 123 | 126 |
| `_create_study_map` | 70 | 56 |
| `_append` | 85 | 67 |
| `_run_reconciliation` + `_AppendCall` | 28 + 51 | none |
| functions over 200 lines in the two files | 2 (`_normalize` 1,081, `_normalize_append` 221) | the same 2 |
| per-run callables the tail takes | 3 (`ask`, `drop_answers`, `apply`) | 1 (`apply`) |

The two files are 96 lines longer together. The model-call path exists once (the append's 79 lines of call are
gone), but naming the per-mode values costs lines: `SynthesisCall` with a line of documentation per field, the
append's budget rule as a class of the same shape as bootstrap's (45 lines where `_AppendCall` inlined two checks),
the two modes' small call functions, and four kept booleans with their documentation.

## Judgment calls

1. **The call's values are a record on the mode (`SynthesisMode.call`), not more `SynthesisMode` fields.** Ten values
   say how a mode asks the model; on `SynthesisMode` they would double its length and mix the call with the tail's
   decisions. The kept differences stay on `SynthesisMode`, beside the five K2.4a kept, so the list of kept
   behaviour is in one place.
2. **The append's budget rule is an object with bootstrap's methods (`_AppendBudget`)** rather than flags on the
   runner: the two rules differ in five places (per-request vs cumulative input, a fixed vs a shrinking output limit,
   size vs reported output, no merged check, the refusal's type), and one object per rule keeps each readable.
3. **K2-11, K2-12, K2-15 stay open (see above), K2-17 is filed**, all four as kept booleans, by the brief's rule; the
   orchestrator expected K2-12 and K2-15 to close here. Each is now a one-field flip with a golden that moves.
4. **The epigraph digest became a mode field** because the run's context is now the append's record (it carries the
   change kind and revision diff its request reads); the tail no longer knows the context's shape.
5. **`check_base_passes` takes the unpaid passes as a list** so the append's rule checks each request alone rather
   than a sum; with one unit they are equal, and Part B needs the list.
6. **One source commit for the move.** The two modules change together (the tail's signature and both callers), so
   the move could not be split into commits that each keep both modes running; the goldens and the targeted tests
   were run on it before it was committed.
7. **`_record_sent` records receipts through `observe_model_calls`**, a test-only observer; it changes no row (the
   production observer is what writes receipts).
8. **Unused imports** after the move were removed with `ruff check --select F401 --fix` on the two files; every other
   edit was a short script replacing one exact block (asserted to occur once) or the Edit tool.
