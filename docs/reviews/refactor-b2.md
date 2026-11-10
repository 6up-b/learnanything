# Refactor B2: router failures

Step B2 of `docs/specs/refactor_strategy_v3.md` (§2.4, case 1 of §3.6; the map's S1, S2, S3, S5, S6). Branch `refactor/b2-router-failures`, based on main `536963aa30` (B1 landed: ADR-017, `provenance`, migration 253).

**Result.** Every plan block decision the container persists now leaves a `plan_block` decision record with one `model_answer` child per component. A chooser crash, a component timeout, a failed or refused component, a late answer and an unclaimed prefetch can all be answered through `learnloop why`, where before B2 each was silent or lived only inside the router's ledger JSON. Nothing served changes. The draw-for-draw replay matches main on all three vault copies apart from the new records and the trace column. It needed one harness hook for a race that main has on its own (below).

## Records added

All are written by `engine._boundary` (a block) or `engine._close` (a chooser's stop) on the block's own connection, inside its `BEGIN IMMEDIATE` transaction, right after the router's `plan_block` row. They're built by a pure function, `daily_plan/boundary_records.plan_block_records`, and written with `provenance.write`; there is no second writer. A builder exception is caught and logged with the trace, and `provenance.write` never raises, so the block commits whatever happens to its records.

| kind | status | rule | decided_by | what it carries |
|---|---|---|---|---|
| `plan_block` | `chosen` | the chosen block's reason code (`new_material`, `review`, `repair_open_problem`, `lesson_offer`, `stop_offer`, `stop_minutes_used`, ...) | the chooser's (`mixture`, `objective_no_models`, `single_option`, `irreversible`, `not_ready`) or `lane_quota` | `chosen_ref`; `alternatives` = every support option with its `p` and `lost_by=not_drawn`, feasible options outside the support (`outside_support`) and infeasible candidates (`infeasible`); `facts` = `timeout_s` and `prefetch_timeout_s` (the configured waits), `waited_ms`, `may_defer`, `boundary_key`, `prefetch_trace`, `propensity`, `drawn_component`, `mix_fallback`, `option_count`, `feasible_n`, `candidates_n`, `stop`, `stop_offered`, `card_error`; `versions` = algorithm version, policy, design, seed, why version, question-set and LLM schema versions; `subject = block:<id>`; `detail = router_decisions:<id>`; `created_at` = the wall time the chooser took its models' answers |
| `plan_block` | `fallback` | `chooser_error`, `not_offered`, `continue_current_at_boundary`, `chosen_by_not_allowed`, `propensity_out_of_range`, `why_kind_unknown` | `lane_quota` (`facts.chooser_decided_by` keeps the chooser's) | as above; the rejected choice first in `alternatives` with `lost_by` = the rule. On `chooser_error`: `error_type` (the class) and `error_where` (`module:function:line` of the raising frame, `<`/`>` replaced so the record passes its code check), never the message |
| `model_answer` | `chosen` (answered in time), `timeout`, `failed` (failed, invalid, unreachable), `refused` (the spend guard), `excluded` (not set up), `discarded` (answered, but the chooser then crashed) | the component's own status code (`answered`, `timeout`, `failed`, `invalid`, `spend`, `not_ready`, `unreachable`) | `router_llm`, `router_decider`, `numeric_policy`, `staged_rule` | one per component in the router's `models` summary (Decider, LLM, numeric) plus the staged rule; child of the `plan_block` (`parent_id`), same trace, subject and detail; `chosen_ref` = the component's favoured option; `alternatives` = its distribution `[{ref, p}]`; `facts` = `component`, `latency_ms`, `cost_usd`, `subscription`, `drew`, `timeout_s`, `prefetch_timeout_s`, `waited_ms`, `reason` (a readiness code), `discarded_by`; `versions` = model and provider; `error_type` from the head of the component's error ("TimeoutError: ..."), never the rest |

An id that isn't a code (whitespace in a vault's id) is kept as `sha256:<16 hex>` rather than letting the whole record drop.

**Derived at read time, with no write** (`db/stores/provenance.py`, shown by `why`):

- **`discarded`**: for each `plan_block` (`LATE_ANSWER_KINDS`), the calls of its trace and its prefetch's trace, for its boundary key, that started before its `created_at` and finished after it (`late_ms`), or hadn't finished when asked (`late_ms` null).
- **`unclaimed`**: router calls (`owner_kind = router_decision`) whose boundary key no shown record and no logged router decision names. Their decision was never made: the key changed before the serve (S4) or the prefetch was evicted (S5).
- **`prefetch_traces`**: the traces that started the shown decisions' prefetches, whose calls `why` now reads too. A trace with calls and no records, such as a prefetch whose key went stale, now answers with its calls instead of `not_found`.

## The failure each answers

| Map | Before B2 | Now |
|---|---|---|
| S1 (`engine.py` chooser call, now :2708) | Any chooser exception became `<error: Type>`. The chooser's record, the mix and both models' answers were dropped, with no log line. Since Nov 9 the router's row said `chooser_error` | `plan_block`/`fallback`/`chooser_error` with type and where; a `model_answer` per component, `discarded` when it had answered (the router hangs each model's summary on the exception, `router_runtime.note_failure`); one WARNING line naming the trace, the type and where, and the message at DEBUG only |
| S2 (`router_runtime.py` `Prefetch.results`, now :188) | An unanswered component became a synthetic timeout inside the router's JSON only | `model_answer`/`timeout` with `timeout_s` and `prefetch_timeout_s`; the plan_block's `waited_ms` and `may_defer`; and when the answer lands, `why` lists it under `discarded` with `late_ms` |
| S3 (`call_decider` now :638, `call_llm` now :728) | A provider failure stayed in the result object | `model_answer`/`failed` or `refused` with the error class; when no decision is drawn from the entry, the call shows under `unclaimed` (its receipt already carries status and `error_type`) |
| S5 (`RouterRuntime.start` eviction, now :497) | No record | Derived: the evicted entry's calls are `unclaimed` |
| S6 (`router_chooser.py` `card_error`, :342 at the map, now :354) | On the record, but no persisting reader | `plan_block.facts.card_error` (the exception class) |
| B1 open item: prefetched decisions | A decision prefetched in one RPC and served in the next named only one trace | `trace_id` = the serving request; `facts.prefetch_trace` = the request that started the job (`Prefetch.trace_id`, set from the ContextVar at `RouterRuntime.start`). In the P-draw runs, 26 of 29 plan_block records were prefetched under a different trace |
| F10 | `decide`'s docstring said "Pure" | It says it writes nothing but isn't pure: the chooser reads the vault, starts the model threads and waits on them |

**How the pieces reach the shell.** `BlockChoice.provenance` (new, `compare=False`, never persisted) carries the prefetch's trace, the wall time the answers were taken and `may_defer`, kept off `router_record` because that dict is written to `router_decisions` as it stands. `engine.Decision.seen` carries the same, plus on a crash the exception's type, where it was raised and the noted models.

**The B1 open items B2 touched.** The writers are outside the replay closure: `daily_plan.engine`, `router_runtime`, `router_chooser`, `objective_chooser` and the new `boundary_records` aren't reached from any rebuild, replay or upgrade root (grimp), so `test_decision_records_is_unreachable_from_replay` needed no widening and passes unchanged. The router path's deadline is unaffected: the records go in the caller's transaction after the decision, which is the "write in the caller's transaction or after the decision" rule. No writer sits inside an AD operation: `ad_operation` scopes are confined to `ad_slot.py`.

## Proofs

**P-tests** (`tests/test_router_failure_records.py`, 10 tests, every model a fake from `tests/router_model_fakes.py`, every assertion read back through `learnloop why --json`):

- a chooser crash at the R2 mixture (`mvp-0.24`) and at the objective (`mvp-0.47`): `fallback`/`chooser_error`/`lane_quota`, `RuntimeError` at `tests.test_router_failure_records:exploding:<line>`, the planted message nowhere in the output, one `discarded` `model_answer` per component (Decider, LLM, and numeric at the objective), the step still an item;
- the crash's WARNING names the trace and type and never the message;
- a component timeout (LLM gated, `timeout_seconds = 0.3`, `prefetch_timeout_seconds = 0.6`): `model_answer`/`timeout`/`router_llm` with both waits, the Decider `chosen`, staged and numeric present, the alternatives with `p` and `lost_by`;
- the late answer: `discarded` with `late_ms` null while the gated LLM is still out, and `late_ms > 0` once it answers; the text output says "answered N s late";
- a prefetched decision: `trace_id = TRACE_SERVE`, `facts.prefetch_trace = TRACE_PREFETCH`, and `why` reads both traces' calls;
- a key that changed before the serve: `why` on the prefetch's trace (no records) returns its calls with the stale key's calls `unclaimed`, and the serving trace has none;
- the store's router owner equals `router_runtime.RECEIPT_OWNER`; ids that aren't codes are hashed; error class extraction; a builder that raises leaves the block served and no records.

**Fail-first.** The five end-to-end tests (crash x2, timeout, late answer, prefetch) were run against main's code (`536963aa30`'s `src` and `migrations` from `git archive`, on `pytest -o pythonpath=`), with only the new module's import removed: all five fail with `why` answering `not_found` for the trace (no record exists). On this branch they pass.

**P-draw.** B1's harness (`drive5.py`, `compare7.py`, `fakes4.py`, `neutralize.py`, `premigrate.py`), copied and adapted. Main is `536963aa30`'s tree from `git archive`, the branch is this worktree, and each runs on its own fresh backup-API copy of `~/learnloop-backups/20261109-copy` (stale `probability/.learnloop/state.sqlite` removed) under `fixtures-local/`, premigrated by its own code (both to 253). Every AI route is at `http://127.0.0.1:9`, the router LLM and the Decider are in-process fakes, and the mixture seed is pinned to the decision id. Each run is one day of at most 40 steps, with the second served item missed and the first stop declined. The comparison reports `decision_records` apart and sets `model_call_receipts.trace_id` aside.

*First pass (B1's driver as it was):* linear_algebra was IDENTICAL. arxiv_v2 differed only in `router_objective_traces.carried_for` (one carried valuation recorded one decision earlier). probability differed there, and in one router decision's candidate propensities (0.088 against 0.260), through `v_residual` (0.001898 against 0.001787). **Main against main shows the same thing.** A second main run on probability differs from the first in exactly that propensity (0.088 against 0.260) and in `v_residual` (0.001898 against 0.001894). It's RO6's carried-valuation race: a prefetch job drains the deferred valuations after its numeric answer releases the serve, and the serve's `_carried_for` reads whatever has landed. `docs/reviews/router-speed2.md` ("Identity") and `docs/reviews/instruct-handoff-review.md` ("The flaky test") describe it, and B1's pass was identical by timing.

*Second pass (`drive6.py`, the same driver plus one hook on both sides):* each decision waits for its own prefetch job to finish, its drain included, before it decides. That removes the race without touching a draw. Every decision waited, and none timed out (13, 5 and 9 waits).

| Vault | Served | Router decisions | LLM / Decider requests | Gates | New receipts (traced) | decision_records (branch) | Result |
|---|---|---|---|---|---|---|---|
| arxiv_v2 | 12 | 15 | 15 / 15 identical | 1 identical | 50 (42) | 13 `plan_block` `chosen` (8 `new_material`, 3 `repair_open_problem`, 1 `lesson_offer`, 1 `stop_offer`); 52 `model_answer` `chosen`/`answered` | **IDENTICAL** (ids and times aside) |
| linear_algebra | 9 | 9 | 5 / 5 identical | 1 identical | 20 (15) | 6 `plan_block` `chosen` (2 `review`, 1 `new_material`, 1 `repair_open_problem`, 1 `stop_offer`, 1 `stop_minutes_used`); 20 `model_answer` `chosen`/`answered` | **IDENTICAL** |
| probability | 14 | 13 | 11 / 11 identical | 1 identical | 38 (30) | 10 `plan_block` `chosen` (6 `new_material`, 2 `repair_open_problem`, 1 `stop_offer`, 1 `stop_minutes_used`); 36 `model_answer` `chosen`/`answered` | **IDENTICAL** |

Prompts (14, 11 and 16), Today, the plan, every step, submit and feedback, the traces (22, 5, 10) and every other table's new rows matched, as did the removed-row counts. Main wrote no `decision_records`. With fakes that answer at once, no timeout, failure or fallback happened, so every component is `chosen`; the P-tests stage those. Router decisions outnumber plan blocks because the restraint gate's `plan_interrupt` and the learner's picks are router decisions too, and neither is a boundary decision (open items).

**No real model, no network.** All 216 new receipts across the six runs of each pass came from fake providers (`fake_llm`, `fake_decider`, `fake`): 0 from a real model. The second pass's net watch (`sitecustomize`) logged no connect or resolve. It logged 12 subprocesses, all `powerprofilesctl get` and `git rev-parse HEAD`, and no Codex process. The first pass's net log was overwritten before it was read; its receipts are the same fakes.

**P-shadow** isn't named for B2. The records sit outside replay (above), and B1's runtime test (`test_a_rebuild_never_calls_the_record_and_keeps_its_rows`) still passes.

## Storage

From the P-draw branch copies: a `plan_block` holds about 1.1-1.3 KB of JSON and ids (at most 1.4 KB), and a `model_answer` about 0.55-0.66 KB, so a decision with four components is about 3.5 KB. The arxiv_v2 day's 65 records took 104 KB of pages, indexes included (`dbstat`), for 13 decisions: about 8 KB a decision. At the copy's busiest weeks (13 attempts a week), that is around 100-150 KB a week, well inside §3.7's 5% a month.

## Tests

- Targeted lane, `-n 4` under the 5 GB scope: `scripts/affected_tests.py --base 536963aa30` on the changed source picked 934 files. The lane added `test_router_failure_records`, `test_provenance`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json` and `test_effective_defaults_golden` to them, for 935 files: **16,385 passed, 58 skipped, 5 xfailed, 1 failed** in 27:48. The failure, `test_tui_feedback.py::test_feedback_submit_uses_codex_grading_when_runtime_ready`, polls a local HTTP grading server for 10 Textual pauses; it passed alone three times and its file passed whole, so I read it as load (`-n 4` beside the B4 and B6 agents) rather than B2. The landing gate will show it either way. The new test file alone: 10 passed.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean.
- `tests/cli_surface.json` is unchanged: `why` gained JSON keys (`prefetch_traces`, `discarded`, `unclaimed`), not parameters.
- Vault: `Concepts/Scheduling and Selection` has a new "The daily plan's block router" section, and `Workflows/Inspect Persistent State` gained the prefetch trace, `discarded` and `unclaimed`. The references were regenerated once after the source commit and committed, and a second run changed nothing (28 notes changed and one added, `daily_plan/boundary_records`; mostly line shifts in engine-cited config fields). The four validators pass.

## Open items

- **Restraint and follow-up gate decisions** (`plan_interrupt`, `followup_run.router.decide`, `engine.py` gate call at :4760) have their own models and timeouts and write no record yet. Their calls aren't `unclaimed`, because the router's ledger names their keys. B3 (the offer and withdrawal records) or B5 is the natural home.
- **A boundary dropped whole** (`_refuse_a_taken_boundary`, `BoundaryTaken`) rolls its records back with the block, which is consistent with "nothing logged". If the owner wants dropped draws visible, they need a record outside the block's transaction.
- **`unclaimed` scans `router_decisions.detail_json`** with `json_extract` for the keys it checks. It runs only when a shown trace has router calls whose key no shown record names. On the arxiv_v2 copy this costs milliseconds, but a much larger ledger may want an indexed key column.
- **`LATE_ANSWER_KINDS`** is `plan_block` alone. A later kind joins only if its writer stamps `created_at` with the moment its answers were taken.
- **The carried-valuation race** (main's own, above) makes main differ from main through `carried_for`, `v_residual` and propensities. Later P-draws should use `drive6.py`'s job-wait hook, or the race should be fixed in its own step.
- **B1's other open items** stand: `job_enqueued` (B7), retention's trigger relaxation, and B9's reconstructed reader.

## Unverified

- The desktop app and the phone host weren't run. The records come from `engine._boundary` and `_close`, which every surface reaches, and the P-draw drives the sidecar handlers.
- The durability lane (WAL) wasn't run for the new tests. The writes join the block's own `BEGIN IMMEDIATE` transaction, and the landing gate runs durability.
- A real timeout, failure or spend refusal was staged only with fakes (the P-tests), not on a backup copy.
