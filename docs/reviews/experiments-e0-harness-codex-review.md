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

## Fix round 4 (orchestrator)

**Verify:** Codex job `20261021-131313-hCUxeG` before the paid run, on `a76c8358a..b6179f60f`. It found 8 High and 6 Medium findings, all reopening the stage. **Fix commit:** `34d2068e1`.

Every finding reproduced. Each has regressions in the new `tests/test_e0_review_round4.py` (32 tests). Fail-before ran on `b6179f60f`'s `src`, `migrations` and `calibration_bundles`, extracted with `git archive` and loaded with `pytest -o pythonpath=<archive>/src` (no `git stash`). It gave **32 failed**. The behavioural failures are listed with each finding below. The rest failed on the API the fix adds (`E0PriceUnverified`, `authorized_ledger`, `CopyContainment`, `request_key`, `start_clock(wall=)`, `logged_questions`, `slice_completion`).

**No live, paid or network call was made ($0.00).** The tests use fake embedding transports, the fake `openai` module, hash vectors and fake role clients, behind a socket guard. The E0 test modules mark prices verified through a test-only fixture (`tests/e0_fakes.verified_prices`). The production pins stay empty.

### The orchestrator's rulings, as built

- **High 2: unverified prices.**
  - Every metered pin carries `price_verified: PriceVerification(source_url, checked_on)`. It is **empty**, and the orchestrator fills it from the providers' published price pages; nothing was filled from memory. The Qwen pin's earlier `price_verified=True` is gone.
  - Admission refuses any request priced by an unverified pin (`pins.price_problem`) at every gate: the hosted adapters, `QwenAdapter`, `E0RequestGate`, and `SystemRequestGate` for embeddings. A metered production LLM route on a service copy is priced only through a metered role pin with a verified price for its model; the copy's `llm_price_per_million` no longer admits anything.
  - The paid CLI also refuses authorization while any metered pin is unverified.
  - Each reservation is the request's hard maximum: the input upper bound (UTF-8 bytes + 8) plus the output bound it is sent with, at the verified price. The service backfill is now admitted per physical request by `SystemRequestGate` at that maximum. It used to go through `LedgerEnvelope` at the production estimate.
  - A settlement above its reservation records the overage and marks the ledger `halted`. `E0RunHalted` is raised after the record is written. Every later reservation, in any process or category, Codex included, is refused. `run_paid` stops at the next step (the status is `halted: …`), and `run_live` runs no further copy.
  - The dry run lists the unverified pins.
- **High 3: one budget per authorization.**
  - `budget.authorized_ledger` puts the ledger at `<fixtures-local>/contextual-embeddings/ledger/<plan_id>.ledger`. The root comes from the copies' own `fixtures-local` ancestor, never from `--run-dir` or the working directory.
  - The same plan reopens it. A plan without a ledger, while another plan's ledger exists, needs `--new-authorization <reason>` (a new CLI option; the help snapshot entry is updated). The reason and the plan id are recorded in the ledger, and a ledger refuses another plan's id.
- **Medium 10: a Codex request cap.**
  - `pins.MAX_SUBSCRIPTION_REQUESTS = 600`. It is persisted in the ledger at creation, and every physical subscription request counts against it, retries and repairs included. It is enforced at reservation, with $0 marginal accounting kept.
  - The run clock is persisted too: a resumed process keeps the elapsed time.
  - The dry run reports the planned count against the allowance.

### What changed, per finding

| ID | Severity | Fix | Fail-before on `b6179f60f` |
|---|---|---|---|
| High 1 | High | `corpus.contained_root`/`contained_database` run before any open (`open_copy`, `open_service`). The configured `storage.sqlite_path` must be relative, must not escape the copy and must not pass through a symlink, and the root must not be a symlink. `prepare_copies` backs up a relocated database into the copy and rewrites the copy's toml. | The absolute path was kept by `prepare` (`assert not True`); `CopyContainment` is missing |
| High 2 | High | See above. | `KeyError: 'prices'`; the halting/refusal API is missing |
| High 3 | High | See above. Two `run_live` runs with different run directories share one ledger. | `authorized_ledger` is missing; the ledger lived under each run directory |
| High 4 | High | `adapters.qwen_identity` checks the client's transport (the production OpenRouter embedding client), model, endpoint, dimensions and billing against the pin before its first request. A mismatch is a contract failure with nothing sent. The identity digest is in `document_space_id` and `query_encoder_id` (so in every vector key), and in every receipt. `SystemRequestGate` refuses another model's embedding. | `DID NOT RAISE` for each of the four changed identities; `KeyError: 'identity'` |
| High 5 | High | `corpus.permitted_titles`: a withheld or unanchored heading reads as `(withheld heading)` in every section path, the snapshot's `titles` included. `CandidateUnit.heading_keys` records the heading spans a unit's path names. They are in `unit_dependency`, `window_dependency` and `document_vector_key`, so a heading marked later invalidates the unit, its prompts and its vectors. | `'secret' not in 'midterm pro…cret heading'`; the heading key was missing from the dependency |
| High 6 | High | `bank.event_protection` uses the production authority, `learner_protection.PastWork.question_reason`. It checks the question on record, the item's protection (exam and held-out material, reservations, cold checks, probes, unknown items), the attempt, and the recorded assessment contract (it must be that item's own). `logged_bank` rejects protected or unresolved provenance before admitting text, and an unknown caller context. Without an authority, an event naming an item or attempt is rejected (fail closed). | A held-out item's question was admitted; `logged_questions` is missing |
| High 7 | High | `delivery.quote_covered`: a quote is used only when it names at least one span, every span it names exists and is permitted, and the normalized quote is a substring of their normalized canonical text in document order. Otherwise `freeze_context` rebuilds from the permitted block, and delivery drops the quote with reason `coverage`. | The protected text was in the frozen passage |
| High 8 | High | New `boundary.py`. Every `LiveRoleCaller` failure becomes `E0ProviderFailure`, which carries only an allowlisted classification, a status code and a safe request id; it is raised `from None`, so no traceback carries the original. `quiet_provider_logs` sanitizes records from `learnloop.ai`, `learnloop.source_retrieval`, `openai`, `httpx` and `httpcore` at every handler, the last-resort handler included, for the whole paid run and every system-arm search and backfill. The CLI prints `boundary.safe_message` only. The test uses the real OpenRouter client with an error body echoing the fake key. | The API is missing; on old code the CLI printed the key |
| Medium 9 | Medium | The canary checks the document AND the query method. Both must decode at the pinned dimensions and score in one paired space, and a response that names its model must name the pinned one. Qwen (`R1`) is canaried first, and a failed Qwen canary blocks R1-R3 and the three service arms. `run_live` runs the canaries before `prepare_service_copies`, which then skips the Qwen copy and its backfill. | A broken query method passed the canary; `KeyError: 'R1'` |
| Medium 10 | Medium | See above. | `TypeError` (no allowance or wall clock); `KeyError: 'subscription_requests'` |
| Medium 11 | Medium | `LiveRoleCaller` holds a cross-process `flock` claim per complete request identity (the checkpoint key). A second worker waits, then reuses the result. Checkpoints and failure markers are fsynced, the directory included. Every ledger entry carries its `request_key`. On resume, an admitted entry that was neither recorded nor marked failed is first recovered from the experiment's completed receipts (same prompt, output validates). Otherwise it raises `E0RequestBlocked` and is never re-sent. An attempt recorded as failed may retry. | 4 concurrent workers sent 4 requests; `request_key` is missing |
| Medium 12 | Medium | `budget.E0Stop` is the base of budget stops, `E0ProviderFailure`, `E0RequestBlocked` and `PinMismatch`. Every paid step (writer, contexts, arms, system arms, labels, audits, answers) catches it, records the incomplete work and its kind, and keeps the report. `run_live` writes an aggregate failure `results.json` and `report.md` for any other failure, with the classification only. | The failure report was never written, and the key was in the raised error |
| Medium 13 | Medium | `run_paid` computes completion per required slice (`development_all`, `logged`) beside the primary one, as `arm@slice` in S1's `arm_completion` and `slice_completion` in the results. | `KeyError: 'slice_completion'`; S1 allowed verdicts |
| Medium 14 | Medium | `paired_bootstrap` reports `families`: the real clusters of the complete-case pairs, excluding `none`. `exploratory` follows them. S4 takes `independent_families` from its paired evidence (the smaller of the retrieval and answer comparisons) and defers when that evidence is exploratory. | `KeyError: 'families'` |

### The dry run (re-run on the final code)

The dry run ran on the existing copies `fixtures-local/contextual-embeddings/vaults/{linear_algebra,probability}-20261021`. It ran under `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`, with no key variable and `OPENROUTER_BASE_URL=http://127.0.0.1:9`, and no settings file was read. Results:

- `network_calls: 0` and `copies_changed: 0`. The sha256 of every file under the copies was equal before and after, and the empty home directories stayed empty.
- It was run twice; the second run, on the committed code, is byte-identical to the refreshed artifacts `docs/reviews/artifacts/experiments-e0/dry-run-plan.{json,md}` (run `e0_b3532a323a4cdc1a`; the pins fingerprint changed).

**Estimate: $7.55 expected, $22.64 worst case** against the $25 cap; every category is within its allocation.

| Category | Expected $ | Worst case $ |
|---|---|---|
| embeddings | 0.12 | 0.37 |
| drafting/context | 0.00 | 0.00 |
| labels/audits | 4.45 | 13.34 |
| answers/verification | 2.98 | 8.93 |

**Codex requests: 3,175 planned against the allowance of 600 (does not fit).** The roles account for 1,995: writer 12, context 37, label passes 430 each, tutor 362, judges 362 each. The system arms account for 1,180: R0 472 and R1' 708, an upper-bound estimate. Retries and repairs count on top. At 600, the paid run would stop at the allowance with an incomplete report. **This is an orchestrator decision: raise the allowance, or reduce the plan.**

**Unverified prices (admission refuses each):** `pplx_4b`, `pplx_context_4b`, `qwen3_8b`, `voyage_4_large`, `voyage_context_4`, `adjudicator`, `judge_adjudicator`.

**Logged questions: 29 before, 14 now** (11 linear algebra, 3 probability; all Reader questions). Every practice and feedback question is rejected by the production protection:

- 4 are protected (their item is withheld).
- 11 are unresolved: the owner copies are at migration head 165, whose question events record no assessment contract, and `question_reason` treats an unrecorded contract as unresolved provenance.

The smaller logged slice is why the estimate fell from $8.72 to $7.55.

### Notes

- **Production follow-up (not changed here):** the shared `learnloop.ai.providers.openai_chat` client logs provider exceptions verbatim and raises `CodexUnavailable(str(error))`. E0 now wraps it at its own boundary; production callers outside E0 still carry that text.
- `LedgerEnvelope` remains for tests and reused paths. The paid run no longer uses it.
- **Isolation slip (no effect):** one `python3 -c "print()"` ran outside `env -i`; it imported nothing and used no network or credential. Every other Python or CLI run outside pytest used `env -i` with empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR: the two dry runs, `lint-imports`, and one help-snapshot write. That write rendered every entry differently under `env -i`, so it was reverted with `git checkout`. The one changed entry was then written from inside pytest, by a temporary test file that was removed afterwards.

### Gate (this step, on `34d2068e1`)

Owner rule 2026-10-17: no full suite, durability lane or vitest here. No migration, DB/connection code, frontend, `src-tauri` or schema change was made. One CLI option was added, and its help snapshot entry is updated.

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **29 kept, 0 broken**.
- `pytest -n auto` with `TMPDIR=fixtures-local/tmp` on 26 files (the 25 of round 3 plus `tests/test_e0_review_round4.py`): **325 passed**.
- Fail-before on `b6179f60f`: `tests/test_e0_review_round4.py`, **32 failed**.
- Changed:
  - `src/learnloop/experiments/contextual_embeddings/{adapters,bank,budget,callers,corpus,delivery,live,metrics,paid,pins,plan,records,retrieval,runner,stop_rules,system_arms}.py`;
  - new `boundary.py`;
  - `src/learnloop/cli/experiments.py` (the option and the safe failure output);
  - tests: `tests/e0_fakes.py` (the price fixture, the Qwen fake's identity), the existing E0 test modules (the fixture; four tests updated for the new rules: the canary query on resume, a canonical permitted quote, the verified role price, the Qwen identity), new `tests/test_e0_review_round4.py`, and `tests/cli_help_snapshot.json`.
- No production module outside the experiment package and its CLI changed.
- The main checkout's tracked fixtures were not opened or changed.

## Fix round 4 follow-up (orchestrator)

**Commits:** the merge `7bea424f8` and the follow-up `4ecbeebeb`. **No paid, live or network call was made ($0.00), and no Codex turn ran.**

### Verified prices

The orchestrator verified these on 2026-10-21, and the pins carry them exactly in `pins.PriceVerification(source_url, checked_on, note)`:

| Pin | Model | Price per 1M tokens | Source |
|---|---|---|---|
| `pplx_4b` | `pplx-embed-v1-4b` | $0.03 | https://docs.perplexity.ai/docs/pricing |
| `pplx_context_4b` | `pplx-embed-context-v1-4b` | $0.05 | https://docs.perplexity.ai/docs/pricing |
| `voyage_4_large` | `voyage-4-large` | $0.12 | https://docs.voyageai.com/docs/pricing |
| `voyage_context_4` | `voyage-context-4` | $0.12 | https://docs.voyageai.com/docs/pricing |
| `qwen3_8b` | `qwen/qwen3-embedding-8b` (OpenRouter) | $0.01 input | https://openrouter.ai/qwen/qwen3-embedding-8b/pricing |
| `adjudicator`, `judge_adjudicator` | `anthropic/claude-sonnet-5.5` (OpenRouter) | $2 input, $10 output | https://openrouter.ai/anthropic/claude-sonnet-5.5/pricing |

- **Voyage free tier:** both Voyage pins note that the first 200M tokens are free per account. Admission and reconciliation use the full $0.12 and never assume the free tier; a test checks the reservation.
- **Sonnet:** the record notes that the price matches Anthropic's table at https://platform.claude.com/docs/en/about-claude/pricing. The earlier +10% margin is gone, because the hard cap comes from the guaranteed token upper bounds.
- **No unverified price remains.**

### The Codex tool lockdown

- **Merge:** `git merge --no-ff main` (main `55063be64`) gave no conflicts.
- **Isolation contract:** main added the packages `learnloop.figure_admission` and `learnloop.figures`. `tests/test_e0_isolation.py` requires every production package in the import-linter contract `experiments-stay-outside-production`, so both are now in its `source_modules`.
- **The E0 Codex roles go through the locked-down transport.** The roles are writer, contexts, both label passes, tutor and judges. `LiveRoleCaller` resolves the production Codex client (`SdkCodexClient`) and calls `execute_structured_operation(..., isolated=True)`. On main, every turn of that client runs `_run_sdk_turn` with the lockdown's verified overrides, `TurnLockdown` and `ApprovalMode.deny_all`. A test stops the turn at the entry of `_run_sdk_turn` for `label_a` and `label_b`: both reach it, isolated, with no workspace, and nothing starts.
- **The paid run is gated on the lockdown.** `boundary.require_codex_lockdown()` runs first in `run_live` and in the paid CLI path. The run is refused (`CodexLockdownMissing`) before any ledger, copy or request when any of these fails:
  - `learnloop.ai.providers.codex_lockdown` must import;
  - the Codex provider must use its `TurnLockdown` and have the verified isolated launch;
  - `isolated_turn_overrides` must carry every lockdown configuration override, the command-environment allowlist and every disabled feature.

  Tests cover a missing module and a provider whose overrides drop `agents.enabled=false`; the CLI exits 1 with "lockdown is not active" and never calls the run.
- **Fail-before:** not meaningful here. With the pre-merge sources, the merged `conftest` itself imports `codex_lockdown`, so all 6 follow-up tests error at setup (`ModuleNotFoundError`). That is also the guarantee that matters: the unmerged branch has no lockdown and can no longer start a test, let alone a paid run.

### Unchanged by decision

- **The Codex allowance stays 600** against 3,175 planned, pending the Codex transport review.
- **The 11 logged practice and feedback questions with no recorded assessment contract stay rejected (fail closed).** The owner copies' migration head 165 records none, and the production protection treats that as unresolved provenance. The 4 whose item is protected stay rejected too, which leaves 14 logged questions, all from the Reader.

### The dry run (verified prices)

The dry run ran on the existing copies under `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`, with no key variable. Results:

- `network_calls: 0` and `copies_changed: 0`. The sha256 of every file under the copies was equal before and after, and the empty home directories stayed empty.
- Artifacts refreshed: `docs/reviews/artifacts/experiments-e0/dry-run-plan.{json,md}`, run `e0_2235492bf452889e`. The plan's cost basis now reads "the verified published prices on guaranteed token upper bounds".

**$6.79 expected, $20.36 worst case** against the $25 cap; the expected spend in every category is within its allocation.

| Category | Expected $ | Worst case $ | Allocation $ |
|---|---|---|---|
| embeddings | 0.04 | 0.12 | 2.00 |
| drafting/context | 0.00 | 0.00 | 5.00 |
| labels/audits | 4.04 | 12.13 | 10.00 |
| answers/verification | 2.71 | 8.12 | 8.00 |

- **Worst case:** labels/audits ($12.13) and answers/verification ($8.12) pass their allocations if every request were retried twice. Admission stops at the allocation, so such a run ends incomplete rather than overspending.
- **Metered calls:** adjudicator 86 calls ($4.04), answer adjudicator 128 calls ($2.71).
- **Embedding arms:** $0.001 to $0.009 each.
- **Codex:** 3,175 requests planned against the 600 allowance (does not fit). **Unverified prices:** none.

### Gate (this step, on `4ecbeebeb`)

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **30 kept, 0 broken**. That is 29 plus main's new `evidence-never-reads-figures`.
- `pytest -n auto` with `TMPDIR=fixtures-local/tmp` on 29 files: **499 passed, 1 skipped**. The files are the 26 of round 4, plus `tests/test_e0_review_round4_followup.py` (6, new) and the security lockdown tests `tests/test_codex_tool_lockdown.py` and `tests/test_codex_isolation_mcp_check.py` (168 passed). The skip is `test_codex_tool_lockdown.py:405`, which needs the `openai_codex` SDK; it is not installed in this environment.
- The main checkout's tracked fixtures were not opened or changed.
