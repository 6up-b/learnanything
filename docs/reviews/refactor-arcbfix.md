# Arc B close: review fixes

The fix round after arc B's end-of-arc Codex review (`gpt-6.1-sol`, read-only, of `0f11cb1053..e0aae08684`), in
`docs/specs/refactor_strategy_v3.md` §2.1's rhythm. Branch `refactor/arcB-review-fixes`, based on main `e0aae08684`
(B1-B9 landed). Nine review findings, two items from the code-free reader of B9 (10) and a flaky IH test (11), and
one item the orchestrator added from the arc-close `--fresh-connections` run (12). Every claim was checked against the
code first; all nine findings held. Each fix is its own commit with a test that failed before it (checked by running
the new tests against an export of `e0aae08684`'s `src`).

## Findings, verdicts, fixes, tests

| # | Finding | Verdict | Fix | Test (fail-first) |
|---|---|---|---|---|
| 1 (high) | The router's spend guard committed its `spend_admission` record before raising `SpendRefused`; in rollback-journal mode a reader's snapshot blocks that commit for the 5 s busy timeout, so the component reported `failed` (or stayed pending past the deadline) instead of `spend` | Holds (base: `OperationalError: database is locked` at `repositories.py:1142` after 5 s) | The pre-B5 refusal path again (raise inside the transaction, which rolls back). The record is then built and written by `db.stores.provenance.write_decision_without_waiting`: a connection of its own, `busy_timeout = 0`, transaction-exit failures caught; under contention it is dropped with a warning | `test_arcb_close_fixes.py::test_a_refused_router_request_is_refused_at_once_while_a_reader_holds_a_snapshot` (refused in < 2 s, no receipt); the record still lands when nothing holds a lock |
| 2 (high) | `write_decision` (and `refusal_records.write`'s duplicate) entered `repository.connection()`; under a pin that is the caller's handle and its exit commits the caller's open transaction | Holds | One helper in the leaf, `provenance.write_through`: an owned connection (`OwnedConnection.owns_connection`) is entered as before; a borrowed one (pin, atomic) is never entered, and `write()`'s savepoint joins the caller's transaction or commits alone. Both writers call it (the store can't be imported by `refusal_records` without closing the db/refusal_records package cycle, so they share the leaf helper). `continue_job_trace`'s read does the same | `test_a_record_written_under_a_pin_never_commits_the_callers_work[store, refusal_records]` (base: the caller's row was committed) |
| 3 | Records and traces drew ids from `ids.new_ulid`, the stream the router's decision id (and its draw seed) comes from | Holds (base: under a frozen clock the second decision's id and seed differ with records on vs off) | `ids.UlidStream`, a monotonic stream with its own state and its own system randomness; `provenance.new_record_id` / `new_trace_id` and the plan-block and plan record builders use it. The shared stream's behaviour is unchanged (one `_next_ulid` step). B7's `seed_ids` workaround in `tests/voi_restore_scenarios.py` is removed; `test_voi_v2` and `test_voi_merge_composition` pass without it | `test_a_decisions_id_and_seed_are_the_same_whether_records_are_written_or_not`; `test_the_record_stream_is_monotonic_and_apart_from_the_shared_one` |
| 4 | `why.get`'s `codes_only` kept any token-shaped string; a figure author's one-word `unsupported_kind` (model text) passed | Holds | `why.reader.TEXT_FIELDS`: under those names every string and every key is withheld whatever its spelling. At the source, the reconstructed figure hashes `unsupported_kind` (`digest`) | `test_a_figure_authors_one_word_unsupported_kind_never_leaves_through_why` ("photosynthesis", CLI and RPC); `test_codes_only_withholds_text_fields_and_their_keys_whatever_the_spelling` |
| 5 | The plan block's record re-read the newest attempt in the write transaction instead of the chooser's captured `as_of` | Holds (base named attempt B, committed while the chooser waited) | `RouterChooser._noting` puts the identity's `as_of` on `BlockChoice.provenance` (and on the failure note); the engine records that; a decision with no captured `as_of` (the staged rule alone) reads it at write time as before | `test_a_plan_block_names_the_attempt_its_chooser_saw_not_one_committed_while_it_waited` |
| 6 | "What happened next" read the `router_outcomes` rebuild cache | Holds (base: outcome null for an attempt completed since the last rebuild) | `why/outcomes_now.py`: the read-time derivation `learnloop router decisions` used, now shared by `router decisions`, `router report` and both `why` paths (`outcome.basis = "derived_at_read"`; None without the vault). It lives in `why/` because `router` may not import `substrate` (lint-imports) | `test_why_shows_an_attempt_completed_after_the_last_rebuild` |
| 7 | `BackgroundJobs.spawn` started bare threads: hint jobs' receipts had no trace, their records a new one | Holds | `spawn` captures the request's trace and runs the job under it (only the trace; gates and observers stay with the request). The figure prefetch queue carries each trigger's trace, and each pass runs under it | `test_an_async_hints_receipts_and_records_share_the_requests_trace`; `test_each_queued_figure_trigger_runs_under_the_trace_that_queued_it` |
| 8 | Retention was promised (§3.7, ADR-017) but 253's trigger refused every update | Holds. Implemented, not documented away | Migration 254 replaces only `decision_records_no_update`: an update may change nothing but `alternatives_json` and `facts_json`, only to `[]` and `{"payload_pruned":true}`, only on a row over a day old; identity columns immutable, deletes refused. `db.stores.provenance.prune_old_decision_payloads` runs from startup maintenance with `router.payload_retention_days`; never raises; clears nothing below 254. Head fixture upgraded in place (only that trigger and `schema_migrations` change; README section). No table classified: none is new | `tests/test_decision_records_retention.py` (11 tests: old rows only, a second pass clears nothing, each identity column refused, placeholders only, a young row refused, deletes refused, below 254 a no-op, the migration changes only the trigger, startup runs the pass) |
| 9 (low) | `lesson_budget_record` set no subject | Holds | `subject_kind = "lesson"`, `subject_id` | `test_why_lesson_finds_the_record_the_real_lesson_budget_builder_writes` |
| 10 | The code-free reader's rough edges | Done, all eight | `waited_ms` shown as `prefetch_to_decision_ms` (configured wait stays `timeout_s`); failed components name their model from the route the decision logged where kept (`model_basis`: `answer` / `route_at_decision` / `not_stored`; `provider_basis`), in records and reconstructed rows; one `discarded` list at the top level, each entry naming its decision and label; `late_ms_precision_ms`; reconstructed withdrawals fill `workflows` / `source_attempts` from what opened or was generated in the window (`*_basis`); `author_attempts_n` vs `author_receipts_n`; `--first-build` gives `by_trigger_kind_window` and a `source` that follows the label; routing alternatives carry `p_basis` (record, stored or recomputed mix via `router_objective.mix.recompute`, `outside_support` = 0, or why null) | `test_why_cases.py`, `test_why_reader.py`, two unit tests in `test_arcb_close_fixes.py`; "Debug a decision" updated. Not stored, honestly: in the staged timeout case the decision kept no model for the timed-out LLM, so the record says `model_basis = not_stored` (filling it from the prefetch would change `router_decisions`, a ledger P-draw holds fixed) |
| 11 | `test_ih_numeric_seed.py::test_the_workflows_decision_with_no_lesson_keeps_the_predecessors_identity` failed 1-2 in 10 | The test's own setup, not a race: the plan's draws are live (random decision-id seeds); when the answered question finished its block, `current_block()` was None, `wait_feasible` False, and `decide_followup` took its deterministic insert-now path, which hashes no identity. Measured: 1 of 48 runs `(wait_feasible=False, block=None)` | `_miss_env(..., questions_left=True)` for that test (an answer that leaves questions in its block) | 120/120 runs with a current block and an identity after |
| 12 (orchestrator) | `test_forced_withdrawal_records.py::test_a_failed_check_draw_placement_and_lesson_builder_are_the_boundarys_children` failed under load (`'done' == 'item'`); also `test_ro5_landing.py::test_r5_1_..._unchanged[below_the_tag]` | Same cause in both, and not timing: stop_for_today is in the mix's support (`stop_coin = 0` removes only the coin) and the live draw chose it where the test needed an item. B3 test: 1 in 60 (the builder's boundary record was `chosen=stop_for_today, rule=stop_offer`); ro5: 7 in 240, at the first boundary, which `build_plan` decides | The B3 test uses the IH2 `draw` fixture's `never_stop`; `_fg1_env` redirects only a stop draw (both mixes) around the build and its first serve | B3 test 240/240, ro5 case 360/360 after. `test_ih2_lessons_compete.py::test_a_requested_item_is_placed_at_the_build_with_no_offer_beside_it` does not share it (it prefers the offer and reads the build's first row) and was left alone |

## Records added or changed

No new kind. Changed: `spend_admission` (router daily cap) is now written after the guard's rollback on its own
no-wait connection; `spend_admission` by `lesson_envelope` has subject `lesson:<id>`; `model_answer` facts gain
`model_basis` and `provider_basis`; record ids and trace ids come from their own stream; old rows' `facts_json` and
`alternatives_json` may read `{"payload_pruned":true}` and `[]` after the retention window.

## Proofs

**P-tests.** Every fix's test failed on `e0aae08684`'s `src` and passes on the tip (`tests/test_arcb_close_fixes.py`:
15 test functions, 16 cases; `tests/test_decision_records_retention.py`: 7 functions, 22 cases). Targeted run, 349 files
at `-n 4`: 5547 passed, 27 skipped, 2 xfailed, 2 failed, both from these fixes and fixed in `702dff6c04`:
`test_ad23_contract.py::test_protected_material_is_indistinguishable_from_absent_material` and (found by the same
check) `test_hint_telemetry.py`'s twin-run test compare two runs' rows under frozen ids and now reset the records'
own stream per run as they reset the shared one; `test_architecture.py::test_sql_writes_stay_in_registered_owner_modules`
registers retention's update. Those three files then pass (44 + 101 with `test_notes_linked.py`). (The selector `scripts/affected_tests.py --base e0aae08684` falls back to the whole suite because `migrations/` and
`fixtures/` changed; the explicit list was its depth-0 selection on the source files minus `ids.py`, `db/scopes.py`
and `cli/app.py` (303 files), plus the named gates, every migration test and the edited tests: 349 files).
`lint-imports` 43 kept, 0 broken; `ruff check src tests scripts` clean; the four validators pass; references
regenerated, a second run changes nothing.

**P-draw** (B2's harness as B8 left it: `drive6.py`, `compare7.py`, `fakes4.py`, `neutralize.py`, `premigrate.py`;
fresh backup-API copies of `~/learnloop-backups/20261109-copy` under `fixtures-local/`, one day, the second served item
missed, FG1's follow-up by the tests' `AuthorFake`, the first stop declined, the mixture seed pinned, the router LLM
and Decider in-process fakes, every other route at `127.0.0.1:9`, the net watch on), three sides: pre-arc
`0f11cb1053`, main `e0aae08684`, the tip.

- Main vs tip, each vault: LLM requests identical (15 / 5 / 11), Decider requests identical (15 / 5 / 11), gates
  identical, traces 22 / 5 / 10 each, every table identical with ids and times aside; `decision_records` 115 / 67 /
  102 rows on both sides with the same kind/status/rule counts.
- Pre-arc vs tip: requests, prompts and gates identical. One table differed, `probe_presentations`, in each vault:
  B6's deliberate key split (FG1's pin names its router decision `router_decision_id`, no longer
  `decision_receipt_id`; `docs/reviews/refactor-b6.md`), already on main. With that one key set aside on both sides,
  every table is identical (ids and times aside). `decision_records`: 0 rows pre-arc vs 115 / 67 / 102.
- Records on the tip by status: arxiv_v2 chosen 112, deferred 3; linear_algebra chosen 63, deferred 4; probability
  chosen 98, deferred 3, fallback 1.
- No non-loopback connect; subprocesses only `git` (the project sweep) and `powerprofilesctl`; no Codex process; every
  receipt this run wrote is from a fake provider (traced: `fake_decider`, `fake_llm`; untraced: driver-side `fake`).

**P-shadow** (B1's scripts, B7's shape): `learnloop rebuild --shadow --json` on fresh copies with main's tree and with
the tip's (which applies 254): arxiv_v2 1037 leaves, linear_algebra 999, probability 633, 0 differing after ids and
times are masked; `schedule_effects` identical on both sides (arxiv_v2's nine `practice_item_state` rows with a 0-day
shift are the same on main).

## Open items

- Codex's review lists no high finding left; the review is not re-run here.
- `continue_job_trace` and `prune_old_decision_payloads` still enter `repository.connection()` for their own reads
  and writes at points where no caller transaction is expected (a worker's lease, startup). The first now avoids
  entering a borrowed connection; the second runs at startup only.
- A timed-out component's model is `not_stored` when the decision's `model_ids` kept none (fix 10): naming it from
  the prefetch would change `router_decisions`' rows.

## Unverified

- The durability lane (WAL) was not run for the new tests; fix 1's test is rollback-journal by design (WAL readers
  don't block a commit).
- The phone host and MCP server were not run end to end; fix 7 touches only the sidecar's job threads.
