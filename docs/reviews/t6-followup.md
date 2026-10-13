# Slice 2 T6 follow-up: output budgets, low effort, the dense_plus_bm25 pool, tutor timing

Branch `slice-2/t6-followup`, worktree `learnanything-t6-followup`, base
`68213d96` (main). Every item is an owner decision (2026-10-12). The owner's
words: "get rid of the hard coded output caps for T6 or B6 or extend them
significantly so they dont cut off--we're cutting the model off prematurely
and its probably affecting output quality significantly. Im fine with testing
a T6 follow up with a new candidate pool, upping the caps + low effort, no
tutor deadline cancellation for now but log the time spent."

What the owner's T6 re-evaluation with Claude Haiku 5.5 (main checkout,
`fixtures-local/t6-rerun/`, read only) found, and what this stage does about
it:

| Finding (Haiku rerun) | This stage |
|---|---|
| Hard-coded output caps truncated Haiku (writer 28 of 36 calls, rewrite 6 of 68) | One output-budget policy for every LLM role (§1); 0 truncations in this stage's runs |
| Verification lifts the relevant share of tutor spans from ~70% to ~93%, but takes ~6 s because Haiku reasons by default | Low reasoning effort for the rewrite and the verification by default (§2); verification is now measured inside the bench (§5) |
| Dense alone ≥ the BM25+dense RRF hybrid on generated questions | New pool `dense_plus_bm25` behind `source_retrieval.pool` (§3) |
| The rewrite helps only on large libraries | Measured again per query type (§5) |
| The bench only asked single-concept generated questions; on the 7 real learner questions the hybrid beat dense (+0.09) | Keyword, compositional and procedural questions, every logged learner question, results per type (§5) |


## 1. One output-budget policy for every LLM role

**The policy** (`src/learnloop/ai/output_budget.py`, config in `[ai]`):

- **One generous default.** `ai.output_tokens = 16384`: room for a reasoning
  model's thinking and its answer. `ai.route_output_tokens.<route> = N` (at
  least 256; unknown route names are refused at load) replaces it for one
  route. A profile's own `max_tokens` (the provider or profile maximum, e.g.
  DeepSeek Flash's 8,192) is a ceiling: it replaces the default for that
  profile and holds a route override to it, since the chat transport never
  sends more. *(Codex review F6: this said the route override "replaces
  both", which the transport's clamp contradicted.)*
  `output_budget(config, route, provider=...)` resolves it; `PaidRoute`,
  `ProjectRoute`, `ReviewSpend` and `PFCaller` carry the resolved budget.
- **Used for spend reservations.** The budget is both the request's
  `max_tokens` (on metered routes, `generation_limit`) and what admission
  reserves; every truncation retry is reserved at the larger allowance it is
  sent with *(Codex review F1: a transport-owned retry was sent at double the
  budget but reserved at the first request's estimate)*. Caps that could no
  longer admit one call at the bigger reservation were raised (below).
- **Where a provider allows, no low `max_tokens`.** A caller-budgeted request
  sends the generous budget; an unbudgeted call (tutor answers, live grading,
  authoring, ...) still sends none unless its profile declares a maximum, as
  before.
- **A truncation is never accepted.** `finish_reason = "length"` raises
  `AIOutputTruncated` in the chat transport (as before, after metering).
  New: it is logged as an event naming the role, provider, model and budget
  (`record_truncation`, logger `learnloop.ai.output_budget`), the attempt's
  receipt keeps status `truncated` and its finish reason, and the call is
  retried **once at double the budget, held to the transport's ceiling** (the
  profile's `max_tokens`; a call already at it fails at once, since another
  request would have no more room; Codex review F6):
  - callers that admit each physical request themselves (`PaidCalls`,
    `PFCaller`, the family and contamination judges, the LLM probability arm)
    retry in their own loop through `TruncationRetry` (given the client's
    ceiling, `output_ceiling`): the retry is admitted and charged as a retry
    at the budget it sends, and its root receipt's `budget_json` carries
    `truncation_retry: {role, model, previous_budget, budget}`; the events are
    in each command's report (`truncations`);
  - callers that admit each further physical request as it starts (Slice 1's
    `ReviewSpend` on metered routes, the project probes) let the chat transport
    retry itself (`truncation_retry_allowed`), at most to the profile's
    `max_tokens`; the retry is admitted as a retry when it starts, reserved at
    the output allowance it is sent with (Codex review F1);
  - nowhere else: an owner-set budget (`[ingest.budgets]`, exempt) is never
    exceeded, and an unbudgeted call sends no `max_tokens` (or its profile's
    maximum), so a length stop there is the provider's or profile's own limit;
  - a second truncation, a spent retry cap or a maximum already reached fails
    the call (logged with `next: fail`). The answer is never used.
- **Reasoning effort per route** (§2) is part of every request identity
  (checkpoint keys, request-derived ledger ids) when set, so an answer produced
  at another effort is never replayed for it.

**Exempt** (owner): the Decider's typed answers (`DECIDER_OUTPUT_TOKENS = 16`, a
decision API, not a chat completion) and the owner-set synthesis budgets in
`[ingest.budgets]` (inventory 3,000, shards 10,000, synthesis 16,000, append
10,000). **Left alone on purpose:** `diagnosis/recurrence/benchmarks.py`
(`WRITER_OUTPUT_TOKENS = 300`, B1's writer): the in-flight `fix/owner-batch-2`
branch changes it and the orchestrator raises its default at that merge.

**Every LLM call site and its budget now.** "Policy" means `ai.output_tokens`
(16,384) unless the serving profile declares `max_tokens` or the route has an
`ai.route_output_tokens` entry.

| Call site (route) | Before | Now | Truncation retry |
|---|---|---|---|
| `source_retrieval/queries.py` live rewrite (`source_query_rewrite`) | `REWRITE_OUTPUT_TOKENS` 1,200 | policy, effort **low** | `PaidCalls` loop |
| `source_retrieval/verify.py` tutor-span verification (`source_rerank`, via `practice_index/listwise.py`) | `VERIFY_OUTPUT_TOKENS` 2,500 | policy, effort **low** | `PaidCalls` loop |
| `source_retrieval/bench.py` question writer (`source_query_writer`) | `QUESTION_OUTPUT_TOKENS` 1,500 | policy | `PFCaller` loop |
| `source_retrieval/bench.py` relevance labels (`source_relevance_judge`) | `LABEL_OUTPUT_TOKENS` 3,000 | policy | `PFCaller` loop |
| `source_retrieval/evaluation.py` rewrite in the report (`source_query_rewrite`) | 1,200 | policy, low | `PFCaller` loop |
| `source_retrieval/evaluation.py` verification in the report (`source_rerank`) | (not measured) | policy, low (the production step) | `PaidCalls` loop |
| `source_retrieval/b4.py` writer and labels | 1,500 / 3,000 | policy | `PFCaller` loop |
| `practice_index/evaluation.py` query writer (`practice_query_writer`) | `QUERY_OUTPUT_TOKENS` 1,200 | policy | `PaidCalls` loop |
| `practice_index/evaluation.py` relevance judge (`practice_relevance_judge`) | `LABEL_OUTPUT_TOKENS` 3,000 | policy | `PaidCalls` loop |
| `practice_index/retrieval.py` find_practice rerank (`practice_rerank`) | `RERANK_OUTPUT_TOKENS` 2,500 | policy | `PaidCalls` loop |
| `practice_index/dossiers.py` facet dossiers (`practice_dossier`) | `DOSSIER_OUTPUT_TOKENS` 1,800 | policy | `PaidCalls` loop |
| `ops/family_proposals.py` family judge (`pf_family_judge`) | `OUTPUT_TOKENS` 1,024 | policy | own loop (`TruncationRetry`) |
| `ops/contamination/judge.py` leak/reveal judge (`contamination_judge`) | `OUTPUT_TOKENS` 1,024 | policy | own loop (`TruncationRetry`) |
| `ops/embedding_compare.py` B2 skeleton (`pf_generator`) / freshness (`pf_isomorph_judge`) | `output_tokens=1200` / `2500` | policy | `PFCaller` loop |
| `ops/embedding_compare.py` valid-alternative writer / verifier / grader | 6,000 / 2,500 / 4,000 | policy (the plan's trace bound follows: 4/3 of the writer budget, in bytes) | `PFCaller` loop |
| `ops/pf_reports.py` pairwise judge (`pf_selection_judge`) | `output_tokens=800` | policy | `PFCaller` loop |
| `ops/pf_generation.py` 12 roles (skeleton 1,200, program 6,000, proposer/single-shot/source 8,000, panel 1,500, equivalence 2,500, structure 800, freshness 2,500, selection 1,500, closed book 1,500, span support 1,200) | per-role dict | policy | `PFCaller` loop |
| `diagnosis/recurrence/backlog.py` + `guard.py` same-cause judge (`same_cause_judge`) | `JUDGE_OUTPUT_TOKENS` 600 (passed as the profile maximum) | policy | transport (`ReviewSpend` admits it) |
| `diagnosis/offline_review/spend.py` allowances: grading / diagnosis / judge / generator / any other route (escalated repair, live judge) | 6,000 / 8,000 / 4,000 / 6,000 / 2,000 | policy (embedding stays 0); `ReviewSpend` now takes the vault config so route overrides apply | transport |
| `projects/probes.py` authoring / closed book / grading (`project`, `grading`) | 6,000 + 4,000 headroom / 250 per question + 4,000 / 250 per item + 4,000 | policy (resolved with the route) | transport |
| `cli/success_head.py`, `cli/field.py`, `cli/evaluation.py` `--output-tokens` (LLM probability arm, `llm_probability_llm`) | 256 | policy; the option still overrides | own loop (`TruncationRetry`) |
| `cli/field_classification.py` `--output-tokens` (`field_question_classifier`) | 512 | policy; the option still overrides | none: one physical call per question by contract, so a truncation is logged and stops the command |
| `diagnosis/recurrence/benchmarks.py` B1 writer | 300 | **unchanged** (owner-batch-2) | `PFCaller` loop |
| `field/probability_prep.py` Decider | 16 | **exempt** | none (typed answers) |
| `content/synthesis/*` inventory / shards / synthesis / append | `[ingest.budgets]` | **exempt** (owner-set) | none (the owner's budget is the limit): raised and logged, as before plus the event |
| Unbudgeted structured calls: `tutor/tutor_qa.py`, `tutor/teach_back.py`, `tutor/promotions.py`, `attempts/grading*.py` and `blind_grading.py` (live), `content/authoring/*`, `content/pipeline/source_ingestion.py`, `content/proposals/proposals.py`, `content/synthesis/vault_epigraphs.py`, `curriculum/*`, `diagnosis/diagnostic_gate.py`, `misconceptions.py`, `probe_dialogue.py`, `probe_instance_generation.py`, `reader/*`, native media transcription and PDF markdown | no cap (profile/provider maximum) | unchanged: no `max_tokens` unless the profile sets one | none possible (the provider's or profile's own maximum): raised and logged |
| Codex (any route on `codex_sdk`) | the budget as a prompt hint | the policy budget as the hint (the app-server has no hard output cap, so no length stop) | n/a |

**Caps raised so one call fits its bigger reservation.** The reservation is
the prompt plus the full output budget, and a truncation retry reserves twice
the budget:

- `source_retrieval.rewrite_max_cost_usd` 0.01 → **0.15**, `rerank_max_cost_usd`
  0.05 → **0.30**, `practice_index.rerank_max_cost_usd` 0.05 → **0.30** (per
  question; reservations, never what is billed);
- the rewrite's token cap is now `2 × 6,000 + 3 × budget` (was 40,000), the
  verification's `2 × 60,000 + 3 × budget` (was 200,000);
- `learnloop sources search --deep` defaults `--max-tokens` 60,000 → 120,000
  and `--max-cost-usd` 0.02 → 0.25; its dry run plans the retry at double the
  budget.

**Consequences for reuse.** The output budget is part of every paid request's
identity (checkpoint keys, request-derived ledger ids, the probability arms'
settings hash, the review runs' route bindings), so work checkpointed under an
old cap is not replayed under the new budget: a rerun pays again once. This is
deliberate (an answer produced under a cap that cut reasoning short is not the
answer the new budget asks for).

## 2. Low reasoning effort for the rewrite and the verification

- `ai.route_reasoning_effort` (default `{source_query_rewrite = "low",
  source_rerank = "low"}`; an owner table merges over the defaults; `""` or
  `"profile"` keeps the profile's `reasoning_effort`). Per profile, the existing
  `reasoning_effort` still applies to every other route.
- Requests carry it (`StructuredRequest.reasoning_effort`, set from
  `requested_reasoning_effort`): OpenRouter sends `reasoning: {effort}` (the
  route wins over a profile that disables thinking); an OpenAI-compatible
  profile with `thinking` enabled sends `reasoning_effort`; Codex uses it as
  that turn's effort and restores the profile's after. Other transports ignore
  it.
- Applied by `PaidCalls` (the live rewrite and verification, practice-index
  roles if the owner sets them) and `PFCaller` (the report's roles, by their
  routes).

## 3. The candidate pool switch

`source_retrieval.pool = "dense_plus_bm25" | "hybrid_rrf"`, with
`source_retrieval.pool_keyword_extras = 4` (`src/learnloop/source_retrieval/search.py`,
`dense_plus_bm25()`):

- **`dense_plus_bm25`**: the dense top `k` (the `meaning` list; for a rewritten
  question, `meaning` fused by rank with `rewrite_meaning`), then the BM25
  (`keyword`) top `m` that dense did not return, then the same for each caller
  list (the tutor's LO-linked spans), deduplicated. Ranked dense first for
  display. BM25 only widens the pool. Every hit carries its `pool_role`
  (`dense`, `keyword`, `provenance`) and its rank in every list; the result's
  `pool` says the mode, `k`, `m` and how many extras each list added.
  - Library deep search: `k = limit - m` (36 + 4 at the reader's 40 hits), so
    the page shows dense hits first and the BM25 extras last.
  - Tutor: the dense top `tutor_candidate_pool` (12) plus up to 4 BM25 and 4
    linked-span extras go to the verification, which picks at most 4. Four
    spare dense candidates are fetched so that withholding a span that leaks
    the expected answer still leaves 12; a spare that is also in the BM25 or
    linked-span top 4 stays as that list's extra.
- **`hybrid_rrf`**: T6 as merged (every list fused by reciprocal rank).
- **Fallback.** With the scope's dense index not `ready` (incomplete,
  partial, disabled) or no query vector, a deep search uses `hybrid_rrf` and
  says why (`pool.fallback`). A typing search is keyword only either way.
- Recorded on the tutor question's receipt (`source_retrieval.pool`) and in the
  library response (`retrieval.pool`). No frontend change: the basis label
  still names the evidence used.

## 4. Tutor timing: logged, never cancelled

- **No deadline cancellation** (owner: "not now"). The tutor's retrieval no
  longer passes a deadline, so no request carries a time-box timeout and no
  step is skipped for time. `source_retrieval.tutor_deadline_cancels = true`
  restores T6's time box exactly. The library's deep search keeps its time box
  (`retrieval_timeout_seconds`, display only).
- **Every step is timed on the question's receipt**
  (`question_events.source_context.source_retrieval.timings_ms`): `rewrite`,
  `query_embedding`, `retrieval` (the search minus its two paid steps),
  `verification` and `total`, in milliseconds, plus `deadline: "soft"` and
  `over_soft_deadline`, the steps over `retrieval_timeout_seconds` (15 s).
  `tutor_qa` adds only the provider's wall time (`timings_ms.total`) on paths
  where the provider timed nothing (`tutor_rerank` off, verification
  unavailable, a provider failure; the kill switch still records nothing): no
  other `tutor_qa` change.
- **`learnloop sources report --vault <v> [--since ISO] [--json]`**
  (`source_retrieval/timing.py`): per step n, p50, p90, max and the count over
  the soft deadline, a note for each step that exceeded it, the basis,
  verification and pool counts, and the truncated LLM answers by purpose and
  model (root receipts with status `truncated`). Read only.

## 5. The evaluation

### 5.1 What the report now measures

`learnloop embeddings compare --suite source_retrieval` (harness version
unchanged; benchmark manifest `t6-eval-v2`; `source_retrieval/evaluation.py`):

- **Query types.** The generated questions are split evenly across four
  types, each from its own seeds: `conceptual` (the first run's prompt
  `source_eval_question.v1` and seed order, so its seeds are a prefix of every
  earlier run's), `keyword` (an exact-term search, 1 to 6 words),
  `compositional` (two blocks at least 3 apart, from different sections of one
  source; the question needs both; either seed counts for seed hit) and
  `procedural` (how to compute, derive, prove, apply or check). Each type has
  its own prompt version.
- **Every logged learner question.** No longer capped at a quarter of
  `--max-cases`: probability has 8 (the earlier runs took 7), arxiv_v2 1.
- **Systems.** The five earlier systems, plus `pool_rewrite` (the library's
  `dense_plus_bm25` deep search with the production rewrite; its top 10 is
  dense first) and three systems that run the **production verification**
  (`verify_spans`, route `source_rerank`, its prompt, low effort, ledger and
  receipts) inside the bench on tutor-shaped pools: `hybrid_verify` (today's
  `hybrid_rrf` top 12), `pool_verify` (dense top 12 plus the BM25 top 4 dense
  missed) and `dense_verify` (dense top 12). A verification system's ranking is
  its picks, then the rest of its pool; its picks are also scored as what the
  tutor would get (relevant share of picks, nDCG@picks against the best the
  pool allowed, picks per question, empty picks while a relevant span was in
  the pool, latency). The verification runs under the harness's budget, price
  and receipts (`verify_spans(budget=, price_per_million=)`, a new
  `source_verify` role on route `source_rerank`).
  *(Codex review, `docs/reviews/t6-followup-codex-review.md`: as first built,
  the pools were the library scope's, without the tutor's linked spans, answer
  withholding, item exclusions or practice question (F5); a failed
  verification was scored as its unverified pool (F4); verification attempts
  escaped the harness's shared caps (F2); the dry run planned no candidates or
  pairs (F3). Now the pools are the tutor's own (`tutor_pool`, per question: a
  logged practice or feedback question keeps its item, a logged library
  question its note's LOs, a generated or reader question is asked as a
  library question about the LOs the reader links to its passages), a
  verification that did not run is not scored and blocks that system's
  verdicts, every attempt passes the shared caps after the cache, and the dry
  run plans every candidate and pair. §5.9 reports the rerun.)*
- **Labels** cover the union of every display system's top 10 and every
  verification pool (two passes, as before), so every pick is labelled.
- **Per query type**: means for every system, the paired differences that
  decide the pool and the rewrite, and the verification metrics.

### 5.2 Runs

Fresh backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of
the worktree's tracked `fixtures/probability` and `fixtures/arxiv_v2` under the
worktree's `fixtures-local/t6fu/` (`scripts/setup_copies.py`): the
probability practice item that does not parse
(`pi_exercise_01kyn22qcffk7sae9ttxvz4j5n.yaml`) set aside on the copy, and the
copy's `learnloop.toml` given the four T6 routes on a new
`openrouter_haiku` profile (`anthropic/claude-haiku-5.5`, `json_object`), the
`openrouter_embedding` route and profile, `[embedding] enabled` and
`backfill_enabled`, and `source_retrieval.llm_price_per_million = 0.5` (Haiku
5.5's listed output price; input is $0.10/M, OpenRouter's public `/models`
listing). The tracked fixtures were never written (`git status` clean).
Writer and labels at Haiku's default reasoning; rewrite and verification at
`low` (the new route defaults). Every role at the policy's 16,384-token budget.

Dry runs first. The harness's caps are reservations (each call reserves its
full 16,384-token output budget at $0.50/M, never refunded): the dry runs
planned $11.57 (probability, 575 calls) and $10.10 (arxiv_v2, 503 calls), so
`--max-cost-usd` was set to $15 per copy to admit them. **The owner's $5 total
cap was enforced on billed spend**: the run driver
(`fixtures-local/t6fu/scripts/run_eval.py`) passes the harness a cancellation
hook that sums the OpenRouter-reported `cost` of every receipt this stage wrote
on both copies (backfills included) and stops before the next request once it
reaches $5. It was never reached. (The driver's per-run "billed" field sums
both copies, so with the two reports running concurrently it double-counts;
the table below is from each copy's receipts.)

| Run | Calls | Billed (OpenRouter `cost`, from the copies' receipts) |
|---|---|---|
| Source-block backfills (456 + 4,259 blocks; dry runs first) | 15 + 134 embedding requests | $0.0017 |
| Smoke, probability, 12 questions (interface check) | 90 admitted | $0.047 |
| Report, probability, 47 questions | 286 admitted (8 writer, 33 rewrite, 112 labels, 129 verification, 3 embedding; 16 labels and 8 rewrites reused from the smoke) | $0.288 |
| Report, arxiv_v2, 41 questions | 308 admitted (8 writer, 33 rewrite, 146 labels, 118 verification, 3 embedding) | $0.269 |
| Live tutor timing, probability (§5.7), twice | 10 query embeddings, 5 rewrites, 10 verifications (the repeat was all cache) | $0.013 |
| Effort probe (§5.8) | 12 | $0.011 |
| Rerun after the Codex review (§5.9): probability / arxiv_v2 | 281 / 255 requests (170 / 161 labels, 111 / 94 verifications; writer, rewrites and query vectors reused) | $0.286 / $0.263 |
| **Total** | | **$1.18** of the $5 cap (first cut $0.63) |

Charged (reservation accounting): $3.44 and $3.50. Zero truncations in every
run (the Haiku rerun truncated 28 of 36 writer and 6 of 68 rewrite calls at
1,500 and 1,200 tokens). One label answer failed JSON validation and was
retried (`AIInvalidOutput`). Label agreement between the two passes: 921 pairs
exact 0.810, κ 0.669 (probability); 1,019 pairs exact 0.827, κ 0.659
(arxiv_v2); the Haiku rerun had κ 0.73 and 0.66.

Reports (aggregate only): `fixtures-local/t6fu/out/{probability,arxiv_v2}/`,
the driver's output with the billed accounting in `fixtures-local/t6fu/logs/`.

### 5.3 Results

nDCG@10 (Recall@10 and MRR@10 in the reports):

| System | probability (47) | arxiv_v2 (41) |
|---|---|---|
| substring (today's library search, as merged before T6) | 0.000 | 0.000 |
| keyword | 0.636 | 0.496 |
| meaning (dense) | 0.792 | 0.821 |
| hybrid (`hybrid_rrf`, no rewrite) | 0.740 | 0.696 |
| hybrid_rewrite (today's library deep search) | 0.759 | 0.785 |
| **pool_rewrite** (`dense_plus_bm25` deep search) | **0.808** | **0.849** |
| hybrid_verify (today's tutor) | 0.821 | 0.777 |
| **pool_verify** (`dense_plus_bm25` tutor) | **0.884** | **0.897** |
| dense_verify | 0.875 | 0.888 |

| Paired difference, nDCG@10 [95% CI] | probability | arxiv_v2 |
|---|---|---|
| hybrid − meaning | −0.052 [−0.103, −0.007] | −0.125 [−0.169, −0.082] |
| hybrid_rewrite − hybrid | +0.019 [−0.014, +0.048] | **+0.089 [+0.043, +0.140]** |
| hybrid_rewrite − meaning | −0.033 [−0.088, +0.025] | −0.036 [−0.084, +0.011] |
| **pool_rewrite − hybrid_rewrite** (display) | **+0.049 [+0.003, +0.098]** | **+0.064 [+0.016, +0.111]** |
| pool_rewrite − meaning | +0.016 [−0.024, +0.052] | +0.028 [−0.003, +0.059] |
| hybrid_verify − hybrid (what verification adds) | **+0.081 [+0.057, +0.108]** | **+0.081 [+0.052, +0.110]** |
| **pool_verify − hybrid_verify** (tutor) | **+0.063 [+0.026, +0.104]** | **+0.120 [+0.070, +0.174]** |
| pool_verify − dense_verify (what BM25 widening adds) | +0.010 [−0.003, +0.028] | +0.009 [−0.003, +0.021] |
| dense_verify − hybrid_verify | +0.054 [+0.015, +0.099] | +0.111 [+0.061, +0.166] |

Bold: the bar (interval above 0, Recall@10 not worse, at least 10 questions).

**What the tutor would get** (the verification's picks; at most 4):

| Verify system | probability: relevant share of picks / unverified top-4 / nDCG@picks / picks per q | arxiv_v2: same |
|---|---|---|
| hybrid_verify | 0.963 / 0.777 / 0.900 / 3.43 (1 empty with a relevant span in the pool) | 0.948 / 0.799 / 0.922 / 3.73 |
| pool_verify | 0.957 / 0.798 / 0.891 / 3.47 | **0.987** / 0.896 / 0.938 / 3.83 |
| dense_verify | 0.955 / 0.798 / 0.881 / 3.34 | 0.975 / 0.896 / 0.929 / 3.83 |

Paired on the picks: pool_verify − hybrid_verify relevant share +0.013
[−0.014, +0.047] (probability), **+0.051 [+0.004, +0.104]** (arxiv_v2);
nDCG@picks −0.009 [−0.043, +0.025] and +0.016 [−0.024, +0.057]. pool_verify −
dense_verify: +0.004 [−0.034, +0.037] and +0.012 [−0.016, +0.041]. The
verification lifts the relevant share from 0.78–0.90 (the pool's own top 4) to
0.95–0.99, as in the Haiku rerun (0.70–0.73 to 0.93–0.95 on hybrid top 10).

**Verification latency** (wall time of the production step, Haiku 5.5 at
`low`, 12–16 candidates): p50 / p90 7.9 / 9.5 s (hybrid_verify), 7.6 / 9.9 s
(pool_verify), 7.4 / 9.4 s (dense_verify) on probability; 7.3 / 9.4, 7.8 /
9.9, 7.8 / 10.3 s on arxiv_v2. The rerun measured 6.4–6.7 s p50 on 10
candidates at the default effort and a 2,500-token cap. Low effort did not make
verification faster (§5.8): at `low` Haiku still reasons a median of 667
tokens per verification (output 1,360), about what the labeller reasons at the
default (703). The rewrite at `low` reasons a median of 0 tokens (2.2 s p50 in
the report, 290 output tokens).

### 5.4 By query type (nDCG@10)

| Type | n (prob / arxiv) | meaning | hybrid | hybrid_rewrite | pool_rewrite | hybrid_verify | pool_verify |
|---|---|---|---|---|---|---|---|
| conceptual | 10 / 10 | .808 / .706 | .698 / .535 | .725 / .732 | .841 / .760 | .767 / .634 | .889 / .845 |
| keyword (exact term) | 10 / 10 | .834 / .854 | .784 / .723 | .816 / .727 | .876 / .863 | .876 / .849 | .925 / .920 |
| compositional | 10 / 10 | .720 / .892 | .698 / .776 | .721 / .837 | .737 / .915 | .793 / .836 | .849 / .940 |
| procedural | 9 / 10 | .811 / .846 | .690 / .785 | .726 / .856 | .830 / .852 | .796 / .816 | .902 / .889 |
| logged (real learner) | 8 / 1 | .788 / .679 | .844 / .330 | .812 / .667 | .746 / .906 | .883 / .505 | .853 / .834 |

| Paired, nDCG@10 [95% CI] | pool_rewrite − hybrid_rewrite (display) | pool_verify − hybrid_verify (tutor) | hybrid − meaning |
|---|---|---|---|
| conceptual, prob / arxiv | +0.116 [+0.015, +0.229] / +0.028 [−0.054, +0.109] | +0.122 [−0.001, +0.272] / +0.211 [+0.062, +0.344] | −0.111 / −0.170 |
| keyword, prob / arxiv | +0.060 [−0.030, +0.180] / +0.137 [+0.055, +0.230] | +0.049 [−0.001, +0.119] / +0.071 [−0.013, +0.172] | −0.050 / −0.131 |
| compositional, prob / arxiv | +0.016 [−0.054, +0.105] / +0.078 [−0.033, +0.179] | +0.055 [+0.008, +0.100] / +0.105 [+0.026, +0.184] | −0.022 / −0.116 |
| procedural, prob / arxiv | +0.104 [+0.005, +0.199] / −0.004 [−0.079, +0.063] | +0.106 [+0.040, +0.173] / +0.073 [+0.011, +0.139] | −0.121 / −0.060 |
| logged, prob (8) | **−0.067 [−0.128, −0.018]** | −0.030 [−0.085, +0.013] | **+0.057 [+0.003, +0.125]** |

Relevant share of the tutor's picks on the 8 logged probability questions:
hybrid_verify 0.96, pool_verify 1.00, dense_verify 0.93.

Reading:

- **Exact-term searches do not need BM25 first.** The generated keyword
  queries (the learner types the term) were ranked better by dense alone than
  by the fusion on both copies (0.834 vs 0.784, 0.854 vs 0.723). BM25's widening
  of the verified pool adds +0.01 nDCG@10 (not significant) on both copies.
- **The rewrite helps on the large library only**, as the rerun found:
  +0.089 on arxiv_v2 (+0.196 on its conceptual questions), +0.019 (n.s.) on
  probability.
- **The real learner questions are the exception, again.** On probability's 8
  logged questions the fusion beats dense (+0.057, rerun +0.088 on 7), and the
  library's display ranking of the pool is worse than the fusion's (−0.067).
  On the verified tutor path the difference is not significant (−0.030) and
  the pool's picks were all relevant (1.00 vs 0.96). Eight questions from one
  vault are too few to set a default against 80 generated ones, but they are
  the only real ones (open question 1).

### 5.5 Compared with the first run and the Haiku rerun

nDCG@10; the first two runs asked 30 questions per copy (23 or 29 conceptual
generated questions, 7 or 1 logged), labels by gpt-4.1-mini (first run) and
Haiku 5.5 at the old caps (rerun). "This run, conceptual" uses the same prompt
and the first 10 of the same seeds.

| | meaning | hybrid | hybrid_rewrite | hybrid − meaning | rewrite − hybrid |
|---|---|---|---|---|---|
| probability, first run | 0.826 | 0.794 | 0.801 | −0.032 | +0.007 |
| probability, Haiku rerun | 0.795 | 0.742 | 0.781 | −0.053 | +0.039 |
| probability, this run, conceptual (10) | 0.808 | 0.698 | 0.725 | −0.111 | +0.027 |
| probability, this run, all (47) | 0.792 | 0.740 | 0.759 | −0.052 | +0.019 |
| probability, logged: rerun (7) / this run (8) | 0.736 / 0.788 | 0.825 / 0.844 | 0.800 / 0.812 | +0.088 / +0.057 | −0.025 / −0.032 |
| arxiv_v2, first run | 0.793 | 0.710 | 0.814 | −0.083 | +0.105 |
| arxiv_v2, Haiku rerun | 0.777 | 0.635 | 0.738 | −0.142 | +0.103 |
| arxiv_v2, this run, conceptual (10) | 0.706 | 0.535 | 0.732 | −0.170 | +0.196 |
| arxiv_v2, this run, all (41) | 0.821 | 0.696 | 0.785 | −0.125 | +0.089 |

The direction of every comparison the earlier runs made holds; the new
question types and the verification systems are what decide the pool.

### 5.6 The pool default: `dense_plus_bm25`

*(Codex review: the tutor-path numbers below came from pools that were not
the tutor's (review F5). §5.9 reruns them on the tutor's own pools; the
decision stands on those numbers.)*

`dense_plus_bm25` beat `hybrid_rrf` on both paths the switch controls, on both
copies, by the bar: the tutor's verified ranking (+0.063 and +0.120 nDCG@10;
relevant share of picks +0.013 n.s. and +0.051) and the library's display
ranking (+0.049 and +0.064), and it was at least as good in every generated
query type, keyword searches included. The one exception is probability's 8
real learner questions on the display path (−0.067; on the tutor path −0.030,
not significant). The default is `dense_plus_bm25`; `pool = "hybrid_rrf"`
restores T6 as merged. BM25 widening is kept as specified (m = 4): it costs
at most 4 more candidates per verification and added +0.01 (n.s.), but it is
the guard against exact terms dense misses, which these generated keyword
queries did not exercise much.

### 5.7 Live tutor timing on the probability copy

`fixtures-local/t6fu/scripts/tutor_timing.py` re-asked the copy's 5 logged
practice and feedback questions through `tutor_qa.ask_question` with the
production `TutorSpanProvider` (Haiku 5.5 verification, qwen3 query embedding,
`dense_plus_bm25`, a stub tutor answer): round A at the defaults, round B with
`tutor_query_rewrite = true`. `learnloop sources report` over those 10
receipts (cold: nothing cached):

| Step | n | p50 ms | p90 ms | max ms | over 15 s |
|---|---|---|---|---|---|
| rewrite (round B only) | 5 | 4,607 | 5,904 | 5,904 | 0 |
| query_embedding | 10 | 4,478 | 6,658 | 6,824 | 0 |
| retrieval | 10 | 18 | 77 | 86 | 0 |
| verification | 10 | 8,785 | 10,119 | 12,134 | 0 |
| total | 10 | 15,020 | 19,374 | 19,475 | **5** |

No step exceeded the 15 s soft deadline; the total did on 5 of 10 questions
(all were answered from verified spans; nothing was cancelled). The query
embedding (OpenRouter qwen3-embedding-8b, one short text) took 0.5 to 6.8 s, a
large share of the total. *(The first cut of this report counted the rewrite
as 0 ms on round A, where it did not run; a step that does not run is now left
out of the receipt. The rewrite row above is round B's.)* Re-asking the same
10 questions is all cache (query vectors, checkpointed rewrites,
ledger-served verification): total p50 224 ms.

### 5.8 Does `low` effort help? (a minimal interface check)

The same three stored verification prompts, sent through the app's OpenRouter
client at the profile default (no `reasoning` parameter) and at efforts
`low`, `minimal` and `none` (`scripts/effort_probe.py`, 12 calls, $0.011):

| Effort | reasoning tokens (3 prompts) | output tokens | seconds |
|---|---|---|---|
| default | 599, 782, 646 | 1,225–1,465 | 6.2, 7.1, 5.7 |
| low | 478, 428, 566 | 1,104–1,220 | 7.3, 5.4, 7.4 |
| minimal | 524, 525, 593 | 1,169–1,212 | 5.4, 7.0, 6.0 |
| none | 0, 0, 0 | 665–716 | **3.6, 4.2, 3.7** |

OpenRouter honours the parameter: `low` trims Haiku 5.5's reasoning by about a
quarter but not its latency, and `none` turns reasoning off and halves the
verification's time. The default stays `low` as the owner decided;
`ai.route_reasoning_effort.source_rerank = "none"` is one line if the owner
wants the speed (its quality is not measured here: open question 2).

### 5.9 Rerun on the tutor's own pools (after the Codex review)

The verification systems now judge the pool `tutor_pool` builds for each
question's context (`docs/reviews/t6-followup-codex-review.md`, F5): on
probability 5 logged questions were asked with their item (3 practice, 2
feedback) and 42 as library questions (39 generated, 3 logged library or
reader questions) about the LOs the reader links to their passages; on
arxiv_v2 all 41 as library questions. Same copies, questions, seeds, models
and efforts as §5.2. The candidate sets changed, so every question was
labelled again (two passes, fresh answers): the display numbers move too.
Every verification ran (coverage 47/47 and 41/41 per system, no blocked
verdict); zero truncations; label agreement 1,150 pairs exact 0.808, κ 0.659
(probability), 1,180 pairs exact 0.839, κ 0.692 (arxiv_v2). Dry runs first
(planned 669 / 585 calls, 2,154 / 1,885 candidates, 2,068 / 1,804 pairs,
$14.05 / $12.26 of reservations at $0.50/M; charged 281 / 255 calls, 1,519 /
1,348 candidates and pairs, $3.59 / $3.06). Reports:
`fixtures-local/t6fu/out/probability/source_retrieval-88d1a5df76740884.*`,
`fixtures-local/t6fu/out/arxiv_v2/source_retrieval-76b6ce3ade149e70.*`.

| System, nDCG@10 | probability (47) | arxiv_v2 (41) |
|---|---|---|
| keyword | 0.632 | 0.465 |
| meaning (dense) | 0.791 | 0.806 |
| hybrid | 0.732 | 0.684 |
| hybrid_rewrite (today's library deep search) | 0.754 | 0.760 |
| pool_rewrite (`dense_plus_bm25` deep search) | 0.797 | 0.832 |
| hybrid_verify (T6's tutor, its own pool) | 0.768 | 0.769 |
| **pool_verify** (`dense_plus_bm25` tutor, its own pool) | **0.861** | **0.854** |
| dense_verify | 0.840 | 0.860 |

| Paired difference, nDCG@10 [95% CI] | probability | arxiv_v2 |
|---|---|---|
| hybrid − meaning | −0.059 [−0.105, −0.015] | −0.122 [−0.164, −0.085] |
| hybrid_rewrite − hybrid | +0.022 [−0.012, +0.050] | **+0.077 [+0.034, +0.123]** |
| pool_rewrite − hybrid_rewrite (display) | +0.043 [−0.003, +0.093] | **+0.071 [+0.028, +0.119]** |
| hybrid_verify − hybrid | +0.036 [−0.006, +0.082] | **+0.085 [+0.059, +0.114]** |
| **pool_verify − hybrid_verify** (tutor) | **+0.093 [+0.054, +0.135]** | **+0.085 [+0.041, +0.131]** |
| pool_verify − dense_verify (what BM25 and linked-span widening add) | **+0.021 [+0.002, +0.042]** | −0.006 [−0.020, +0.007] |
| dense_verify − hybrid_verify | **+0.072 [+0.028, +0.120]** | **+0.091 [+0.048, +0.137]** |

| Verify system | probability: relevant share of picks / unverified top-4 / nDCG@picks / picks per q / empty with a relevant span in the pool | arxiv_v2: same |
|---|---|---|
| hybrid_verify | 0.962 / 0.707 / 0.879 / 3.32 / 1 | 0.940 / 0.805 / 0.903 / 3.68 / 2 |
| pool_verify | 0.957 / 0.798 / 0.891 / 3.47 / 0 | 0.963 / 0.921 / 0.922 / 3.95 / 0 |
| dense_verify | 0.955 / 0.798 / 0.867 / 3.28 / 2 | 0.974 / 0.921 / 0.911 / 3.80 / 1 |

Paired on the picks, pool_verify − hybrid_verify: relevant share +0.022
[−0.020, +0.071] and +0.017 [−0.011, +0.051]; nDCG@picks +0.013 [−0.036,
+0.064] and +0.019 [−0.050, +0.103] (none significant). Verification latency
p50 / p90: 7.9 / 9.9 s (hybrid_verify), 7.9 / 10.4 (pool_verify), 6.5 / 9.2
(dense_verify) on probability; 7.2 / 9.7, 8.1 / 9.9, 7.6 / 9.4 on arxiv_v2.

pool_verify − hybrid_verify by query type (probability / arxiv_v2):
conceptual +0.124 [+0.026, +0.232] / +0.163 [+0.062, +0.296]; keyword +0.088
[+0.018, +0.164] / +0.044 [−0.026, +0.122]; compositional +0.093 [+0.005,
+0.173] / +0.038 [−0.024, +0.097]; procedural +0.140 [+0.071, +0.225] / +0.073
[+0.021, +0.132]; probability's 8 logged questions +0.007 [−0.064, +0.062],
with relevant shares of picks 0.95 (hybrid_verify), 0.84 (pool_verify) and
0.87 (dense_verify). On the display path the logged questions stay the
exception: pool_rewrite − hybrid_rewrite −0.059 [−0.108, −0.012].

Reading:

- **The tutor-path win holds on the tutor's own pools**, on both copies, by
  the bar: +0.093 and +0.085 nDCG@10 (first cut +0.063 and +0.120). The picks
  themselves are as relevant as `hybrid_rrf`'s (differences not significant),
  and the pool never left a relevant span unpicked (0 against 1 and 2).
- **Widening now earns its place on probability** (+0.021 over dense alone):
  the tutor's linked spans are a widening list the first cut did not have.
- **The display half is weaker than the first cut said.** Under fresh labels
  `dense_plus_bm25` beats the fusion on arxiv_v2 (+0.071) and is ahead but not
  significant on probability (+0.043, first cut +0.049 just above the bar).
- **The 8 real probability questions**, 5 now asked with their item in
  context: no significant tutor-path difference, but the pool's picks were
  relevant less often (0.84 against 0.95). Eight questions decide nothing; it
  adds to open question 1.

The default stays `dense_plus_bm25` for both paths: it beats `hybrid_rrf` by
the bar on the tutor path on both copies and on the display path on one, and
is ahead on the other.

## 6. Algorithm successor: none

Output budgets, reasoning effort, the retrieval pool and the tutor's timing
receipts are context and transport settings. Under every algorithm version
they change which source spans the tutor's verifier and the library list see
and how much a model may write; they change no scoring, scheduling,
projection, evidence, certification or choice of the item served, and nothing
persisted changes meaning (replay makes no model call). T6's rule applies
("retrieval is context, so no successor is needed unless something persisted
changes meaning"), so no successor and no migration (main stays at 179).
*(Codex review F7 asked for a successor; rejected with this reason and the
owner's live-behind-kill-switches decision, see
`docs/reviews/t6-followup-codex-review.md`. The first cut said "no serving
change", which read as no change to what the tutor is grounded in.)* The pool's kill switch is `source_retrieval.pool
= "hybrid_rrf"` (T6 as merged); `tutor_deadline_cancels = true` restores the
time box; `ai.output_tokens` / `ai.route_output_tokens` and
`ai.route_reasoning_effort` restore any budget or effort. The config keys
changed, so all five defaults snapshots were recomputed with
`defaults_fingerprint_for_version` (`config/template.py`, with the decision
recorded beside them): `mvp-0.9` `95c181f4…`, `mvp-0.10` `c83d3c5f…`,
`mvp-0.11` `19542648…`, `mvp-0.12` `c235f26e…`, `mvp-0.13` `8ae6b37a…`. The
parameter registry's `ai.` and `source_retrieval.` prefix rules cover the new
keys. The DB and configuration references were regenerated (663 configuration
leaves, the two prose counts updated; the 313 notes whose only change was the
`source_commit` stamp were left as they were, keeping the 28 notes whose
content moved); the validator reports `errors: []`.

## 7. Tests

Written before the code they test, and run against the base commit
(`git archive 68213d96`, with the new test helpers copied in): the two new
files fail to import there (`learnloop.ai.output_budget` and the new
evaluation names do not exist), and the changed behavioural tests fail on the
old behaviour (`output_budget_tokens` 1024 for the family and contamination
judges, a time-boxed tutor query embedding, no `timings_ms`).

- `tests/test_output_budget.py` (18 tests): the default, profile and route
  budgets; unknown routes and budgets under 256 refused; T6's low-effort
  defaults and the owner-table merge; no retired constant left in the 12
  modules that had one; the review allowances and project budgets; the
  same-cause judge no longer held to 600; OpenRouter receives
  `reasoning.effort` and the budget as `max_tokens`, the route effort beating a
  profile that disables thinking; the transport's truncation retry at double
  for an admitting caller, a second truncation failing, a profile maximum never
  exceeded, an owner-set budget never exceeded (logged, failed), and no
  transport retry inside `single_request`; `PaidCalls` and `PFCaller` retrying
  once at double, admitted and charged as a retry, with the `truncated`
  receipt, the `truncation_retry` note on the retry's receipt and the event
  (role, model) in the report; a second truncation failing; Codex taking a
  route's effort for one turn; `ReviewSpend` admitting the transport's retry.
- `tests/test_source_retrieval_followup.py` (14 tests): the `dense_plus_bm25`
  order, dedup and roles; `search_spans` dense first then BM25 extras; the
  fallback without a complete index; the library's pool; the tutor verifying
  dense plus BM25 and linked-span extras, and `hybrid_rrf` keeping today's
  pool; every step timed and a slow step flagged, never cancelled, a step that
  did not run left out; the live rewrite and verification at low effort and an
  owner override; `sources report` p50/p90, the soft-deadline count and
  truncated answers, JSON and text; the even type split; every logged question
  included; the verification metrics; the report running the production
  verification by query type, resumable at no cost; the label pool bound.
- Updated for the owner's decisions (the old expectation encoded the retired
  behaviour): the tutor time-box tests now set `tutor_deadline_cancels = true`
  (and a new test checks the default has no time box); the provider-failure and
  question-row manifests carry `timings_ms`; the RRF-fusion library test pins
  `pool = "hybrid_rrf"`; the suite tests inject the `source_verify` role and
  expect the new systems and query types; the family, contamination, field
  classification and practice-index tests expect the policy budget; the
  ingestion test keeps its one request (an owner-set budget is never doubled);
  `sources search` caps 0.25. `tests/openai_fakes.py` can queue a length stop
  (`FakeTruncated`); `FakeSourceLLM` answers compositional pairs and records
  each request's effort. CLI help snapshot regenerated (`sources report`, the
  `--output-tokens` help, the deep-search caps).

## 8. Gate

Final tree (`uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`,
`TMPDIR` = the worktree's `fixtures-local/tmp`):

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8381 passed**, 0 failed, 0 skipped (297 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **91 passed**, 8290 deselected (95 s) |
| Frontend | not changed (no `apps/` file touched), so not run |
| `db_generate_reference.py`, `db_validate_reference.py` | no schema change; regenerated for the configuration keys: `errors: []` (298 table notes, 663 configuration leaves, 3911 wikilinks) |

*(After the Codex review fixes: 8395 passed, durability 91 passed, imports
12 kept; see `docs/reviews/t6-followup-codex-review.md`.)*

A preliminary full run before the defaults snapshots were recomputed failed
12 tests: the 10 snapshot pins, the field-classification budget (512) and the
ingestion test that showed the transport must not double an owner-set budget
(now opt-in, §1). All are fixed above. The tracked fixture vaults
(`fixtures/probability`, `fixtures/arxiv_v2`, `fixtures/linear_algebra`) were
only read through the backup API; `git status fixtures/` is clean.

## 9. Files

**Added:** `src/learnloop/ai/output_budget.py`,
`src/learnloop/source_retrieval/timing.py`, `tests/test_output_budget.py`,
`tests/test_source_retrieval_followup.py`, this file.

**Changed:** AI layer (`ai/execution.py` effort, annotation and
truncation-retry contexts; `ai/transport.py` `StructuredRequest.reasoning_effort`;
`ai/providers/openai_chat.py`, `openrouter.py`, `codex.py`); config
(`config/schema.py`: `ai.output_tokens`, `route_output_tokens`,
`route_reasoning_effort`, `source_retrieval.pool`, `pool_keyword_extras`,
`tutor_deadline_cancels`, three caps; `config/template.py` snapshots); the
budgeted callers (`practice_index/paid.py`, `listwise.py`, `retrieval.py`,
`dossiers.py`, `evaluation.py`; `ops/pf_calls.py`, `pf_generation.py`,
`pf_reports.py`, `embedding_compare.py`, `family_proposals.py`,
`contamination/judge.py`; `projects/ai_runtime.py`, `probes.py`;
`diagnosis/offline_review/spend.py`, `runner.py`;
`diagnosis/recurrence/backlog.py`, `guard.py`, `live.py`;
`diagnosis/split/jobs.py`, `pfc_report.py`; `field/probability_prep.py`;
CLI `app.py`, `diagnose.py`, `evaluation.py`, `field.py`,
`field_classification.py`, `probability_arms.py`, `success_head.py`,
`sources.py`); source retrieval (`search.py`, `tutor.py`, `queries.py`,
`verify.py`, `library.py`, `bench.py`, `evaluation.py`, `b4.py`);
`tutor/tutor_qa.py` (the provider's wall time on the receipt only); the tests
listed in §7, `tests/cli_help_snapshot.json`; the regenerated configuration
reference notes and the two prose counts.

**Not changed:** `diagnosis/recurrence/benchmarks.py` (owner-batch-2),
`ai/spend.py`, `tutor_qa`'s `TutorAnswer`, the scheduler and Today, the
frontend, the sidecar's RPC set (no new RPC, so nothing to pin in
`tests/test_mobile_allowlist.py`), migrations.

**Runs (gitignored):** `fixtures-local/t6fu/` (copies, scripts
`setup_copies.py`, `run_eval.py`, `tables.py`, `tutor_timing.py`,
`effort_probe.py`, logs and aggregate reports).

## 10. Open questions for the owner

1. **Real learner questions favour the fusion's display ranking.** On
   probability's 8 logged questions `hybrid_rrf` ranks the library better
   (−0.067 for the pool, and +0.057 for hybrid over dense, as the rerun's +0.088
   on 7; after the Codex review, under fresh labels, −0.059 and +0.019). The
   tutor path shows no significant difference there (+0.007 on the tutor's own
   pools, 5 of the 8 asked with their item), but the pool's picks were relevant
   less often (0.84 against 0.95). The display half is also only significant on
   arxiv_v2 in the rerun (§5.9). The default follows the 80 generated
   questions; a larger set of real questions (or owner labels on these 8) could
   overturn the display half. Keep `dense_plus_bm25` for both, or split the
   switch (pool for the tutor, fusion for the library display)?
2. **Verification latency.** At `low`, Haiku 5.5 still reasons ~670 tokens
   and verification takes 7–8 s p50 (12–16 candidates); `none` halves it
   (3.6–4.2 s) by turning reasoning off. The quality at `none` is not measured.
   Try `ai.route_reasoning_effort.source_rerank = "none"` with a bench run, or
   a smaller candidate pool (12 → 8)?
3. **The query embedding is slow.** OpenRouter's qwen3-embedding-8b took 0.5
   to 6.8 s (p50 4.5 s) for one short question, a third of a cold tutor
   question's 15 s. A local or faster embedding provider for queries only, or a
   timeout and dense-less fallback for that step?
4. **Reservations at 16k.** Every metered call now reserves its full 16,384
   output tokens (at an owner price that applies to every token), so dry-run
   plans and harness caps are about 3× larger than before for the same work
   (this report: $10–12 planned, $0.27–0.29 billed per copy). Fine as is, or a
   per-route budget for the high-volume bench labeller?
5. **`hybrid_rrf` code path.** With `dense_plus_bm25` the default and its own
   fallback to `hybrid_rrf` for incomplete indexes, the fusion stays needed;
   nothing to retire.
