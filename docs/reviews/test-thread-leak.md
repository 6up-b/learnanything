# Test-suite thread leak

**Stage:** `test-thread-leak`, branch `fix/test-thread-leak` (worktree `learnanything-tleak`), base `497169069` (main: rebuild-equivalence mvp-0.34, mobile PR-2, migrations through 222).
**Owner request (2026-10-26):** "please fix the thread leak". Symptom: in the landing full suite (`-n 8`) one xdist worker collected ~800 leaked threads that burned ~17 cores (load average 400+ on 32 cores); one full suite stalled for 4 h; `tests/test_reader_rw1c_review.py` leaked ~5 threads per test.
**No migration, no successor, no config key.** No paid or live calls (fakes only).

## 1. Finding every source

### 1.1 The diagnostic

`tests/thread_guard.py` (a pytest plugin, `pytest_plugins` in `tests/conftest.py`) wraps `threading.Thread.start` for the whole test process. Each start records which test, which phase (setup/call/teardown) and which wider-scoped fixture (if any) started the thread, plus its creation stack (40 frames, lines looked up only when reported). A thread started by a tracked thread inherits that thread's owner, so a leaked worker that spawns more is never charged to a later test. After each test's teardown, every thread the test owned that is still alive gets a bounded join; module/class/package/session-fixture threads are checked when that fixture finalizes.

`LEARNLOOP_THREAD_LEAK_REPORT=<file>` turns it into a survey: one JSON line per leaking test (thread name, native id, target, creation site and stack, CPU seconds at the leak, live thread count) instead of a failure, and at session end the CPU each leaked thread had used by then (what kept burning after its test). `LEARNLOOP_THREAD_LEAK_GRACE` shortens the join grace for a survey.

### 1.2 Survey 1: the baseline (base `497169069` + the diagnostic only)

Whole suite (1,052 test files) in four alphabetical shards, each `flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G -- python -m pytest -n 6`, report mode, 0.5 s grace, on a `git archive` snapshot of the commit under the worktree's ignored `.pytest_tmp_survey/` (so editing could go on during the run).

| Shard | Wall | Leaking tests | Leaked threads |
|---|---|---|---|
| 00 (`test_action_loss` … `test_e2e_tui`) | 980 s | 246 | 323 |
| 01 | 744 s | 471 | 613 (77 errors: one worker's guard crashed on the sampler of 2.3 and every later test there errored; covered again in survey 2) |
| 02 (the `test_reader_*` files) | **2,929 s** | 659 | 2,062 |
| 03 | 498 s | 657 | 1,106 |

Leaks by creation site, all shards:

| Threads | Thread | Created at | Test files |
|---|---|---|---|
| 3,037 | `learnloop-reading-sweep` | `content/pipeline/jobs.py` `_ensure_reading_sweep` (a `SidecarContext.load` → `DurableIngestJobs.bind`) | 270 |
| 318 ×3 | `learnloop-post-attempt-{diagnose,embed,gaps}` | `learnloop_sidecar/post_attempt_worker.py` `notify` | 38 |
| 57 | `learnloop-quick-check-N` | `jobs.py` `_ensure_worker` | 10 |
| 28 | `source-service-spend-leases` | `source_retrieval/service_spend.py` `_Leases.hold` (process singleton) | 27 |
| 21 | `learnloop-ingest-drain` | `jobs.py` `_ensure_worker` | 11 |
| 3 | `ingest-heartbeat-<job>` | `content/pipeline/runner.py` `_run_claimed` | 2 |
| 2 | `process_request_thread` | the ChatGPT-plan fake server's stalled reply (`tests/chatgpt_plan_fakes.py`) | 2 |
| 1 | `learnloop-codex-interrupt` | `ai/providers/codex.py` `_schedule_turn_stop` (a fake whose interrupt never answers, 2 s) | 1 |
| 1 | `Thread` | `local_embeddings/worker.py` `run_job` (the GPU sampler) | 1 |

No leaked thread was non-daemon.

**What burned the CPU.** At session end, the leaked threads that had kept using CPU after their test were all sidecar background owners of Reader tests, and almost all of them came from one file:

| CPU seconds after the leak | Thread | From |
|---|---|---|
| 33,532 | reading sweep (~100 threads) | `test_reader_rw1c_review.py` |
| 3,821 / 1,921 / 1,854 / 959 / 957 | reading sweep | `test_reader_reconnect.py`, `_inquiry_kill_switch.py`, `_branches.py`, `_inquiry_status.py`, `_reconstruct.py` |
| 2,382 + 1,242 + 1,242 | post-attempt slots | `test_reader_rw1c_review.py` |

The same picture was visible live in the CA1 landing's full suite (read from `/proc` only): one worker at 711 % CPU, 200 threads, 139 of them runnable at ~0.24 cores each with ~316 s of CPU apiece. Shard 02 of the survey took 2,929 s against 500–1,000 s for the others, while one of its workers held 37–77 runnable threads using 20–26 cores.

**Why idle pollers burned cores.** Alone, a sweep pass on the Reader library vault costs 16 ms of CPU and then waits 30 s (measured: `sweep_reading_requests` 3 ms, `resume_book_preparation` 6 ms, `resume_contextual_index` 6 ms, `refresh_fusion_posteriors` ~0; a post-attempt pass 3–16 ms). No loop busy-spins by itself. The most likely cause, consistent with both measurements, is the count: with hundreds of leaked threads in one interpreter, every wake competes for the GIL, and CPython's GIL hand-off (each waiter wakes every 5 ms switch interval to ask for the lock) turns hundreds of runnable threads into a futex convoy that burns kernel and user time without progress. The passes then take seconds instead of milliseconds, so more threads are runnable at once, and the convoy feeds itself. That fits the ~0.24 cores per thread seen in both runs, and survey 2 (4.1) shows the burn gone once the threads stop leaking. The fix is to stop leaking the threads, not to tune their pace.

## 2. Root causes and fixes

### 2.1 Production: a sidecar context had no way to stop everything it starts

`SidecarContext` owns the ingest host (drain, quick checks, reading sweep), the exam graders, the post-attempt worker (three slots) and the approach-map builds. The `shutdown` RPC stopped three of them and EOF only drained the map builds; the post-attempt worker was never stopped.

* New `SidecarContext.close()` stops all four, each with a bounded join, idempotent (a later `load` or submit restarts them, as after `shutdown`).
* `handlers/app.py` `shutdown` and `server.serve`'s `finally` (EOF) both call it.
* `PostAttemptWorker.shutdown(timeout)` now joins its three slots within one deadline (it was 2 s per slot), so shutdown stays bounded when a slot is inside a model call. The job in flight is released before its next paid request (unchanged).

### 2.2 Production: the spend-lease heartbeat outlived its last lease

`source_service`'s process-wide `_Leases` heartbeat only noticed it had nothing to renew after a full 60 s beat. `drop` now sets an `_idle` event when the last lease goes, and the thread ends at once; `hold` clears it. (Leases still renew every `HEARTBEAT_SECONDS` while any is held; the reservation semantics are unchanged.)

### 2.3 Production: two sampler threads shadowed `Thread._stop`

`local_embeddings/worker.py` and `experiments/contextual_embeddings/e1/worker.py` each define `Sampler(threading.Thread)` with `self._stop = threading.Event()`. `_stop` is `Thread`'s own private method: once such a thread ends, `is_alive()` and `join()` raise `TypeError: 'Event' object is not callable`. Renamed to `_stop_requested`. (Survey 1 found it because the guard's `is_alive()` crashed on it; the guard now tolerates a broken `is_alive` too.)

### 2.4 Tests: close what the test constructs

Most leaks were tests that build a `SidecarContext` (211 construction sites in 130 files, mostly through helpers such as `recap_fixtures.context`) and return without closing it. Rather than edit every site, `tests/background_owners.py` wraps the constructors of `SidecarContext`, `DurableIngestJobs`, `PostAttemptWorker` and `ExamGradingManager`; an instance constructed **directly by code under `tests/`** is recorded (by weak reference, so a test that drops its host to check that the host's threads end on their own still can; a context's thread-owning parts are held strongly, so a context a test drops, say by rebinding a fresh one, still has its threads stopped), and the autouse `close_test_background_owners` fixture closes them, newest first, when the test ends. Instances built by production code (a context's own ingest host; any host that builds contexts) are not recorded: they are their owner's to stop, so a production owner without a stop path still fails the guard.

Individual fixes where the generic one did not apply:

* `tests/test_daily_plan_reentry.py`: one test replaced its context in a loop (the dropped one was never closed); it now closes each round's context.
* `tests/test_source_service_spend_accounting.py::test_concurrent_admission_counts_the_unreconciled_receipt` admitted four reservations and never settled them, so the process heartbeat renewed them for the rest of the run; it now settles them after its assertions.
* `tests/chatgpt_plan_fakes.py`: a stalled reply slept `stall` seconds (5 s) in the fake server's handler thread; it now waits on a `_closing` event that `close()` sets.

The test semantics are unchanged: no test was skipped, xfailed or loosened; only teardown was added.

### 2.5 The idle desktop sidecar

`tests/test_sidecar_idle_threads.py` (new) pins the production half:

* a loaded sidecar with its post-attempt slots started has exactly the four background threads (`reading-sweep`, `post-attempt-{diagnose,embed,gaps}`) and over a 1 s quiet window they use < 0.05 s CPU (read per thread from `/proc/self/task/<tid>/stat`);
* `close()` stops all of them within 5 s; the `shutdown` RPC does too; EOF on the sidecar's stdin closes its context;
* the lease heartbeat ends within 5 s of its last lease being dropped (its beat is 60 s), and keeps beating while one is held.

## 3. The permanent guard

`tests/thread_guard.py` stays on for every run. A test (or wider-scoped fixture) that leaves a thread alive after a **2 s** join grace (`JOIN_GRACE_SECONDS`, a guardrail: long enough for a worker told to stop to see its event, short enough that a real leak costs little) fails in teardown with each thread's name, daemon flag, target, CPU seconds, the phase it started in, its creation site and the last 12 frames of its creation stack. Daemon threads are not exempt: a daemon that keeps running still burns the worker. Non-daemon threads fail the same way (none were found; a non-daemon leak would also block the xdist worker's exit).

`ALLOWED` is the reviewed allowlist of process-lifetime singletons (a creation-site substring and the reason). It is **empty**: the one process singleton found (the spend-lease heartbeat) now ends with its last lease.

## 4. After the fix

### 4.1 Survey 2 (the fixed code, 2 s grace)

Same shards, same lock and scope, report mode with the guard's real 2 s grace, on a snapshot of the fixed commits (shard 00 at `db75235`, whose one leak, the reentry test of 2.4, is fixed since; shards 01–03 at `b382bd0`):

| Shard | Wall | Leaked threads |
|---|---|---|
| 00 | 958 s | 1 (fixed in `test_daily_plan_reentry.py`) |
| 01 | 739 s | 0 |
| 02 | 1,446 s of pytest (the wall includes ~1.7 h queued behind the CA1 landing's suite) | 0 |
| 03 | 483 s | 0 |

No thread kept burning CPU after its test. Shard 02 ran in 24 min against 49 min in survey 1. The survey's failures are all artifacts of running on a `git archive` snapshot (no `.git`: `test_public_tip_guards`, the tracked-fixture walkers, `test_reader_rw2b_fix10/11` and `test_rw2c_*`, which `git archive` an old commit) plus the installed-Codex tests below. None of them fail in the worktree (4.2).

### 4.2 The full suite, once, at the end (the baseline for a speed-up pass)

```
flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=2G -- \
  uv run --no-sync pytest -n 8 -p no:cacheprovider --durations=50
```

At `b382bd0` (the code of this stage; later commits touch only this record). **10 failed, 21,669 passed, 80 skipped, 41 xfailed in 3,319.6 s (55 min 20 s).** No test failed the thread-leak guard. The 10 failures are the known environment break, the machine's Codex CLI 0.164.0, and fail on main too: `test_codex_isolation_mcp_check.py` ×3 (`test_the_installed_codex_passes_the_launch_check[False|True]`, `..._pins_a_server_only_an_unseen_ancestor_project_disables`), `test_codex_lockdown_round2.py` ×3, `test_codex_lockdown_round3.py` ×3 and `test_diagnosis_isolation.py::test_configured_mcp_servers_are_listed_and_disabled` (`@needs_codex`).

* **Threads per worker** (sampled every 5 s from `/proc/<pid>/status`, 654 samples; the first ~55 s were missed while the sampler was fixed): idle workers hold 33 threads (native pools); peaks over the run were **92, 64, 49, 37, 35, 35, 35, 34**. Before the fix the CA1 landing's suite had a worker at 737 threads (read from `/proc`).
* **Load average (1 min):** peak **88.5** at 01:05:31, during the stretch of the upgrade-chain and simulation tests (`test_evsi_multisim`, the `mvp0NN_upgrade` and `ad23_sim` files, 01:00–01:08). Python threads in the workers stayed under 100 in total then, so that load is processes those tests start, not threads. It was 5–20 for most of the run, against 400+ before the fix.
* **The 50 slowest tests:**

```
175.75s call     tests/test_evsi_multisim.py::test_cli_multisim_quick_fits_every_family_and_reports_claims
158.20s call     tests/test_ad23_successor.py::test_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest
107.88s call     tests/test_e0_review_round1.py::test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes
107.30s call     tests/test_mvp011_upgrade.py::test_existing_vaults_keep_their_version_until_the_owner_upgrades
104.39s call     tests/test_method_explicit_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required
102.93s call     tests/test_e0_relabel_round.py::test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results
101.75s call     tests/test_mvp015_upgrade.py::test_upgrade_command_defaults_to_the_latest
101.47s call     tests/test_method_explicit_upgrade.py::test_by_default_the_chain_reports_the_advisory_guard_and_proceeds
96.44s call     tests/test_mvp016_upgrade.py::test_upgrade_command_defaults_to_the_latest
93.15s call     tests/test_method_explicit_upgrade.py::test_upgrade_through_the_chain_from_earlier_successors
90.95s call     tests/test_recurrence_commands.py::test_the_upgrade_command_defaults_to_the_latest
89.70s call     tests/test_recurrence_commands.py::test_the_upgrade_command_prints_the_advisory_guard_status
82.66s setup    tests/test_e1_harness.py::test_a_smoke_only_local_run_loads_checks_and_stores_nothing
80.86s setup    tests/test_sim_teach_back.py::test_runner_completes_session_with_teach_back_item
80.66s call     tests/test_e0_review_round4.py::test_h3_two_paid_runs_with_different_run_directories_share_one_budget
80.38s setup    tests/test_e1_harness.py::test_the_cli_plans_from_e0_manifests_offline
80.19s setup    tests/test_e1_harness.py::test_the_whole_pilot_with_fakes
79.35s setup    tests/test_e1_harness.py::test_a_provisional_plan_runs_no_stage
77.99s call     tests/test_mvp018_upgrade.py::test_upgrade_command_defaults_to_the_latest
77.84s setup    tests/test_e1_harness.py::test_an_unfinished_e0_run_is_not_imported_and_the_manifest_plan_is_provisional
73.92s setup    tests/test_e1_harness.py::test_a_wrong_label_pool_misses_e0s_checkpoints_and_the_replay_is_unverified
73.67s setup    tests/test_e1_harness.py::test_the_replay_reproduces_e0_without_any_call_and_the_plan_is_frozen
73.40s call     tests/test_regrade_contract_upgrade.py::test_upgrade_through_the_chain_from_earlier_successors
72.51s setup    tests/test_e1_harness.py::test_preflight_reports_every_check_and_is_not_ready_without_the_model
69.72s setup    tests/test_sim_probe_validation.py::test_planted_confuses_with_is_diagnosed_within_budget
69.34s call     tests/test_ad23_sim.py::test_related_topics_adapt_faster_practice_correct
69.25s call     tests/test_ad23_sim.py::test_unrelated_topics_not_dragged[noisy]
69.19s call     tests/test_mvp020_upgrade.py::test_upgrade_through_the_chain_from_mvp013_to_mvp018
69.13s call     tests/test_ad23_sim.py::test_unrelated_topics_not_dragged[wrong]
63.40s call     tests/test_plan_first_transport_offer_grants.py::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter
62.80s call     tests/test_ad23_sim.py::test_reading_kind_effects_and_saturation_recovered[0.3]
62.34s call     tests/test_ad23_sim.py::test_reading_downturn_found
61.56s call     tests/test_ad23_sim.py::test_reading_kind_effects_and_saturation_recovered[0.1]
61.26s call     tests/test_mvp020_upgrade.py::test_upgrade_command_defaults_to_the_latest
60.82s call     tests/test_mvp024_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required
60.16s call     tests/test_mvp022_upgrade.py::test_upgrade_command_defaults_to_the_latest
59.86s call     tests/test_mvp024_upgrade.py::test_by_default_the_chain_reports_the_advisory_guard_and_proceeds
56.01s call     tests/test_mvp023_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required
55.61s call     tests/test_mvp024_upgrade.py::test_upgrade_through_the_chain_from_earlier_successors
55.28s call     tests/test_mvp021_upgrade.py::test_upgrade_command_defaults_to_the_latest
55.00s call     tests/test_mvp023_upgrade.py::test_by_default_the_chain_reports_the_advisory_guard_and_proceeds
54.04s call     tests/test_intent_codex_rereview.py::test_f2_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest
53.98s call     tests/test_mvp018_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required
52.91s call     tests/test_mvp018_upgrade.py::test_by_default_the_chain_reports_the_advisory_guard_and_proceeds
52.89s call     tests/test_mvp023_upgrade.py::test_upgrade_command_defaults_to_the_latest
52.65s call     tests/test_mvp022_upgrade.py::test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required
51.21s call     tests/test_mvp022_upgrade.py::test_by_default_the_chain_reports_the_advisory_guard_and_proceeds
50.93s call     tests/test_mvp023_upgrade.py::test_upgrade_through_the_chain_from_earlier_successors
50.48s call     tests/test_plan_determinism.py::test_a_contrast_pair_plans_the_same_staged_block_in_every_session[one_fits]
50.22s call     tests/test_cli_help_snapshot.py::test_recursive_cli_help_matches_snapshot
```

They are mostly whole upgrade chains (`test_mvp0NN_upgrade.py`, `test_method_explicit_upgrade.py`, `test_recurrence_commands.py`: one fresh vault upgraded through every successor), simulations (`test_evsi_multisim`, `test_ad23_sim`, `test_sim_*`) and the E0/E1 harness fixtures (module setups of ~80 s in `test_e1_harness.py`). That is where a speed-up pass should start: share an upgraded vault per chain through a backup-API copy, and build the E1 harness fixture once per session.

## 5. Gate

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
* Targeted pytest, in the 5G scope with `-n 6` and the guard on: **1,938 passed, 5 skipped, 3 failed** (the installed-Codex tests of `test_codex_lockdown_round3.py`, the environment break above). The files: every file this stage added or changed, every test file that exercises a changed module (found with `git grep` for `post_attempt_worker`, `PostAttemptWorker`, `service_spend`, the two sampler modules, `chatgpt_plan_fakes`, `learnloop_sidecar.server` and the `shutdown` RPC), the sidecar files that build contexts in the leak list, and the contract tests (architecture, CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, SQLite file copies, tracked fixture databases):

  `test_ad23_t1_routes.py`, `test_ai_compare.py`, `test_approach_maps.py`, `test_architecture.py`, `test_auto_build_spend_report.py`, `test_chatgpt_plan_cli.py`, `test_chatgpt_plan_landing.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_sidecar.py`, `test_chatgpt_plan_signin.py`, `test_chatgpt_plan_workspace.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round3.py`, `test_daily_loop_reader_authored_practice.py`, `test_daily_plan_reentry.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_async_router.py`, `test_diagnosis_card.py`, `test_e1_worker.py`, `test_exam_protection.py`, `test_exam_protection_review.py`, `test_facet_identity_ingest.py`, `test_facet_locks_landing.py`, `test_figures_codex_review.py`, `test_figures_rpc.py`, `test_hint_feedback_texts.py`, `test_hint_outcome.py`, `test_ingest_jobs.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`, `test_library_ask_review.py`, `test_mobile_allowlist.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport_paid_roles.py`, `test_plan_first_transport.py`, `test_plan_first_transport_today_quiet.py`, `test_post_attempt_worker.py`, `test_probe_orchestration_remainder.py`, `test_probe_remint.py`, `test_provenance_service.py`, `test_question_queue.py`, `test_reader_formative_texts.py`, `test_reader_pdf_selection.py`, `test_reader_rw1b_review.py`, `test_reader_rw1c_review.py`, `test_reader_rw3b_review_fixes.py`, `test_reading_hardening_2_fixes.py`, `test_reading_hardening_review_fixes.py`, `test_reading_request_sweep.py`, `test_required_method_round3_review.py`, `test_reread_safety.py`, `test_reveal_ledger.py`, `test_secondary_attach.py`, `test_section_coverage_rpcs.py`, `test_settings_sidecar.py`, `test_sidecar_animation.py`, `test_sidecar_append.py`, `test_sidecar_blueprint_picker.py`, `test_sidecar_contract.py`, `test_sidecar_diagnostic.py`, `test_sidecar_epigraphs.py`, `test_sidecar_exams.py`, `test_sidecar_golden_path_assessment.py`, `test_sidecar_golden_path.py`, `test_sidecar_idle_threads.py`, `test_sidecar_ingest_m3.py`, `test_sidecar_item_authoring.py`, `test_sidecar_knowledge_model.py`, `test_sidecar_ladder.py`, `test_sidecar_probe.py`, `test_sidecar_quick_add.py`, `test_sidecar_reader_p3.py`, `test_sidecar_reader.py`, `test_sidecar_registry.py`, `test_sidecar_serializer_snapshot.py`, `test_sidecar_source_retrieval.py`, `test_sidecar_span_view.py`, `test_sidecar_synthesis.py`, `test_sidecar_teach_back.py`, `test_sidecar_transport.py`, `test_sidecar_tutor_qa.py`, `test_source_deletion.py`, `test_source_service_spend_accounting.py`, `test_source_service_spend_envelopes.py`, `test_source_space_resolver.py`, `test_sqlite_file_copies.py`, `test_t6_followup_composition.py`, `test_tracked_fixture_databases.py`, `test_ux_phase1_first_run.py`, `test_workbench_in_session_gaps.py`, `test_workbench_text_gaps.py`.
* The full suite once (4.2).
* Durability lane: not run on its own. No migration or DB/connection code changed; the durability-marked tests in the files above ran in the targeted run and in the full suite.
* No frontend, Rust, schema or config change: no vitest, `cargo check` or DB reference regeneration was needed.

## 6. Open items

* **CLAUDE.md.** The Tests section says `conftest.py` "does three things that surprise people". It now does two more: the thread-leak guard (`tests/thread_guard.py`) and closing the background owners test code constructs (`tests/background_owners.py`). This stage did not edit CLAUDE.md. The owner may want a line there.
* **The idle sidecar's pollers.** Idle, the reading sweep and the three post-attempt slots each wake every 30 s for a 3–16 ms pass (§1.2). That is not a busy loop (the test pins it), but the post-attempt slots could block until a notify or the next lease or backoff time instead of polling. Left as is: it is not needed for the leak, and it would change when the queue is reconciled.
* **Other worktrees.** The fix helps a suite only once that branch has it. The CA1 landing's runs during this stage (in `learnanything-merge2`) still showed the leak: a worker at 677–737 threads, load average up to 214, and a stall at the end.
