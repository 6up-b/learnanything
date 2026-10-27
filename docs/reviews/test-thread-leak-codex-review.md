# test-thread-leak: Codex review fixes

Codex review job `20261027-013934-YFECh4` (gpt-6.1-sol) on branch `fix/test-thread-leak` at `c22b38bf2`. It found two Medium findings, no High. Both reproduced as failing tests and both are fixed. No live calls were made; every model in the tests is a fake.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Closing a context leaves Reader jobs uncancelled | fixed | `091f05ea0` (+ `7088c9b68` imports) | `tests/test_sidecar_close_cancels_jobs.py`: `test_closing_the_context_stops_a_running_discovery_before_its_next_request`, `test_the_sidecars_eof_cancels_a_running_discovery`, `test_a_closed_contexts_job_has_its_next_physical_request_refused`, `test_close_is_bounded_when_a_job_does_not_return` |
| F2 | Medium | The gaps worker can start further paid requests after shutdown | fixed | `091f05ea0` | `tests/test_sidecar_close_cancels_jobs.py`: `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request`, `test_a_stopped_worker_leases_no_gap_job` |

### F1: reproduction and fix

**Reproduced.** Before the fix, the two cue-discovery tests failed. In each, the first judge request is held on an event, and the close (`ctx.close()`, or EOF through `server.serve`) releases that request only after it has cancelled. `close()` returned with the job still running (`done` unset). Under EOF the context's job registry never saw a close, and the thread guard reported the job's thread as leaked at teardown.

**Fix.** A context-owned job registry, `src/learnloop_sidecar/background_jobs.py` (`BackgroundJobs`, on `SidecarContext.background_jobs`):

* `spawn(target, name=, epoch=)` starts the job on a daemon thread and records the *epoch* it started in. It runs the job under `gate_model_requests(_ClosingGate)`. Once the epoch has ended, that gate refuses every physical model request with `SpendCancelled`, the refusal every paid path already stops on. An outer gate the job installs itself (FiguresGate, coverage's, AD's guard) composes with it and is settled on a refusal.
* `cancel()` ends the epoch. `close()` cancels and then joins the spawned threads, bounded to 2 s in all (`CLOSE_JOIN_SECONDS`). That is a guardrail, not a model parameter: it is the same bound as the post-attempt worker's join. A job started after a close belongs to the new epoch and runs normally, matching the existing "a later load or submit starts work again" semantics.
* `SidecarContext.close()` now cancels these jobs **first**, before joining anything else. Then it stops the ingest host, the exam graders, the post-attempt slots and the map builds. Last, it joins the cancelled jobs. The `shutdown` RPC and EOF (`server.serve`'s `finally`) both call `close()`. EOF does not set `shutdown_requested`, so the epoch is what the jobs check.
* Cue discovery's cancellation predicate now also asks `closed_since(epoch)`. Its open budget asks that predicate before every request, so after the close no request is admitted, even one to a fake client. Hints' predicate (`practice.cancel_hint`) asks it too.
* These now start through the registry: cue discovery, library jobs (ask / notes / compare / tutor), reading-path judgments, intent routings, hints and coverage (`curriculum.cover`). The jobs without a predicate of their own (library, reading paths, intent, coverage) are stopped at their next physical request by the gate.
* `tests/background_owners.py` closes `background_jobs` among a test-built context's parts.

**Not converted, stated as open items:** `chatgpt_plan` sign-in (an interactive OAuth wait that sends no model request), `edit-key-recheck` (`item_authoring`) and `import-key-check-recovery` (`context.recover_import_key_checks`). The last two run exercise key checks with durable markers. I have not audited how a refused request is recorded there: it might be recorded as a failed check rather than left for the next start. Gating them would change persisted state, which goes beyond this stage.

### F2: reproduction and fix

**Reproduced.** Before the fix, `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request` failed: three `learner_gap_same_prerequisite` requests were sent after `shutdown` began. The test holds the first request until `worker._stop` is set. `test_a_stopped_worker_leases_no_gap_job` failed because `process_next_gap_job` had no `cancelled` argument.

**Fix.**

* `process_next_gap_job(..., cancelled=)`, in `src/learnloop/diagnosis/text_gaps/jobs.py`:
  * It asks `cancelled` before the lease and leases nothing when it is true.
  * On the live path (no `budget_factory`) it builds the text's own budget as `TextBudget.for_text(vault, cancelled=cancelled)`. That is the budget `process_learner_text` would build, plus the cancellation that `ReviewSpend` asks before every request. The worker does **not** pass a `budget_factory`, so the live daily-cap check (`max_calls_per_day`) still runs as before.
  * A job stopped by `cancelled` (a `ReadingDeferred(spend=True)` or an `AIInterrupted` while `cancelled()` is true) is released as `released`. Its checkpoint payload is kept, it gets no backoff, its attempt is refunded, and its `last_error` reads `cancelled: the worker stopped`, so the next start resumes it.
* `PostAttemptWorker._run_gaps` passes `cancelled=self._stop.is_set` and stops its drain on `released`.

### Claims that didn't hold (from the review)

* "`SidecarContext.close()` stops every background thread this context owns": it now covers request-started jobs too (F1). The three spawns listed above remain outside the registry, as open items.
* "A job in flight stops before its next paid request": now true of the gaps slot (F2). The stage record (`docs/reviews/test-thread-leak.md` §2.1) is corrected to say so.
* `test_the_shutdown_rpc_stops_every_background_thread` overstated what it checks, so it is renamed `test_the_shutdown_rpc_stops_the_idle_background_owners`. The active-job claims are pinned by the new tests.
* "Required validation: the durability run was omitted": by the owner's 2026-10-17 rule the durability lane runs once, in the landing gate. This change touches no migration, DB or connection code.

### Spec and owner-rule conformance

There is no schema, migration, table-role, replay or WAL change, and no serving algorithm or kill switch changed. No new decision parameter was added. The one new constant, `CLOSE_JOIN_SECONDS = 2.0`, is a lifecycle guardrail (a bounded join), not a model or decision parameter, so it is not registered in `parameter_registry.py`. Spend controls are unchanged: the daily cap and per-text caps still apply, and a cancelled gap job's attempt is refunded the same way a spend stop's is. No new network surface.

## Gate (this step)

* `uv sync --extra dev --extra mobile` passed, and `uv pip install pypdfium2` reported it already installed.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
* Reproduction, before the fix: `tests/test_sidecar_close_cancels_jobs.py` gave 4 failed, 2 passed, 2 errors (thread-guard leaks at teardown). After the fix: **6 passed**.
* Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 <78 files>`: **1,385 passed, 9 skipped, 1 failed, 1 error** in 300 s.
  * The one failure (and its teardown error) is `test_plan_first_transport_offer_grants.py::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`. Its harness joins an ingest drain of ~1,200 batches for at most 60 s, and the full-suite durations in the stage record list this test at 63.4 s.
  * The machine's load average was 137–145 throughout, from the CA1 landing's full suite in another worktree.
  * It failed the same way alone (3/3), and also alone **on the pre-fix source** (`c22b38bf2`'s `src/`, 1/1: 1 failed, 1 error). It is load-bound and not caused by this change. The landing gate should judge it at normal load.
* No migration, DB or connection code changed, so no durability tests. No frontend or `src-tauri` changes, so no npm, vitest or cargo. No schema change, so no DB reference regeneration.
* Not run, per the owner's 2026-10-17 rule: the full suite, the whole durability lane and the whole vitest run. They belong to the landing gate.

Targeted test files run (78): `test_ad1_outside_and_cli.py`, `test_approach_map_replay.py`, `test_architecture.py`, `test_compare_keep_switch_off.py`, `test_compare_sources_keep.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_async_router.py`, `test_diagnosis_card.py`, `test_figures_codex_review.py`, `test_figures_fix_round2.py`, `test_figures_fix_round4.py`, `test_figures_scope_redesign.py`, `test_figures_switch_off.py`, `test_hint_authored_reveal_ruling.py`, `test_hint_blind.py`, `test_hint_discriminating.py`, `test_hint_evidence.py`, `test_hint_feedback_texts.py`, `test_hint_h2a_review.py`, `test_hint_h2a_review_round2.py`, `test_hint_h2a_review_round3.py`, `test_hint_h2b_fix3.py`, `test_hint_h2b_rereview.py`, `test_hint_h2b_review.py`, `test_hint_kill_switch.py`, `test_hint_outcome.py`, `test_hint_report.py`, `test_hint_service.py`, `test_judge_routes.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps_rereview.py`, `test_learner_text_gaps_review.py`, `test_library_ask_expand.py`, `test_library_ask.py`, `test_library_ask_review.py`, `test_library_exercises.py`, `test_mobile_allowlist.py`, `test_owner_capture_1025.py`, `test_plan_first_transport_grant_scope.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport.py`, `test_plan_follows_path.py`, `test_post_attempt_worker.py`, `test_practice_proposal_caller_columns.py`, `test_reader_compare_table.py`, `test_reader_cue_holdout.py`, `test_reader_find_sources_callers.py`, `test_reader_formative_texts.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_reconstruct.py`, `test_reader_rw1b_final_verify.py`, `test_reader_rw1b_fix_round4.py`, `test_reader_rw1b_rereview.py`, `test_reader_rw1b_review.py`, `test_reader_rw3b_fix_round4.py`, `test_reader_rw3b_fix_round5.py`, `test_reader_rw3b_protection.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_try_first.py`, `test_reading_paths.py`, `test_roles_judges.py`, `test_roles_switch_off.py`, `test_rw4d_rw3b_composition.py`, `test_rw4_kill_switches.py`, `test_rw7b_codex_review_fixes.py`, `test_secondary_attach.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`, `test_sidecar_close_cancels_jobs.py`, `test_sidecar_contract.py`, `test_sidecar_idle_threads.py`, `test_sidecar_serializer_snapshot.py`, `test_workbench_assistance.py`, `test_workbench_in_session_gaps.py`, `test_workbench_text_gaps.py` .
