# Phone v2, stage V2: Today is the plan; practice and feedback parity

**Spec:** `docs/specs/spec_mobile_frontend_v2.md` §8's V2 row (detail in §2.1-§2.3, §4, §5.6, §7; owner decision D1: the phone's Today serves the shared desktop plan, reversing M2a's "phone shows the queue"). **Branch:** `phone/v2-today-plan`, from `phone/v1-shell`'s tip `5a03164763` (V1 had not landed on main when this stage ended; main had not moved since `1c12763372`, so there was nothing to merge). **No migration, no successor, no new dependency, no model call of its own.**

## Commits

| Commit | What |
|---|---|
| `f10149a271` | Host and sidecar: the V2 allowlist row, the step filter, the RO5 deferral, the `phone_plan` surface, PR-4's open list closed, the kill switch; host journey tests J1-J6, the two-process plan test |
| `30213eb580` | PWA: Today is the plan, practice and feedback parity, `App.test.tsx` split by journey; the desktop's answer-exposure gate split into a pure module the phone shares |
| (this commit) | This review, the spec's "As built" note, the regenerated references (and the desktop catalog's three pinned counts, for the one new desktop module) |

## 1. What was built

### 1.1 Host and sidecar

- **The allowlist's V2 row** (`learnloop_mobile/allowlist.py`, milestone `V2`), default-deny as before:
  - J1: `get_daily_plan`, `get_today_headline`, `get_start_summary`, `next_plan_item` (**long**: a job under its `request_id`, so a boundary that waits on RO4's LLM policy gets the 15 s wait and then `202`), `set_plan_minutes`, `plan_keep_going`, `plan_more_new`, `plan_reading_ended`, `plan_learner_pick` (its `proposal_id`/`source_exercise_import_id` refused: Find practice is the desktop's).
  - J4: `router_objective_explain` (read only).
  - J2: `record_answer_display`, `record_diagnosis_feedback`, `trigger_regrade` (**long**, and constrained to the contest: `learner_reason` and `contest_id` are required, and the host requires `request_id == contest_id`, so a retry records and queues the contest once), `rate_followup`.
  - J3 without probes: `followup_status`, `followup_continue_without`, `followup_show_anyway`, `record_hypothesis_exposure`, `record_hypothesis_mark`.
  - J16 partial: `practice.record_hint_reveal`.
  - Not allowed (pinned by a test): `followup_next` (it opens a generated probe: V3), the adaptive hint jobs (§2, item 5), `lesson.turn`, `reader.ask`, `ask_tutor_question`.
  - The generated `retryPolicy.json` and `phoneMethods.ts` follow (`LEARNLOOP_UPDATE_PHONE_CONTRACT=1`), and so does the digest, so a cached V1 app offers the reload.
- **The step filter** (§2.2):
  - `scheduling/device_eligibility.py` adds `PlanStepFilter`: PR-6's rules, the diagnostic check the session left for the desktop (`left_for_desktop`), and a generated FG1 probe (until V3). `daily_plan/engine.py`'s `PlanEnv` gains `device` (None for the desktop).
  - The build, the pool, the router's support and every decision's candidates are the desktop's. Only the serving door skips: `advance_with_context` serves the first open block, in plan order, with an item the device can show, in `next_item`'s order (served, follow-ups, position). What it passes over stays assigned and is counted (the reply's `device: {surface, deferredCount, readingsWaiting}`).
  - When every open block is held: a **read never crosses a boundary** (it answers a `held_for_desktop` step); the **phone's Next crosses one**. A boundary under a device with **nothing feasible waits** (the held work is the desktop's) instead of closing the plan; this case has no draw, so nothing depends on an action. A stop the chooser **drew** while work was feasible is that stop, on either device.
  - **The day's randomized check comes first on every device**: while it waits for the desktop the phone crosses no boundary, so no later decision's draw (a stop) can leave it unanswered. The held step names the first held item, and the phone's **Skip** is the desktop's own skip link for it.
  - **AD's slot draw is not asked under a device** (§2, item 3).
  - Readings wait for the desktop until the phone has its Reader (§2, item 2).
- **RO5 (J6):** a check a phone's step passes over writes `item_device_deferred` once (block, item; with its origin, reason, surface and session), and `router_objective/checks.py` resolves an unanswered one `not_answered:device_deferred` at the day's end. It is not completed, exactly as `not_answered`: the rate is unchanged and `by_status` names it. The draw, its `r_L` and its propensity are untouched, and nothing re-draws it for the phone (`test_mobile_v2_checks.py` compares the assignment rows of a phone day and a desktop day).
- **Decisions under a phone origin** record `surface = phone_plan` and `device: {surface, device_policy}` (`device_eligibility_v1`, or `off` with `practice.device_eligibility_enabled` off) on the `block_chosen` receipt, the `router_decisions` row and its inputs (`router/plan_log.py`: block, interrupt). The desktop's rows carry neither, so their snapshot hashes are unchanged.
- **§5.6, PR-4's open list:** `refuse_moved_session` (`handlers/sessions.py`) refuses a session-keyed write from the device that does not own the session with `session_moved`, at:
  - every plan write that names a session: `next_plan_item` with `serve` or a skip, `plan_keep_going`, `plan_reading_ended`, `set_plan_minutes`, `plan_more_new{confirm}`, `plan_learner_pick` (before a proposal's selection is recorded);
  - `ask_tutor_question` with a session (before anything is asked or written);
  - `lesson.suggestion_respond` with a session.
  - Reads never check. An ended or unknown session answers as before (those writes never required an open session), so the desktop's own session answers exactly as it did. The desktop's `sessionMoved.ts` already turns `session_moved` into *This session continued on your phone*.
- **Freshness:** the phone's plan writes, `trigger_regrade` and `followup_continue_without` are `host_mutation`s, so the desktop's Today moves on the next token poll (P3). A no-op for a None origin.
- **D6:** under the host's secondary attach the plan runs none of its background work: the deliverable refresh, AD's preparation, forecasts and commission generation, and the figure prefetch stay the desktop's.
- **Kill switch `mobile.phone_plan`** (`mobile.toml`, default on): off, the plan's methods answer `409 phone_plan_off`, `GET /api/v1/meta` says `phone_plan: false`, and the phone's Today is M2a's queue.

### 1.2 PWA

- **`today/PlanToday.tsx`** (J1, J4, J5): the plan's sentence (`today/planWords.ts`), `why?` in a sheet with the block's details and *how was this chosen?* (`router_objective_explain`, asked only when tapped), the router's plain line with `details` in a sheet, the one count *N questions are waiting for the desktop* (and readings), minutes chips before a session, one primary action (Begin, Next; with the plan done, Keep going), *Choosing what's next…* while a step is with the host, *Skip it* for what waits, *Done for today* (the stop, then the end of the session). M2a's queue (`today/TodayScreen.tsx`) is Today only with the plan off or the kill switch.
- **The plan's Next** is always a serve under the phone's origin, as a long job (`nextPlanItem`). The phone makes no peek (§2, item 4).
- **`practice/QuestionScreen.tsx`:** the answer binds to the step's plan presentation; an item's own hints behind *Hint*, whose sheet says first that the answer then counts as answered with help (◌); a reveal is recorded (`practice.record_hint_reveal`), shown inline under *◌ with help* and counted at submit (`hintsUsed`, `authoredHints`, the first-hint marker). No help on the randomized check (the step's origin), a check on your own or a cold follow-up lane, and nothing says why.
- **`practice/FeedbackScreen.tsx`** and **`FeedbackParts.tsx`** (J2, J3, J4):
  - the follow-up panel without probes: its line (*Preparing a question on this…*), the held explanation with *Show anyway*, *Continue without it*, the router's line; it polls `followup_status` every 2 s while pending or held, and a release re-reads the bundle with `recordOpen: false`;
  - the optional marks (FG1c), with the list's display event once;
  - *Show the full answer*: a reveal, shown only while a recorded display covers it, through the desktop's own gate (`screens/feedback/answerExposureGate.ts`, split out pure from `answerExposure.ts`); hidden on page hide, freeze and blur, renewed while the learner is there; not offered while held or when the record doesn't say which answer the grade stands on;
  - *I think I was right*: one optional line, one key per contest reused on a retry (`trigger_regrade` as a job under that key);
  - *Choosing what's next…* under Next.
- **V1's carried items:** Feedback gets the back chevron (to Today, serving nothing; the feedback stays one Next behind). The top bar's **+** stays. `App.test.tsx` is split by journey over a shared fake host (`src/test/fakeHost.tsx`): `today/Today.queue`, `practice/{Question,Recovery,Feedback.diagnosis}`, `shell/Handoff`, `capture/Capture`. Its 94 `it` cases moved unchanged except two (§2, item 11).

### 1.3 Tests added or changed

- **pytest**
  - `tests/test_mobile_v2_plan.py` (13): J1 through the real host on a fresh plan vault with an image-prompt item and the desktop as a `SidecarContext` on the same database (the shared record, the held item counted and served next by the desktop after a handoff, a read that writes no decision, `phone_plan` and the device rules on decisions, the token bump, the long method and its retry); J5 (the end of the plan, Keep going, Done); §5.6 (seven plan writes refused to the non-owner, reads not, the owner's write goes through; tutor and lesson-suggestion writes; ended and unknown sessions as before); the kill switch and meta; **a None origin never enters the device branch** (every device-only function raises if reached).
  - `tests/test_mobile_v2_checks.py` (5): J6 with RO5's own fakes: the check held, recorded once, never served on the phone, never re-drawn (the assignment rows equal a desktop day's), served by the desktop's next Next; `not_answered:device_deferred` at the day's end with the rate unchanged; the phone's Skip resolves it `skipped`; an eligible check is served on the phone as an ordinary item.
  - `tests/test_mobile_v2_feedback.py` (6): J2-J4, J16 through the host (display rows once per id, the contest's key, the follow-up read and its ways out, `followup_next` refused, the explanation, a hint reveal and the other device refused).
  - `tests/test_mobile_two_process.py` (+1, durability lane): the phone (a child process running the real host) and the desktop (the parent's primary sidecar) take turns on one plan, handing the session over each turn: no item served twice, every answer recorded once, each decision on its device's surface.
  - Changed: `test_mobile_allowlist.py` (the V2 row, its constraints, what stays out), `test_mobile_rpc.py` and `test_mobile_host_auth.py` (the M2 row unchanged beside V2), `test_mobile_phone_contract.py` (the reply journey reaches every new method but `record_hypothesis_mark`, pinned by `tests/test_hypothesis_marks.py`; the contest's grader is an outage, so no model is asked).
- **vitest**
  - `src/today/Today.plan.test.tsx` (11): J1 (the sentence, Begin, the presentation bound, Feedback's Next, the count and Skip, the back chevron, a minutes chip), J5, J4, J16 and J6, and the deny-list over Today's plan, held and done states, the hint sheet and the new feedback parts.
  - `src/practice/Feedback.parity.test.tsx` (8): the held panel and its re-read, Continue without it, the router line, the marks and their display event, the full answer after its row, an unrecorded answer never shown, the contest's key, no contest on a self grade.
  - The split files, `src/api/contract.test.ts` (the new wrappers' requests, recorded into `contract/*.json`), and `shell/{Shell,a11y}.test.tsx` (their fakes answer the plan as off).

## 2. Where the spec was not built as written, and the smallest way to finish

1. **"The step goes to the next eligible block in plan order."** The engine decides blocks one at a time; there is no later block until a boundary. Built: the first open block with something the phone can show; otherwise the phone's Next crosses one boundary per step (a read never does), a boundary with nothing feasible waits, and the randomized check stops the phone from crossing while it waits (the check comes first on every device, as on the desktop). The phone's way past a held check is the desktop's own skip link (*Skip it*). Without that rule, a stop drawn at a phone boundary could leave the day's check unanswered, so its completion would depend on an action draw (found by `test_mobile_v2_checks.py` while building).
2. **Readings wait for the desktop in V2.** §2.2 says a reading block is never ineligible "because the phone has a Reader"; the Reader is V4. Smallest finish (V4): drop the `is_reading` hold in `_device_block` and the boundary branch, and render the reading step.
3. **AD's slot draw is not asked under a device.** AD's support is computed inside `ad_slot`; letting it draw and then refusing an ineligible choice would make its logged probabilities depend on the device. The planned item is served, as when AD is unavailable for a slot, and nothing of AD's is written. Smallest finish: pass the device's predicate into `ad_slot.open_slot` so the support is restricted before the draw (and logged as such).
4. **No peek (§4.5).** `next_plan_item{serve: false}` can cross a boundary and write its decision, so the phone never peeks; Next shows *Choosing what's next…* (the §4.5 fallback).
5. **Hints with their surfaces (J16 partial).**
   - `help_assists.surface` has a CHECK constraint (`practice`, `workbench`, `guided_redo`, `tutor`), so writing `phone_practice` needs a table rebuild, a migration V2 does not plan. The reveal row keeps `practice`; its device is the attempt's: the row names the submission, whose attempt's `entry_surface` is `phone_practice`. Smallest finish: a migration widening the CHECK, and `record_authored_reveal(surface=practice_surface(origin))`.
   - The adaptive hint jobs (`practice.request_hint`, `hint_job`, `cancel_hint`) are not allowlisted: they are in-memory threads of one sidecar (`HintJobs`), not the host's durable jobs, and they spend. Smallest finish: run `request_hint` as a long host job whose worker waits for its thread, with `hint_job` reading the durable row.
6. **"Reading-progress writes that carry a session" and "lesson turns bound to a session"** (§5.6): none carries a practice session (`reader.mark_section_progress` has none; `lesson.turn` has a `screen_session` only), so there is nothing to check; the lesson's concurrency is V6's `expectedTurn`. `reader.ask` has no session either (V4/V5).
7. **The "predicted gain" line (J5)** is not shown: the desktop's Today shows no such line on its done screen either, and the plan DTO carries none.
8. **A feedback reopened from the fragment** (V1's item 1) is still not reopened: the plan's Next and the checkpoint cover a reopened app. Smallest finish: `#/today/feedback/<attempt>` opens `get_feedback{recordOpen: false}`.
9. **The kill switch lives in `mobile.toml`** (the host's machine-local config, where `mobile.*` keys are), not in the vault's config: it is the host's door. It is a kill switch, not a decision parameter, so `parameter_registry.py` is unchanged (it lists no `mobile.toml` key).
10. **The phone's plan words** (`today/planWords.ts`) follow the desktop's `app/todayPlan.ts`, which the phone cannot import (it imports the desktop's Tauri client; the import walk refuses it). Smallest finish: move the desktop's pure sentence helpers into a Tauri-free module both import.
11. **Two `App.test.tsx` cases changed:** "names no plan RPC" is now "with the plan off, serves the queue and asks the plan nothing more" (V2 reverses its premise); one diagnosis case now drops the cached session before its second half, which had begun a session in the instant before the cached one loaded (a race; Today now reads the plan first).
12. **V1's item 12** (the question's own grading line beside the connection line) is unchanged.
13. **TE3b** had not landed; its lesson offers as plan steps are V6's, as §8 says.

## 3. Persisted meaning and the playbook ruling

- No table, column or migration.
- New only under a phone origin: `attention_block_events` of kind `item_device_deferred` (the fold ignores unknown kinds; the RO5 ledger reads it), and decisions with `surface = phone_plan` and a `device` entry.
- `checks.Ledger.resolve` names `not_answered:device_deferred` where it said `not_answered`, only when that event exists; the completion rate and everything scored from it are unchanged for every record.
- **Ruling (`docs/algorithm-change-playbook.md`): no successor.**
  - Step 1: no stored record changes meaning, and replay and rebuild read nothing new (the resolver's new label applies only to events no vault has).
  - The 2026-10-17 rule (a change to which items are served as measurements, or to which new attempts are primed, mints a successor with a kill switch) does not apply: what the desktop serves and primes is unchanged (byte-identical, §5); a phone serves only what PR-6 lets it, as M2a's queue did without a successor, and it never serves a measurement it can't show (the check waits).
  - The kill switch is `phone_plan`. As M2a reasoned: no vault has a phone-plan predecessor state.

## 4. Security notes for review

- **Allowlist:** every new method is named, with its constraints; the G3 enumeration keeps every other registered method at 403 (`test_mobile_rpc.py`, `test_mobile_host_auth.py`).
- **Origin:** the device class and surface come from the token (`RequestOrigin`), never a parameter; the plan's filter is built from it in the handler.
- **Ownership:** §1.1's list; a job accepted for a session keeps PR-4's acceptance rule.
- **Contest:** the reason never reaches the grader (the handler's own rule); one key per contest.
- **Spend:** V2 adds no model request. A plan decision's model call at a boundary is the desktop journey's (D2), under its budgets. The host's attach starts none of the plan's background spenders (D6).

## 5. The desktop at a None origin: byte-identical

- **By construction:** every new branch is behind `env.device is not None` or `ctx.request_origin is not None`; `test_a_none_origin_never_enters_the_device_branch` makes every device-only function raise and runs a full desktop day.
- **Against the base commit:** the same desktop journey (session, plan read, eight served steps answered, Keep going; an image-prompt item in the plan; the clock pinned; `random.seed(7)`) was run under `env -i` with empty homes on `5a03164763`'s `src` (`git archive`) and on this branch's, dumping every reply plus the `router_decisions` and `attention_block_events` rows, ids normalized. **Identical**, with one mask: `router_decisions.snapshot_hash`, which hashes inputs that include the random plan id (two base runs differ there too).
- An incrementing fake clock showed the branch reads the clock a few more times over the journey (where was not traced), which moves later timestamps under that fake. No reply or row reads differently at a pinned clock.

## 6. Gate (this step; the full suite runs once in the landing gate)

Run in the worktree, every pytest and vitest command inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6` and vitest at `--maxWorkers=4`, every Python command under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

- **Setup:** `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`; `npm install --prefer-offline` in `apps/learnloop-mobile` and `apps/learnloop-tauri`.
- **`lint-imports --no-cache`:** **43 kept, 0 broken** (before the first commit and at the end).
- **Targeted pytest** (`-n 6`, 213 files: every test file that names a module this stage changed, found with `git grep` over the engine, view, plan log, RO5 checks, device eligibility, request origin, the changed handlers, the plan RPC names and `learnloop_mobile`, plus the contract set): **4835 passed, 18 skipped, 2 failed**, in 54 min.
  - `test_mobile_meta_timing.py::test_meta_names_the_allowlist_the_host_enforces`: the meta reply gained `phone_plan`; the test was updated, and the file then passed **23/23**.
  - `test_rofu_carried.py::test_an_early_publication_served_keeps_its_carried_valuation`: **fails identically on the base commit's code** (`5a03164763`'s `src` on `PYTHONPATH`, run twice on each), so it is not this stage's; it is left for the landing gate to read against main.
  - The contract set inside it: `test_sidecar_measurement.py` (display-label audit), `test_codex_lockdown_round3.py` (process-launch allowlist), `test_codex_lockdown_frozen.py` (frozen cycles), `test_cli_help_snapshot.py`, `test_architecture.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_config_refactor.py`, `test_public_tip_guards.py`, `test_sqlite_file_copies.py`, `test_figures_prefetch_boundary.py`, `test_module_catalog_inventory.py`, `test_hypothesis_marks.py`.
  - The new files: `test_mobile_v2_plan.py` (13), `test_mobile_v2_checks.py` (5), `test_mobile_v2_feedback.py` (6); all `tests/test_mobile_*.py`.
- **Durability:** `pytest -m durability tests/test_mobile_two_process.py`: **2 passed** (the new plan-turns test and M2a's).
- **`apps/learnloop-mobile`:** `npm run typecheck` clean; `npx vitest run --maxWorkers=4 src public` (every phone test file; all exercise the rewritten App, Today or practice): **23 files, 276 tests passed**; `npm run build`: built.
- **`apps/learnloop-tauri`** (one file split, one added): `npm run typecheck` clean; `npx vitest run --maxWorkers=4 src/screens/feedback/answerExposure.test.ts src/screens/feedback/answerExposure.shell.test.tsx src/screens/FeedbackScreen.phase4.test.tsx`: **3 files, 93 passed**; `npm run frontend:build`: built. No `src-tauri` change, so no `cargo check`.
- **References:** `module_generate.py` then `module_validate.py`: **PASS**; `desktop_generate.py` then `desktop_validate.py`: **passed** (322/322 TS, its three pinned counts moved by the one new module); `validate_vault.py`: passed. Provenance-only churn in modules this stage did not touch was left out. No schema change, so no DB reference run.
- **No paid or live call.** The contest's grader is an outage in every test that reaches it.

**Test files run, for reading the landing gate against:** the 213 targeted files (the list is reproducible with the `git grep` above), `tests/test_mobile_two_process.py` in the durability lane, every vitest file in `apps/learnloop-mobile/src` and `public`, and the three desktop exposure files.

## 7. What the owner runs on the iPhone (P3-P5)

Nothing below has been run on a device.

On carson, after landing. V2 adds no Python dependency and no migration; rebuild the app and restart the host:

```bash
cd ~/Documents/thinking/learnanything
(cd apps/learnloop-mobile && npm install && npm run build)
systemctl --user restart learnloop-mobile
.venv/bin/learnloop-mobile doctor
```

The cached V1 app offers *LearnLoop was updated. Reload* (the allowlist moved): tap it.

- **P3. Today is the plan.**
  1. Open the app. Today shows one sentence ("25 minutes today: …"), `why?`, and Begin. With the desktop app open on Today, both show the same plan.
  2. Tap Begin. The question opened is the one the desktop's Today names as its next block (the desktop's Today, Begin, would show the same item; don't answer it there).
  3. Answer it. Within about 3 s the desktop's Today moves (the item done, the next block named).
  4. If an item has a picture or a page link, the phone skips it and Today says *1 question is waiting for the desktop.* Open the desktop: its next Next serves that item (take the session back there when asked).
- **P4. A miss, held feedback, a hint.**
  1. Miss a question on purpose. Feedback says *Preparing a question on this…* and holds the full answer and the causes (*…come after the question…*), with the router's line beneath when the router decided.
  2. Tap *Show anyway*: the full answer is offered (*Show the full answer*) and the causes appear. On another miss, tap *Continue without it* instead: Next goes on with the plan. The question itself waits for the desktop (V3).
  3. On a question with hints, tap *Hint*: the sheet says the answer will count as answered with help. Tap *Show a hint*: it appears under *◌ with help*. Submit: the answer is recorded with one hint used (a hinted attempt, where the item allows one).
- **P5. The stop offer.**
  1. Keep answering past the plan's minutes. When the plan stops, Today says *Done for today · N minutes.* with *Keep going* and *Done for today*.
  2. Tap *Keep going*: a short extension's Next appears. Answer one.
  3. When it stops again, tap *Done for today*: the session ends (*Session finished: …*).

## 8. Process notes

- One text-replacement script ran with plain `python3`, outside `env -i`, to patch `router/plan_log.py` (five string replacements). It read and wrote that file only and imported nothing from LearnLoop. Every other patch used the editor; every other Python or CLI call ran under `env -i` with empty homes.
- The byte-identity check's scripts and outputs are in the stage's scratch directory, outside the worktree.

## 9. Open questions

1. A drawn stop at a phone boundary can close the plan while ordinary items (not the day's check) wait for the desktop; they stay unresolved in the closed plan, as after a desktop *Done for today*. Should the phone's boundary instead wait whenever anything is held (the phone would then often stop at "waiting for the desktop")? V2 lets the drawn stop stand, so no decision is discarded by its outcome.
2. The phone's *Skip it* on a held item skips something the learner has not seen (as the desktop's Today skip link does). Keep it, or offer the skip only for the randomized check's wait?
3. Hints' surface: take the small migration (§2, item 5) in V3, or leave the device recoverable through the attempt only?
