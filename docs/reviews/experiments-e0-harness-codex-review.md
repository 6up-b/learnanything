# Experiment E0 harness: Codex review, fix round 1

**Stage:** `experiments-e0-harness` (worktree `learnanything-e0`, branch `experiments/e0-contextual-embeddings`). **Review:** Codex `gpt-6-astra`, high effort, read-only (job `20261021-102454-94nEAZ`), on `e7e59e579`. **Fix commit:** `330379be7`.

All 18 findings reproduced: each has a regression test, and every one of them failed on the pre-fix tree. To check that, the sources of `e7e59e579` were swapped into the worktree for one run and then restored byte for byte from a backup (no `git stash`). That run gave **30 of 30 failed**. Every finding is fixed; none was rejected.

**No live, paid or network call was made ($0.00).** Every test uses fakes: hash-vector embeddings, `tests/e0_fakes.FakeRoleClient` / `FakeRoleCaller`, `tests/embedding_fakes.BagOfWordsEmbedder` and the fake `openai` module, with a socket guard. Any test that runs production retrieval sets the vault's `ai.active_provider = "manual"`, so no verification or comparison route can resolve a real client. No credential or settings file was read, and no tracked fixture vault was opened.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (in `tests/test_e0_review_round1.py` unless named) |
|---|---|---|---|---|---|
| F1 | High | System-arm backfill embeds protected material | fixed | `330379be7` | `test_f1_service_copy_preparation_never_sends_protected_text` (the real preparation path through the production backfill, with an embedder that fails on any exam, solution or protected-header text; neither service database keeps the text), `test_f1_the_guard_refuses_a_batch_carrying_protected_text` |
| F2 | High | Metered output reservations do not bound actual requests | fixed | `330379be7` | `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy` (the real OpenRouter client on the fake SDK: the emitted `max_tokens` is the policy's 16,384 and the reservation covers it); `tests/test_e0_budget.py::test_the_request_gate_admits_every_physical_request` (an unbounded metered request is refused) |
| F3 | High | Configurable profiles can bypass billing and invalidate model pins | fixed | `330379be7` | `test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request` (a metered `codex_luna`, another model, another endpoint: refused with no request and an empty ledger; a copy redefining the experiment profile is refused), `test_f3_a_changed_identity_never_reuses_a_checkpoint` |
| F4 | High | Paid CLI calls have no receipt destination | fixed | `330379be7` | `test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes` (the paid CLI run from a directory outside any vault: receipts and verdicts land in the copy's experiment repository; nothing is created in the working directory) |
| F5 | High | Paid execution discards the reserved-family split | fixed | `330379be7` | `test_f5_the_paid_run_executes_the_frozen_split_or_refuses` (`--reserve-share 0.5` is rebuilt exactly; a different share or a plan without one is refused before spending) |
| F6 | High | Deictic questions lose their referent during labeling and judging | fixed | `330379be7` | `test_f6_deictic_questions_carry_their_own_selection_to_every_role` (two "Why does this step follow?" questions: retrieval, both label prompts, the sufficiency review, the tutor and the judges each carry their own selected passage), `test_f6_a_quote_over_withheld_spans_falls_back_to_the_selected_block` |
| F7 | High | Invalid adjudicator references silently weaken sufficient evidence sets | fixed | `330379be7` | `test_f7_a_malformed_adjudication_leaves_sufficiency_unresolved` (5 cases: an unknown ref, a duplicate ref, a disputed candidate left unlabelled, answerable without a set, unanswerable with a set) |
| F8 | High | Bounded fallbacks are scored as whole-section/source successes | fixed | `330379be7` | `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs` |
| F9 | High | S4 can approve an arm whose actual Reader latency regresses | fixed | `330379be7` | `test_f9_latency_needs_the_deadline_and_no_paired_regression_against_the_incumbent`, `test_f9_finalist_latency_includes_a_fresh_online_query_and_the_search`; `tests/test_e0_paid_fakes.py::test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints` (a resume reports the original measurement and marks it cached) |
| F10 | Medium | Experiment verdicts never enter `judgment_ledger` | fixed | `330379be7` | `test_f10_verdicts_enter_judgment_ledger_once` (label passes, sets, adjudication and answer judgements, each with its model, prompt version, input identity and span references, appended once across a repeat) |
| F11 | Medium | The documented paid command cannot resume | fixed | `330379be7` | `test_f4_f11_...` (a second CLI run reopens both service copies and re-sends no document), `test_f11_an_interrupted_service_copy_is_set_aside_and_prepared_again` |
| F12 | Medium | Required production controls are replaced by raw search | fixed | `330379be7` | `test_f12_system_arms_use_find_sources_and_an_unverified_intent_is_no_ranking`, `test_f12_an_incompletely_covered_service_copy_blocks_the_qwen_system_arms`; `tests/test_e0_paid_fakes.py::test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched` |
| F13 | Medium | Batched labeling cannot discover cross-batch evidence conjunctions | fixed | `330379be7` | `test_f13_a_conjunction_split_across_batches_is_found_by_the_joint_review` |
| F14 | Medium | The declared execution limits are not enforced correctly | fixed | `330379be7` | `test_f14_a_run_past_its_wall_time_stops_cleanly_and_reports_incomplete`; `tests/test_e0_budget.py::test_the_wall_time_bound_refuses_every_later_admission_including_retries`, `::test_subscription_requests_are_admitted_at_zero_and_never_hit_the_request_cap` |
| F15 | Medium | Token estimates are incorrectly treated as guaranteed bounds | fixed | `330379be7` | `test_f15_provider_limits_use_a_guaranteed_upper_bound` (dense notation and punctuation: the estimate undercounts, the bound refuses a document and a query, a whole segment between the estimate and the bound gets no window) |
| F16 | Medium | Finalist selection mixes the real slice into development | fixed | `330379be7` | `test_f16_finalists_come_from_the_primary_development_slice_only` (the logged slice and the direct lookups favour another arm; mixing would have picked it) |
| F17 | Medium | Missing work can become a smaller "complete" experiment | fixed | `330379be7` | `test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator`, `test_f17_an_answer_stop_keeps_the_planned_denominator` |
| F18 | Medium | Paid embedding artifacts are not durably resumable | fixed | `330379be7` | `test_f18_a_torn_vector_append_is_recovered_and_raw_output_is_kept`, `test_f18_query_vectors_are_cached_and_not_repaid`, `test_f18_concurrent_writers_never_duplicate_a_key`; `tests/test_e0_paid_fakes.py::test_resume_pays_only_for_what_is_missing` (no document, query or online measurement is re-sent) |

## What changed, per finding

- **F1.** `system_arms.redact_service_copy` blanks every block the frozen policy withholds in the service copy's own `source_document_blocks`, section headers included (the FTS index follows by its triggers). It runs before the production backfill, search, rewrite and verification. A blank block cannot be embedded, adds no section-path title and matches no keyword, so dense coverage is still complete over what is left. A second guard, `ProtectedTextGuard`, wraps the backfill client and refuses any batch that still carries a protected passage. This is the experiment package's one raw SQL write. It refuses any database outside fixtures-local and is registered, with a comment, in `tests/test_architecture.py`'s SQL owners. `test_e0_isolation` was renamed to pin that one statement.
- **F2.** The pin's `output_tokens` is now only an expected value. `LiveRoleCaller` resolves the normal policy (`learnloop.ai.output_budget.output_budget` for the role's profile: 16,384 unless the profile or route sets otherwise; spec §6: "keep the existing output-budget policy"). It installs that bound with `generation_limit` and allows the transport's own truncation retry. The gate reserves exactly the bound each physical request is sent with. A metered request with no bound is refused.
- **F3.** `callers.check_pin` compares the resolved client with its pin before anything is sent: transport type, model, billing class (taken from the client, never assumed from the pin) and, for a metered pin, the experiment's own endpoint. The pinned effort is requested on every call. `with_experiment_profiles` refuses a copy that defines `e0_openrouter_sonnet` differently. The resolved identity and the output bound are part of every checkpoint key.
- **F4, F10.** New `records.ExperimentRecords`: a fresh vault under `<run>/<copy>/records` (fixtures-local only), migrated to head. Every model call of the copy's run is observed into its `model_call_receipts` (`owner_kind = "experiment_e0"`), and the CLI binds its own `CommandReceipts` to the same repository. Each verdict is appended once to `judgment_ledger` with `append_judgment`: the task, the question and unit or arm, the resolved model, the prompt version, the checkpoint key as `input_hash`, and the span references and receipt ids in `rationale`. The id is derived from that identity.
- **F5.** The plan now records `reserve_share` and the family `splits`. `live.rebuild_frozen` rebuilds the copies with the plan's share and per-vault strata. It refuses with `PlanMismatch` before any spending when the pins fingerprint, the run id (policy, units and bank ids) or the splits differ. `runner.plan_identity` is the one definition shared by the dry run and the paid run.
- **F6.** `bank.freeze_context` freezes one policy-checked context per question: the learner's quote when every span it covers is permitted, else the selected block, bounded at 1,200 characters. `BankQuestion.context()` and `.retrieval_query` carry it to retrieval, both label passes, the sufficiency review, the adjudicator, the tutor and both judges. Reading an unfrozen context raises.
- **F7.** `bank.adjudication_problems` rejects a whole set that has an unknown or repeated ref, a label for an unknown or repeated candidate, a disputed candidate left unlabelled, a set member labelled background or unrelated, and an answerability that contradicts the sets. Any of these leaves the question unresolved with no accepted set, so S1 blocks it. A label pass's malformed sets are counted and force an audit.
- **F8.** Answers carry `Delivered.arm` (for example `D3_fallback_d2`), the planned arm and the delivery receipt. `delivery.does_not_fit` counts fallbacks per planned arm. The whole-context pairs (`D2`/`D3` minus `D1`) pair only real D2/D3 answers, and fallback answers appear under their own names. `D1_vs_D0` was added.
- **F9.** Each finalist's Reader latency is measured online, per question: a fresh query embedding (never the cache), the exact search and the D1 delivery, plus the tutor call. The measurement is stored once under `<run>/latency`, and a resume reuses the original value. Role checkpoints keep the original tutor latency, and a cached answer is marked `cached`. `paid.latency_check` requires the frozen deadline and no paired p50/p95 regression against the incumbent, within `pins.LATENCY_REGRESSION_TOLERANCE` (0.10, new open question 8). S4 compares the best hosted finalist with the best one-model arm, and S2 compares D2/D3 with D1.
- **F11.** `prepare_service_copies` keeps a state file. A copy whose preparation completed for the same frozen tree digest, policy and harness is reopened. An incomplete or incompatible one is moved aside (`.<name>.stale-*`) and prepared again. The backfill is idempotent.
- **F12.** `R0` and `R1_service_rrf` run the actual `find_sources`: policy `reading`, the question's intent, intent lists, the mandatory verification of a non-explain intent, the `compare` delegation, and two pages with cross-page duplicates counted. `R1_service_pool` stays as R1''s named first-page `dense_plus_bm25` variant. The new `R1_pool_verify` is the production `pool_verify` control (`tutor_pool` with `dense_plus_bm25`, then `verify_spans`). Per question, an arm records its pages, verification status, pool mode and dense use. When a required verification does not run, or a Qwen arm's search falls back from dense ranking, that question has no ranking. The Qwen system arms are blocked when the service copy's dense coverage is incomplete. A materially incomplete arm (below 95% completion) makes the run incomplete. `SystemRequestGate` bills each production LLM request by its resolved client and lets embedding requests through to their `LedgerEnvelope` admission.
- **F13.** A pool larger than one label batch is labelled for relevance batch by batch. Then one joint sufficiency review per pass sees every candidate that pass judged required or helpful, so a conjunction split across batches can still be proposed. The plan's estimate includes these calls.
- **F14.** `E0Ledger.start_clock(pins.MAX_WALL_S)` is started by `run_live`. Every later admission, each retry included, is refused with `E0DeadlineExceeded`, and `run_paid` also checks the clock between steps. The request cap now counts metered requests only, because the owner exempted subscription transports; their usage is still tallied.
- **F15.** `pins.token_upper_bound` (UTF-8 bytes + 8: a byte-level BPE or byte-fallback tokenizer emits at least one byte per token) is used for every provider limit (document, request, query), for whole-segment fits and for admission. `pins.token_estimate` (bytes/3) is the renamed estimate, used only for the plan, the unit cap and the window packing target.
- **F16.** Finalists are picked on the primary slice only: development questions outside `direct_lookup` and `no_support`. The paired comparisons use it. `retrieval_slices` reports the primary slice, all development, logged, direct lookups, no-support, every stratum and every intent, each with its own denominators. The logged-slice comparison is reported apart.
- **F17.** `run_paid` counts the planned work: seeds, labels, mandatory and sampled audits, and the answer schedule. A seed the writer omitted, or work a stop left undone, appears under `planned.missing`, makes the run `incomplete` and stops verdicts through S1's new `incomplete_work` input. The writer and the labeller keep what they finished before a stop. Answer summaries carry `planned` and `missing`. The answer schedule is a fixed interleaved order (spec §6).
- **F18.** `VectorStore` records are checksummed lines that keep the decoded vectors and the provider's raw rows. Appends run under an `fcntl` lock, re-read what other writers added, and are fsynced. A torn last line is ignored on load and truncated on the next append, and a damaged complete record is refused. Query vectors are cached per `query_vector_key` by every adapter (Qwen included). `fresh=True` re-sends a query for the online measurement.

The report renders the planned work, `does_not_fit`, the latency checks, the slices and the system arms. The committed dry-run aggregate (`docs/reviews/artifacts/experiments-e0/dry-run-plan.{json,md}`) was regenerated on the same local copies. The run used `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR, `OPENROUTER_BASE_URL`/`OPENAI_BASE_URL` set to `http://127.0.0.1:9` and no key variable. Results: network calls 0; copy trees unchanged; keys absent; **$8.72 expected, $26.16 worst case** against the $25 cap, every category within its allocation. The estimate now includes the online-latency queries and the joint reviews, and the backfill estimate excludes redacted blocks. The stage review (`experiments-e0-contextual-embeddings.md`) corrects its no-SQL claim, the estimate, deviation 4 and open question 3, and adds open question 8.

## Notes

- **R1_pool_verify on the owner's copies** verifies on the service copy's own `source_rerank` route. That is Codex on the owner's configuration, so it is billed at $0 as subscription. Its cost is latency and one Codex request per question. A metered route without `source_retrieval.llm_price_per_million` is refused and recorded.
- **Not changed (outside the findings):** the canaries still validate documents only, not query compatibility (listed by Codex under spec conformance, not as a finding). The backfill price comes from the copy's `source_retrieval.query_embedding_price_per_million`, as before.
- **Isolation slips (no effect):** two `python3` invocations ran outside `env -i`: an empty no-op heredoc and `python3 -c "print(1)"`. Neither imported the app, used the network or read a credential. Every other Python or CLI run outside pytest (lint-imports, the dry run) used `env -i PATH=$PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.

## Gate (this step, on `330379be7`)

Owner rule 2026-10-17: no full suite, durability lane or vitest here. No migration, DB/connection code, frontend, `src-tauri` or schema change was made, so no durability, vitest, cargo or DB-reference step applies. No config key and no CLI option changed.

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `.venv/bin/lint-imports --no-cache` (under `env -i`): **29 kept, 0 broken**.
- `uv run pytest -n auto <22 files>` with `TMPDIR=fixtures-local/tmp`: **241 passed**. Files:
  - The E0 files, **123** in total:
    - `tests/test_e0_review_round1.py` (30, new);
    - `tests/test_e0_adapters.py` (18), `tests/test_e0_bank.py` (8), `tests/test_e0_budget.py` (10), `tests/test_e0_corpus.py` (18), `tests/test_e0_credentials.py` (4), `tests/test_e0_delivery.py` (6), `tests/test_e0_dry_run.py` (7), `tests/test_e0_isolation.py` (4), `tests/test_e0_metrics_stop_rules.py` (12), `tests/test_e0_paid_fakes.py` (6).
  - The contracts: `tests/test_architecture.py`, `tests/test_cli_help_snapshot.py`, `tests/test_sqlite_file_copies.py`, `tests/test_tracked_fixture_databases.py`.
  - The modules the harness reuses or reads: `tests/test_tutor_delivery_fixes.py`, `tests/test_source_inventory.py`, `tests/test_reader_observation_records.py`, `tests/test_approach_map_boundaries.py`, `tests/test_workbench_hint_service.py`.
  - The CLI tests: `tests/test_cli_entrypoint.py`, `tests/test_cli_commands.py`.
- The E0 files were run twice more to check for flakes: 123 passed each time. A latency test that compared millisecond fake timings under load was flaky once; it was fixed by giving it a steady simulated tutor latency.
- Fail-before on `e7e59e579`: the 30 round-1 tests, **30 failed**.
- Changed test files: `tests/e0_fakes.py` (`FakeRoleClient`, `manual_ai`, the sufficiency schema), `tests/test_architecture.py` (the SQL owner registration), `tests/test_e0_bank.py`, `tests/test_e0_budget.py`, `tests/test_e0_corpus.py` (the token-helper rename), `tests/test_e0_isolation.py`, `tests/test_e0_paid_fakes.py`.
- The main checkout's tracked fixtures were not opened or changed by this step.

## Re-review (fix round 2)

**Re-review:** Codex `gpt-6-astra`, high effort, read-only (job `20261021-113712-Q0d0Er`), on `e7e59e579..f01b40941` (fixer commit `330379be7`). F1-F5, F8 and F9 were confirmed fixed. F6 and F7 were reopened, and two new findings were raised (F19 High, F20 Medium). **Fix commit:** `e5c6c7342`.

Every finding reproduced. Each has a regression in `tests/test_e0_review_round2.py` (17 tests). To check fail-before, the four changed sources were replaced with their `f01b40941` versions for one run, then restored byte for byte from a scratch backup (`cmp`-checked; no `git stash`). That run gave **14 failed, 3 passed**. The 3 that passed are guards that must still hold after the fix: a permitted quote is still delivered, an inherited supporting label still completes a set, and an explicit background member was already caught. No finding was rejected.

**No live, paid or network call was made ($0.00).** The tests use fakes only (`FakeRoleClient`, `BagOfWordsEmbedder`, hash vectors) behind a socket guard. Production retrieval runs on service copies with `ai.active_provider = "manual"`, so only the injected fake clients can answer. No credential or settings file was read, and no tracked fixture vault was opened.

| ID | Severity | Title | Verdict | Commit | Test (in `tests/test_e0_review_round2.py`) |
|---|---|---|---|---|---|
| F6 (reopened) | High | A rejected quote still reaches tutor and judge prompts through delivery | fixed | `e5c6c7342` | `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges[D0,D1]`, `test_f6_delivery_refuses_a_protected_quote_even_from_an_unfrozen_selection`, `test_f6_a_permitted_quote_is_still_delivered` |
| F7 (reopened) | High | An omitted set member that inherits `background` is accepted as sufficient | fixed | `e5c6c7342` | `test_f7_a_set_member_is_checked_against_the_merged_final_labels[False,True]` (False: the member omitted and inherited; True: labelled background explicitly), `test_f7_an_inherited_supporting_label_still_completes_a_set` |
| F19 | High | Production verification mishandles the embedding spend envelope | fixed | `e5c6c7342` | `test_f19_successful_production_verification_charges_once_per_physical_request[subscription,metered]`, `test_f19_a_qwen_arm_charges_embeddings_and_verification_once_each`, `test_f19_the_ledger_envelope_ignores_a_subscription_sentinel` |
| F20 | Medium | Failed delegated comparisons count as completed rankings | fixed | `e5c6c7342` | `test_f20_a_failed_delegated_comparison_is_missing_not_ranked` (5 cases: unavailable, failed, over budget, verification timed out, verification unavailable), `test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding` |

### What changed

- **F6.** `bank.freeze_context` now also freezes the selection to the policy. When the quote covers a withheld span, the frozen `question.selection` drops the quote and keeps only the permitted covered spans. Delivery reads `question.selection`, so the tutor and the judges get the same context the labellers saw: the selected block, never the quote. As a second check, `delivery._selection_spans` delivers a `selected_text` quote only when every span it covers is permitted; otherwise it records the drop in the receipt's `policy_dropped`. This covers a selection that was never frozen.
- **F7.** `bank.adjudication_problems` checks every set member against its final label. That is the adjudicator's own label, or else the label both passes agreed on, which is what `adjudicate` merges. A member that is not `required` or `helpful` (an inherited `background` included) gives `set_member_not_supporting`, and the question stays unresolved with no accepted set.
- **F19.** The cause: the production `SpendBudget.request` reserves every request in each active envelope, LLM requests included. On the system arms, `LedgerEnvelope` therefore billed each metered LLM request a second time, as an embedding, next to the `SystemRequestGate` reservation. A subscription request's `NO_RESERVATION` (text `"0"`) was settled as a ledger id and raised `KeyError('0')`. The fix:
  - `rank_system` no longer activates a `LedgerEnvelope`. `SystemRequestGate`, the transport's per-request gate, admits both kinds once per physical request. An embedding goes to `embeddings` at the Qwen pin's upper-bound price on `pins.token_upper_bound` of its inputs, with no output, and is settled from the usage it reports. An LLM request goes to `answers_verification`, billed by the resolved client as before: subscription at $0; metered at `source_retrieval.llm_price_per_million` within its output bound.
  - `LedgerEnvelope` now settles, charges or releases only handles it returned (ledger ids). A subscription sentinel is ignored. The backfill, whose every request is an embedding, keeps its envelope.
  - The tests run successful production verification under both billing classes and assert one settled ledger entry per physical request. A Qwen `R1_pool_verify` run shows exactly one `embeddings` entry per embedding request plus one `answers_verification` entry per verification request.
- **F20.** New `system_arms._comparison_outcome`. A delegated `compare` is a ranking only when its status is `ok`, or the honest `too_few_sources`, and its verification ran (`verified`/`cached`, or `not_needed` with no candidate sources). On a Qwen arm it also needs its query embedding (`embedded`/`cached`). Anything else is recorded as missing: `compare_unavailable`, `compare_failed`, `compare_over_budget`, `compare_cancelled`, a route skip, or `compare_verification_<status>`. It counts against completion (S1) and never enters scoring. Dense use is now decided per interface, so a comparison no longer bypasses the dense check.

### Notes

- **Isolation slip (no effect):** one empty `python3` heredoc, a no-op that imported nothing, ran outside `env -i` while a test file was being edited. It read no credential and used no network. Every other Python or CLI run outside pytest (`lint-imports`) used `env -i PATH=$PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.
- **Not re-run:** the dry run, and its committed aggregate. The changes touch neither the plan nor its estimates, the run identity (query ids are unchanged) nor the CLI.

### Gate (this step, on `e5c6c7342`)

Owner rule 2026-10-17: no full suite, durability lane or vitest here. No migration, DB/connection code, frontend, `src-tauri`, schema, config key or CLI option changed, so no durability, vitest, cargo, DB-reference, config-snapshot or CLI-help step applies.

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `.venv/bin/lint-imports --no-cache` (under `env -i`): **29 kept, 0 broken**.
- `uv run pytest -n auto <17 files>` with `TMPDIR=fixtures-local/tmp`: **231 passed**. Files:
  - The E0 files, **140** in total:
    - `tests/test_e0_review_round2.py` (17, new);
    - `tests/test_e0_review_round1.py` (30), `tests/test_e0_adapters.py` (18), `tests/test_e0_bank.py` (8), `tests/test_e0_budget.py` (10), `tests/test_e0_corpus.py` (18), `tests/test_e0_credentials.py` (4), `tests/test_e0_delivery.py` (6), `tests/test_e0_dry_run.py` (7), `tests/test_e0_isolation.py` (4), `tests/test_e0_metrics_stop_rules.py` (12), `tests/test_e0_paid_fakes.py` (6).
  - The contracts: `tests/test_architecture.py` (18), `tests/test_sqlite_file_copies.py` (1), `tests/test_tracked_fixture_databases.py` (2).
  - The production modules the fixed paths drive (verification, delivery): `tests/test_source_retrieval_followup.py` (14), `tests/test_tutor_delivery_fixes.py` (56).
- Fail-before on `f01b40941`'s sources: `tests/test_e0_review_round2.py`, **14 failed, 3 passed** (the 3 are the guards named above).
- Changed files: `src/learnloop/experiments/contextual_embeddings/{bank,budget,delivery,system_arms}.py`; new `tests/test_e0_review_round2.py`. No production module outside the experiment package changed.
- The main checkout's tracked fixtures were not opened or changed by this step.

## Fix round 3 (orchestrator)

**Final verify:** Codex job `20261021-120108-Ig3dcp` on `f01b40941..cfb8de724`. It confirmed F1-F9 and F19 fixed. It reopened F20 (Medium) and raised F21 (High). **Fix commit:** `24244b98f`.

Both findings reproduced. Each has regressions in the new `tests/test_e0_review_round3.py` (21 tests). Fail-before ran on `cfb8de724`'s `src`, `migrations` and `calibration_bundles`, extracted with `git archive` and loaded with `pytest -o pythonpath=<archive>/src` (no `git stash`). It gave **15 failed, 6 passed**. The 6 that passed are guards that already held: an empty usage, a NaN cost and a negative cost on the system gate, and an omitted, empty or boolean usage on the hosted adapter. On the old code, the scenario tests failed for the reasons the verify gave. The second usage-less embedding request `DID NOT RAISE` the budget refusal. The keyword-only comparison was ranked as `{'q1': [...]}` with `dense_used: 1`.

**No live, paid or network call was made ($0.00).** The tests use only the fake `openai` module, hash-vector embeddings and fake role clients, behind a socket guard. Service copies run with `ai.active_provider = "manual"`.

| ID | Severity | Title | Verdict | Commit | Tests (in `tests/test_e0_review_round3.py`) |
|---|---|---|---|---|---|
| F21 | High | A missing embedding usage releases the spend reservation as zero | fixed | `24244b98f` | `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`, `test_f21_a_metered_system_llm_request_without_input_usage_or_cost_keeps_its_reservation` (8 cases), `test_f21_reported_input_tokens_or_an_explicit_cost_still_reconcile`, `test_f21_the_role_gate_never_settles_a_metered_request_from_output_tokens_alone`, `test_f21_a_hosted_embedding_without_positive_usage_keeps_its_reservation` (5 cases), `test_f21_the_ledger_envelope_keeps_a_zero_dollar_reconciliation_reserved` |
| F20 (reopened) | Medium | A keyword fallback counts as a completed dense ranking | fixed | `24244b98f` | `test_f20_a_keyword_only_comparison_is_missing_for_a_qwen_arm` (the verify's scenario), `test_f20_a_comparison_whose_source_searches_ranked_by_meaning_is_dense`, `test_f20_the_comparison_outcome_needs_every_counted_source_search_dense`, `test_f20_the_search_observer_is_scoped_and_removed` |

### What changed

- **F21.** There is now one rule, `budget.reconciled_usd`. A metered reservation moves, down or up, only on an explicit, finite, nonnegative provider cost, or on a reported, positive input-token count. Anything less keeps the whole reservation as `unknown_billing`, counted against the cap. That covers no usage, an output count alone (the production embedding wrapper's constant `output_tokens=0`), zero input tokens, booleans, NaN and negative values. When input is reported and output is not, the output side is charged at the reserved bound. Every settle path in the package was audited:
  - `system_arms.SystemRequestGate.settle` (the reported case). Embeddings and metered LLM requests both use the rule. Admissions are a small dataclass that carries the reserved output bound (0 for an embedding).
  - `callers.E0RequestGate.settle` had the same pattern: one integer, even an output-only one, settled the request. It now uses the rule, with the request's own output bound.
  - `adapters.EmbeddingAdapter._send` (hosted Perplexity and Voyage). `total_tokens or prompt_tokens` let an explicit `prompt_tokens: 0` settle at $0, and a negative cost would have raised inside the ledger. It now takes the larger positive reported count and the rule.
  - `budget.LedgerEnvelope.settle` (the production backfill's envelope). The backfill hands over a reconciled dollar figure that cannot say whether it came from a cost or from `input_tokens=0` priced at $0. A $0 or non-finite figure now keeps the reservation.
  - Unchanged, by design:
    - `QwenAdapter._embed` already settles at its full estimate.
    - `LedgerEnvelope.unreserve` releases at $0 only a request that was never sent (production calls it only when another envelope refused).
    - A request that fails without settling keeps its reservation (`failed`).
    - `FakeRoleCaller` is a test double.
- **F20.** Dense use is never inferred from a successful query embedding.
  - On every interface, a search is dense only when its own `SpanSearch.describe()` has a `meaning` list and dense status `ready` (`system_arms._dense_ran`). That covers `find_sources`, on every page, `dense_plus_bm25_first_page` and `pool_verify`.
  - For a delegated comparison, `compare_sources` does not record how each per-source search ranked. So `rank_system` observes those searches at their one call. `observe_compare_searches` is a pass-through around `learnloop.source_retrieval.compare.search_spans`. It is installed while any observer is active, records into the current context only (a `ContextVar`, so threads never mix), and is removed with the last observer. Arguments and results are untouched, and no production module was edited.
  - `_comparison_outcome(result, searches)` needs three things: the query embedded, at least one source search, and every counted source search dense. A source with nothing embeddable and no hits (`empty`: the redacted exam) is not counted. A keyword-only, disabled, partial or unobserved search makes the query `dense_not_used` for a Qwen arm: missing, never ranked.
  - The system-arm report gains `compare_source_searches` (counts of `dense`, `nothing_embeddable`, `keyword_only:<status>`). The verify's scenario gives `{"keyword_only:disabled": 3}` and `missing: {"dense_not_used": 1}`.

### Dry run (re-run on the final code)

The dry run ran on the existing copies `fixtures-local/contextual-embeddings/vaults/{linear_algebra,probability}-20261021`. It ran under `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`, with no key variable and `OPENROUTER_BASE_URL=http://127.0.0.1:9`, and no settings file was read. Results:

- `network_calls: 0` and `copies_changed: 0`.
- The sha256 digest of every file under the copies was equal before and after.
- The empty HOME, CODEX_HOME and config directories stayed empty.
- The plan JSON and Markdown are **byte-identical** to the committed `docs/reviews/artifacts/experiments-e0/dry-run-plan.{json,md}`, so nothing there changed: **$8.72 expected, $26.16 worst case** against the $25 cap, every category within its allocation.

### Notes

- **Not changed (outside E0):** production's own request gate (`learnloop.ai.spend._reported_usd`) also accepts a lone `output_tokens=0` as a reported usage. E0 never runs under it: the system arms install `SystemRequestGate`, and the roles install `E0RequestGate`. This is recorded here for the production owner and was not changed in this stage.
- **Isolation slips (no effect):** two invocations ran outside `env -i`:
  - an empty `python3` heredoc (a no-op);
  - `.venv/bin/python -I -c` re-serializing the committed `dry-run-plan.json` for a diff. It imported only `json`, not the app, and read no credential.

  Every other Python or CLI run outside pytest used `env -i` with empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR: the two dry runs and `lint-imports`.
- Every pytest and lint run waited for, and held, `/tmp/learnloop-fullsuite.lock`. One early 3-second run of the new file started before the lock was noticed.

### Gate (this step, on `24244b98f`)

Owner rule 2026-10-17: no full suite, durability lane or vitest here. No migration, DB/connection code, frontend, `src-tauri`, schema, config key or CLI option changed.

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **29 kept, 0 broken**.
- `pytest -n auto` with `TMPDIR=fixtures-local/tmp` on 25 files: **293 passed**. Files:
  - The 13 E0 files: `tests/test_e0_review_round3.py` (21, new), `tests/test_e0_review_round2.py`, `tests/test_e0_review_round1.py`, and the ten harness files.
  - The contracts: `tests/test_architecture.py`, `tests/test_cli_help_snapshot.py`, `tests/test_sqlite_file_copies.py`, `tests/test_tracked_fixture_databases.py`.
  - The modules the harness reuses: `tests/test_tutor_delivery_fixes.py`, `tests/test_source_inventory.py`, `tests/test_reader_observation_records.py`, `tests/test_approach_map_boundaries.py`, `tests/test_workbench_hint_service.py`, `tests/test_source_retrieval_followup.py`.
  - The CLI tests: `tests/test_cli_entrypoint.py`, `tests/test_cli_commands.py`.
- Fail-before on `cfb8de724`: `tests/test_e0_review_round3.py`, **15 failed, 6 passed** (the 6 are the guards named above).
- Changed files: `src/learnloop/experiments/contextual_embeddings/{adapters,budget,callers,system_arms}.py`; new `tests/test_e0_review_round3.py`. No production module outside the experiment package changed.
- The main checkout's tracked fixtures were not opened or changed by this step.
