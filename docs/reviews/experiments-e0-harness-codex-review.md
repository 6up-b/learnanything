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

## Re-plan: E0 off Codex (orchestrator, 2026-10-22)

Owner, 2026-10-22: "you can try running it through claude -p or the anthropic api key i provided". Codex is out of quota until Oct 27 and is being replaced for serving.

**Ruling:** E0 uses the Anthropic Messages API directly, never `claude -p`.

**Commit:** `494290c5f`. **No paid, live or network call was made ($0.00).**

### The transport (`src/learnloop/experiments/contextual_embeddings/anthropic_api.py`, experiment-only)

- **Requests.**
  - One HTTPS POST to `https://api.anthropic.com/v1/messages` per admitted request, with `anthropic-version: 2026-10-21`.
  - Body keys are within {`model`, `max_tokens`, `system`, `messages`, `temperature`, `stop_sequences`}. E0 sends only the first four. `temperature` is never sent, because version 2026-10-21 rejects sampling parameters.
  - `tools` and any other key (`tool_choice`, `mcp_servers`, `output_config`...) are refused before anything is sent (`check_body`).
  - `messages` is one user turn of plain text.
- **Admission and settlement.**
  - Every POST runs in `model_call` under the role's `E0RequestGate`, so the ledger admits it before it is sent.
  - The admission is the request's hard maximum: the input upper bound of exactly what is sent (`[system, user text]`) plus the `max_tokens` sent, at the verified price. Claude Haiku 5.5's >100k-token rate applies whenever the input upper bound passes 100k.
  - A transient failure (429, 5xx, 529, network) is retried as another admitted POST, at most twice.
  - Settlement uses the response's `usage` only. A response without usage keeps the whole reservation (round 3's rule).
- **Errors and the key.**
  - A refusal, a truncation or an answer outside the schema each raise an allowlisted `E0ProviderFailure`.
  - The key `ANTHROPIC_API_KEY` (configurable with `--anthropic-key-env`) is read from the environment that `--env-file` loads. It goes in the `x-api-key` header only, never into a log, receipt, ledger entry or exception.
- **Isolation.** Production never imports the module: the import-linter contract `experiments-stay-outside-production` covers all of `learnloop.experiments`, and a test scans the source tree.

### Roles

| Role | Model (exact API id) | max_tokens |
|---|---|---|
| writer (spec §5.1: a strong writer) | `claude-sonnet-5-5` | 16,384 |
| label pass A | `claude-haiku-5-5` | 8,192 |
| label pass B | `claude-sonnet-5-5` | 8,192 |
| adjudicator, answer adjudicator | `claude-opus-5-5` (differs from both labellers and both judges) | 16,384 |
| R3 contexts | `claude-haiku-5-5` | 16,384 |
| tutor, judges A and B | `claude-haiku-5-5` | 8,192 |

- **Model ids:** taken from the Claude API reference's model table, cached 2026-10-06; they could not be checked live offline. They are pinned in `pins.ANTHROPIC_MODELS`. Before any bulk work, `run_live` canaries each distinct model with one tiny admitted request; it must be answered as a `message` by exactly that model, with usage. A wrong model stops that copy's run with a failure report.
- **Prices:** all from https://platform.claude.com/docs/en/about-claude/pricing, `checked_on` 2026-10-22.
  - Haiku 5.5: $0.10/$0.50 per 1M tokens, $0.50/$2.50 above 100k.
  - Sonnet 5.5: $2/$10.
  - Opus 5.5: $4/$20.
- **Thinking:** adaptive thinking is always on and cannot be configured within the body grammar. Its tokens are output tokens. The plan estimates them per call (Haiku 1,000, Sonnet 1,500, Opus 2,000), and every request is reserved at its full `max_tokens` anyway.

### The system arms and Codex

- **System arms.** On the service copies only, `source_rerank`, `source_query_rewrite` and `source_compare` go to the OpenRouter profile `e0_openrouter_haiku` (`anthropic/claude-haiku-5.5`), with the copies' price settings filled for production's own caps.
  - **The slug and its price are PENDING orchestrator verification.** I could not check offline whether OpenRouter lists Claude Haiku 5.5. The pin `system_verifier` assumes Anthropic's own price and is unverified, so the ledger refuses every such request and the paid CLI refuses to start until it is filled.
  - The R0 copy is re-routed too: Codex is out, so R0 is now "today's path with OpenRouter Haiku on the source routes".
- **No Codex.** E0 makes no Codex call:
  - every role pin is metered (`require_no_codex_roles`, run first in `run_live`);
  - the paid run's canonical ledger is created with a Codex allowance of 0, so any subscription request is refused;
  - the plan counts 0 Codex requests (tested);
  - the lockdown gate of the follow-up stays as an extra guard.

### The dry run

The dry run ran on the existing copies under `env -i` (empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR, no key). Results:

- `network_calls: 0`, copies unchanged by sha256, empty home directories stayed empty.
- Artifacts refreshed: run `e0_5d51209082898626`, harness `e0-harness-v2`.

**$37.84 expected, $113.53 worst case against the $25 cap: it does not fit.**

| Category | Expected $ | Allocation $ |
|---|---|---|
| embeddings | 0.04 | 2.00 |
| drafting/context | 0.51 | 5.00 |
| labels/audits | 23.62 | 10.00 |
| answers/verification | 13.67 | 8.00 |

The drivers are three roles:

- label B on Sonnet: $11.62;
- the adjudicator on Opus: $11.52;
- the answer adjudicator on Opus: $10.53.

The rest: the writer $0.41, the system arms' OpenRouter Haiku requests 1,180 for $1.30, every Haiku role under $0.80 each.

**The smallest change that fits (proposed, not applied).** It was computed with the same dry-run arithmetic under `env -i`, with 0 network calls and the copies unchanged:

- label pass B → `claude-haiku-4-5`, a different model from label A ($1/$5 per the reference table; to be verified);
- the label adjudicator → `claude-sonnet-5-5`, which differs from both labellers;
- the answer adjudicator → `claude-sonnet-5-5`, which differs from the Haiku judges.

That gives **$16.71 expected**: labels $8.39 of $10 and answers $7.77 of $8, with no allocation change. It keeps two different labellers and a different adjudicator, but uses an older Haiku for pass B.

The alternative keeps the ruling's models and cuts the bank to about 36 scored questions, well below the 60-80 development target. That is not recommended.

### Recorded decision

The 11 logged practice and feedback questions with no recorded assessment contract stay rejected (fail closed), as ruled in the follow-up.

### Gate (this step, on `494290c5f`)

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **30 kept, 0 broken**.
- `pytest -n auto` with `TMPDIR=fixtures-local/tmp` on 30 files: **511 passed, 1 skipped**. The skip needs the `openai_codex` SDK. The files:
  - the 16 E0 files, including the new `tests/test_e0_review_round5.py` (13 tests): body grammar, admission equals the wire with a fake server, missing usage, Haiku's long rate, the key and allowlisted errors, the roles, no Codex role, zero Codex requests and a zero allowance, the re-routed service copies refused while pending, model canaries, a role call through the transport, and no production import;
  - the 12 contract and reuse files;
  - the 2 Codex lockdown test files.
- Tests updated for the new roles: the writer is metered, the fake profiles are the Anthropic ones, and the metered system verifier is the OpenRouter Haiku profile. The CLI help snapshot entry is updated for the new `--anthropic-key-env` option.
- The main checkout's tracked fixtures were not opened or changed.

## Cap raised to $40, models kept (owner, 2026-10-22)

**Commit:** `ab9da7b65`. **No paid, live or network call was made ($0.00).**

The owner raised the E0 cap to $40 and kept the re-planned models: Claude Haiku 5.5 for label A, Claude Sonnet 5.5 for label B and the writer, Claude Opus 5.5 for both adjudicators. The proposed Haiku 4.5 option above is withdrawn.

### Cap and allocations

- **Cap:** `pins.E0_CAP_USD = 40.0`, enforced as before. Every request is admitted before it is sent, at its hard maximum, against the cap and its category; unknown billing stays reserved; a settlement above its reservation halts the whole run.
- **Allocations:** in proportion to the dry run's expected spend, with headroom.

| Category | Owner's proposal $ | Pinned $ | Expected $ | Worst case $ (every request retried twice) |
|---|---|---|---|---|
| embeddings | 1.00 | **0.50** | 0.04 | 0.12 |
| drafting/context | 1.50 | 1.50 | 0.51 | 1.52 |
| labels/audits | 24.00 | 24.00 | 23.62 | 70.87 |
| answers/verification | 13.50 | **14.00** | 13.67 | 41.02 |
| **total** | 40.00 | **40.00** | **37.84** | 113.53 |

- **Adjustment:** answers/verification expects $13.67, more than the proposed $13.50. I moved $0.50 from embeddings (expected $0.04, worst case $0.12) to answers, within the $40.
- **Headroom is thin:** labels has $0.38 left and answers $0.33.
- **Worst case:** it assumes every request is retried twice, which no category's allocation covers. Admission stops a category at its allocation and the run at $40, so a run that met it would end incomplete rather than overspend. The Opus calls' hard reservations ($0.33+ each) are reserved and released one at a time.

### The OpenRouter Haiku pin (verified)

- **Price:** `system_verifier` is `anthropic/claude-haiku-5.5` at $0.10/M input and $0.50/M output, source https://openrouter.ai/anthropic/claude-haiku-5.5/pricing, `checked_on` 2026-10-22.
- **Long prompts:** the page shows no prompt-length tier. E0 still admits at Anthropic's >100k rate ($0.50/$2.50) whenever the input bound passes 100k (tested).
- **No unverified pin remains.**

### Keys

The paid run now loads no copy settings or dotenv (`open_copy(..., load_environment=False)` in `live.rebuild_frozen`). Keys come only from the shell or `--env-file`. This supersedes the "Commands for the paid run" section of `docs/reviews/experiments-e0-contextual-embeddings.md`.

### Dry run (env -i, no keys)

The dry run ran on the existing copies:

- `network_calls: 0` and copies unchanged by sha256 checksum.
- Artifacts refreshed: run `e0_dec5776aa73cdd5a`.
- **$37.84 expected against $40, which fits; every allocation fits.**
- Codex requests: 0 planned (allowance 0). Unverified prices: none. All four system-arm LLM rows are priced `verified`.

### Paid-run preflight

The paid CLI's checks were run on that plan under `env -i`, with no network:

- `require_paid_authorization`: authorized, the plan fits, no unverified price. **Passes.**
- `require_no_codex_roles`: **passes.**
- `require_codex_lockdown`: **active**, 58 lockdown overrides checked.

The only thing missing is the keys, which are absent in the dry run (`ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `PERPLEXITY_API_KEY`, `VOYAGE_API_KEY`). Without them, the model canaries fail with `auth` before any bulk work, and each copy writes its failure report. A test checks the same preflight on a fresh vault.

### The paid-run command (for the orchestrator to execute; not run here)

Run it from the worktree, or the merged tree, with the app's normal environment. The keys must be in the env file named here; nothing else is loaded.

```bash
cd /home/saturn/Documents/thinking/learnanything-e0
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file <PATH/TO/KEYS.env> \
  --anthropic-key-env ANTHROPIC_API_KEY \
  --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY \
  --voyage-key-env VOYAGE_API_KEY \
  --run-dir fixtures-local/contextual-embeddings/runs \
  --reader-latency-budget-s <SECONDS> \
  --new-authorization 'owner raised cap to $40 on 2026-10-22' \
  --i-am-authorized-to-spend \
  --json
```

- **Quoting:** keep the single quotes. In bash or fish, double quotes would expand `$4` in `$40`.
- **Caps:** no CLI flag changes them. They are pinned in `pins.py` and enforced by the ledger: cap $40.00; allocations as in the table above; 6,000 metered requests; Codex allowance 0; wall time 6 h; 2 transient retries; no auth or contract retries.
- **Ledger:** the run's canonical ledger is `fixtures-local/contextual-embeddings/ledger/e0_dec5776aa73cdd5a.ledger`. The plan id is recomputed from the copies and pins at run time and must equal the dry run's.
- **Reader latency budget:** `--reader-latency-budget-s` is optional. Without it, S2 and S4 fail closed.
- **Order of work:** the run first does the Codex lockdown and no-Codex checks, then the model canaries (Haiku, Sonnet, Opus), then the embedding canaries (Qwen first, before its backfill), then the bulk work.
- **Report:** results land in `fixtures-local/contextual-embeddings/runs/e0_dec5776aa73cdd5a/<copy>/results.json` and `report.md`. The aggregate is rendered with `learnloop experiments e0 report --results <that results.json> --out docs/reviews/experiments-e0-report-<copy>.md`.

### Gate (this step, on `ab9da7b65`)

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **30 kept, 0 broken**.
- `pytest -n auto` with `TMPDIR=fixtures-local/tmp`, on the same 30 files plus the new preflight test: **512 passed, 1 skipped**. The skip needs the `openai_codex` SDK.
- Test changes:
  - the ledger-mechanics tests in `tests/test_e0_budget.py` are now checked against a fixed $25 envelope with a $2 embeddings category, independent of the pins;
  - the cap assertions now expect $40;
  - the round-5 OpenRouter assertions now expect a verified price.

## Two env files and a preflight-only mode (owner, 2026-10-22)

The keys live in two files that no agent reads:

- the owner's `/home/saturn/.config/learnloop/settings.env` (the Anthropic API key);
- the repo-root `/home/saturn/Documents/thinking/learnanything/settings.env` (OpenRouter).

The Perplexity and Voyage keys may be in either file. The code loads them only through `--env-file`.

- **`--env-file` is repeatable.**
  - `credentials.load_env_files` loads only the named variables (`ANTHROPIC_API_KEY` or the `--anthropic-key-env` name, and the OpenRouter, Perplexity and Voyage names), in order, and never overrides a value the shell already set.
  - A later file never silently overrides an earlier one. A variable set to different values in two files, or twice in one file, is refused, and nothing is loaded. The error names the variable only, never a value, prefix, length or hash. The same value in both files is accepted.
- **`--preflight-only`** loads the env files, then builds the frozen plan exactly as the dry run does, with the socket guard counting every attempted connection. It reports:
  - each required key variable, as `present` or `absent` only;
  - whether every metered pin's price is verified;
  - planned Codex requests (0) against the paid ledger's Codex allowance (0), and that no role is on Codex;
  - whether the Codex tool lockdown is present;
  - the $40 cap and each allocation with its expected and worst-case spend, and whether the plan fits them;
  - the plan id and its canonical ledger path (nothing is created);
  - each copy's sha256 tree checksum before and after (equal);
  - the network call count (0).
- **Output and exit code.** It prints no value. It exits 0 only when every check passes and every key is present (`ready`); otherwise it exits 1 with the same report.
- **Tests** cover two files loading by name, the conflict refusal naming the variable only (two files, and twice in one file), and the CLI preflight with fake values: no value appears in the output, every key is `present`, every check passes, 0 network calls, no ledger created. They also cover an absent key reported by name, with exit 1.

### Step 1: the preflight (zero network, prints no value)

Run it from the worktree, or the merged tree, with the app's normal environment:

```bash
cd /home/saturn/Documents/thinking/learnanything-e0
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file /home/saturn/.config/learnloop/settings.env \
  --env-file /home/saturn/Documents/thinking/learnanything/settings.env \
  --anthropic-key-env ANTHROPIC_API_KEY \
  --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY \
  --voyage-key-env VOYAGE_API_KEY \
  --preflight-only
```

Expected: `"ready": true`, every key `present`, every check `true`, `network_calls: 0`, and the before and after checksums equal. The plan id should be `e0_dec5776aa73cdd5a`, the committed dry run's (the copies and pins are unchanged).

### Step 2: the paid run (the orchestrator executes it; never run by an agent)

```bash
cd /home/saturn/Documents/thinking/learnanything-e0
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file /home/saturn/.config/learnloop/settings.env \
  --env-file /home/saturn/Documents/thinking/learnanything/settings.env \
  --anthropic-key-env ANTHROPIC_API_KEY \
  --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY \
  --voyage-key-env VOYAGE_API_KEY \
  --run-dir fixtures-local/contextual-embeddings/runs \
  --reader-latency-budget-s <SECONDS> \
  --new-authorization 'owner raised cap to $40 on 2026-10-22' \
  --i-am-authorized-to-spend \
  --json
```

- **Quoting:** keep the single quotes; double quotes would expand `$4`.
- **Caps:** fixed in `pins.py` and enforced by the ledger, with no flag: $40.00 total; embeddings 0.50, drafting/context 1.50, labels/audits 24.00, answers/verification 14.00; Codex allowance 0; 6,000 metered requests; 6 h wall time.
- **Ledger:** `fixtures-local/contextual-embeddings/ledger/e0_dec5776aa73cdd5a.ledger`.
- **Reader latency budget:** optional; without it, S2 and S4 fail closed.
- This command supersedes the single-`--env-file` command in the section above.

## Pre-paid verify of `6b203def3`: the small round (2026-10-23)

The verify found no High and judged the harness safe to run. Before the paid run, M1, M2, L1, L4 and L7 are fixed here; L2, L3, L5 and L6 are recorded as open. **No paid, live or network call was made ($0.00).** Neither settings.env was read.

### Fixed

- **M1: no settings or dotenv mid-run.**
  - The problem: `system_arms.open_service` called `load_vault(root)` with the default `load_environment=True`. That loaded the service copy's `.env` and the machine's `~/.config/learnloop/settings.env` into the process, along with the global AI defaults, so a `LEARNLOOP_AI_PROVIDER` there could re-route the copies' source routes mid-run.
  - The fix: every E0 vault load now passes `load_environment=False` (`open_service`, `open_copy`, `rebuild_frozen`, `ExperimentRecords`).
  - The test puts `LEARNLOOP_AI_PROVIDER` in the test's own config dir `settings.env`, and a marker in each copy's `.env`. Neither reaches the process, and the copy's active provider is unchanged.
- **M2: headroom above one Opus reservation.** The categories were re-allocated within the unchanged $40 cap.

| Category | Was $ | Now $ | Expected $ | Headroom $ |
|---|---|---|---|---|
| embeddings | 0.50 | 0.25 | 0.04 | 0.21 |
| drafting/context | 1.50 | 0.85 | 0.51 | 0.34 |
| labels/audits | 24.00 | 24.60 | 23.62 | 0.98 |
| answers/verification | 14.00 | 14.30 | 13.67 | 0.63 |

  - Each category covers its expected spend. Labels and answers now have more headroom than one Opus reservation's output side ($0.33; tested against the committed plan).
  - **The authorization is the same, regenerated the same way.** The ledger binds an authorization to the plan id, which hashes the pins, allocations included. So the plan id changes, from `e0_dec5776aa73cdd5a` to `e0_a47534fecc49ded5`, and the run opens a new canonical ledger, `fixtures-local/contextual-embeddings/ledger/e0_a47534fecc49ded5.ledger`.
  - No ledger existed yet (the preflight creates none). The paid-run command keeps `--new-authorization 'owner raised cap to $40 on 2026-10-22'`, which is recorded in the new ledger.
- **L1: redirects are refused.** `adapters.UrllibTransport` now uses an opener with `NoRedirect` instead of urllib's redirect handler. A 3xx would otherwise replay `x-api-key` or `Authorization` to another host. The 3xx comes back as its status: a contract failure, never retried, both for the Messages API client and for the hosted embedding adapters. The tests use an opener that answers 302: one request, a contract failure, no retry.
- **L4: no gate, no send.** `AnthropicMessagesClient.send` refuses to send without an active request gate (`E0BudgetExceeded`, fail closed). Tested: nothing is posted.
- **L7: the run directory stays local.** `run_live` refuses a `--run-dir` outside fixtures-local before anything else. Tested: no run directory or ledger is created.

### Open (recorded, not fixed)

- **L2:** when a response reports both a provider cost and token counts, the provider's cost wins over the tokens priced at the pin. A provider cost below the token price lowers the committed amount.
- **L3:** a key already set in the shell wins over the env files, silently; the preflight reports it only as `present`.
- **L5:** the Qwen reservation (`EmbeddingAdapter._estimate`) prices the texts without the production client's instruct prefix for queries. That prefix is about 30 tokens per query: an under-reservation of a few cents' fractions at most.
- **L6:** the dry-run plan still names Codex in places. Its baseline section reports the frozen copies' own configured routes (`source_rerank`, `source_query_rewrite` and `tutor_qa` on `codex` / `codex_low`, type `codex_sdk`), not the service copies' OpenRouter re-routing. Older prose in this doc and in the stage doc mentions the 600 allowance. The plan's numbers are the current ones: 0 Codex requests, allowance 0.

### Dry run (env -i, no keys, inside a memory-capped scope)

The dry run ran on the existing copies:

- `network_calls: 0`, copies unchanged by sha256 checksum.
- Artifacts refreshed: run `e0_a47534fecc49ded5`.
- **$37.84 expected, $113.53 worst case (every request retried twice), against $40: it fits, and every allocation fits.** The per-category figures are in the M2 table above.
- Codex: 0 planned, allowance 0. No unverified price.

### The commands, with the new plan id

The preflight and paid-run commands in the section above are unchanged. Only the expected plan id changes: the preflight should now print `e0_a47534fecc49ded5`, and the paid run's ledger is `fixtures-local/contextual-embeddings/ledger/e0_a47534fecc49ded5.ledger`.

### Gate

Every pytest ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 4`, never `-n auto` (the owner's memory rule, 2026-10-23). The counts are below.

- **Gate results:**
  - `.venv/bin/lint-imports --no-cache` (under `env -i`): **30 kept, 0 broken**.
  - `pytest -n 4` on 31 files: **520 passed, 1 skipped**. The 31 files are the 30 of the previous step plus the new `tests/test_e0_review_round6.py`, with 6 tests. The skip needs the `openai_codex` SDK.
  - Fail-before on `6b203def3`'s `src`, `migrations` and `calibration_bundles` (`git archive`, `pytest -o pythonpath`): the 6 round-6 tests, **6 failed**. M1 failed with `LEARNLOOP_AI_PROVIDER` loaded into the process. L4 tried to send without a gate. L7 went past the run-dir check. L1 found no redirect-refusing opener. M2 found the old allocations.

## The Perplexity canary round (2026-10-23)

The first paid run (plan `e0_a47534fecc49ded5`) was stopped by the orchestrator after the canaries. It spent $0.0004. All three Perplexity canaries failed with `error_kind: "contract"` in about 70 ms, each with a Perplexity request id. Each one wrote a `failed` receipt from inside `_send`, so the failure was a non-2xx status, not a parse error. Everything else passed: Claude Haiku, Sonnet and Opus, Voyage `voyage-context-4` and `voyage-4-large`, the OpenRouter Qwen canaries, and the start of the Qwen service backfill.

### What the API reference says (read 2026-10-23, no other network request)

| Source | What it says |
|---|---|
| https://docs.perplexity.ai/api-reference/embeddings-post | **Endpoint:** `POST https://api.perplexity.ai/v1/embeddings`, Bearer auth.<br>**Request** (`EmbeddingsRequest`):<br>• `input`: a string, or an array of 1 to 512 non-empty strings. At most 32K tokens each and 120,000 in total.<br>• `model`: `pplx-embed-v1-0.6b` or `pplx-embed-v1-4b`.<br>• `dimensions`: optional, 128 to 2560 for 4b, default 2560.<br>• `encoding_format`: optional, enum `base64_int8` (the default) or `base64_binary`.<br>• **No `input_type` field.**<br>**200 response** (`EmbeddingsResponse`):<br>• `object` (`list`), `data[]` and `model`.<br>• Each `data[]` item has `object` (`embedding`), `index`, and `embedding`: a **base64 string**. For `base64_int8` it decodes to `dimensions` signed int8 values.<br>• `usage`: `prompt_tokens`, `total_tokens`, and `cost` = `{input_cost, total_cost, currency: "USD"}`.<br>**Errors:** the only documented one is **422** `HTTPValidationError` = `{"detail": [{"loc", "msg", "type"}]}`. |
| https://docs.perplexity.ai/api-reference/contextualized-embeddings-post | **Endpoint:** `POST https://api.perplexity.ai/v1/contextualizedembeddings`.<br>**Request:**<br>• `input`: an array of 1 to 512 documents. Each document is an array of at least one non-empty chunk string. At most 16,000 chunks in total, 32K tokens per document and 120,000 tokens in total.<br>• `model`: `pplx-embed-context-v1-0.6b` or `pplx-embed-context-v1-4b`.<br>• `dimensions` and `encoding_format`: as above, default `base64_int8`.<br>• **No `input_type` field.**<br>**200 response:**<br>• `data[]` has one entry per document, with `object`, `index` (the document) and `data[]`.<br>• Each inner `data[]` item is one chunk, with `object`, `index` (the chunk) and `embedding` (a base64 string).<br>• `usage` and the errors are as above. |
| https://docs.perplexity.ai/docs/embeddings/contextualized-embeddings | Queries go to the same contextualized endpoint and model, with each query wrapped as a one-element inner list, `[[query]]`. The example decodes with `np.frombuffer(base64.b64decode(b64), dtype=np.int8)` and ranks by cosine. |
| https://docs.perplexity.ai/docs/embeddings/standard-embeddings | The standard endpoint has no input type or prefix parameter: queries and documents go through the same call with the same settings. The int8 decoding is the same as above. |

### Field by field

| Field | Sent by the first paid run | Documented | Fixed |
|---|---|---|---|
| `encoding_format` | `"int8"` | `base64_int8` or `base64_binary` | **`"base64_int8"`**. `"int8"` is outside the enum: a 422 on both endpoints. This is the cause. |
| `input_type` | `"document"` or `"query"` | not in either schema | **dropped**. The docs do not say whether an unknown field is rejected; the adapter now sends only documented fields. |
| `input` (contextualized) | `[[chunk, ...], ...]`, queries `[[query]]` | the same | unchanged |
| `input` (standard) | `[text, ...]` | a string or an array of strings | unchanged |
| `model` | `pplx-embed-context-v1-4b` and `pplx-embed-v1-4b` | in the enum | unchanged |
| `dimensions` | 2560 | 128 to 2560 for 4b, default 2560 | unchanged (the pin) |
| Response nesting | `data[].index`, `data[].data[].index` and `.embedding` | the same | unchanged; rows are still matched by `index` |
| `embedding` | parsed as an int8 list or a base64 string | a base64 string (`base64_int8`) | already decoded as signed int8 and length-checked against `dimensions`; now tested on the documented shape |
| `usage.cost` | an object, so ignored (not a number) | `{input_cost, total_cost, currency: "USD"}` | **`total_cost` in USD is the explicit bill** (`EmbeddingAdapter._billed`). Before, the request was settled on the reported tokens at the pin price. |

The query method is the documented one: `[[query]]` on the contextualized endpoint, and the same call on the standard endpoint. The pins' `query_method` text already said this, so no pin changed (see Resume below).

### Safe contract reasons

- A failed attempt's receipt now has two more fields, `http_status` and `contract_reason`.
  - On a non-2xx, `contract_reason` is `HTTP <status>`, followed by the error body's allowlisted codes (`adapters.safe_error_codes`). For the first paid run's bodies, that is `HTTP 422: body.input_type:extra_forbidden, body.encoding_format:enum`.
- How a code is built:
  - `UrllibTransport` reads the HTTP error body, at most 64 KB, and keeps only the codes; the body is dropped.
  - A code is `<loc>:<type>`. Each part of the location is an integer or a name from a fixed field list; anything else becomes `?`.
  - The type comes from a fixed vocabulary (the Pydantic/FastAPI types, plus the OpenAI-style `error.type`/`error.code` values); anything else becomes `other`.
  - `msg`, `message` and a string `detail` are never read.
  - At most 8 codes are kept.
  - Tested: a `msg`, `loc` part, `type` or `error.code` carrying request text never reaches the codes or the receipt.
- **A 2xx that does not parse is now on the receipt.** The parse and decode run inside `_send`'s receipt path (`parse=`). Before, the receipt said `ok` and the error was raised afterwards.
  - The request was billed, so its ledger entry is settled on the reported cost.
  - The receipt is `status: "failed"`, with `error_kind`, `http_status: 200` and a reason built from field paths, JSON types and counts only. Examples: `missing field data[0].data[0].embedding`, `unexpected type at data (object, expected array)`, `output has 1024 dimensions at data[0].data[1].embedding, pinned 2560`, `the provider answered with another model than the pinned one (at model)`.
- `run_contracts` copies `http_status` and `reason` into the run result's `contracts[arm]`.

### Tests (`tests/test_e0_review_round7.py`, 21 tests)

- **The documented shapes.**
  - `tests/e0_fakes.perplexity_documented` implements both published request schemas. It enforces them with the documented 422 `detail` (reduced by `safe_error_codes`, as the real transport does) and answers with the documented 200 shapes: `object`, nested `data` with `index`, base64 int8 `embedding`, and `usage.cost`.
  - `FakeEmbeddingTransport` now routes every Perplexity URL through it, so every fake paid run in the suite exercises the documented contract.
  - Literal documented responses, with rows out of order, decode by `index`. `usage.cost.total_cost` settles the ledger.
- **The three canaries that failed live** (`R4_grouped`, `R4_singleton`, `R4_independent`) pass against the documented contract.
  - The first paid run's bodies get the documented 422 with exactly `body.input_type:extra_forbidden` and `body.encoding_format:enum`.
  - The receipt records `http_status: 422` and that reason.
- **Resume checks** for receipts in `test_e0_paid_fakes` and `test_e0_review_round1`. A Perplexity body no longer has `input_type`, so the transport-level "no document re-sent" filters cannot see it. Both tests now also check that the resumed run's receipts are canaries only, for every adapter.
- **Fail-before** on `e5ea349ab`'s `src` (`git archive`, `pytest -o pythonpath`): **18 failed, 3 passed**.
  - The three canary tests fail on the 422 path of the documented fake, the live failure. They stop with an AttributeError: the old adapters lack `safe_error_codes`.
  - The 3 that pass are the resume and fingerprint checks, which pin unchanged behaviour.

### Resume (no live call made by the agent)

- **The plan id is unchanged: `e0_a47534fecc49ded5`.**
  - The fix is adapter code only. No pin, allocation, harness version or number changed, so `pins_fingerprint()` is still `883d5380…63b6`.
  - The `env -i` dry run on the same copies printed run `e0_a47534fecc49ded5`. Its plan JSON is identical to the committed artifact apart from the timestamp, and the copies were unchanged by sha256.
  - A test pins the fingerprint to the artifact.
- **The rerun reuses the same ledger.**
  - `authorized_ledger` reopens `fixtures-local/contextual-embeddings/ledger/e0_a47534fecc49ded5.ledger` for the same plan id, whether or not `--new-authorization` is passed.
  - The authorization recorded on 2026-10-23 is kept. A second reason is ignored, never rewritten.
  - Everything already committed counts against the $40: $0.00039517 settled, $0.00001586 for the three failed Perplexity canaries (no bill reported, so kept at their reservation), and $0.000073 for the open reservation. That is about $0.00048 in all.
  - The plan id is unchanged. If it were not, the run would open a new ledger with a fresh $40. That would need `--new-authorization`, and the run refuses without it.
- **The interrupted request** is the one entry still `reserved`: `R1_service_backfill`, `qwen/qwen3-embedding-8b`, 7,300 estimated tokens, $0.000073, no request key.
  - Nothing settles or releases it. It counts in full against the cap forever: unknown billing, the conservative reading.
  - The Qwen service copy's state is `ready` with the same identity, so it is reopened, not rebuilt.
  - The production backfill checkpoints each successful batch and plans only missing content hashes. So the 7 settled batches are not re-sent.
  - The interrupted batch's vectors were never checkpointed: its reservation was never settled, so no response was processed. **That one batch is sent again, once, as a new admitted request.** It cannot be skipped: the vectors are missing. It is never sent twice by this rerun.
  - If the first attempt did reach OpenRouter, the cost of that batch is paid twice, about $0.00002 each. The ledger counts it conservatively: the old full reservation plus the new request's.
  - LLM role calls carry a request key. An unexplained earlier entry for the same key blocks them, so they are never re-sent.

### The rerun command (for the orchestrator; not run here)

First the preflight, which should print plan `e0_a47534fecc49ded5`:

```
cd /home/saturn/Documents/thinking/learnanything-e0
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file /home/saturn/.config/learnloop/settings.env \
  --env-file /home/saturn/Documents/thinking/learnanything/settings.env \
  --anthropic-key-env ANTHROPIC_API_KEY --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY --voyage-key-env VOYAGE_API_KEY \
  --preflight-only
```

Then the run. Drop `--new-authorization`:

```
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file /home/saturn/.config/learnloop/settings.env \
  --env-file /home/saturn/Documents/thinking/learnanything/settings.env \
  --anthropic-key-env ANTHROPIC_API_KEY --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY --voyage-key-env VOYAGE_API_KEY \
  --run-dir fixtures-local/contextual-embeddings/runs \
  --reader-latency-budget-s <SECONDS> \
  --i-am-authorized-to-spend --json
```

Why drop it:
- Without it, the run can only reopen the existing ledger, which already records the owner's reason.
- If the plan id were somehow different, the run refuses ("another plan's E0 authorization ledger exists") instead of silently opening a fresh $40 budget.
- Keeping it would be harmless for the same plan id (it is ignored), but it would hide that case.

On the rerun:
- The canaries go out again: the Anthropic and Voyage canaries compare as `stable` against their cached first outputs, and the Perplexity canaries run for the first time.
- If a Perplexity canary still fails, its receipt (`runs/e0_a47534fecc49ded5/linear_algebra-20261021/receipts.jsonl`) and the result's `contracts` now carry `http_status` and the allowlisted reason.

### Gate

Every pytest ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 4`.

- `.venv/bin/lint-imports --no-cache` (under `env -i`): **30 kept, 0 broken**.
- `pytest -n 4` on 32 files (the 31 of the previous step plus `tests/test_e0_review_round7.py`): **541 passed, 1 skipped**. The skip needs the `openai_codex` SDK.
- Dry run under `env -i`, no keys, `network_calls: 0`: plan `e0_a47534fecc49ded5`, $37.84 of $40, unchanged. The artifacts were not refreshed: the plan is identical.

The only network requests of this round were the four documentation reads listed above, plus `docs.perplexity.ai/llms.txt` to find them. One guessed URL (`/api-reference/contextualizedembeddings-post`) returned 404.

## Paid run 2: the incomplete rerun's three failures (2026-10-23)

The rerun of plan `e0_a47534fecc49ded5` used the same ledger and exited 0 with status INCOMPLETE.
- It committed $1.38 of $40: labels 0.92, drafting 0.29, answers 0.14, embeddings 0.03.
- It made 640 requests, with 0 refusals, 0 overages and 0 Codex.
- Every embedding arm ran, Perplexity included.

Both vaults stopped their labels on `provider failure (invalid_output)`, so no answers were made. R3 failed `truncated` in both vaults. In probability, one Qwen backfill batch was rejected.

### How each was diagnosed (no body, key or model text read or printed)

The sources were:
- the ledger;
- the `.failed.json` markers in `runs/.../llm/`, which map a failed checkpoint key to its ledger entries;
- the safe columns of `model_call_receipts`;
- a validation run over the stored outputs that printed only JSON types, counts, allowlisted field names and pydantic `loc:type` codes.

| Failure | Role / model | Finding |
|---|---|---|
| linear_algebra labels | `label_a`, Claude Haiku 5.5 | **Cause:** valid JSON (1,582 chars) with one extra top-level key, a misspelled duplicate of `answerable` (`aswerable`). `LabelPass` (`extra="forbid"`) rejected it as `?:extra_forbidden`. **Usage:** output 1,994 of 8,192 tokens, `end_turn`, so the answer was not truncated. |
| probability labels | `label_b`, Claude Sonnet 5.5 | **Cause:** 202 chars holding two different valid `SufficiencyPass` objects with 83 chars of prose between them (the model revised its answer). The old parse sliced from the first `{` to the last `}`: `json Extra data at char 70`. **Usage:** 95 output tokens, `end_turn`. |
| R3, both vaults | `context`, Claude Haiku 5.5 | **Cause:** a 40-ref window stopped at `max_tokens` 16,384 (`stop_reason: max_tokens`). **Evidence:** the visible text was about 18 KB, about 5,000 tokens, so most of the output tokens were thinking. Visible chars per output token were 1.1-1.6 on context calls, about 0.8 on Haiku labels and about 1.9 on Sonnet labels. Adaptive thinking is the documented default for Haiku, Sonnet and Opus 5.5, and it counts in `output_tokens` and against `max_tokens` (Claude API reference, Thinking & Effort). The successful windows had up to 43 refs at 11,096 output tokens, so how much a window thinks varies. |
| probability Qwen backfill | the production `openai_embedding` client | **Cause:** a paid 200 (the 6th receipt reported 1,654 input tokens against 2,600-3,300 for the full batches before it) whose vectors failed the production contract check. The client raised `ValueError`; the backfill reports `provider_failed` and does not save or retry the batch. **Gap:** E0's report kept only `status/records/embedded/reason`, so the error class and the exact check were not visible. **Ruled out**, offline on a scratch copy of the service copy: an oversized or empty input. The 177 pending records are at most 3,398 UTF-8 bytes; the client's limit is 32,768. |

### Fixes

1. **Labels (`anthropic_api.parse_answer`, one repair).**
   - The parse decodes every top-level JSON object in the text blocks of the documented response (`content[]` of type `text`; `thinking` blocks are skipped).
   - Exactly one object that validates is the answer. Prose or a fence around it is tolerated, and duplicates that are equal are accepted.
   - Otherwise the failure is `invalid_output` with a safe reason. Examples: `validation ?:extra_forbidden`, `2 different JSON objects validate`, `json <decoder message> at char N`, `no JSON object`.
   - An `invalid_output` gets **one admitted repair**: the same system prompt and `max_tokens`, with the model's own answer and the safe reason. This is the production providers' JSON-repair pattern. It is a separate POST, admitted by the same request gate, so it is reserved at its hard maximum before it is sent.
   - A `max_tokens` or `refusal` stop is never repaired.
   - The spec's "zero retries for contract errors" covers transport and contract failures. A repair is a regeneration of an unusable answer, and every paid attempt counts.
   - The bounds are unchanged (label A and B 8,192; adjudicator 16,384). Those calls used at most about 2,000 output tokens, and changing a pin would change the plan id and re-key every checkpoint.
2. **R3 (`retrieval.generate_contexts`).**
   - A window request that stops at `max_tokens` is split into halves of its refs, down to one ref.
   - Each half shows the whole window excerpt and lists `only_refs`.
   - The whole-window prompt is unchanged byte for byte, so every window that succeeded reuses its checkpoint.
   - A single ref that still fails (`truncated`, `invalid_output` or `refusal`) leaves that unit without a context, counted in `context_missing` and `context_requests_failed`. It no longer blocks R3 for every window.
   - **No re-send at the same bound:** `LiveRoleCaller` refuses to send a request again that is known to have truncated at that `max_tokens`. That is known from the new failure record, or, for the first paid run's markers, from a ledger entry whose `output_tokens` reached the bound. The split then takes over.
   - The `context` pin's 16,384 is unchanged, for the same plan-id reason.
   - The admission maths stay conservative: `max_tokens` already reserves the whole output side, thinking included.
3. **One item's unusable answer no longer stops the step.**
   - In `label_all`, the audits and the answer schedule, an `E0ProviderFailure` classified `invalid_output`, `refusal` or `truncated` fails that question or pair only. It is counted (`labels_failed`, `labels_<kind>`, `audit_<kind>`, `answer_<kind>`, `answers_missing`) and the step goes on.
   - Auth, budget, transient-past-retries and every other failure still stop the step.
4. **Qwen backfill (`system_arms.backfill_service_copy`).**
   - The `ProtectedTextGuard` wrapper records the production client's `ValueError` by its fixed message. The messages are allowlisted (`EMBEDDING_CONTRACT_ERRORS`), anything else is `other ValueError`, and a test pins every message to the production source.
   - The guard also names the backfill's own wrong-count/width check.
   - The report keeps `error_type`, `provider_error`, `invalid_reasons`, `remaining` and `pass`.
   - A pass that ends `provider_failed` gets **one more pass** in the same run. The production backfill re-plans only the missing vectors, so only the unsaved batch is sent again, and it is admitted.
5. **Diagnosable failures.**
   - `E0ProviderFailure` now carries a safe `reason` and `details`: `stop_reason` (allowlisted), `output_tokens`, `input_tokens`, `max_tokens`, the content block types, and `repaired`.
   - Its message is `provider failure (<kind>: <reason>)`, and that message reaches `results.json`'s failures.
   - Each failed role call's `.failed.json` is now `{"reservations": [...], "failure": {role, classification, reason, status_code, request_id, details}}`. The first run's bare list is still read.

### Tests (`tests/test_e0_review_round8.py`, 16, documented Messages shapes)

The fake responses carry a `thinking` block with empty text, then the `text` block, a `stop_reason`, and `usage.output_tokens` that includes thinking.

The tests cover:
- the misspelled-key answer, named safely and repaired once (two admitted entries, same `max_tokens` and system prompt);
- the two-object answer;
- a single object in prose or a fence, with no repair;
- a failed repair, with both reasons and no model text;
- `max_tokens` and `refusal`, never repaired, with their details;
- the failure record on disk;
- the known-truncated request not re-sent, including from the first run's marker format via the ledger;
- R3 splitting until every unit has a context, with the window's original prompt unchanged;
- a single ref that still truncates, counted, not a stop;
- labels going on past one question's failure, while auth still stops them;
- the backfill reporting its reason and finishing coverage on the extra pass;
- the allowlisted messages and an unknown message reduced to `other ValueError`;
- the plan id unchanged.

### Resume (no live call made by the agent)

- **Same plan, same ledger.**
  - No pin changed: `pins_fingerprint()` is still `883d5380…63b6`.
  - The `env -i` dry run on the same copies printed run `e0_a47534fecc49ded5`, with a plan JSON identical to the committed artifact apart from the timestamp.
  - The rerun reopens `fixtures-local/contextual-embeddings/ledger/e0_a47534fecc49ded5.ledger`, and its $1.38 counts against the $40.
- **What is reused:**
  - every settled role call by its checkpoint: the 121 label passes, the writer drafts, and the 32 context windows that finished;
  - the judgments already recorded (`judgment_ledger` appends are idempotent);
  - the receipts;
  - every stored embedding vector and query vector;
  - the cached first canary outputs (the canaries go out again and compare `stable`);
  - both service copies (state `ready`, same identity: reopened, not rebuilt);
  - the Qwen vectors already saved.
- **What is sent again, once:**
  - the two failed label calls (label A in linear_algebra, label B in probability), plus at most one repair each;
  - the probability backfill's missing records: 177 of 337, the rejected batch and the batches after it (about $0.0002);
  - the halves of the truncated linear_algebra context window. The window's own request is not re-sent: its ledger entry reports 16,384 output tokens at a 16,384 bound;
  - everything never reached: 67 questions' labels, the audits, and every answer.
- **Never re-sent:** a request with an admitted but unexplained entry (no checkpoint, no failure record) is still blocked (fix round 4, Medium 11).

### Expected additional spend

The dry run prices the whole plan; it has no remaining-work mode. Two estimates:

- **Plan-based upper estimate: about $32.**
  - Labels and audits: 67 of 86 questions remain, so about $18.4 of the plan's $23.62.
  - Answers and verification: none made yet, so the plan's $13.67.
  - Drafting: under $0.10 (the split R3 halves).
  - Embeddings: under $0.01.
  - With the $1.38 committed, that totals about $33.5 of $40. It fits.
- **Observed-rate estimate: about $8-12.**
  - The plan's per-request estimates are far above what this run measured. Label passes cost about $0.048 per question (121 calls, $0.91), so 67 questions are about $3.2.
  - The Opus audits come to about $0.07 each.
  - The Haiku tutor and judges come to about $0.006 per pair.
- **Not in the plan:** the repair requests. Each is admitted at its hard maximum, so the cap still holds.

### The rerun command (for the orchestrator; not run here). No `--new-authorization`.

```
cd /home/saturn/Documents/thinking/learnanything-e0
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 \
  --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 \
  --env-file /home/saturn/.config/learnloop/settings.env \
  --env-file /home/saturn/Documents/thinking/learnanything/settings.env \
  --anthropic-key-env ANTHROPIC_API_KEY --openrouter-key-env OPENROUTER_API_KEY \
  --perplexity-key-env PERPLEXITY_API_KEY --voyage-key-env VOYAGE_API_KEY \
  --run-dir fixtures-local/contextual-embeddings/runs \
  --reader-latency-budget-s <SECONDS> \
  --i-am-authorized-to-spend --json
```

### Gate

Every pytest ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 4`.

- **pytest:** 33 files (the 32 of the previous round plus `tests/test_e0_review_round8.py`): **557 passed, 1 skipped**.
  - One test expectation changed: `test_the_label_passes_never_reach_a_codex_turn`. Its fake answer does not validate, so each pass now also makes its one repair POST. The routing it checks (Haiku, then Sonnet, never Codex) is unchanged.
- **lint-imports** (`env -i`): **30 kept, 0 broken**.
- **Fail-before** on `1bb7b87bd`'s `src`: `tests/test_e0_review_round8.py` does not import (`parse_answer` does not exist there).
- **Dry run:** unchanged, so the artifacts were not refreshed.

## Relabel round (owner: Sonnet both + rubric), 2026-10-23

Paid run 3 (plan `e0_a47534fecc49ded5`) completed with **$14.149 committed of $40** and 0 refusals. S1 stopped verdicts on both copies:

- linear_algebra: κ 0.444 (weighted 0.574), n=3,012.
- probability: κ 0.490 (weighted 0.629), n=2,256. It was also INCOMPLETE: the Qwen backfill of the service copy was refused, so R1_pool_verify, R1_service_pool and R1_service_rrf were blocked.

The owner decided **"Sonnet both + rubric"**. **No paid, live or network call was made in this round ($0.00).** No settings or credential file was read. The run-3 artefacts under `fixtures-local/` were read (they are copies), but none of their text is committed or quoted here.

### Diagnosis

**Labels.** This uses the development slice only, from run 3's `judgment_ledger` (pass 1 = label A, Haiku 5.5; pass 2 = label B, Sonnet 5.5). The logged questions were counted and set aside. Arm outcomes were not opened. Rows are label A and columns are label B, in the order unrelated, background, helpful, required:

| Copy (development slice) | n | Confusion |
|---|---|---|
| probability (36 questions) | 2,068 | `[[983, 77, 4, 0], [350, 303, 67, 6], [2, 40, 101, 45], [0, 4, 18, 68]]` |
| linear_algebra (36 questions) | 2,334 | `[[851, 128, 12, 2], [414, 449, 133, 12], [9, 62, 108, 62], [0, 4, 13, 75]]` |

The largest cell by far is **A background / B unrelated** (350 and 414). The examples read for the revision were a seeded sample of dev pairs, read locally and not recorded. In them, label A called "background" any passage that shares the chapter, section or broad subject with the question. Examples of such passages: another counting problem, another theorem about subspaces, an exercise list, an R-vector example, a notation fragment. Label B called these "unrelated" unless they addressed the question's specific concept. The next boundaries are helpful / required (45 and 62) and background / helpful (67 and 133). Both of these reduce to "is this content the answer needs, or could use?".

**The probability backfill (`ProtectedTextRefused`, 177 of 337 records left).** This was counted offline on the run's own frozen and service copies. No text was printed.

- Redaction was correct. The service copy has 0 non-blank withheld blocks, and none of the 337 + 15 planned records is a withheld block.
- The guard's probes were the first 48 normalized characters of each withheld block. That gave 105 probes, 97 of them unique. One of them is a withheld **assessment-lane SectionHeader of 19 normalized characters**. Seven **permitted** Text blocks of the same extraction contain its whole text.
- The guard therefore refused permitted text. The first such record is index 177, so batch 6 (records 160–191) was refused before sending. The production backfill stops at a failed batch, which left records 160–336 (177) unembedded. The extra pass met the same refusal.
- **Correction to the paid-run-2 diagnosis.** That diagnosis blamed a "contract check" on a paid 200 of 1,654 input tokens. A refusal raises before anything is sent, so it leaves no receipt. The 1,654-token receipt is most likely the 15-record fourth extraction, which completed. Run 2's report did not keep the error class, so its true cause was most likely this same refusal.

### Rubric v2 (frozen before any relabel spend)

`bank.RELEVANCE_RUBRIC`, SHA-256 `b48ddc203b82495e14e5359f292ca87141520cbb381a626e765b6ce2830a8b33`.

- The hash is pinned as `pins.LABEL_RUBRIC_SHA256` and is part of the pins fingerprint, so of the plan id.
- `bank.check_rubric_frozen()` refuses to load an edited text.
- Prompt versions: `e0-label-v2` and `e0-adjudicate-v2`. The adjudicator's instructions carry the same rubric.
- The spec's new §12 amendment log records it.

Before (v1, in both the one-call and relevance-only prompts):

> relevance: required (states the answer or a condition the answer needs), helpful (useful support that is not required), background (on topic, not needed), unrelated. … Background never completes a set.

After (v2; the sets rule follows it in `LABEL_INSTRUCTIONS`):

> Judge each candidate passage against the question's specific subject: the particular concept, result, example, object or step the question asks about (with a selected passage, what the question asks about that passage), not the broad topic, chapter or section it comes from. relevance: required: the passage states the answer, or a definition, fact, step or condition without which the answer would be wrong or incomplete; every member of a sufficient evidence set is required, and a passage that belongs to no sufficient set is at most helpful. helpful: the passage is about the question's specific subject and gives content an answer could use or cite (an example, a restatement, an intuition, a consequence), but a complete answer does not need it. background: the passage is about the question's specific subject, or names it or describes its immediate setting, but gives nothing an answer would use or cite. unrelated: everything else. Sharing the chapter, the section, the broad subject or some vocabulary is not enough for background: another problem, example, exercise, theorem, definition or notation from the same area that does not address the question's specific subject is unrelated, and so is a fragment (a heading, a label, an isolated formula) that says nothing about it. When no passage addresses the specific subject, most or all are unrelated. Between two adjacent labels, give the lower one unless the passage meets the whole definition of the higher one.

The sets rule now reads "Background and unrelated passages never belong to a set". The joint sufficiency review adds "A passage belongs to a set only if the answer would be wrong or incomplete without it".

| Rubric change | Development-slice disagreement it targets |
|---|---|
| Judge against the question's specific subject, not the area | A background / B unrelated (350 and 414) |
| "Sharing the chapter … is not enough for background", with the kinds of same-area passage named | The same cell's examples |
| "Required" means membership of a sufficient set; outside every set, at most helpful | Helpful / required (45 and 62) |
| Helpful gives content an answer could use; background gives nothing an answer would use | Background / helpful (67 and 133) |
| A tie goes to the lower label | Every adjacent boundary |

**Label A is Claude Sonnet 5.5** (`claude-sonnet-5-5`), the same model as label B, and remains an independent pass:

- It is its own request.
- It is blinded to arm: no arm, rank or score is in the prompt.
- It has its own candidate order and refs (`stable_order` salted by pass) and its own pass number.
- It never sees the other pass.

`test_the_two_passes_stay_independent_requests_in_different_orders` pins this. The Opus 5.5 adjudication rule is unchanged.

### The backfill fix (fails closed)

1. **The guard probes only text distinctive to withheld blocks** (`system_arms.probe_plan`).
   - It probes every window of 48 characters of a withheld block's normalized text, 24 apart, plus the last window. A block shorter than 48 characters is one probe, whole. A block shorter than 16 characters is not probed, as before.
   - A window is dropped when some permitted block contains it. That text is sent anyway as the permitted block, by policy.
   - This is stronger for real protected text than the old guard. A leaked tail is refused as well as a leaked head; the old guard probed the head only.
   - A withheld block lying wholly inside permitted text has no probe and is counted (`withheld_inside_permitted`).
   - Probability now has **906 probes**: 104 blocks probed, 1 inside permitted text, 21 too short. The 352 planned records give **0 guard hits**. linear_algebra has 22 probes and 0 hits.
2. **Record-level refusal.** `backfill_service_copy(..., policy=)` first checks every planned record of every extraction by identity. If any record is a withheld block (an unredacted copy), it sends nothing for the whole copy (`refused_unredacted`), whatever the text.
3. **Coverage.** The coverage denominator is unchanged and honest. It is the production one: the embeddable blocks of the redacted copy. The 111 blanked withheld blocks are outside it and reported as `redaction.blanked_blocks`. The guard's counts are now reported as `service_preparation.qwen.guard`.

Failing-first tests are in `tests/test_e0_relabel_round.py`, with fakes:
- A permitted block containing a withheld block's whole text reproduced `['ProtectedTextRefused', 'ProtectedTextRefused', …]` on `43b34769b`'s code. It is now embedded and coverage completes.
- A withheld tail is refused. It `DID NOT RAISE` before.
- An unredacted copy sends nothing.

### Reuse plan

The new plan is **`e0_e6a077cd391c5421`**. The pins changed (label A, prompt versions, rubric hash, allocations), so the plan id changed on purpose. `--reuse-run e0_a47534fecc49ded5` points it at run 3's directory for every **content-keyed** store:

- role checkpoints, keyed by pin, resolved identity, output bound, prompt and schema;
- vectors, keyed by document space and content;
- latency measurements, keyed by query encoder and question;
- the service copies, keyed by frozen tree, policy and harness;
- the experiment records.

How the reuse is held safe:
- **Only identical requests are reused.** A changed request misses its key.
- **The corpus must match.** `live.reused_store` refuses unless run 3 froze the same splits and candidate maps.
- **Separate outputs.** This plan's frozen manifests and results go to `runs/e0_e6a077cd391c5421/`. Run 3's results stay as they are.
- **Earlier admissions stay visible.** The new ledger's `entries_for` also reads run 3's sealed ledger. So a request that truncated, or was admitted without a recorded result, under run 3 is still never re-sent blindly.

| Reused ($0) | Re-sent or recomputed, and why |
|---|---|
| The bank (the writer's 12 calls), every question's frozen context, smoke and logged slices | Every **label pass** (both copies, all slices). Label A's pin and both prompts changed. |
| R3's contexts (window and split checkpoints), every document and query vector of R1–R5 | Every **adjudication**. Its prompt carries the rubric and the new passes. |
| The D0–D3 delivery answers and their judges and adjudications. They depend on the selection, not the labels. | The **metrics, finalists, S1–S4 decisions and reports**. They follow from the labels. |
| The finalists' D1 answers and online latencies, when a finalist is unchanged (same checkpoint key) | **A finalist that changes** gets its D1 answers, judges and online latency once. Finalist choice depends on the labels. |
| Both service copies (reopened: same identity) and run 3's 160 + 15 saved Qwen vectors | The probability backfill's **177 missing records** (now admitted). For the first time, probability's **three Qwen service arms** run and their top-20s join its label pools. |
| | **R0 and the service arms** are not checkpointed by E0, so they run again. Their production verification and query embeddings may hit the copies' own caches. |
| | The **model and route canaries**, as on every run. |

**Incidental finding (Low, not fixed).** `bank.plan_seeds` takes strata in the iteration order of the dict it is given. The CLI path always passes the in-memory `split_strata`, in `DEV_STRATA` order, so its seeds are stable. A plan's strata re-read from its JSON (sorted keys) gives other seeds for the later strata. An offline replay must reorder them. Fixing it would change the bank and every downstream key.

### The cumulative cap and the cost estimate

- **One cumulative cap.** When the relabel's ledger is created, `budget.authorized_ledger` **seals** run 3's ledger and **carries** its own committed spend into every admission. Run 3's ledger gets `superseded` and `halted`, which every earlier version of this code also refuses on. The spend carried is $14.149: reconciled charges plus outstanding reservations, per category.
- **What admission holds.** Carried plus own plus each request stays under $40 and under each **E0-wide** allocation. The relabel's hard cap is therefore **$40 − $14.149 = $25.851**, enforced before each send.
- **Allocations re-split** within the $40: labels/audits 24.60 → **33.00**, answers/verification 14.30 → **5.90**, drafting/context 0.85 and embeddings 0.25 unchanged.
- **What is left:** labels $21.70, answers $3.45, drafting $0.49, embeddings $0.22.
- **The dry run.** It now reports `plan["budget"]`: the estimate against what is left of the cumulative cap. The paid CLI authorizes on that. The whole-plan estimate ($48.99) no longer fits $40 and no longer applies when work is reused. With `--reuse-run` the estimate is `plan.reuse_estimate`, built from run 3's own ledger.

The offline estimate re-prices run 3's `labels_audits` tokens. Prices: Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Haiku 5.5 $0.10/$0.50 per 1M.

| Role | Run 3 calls | Input tokens | Output tokens | Run 3 $ | Re-priced, plain $ | Conservative $ (+ rubric 492 tok/call, +15% pools) |
|---|---|---|---|---|---|---|
| label_a (Haiku → Sonnet) | 277 | 1,346,917 | 294,804 | 0.282 | 5.642 | 6.761 |
| label_b (Sonnet) | 281 | 1,356,733 | 127,649 | 3.990 | 3.990 | 4.865 |
| adjudicator (Opus) | 86 | 1,135,686 | 124,336 | 7.030 | 7.029 | 8.253 |
| **labels/audits** | | | | 11.302 | **16.66** | **19.89** (with $0.01 canaries) |

The other categories, and the total:
- **Answers/verification:** $1.42 at worst, if every finalist changes (run 3's finalist answers cost $1.127) and the system arms cost twice run 3's $0.144.
- **Embeddings:** at most $0.045.
- **Drafting:** $0.01.
- **Total, conservative: $21.37.** That is against $25.85 left, with every category inside what is left of it. Labels/audits leaves $1.81 of headroom, more than one Opus reservation.
- **Central estimate: about $16.** This uses label A at Sonnet's own observed output rate, no pool growth, and unchanged finalists.

Committed aggregate: `docs/reviews/artifacts/experiments-e0/dry-run-plan.{json,md}`.
- It was refreshed under `env -i`, with no key and with `OPENROUTER_BASE_URL`/`OPENAI_BASE_URL` set to `http://127.0.0.1:9`.
- Network calls 0; copy trees unchanged; run 3's ledger byte-identical afterwards (sha256 `dbaa4d85…`).
- The preflight without env files passed every check, `reuse_ready` included. It was not ready only because the keys are absent. `new_authorization_needed: true`.

### The commands (for the orchestrator; not run here)

`$E` is an empty scratch root, as before. **`--new-authorization` is needed.** The plan id changed, because the label pins, prompt versions, rubric hash and allocations are part of it. Another plan's ledger exists, so `authorized_ledger` refuses without the flag. Creating the new ledger seals run 3's and carries its $14.149. Keep the single quotes, so the shell does not expand `$40`. `--reader-latency-budget-s` stays optional; without it S2 and S4 fail closed.

(a) Preflight only. Zero network; no value printed. Expect `"ready": true`, `run_id` `e0_e6a077cd391c5421`, `carried_usd` 14.149, `remaining_usd` 25.851, `estimated_usd` 21.37, `new_authorization_needed: true`:

```
cd learnanything-e0 && systemd-run --user --scope --quiet -p MemoryMax=6G -p MemorySwapMax=1G -- env -i PATH=$PATH HOME=$E/h CODEX_HOME=$E/c LEARNLOOP_CONFIG_DIR=$E/l UV_CACHE_DIR=/home/saturn/.cache/uv uv run --no-sync learnloop experiments e0 run --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 --env-file /home/saturn/.config/learnloop/settings.env --env-file /home/saturn/Documents/thinking/learnanything/settings.env --anthropic-key-env ANTHROPIC_API_KEY --openrouter-key-env OPENROUTER_API_KEY --perplexity-key-env PERPLEXITY_API_KEY --voyage-key-env VOYAGE_API_KEY --reuse-run e0_a47534fecc49ded5 --preflight-only --json
```

(b) The paid relabel run:

```
cd learnanything-e0 && systemd-run --user --scope --quiet -p MemoryMax=6G -p MemorySwapMax=1G -- env -i PATH=$PATH HOME=$E/h CODEX_HOME=$E/c LEARNLOOP_CONFIG_DIR=$E/l UV_CACHE_DIR=/home/saturn/.cache/uv uv run --no-sync learnloop experiments e0 run --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-20261021 --copy fixtures-local/contextual-embeddings/vaults/probability-20261021 --env-file /home/saturn/.config/learnloop/settings.env --env-file /home/saturn/Documents/thinking/learnanything/settings.env --anthropic-key-env ANTHROPIC_API_KEY --openrouter-key-env OPENROUTER_API_KEY --perplexity-key-env PERPLEXITY_API_KEY --voyage-key-env VOYAGE_API_KEY --run-dir fixtures-local/contextual-embeddings/runs --reuse-run e0_a47534fecc49ded5 --new-authorization 'owner 2026-10-23: Sonnet both + rubric relabel; cumulative $40 cap' --i-am-authorized-to-spend --json
```

Results are written to:
- `fixtures-local/contextual-embeddings/runs/e0_e6a077cd391c5421/<copy>/results.json`;
- the ledger: `fixtures-local/contextual-embeddings/ledger/e0_e6a077cd391c5421.ledger`.

### Gate

Every test command ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time, with `-n 6`. No full suite was run.

- **pytest:** 34 files, **572 passed, 1 skipped**. The skip needs the `openai_codex` SDK. The 34 files are:
  - the 33 of the previous round;
  - the new `tests/test_e0_relabel_round.py` (15 tests).
- **lint-imports** (`env -i`): **30 kept, 0 broken**.
- **Tests updated for the owner's decision:**
  - label A is Sonnet in `test_e0_review_round4_followup.py` and `test_e0_review_round5.py`;
  - the re-split allocations, and authorization on `plan["budget"]`, in `test_e0_review_round5.py` and `test_e0_review_round6.py`;
  - the committed plan id is now the relabel plan, in `test_e0_review_round7.py` and `test_e0_review_round8.py`;
  - the CLI help snapshot has the `run` entry's new `--reuse-run` option.
- **Fail-before:** the backfill tests above, on `43b34769b`.
