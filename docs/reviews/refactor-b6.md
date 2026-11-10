# Refactor B6: scheduler and serving exclusions

Step B6 of `docs/specs/refactor_strategy_v3.md` (§2.4, design in §3), in arc B ("why x and not y"). Branch `refactor/b6-scheduler-exclusions`, based on main `536963aa30` (B1 landed). It answers the map's O3 (exclusions mostly unrecorded), S15 (a placement check's candidates skipped with no reason), daily-loop bug 2's question (why did this item never reach the slate?) and break 4 (`decision_receipt_id` overloaded).

**Result.** Every slate row (a persisting queue build with a session) gets one `slate` decision record, and `learnloop why` reads it back. FG1's pin names its router decision under its own key. Nothing served changes. The draw-for-draw replay matches main on all three vault copies, apart from the records and the pin's renamed key (below). The shadow rebuild matches main exactly.

## Records added

One kind, written from one place: `scheduling/slate_record.py`, called at the end of `build_due_queue` when it wrote a `scheduler_slates` row (`persist_explanations` and a session).

| Field | What it carries |
|---|---|
| `kind`, `status` | `slate`, `chosen` (an empty slate is `chosen` with no `chosen_ref`, rule `empty_slate`) |
| `subject_kind`, `subject_id`, `detail_table`, `detail_id` | `slate`, the `scheduler_slates.id`, `scheduler_slates`, the same id. A sessionless build (`learnloop review`, the TUI, a plan read with no session) records no slate and no record |
| `chosen_ref` | The head of the returned queue |
| `decided_by` | `composed_offer_v2` (`SELECTION_POLICY`) |
| `rule` | What put the head first, most specific first: `presentation_pin`, `pending_followup`, `check_once`, `seeded_exploration`, `greedy_order` (the head of the ranked order), `composition_order` (the goal quota, requested floor, same-day rotation or a contrast pair moved it up) |
| `alternatives` | The composed candidates after the head, in order: `{ref, score (selection reward), p (the draw's base propensity), lost_by}`, where `lost_by` is `ranked_below` (returned) or `beyond_limit`. Ten are kept, because `scheduler_slate_candidates` already holds every candidate with its rank and scores. The rest are counted in `facts.alternatives_overflow` by rule. The pure builder keeps `provenance.write`'s 50 when given no slate id, but `build_due_queue` never calls it that way |
| `facts.exclusions` | Every item kept off the slate, by rule, as `{n, ids}` with up to ten ids (`IDS_PER_RULE`). The rules are the candidate loop's reason codes (`admission_reason`'s routine and build gates, intent's, `zero_priority`, `device_ineligible`, the probe-reserve gates), plus `teach_back_session_cap` or `teach_back_value_below_minutes_cost` for teach-backs the composition dropped, and `cold_followup_deferred` for revealed cold tasks. A vault id that is not a code token (vault ids are free-form) is counted under `unnamed`, never named, so one odd id never drops the record |
| `facts.placement_check_exclusions` | S15: why each other item of an LO whose placement check is due could not be that check: `retired`, `inactive_state`, `routine_exclusion`, `out_of_timing`, `check_excluded_mode`, `unservable_stimulus`, `no_learning_object`, `lifecycle_put_away` |
| `facts` (other) | `considered_n`, `served_n`, `limit`, `excluded_n`, `session_id`, `greedy_head`, `pinned`, `probe_block_reason` |
| `versions` | `algorithm_version`, `selection_policy` |

There is no learner or item text: ids, numbers and codes only. `provenance.write`'s check enforces it, and a test checks every item prompt is absent.

**The failures each answers.**
- *Why did this item never reach the slate?* (daily-loop bug 2, O3). `why item:<id>` lists the newest slate records naming the item, each with what it says (`chosen`, the rule it lost by, or the rule that excluded it). When the item is not on a slate built now, it adds `excluded_now`: the rule keeping it off, from a build that persists nothing. The second part covers the case the ten-id cap can't name.
- *Why was this LO's check never served?* (S15). `facts.placement_check_exclusions`.
- *Why this head and not the greedy pick?* `rule`, `facts.greedy_head`.

**Reads write none.** The record follows the slate row, which needs `persist_explanations` (the build's existing "serving build" flag) and a session. The first version wrote a record for every persisting build. The targeted lane caught that a plan read with no session then committed on every read, which cooled the plan's memo and re-ran its reading choice: `test_curriculum_c1_fix_round2` L6 (5 choices instead of 1), `fix_round3` M2 (`data_version` moved) and `codex_review_fixes` F3. Tying the record to the slate row fixed all three, and `test_reads_write_no_slate_record` now pins the sessionless case. At this tip no `persist_explanations=False` build serves its result: `why`/`explain_practice_item`, the knowledge map, the facet chart, the staged policy's advisory comparator and the simulator only read. The phone's plan prefetch builds on a read-only attach, so it couldn't write anyway (see open items). So the strategy's "unless reached from a serve" needed no new parameter.

**Where it writes.** `record_slate` builds the record and writes it through `db/stores/provenance.write_decision`, after the build has decided and after its slate row. It never raises: a build or write failure logs `decision record 'slate' not written (trace <id>): <ExceptionType>` and the queue is returned unchanged. `build_due_queue` runs pinned (`pinned_repository_call`), so the write joins that connection in its own savepoint. It takes the lock right after the slate rows the same build already writes, so it adds no new kind of wait on any path.

**Small additions to the leaf** (`provenance.py`): `slate` in `SUBJECT_KINDS`, `is_code(value)` (the token check, public so a writer can count rather than drop), and `read_naming(connection, ref, kind=, limit=)` (records naming a ref as a JSON string, newest first). `router/decisions.py:60` got only a comment pointing from `COUNTED_EXCLUSIONS` to the record.

## `decision_receipt_id`: one meaning each

`accept_probe_offer` takes `router_decision_id` beside `decision_receipt_id`. The learner lane (`causal_probe_offer_action`, `remediation.py:191`) passes the causal probe decision receipt as before, and its pin is byte-identical. FG1 (`followup_run/jobs.py:440` to `admission.commission_and_pin(router_decision_id=)` to `accept_probe_offer(router_decision_id=)`) now pins `router_decision_id` and no `decision_receipt_id` key. Old rows aren't migrated. An FG1 pin written before B6 carries `followup_workflow_id` and no `router_decision_id`, and its `decision_receipt_id` holds a router decision id. The docstring says so. No code in `src` reads the pinned `decision_receipt_id`, and classification reads only `blind_bundle_ids`.

## Proofs

**P-tests** (`tests/test_slate_record.py`, 9 tests; one added to `tests/test_causal_orchestrator.py`; two widened in `tests/test_provenance.py`):
- A persisting build with a session writes one record: `slate:<id>` reads it back with its trace, detail, head, rule, versions, alternatives (`ranked_below` then `beyond_limit`) and `exclusions.retired = {n: 1, ids: [pi_eig_hard]}`. It passes the prose check, and no item prompt appears in it.
- Reads write none: two `persist_explanations=False` builds (with and without a session), `explain_practice_item` and a persisting build with no session leave `decision_records` empty. The same build persisting with a session writes exactly one.
- A record that can't be written changes nothing served: with `write_decision` raising, the queue (ids, priorities, modes, components) equals the one from an identical vault whose record was written, and the warning names the trace.
- S15: an assumed LO's check with its middle item reserved by a cold retry records `placement_check_exclusions.out_of_timing = {n: 1, ids: [pi_diag_mid]}`.
- Units: counts by rule with ten ids and `unnamed`; composition and cold-lane exclusions merged; every head rule; an odd chosen id recorded as `chosen_unnamed`; ten alternatives with a slate row (19 counted `beyond_limit`), 29 without one.
- **Fail-first** (`test_why_names_the_rule_that_kept_an_item_off_the_slate`): the test's body as a scratch script on main's code (`536963aa30`) gives `why item:pi_eig_hard --json`, exit 1, `{"error": "not_found"}`. On this branch it gives exit 0 with `excluded_now: "retired"` and the slate naming it `retired`.
- The FG1 pin carries `router_decision_id` and no `decision_receipt_id`. The learner lane's test still asserts its `decision_receipt_id`.

**Replay.** `scheduling.scheduler` is statically in the replay closure (through `substrate.state_sync`, `params.sensitivity_certificates`, `sim.sweep` and `sim.runner`), so the writer is too. `test_decision_records_is_unreachable_from_replay` is widened on purpose: `_RECORD_WRITERS = {"learnloop.scheduling.slate_record"}` is the only closure module allowed to import the store, and the store is set aside with the leaf. `is_code` joins the leaf names a closure module may import (a pure check). `test_a_rebuild_never_calls_the_record_and_keeps_its_rows` now also counts calls to `record_slate` (both the scheduler's name and the module's) during a live `rebuild_all_derived_state` on the head fixture: zero. `decision_records` stays unreachable from replay: no closure module but the registries names it.

**P-draw** (the router speed stages' harness, B1's adaptation: `drive5.py`, `compare7.py`, `fakes4.py`, `neutralize.py`, `premigrate.py`). Main `536963aa30` and the branch each ran on their own fresh backup-API copy of `~/learnloop-backups/20261109-copy` (stale `probability/.learnloop/state.sqlite` deleted), under `fixtures-local/b6-pdraw/`. Settings: one day, 40 steps at most, the second served item missed, FG1's follow-up authored by the tests' `AuthorFake`, the first stop declined, the mixture seed pinned to the decision id, the router LLM and Decider in-process fakes, and every other AI route at `127.0.0.1:9`. The comparison sets `decision_records` apart (reported by kind, status and rule), and with `SMOKE_B6_PIN=1` maps the FG1 pin's `router_decision_id` back to `decision_receipt_id`, counting each mapping.

| Vault | Served | Router decisions | LLM / Decider requests | Gates | Prompts | Pin keys mapped | `decision_records` (branch) | Result |
|---|---|---|---|---|---|---|---|---|
| arxiv_v2 | 12 | 15 | 15 / 15 identical | 1 identical | 14 identical | 1 | 31 `slate`/`chosen`/`greedy_order` | **IDENTICAL** |
| linear_algebra | 9 | 9 | 5 / 5 identical | 1 identical | 11 identical | 1 | 23 `slate`/`chosen`/`greedy_order` | **IDENTICAL** |
| probability | 14 | 13 | 11 / 11 identical | 1 identical | 16 identical | 1 | 33 `slate`/`chosen`/`greedy_order` | **IDENTICAL** |

Without the mapping, the one difference on each vault is that FG1 pin in `probe_presentations.selection_components_json`. The step mandates that change, and the table shows it is the only one. Every other table's new rows, Today, the plan, every step, submit and feedback, the traces (22, 5, 10) and the removed-row counts matched.

The table is the final run: both sides fresh, on the committed tip `2b249f4c8c`. Two earlier runs, before the alternatives trim and before the slate-row fix, gave the same records (every journey build had a session) and the same result on all three vaults, with one exception. **The harness is not fully deterministic.** On the second run, arxiv_v2's main side differed from its own first run in one `router_objective_traces` row's carried valuations (main against main). probability's branch run differed from main in one of 13 decisions' numeric mixture shares and two traces' `v_residual`. Both are values a later boundary's prefetch fills off the serving path, so they move with thread timing. Two more branch runs on probability, and the final run, matched main exactly.

Each record's JSON is about 2.3 KB after the trim (72,992, 53,837 and 74,659 bytes for 31, 23 and 33 records), from 3.5-6.3 KB before. Every exclusion rule seen was a candidate-loop code: `cold_start_unattempted`, `generated_probe_reserved`, `inactive_state`, `intent_check_waiting`, `lifecycle_put_away`, `reserved_exam`, `retired`, `zero_priority`. No placement check fell due in these journeys.

**No real model, no network.** Every new receipt in all runs came from a fake provider (`fake`, `fake_decider`, `fake_llm`): 0 new receipts from a real model. The net watch logged no non-loopback connect or resolve. It logged 12 subprocesses (6 `powerprofilesctl get`, 6 `git rev-parse`), and no Codex process.

**P-shadow.** `learnloop rebuild --shadow --json` on fresh backup-API copies (`fixtures-local/b6-shadow/`), main against the committed branch tip, compared after masking ULIDs and ISO times:

| Vault | JSON leaves | Differing after masking | Raw differences masked | `schedule_effects` |
|---|---|---|---|---|
| arxiv_v2 | 1,037 | 0 | 18 | equal to main: 9 due dates "moved" by 0.0 days, interval ratio 1.0 (rounding, as at B1) |
| linear_algebra | 999 | 0 | 2 | equal to main, none moved |
| probability | 633 | 0 | 2 | equal to main, none moved |

## Storage

Measured on the P-draw journeys' own rows. Each branch copy's `decision_records` rows were re-inserted 40 times into a scratch table with the same DDL, and the file size measured after `VACUUM`. Rates come from the clean shadow copies' real history: their busiest week of `scheduler_slates`, since one slate row is one record. In the journeys records equal slates (31, 23, 33), all with a session, which is 2.4-2.6 records per attempt.

| Vault | Database | Busiest week (slates) | Bytes/row, 50 alternatives | Growth/month, 50 | Bytes/row, 10 | Growth/month, 10 |
|---|---|---|---|---|---|---|
| arxiv_v2 | 73.6 MB | 90 (2026-45) | 4,433 | 1.7 MB, 2.3% | 4,433 | 1.7 MB, 2.3% |
| linear_algebra | 52.4 MB | 103 (2026-29) | 6,474 | 2.9 MB, **5.5%** | 4,434 | 2.0 MB, 3.8% |
| probability | 37.5 MB | 26 (2026-31) | 8,527 | 1.0 MB, 2.6% | 4,431 | 0.5 MB, 1.3% |

With 50 alternatives, linear_algebra's busiest week would pass §3.7's 5% a month. **Chosen trim: ten alternatives** (`ALTERNATIVES_WITH_SLATE_ROW`), since the slate row already holds every candidate with its rank and scores, and the rest are counted by rule. Ids stay in the exclusions, ten per rule: the record exists to name what was excluded, and its JSON is now about 2.3 KB. A row of that size still takes about one 4 KB page with its indexes, so 4.4 KB is the floor until rows fit two to a page (about 2 KB). Fewer exclusion ids would buy that if a later vault needs it. These are the busiest weeks on record. The last four weeks averaged 151, 0 and 13 slates on the three copies.

## Tests

- **Targeted lane**, `-n 4` under the 5 GB scope. Selection: `scripts/affected_tests.py --files <the 12 changed paths>` (run under the isolated wrapper) picked 1,258 test files (it did not fall back to the whole suite). Added to it: `test_slate_record`, `test_provenance`, `test_causal_orchestrator`, `test_architecture`, `test_cli_help_snapshot`, `test_cli_json` and `test_effective_defaults_golden`, for 1,259 files. The first run (`-m "not slow"`, before the slate-row fix): 19,627 passed, 78 skipped, 11 xfailed and 4 failed in 28:07. Three of the failures were the curriculum memo tests above. The fourth, `test_tui_feedback::test_feedback_submit_uses_codex_grading_when_runtime_ready`, read no grading result within its ten pauses; the TUI's sessionless build was writing a record then. After the fix, the four, `test_slate_record` and `test_provenance` gave 78 passed. Final run on the tip `2b249f4c8c`, slow tests included: **19,655 passed, 78 skipped, 11 xfailed, 0 failed** in 32:37.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check src tests scripts`: clean. `test_architecture` (the function-local edge inventory, the SQL-writer registry): 18 passed.
- Vault: `Workflows/Inspect Persistent State` (the `slate` target, the record, `item:<id>`'s `slates` and `excluded_now`) was the one note made incomplete. References were regenerated after each source commit (`generate_all.py`: one new module note, `slate_record`, plus line shifts) and committed, and a second run on the clean tree changed nothing. The four validators pass: `validate_vault` (2,276 notes, every non-template note reachable from Home), `module_validate`, `desktop_validate` and `db_validate_reference`.

## Open items

- **The phone's plan prefetch** (`daily_plan.py` `_env(prefetch=True)`) builds on a read-only attach, so it writes no slate row and no record. A plan it prefetched and the next request served has no slate record for its eligible list. B2's `plan_block` (with the prefetch's trace in `facts`) is the place to name it.
- **Retention** (B1's item): `alternatives_json` and `facts_json` pruning on old rows still needs the no-update trigger relaxed for those columns.
- **The P-draw harness's nondeterminism** (above): carried and residual valuations filled by off-path prefetches vary between runs of the same code. A landing that needs strict identity should run each side twice, or pin the prefetch completion order.
- **Exclusions outside the build** stay as they were: the quick check and `find_practice` share `serving_exclusions` but write no record. They are learner-initiated selectors, and B8's inventory should decide whether they need one.
- `created_at` is the wall clock (B1's choice), not the build's injected clock, so under a frozen clock a record's time and its slate row's `generated_at` differ.

## Unverified

- The durability lane (WAL) was not run for the new tests. The write is B1's savepoint path, which doesn't depend on the journal mode.
- The desktop and phone weren't run end to end. `get_today_queue`, `next_practice_item` and the plan handler reach the record only through `build_due_queue`, which the P-draw drives through the real handlers.
