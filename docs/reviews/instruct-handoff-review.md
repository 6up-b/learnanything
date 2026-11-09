# Instruct hand-off (IH0-IH7): independent code review

**Tip reviewed:** `38ccfa65f8` on `instruct/handoff`. The tip is a single-parent commit holding main's V4 tree (see m1), so the merge base with `main` is still `a525dbcef4`. I reviewed `git diff 6c8962ce95 HEAD` (main's tip against this one), which holds only IH's changes. I confirmed that no `src/` file main changed since the base differs from main except through IH.

**Result:** 1 blocker, 6 major, 9 minor. Do not land before B1 is fixed. M1-M6 should be fixed in the same pass: M1, M3, M4 and M5 feed wrong data or undo the owner's rule, and M2 strands a learner on a dead page.

Reproductions are under `/tmp/ihreview/` (scratch, not committed): `py/test_repros*.py`, `py/test_flake.py`, `SomethingElsePeek.test.tsx`, `NoLinkBaseline.test.tsx`. The Python ones run from the worktree with `env PYTHONPATH=src:. <venv>/bin/python -m pytest -p tests.conftest --rootdir=. -c pyproject.toml /tmp/ihreview/py/<file> -q -s -p no:cacheprovider`. They use the repo's fakes and make no model call.

## Blocker

### B1. The phone's feedback link is the peek the phone was built not to make, in every switch state and at every tag

`apps/learnloop-mobile/src/practice/SomethingElse.tsx:41`, mounted from `apps/learnloop-mobile/src/App.tsx:820`.

**What goes wrong.** `App.tsx` passes the `somethingElse` prop whenever a session is open in plan mode, without looking at the host's flag. To learn the flag, the component runs `useCachedQuery(["get_daily_plan", sessionId], phone.getDailyPlan)`, and it does this before its `if (!plan.data?.somethingElse) return null`. On the phone a plan read at a finished block crosses the boundary. Spec §3a item 2 and `spec_mobile_frontend_v2` §4.5 exist because of this: "a read at a finished block crosses a boundary and writes its decision", "so there is no peek". IH0 built `plan_prefetch` so the phone would not need one, and IH3 puts one back.

**Scenario.**
1. The learner answers the last question of a block on the phone. Submit invalidates `TAG.queue`, feedback renders, and the link mounts.
2. `get_daily_plan` runs. On the single RPC worker it first waits in `prepare_queue_build` for up to `diagnosis.next_item_wait_seconds` (10 s), and `get_feedback` polls queue behind it. It then crosses the boundary and starts the job.
3. Any later read writes the decision while feedback is still showing. The mounted query re-reads on every `TAG.queue` invalidation, and `pollRevision` (`App.tsx:357`) invalidates whenever background work lands.
4. With no model set up, the first read writes it.

The kill switch does not stop this. With `learner_preferences = false`, or a vault at `mvp-0.54`, the host omits the flag, but the read still fires because the flag is what it is reading.

**Verified.**
- `SomethingElsePeek.test.tsx` against the real App, counting `get_daily_plan` from before submit to after the feedback screen:
  ```
  link? false  before feedback: 2  after feedback: 3
  link? true   before feedback: 2  after feedback: 3
  ```
- `NoLinkBaseline.test.tsx` is the same run with the component mocked out: `2` then `2` both ways. So the extra read is this component's, and it fires with the flag absent.
- `test_repros2.py::test_R8` through the real host, at a boundary once the job has finished, one `get_daily_plan`:
  ```
  changed {'attention_blocks': 1, 'router_decisions': 1, 'attention_block_events': 5, 'router_decision_payloads': 5, 'decision_objectives': 1, ...}
  ```

**Why the tests miss it.** The IH0 phone tests count `next_plan_item` and `plan_prefetch`, never `get_daily_plan`.

**Fix.** Don't read the plan from the feedback screen. Have `App` decide from the plan it already holds, using `peek(planKey(sessionId)).data?.somethingElse` without a fetch, and pass `somethingElse` only when that is true. Add a test that feedback makes no `get_daily_plan` call, with and without the flag.

## Major

### M1. "Not now" on an interrupting offer opens the next question without serving it

`apps/learnloop-tauri/src/app/App.tsx:1261-1263`; the test `App.offerPage.test.tsx:201` pins the behaviour.

**What goes wrong.** After a decline, `answerPlanOffer` calls `nextPlanItem({serve: false})` and passes the result to `routePlanStep`. A non-boundary item step goes straight to `openPractice` with `presentationId: null`. Every other path serves first: `useNextPlanStep.resolve` says "Inside the block: serve it now". An IH2 offer over a block with questions left produces exactly this step. It is the main mid-block path.

**Effect.** The attempt binds to no presentation, and the following are all skipped:
- the `item_served` event;
- `plan_presentations`;
- AD's frozen serve inputs (`record_plan_serve`);
- `_held_cold_check`, the eligibility decision every serve path must ask.

The next miss on that item also fails `followup_run.serving.plan_will_place`, which reads `plan_presentation_id`. Next then opens the probe directly instead of going through the plan.

**Verified.** `test_repros.py::test_R1`, the same read the App makes after `SG.respond(declined)`:
```
step item boundary False presentation_id None item pi_p1b
presentations 0 item_served events 0
```

**Fix.** When the step is an item with `boundary: false`, call `nextPlanItem({serve: true})`, as `resolve` does. Correct the test.

### M2. An offer superseded while its page is on screen leaves a dead page

`apps/learnloop-tauri/src/screens/today/LessonOfferPage.tsx`, `App.tsx:2120` and `LessonOfferBlock.tsx:74`, with `lesson_suggestion.py:577-578` refusing.

**What goes wrong.** The page holds the step it was opened with (`planOffer`) and nothing updates it. `useDailyPlan` stays mounted in `App`, so a queue invalidation runs a read, and that read crosses the boundary when a follow-up becomes ready (IH2 item 1). The offer on the page is superseded by a new decision. Start, the alternatives and Not now then all answer "That suggestion is no longer in your plan." The catch only calls `onError`, so the page stays.

**Scenario.** This is the Nov 8 shape: a probe becomes ready seconds after feedback's Next opened the page. The learner taps Start and gets an error, then Not now and gets the same error. Today's own tab doesn't reset the stage (`gotoTab` resets only for `next !== "today"`, `App.tsx:1525`). The only ways out are "Something else would help" or going to another place and back.

**Verified.** `test_repros.py::test_R7`: both responses raise `not_found` after a background read supersedes the offer. The page side is from reading the code, with no running app.

**Fix.** On `not_found`, close the page and re-read the plan. Also close the page when the plan's `currentBlockId` stops being `planOffer.blockId`.

### M3. Offers nobody saw use up the daily ceiling, and at the ceiling an open offer is cancelled with no contest

`daily_plan/lesson_offer.py:218-221` (`shown_today`) and `:261`, reached from `engine.py:5101`.

**What goes wrong.** `shown_today` counts every drawn offer, including superseded ones and ones that never rendered. It also counts the open offer being replaced. So when a follow-up arrives at the ceiling, the boundary ends the open offer and `LO.build` answers `none:ceiling_bound`: the new decision holds no lesson. This is the rule-based cancellation §1 and §10 rule out ("a new decision holding both candidates"), reached through the ceiling. `offer_shown` (IH1) records what was seen, and nothing uses it here.

**Scenario.** Default ceiling 3. Three background reads each draw an offer as follow-ups arrive. The learner has seen none of them. The third is superseded by rule, and no lesson can compete for the rest of the day.

**Verified.**
- `test_repros.py::test_R3`, default config:
  ```
  statuses [('lesson_offer:lo_diag','offered'), ('lesson_offer:lo_diag','offered'), ('new:…','none:ceiling_bound')]
  offer decisions 3  shown_today 3  offer_shown events 0  block_started on offers 0  expired 3
  ```
- `test_R3b`, `ceiling_per_day = 1`, the Nov 8 shape: `lesson_offers none:ceiling_bound`, a support with no lesson, old offer `superseded`.

**Fix.** Don't count the offer being superseded. Count an offer against the ceiling only if it was shown (`offer_shown` or `block_started`) or answered. The fold needs a tag decision, since older offers have no `offer_shown`.

### M4. `none:forced_items` still cancels an open offer

`daily_plan/engine.py:3181-3202` and `:5097-5101`.

**What goes wrong.** `advance_with_context` picks `superseding` whenever forced items and IH2 are on. `_followups_compete` then returns False if the follow-up's own decision already held a lesson. That rule is about an earlier draw, but it is applied to an offer drawn later. So `offer` becomes `none:forced_items`, there is no contest, and the open offer ends `superseded`. The logged status is the Nov 8 line, and the owner's rule is what this was meant to remove.

**Scenario.**
1. A miss draws `insert_now` with a lesson in its support.
2. While the probe is being written (a job of tens of seconds, feedback held), a plan read at the boundary draws a lesson offer.
3. The probe becomes ready.
4. The later offer is cancelled by the forced rule, with no decision holding both.

**Verified.** `test_repros4.py::test_R9`. `_lesson_already_competed` is stubbed to True, the state `test_a_probe_whose_decision_already_beat_the_lesson_is_not_contested_twice` shows it reaches:
```
new policy router_objective_v1  support ['new:…','push:…','repair:…','maintain:…','stop_for_today']  lesson_offers none:forced_items  old offer superseded
```

**Fix.** With `superseding` set, always run the contest. "That draw stands" should apply only when no offer has been drawn since that decision.

### M5. An offer never rendered is recorded `ignored` and read as a decline

`daily_plan/lesson_offer.py:472` (`_sweep_decisions`) and `:459`; `router/lesson_suggestions.py:406-407`.

**What goes wrong.** The sweep writes `ignored` for any unanswered offer whose block ended, whose plan closed or whose day passed, and `LS.observations` turns `ignored` into `accepted = False`. Offers are drawn on background reads, and IH2 adds draws on the generation slot. An offer the learner never saw therefore counts as a refusal. This is a plan act recorded as a learner answer. The base rule dates from TE3b, but IH2 adds a path that draws with no screen involved, and IH1 now records what is needed to tell the two apart.

**Scenario.** A miss's job draws the lesson (IH2 item 3), the learner closes the app on feedback, and the next day that offer lowers `P(accept)`.

**Verified.** `test_repros.py::test_R4`:
```
swept 1  response ignored  offer_shown 0  block_started 0  observations [False]
```

**Fix.** At the tag, an offer with neither `offer_shown` nor `block_started` ends `expired` (for example `never_shown`), never `ignored`. Offers below the tag have no such record and keep their rule.

### M6. A phone choice that "places nothing" draws a plan block through its reply

`learnloop_sidecar/handlers/daily_plan.py:617`.

**What goes wrong.** `plan_something_else` builds its reply with `**_current_view(env)`, which is `advance_with_context(serve=False)`. At a boundary on the phone that read crosses it. Spec §6 says a `waits_on_desktop` choice "places nothing", but this one draws and logs a router block in the same call, and the reply's `step` is None.

**Verified.** `test_repros5.py::test_R10` through the real host (the lesson candidate is stubbed so the option exists):
```
outcome waits_on_desktop  delta {'attention_blocks': 1, 'router_decisions': 2, 'router_objective_traces': 1, 'router_learner_preferences': 1}  step None
last decisions [..., ('learner_pick','learner','lesson_offer:lo_a'), ('plan_block','router_objective_v1','new:b46c7fe5ca862afd')]
```

**Why the tests miss it.** No test calls `plan_something_else` through the RPC on a plan vault. `test_mobile_phone_contract.py:222` runs it with the plan off, and `test_ih3` calls `learner_action` directly.

**Fix.** For an outcome that serves nothing on a device, build the view from the stored plan without crossing. `agreed` on the phone has the same reply path (m2), so cover it too. Add a host test pinning the row counts.

## Minor

**m1. The tip says "Merge main" but has one parent.** `38ccfa65f8`'s only parent is `ffb1157597`, so `git merge main` replays V4. `git merge-tree --write-tree --name-only HEAD main` reports conflicts in `src/learnloop_mobile/allowlist.py`, `apps/learnloop-mobile/src/api/{phone.ts,phoneMethods.ts,retryPolicy.json}`, `tests/test_mobile_{allowlist,rpc}.py` and many generated reference notes. Fix: record the merge with both parents on the same tree (`git commit-tree c81da441f2 -p ffb1157597 -p 6c8962ce95`).

**m2. Phone "learn this" on a drawn offer doesn't say it waits on the desktop.** `learner_action.py:410` handles `agrees` before `:415` handles `not servable`. The outcome is `agreed` and `onAgreed` calls `planNext`, so the wording §6 item 5 requires never shows. `test_repros2.py::test_R5`: option `('lesson', plansPick True, servable False)`, `outcome agreed`, `step None`.

**m3. "Read the source" on the phone says it waits on the desktop, though V4 serves readings there.** `learner_action.py:247` returns False for `READ` unconditionally, while `env.device.serves_reading(block)` exists and `App.openStep` opens readings in the phone's Reader. From the code; no reading option arose in my fixture.

**m4. A retry loses the outcome.** `_replayed` (`learner_action.py:526`) always answers `replayed` with no `lesson`. A desktop retry of a lesson pick whose reply was lost opens nothing (`lessonEntryFor` needs `outcome === "lesson"`), and a phone retry of `waits_on_desktop` loses the message. `test_repros.py::test_R6`: `lesson {...} | retry replayed None`. If the crash came between `_place`'s commit and `_serve_step`, the replay also returns an unserved item. Fix: replay the original outcome.

**m5. A need follow-up's lesson draw runs twice.** Spec §5: "A follow-up whose own decision already held a lesson and drew the follow-up stays forced … not run twice". `_lesson_already_competed` (`engine.py:3181`) looks up only a workflow, so a need path item returns False. `test_repros.py::test_R2`: `first [('continue_current', ['insert_now','continue_current','lesson_offer:lo_diag'])]`, then at the boundary `support ['followup_contest:pi_diag_mid','lesson_offer:lo_diag']`. Each draw logs its own propensity, so replay stays exact, but the lesson gets a second chance the spec denies. Fix: read the `plan_interrupt` row by its item's `decision_ref` or `followup_deferred` event.

**m6. `last_miss` doesn't read the latest graded answer.** `router_objective/preferences.py:157-160` selects the latest attempt with no `correctness IS NOT NULL`, then treats NULL as 1.0, so an ungraded attempt hides an earlier miss. Spec §7 and the docstring say "the latest graded answer". From the code.

**m7. The default Today has no link.** §6 item 1 says "at any plan boundary", and the as-built note says "under the current block on Today". `DailyPlanView` (classic shell) has it, but `TodayPlace` (the `simple` shell, the default) doesn't. Feedback and the offer page do. Grep: no `SomethingElse` in `TodayPlace.tsx`.

**m8. An override writes no decision-state receipt.** `learner_action._place` (`:476`) logs its `learner_pick` with no `decision_state` or `prefilter`, where `engine._pick_new_block` keeps RO0 rows 9 and 13 (`pick_state`). Override rows will lack the frozen state other picks have. From the code; I didn't trace a reader that fails on it.

**m9. Test quality.**
- `tests/test_ih6_workbench_open_item.py:374-378` is flaky (see "Settled" below).
- `App.offerPage.test.tsx:201` pins M1 as intended behaviour.
- `test_mobile_phone_contract.py` runs IH3 with the plan off and reads only `enabled`, so `options`, `preference`, `step`, `somethingElse` and `questionInProgress` have no contract check against a real host.
- `test_no_decision_module_reads_a_score_or_a_stuck_flag` (`test_ih2:874`) leaves out `daily_plan/engine.py`, where the forced paths live. Its word list can't see M3 or M4, which are rules on counts and forced flags.
- `test_ih5_successor.py` tests the gate and the mix but no chooser under a failed policy. I checked that path end to end and it is correct (below), so this is a missing pin, not a bug.

**For the owner, not a defect.** `lesson_suggestion.py:198` makes a topic a lesson candidate when `len(cold) >= 2 and all(correctness < 1.0)`. Spec §5 calls this by design: it says what is offerable, and the offer must still win the draw. It does keep the router from offering a lesson until the score rule is met, and it has the shape of the rule §1 quotes. On Nov 7 this is why "the lesson was not yet a candidate at 9:11". Keep it, or make it a decision.

## Settled: the unexplained failure

`test_a_mid_block_follow_up_waits_too_with_no_decision_of_its_own` failing with `lesson_offer` is **nondeterminism in the test only**. There is no race in the code.

The test's first `advance(serve=True)` makes a real draw, unpinned. The seed is `mix.seed_for(key, decision_id)` and `decision_id` is a fresh ULID, so every run draws differently, as designed. The support holds a lesson at the floor.

`py/test_flake.py`, 60 fresh vaults:
```
TALLY {'item': 57, 'done': 2, 'lesson_offer': 1}  offer mu [0.02]  distinct seeds 60
```
So the assertion `step["kind"] == "item"` fails about 5% of the time: the lesson at μ = 0.02, and a floor draw of stop as well, which fails the same way. Fix: use the `draw` fixture (`never_stop` and a `prefer`), or a pinned seed.

## Checked and found sound

- **IH5 end to end.** A real chooser with the LLM failing: `on` gives `{numeric: 1.0}`, rule `other_policy`, component `numeric`. Switch off and at `mvp-0.54` give `{numeric: 0.2, staged: 0.8}`, no rule key, component `staged`. `mix.recompute` matches the logged propensities in all three.
- **All six switches off at the tag against `mvp-0.54`.** The `plan_block` row's detail and mixture have the same keys. Objective settings, key and seed gates read as the spec says; `numeric_seed` strips only what it says.
- **Propensities in contests and `plan_interrupt`.** Support, `_offer_arm`, the `candidates_json` rows and `recompute` agree, including no-room `{insert_now, lesson}`. A lesson row has `chosen_practice_item_id` NULL, so outcomes don't attribute it to the follow-up.
- **`plan_prefetch`.** Read-only attach, `start_only`, `persist_explanations=False`. Writes on its path (`_settle_lost_followups`, a waiting probe's moves, `refused_now`) fail at the database and return `unavailable`, not a partial write. No `get_or_create_today` caller reached on a read path bypasses the workbench hold (`set_minutes`, `keep_going`, `learner_pick` are explicit steps).
- **Stuck paths on the server.** A lost workflow is released at once. `next_action` answers `continue` for `WAITING` and for reopened `PENDING`. Superseded and passed offers settle by `offer_standing`. A reopened job runs a new decision on a new receipt. With nothing to place, Next goes on.
- **IH6 data.** `leave` writes no `updated_at`, so "Leave for now" doesn't affect the hold. A serve never holds. The view has `deciding: false` under a hold, so nothing polls. `lint-imports --no-cache`: 43 kept, 0 broken.
- **IH6's raw SQL against `evidence-never-reads-the-workbench`.** The read takes only `id` and `practice_item_id`, reads no steps or stems, and changes when a decision is drawn, not what it reads. It goes around the contract's static check, so nothing would flag a wider read later. A one-column pin, or a declared `ignore_imports` door as the notes contract has, would make it visible. No defect today.
- **Learning data.** `w_pref`'s cohort comes from `plan_block` traces, and picks have none. Agreements are left out of the acceptance offset. The offset's slot exists only with a request on record, and the other `.banks` readers (`teacher/report.py`) index by term. Superseded rows are `expired`, in `release_for`, read by neither observations nor declines.
- **IH7.** `search_sections(read_only=True)` means `deep=False`, no query vectors, no rewrite, no `deliver`. The Library's scope excludes withheld and exam material. Provenance kinds `hypothesis` and `learner_text_gap` match the writers. `analysis_md` is unread. With no extras `_render_sources` is the predecessor. Open turn origins reach `plan_interrupt` offers through `_accepted_suggestion`.
- **Migration and chain.** Table role `RAW_LEDGER`, triggers, head fixture at 251 in rollback mode, upgrade link and journal handoff.
- **Script-edited pins.** I read the IH5 commit's edits as a whole and spot-checked ten files. They move version strings, chain slices and fixture paths. The `timeout_seconds` reset to 8 in frozen digest tests is explained and asserts 40 first. None makes an assertion vacuous.
- **Offer page wording** matches §4 item 2; the question-in-progress and waits-on-desktop lines match §6 and §7b.
- **Test runs.** `tests/test_ih*`, `test_instruct_handoff*`, the fixture, tip-guard, migration and allowlist files: 628 passed under `-n 6`.

## Could not check

- Anything in a running app, on a real phone or with real models. Layout and feel are untested, and M2's page behaviour is from code plus the refusal I reproduced.
- Real logs: no vault was read. How often M3 and M4 occur depends on real read timing.
- `w_pref` above 0 on realistic data. I read the shift and contrast code and the tests but didn't simulate it.
- The durability lane (WAL) for the prefetch's read-only attach, and `plan_something_else` on the RPC worker racing a serve on the job worker. It's guarded by the receipt key and SQLite, but I didn't run it.
- `router.log_decisions = false`. `record_decision`'s fallback to `insert_now` covers only an exception, and a `None` receipt returns earlier, so a drawn lesson with no receipt looks possible. My run with logging off settled `no_intervention` without drawing a lesson, so I can't say whether it's reachable.
- The Rust passthroughs (compiled by nobody here), and the full suite, per your instruction.

## Fixes

Fixed on `instruct/handoff` after this review. Each finding was reproduced first. Commit hashes are in the table; the merge is the last step (m1).

| Finding | Outcome | Commit |
|---|---|---|
| B1 | Fixed. `SomethingElse` reads no plan. `App` decides from the plan it holds (`peek`, no fetch) and `PlanToday` from its own read. Test: feedback makes no `get_daily_plan` call with and without the flag (3 against 2 before the fix). | `3217a11da4`, `efe49488ae` |
| M1 | Fixed. *Not now* serves through `servedForExplicitStep`, shared with feedback's Next. The test that pinned the bug now pins the serve. | `05e1f7dbe0` |
| M2 | Fixed. `not_found` closes the page and re-reads, and a later plan read with another block current closes it. Today's card takes `not_found` the same way. | `05e1f7dbe0` |
| M3 | Fixed, with a different rule for the open offer. An offer counts only if it was on screen or answered, and only for rows at the tag with the switch on. A decision replacing an open offer isn't held back by the ceiling at all, because leaving only that offer out of the count still ends the next replacement by rule. | `4a43accdee` |
| M4 | Fixed. A contest always runs with an open offer being replaced, and "that draw stands" holds only while no offer has been drawn since. A requested item or a randomized check still gives `none:forced_items` beside an open offer: §5 item 2 keeps those forced. | `4a43accdee` |
| M5 | Fixed. An unseen offer ends `expired` (`withdrawn: never_shown`). The review named one sweep; TE1b's `_sweep_ignored` also reached passed offers and is fixed too. | `4a43accdee` |
| M6 | Fixed. A device's choice with no step builds its reply from the stored plan. Host tests pin the row counts. | `3fff1f3022` |
| m1 | Fixed as the last step: main recorded as a real parent with `git merge -s ours`. See the report for how it was checked. | the merge commit |
| m2 | Fixed. The phone is told the drawn lesson waits; it stays an agreement, so the parent isn't called `overridden`. | `3fff1f3022` |
| m3 | Fixed. Servable where `device.serves_reading` says so. Checked at the function; no reading option arises in the host fixture. | `3fff1f3022` |
| m4 | Fixed. A retry gives the first outcome and finishes a serve a crash left owing. `replayed` is no longer an outcome, only a flag. | `3fff1f3022` |
| m5 | Fixed. A need follow-up's `plan_interrupt` is read through its `followup_deferred` event. | `4a43accdee` |
| m6 | Fixed. `correctness IS NOT NULL`. | `3fff1f3022` |
| m7 | Fixed. `TodayPlace` has the link with a session. | `4a43accdee` |
| m8 | Fixed. An override writes `prefilter` and `decision_state` receipts with `decision_kind = learner_pick`. | `3fff1f3022` |
| m9 | Fixed. `App.offerPage.test.tsx` corrected; IH3's replies checked against a real host with the plan on (`tests/test_ih3_phone_host.py`); the word-list guard now reads `engine.py` and `learner_action.py`, and its docstring says rules on other counts need behaviour tests; IH5 pinned through a real chooser; the IH6 test pins its draw, and so does the rest of that file, since `test_resuming_it_in_this_session_makes_it_count` failed the same way in a repeat scan. | `3fff1f3022`, `53be1788a5`, `db728fa40a` |

**New in this pass, not in the review.** The old ceiling count was the only thing stopping a redraw loop. Two written probes that had each lost to a lesson passed each other's offer on every read, so reads alone would have drawn for ever once unseen offers stopped counting. Workflows an offer replaced had beaten now move to the newest offer (`engine._followups_lost`). Spec §5 "What bounds the draws" has the argument. The test fails without the change.

**Left for the owner, unchanged:** whether `w_pref` acts or stays report-only; whether a learner-asked lesson uses IH7's diagnosed sections; whether an open Reader problem holds decisions when no session is open; the `cold_failing` gate at `lesson_suggestion.py:198`.

## Second review (fixes)

**Tip reviewed:** `6b4997dd6c` on `instruct/handoff`, against `ef0580db76`.

**Result:** no blockers, 1 major, 4 minor. The major one predates the fixes and neither review's tests reach it. It should be fixed before landing, in a small change. The fixes themselves hold.

Reproductions are in `/tmp/ihreview2/` (scratch, not committed): `py/test_second.py` (cases S1-S17), `py/test_stress.py`, `py/test_equal.py`, `web/offerPage2.test.tsx`. They run as the first review's do, with fakes and no model call.

### Major

#### R2-M1. A plan read during a follow-up's decision leaves two open offers, and taking one doesn't end the other

`daily_plan/engine.py:3307` and `:3319-3330`; `followup_run/router.py:218` and `:320`.

**What goes wrong.** `interrupt_offer` checks for an open offer before the job's decision starts. The decision then waits on its models, 11-15 s on the Nov 7 log and up to 40 s by §3a. Nothing checks again before `place_interrupt_offer` writes the block. A plan read at the same boundary can draw an offer during that wait. This is the same read and the same window as the first review's M4. If the job also draws the lesson, the plan holds two unanswered offers, which breaks §5's "no arm while an offer is open".

**Scenario.**
1. A miss ends a block, and the job starts its decision with the lesson arm.
2. A plan read draws offer A.
3. The job draws the lesson, which places offer B. The workflow now waits on B.
4. The learner taps Start on A. The workflow doesn't settle, because it lost to B. When the lesson closes, B offers the same lesson again.
5. If B is left unanswered it was still on screen, so it ends `ignored` and counts as a decline of the lesson just taken.

**Verified.** `test_S16` draws through a plan read inside `decide_followup`, at a real boundary:
```
open offers [(2, <A>, False, False), (3, <B>, False, False)]
after start lesson_offer <B> lesson:lo_diag
wf waiting lesson_offer:lo_diag
second offer's row ignored
observations [True, False]
```
With "Not now" on A, the same run gives B at once and `observations [False, False]`, so one refusal is recorded twice. Both draws need the lesson, so its frequency depends on real read timing, which I couldn't measure. From the code only, not reproduced: a serve's `_boundary` waiting on its models can have a job's offer placed under it, with the same result.

**Fix.** Check again inside the decision's transaction. If an offer is open by then, end it with `LO.supersede(..., by=<this decision>)`, the §5 item 1 mechanism, so exactly one stays open and the logged propensities stay exact. Do the same in `_boundary`'s transaction for any open offer other than the one in `superseding`. Add a test from S16.

### Minor

**R2-m1. "Not now" under IH6's hold makes a decision and serves an item nobody opens.** `app/dailyPlan.ts:96`, `app/App.tsx:1280`. After a decline with a workbench problem open, the read says `question_in_progress`, and `servedForExplicitStep` serves. Before M1's fix, this path stayed on Today with the resume line. §7b item 4 names Next, Begin and Continue as explicit steps, and "Not now" only declines a lesson. The new decision is drawn before the open problem's answer exists, which is what IH6 prevents. The item is also served with `boundary: true`, so `routePlanStep` stays on Today: its presentation starts with nothing on screen. Without a hold, the test "Not now with a new block next stays a read" serves nothing, so the two cases differ. Verified: `test_S10` (`question_in_progress`, then one new decision, an item with a presentation and `boundary True`) and `offerPage2.test.tsx` (`serve:false`, `serve:true`, Today showing). Fix: in `answerPlanOffer`, leave `question_in_progress` to Today and serve only `item && !boundary`. Feedback's Next has the same served-but-unopened step under a hold (IH6's own path). There the decision is allowed, but the serve should go through the block line or open the item.

**R2-m2. A workflow with nothing written doesn't move to the replacing offer, unlike a written one.** `engine.py:3066-3067`, `:3242-3254`. `followups_lost` holds item ids, so a workflow with no item keeps its old offer. When a contest replaces that offer with a new one, the workflow reopens with an offer still open and its job runs with no lesson arm. So it generates a question while the lesson stands, and that question then contests the new offer in one more draw. §5 says "what an offer beat waits on its replacement too", and the next item says "the job runs again only after its offer passed", which reads as true only of the old offer. Draws stay bounded, at one extra job and one extra contest per workflow, but it spends an author call on a question the lesson may still beat. Verified: `test_S17` (`unwritten workflow pending None offer open True`; the author call is from the code). Fix: move open workflows that lost to the replaced offer as well, found through their `lesson_offer_won` event, or say in the spec that this is intended.

**R2-m3. A phone "learn this" on a drawn offer reaches no model.** `daily_plan/learner_action.py:422-428`, `router/lesson_suggestions.py:432-434`. After m2's fix the outcome is `waits_on_desktop`, but the row is still an agreement, so `unprompted_observations` leaves it out because "the offer was on screen". On the phone it wasn't. If the desktop never renders the offer, it ends `never_shown`, and the learner's explicit request appears nowhere in the acceptance model. Spec §7 says requests count "including a phone's". Verified: `test_S15` (`unprompted obs 0`, `withdrawn: never_shown`, `observations []`). Fix: count an agreement made on a phone surface as a request. The offer never reached that learner on that surface, so nothing is counted twice unless a later answer on the desktop lands too, which the owner may want to rule on.

**R2-m4. Two edges of a retry.** `learner_action.py:400-401`, `:617-619`.
- A retry whose block has no served item serves it even if the plan has closed since. Verified: `test_S14`, a crash after commit and then a stop: `retry served item <presentation> plan stopped`, with one `item_served`. A third call makes no second serve. Fix: serve what is owed only on an open plan.
- Both clients keep the key after a failed send with the panel open, and a replay never compares the kind. A lost reply followed by a tap on a different option therefore gets the first choice. From the code. Fix: start a new key when the option changes.

### How many offers a learner can be shown in a day

**There is no constant bound, but a bound exists:** seen offers ≤ `ceiling_per_day` + the follow-ups that became ready while an offer stood open with no questions below it. Reads alone add nothing.

- A fresh offer, at a boundary or through a `plan_interrupt` arm, needs the seen count below the ceiling. Only a replacement skips that, and each replacement uses up a follow-up that hasn't yet lost: everything it beat waits on the new offer. A need item must also fit the plan's minutes. A workflow's probe has no such check.
- The chain ends at the first answer, and then the ceiling binds. `test_S4`: default ceiling 3, 9 arrivals, 10 offers seen; "Not now" then gives `none:ceiling_bound`.
- **In the plan's normal path** the learner can't answer plan questions while such an offer is the next step, so the extras can only be probes still being written when the offer appears. They come from recent misses. I'd expect 4-5 offers on a heavy day at ceiling 3, but that's reasoning, not measurement.
- **From the full list** there's no upper limit. Each pick that misses while the offer stands readies one more follow-up, and that replaces the offer. `test_S7`: 5 seen after 4 picks, and still contested. Each one takes an answer from the learner, so the rate is at most one offer per answered miss.
- R2-M1 can add one more offer per job's decision until it's fixed.

### Checked and found sound

- **First review's reproductions.** Rerun on the tip. R2, R3b, R4, R5, R6 and R9 now fail their assertions because those pinned the bugs, and their printed output shows each fixed. R10 draws no block, and B1's `SomethingElsePeek` goes 2 to 2 in both flag states. R7 still gets `not_found`, which is what M2's page now handles.
- **Draws on reads.** Mixed fixtures (4 written probes, 3 need items): 25 reads gave 2 draws, then 0. Over four day rollovers with nothing answered, no objective draw. `test_stress.py` ran 24 random sequences of reads, serves, answers, Not now, arrivals and rollovers, and repeated reads after each step. One run flagged reads that kept drawing: blocks holding one item the fixture had already answered that day, which the fake pool keeps offering and the plan resolves at once. No offer or follow-up was involved (`none:ceiling_bound`, no workflows). It would need the real scheduler to re-offer an item answered that day, which I didn't test. The draw state lives in the ledger, so a restart changes nothing, and I didn't run one separately.
- **`_followups_lost`.** A real written probe with the real `waiting_still_valid` loses a contest, and then "Not now", a seen rollover and an unseen rollover each lead to it being served (`test_S6b`). The first goes straight to the probe, the other two on the next step. After repeated "Not now" the ceiling ends the competition and the follow-up serves (`test_S2`, `test_S5`). An offer stands open at most until its day passes, so a follow-up can't wait on it for longer than that. In the stress runs, a probe left unserved at plan end was a fixture item displaced by the intent check.
- **Seen and unseen.** `on_screen`, `never_on_screen`, the ceiling and `days_since_last` agree. A decision counts once whichever way it was seen. A seen offer that is superseded counts against the ceiling and writes no response. `record_shown` on a block that has ended is refused, so a race counts as unseen, as the spec says. The Rust passthrough exists.
- **`never_shown` readers.** `offer_report`, `LS.observations`, the decline recovery, `pending_start`, `offer_standing`, `respond`, forecast censoring (`offer_unanswered`), `router_card`, `suggestion_report` (TE1b decisions only) and `router_outcomes` treat the row as the plan's act. Both sweeps write it.
- **`_standing_view`.** Its reply is used only for `preference`: the phone doesn't store it for `waits_on_desktop` or `agreed`, and `stopped` and `served` carry a step and use `_current_view`. So `deciding: false` and `plan: null` reach nothing that polls.
- **M1 and M2.** No other path opens a read's item unserved. The desktop sidecar handles requests one at a time, so a read issued before the draw has landed before the page opens, and the page can't be closed by an older read. A stale page closes on the next read or the first tap.
- **`servedForExplicitStep`.** Used by Next and Not now. A second serve resumes the standing presentation, and a failed one leaves Today's Begin to resume.
- **m4's owed serve.** The retry serves once, the third call writes nothing, and each write has its own transaction after the placement's commit.
- **B1.** Feedback reads no plan. The link follows the held plan's flag, and nothing else on that screen reads the plan.
- **Switches.** One normalized scenario (open offer, follow-up arrives, answers, rollover) on main's own tree at `mvp-0.54`, compared with the tip at `mvp-0.54`, the tip at the tag with all six off, and the tip at the tag with only `lessons_compete_with_followups` off. Trail, events and responses match in all three. Decisions match too, except for `mixture.failure_rule` in the last, which is IH5's own key, on as configured.
- **The owner's rule.** No path maps a score, a miss count or a stuck flag to an action. What's still forced: requested items and randomized checks (§5 item 2), a decision of the follow-up's own that already weighed a lesson with no offer drawn since (§5), a phone's decisions, and the switch-off path. An arm is also absent over a check, a probe or a reading (§5 item 3). The `cold_failing` gate is already with the owner.
- **Merge record.** `6c8962ce95` is an ancestor, the merge changed no tree, and the files both sides changed differ from main only by IH's additions and edits.
- **Test runs.** `tests/test_ih*` and `test_te3b*`: 322 passed under `-n 4`. `lint-imports`: 43 kept, 0 broken. `tsc` clean on both apps. Vitest: the phone's `SomethingElse` (8), and the desktop's `App.offerPage`, `TodayPlace` and `dailyPlan` (70), all passed.

### Could not check

- Anything in a running app, on a real phone or with real models. No vault or real log was read, so how often R2-M1 happens and how many offers a real day shows are unmeasured.
- `router.log_decisions = false` beyond one run, which ended `done` with no offer drawn. I couldn't reach an offer with logging off, so I can't rule out a redraw there, since `lost_offer_decision` would return None.
- A rollover with a real written probe was run with a moved clock on a frozen-clock fixture, not through a full day's session.
- The durability lane, the full suite, and the phone host racing the desktop.

**For landing, not a defect.** `main` has moved to `bbb31ace19` (the test-suite audit). `git merge-tree` against it reports one conflict: `tests/cli_help_snapshot.json`, deleted on main and modified here.

### Outcomes (fixes on `instruct/handoff`)

Each finding was reproduced first with the review's `test_S*` cases, and each fix has a test that fails on the code before it. Commit `f837a8a7b4`.

| Finding | Outcome |
|---|---|
| R2-M1 | Fixed. See below. |
| R2-m1 | Fixed. *Not now* serves only an item inside the block, so under a hold it stays a read and Today says a question is in progress. Feedback's Next under a hold still decides, as IH6 says, and its served step now opens instead of leaving a presentation running behind the block line. |
| R2-m2 | Fixed. Every open workflow that lost to a replaced offer moves to the new one, found through its `lesson_offer_won` event, with or without a question written. No job runs while the lesson stands. |
| R2-m3 | Fixed. A phone's agreement counts as a request, on the drawn offer's own card, because no offer was on that screen. See "Double counting" below. |
| R2-m4, closed plan | Fixed. A retry serves what it owes only while the block is open in an open plan. Otherwise it answers with no step, and the plan view says where things stand. The review named only the closed plan; a block that has ended is the same case. |
| R2-m4, another option | Fixed. See "Why a new key" below. |

**What now enforces at most one open offer.** Every offer's block is written through `engine._persist_block`, and `_replace_open_offers` runs there, inside the decision's `BEGIN IMMEDIATE` transaction. Any offer still open ends `superseded`, naming the new decision (§5 item 1's mechanism), so the newer draw stands. Each decision keeps the propensity it logged and the replaced offer gets an `expired` row, so the plan's act can't reach the acceptance model as an answer. `tests/test_ih2_one_open_offer.py` runs a read or a job inside another decision's wait across outer, inner and both draws, counts open blocks from the tables, repeats reads, and checks that one answer gives one observation. There's no database constraint: an offer's being open comes from its events, and a constraint would need a second migration.

**Where this differs from the suggested fix.** The review suggested ending any open offer in `_boundary`'s transaction. Only a decision that writes an offer does that. A boundary decision that draws a block leaves a job's offer open, and the offer comes first. That decision may never have weighed that lesson, and a phone's decision must not end a desktop offer.

**New in this pass, not in the review.**
- **The reverse race fails the call.** The review expected a job's offer placed under a serve's `_boundary` to leave two open offers. In fact the block's stale ordinal hit the unique index on `(daily_plan_id, plan_ordinal)`, so the whole decision failed and Next or the read raised `IntegrityError`. That same failure was also the only thing stopping two boundary decisions from both landing. Reading the ordinal in the transaction would have removed that guard, so there is now an explicit one: a boundary is decided once (`_refuse_a_taken_boundary`, `BoundaryTaken`). The later decision is dropped with nothing logged, and the step is what took the boundary. A job's offer doesn't count as taking it. Its model calls are spent with no record, as they were on the failure.
- **Off, or below the tag,** all of this is the predecessor's, including that `IntegrityError`, and a test pins it.
- **An offer's place is read at its write.** One replacing an interrupting offer keeps that offer's place, where it would have fallen behind the block. One that finds a check block below it doesn't come first (§15.1a).

**Double counting (R2-m3).** A phone's agreement and a later desktop answer to the same offer are one wish, so they give one observation: the request counts until the learner answers, and from then on the answer counts. Decisions drawn before the answer still read the request, and each has frozen what it read. `ignored` isn't an answer, since it's the plan reading a card passed over, so the request and the pass both stay. They are two acts, and one says the other's opposite. The review left this for the owner to rule on; this is the reading that follows §7's own reason for leaving agreements out, and it's one condition to change if the owner rules otherwise.

**Why a new key (R2-m4).** The key names one act. A lost reply followed by a tap on another option means the learner changed their mind, and replaying the first choice would give them what they just left, with no message. Both clients now start a new key when the kind changes. If the first reply had in fact landed, both preferences are on record, which is true of what they did, and the first block stays planned as any pick's does. If the first choice was stop, the plan has closed and the second tap is told so. `choose` refuses a known key with another kind. Retrying the same option keeps its key, as before.

**Left as it is: a lesson taken during the wait.** A read draws an offer, the learner taps Start, and a job whose decision started earlier then draws the same lesson. One offer is open, but it offers a lesson just taken. Reproduced with fakes: `open 1`, step `lesson_offer`, observations `[True]`, workflow still `waiting`. It needs the read, the page and the tap all inside one decision's wait. Dropping that draw would need a new rule on the offer's ledger, so I left it, and §5 names it.

**Left for the owner, unchanged:** whether `w_pref` acts or stays report-only; whether a learner-asked lesson uses IH7's diagnosed sections; whether an open Reader problem holds decisions when no session is open; the `cold_failing` gate at `lesson_suggestion.py:198`; a decision replacing an open offer skipping the daily ceiling.

## The owner's decisions on what was left open (Nov 9)

The five questions both reviews left for the owner were decided on Nov 9. Spec §1 holds the owner's words and §8 rows 4-8 the outcomes. `w_pref` acts as built, and the owner watches it in the data-capture report. A lesson asked for with "learn this" reads IH7's sections from the latest diagnosed miss on its topic (§7c). An open Reader problem holds reads with no session open, but only if it was touched on the plan's day (§7b). The `cold_failing` gate is removed: any missed cold check since the last lesson makes a candidate, under its own switch, and §7d states what the numeric policy and the card can and can't see of a slip. A replacement skips the ceiling, as built.

## Third review (owner decisions)

**Tip reviewed:** `17684910a7` on `instruct/handoff`, the stage `git diff 3b6c18e70b 17684910a7 -- src apps tests` (decisions 2, 3 and 4).

**Result:** no blockers, 3 major, 5 minor. M1 and M2 are code fixes. M3 is the spec's §7d claim, which the owner will rely on and which is wrong as written. m5, the flaky test, will sometimes fail the landing gate's full suite, so fix it before landing.

Reproductions are in `/tmp/ihreview3/py/` (scratch, not committed): `test_repros3.py` (R1-R5) and `test_flake.py`. They run like the earlier reviews' repros, with fakes and no model call.

### Major

#### M1. "Learn this" on feedback reads an older miss while the latest one's diagnosis is still being written, and the record doesn't say so

`src/learnloop/teacher/diagnosed_sources.py:317-341` (`_latest_diagnosed_miss`), called at `:373`.

**What goes wrong.** The owner's words are "use the latest miss on that topic". The code instead takes the latest attempt that already has a live diagnosis in force. "Learn this" is offered on the feedback screen, right after the miss. The lesson opens at once, without waiting for the diagnosis (§3a: the serve waits for it, the lesson doesn't). So in the main use of decision 2, the answer the learner is looking at usually has no diagnosis yet, and the lesson reads whichever earlier miss on the topic was diagnosed. There is no age bound: it can be weeks old, on another item, with a confusion that has since been settled (a validated hypothesis whose misconception was resolved still counts). The preference row already names the attempt the learner was looking at (`router_learner_preferences.attempt_id`, written by `learner_action.choose`), but nothing reads it. §7c labels this as a limit and says "the record names which attempt it read". That is true, but the record never says that a newer miss was passed over.

**Verified.** R1: a diagnosed miss from a month earlier, then the latest miss with its live diagnosis job still `queued`, then a preference naming that latest attempt, then the lesson opens. The result is `status added`, `miss.attempt_id` = the month-old attempt, and the latest attempt's id appears nowhere in the record.

**Fix.** Use the preference's `attempt_id` when there is one, and the latest attempt on the topic when there isn't. Don't read a score to decide this. If that attempt's diagnosis is pending, record `PENDING` as the router path does (`_why_no_diagnosis`), and optionally follow again once it lands. Skip an attempt only when it has no diagnosis row at all, which is what a correct answer looks like. At the very least, add a `passed_over` list (attempt id and why) to the record.

#### M2. "Since the last lesson" counts the lesson's own probe misses, so a lesson's placement miss makes its topic a candidate again as soon as it closes

`src/learnloop/daily_plan/lesson_suggestion.py:145` (`missed_since`) against `lessons.opened_at` (`db/stores/router_suggestions.py:230`).

**What goes wrong.** TE2's in-lesson probes are recorded as `diagnostic_probe` attempts (`teacher/probes.py:49`). That is a cold type (`lesson_weight.COLD_ATTEMPT_TYPES`), and the attempt is unprimed with no hints. The boundary is when the lesson opened, so a probe missed while the lesson is open is "a missed cold check since the last lesson". When the lesson closes, the topic is immediately `cold_missed`, and its offer says "A recent check on it didn't come out right.", about a question the lesson asked in order to place the learner. `_cold` also ignores `diagnostic_exposure`, so a probe answer the system itself records as not independent (asked after the lesson showed text) still counts. The predecessor had the same boundary, but it needed two cold misses in a row. Now one placement miss is enough, and placement probes exist to find what the learner doesn't know.

**Verified.** R2: a right answer, then a lesson, then a `diagnostic_probe` attempt scored 0 five minutes into it, then the lesson closes. On: `lo_det: cold_missed`. Off: no candidate. The `diagnostic_probe` type was set on the row directly; the probe's real writer was not run.

**Fix.** Measure from the lesson's close (`coalesce(closed_at, opened_at)`; an open lesson already excludes its LO), or leave out attempts made while the lesson was open. Also decide whether an answer recorded as not independent is cold. Add a test for each.

#### M3. Spec §7d's central claim is wrong as written

`docs/specs/spec_instruct_handoff_v1.md:290-292`. See "Verdict on §7d" below. In short, the lesson offer's value can't tell a slip from a gap at the same grade, but the support it competes in can: after a gap, a repair block on the topic is a candidate, and after a slip it isn't. The claim should be narrowed before the owner relies on it.

### Minor

**m1. The reason's words aren't true for every `cold_missed` candidate.** `lesson_suggestion.py:73`, `:218`.
- A cold check at 0.8 or above but below 1.0 is a success to AD, and the LLM's card calls it `correct` (`adaptive_difficulty/outside.py:160`). Yet the offer row beside it says the check "didn't come out right". R3: 0.9 gives `cold_missed` and the card says `correct`.
- With no recency, "recent" is false too. R4: one miss 200 days ago with ten right answers since is still `cold_missed`.
- Candidacy never lapses short of a lesson, and any partial credit counts. Over time the pool therefore approaches "every practised topic", which weakens §7d's own reason for choosing "missed" over "attempted".

Fix: words that hold for every case (for example, "A check on it since your last lesson wasn't fully right."), and say in §7d that the pool grows this way.

**m2. A topic below its band that also has a miss is relabelled `cold_missed`.** `lesson_suggestion.py:218-226`. The branch order hands such a topic to `cold_missed`. It then loses its `band` record and reads `reason_cold_failing` in place of `reason_below_band`, so its `P(accept)` and its words change. Under the predecessor this happened only after two misses in a row; now one partial answer is enough. This is from the code: AD's subject view isn't live in the fixture. Fix: document the precedence in §7d, or record both reasons.

**m3. A preference id is accepted for any later lesson on its topic.** `diagnosed_sources.py:301-314`. Nothing ties a preference to one lesson or checks its age. R1b: the same id gives `added` five minutes later and again two weeks later. Today only `lessonEntryFor` sends it, so the harm is low. Fix: accept a preference for the first lesson it opens only, or record its reuse.

**m4. Decision 3's day boundary is an hour off on daylight-saving change days.** `daily_plan/engine.py:612-617`, now read at `:5119`. `astimezone()` takes today's UTC offset, and `replace(hour=0)` applies it to midnight. Under `TZ=America/New_York`, Nov 1 2026 gives `05:00Z` where midnight was `04:00Z`, and Mar 8 2026 gives `04:00Z` where it was `05:00Z`. A Reader problem touched in that hour is counted on the wrong day. The function is inherited. Fix: `datetime.combine(local_now.date(), time()).astimezone()`.

**m5. The IH4 twin tests are unsound.** See "The flaky test" below.

### Verdict on §7d

**Refuted as written. True in a narrower form: "a slip and a gap at the same grade give the lesson offer the same value, and the support it competes in differs."**

What holds:
- **Which candidate becomes the offer.** TE1b's staged value picks it (`LS.score`: `log P(accept) + log(1 − p)`, ties by ref). `P(accept)` reads the reason, which is one effect for every cold miss, plus the context and the declines. `p` comes from the mastery EKF, whose reliability weight is assistance.
- **The offer's numeric value.** It reads AD's posterior (ordinal categories at 0.8 and 0.4), `γ`, the mass and TE3a's curve.
- **No diagnosis reaches either.** Nothing in `adaptive_difficulty` (outside its table-classification modules), `learner/mastery.py`, `router_objective/value.py`, `daily_plan/objective_inputs.py` or `router/lesson_suggestions.py` reads `causal_hypotheses`, `attempt_diagnoses`, `cause_scope`, error type or severity. `router_objective/decision_state.py` reads misconceptions for its receipt only.

What fails:
- **The support depends on the diagnosis's causal class.** With the diagnosis split on, `engine._open_problems` (`engine.py:1097`) takes `open_diagnosed_problem_learning_object_ids` (`db/stores/daily_plans.py:318`). That counts only `cause_scope = 'learner_state'` hypotheses, plus open unresolved-cause factors.
- **The repair lane follows from it.** `lanes.py:269-270` puts the topic's previously attempted items in the repair lane only then, and `objective_inputs.py:646` values a repair block as `V.REPAIR`.
- **The LLM sees it too.** The LLM's option for that block reads "Another go at something still unclear in {topic}." (`router/why.py:32`).
- **Reproduced.** R5, the same 0.75 answer on the same topic: diagnosed `learner_state`, the repair-lane LOs are `['lo_regions']`; diagnosed `transient_execution`, they are `[]`. So after a gap the lesson competes with a repair block on the topic, and after a slip at the same grade it doesn't. Numeric's argmax and the LLM's options can differ.
- **The spec's framing.** §7d mentions this only as "staged's repair lane". In fact it is the support that staged's top-k, numeric and the LLM all choose from.
- **Not run end to end.** I didn't run it through a full decision. Whether the block reaches the support also depends on the scheduler's eligibility and staged's top-k.

Corrections to the LLM paragraph:
- **Probe and exam answers.** For `diagnostic_probe` and `exam_attempt`, both cold types, the card shows the result only, with no stem and no answer (`history_card.py:26-29`). So "the LLM can see a slip in the answer itself" doesn't hold for them. That includes every follow-up probe after a miss.
- **Result buckets.** The card calls 0.8 and above `correct` (m1).
- **No reference solution.** The card carries none, so a slip is visible only where the stem excerpt and a 300-character answer excerpt show it.

### The flaky test

**The builder's explanation is wrong, and the test is unsound.** `tests/test_ih4_preferences_inform_router.py:459-467` runs with no models (`fake_runtime` with no decider or LLM). On that path the numeric policy runs on the calling thread with a 40 s deadline and no `keep_going` (`objective_chooser.py:1376`). It completes one batch of 8 draws for every decision on both twins: every trace says `precision.draws = 8`, with or without load. A deadline could only cut the first batch (`complete = False`), which would fail differently.

**The cause is RO6's deferred carried valuation.** In the no-model branch, `_defer_carry` starts a daemon thread after each serve (`objective_chooser.py:1407-1414`). The next decision records the valuations that have landed (`_carried_for`), and its residual fit reads them. Whether the thread finishes before the next decision is a race. Even unloaded, decision 2 misses decision 1's carry and decision 3 picks up two.

**Reproduced.** `test_flake.py::test_slow_carry_thread_in_one_twin` delays only one twin's carry thread by 4 s, with draws still 8. Decision 4 then differs at `residual.fit.coef` and at every candidate's `v_residual` (0.0 against −0.70). `test_w_pref_at_zero_changes_nothing_bit_for_bit_with_preferences_on_record` (`:500`) has the same run and comparison, so it is exposed the same way. I didn't run that one.

**How to pin it.** Pinning the draw count won't help. Run the carry inline in these tests: a `threading.Thread` subclass whose `start()` calls `run()` for the thread named `learnloop-objective-carried`, monkeypatched for the run, or join that thread after each serve. Verified with `test_slow_carry_with_the_carry_drained_inline`: with the same one-twin delay, the numbers are equal. Dropping `residual` from `_numbers` would also stabilize the test, but it would stop checking what the test claims. In serving, this timing dependence is RO6's by design and is recorded in each trace, so replay stays exact. It isn't this stage's defect.

### Checked and found sound

- **Decision 4's condition.**
  - `missed_since` asks only whether a cold check since the lesson was below 1.0. There is no count, slice, severity, error type or stuck flag, and the attempts it reads carry none.
  - The acceptance model maps `cold_missed` to the existing `reason_cold_failing` effect. The prior and its centre (0) are unchanged.
  - Old rows replay unchanged: `observations` rebuilds each candidate from its stored `reason`, and `cold_failing` sets the same term as before.
  - `REASONS` has no other consumer.
  - Off and below the tag, the branch is the predecessor's expression verbatim.
  - Declined, superseded and `never_shown` offers don't reset "since" and are never read as declines (`expired`).
  - The tag-only gate reaches TE1b's daily card and IH3's option, as §7d says.
- **Decision 2's scope.**
  - The lesson's topics must equal the preference's one LO exactly. So another topic's miss can't be read, and `add_topics` makes the check fail (fail closed).
  - Unknown, missing or non-lesson ids give `NO_REQUEST`.
  - The service drops the id for a selection, a typed goal or a suggestion's Start, and so does the sidecar.
  - `LessonScreen` forwards the id only from `lessonEntryFor`, and the phone has no lesson path.
  - The found attempt passes `PastWork.attempt_reason`, so a probe or exam attempt ends the search rather than being skipped. `analysis_md` stays unread, and the Library scope is unchanged.
- **Decision 3.**
  - With no session open, only `origin = 'reader'` problems hold, and one from an earlier day holds nothing until it is worked again.
  - A serve still decides. `TodayPlace.begin()` with no session starts one and serves.
  - Once a session starts, membership is the session's.
  - The gate returns None before reading anything when off or below the tag.
- **Runs.**
  - pytest: `test_ih_lesson_candidate_after_cold_miss`, `test_ih7_*` and `test_ih6_*` (93 passed); `test_ih5_successor`, `test_teacher_te1b_suggestions` and `test_te3b_offers` (62 passed).
  - vitest: `LessonScreen`, `SomethingElse` and `FeedbackScreen.somethingElse` (34 passed).
  - `lint-imports`: 43 kept, 0 broken.

### Could not check

- How often the diagnosis is still pending when "learn this" is tapped (M1), and how often TE2 probes are missed before the teaching rather than after it (M2). No vault or real log was read.
- R5 through a full objective decision, and the flake under real CPU load. I used a deterministic delay instead of loading the shared desktop.
- Anything in a running app, the durability lane, or the full suite.
