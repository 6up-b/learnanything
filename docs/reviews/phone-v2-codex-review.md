# Phone v2, stage V2: Codex review and its fixes

**Stage:** `docs/reviews/phone-v2-v2-today-plan.md` (branch `phone/v2-today-plan`). **Reviewed range:** `5a03164763..373bcd0202` (gpt-6.1-sol; job `20261106-174552-AduQOl`). The reviewer's own run could not start its tests (`systemd-run --user --scope`: "Operation not permitted" on its user bus), so its findings were traced from source. Every one was reproduced here first: a test that fails on `373bcd0202`'s code (run with `git archive 373bcd0202 src migrations` on `-o pythonpath=`, so the worktree's `src` is not imported) and passes on the fix.

## Findings

| Id | Severity | Title | Verdict | Commit | Test (fails on `373bcd0202`, passes on the fix) |
|---|---|---|---|---|---|
| F1 | High | A phone write naming no open session bypasses ownership | **Fixed** | `98ecc0dca0` | `tests/test_mobile_v2_review_fixes.py::test_f1_*` (on the base: `plan_keep_going{stop}` with no session answered 200 while the desktop owned the session) |
| F2 | Medium | `plan_learner_pick` bypasses the device filter | **Fixed** | `98ecc0dca0` | `test_f2_the_phones_pick_of_a_held_item_is_refused_before_anything_is_served` (base: the image item was served to the phone, presentation written) |
| F3 | Medium | The follow-up panel is not connected to real phone responses; a held desktop miss reopened on the phone is unheld | **Fixed** | `98ecc0dca0` | `tests/test_mobile_v2_followup.py` (base: no `followup` key and the repairs, causes and worked answer in the phone's bundle of a held attempt; a phone miss opened no workflow) |
| F4 | Medium | A stop drawn at a phone boundary strands work held for the desktop | **Fixed** | `98ecc0dca0` | `test_f4_a_stop_drawn_past_held_work_keeps_that_work_for_the_desktop_and_closes_after_it` (base: the phone's step was `done`, the plan closed with the held item unresolved) |
| F5 | Medium | A randomized check restored from its checkpoint offers hints | **Fixed** | `98ecc0dca0` | vitest `src/today/Today.plan.test.tsx` "a randomized check reopened from its checkpoint … stays without help" (fails with the fix's line disabled); pytest `test_f5_*` |
| F6 | Medium | Ownership is checked before the step's slow work, not at its commit | **Fixed** | `98ecc0dca0` | `test_f6_a_desktop_step_whose_session_moved_during_its_work_commits_nothing` (base: the desktop's step committed after the phone adopted mid-step) |

No finding was rejected.

## What changed

### F1: a phone's write naming no open session (`handlers/sessions.py`, `handlers/daily_plan.py`)

- `refuse_moved_session` keeps the desktop's rule exactly (a None origin naming no session, an unknown one or an ended one answers as before: byte-identical at a None origin).
- A **phone** write naming no open session (none, unknown, ended) is refused with `session_moved` (the open session's snapshot in `details`) while another device owns the open session. With no session open, or the phone's own, it goes through, so the pre-session minutes chip still works (`test_f1_with_no_session_open_the_phones_minutes_chip_goes_through`). The phone's existing `session_moved` handling shows the handoff.
- `next_plan_item` from a phone is always checked as a write: the phone never peeks (§4.5), and a read at a finished block crosses a boundary and writes its decision.
- `plan_learner_pick` installs the commit-time check too (below).

### F2: the pick door (`handlers/daily_plan.py::_refuse_held_pick`)

A phone's `plan_learner_pick` asks the same `PlanStepFilter.holds` the step uses, before the cold-check revalidation and anything else is served or written: `desktop_only` (with the PR-6 reason) or, for a generated probe, `generated_probe_reserved`. The desktop (no filter) is never refused (`test_f2_the_desktops_pick_of_the_same_item_is_served`).

### F3: the follow-up panel through the phone's handlers (`followup_serve/gates.py`, `followup_serve/workflow.py`, `attempts/post_attempt.py`, `handlers/{practice,feedback,diagnosis_card,followup}.py`, `followup_run/serving.py`)

- **What a workflow holds is held on every device.** `get_feedback`, the door bundles (contest, rating, clarification), `diagnosis_status` and `record_answer_display` apply FG1 §6.0's hold whatever the origin. Before, a phone reopening a desktop miss whose feedback was held got the worked answer, the causes and the repairs before the pending question (an independence leak), and its diagnosis poll showed the card.
- **The phone's bundle carries the workflow's read and the marks panel**, as the desktop's: `test_f3_the_phones_bundle_is_the_desktops_held_and_released` asserts the two bundles are equal, held and after *Show anyway* from the phone.
- **A phone miss opens its own workflow** (spec §8's V2 row: "the follow-up panel without probes (held feedback, *Continue without it*, *Show anyway*, marks)"; P4 in the stage review expects it). `followup_surface` answers `phone` for a phone origin, and `WORKFLOW_SURFACES = {desktop, phone}` is the one set both `open_for_attempt` and the pipeline check, so the workflow row records `surface = phone`. The TUI (no surface) stays on the predecessor's path.
- **The question stays the desktop's until V3.** Every phone door still refuses a generated probe (the step filter holds it; `get_practice_item` answers `generated_probe_reserved`; `followup_next` is not allowlisted). A ready or waiting question's line on the phone says *Your next question on this is waiting for the desktop.* (`PHONE_HANDOFF_LINE`, FG1 §10's hand-off line), in the bundle and in `followup_status`; every other field equals the desktop's read.
- Spend: the generation a phone miss starts is FG1's, the same journey's on the desktop (D2), on FG1's worker and budgets. Nothing new on the host (D6).

### F4: a stop drawn past held work (`daily_plan/engine.py`)

- At a boundary a device crossed while work it left for the desktop is open, a stop the chooser drew while work was feasible is **that stop**: logged once, with its propensity, as before (router decision, `block_chosen` stop receipt, the stop arm's objective record).
- **The plan stays open** while the held work is open. The stop receipt carries `closes_after_held: {replans: N}`, and no device draws again: the phone's Next answers the held step, and the desktop's Next serves the held block. When nothing is open, the next step **closes the plan on that stop** (its status and reason) with no new decision (`_stop_pending`, `_close_on_pending_stop`).
- A minutes tap that re-plans (the desktop's own way to re-open a stopped plan) lets the pending stop lapse (`test_f4_the_pending_stop_lapses_when_a_minutes_tap_re_plans`); *Done for today* closes the plan as always.
- Only a device writes the key, so for every existing record `_stop_pending` is None and the desktop's path is unchanged.

### F5: the cold restore (`handlers/practice.py`, `daily_plan/engine.py::open_randomized_check`, PWA `practice/QuestionScreen.tsx`)

A phone's session serve of an item that today's plan holds as its open randomized check (RO5) carries `noHelp: true` (a phone origin only; the desktop's reply has no new key). The question screen offers no help when either the step or the serve says so, so a question reopened from its checkpoint (a reload, another device) is as cold as the step that opened it, and nothing names it.

### F6: the check at commit (`handlers/daily_plan.py::OwnerCheckedRepository`, `Repository.in_atomic`)

- A plan write that names an open session (and a phone's sessionless write) checks again **inside every transaction it begins**, under the write lock (`BEGIN IMMEDIATE`): owner and generation (`expected_generation`), so a handoff during the step's slow work (the queue build, a boundary's model call) refuses the step with `session_moved` and commits nothing, even if the session came back.
- No write transaction is held across model work: the check rides on the transactions the engine already opens.
- A nested `atomic()` (a savepoint) checks nothing: its transaction was checked when it began, and AD's serve receipts run under AD's read guard, which refuses the `sessions` table (found while building: without this the desktop's AD serve receipts were lost, `test_f6_nothing_changes_for_a_step_whose_session_stayed` pins it).
- The policy's background work and AD's scheduling keep the plain repository: they are no step of the session's.

## Persisted meaning and the playbook

- No table, column or migration. `table_roles.py` unchanged.
- New values, only from a phone: `followup_workflows.surface = 'phone'` (no reader filters on it; FG1's identity keys burns by the serving surface, which stays the desktop's); the stop receipt's and router decision's `closes_after_held` key; `noHelp` on a phone serve.
- **Ruling: no successor.** Nothing the desktop serves, primes or records at a None origin changed. A phone miss's workflow is FG1's own behaviour (`mvp-0.45`) at a second door that now has FG1's held UI, as the owner-accepted V2 row asks; its kill switch is FG1's `followup.generate_and_serve`, and the phone plan's is `mobile.phone_plan`. The pending stop changes when a phone-drawn stop closes the plan, not what it decides or logs; `daily_plans` is a workflow table that replay never reads.

## The desktop at a None origin

Every change is behind a phone origin or a device, except two that read only: the commit-time check (one `SELECT` on `sessions` in a transaction the step opens anyway, never inside a savepoint) and `_stop_pending` (None for every record without the phone's key). `test_a_none_origin_never_enters_the_device_branch`, the desktop RPC contract and serializer snapshots pass unchanged.

## Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time, the heavy run behind `flock /tmp/learnloop-fullsuite.lock`. Every Python CLI ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

- **Setup:** `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile`.
- **`lint-imports --no-cache`:** **43 kept, 0 broken** (before the commit and after the last fix).
- **Reproduction on the base** (`373bcd0202`'s `src` and `migrations` from `git archive`, `-o pythonpath=` to them): the two new files failed 12 of 17 (F1, F2, F3, F4 behaviourally, F5's new API, F6 "DID NOT RAISE"); F4's test, reordered, fails on the base at the phone's step being `done`. The F5 vitest fails with the fix's line disabled (1 failed, 12 passed) and passes with it.
- **Targeted pytest** (`-n 6`, 309 files, behind the lock: every test file that names the plan RPCs, `daily_plan`, the FG1 packages and RPCs, `run_post_attempt_pipeline`, `get_feedback`, `diagnosis_status`, `record_answer_display`, `trigger_regrade`, the ownership helpers, `get_practice_item`, `learnloop_mobile` or `hypothesis_marks`, every `tests/test_mobile_*.py`, and the contract set): **14752 passed, 28 skipped, 1 failed**, in 58 min.
  - The failure, `test_teacher_te1b_suggestions.py::test_start_opens_a_lesson_whose_origin_is_the_decision`, was this fix's: a test's minimal context has no `request_origin`, which `refuse_moved_session` now read before returning. It reads it with `getattr` (a missing origin is the desktop's); then that file, the two new files, `test_mobile_v2_plan.py`, `test_sidecar_tutor_qa.py`, `test_session_ownership.py` and `test_mobile_handoff.py`: **116 passed**.
  - `test_rofu_carried.py`, which the stage review recorded as failing on its base too, passed in this run.
  - The contract set inside it: `test_sidecar_measurement.py` (display-label audit), `test_codex_lockdown_round3.py` (process-launch allowlist), `test_codex_lockdown_frozen.py` (frozen cycles), `test_cli_help_snapshot.py`, `test_architecture.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_config_refactor.py`, `test_public_tip_guards.py`, `test_sqlite_file_copies.py`, `test_module_catalog_inventory.py`, `test_hypothesis_marks.py`, `test_mobile_allowlist.py`. After the references were regenerated: `test_module_catalog_inventory.py`, `test_public_tip_guards.py`, `test_sidecar_measurement.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_frozen.py`, `test_codex_lockdown_round3.py`: **52 passed**.
  - New: `tests/test_mobile_v2_review_fixes.py` (12), `tests/test_mobile_v2_followup.py` (6). Changed: `tests/test_followup_workflow.py` (the TUI case renamed; the phone now has its own surface).
- **Durability** (the commit-time check reads inside `BEGIN IMMEDIATE`): `pytest -m durability tests/test_mobile_two_process.py`: **2 passed**; `pytest --durable-sqlite tests/test_mobile_v2_review_fixes.py tests/test_mobile_v2_followup.py`: **18 passed**.
- **`apps/learnloop-mobile`:** `npm run typecheck` clean; `npx vitest run --maxWorkers=4 src/practice src/today`: **6 files, 109 passed**; `npm run build`: built. Nothing under `apps/learnloop-tauri` changed, so no desktop vitest, build or `cargo check`.
- **References:** `module_generate.py` then `module_validate.py`: **PASS** (41453/41453 links); `desktop_generate.py` then `desktop_validate.py`: **passed** (322/322, no change). No schema change, so no DB reference run.
- **No paid or live call.** FG1's author and grader are fakes in every test.

**Test files run, for reading the landing gate against:** the 309 targeted files (reproducible with the `git grep` above), `tests/test_mobile_two_process.py` in the durability lane, the two new files under `--durable-sqlite`, and every vitest file in `apps/learnloop-mobile/src/practice` and `src/today`.

**Process note.** One `python3` heredoc printing a constant ran outside `env -i` (no import, no file read); every other Python and CLI call ran isolated.

## Open questions

1. **Phone misses hold feedback before V3.** FG1 §10 said "the phone's feedback doesn't hold what it can't follow with a probe"; spec_mobile_frontend_v2's V2 row (accepted Nov 6) lists the held feedback, *Continue without it* and *Show anyway* for V2, and this fix follows the newer spec. Until V3, a phone miss's question is answered on the desktop (or the learner taps *Show anyway* / *Continue without it*). If the owner prefers FG1 §10's line until V3, the smallest change is `followup_surface` answering None for a phone origin again; the hold on desktop misses read from the phone (the leak) stays fixed either way.
2. **A sessionless phone write while the desktop holds a stale open session** is now `session_moved` (the phone offers the handoff). That includes the pre-session minutes chip while the desktop app has a session open.

## Re-review

**Reviewed range:** `373bcd0202..60f64272f9` (gpt-6.1-sol; job `20261106-195557-AuEuMp`). F1-F4 were confirmed fixed; F5 and F6 were reopened, and F7 is new (introduced by F4's fix). Each was reproduced first: `tests/test_mobile_v2_rereview_fixes.py` run on `60f64272f9`'s `src` and `migrations` (from `git archive`, `-o pythonpath=` to them) failed **6 of 7** (the seventh is the "nothing changes" control), each for the finding's reason (F5: `KeyError: 'noHelp'` on the next day's serve, and the engine had no way to name the checkpoint's presentation; F6: the phone's write answered 200 after the session went to the desktop and back; F7: `KeyError: 'stopOffer'`, `plan_keep_going` returned the unchanged plan with the stop still pending, and *Done for today* closed the plan with the held item unresolved). All 7 pass on the fix.

### Findings

| Id | Severity | Title | Verdict | Commit | Test (fails on `60f64272f9`, passes on the fix) |
|---|---|---|---|---|---|
| F5 | Medium | A randomized check restored on a later day offers hints (coldness read from today's plan only) | **Fixed** | `bc80387a84` | `test_f5_a_check_restored_from_its_checkpoint_the_next_day_stays_cold` (engine, a real RO5 check, the clock a day on), `test_f5_the_phones_serve_of_a_check_restored_the_next_day_says_no_help` (host) |
| F6 | Medium | A phone's sessionless plan write does not pin the open session's generation | **Fixed** | `bc80387a84` | `test_f6_a_phones_sessionless_write_whose_session_moved_and_came_back_commits_nothing`; control `test_f6_a_phones_sessionless_write_with_its_session_where_it_was_goes_through` |
| F7 | Medium | A stop drawn past held work removes the phone's stop offer and *Keep going* | **Fixed** | `bc80387a84` | `test_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone`, `test_f7_keep_going_overrides_the_pending_stop_in_place_and_keeps_the_held_work`, `test_f7_done_for_today_on_the_pending_stop_leaves_the_held_work_for_the_desktop`; vitest `src/today/Today.plan.test.tsx` "a stop drawn while work waits for the desktop is offered too, and Keep going overrides it" (fails with the `PlanToday` condition reverted: 1 failed, 13 passed) |

No finding was rejected.

### What changed

- **F5** (`daily_plan/engine.py::open_randomized_check`, `handlers/sessions.py::checkpoint_plan_presentation`, `handlers/practice.py`). A phone's session serve reads the presentation the checkpoint's draft answers (the draft's own retry key, its item) and asks `open_randomized_check(..., presentation_id=)`: a presentation of this item whose origin is RO5's check and that no attempt has answered (`bindable_presentation`) is cold whatever its day or plan. Today's lookup stays for a question opened without a draft. The desktop's serve is unchanged (the branch is a phone origin's).
- **F6** (`handlers/sessions.py::refuse_moved_session`). The sessionless phone branch pins the open session it was accepted against and its generation; the check at each transaction requires that generation while that session is still the open one (a session opened since is checked for its owner, as before). A None origin never enters the branch.
- **F7** (`daily_plan/engine.py`; PWA `today/PlanToday.tsx`, `api/phone.ts`).
  - The held step carries `stop_offer: {stop_reason}` while a stop drawn past held work is pending (only then; the boundary that draws it answers with the reloaded record, so the offer comes with the draw). The phone shows it as the done step's stop offer: the done line, the count of what waits for the desktop, *Keep going* and *Done for today*.
  - *Keep going* (`keep_going` on an open plan with a pending stop) overrides it **in place**: the override is recorded as the desktop's (RO0 row 7, `via: keep_going`), and the plan gains the desktop's *Keep going* minutes (`plan.keep_going_minutes`, the existing setting) past what it holds, through the same re-split a minutes tap makes (`_resplit`, extracted from `set_minutes` unchanged; its re-plan entry says `via: keep_going`). The re-plan lets the pending stop lapse, so the next boundary decides afresh; the stop's receipt, its probability and the held blocks stay as they were.
  - *Done for today* from a device on a pending stop takes that stop: the plan stays open for the held work and closes on the stop after it (F4), instead of closing as `learner_stopped` with the held work stranded. The desktop's *Done* is unchanged.

**Persisted meaning.** No table, column or migration. New values only on a phone's records: `split_json.replans[].via = "keep_going"` (an override in place) and a `session_receipts` stop override for an open plan; `daily_plans` is a workflow table replay never reads. The ruling stays **no successor**: nothing the desktop serves, primes or records at a None origin changed (`set_minutes`' re-split is the same code, moved).

### Gate (this step; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time. The targeted run did not take `flock /tmp/learnloop-fullsuite.lock`: another stage's landing held it for the full suite, and this step's gate names targeted runs as needing no lock (the 5G cap holds). Every Python CLI ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

- **Setup:** `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile`.
- **`lint-imports --no-cache`:** **43 kept, 0 broken**.
- **Reproduction on the base:** above (6 of 7 failed; the vitest fails with the fix's condition reverted).
- **Targeted pytest:** the 192 files below (`-n 6`): **4807 passed, 23 skipped, 0 failed** in 43 min 46 s. Then, after the module reference was regenerated, the new file, the four RO5 files the first list missed (`test_ro5_calibration.py`, `test_ro5_codex_review.py`, `test_ro5_picks.py`, `test_ro5_successor.py`) and the contract tests that read the references or the CLI (`test_module_catalog_inventory.py`, `test_public_tip_guards.py`, `test_sidecar_measurement.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_frozen.py`, `test_codex_lockdown_round3.py`): **101 passed**.
- **`apps/learnloop-mobile`:** `npm run typecheck` clean; `npx vitest run --maxWorkers=4 src/practice src/today`: **6 files, 110 passed**; `npm run build`: built. Nothing under `apps/learnloop-tauri` changed (no desktop vitest, build or `cargo check`).
- **References:** `module_generate.py` then `module_validate.py`: **PASS** (41463/41463 links); `desktop_validate.py`: **passed** (322/322, reproducible byte-for-byte). No schema change, so no DB reference run.
- **No paid or live call.**

**Test files run:** the 192 files of the targeted run (every test file naming `set_minutes`, `set_plan_minutes`, `keep_going`, `plan_keep_going`, `stop_today`, `open_randomized_check`, `refuse_moved_session`, `draft_plan_presentation`, `DEVICE_HELD_STEP`, `_stop_pending`, `most_recent_open_session`, `get_practice_item` or `session_moved`, every file importing `daily_plan.engine` or naming `next_plan_item` / `get_daily_plan`, and the contract set: `test_mobile_allowlist.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_cli_help_snapshot.py`, `test_sidecar_measurement.py` (display-label audit), `test_codex_lockdown_round3.py` (process-launch allowlist), `test_codex_lockdown_frozen.py` (frozen cycles), `test_architecture.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_config_refactor.py`, `test_public_tip_guards.py`, `test_sqlite_file_copies.py`, `test_module_catalog_inventory.py`, `test_session_ownership.py`, `test_mobile_handoff.py`, `test_mobile_two_process.py`, every tracked `test_mobile_v2_*.py`, `test_ro5_checks.py`, `test_ro5_stop_coin.py`), the second batch above, and the vitest files in `apps/learnloop-mobile/src/today` and `src/practice`. New: `tests/test_mobile_v2_rereview_fixes.py` (7). Changed: `tests/test_mobile_v2_review_fixes.py` (F5's fake takes the new keyword), `src/today/Today.plan.test.tsx` (one test).

**Process note.** One `python3 -c "print(1)"` ran outside `env -i` (no import, no file read); every other Python and CLI call ran isolated.

### Left for the stage

- **Merging main.** V1 has landed on main (`23ce859c16`); this fix step's rules forbid merging, so the merge of main into `phone/v2-today-plan` (with the expected `daily_plan` merge work against TE3b and the router speed stage) is the next step's, before the landing gate.
