# Refactor B3: forced items, withdrawals, boundary failures

Step B3 of `docs/specs/refactor_strategy_v3.md` (§2.4, case 2 of §3.6; the map's S12, the `forced_items` row, §4.1's check, offer and AD-unavailable rows, break 1). Branch `refactor/b3-forced-withdrawals`, based on main `87ec4085a5` (B1, B2, B4 and B6 landed).

**Result.** The Nov 8 case now answers from rows: an offer taken back for forced items names the probe that forced it, its follow-up workflow and source attempt, the offer's own decision as its parent, and the decision that came next as its child. Under IH2's switch the contest decision names the offer it replaces with both options' chances. Plan decisions name their triggering attempt. The restraint gate, a failed check draw or placement, a crashed lesson builder, AD unavailable, a cold check served as practice and a Today offer published unlogged each leave a record where before they left a log line. Nothing served changes: the draw-for-draw replay matches main apart from the new records and the trace column (below).

## Records added

Every record is built by a pure function (`daily_plan/plan_records.py`, `daily_plan/boundary_records.py`, `router/decisions.offer_failure_record`) after its decision, and written with `provenance.write` in the transaction of the act it describes, or `db/stores/provenance.write_decision` where the act has none. There is no second writer API. A builder that raises is caught and logged with the trace (`engine._record_quietly`), and `provenance.write` never raises.

| kind | status | rule | decided_by | subject | what it carries | written by, where |
|---|---|---|---|---|---|---|
| `offer_withdrawn` | `withdrawn` | `forced_items`, `offers_off`, `never_shown`, `superseded_by_decision` | `plan` | `offer:<router_decisions.id>` (else `block:<id>`) | `alternatives` = the forced items, each `{ref, origin, workflow, source_attempt, workflow_state, workflow_decision}`; `facts` = `offer_block`, `offer_decision`, `superseded_by`, `shown_on`, `expired_row`, `forced`, `workflows`, `source_attempts`, `forced_n`, `forced_origin`; `chosen_ref` = the replacing decision (supersession); `parent_id` = the offer's own `plan_block`; `detail` = the offer's `router_decisions` row | `lesson_offer.withdraw`, `supersede`, `release_never_shown`, in the act's own transaction (every caller: the engine's withdrawal, IH2's contest, a new offer replacing an open one, IH3's learner pick, the never-shown sweep) |
| `plan_block` (B2's, extended) | as B2 | as B2 | as B2 | `block:<id>` | new facts: `trigger_attempt` (break 1), `forced`, `workflows`, `source_attempts`, `forced_n`, `forced_origin`, `superseding_offer_block`, `superseding_offer_decision`; `parent_id` = the withdrawal that caused the boundary, else the triggering attempt's newest record (B7's, once it writes one) | `engine._write_boundary_records`, unchanged place |
| `plan_block` (the day's check block) | `chosen` | `ro5_randomized_check` | `rules` | `block:<id>` | `facts` = `checks`, `assignments`, `propensity` 1.0, `trigger_attempt`, the forced items; parent as above | `engine._write_check_block_records`, in the block's transaction. B2 wrote no record for this block |
| `randomized_check` | `failed` | `draw_error`, `place_error` | `plan` | the boundary's block | `error_type`, `error_where`; a child of the boundary's `plan_block` | collected in `_boundary` (`failures`), written with the boundary's records |
| `lesson_offer_build` | `failed` | `builder_error` | `plan` | the boundary's block | as above | as above |
| `plan_interrupt` | `chosen` (insert now, or a lesson offer drawn), `deferred` (wait), `refused` (a hard constraint) | the first refusal's `constraint_key`, else the router's `why_code`, else `decided_by` | the gate's (`mixture`, `refused`, `no_room_to_wait`, `not_ready`, ...) | `item:<follow-up>` | `alternatives` = the gate's support with `p`, `lost_by=not_drawn`; `facts` = `block`, `plan`, `propensity`, `wait_feasible`, `est_minutes`, `displaced`, `refusals`, `boundary_key`, `trigger_attempt`, the configured waits, `waited_ms`; `model_answer` children per component (B2's builder, now `boundary_records.component_records`); `detail` = its `router_decisions` row | `engine._write_interrupt_records`, after `_log_interrupt`, in the write that logs the router row (both callers) |
| `ad_slot` | `fallback` | AD's code: `guard_denied`, `predicate_unavailable`, `facts_refused`, `epoch_changed`, `error:<Type>`, `incumbent_facts_failed`, `choice_rejected`, `slot_not_admitted` | `incumbent` | `item:<slot item>`, or `plan:<id>` for the day's deferrals | `facts` = `phase` (`view`, `facts`, `decide`), `where` (`slot`, `deferrals`), `block`, `position` or `deferrals_n`, `denials` (each `{verb, table, reader}`, at most 10), `denials_n`, `entries`; `error_type` for a failed facts phase | `engine._ad_note`, called once the phase failed, written into the plan's own `atomic()` |
| `serve_eligibility` | `excluded` (displaced), `fallback` (served as practice) | the decision's reason code | `serve_eligibility` | `item:<id>` | `facts` = `verdict`, `request`, `block`, `until`, `window_until`, `reveal_total`, `primed`, `reveal_events`, `tasks`, `retimed`, `task_withdrawals` (codes) | `engine._held_cold_check`: displaced in the event's transaction; served as practice with its own short transaction |
| `today_offer` | `failed` | `head_mismatch`, `decision_not_built` | `scheduler_seeded_exploration` | `slate:<id>` | `facts` = `served_head`, `realized_head`, `surface`, `published_unlogged`; `error_type`, `error_where` for another failure; `parent_id` = the build's `slate` record; `detail` = `scheduler_slates` | `learnloop_sidecar/handlers/queue._record_unlogged_offer`, in the offer's transaction when it has one |

Ids that aren't codes are hashed (`boundary_records.ref`). A refusal's `why`, an eligibility `message`, an exception's message and a head's text never reach a record (`test_the_builders_keep_ids_numbers_and_codes_only` plants text in each).

## The failure each answers

| Map | Before B3 | Now |
|---|---|---|
| `forced_items` row (`engine.py` withdrawal, now `advance_with_context`; `lesson_offer.py:370`'s constants) | The `expired` row said `forced_items`; which probe forced it, its workflow and the next decision were time-ordering only | `offer_withdrawn` names the forced items, workflows and source attempts; parent the offer's `plan_block`; the next boundary's `plan_block` names it as parent (`advance_with_context(parent_record=...)`) |
| IH2 (switch on) | The contest's router row held both options; the replaced offer's `expired` row named the decision | The contest's `plan_block` names the replaced offer and the forced items, with both options' `p`; the offer's `offer_withdrawn` (`superseded_by_decision`) names the contest as `chosen_ref`. `WITHDRAWN_FORCED` stays for the switch's off path, and both paths are tested |
| Break 1 (`router_chooser.py:428`, `objective_chooser.py:1225`) | A plan decision named no triggering attempt; it was only hashed into the key | `facts.trigger_attempt` on every `plan_block` and `plan_interrupt`: the newest attempt, read on the decision's own connection in its transaction, which is the key's `as_of` unless an attempt committed between the decision and its write. `parent_id` = that attempt's newest record when one exists |
| Randomized checks: draw or place failure (`engine.py:3133`, `:3179` at the map) | WARNING line only | `randomized_check`/`failed`/`draw_error` or `place_error`, a child of the boundary's record |
| Lesson offer build: builder crash (`engine.py:2896` at the map) | WARNING line only | `lesson_offer_build`/`failed`/`builder_error`, a child of the boundary's record |
| B2's open item: restraint decisions | `plan_interrupt` router rows only | `plan_interrupt` records with their components |
| AD unavailable (`engine.py:4930`, `:4947`, `:5032` at the map; `denial_log.py:98`) | WARNING line; denials in `ad_guard_denials.jsonl` | `ad_slot`/`fallback` with the phase, AD's code and the guard's refusals as codes; the JSONL log stays (below) |
| Serve eligibility (`engine.py:5069` at the map) | WARNING line on a serve as practice | `serve_eligibility`, `fallback` or `excluded` |
| S12 (`router/decisions.py:100`) | A head mismatch published the offer unlogged, a warning only | `today_offer`/`failed`/`head_mismatch` naming both heads (`OfferHeadMismatch` now carries them as attributes; its message is unchanged) |

## The AD denial log: kept, with records beside it

The brief's condition was "move denials from the JSONL file to records if nothing else reads the file". Two things read it, so it stays:

- `learnloop ad report`'s `guard` block (`adaptive_difficulty/report.py:30` imports `denial_log`; `summary` counts the live log by entry point and the archives);
- `learnloop upgrade` marks the log at its start and archives the marked lines after a successful upgrade (`cli/app.py` `_mark_ad_denial_log`, `_archive_ad_denial_log`).

The records sit beside it. B1's open item (a writer inside an AD operation must add `decision_records` to `AD_WRITABLE` or write outside the operation) is met by writing outside: `operation._record_denials`, which already runs in the operation's `finally` after the guard is removed from every connection, also keeps each refusal's codes (verb, table, reader, entry; never the `why`, which is prose) in a context variable (`operation.take_denials`, reached by the plan through `ad_slot.take_guard_denials`). The plan's AD phase that found AD unavailable takes them when it records the incumbent's fallback, in the plan's own `atomic()`, after AD's savepoint has rolled back. So:

- the record is never written inside an operation, the guard never sees it, and `decision_records` stays `DENIED` and out of `AD_WRITABLE`;
- a poisoned operation's rollback can't take the record with it (writing in `_record_denials` itself would have: its savepoint form rolls back on `OperationPoisoned`);
- it never waits on the write lock: the plan's `atomic()` already holds it (`BEGIN IMMEDIATE`);
- a context variable, not the process-wide `DENIALS` list, so a background AD job's refusals are never told as the serving request's.

`adaptive_difficulty/operation.py` is in the replay closure; it gains only the context variable and imports nothing of `provenance`, and `test_decision_records_is_unreachable_from_replay` passes unchanged.

## Proofs

**P-tests** (`tests/test_forced_withdrawal_records.py`, 14 tests, every model a fake, every assertion read back through `learnloop why --json`):

- the Nov 8 shape with IH2's switch off (at mvp-0.55 with `lessons_compete_with_followups = false`) and below its tag (mvp-0.54): the probe still served; `offer:<id>` gives one `offer_withdrawn`/`withdrawn`/`forced_items` naming the probe, `fw_test` and its source attempt, its parent the offer's `plan_block`; the next decision's `plan_block`, in the same trace, names the withdrawal as parent, the probe in `facts.forced` and the triggering attempt;
- IH2's switch on: the contest's `plan_block` has the offer as an alternative with `0 < p < 1`, `superseding_offer_block`/`_decision` and the forced probe; the replaced offer's `offer_withdrawn` is `superseded_by_decision` with the contest's router row as `chosen_ref`; no `forced_items` record exists;
- the restraint gate: `deferred` (wait) and `chosen` (insert now), each with its support and a `model_answer` child for the Decider; a refused follow-up `refused` with the constraint as its rule;
- a raising check draw, check placement and lesson builder: three `failed` children of one `plan_block`, `RuntimeError` at `tests.test_forced_withdrawal_records:boom:<line>`, the planted message nowhere, the plan still serving an item;
- the day's check block's own `plan_block` (`rules`, `ro5_randomized_check`, its router row as detail);
- AD: a failed facts phase (`incumbent_facts_failed`, the High 1 path with planted text in a malformed context) and a real guard denial (`guard_denied`, phase `view`, the refused read of `practice_attempts` as codes, and the JSONL log still counted by `denial_log.denial_count`);
- a cold check served as practice (`fallback`) and displaced (`excluded`), the eligibility message nowhere;
- S12: a head mismatch publishes the offer, logs no router row, and writes `today_offer`/`failed`/`head_mismatch` with both heads, its parent the build's `slate` record;
- every builder, with text planted in ids, refusals, messages and exceptions, passes `check_no_prose` and carries none of it.

**Fail-first.** The 13 end-to-end tests were run against main's code (`87ec4085a5`'s `src` and `migrations` from `git archive`, `pytest -o pythonpath=`): all 13 fail, each on the missing record (`not enough values to unpack` on the `why` read, or the missing `superseding_offer_block` fact). On this branch all 14 pass.

**P-draw.** B2's harness (`drive6.py` with its job-wait hook, `compare7.py`, `fakes4.py`, `neutralize.py`, `premigrate.py`, `vcopy.py`), copied and adapted. Main is `87ec4085a5` from `git archive` (`src`, `migrations`, `tests`), the branch this worktree at `1ddf7c88ed`. Each side runs on its own fresh backup-API copy of `~/learnloop-backups/20261109-copy` (stale `probability/.learnloop/state.sqlite` removed) under `fixtures-local/`, premigrated by its own code. Every AI route at `http://127.0.0.1:9`, the router LLM and Decider in-process fakes, the mixture seed pinned to the decision id; one day of at most 40 steps, the second served item missed (FG1's follow-up by the tests' AuthorFake), the first stop declined. Three modes, each on all three vaults:

- **asis**: the copies as backed up (mvp-0.54, IH below its tag: the Nov 8 withdrawal path);
- **head**: each copy upgraded to mvp-0.57 by its own code (`learnloop upgrade --to mvp-0.57`), IH switches at their defaults (IH2 on);
- **ih2off**: as head, with `[router_objective] lessons_compete_with_followups = false`.

| Mode | Vault | Served | LLM / Decider requests | Gates | Result | decision_records main / branch | B3's rows on the branch |
|---|---|---|---|---|---|---|---|
| asis | arxiv_v2 | 12 | 15 / 15 identical | 1 identical | **IDENTICAL** | 96 / 96 | none |
| asis | linear_algebra | 9 | 5 / 5 identical | 1 identical | **IDENTICAL** | 49 / 50 | 1 `plan_block`/`chosen`/`ro5_randomized_check` |
| asis | probability | 14 | 11 / 11 identical | 1 identical | differs in carried valuations (the known race, below); **IDENTICAL** against a second main run | 79 / 81 | 1 `ad_slot`/`fallback`/`slot_not_admitted`, 1 check block |
| head | arxiv_v2 | 5 | 8 / 8 identical | 1 identical | **IDENTICAL** | 113 / 114 | 1 `ad_slot`/`fallback`/`slot_not_admitted` |
| head | linear_algebra | 7 | 5 / 5 identical | 1 identical | **IDENTICAL** | 40 / 41 | 1 check block |
| head | probability | 15 | 11 / 11 identical | 1 identical | **IDENTICAL** | 87 / 89 | 1 `ad_slot`, 1 check block |
| ih2off | arxiv_v2 | 6 | 9 / 9 identical | 1 identical | **IDENTICAL** | 113 / 113 | none |
| ih2off | linear_algebra | 9 | 5 / 5 identical | 1 identical | **IDENTICAL** | 49 / 50 | 1 check block |
| ih2off | probability | 15 | 10 / 10 identical | 1 identical | **IDENTICAL** | 82 / 84 | 1 `ad_slot`, 1 check block |

"IDENTICAL" covers served items, router decisions, prompts, gates, traces and every other table's new and removed rows, ids and times aside; `decision_records` is reported apart and `model_call_receipts.trace_id` set aside. Every `plan_block` on the branch carries `facts.trigger_attempt` (12 of 12 on head/probability); none has a parent, since no withdrawal happened and no attempt record exists yet.

*asis/probability.* Main against branch differed in one decision's carried valuation (`v_residual` 0.001633 against 0.001894) and so its propensities (0.4416 against 0.6176). Three more runs of the same mode (two main, one branch): main run 1 against main run 2 differs exactly as main against branch did (0.4416 against 0.6176); main run 2 against main run 3 differs at another decision (propensity 0.4608 against 0.6330, through the same carried valuation); branch run 1 against branch run 2 differs there too; and main run 3 against branch run 2 is **IDENTICAL**. That is RO6's carried-valuation race on main (B2's record, "First pass"), which `drive6.py`'s job-wait hook narrows but doesn't close on this vault; not B3's change.

*What the drive didn't reach.* With fakes that answer at once and one missed item, no offer was open when the probe arrived, so no withdrawal or contest happened on a copy, and the engine's restraint gate didn't fire (the run's `plan_interrupt` rows come from FG1's own gate, `followup_run.router`, which is B5's). The P-tests stage those.

**No real model, no network.** All 564 receipts the 18 runs wrote came from fake providers (`fake_llm` 316, `fake_decider` 158, `fake` 90): 0 from a real model; the 3 repeat runs likewise. The net watch (`sitecustomize`) logged no non-loopback connect; its subprocesses were `powerprofilesctl get` and `git rev-parse HEAD` only, and no Codex process.

**Replay.** The writers are outside the replay closure (`daily_plan.engine`, `lesson_offer`, `plan_records`, `boundary_records`, `router.decisions`, the sidecar's `queue` are not reached from any rebuild, replay or upgrade root, by grimp); `adaptive_difficulty.operation` is, and gains only the context variable. `test_decision_records_is_unreachable_from_replay` and `test_a_rebuild_never_calls_the_record_and_keeps_its_rows` pass unchanged. P-shadow isn't named for B3.

**Storage.** From the branch copies: an `ad_slot` record is about 0.3 KB, a check block's `plan_block` about 0.4 KB, and the new facts add about 50-150 bytes to a `plan_block` (0.74-0.99 KB average with them). An `offer_withdrawn` naming one forced item should be about 0.5 KB (an estimate from its fields; none was written on a copy). All are per event, far below B6's slates.

## Tests

- Targeted lane, `-n 4 --dist worksteal` under the 5 GB scope: `scripts/affected_tests.py --base 87ec4085a5` selected 781 files (no fallback to the whole suite); with `test_forced_withdrawal_records`, `test_provenance`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json` and `test_effective_defaults_golden` added, 784 files: **22,059 passed, 52 skipped, 3 xfailed, 0 failed** in 24:48.
- The new file alone: 14 passed.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean.
- `tests/cli_surface.json` unchanged: no CLI parameter changed. `advance_with_context` gained a keyword argument (`parent_record`), `lesson_offer.withdraw`/`supersede` a keyword (`forced`), `OfferHeadMismatch` keyword attributes; every existing caller is unchanged.
- Vault: `Workflows/Inspect Persistent State` gained one paragraph naming B3's records and targets, and ADR-017's "What it replaces" now says the JSONL denial log stays beside the `ad_slot` record (it said "gone if nothing else reads it"; two things do). References regenerated once after the source commit (42 notes changed, one added, `daily_plan/plan_records`; mostly line shifts) and committed; a second run on the clean tree changed nothing. The four validators pass: `validate_vault` (2,279 notes, 2,277/2,277 reachable from Home), `module_validate`, `desktop_validate`, `db_validate_reference` (no errors).

## Open items

- **Background AD denials** (preparation, generation, forecasts, audits) have no plan phase to attach to: they stay in the JSONL log only. A record for them needs a write after the operation's transaction settles, which only the caller knows.
- **An offer an interrupt placed** (IH2 §5 item 3, `place_interrupt_offer`) has no `plan_block` of its own, so its later `offer_withdrawn` has no parent; it names the offer's decision in `facts.offer_decision` and `detail_id`, which is the `plan_interrupt` record's `detail_id`.
- **`why item:<id>` raises** (exit 1, `JSONDecodeError`) when a cold follow-up's stored context is malformed, because it still runs today's scheduler explanation. Pre-existing (main does the same); the test reads the `ad_slot` record by its id instead. B9's reader is the place to make `item:` degrade.
- **A plain `SERVE` verdict** writes no `serve_eligibility` record: the presentation row is its record, and one per serve would be the noise §4 warns about.
- **Trigger attempt** is the newest attempt read in the decision's write transaction, not the key's `as_of` value carried from the chooser; the two differ only if an attempt commits between the decision and its write. Carrying `as_of` on `BlockChoice.provenance` would need `router_runtime.seen` (B5's file).
- **Parent from the attempt's record** links only once B7 writes records with subject `attempt:<id>`; in the P-draw no such records exist, so plan decisions without a withdrawal have no parent.
- **B1's other open items** stand: `job_enqueued` (B7), retention's trigger relaxation, B9's reconstructed reader.

## Unverified

- The desktop app and the phone host weren't run; the records come from the engine, `lesson_offer` and the sidecar's queue handler, which every surface reaches, and the P-draw drives the sidecar handlers.
- A real withdrawal, contest, restraint decision, boundary failure, guard denial or head mismatch on a backup copy: none occurred in the drive (above); each is staged with fakes in the P-tests.
- The durability lane (WAL) wasn't run for the new tests. Every write joins its act's transaction or takes `write_decision`'s short one, and the landing gate runs durability.
- `learner_action`'s supersession (IH3) and the never-shown sweep reach `lesson_offer.supersede`/`release_never_shown`, whose record is the same builder; neither path has its own record test.
