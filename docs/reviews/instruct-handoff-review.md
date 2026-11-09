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
