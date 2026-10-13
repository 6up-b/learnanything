# Slice 2 T6 follow-up: Codex review fixes

Branch `slice-2/t6-followup`, worktree `learnanything-t6-followup`. The review
(codex-job `20261013-001918-Os5xsn`, read-only, targeted in-memory
reproductions, no full suite) covered the stage commit `debd86c0` (stage
review: `docs/reviews/t6-followup.md`). This file records the fix step: each
finding was reproduced first with a failing test, then fixed or rejected with
a reason, the T6 report was rerun on the fixtures-local copies, and the gate
was rerun.

## Review

### How the findings were reproduced

- **Fail-first tests**, `tests/test_t6_followup_review.py`, committed alone in
  `68ecc1de` against the unfixed code: **12 failed, 2 passed** (the 2 passing
  are the "admitted" halves of F1's two boundary pairs, which held before the
  fix too). Each failure was the finding's scenario:
  - F1: with `max_total_tokens` 49,551 (200 input + 16,384, then 200 + 32,768
    for the doubled retry), `ReviewSpend` and the project calls sent the
    doubled retry anyway (wire limits `[16384, 32768]`, no refusal).
  - F2: three metered calls and one subscription call charged, `max_calls`
    5: a failing verification and its retry reached the provider twice (six
    shared calls); and a verification already in the ledger was refused
    (`calls exceeds max_calls`) by the pre-check made before the cache.
  - F3: the dry run's plan had no `candidates` key; with `max_candidates`
    below the run's charges the dry run passed.
  - F4: with every verification failing, the report had no coverage (the test
    stopped there; the code ranked a verification that did not run as its
    unverified pool, so the systems were scored and could win verdicts, as the
    review's ten-question repro showed).
  - F5: the report verified a logged practice question without its practice
    question and over a pool unlike the tutor's.
  - F6: a profile at `max_tokens = 8192` truncated, and `PaidCalls` and the
    compare harness re-sent 8,192 (`[8192, 8192]`) after announcing 16,384;
    with a 12,000 ceiling the retry recorded 16,000; a route override of
    32,000 resolved to 32,000 for DeepSeek Flash (8,192).
- **F7** is reproduced by reading the code and the stage review: the five
  defaults snapshots were recomputed, `source_retrieval.pool` changes the
  default ranking under every algorithm version, and §6 said "no serving
  change".

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Doubled transport retries exceed their spend reservations | fixed | `08b03158` | `test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance[49552-True/49551-False]`, `test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance[0-True/-1-False]` |
| F2 | Medium | Verification bypasses the harness's shared retry admission | fixed | `9a1d29eb` | `test_every_verification_attempt_is_admitted_under_the_shared_caps`, `test_a_cached_verification_is_served_even_when_the_caps_are_spent` |
| F3 | Medium | Dry-run omits the new verification candidate charges | fixed | `51981532` | `test_insufficient_candidate_caps_fail_at_the_dry_run` (refused at `candidates - 1`, complete at exactly the planned candidates and pairs); `test_the_label_pool_bound_counts_what_each_verification_pool_can_add` updated |
| F4 | Medium | A failed verifier can receive a winning benchmark verdict | fixed | `51981532` | `test_a_failed_verification_is_never_scored_and_blocks_its_verdicts` |
| F5 | Medium | The tutor-default benchmark uses a different candidate population | fixed | `51981532` | `test_the_report_verifies_the_tutors_own_pool_with_its_item_in_context` (the logged practice question's verification gets the tutor's exact candidates, in order, and its practice question; no assessment passage is ever verified) |
| F6 | Medium | "Doubled" caller retries can resend the same profile limit | fixed | `98ebeafc` | `test_a_route_override_cannot_exceed_the_profile_maximum`, `test_a_truncation_retry_stops_at_the_transport_ceiling`, `test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request`, `test_paid_calls_reserve_and_record_the_real_increased_limit`, `test_the_compare_harness_never_resends_a_profile_maximum` |
| F7 | Medium (High-equivalent per the review) | Serving defaults change under existing algorithm versions | rejected (wording corrected) | `83bd5494` | Conflicts with the spec and the owner's decisions; see below |

### Claims that did not hold

| Claim (stage review) | Now |
|---|---|
| The budget is both the request limit and the reservation (F1) | True for every physical request: a truncation retry is reserved at the allowance it is sent with (§1 corrected). |
| A reached profile maximum fails without another retry (F6) | True for caller-owned retries too (`TruncationRetry(ceiling=...)`); the route-override precedence now matches the transport's clamp (§1 corrected). |
| Verification runs under the harness's command caps (F2, F3) | Every attempt passes the shared caps after the cache, and the dry run plans every candidate and pair. |
| The report establishes what today's tutor would receive (F4, F5) | The report now verifies the tutor's own pools and never scores a verification that did not run; rerun in the stage review §5.9. |
| There is no serving change (F7) | Reworded: the defaults change the tutor's grounding context, the library ranking and output budgets under every version; nothing persisted changes meaning. |

### What changed, finding by finding

**F1 (High).** `ReviewSpend.request` and the project `PaidCalls.call` admitted
each further physical request at the first request's estimate. The transport's
own truncation retry sends twice the budget, so a 32,768-token request was
admitted under a 16,384-token reservation. Each further physical request is
now reserved from the output allowance its start event carries
(`output_budget_tokens`, never less than the admitted limit) plus the input
bound, before it is sent; a refusal propagates and nothing is sent. An
unreported charge reconciles to its own reservation, not the first one's.
(`diagnosis/offline_review/spend.py`, `projects/ai_runtime.py`.)

**F2.** The report checked the shared call count once before the verification,
then the production verification charged only its own billing class's budget.
`practice_index.paid.PaidCalls` now takes an `admit` hook applied to every
attempt (its candidates, pairs and retries included) before its budget charges
it, and its retry decisions ask the hook too; `judge_listwise` and
`verify_spans` pass it through, and the report passes the harness's
`check_shared`. Admission happens inside the attempt loop, after the ledger
cache and the checkpoints were found not to answer the request, so a cached
verification is served even when the caps are spent. Production callers pass
no hook (unchanged).

**F3.** Every role in the report's plan now carries what it charges: the
question writer one candidate per seed (`bench.plan_question_calls`, so B4's
writer too), the rewrite one candidate per call, the verification one
candidate and one pair per pool member at the tutor pool's bound
(`verify_pool_bound`: `tutor_candidate_pool` k, or k + 2m for
`dense_plus_bm25`, whose two widening lists, BM25 and the linked spans, add at
most `pool_keyword_extras` m each). `run_compare` aggregates candidates and
pairs per billing class (replacing the B2-only `freshness` pairs) into the
dry run's shared check. The verification's token sample uses the bound and a
practice question. The label bound counts the tutor pools without assuming
overlap with the library's lists (teaching and library scopes differ): with
the defaults 60 + 20 + 12 = 92 candidates per question (was 74).

**F4.** A verification that did not run (failed, unavailable, empty pool) was
ranked as its unverified pool and could win a verdict. It is now no ranking:
production would fall back to the LO-linked spans, which the report does not
score, so the question leaves that system's means, seed hits and paired
comparisons. `verification.coverage` reports verified / asked per system, and
every verdict involving a system with a verification that did not run is
blocked (`verdict_blocks`, verdict `False`; "blocked" in the Markdown).

**F5.** The tutor's pool construction is one function,
`source_retrieval.tutor.tutor_pool` (the teaching scope of the question's LOs
with assessment spans excluded, the LOs' linked spans as the `provenance`
list, the learner's question alone as the query, answer overlap withheld, and
in a practice or feedback context the item's own passages, exercise and
solution blocks excluded and its practice question shown to the verifier).
`TutorSpanProvider` calls it (behaviour unchanged: the tutor tests pass as
they were), and the report calls it per question and per verification system
(pool mode and extras), on query vectors and rewrites it already paid for:

- a logged practice or feedback question keeps its item (its LO, exclusions,
  withholding, practice question); a logged library question its note's
  related LOs;
- a generated question, and a reader question (which the tutor's retrieval
  never serves: the reader answers from its anchored span), is asked as a
  library question about the LOs the reader links to its passages
  (`learning_objects_for_span`); the report counts the contexts
  (`verification.tutor_contexts`).

Query vectors are served at half precision, as production stores them
(`practice_index.query_vectors`), so the dense lists are the ones production
ranks (with unit-length vectors, as real embedding models return, the bench's
and the tutor's candidates are identical; tested).

**F6.** `TruncationRetry` takes the transport's ceiling (`output_ceiling`:
the client profile's `max_tokens`; none for Codex). A call already at it fails
at once (logged `next: fail`, `reason: at_transport_ceiling`); otherwise the
retry sends, reserves and records `min(2 x budget, ceiling)`. `PaidCalls`,
`PFCaller`, the family and contamination judges and the LLM probability arm
pass it. A receipt recovered after such a retry matches any budget from the
request's to double it. The documented precedence now matches the transport:
`output_budget` and `admitted_output_limit` hold a route override to the
profile's `max_tokens`, and the schema comment, the module docstring and the
stage review say so.

**F7 (rejected).** The review asked for an immediate successor with
version-appropriate defaults, upgrade and shadow-rebuild checks, preserving the
predecessors' behaviour and fingerprints. Rejected:

1. *The spec.* T6's handoff (`docs/specs/implementation_handoffs.md`, Slice 2
   T6): "Retrieval is context, so no successor is needed unless something
   persisted changes meaning." The playbook's trigger is persisted meaning
   ("scoring, scheduling, projection, or admissibility semantics"). The pool,
   the low effort, the output budgets and the timing receipts change which
   source spans the verifier and the library list see and how much a model may
   write. No ledger row is reinterpreted, verdicts are new rows under
   request-derived ids that include the budget and effort, replay and rebuild
   make no model or embedding call, and no scoring, scheduling, projection,
   evidence, certification or item choice reads them.
2. *The owner's decisions.* "Live changes behind kill switches, no shadow
   stages by default", and the request this stage implements: the caps were
   "cutting the model off prematurely". A successor would hold the larger
   budgets and the pool behind `learnloop upgrade` and a shadow rebuild, so the
   owner's existing vaults would keep truncating.
3. *Precedent and the fingerprint rule.* T6 as merged changed the tutor's
   grounding under every version on the same rule (two Codex reviews), and the
   T1, T6 and stuck-prompt merges each recomputed every snapshot for keys that
   change no persisted meaning. That recomputation, recorded beside the
   snapshots, is the version/fingerprint decision playbook step 4 asks for.
4. *Kill switches* restore T6 as merged: `source_retrieval.pool =
   "hybrid_rrf"`, `tutor_deadline_cancels = true`, `ai.output_tokens` /
   `ai.route_output_tokens`, `ai.route_reasoning_effort`.

The finding is right that "no serving change" read as no change to what the
tutor is grounded in. The template note (`config/template.py`) and the stage
review §6 now say what changes under every version and why that takes no
successor. The fingerprints are unchanged (all five recompute to the recorded
values). The owner may still ask for a successor at the checkpoint.

### Spec conformance after the fixes

| Requirement | Now |
|---|---|
| R4: shortlist, then judge consequential grounding | The report's tutor path is the production path (`tutor_pool` then `verify_spans`); a verification that did not run is not scored. |
| R6: report-based live decisions | The pool default is decided on the rerun of the tutor's own pools (stage review §5.9). |
| T6 consequential reranking and two-stage grounding | The benchmark reproduces the serving path, including the item context and the fallback (counted, blocked). |
| Spend controls and dry run | F1, F2, F3 and F6 fixed: every physical request reserved at its allowance, every attempt under the shared caps, every candidate and pair planned. |
| Successor and kill switches | Kill switches unchanged; successor rejected (F7). |
| Ledger, replay, schema, durability | No new table, migration, replayer or RPC; nothing to pin in `tests/test_mobile_allowlist.py`. |

### Real calls

The T6 report rerun on the stage's backup-API copies
(`fixtures-local/t6fu/probability`, `fixtures-local/t6fu/arxiv_v2`, made with
`learnloop.db.copies`; the tracked vaults were never touched), through the
stage's driver (`fixtures-local/t6fu/scripts/run_eval.py`: harness caps as
reservations, `--max-cost-usd` 15, and the owner's $5 stage cap enforced on
OpenRouter-billed cost before every request). Claude Haiku 5.5 on OpenRouter
for every LLM role, Haiku 5.5's listed $0.50/M as the owner price.

| Step | probability (47 questions) | arxiv_v2 (41 questions) |
|---|---|---|
| Dry run (no request) | 669 calls, 2,154 candidates, 2,068 pairs, $14.05 of reservations planned: admitted | 585 calls, 1,885 candidates, 1,804 pairs, $12.26: admitted |
| Run: requests | 281 (170 label calls, one answer that failed JSON validation retried; 111 verifications) | 255 (161 label calls, five retried; 94 verifications) |
| Reused, no request | 8 writer, 41 rewrites, 7 label and 30 verification answers (ledger and checkpoints), every query vector | 8 writer, 33 rewrites, 4 label and 29 verification answers, every query vector |
| Charged (reservation accounting) | 281 calls, 1,519 candidates and pairs, $3.59 | 255 calls, 1,348 candidates and pairs, $3.06 |
| Billed (OpenRouter `cost` on the copy's receipts) | **$0.286** | **$0.263** |

Every verification ran (coverage 100%, no blocked verdict), zero truncations.
The stage's billed total is now **$1.18 of the $5 cap** (first cut $0.63).
Everything run charged less than its dry run planned, candidates and pairs
included. Results: stage review §5.9. Driver output:
`fixtures-local/t6fu/logs/review-run-{probability,arxiv_v2}.json` (its
"this run billed" field sums both copies, which ran concurrently); reports
`fixtures-local/t6fu/out/probability/source_retrieval-88d1a5df76740884.{json,md}`
and `fixtures-local/t6fu/out/arxiv_v2/source_retrieval-76b6ce3ade149e70.{json,md}`.

In short: on the tutor's own pools `dense_plus_bm25` still beats `hybrid_rrf`
on the tutor path on both copies by the bar (+0.093 and +0.085 nDCG@10; first
cut +0.063 and +0.120), its picks are as relevant (differences not
significant), and widening by BM25 and the linked spans now adds +0.021 on
probability. The display half is weaker than the first cut said: +0.071 on
arxiv_v2 by the bar, +0.043 (not significant) on probability. The default
stays `dense_plus_bm25`.

### Gate

Code at `83bd5494` (the commits after it change only this file and the stage
review). `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`,
`TMPDIR` = the worktree's `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8395 passed**, 0 failed, 0 skipped (261 s; the stage's 8381 plus the 14 review tests) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **91 passed**, 8304 deselected (84 s) |
| Frontend | not changed (no `apps/` file touched), so not run |
| DB reference scripts | no schema or configuration key changed, so not rerun |

A targeted run over the 76 test files of the touched areas (source retrieval,
tutor, practice index, compare harness, recurrence benchmarks, review spend,
projects, PF, family and contamination judges, probability arms) before the
gate: 1129 passed. `git status fixtures/` is clean: the tracked vaults were
never written.

### Owner questions

1. **F7: no successor.** The pool, the low effort and the output budgets apply
   to existing vaults at their current versions, behind kill switches, per
   T6's rule and the owner's live-changes decision. Confirm, or ask for a
   successor that gates them behind `learnloop upgrade`.
2. **Report caps are now honest, and larger than the CLI defaults.** With every
   candidate and pair planned, a default `learnloop embeddings compare --suite
   source_retrieval` (`--max-candidates 100`, `--max-pairs 2000`) refuses at
   the dry run: 47 questions plan 2,154 candidates and 2,068 pairs (three
   verification pools of 12 to 20 candidates per question). Pass
   `--max-candidates 2500 --max-pairs 2500`, or raise the defaults for this
   suite?
3. **Generated questions are asked as library questions** about the LOs the
   reader links to their passages (no item, so no withholding or practice
   question). It is the closest production path for a question with no item;
   asking them as practice questions of an item on that LO would test the
   withholding too, at the cost of choosing an item per passage. Keep?
4. Stage open question 1 is updated with the rerun: on probability's 8 real
   questions the pool's picks were relevant less often (0.84 against 0.95),
   and the display half is significant only on arxiv_v2.

## Re-review

The Codex re-review (codex-job `20261013-012804-9EfuG6`, read-only, targeted
in-memory reproductions, no full suite) covered the fix step above (code at
`83bd5494`, this file at `5fcb0f7a`). Verdict: REOPENED. F1 was confirmed
fixed; F7 was reopened; one new finding, F8. F2 to F6 were not raised again.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Doubled transport retries exceed their spend reservations | fixed (confirmed by the re-review) | `08b03158` | as above; the re-review found both callers refuse one token below the reservation and admit at the boundary |
| F7 | Medium (High-equivalent per the review) | Serving defaults change under existing algorithm versions | rejected again | none (this file) | Conflicts with the owner's request and decisions and with the spec; the re-review names no persisted meaning that changes. See below |
| F8 | Medium | Tutor-scoped dense baselines can silently become hybrid | fixed | `1985c6d9` (fail-first tests `bf261d7a`) | `test_a_dense_baseline_whose_teaching_pool_falls_back_is_neither_verified_nor_scored`, `test_an_incomplete_library_index_does_not_starve_a_complete_teaching_index`, `test_dense_verify_is_unavailable_only_when_no_teaching_scope_can_be_dense` (`tests/test_t6_followup_rereview.py`) |

### F8: how it was reproduced

`tests/test_t6_followup_rereview.py`, committed alone in `bf261d7a` against
the unfixed code: **2 failed** (the third test was added with the fix and
covers the case where no teaching scope can be dense). Both scenarios use the
retrieval test vault with every current source embedded.

- **Library complete, teaching index partial.** The book's earlier revision
  (`ext_book_old`, other wording, so no stored vector covers it) is cited by
  every LO, and a logged practice question is added. The library's index is
  `ready`. One `dense_verify` pool of 8 fell back to `hybrid_rrf`, yet the
  report counted 8 of 8 `dense_verify` verifications, scored it as the dense
  baseline and blocked no verdict (the test failed on the missing
  `unavailable` coverage count).
- **Library partial, teaching indexes complete.** A reader-enabled source in
  no source set, cited by nothing, is added after the backfill. The library's
  index is `partial`, so the report paid for no query vector: `dense_verify`
  was reported unavailable (with the library's reason) and `pool_verify` fell
  back to `hybrid_rrf` on 8 of 8 questions, although the tutor would have
  built dense pools for every one of them.

### F8: what changed

- `source_retrieval.tutor.tutor_scope` is the tutor's scope construction (the
  teaching scope of the question's LOs, with the item's exclusions in a
  practice or feedback context). `tutor_pool` calls it, unchanged in behaviour.
- The report reads each question's teaching-scope coverage
  (`dense_coverage`, no vector bytes) before paying for query vectors. A
  question's vector is paid for when the library's index is complete and a
  display system ranks by meaning (as before), or when its teaching index can
  rank (`ready` or `partial`); a rewrite's vector when the display systems use
  it, or the tutor would (`tutor_query_rewrite`). The display systems keep
  their rule: meaning lists only over a complete library index.
- `meaning` is unavailable without a complete library index (as before);
  `dense_verify` is unavailable only when no question's teaching scope has a
  complete index (its reason says so).
- Per question, a `dense_verify` pool that falls back (`hybrid_rrf`: no
  complete teaching index, or no query vector) is no dense baseline: it is
  never labelled, verified or scored. Its coverage counts it (`unavailable`;
  `failed` is now what did not run among the rest), the fallback reasons are
  counted (`verification.not_dense`), the teaching indexes' statuses are
  reported (`verification.teaching_dense_index`), and every verdict involving
  `dense_verify` is blocked (`verdict_blocks`, with a line in the Markdown).
  `pool_verify`'s fallback is the tutor's own production behaviour, so it
  stays verified and scored, as `pool_modes` reports.
- The dry run's plan is unchanged: it already plans a vector for every
  question and rewrite, an upper bound on what is now paid.

On the stage's copies every teaching scope is complete (`teaching_dense_index`
`ready` 47/47 and 41/41), so the published results (stage review §5.9) are
unaffected. A rerun confirmed it (below).

### F7: rejected again

The re-review is right that the fix step changed documentation only: the
defaults stay changed under the existing versions, with no successor, no
restoration of the predecessors' defaults and no upgrade or shadow check. That
is the owner's decision, not an omission:

1. **The owner asked for exactly this compatibility behaviour.** The request
   ("we're cutting the model off prematurely and its probably affecting output
   quality significantly"; "no tutor deadline cancellation for now") is about
   the owner's existing vaults, all at existing versions (`mvp-0.9` to
   `mvp-0.13`). Restoring the predecessors' defaults under those versions
   would restore the truncation the owner asked to remove; a successor would
   hold the fix behind `learnloop upgrade` on every vault; a shadow check
   contradicts the owner's standing decision (2026-10-12: live changes behind
   kill switches, no shadow stages by default).
2. **No persisted meaning changes, and the re-review names none.** The
   playbook's trigger is "scoring, scheduling, projection, or admissibility
   semantics"; T6's handoff: "Retrieval is context, so no successor is needed
   unless something persisted changes meaning". Checked at `1985c6d9`: the
   changed keys (`ai.output_tokens`, `ai.route_output_tokens`,
   `ai.route_reasoning_effort`, `source_retrieval.pool`,
   `pool_keyword_extras`, `tutor_deadline_cancels`, the three per-question
   reservation caps) are read only where requests are built or admitted
   (`ai/`, `source_retrieval/`, `practice_index/`, `projects/`, `ops/`,
   `cli/`, `diagnosis/offline_review/spend.py`, the recurrence judge's request
   budget). No module under `substrate/` (replay, the rebuild orchestrator,
   projections), the scheduler, scoring, evidence or certification reads
   them; the `output_tokens` hits under `substrate/` are receipts' usage
   columns. Every answer produced under the new budgets or effort is a new row
   under a request-derived id that includes them, and replay makes no model
   call.
3. **The version/fingerprint decision (playbook step 4) is made and recorded**
   beside the snapshots in `config/template.py`, as at the T1, T6 and
   stuck-prompt merges, which each recomputed every snapshot for keys that
   change no persisted meaning.
4. **Per-vault restoration exists without a version:** `source_retrieval.pool
   = "hybrid_rrf"`, `tutor_deadline_cancels = true`, `ai.output_tokens` /
   `ai.route_output_tokens`, `ai.route_reasoning_effort`.

Owner question 1 above stays open: the owner may still ask for a successor
at the checkpoint.

### Real calls

The T6 report rerun on the same backup-API copies
(`fixtures-local/t6fu/probability`, `fixtures-local/t6fu/arxiv_v2`; the
tracked vaults were never touched), one after the other, through the stage's
driver (`fixtures-local/t6fu/scripts/run_eval.py`, `--max-cost-usd` 15, the
$5 billed cap) into new output directories seeded with the earlier runs'
query-vector caches (`fixtures-local/t6fu/out-f8/`).

| Step | probability (47 questions) | arxiv_v2 (41 questions) |
|---|---|---|
| Dry run (no request) | 669 calls, 2,154 candidates, 2,068 pairs, $14.05 of reservations: admitted (as before) | 585 calls, 1,885 candidates, 1,804 pairs, $12.26: admitted |
| Run: requests | **0** (8 writer, 41 rewrite, 176 label and 141 verification answers from the ledger and checkpoints; every query vector cached) | **0** (8, 33, 160, 123) |
| Billed | **$0.00** | **$0.00** |
| Teaching indexes | `ready` 47/47; no `dense_verify` pool fell back; coverage 47/47 per system | `ready` 41/41; none fell back; 41/41 |
| Results | summary, verdicts, per-type results, seed hits, label agreement and verification differences identical to §5.9's report | identical |

The stage's billed total stays **$1.18 of the $5 cap**. Driver output:
`fixtures-local/t6fu/logs/rereview-{dryrun,run}-{probability,arxiv_v2}.json`;
reports `fixtures-local/t6fu/out-f8/probability/source_retrieval-88d1a5df76740884.{json,md}`
and `fixtures-local/t6fu/out-f8/arxiv_v2/source_retrieval-76b6ce3ade149e70.{json,md}`.

### Gate

Code at `1985c6d9` (the commit after it changes only this file and the stage
review). `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`,
`TMPDIR` = the worktree's `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8398 passed**, 0 failed, 0 skipped (220 s; the fix step's 8395 plus the 3 F8 tests) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **91 passed**, 8307 deselected (80 s) |
| Frontend | not changed (no `apps/` file touched), so not run |
| DB reference scripts | no schema or configuration key changed, so not rerun |
| Sidecar RPCs | none added, so nothing to pin in `tests/test_mobile_allowlist.py` |

Before the gate, the 12 source-retrieval test files plus the review tests:
122 passed; `test_output_budget.py`, the compare-harness and tutor tests: 77
passed. `git status fixtures/` is clean: the tracked vaults were never
written.
