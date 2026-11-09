# Instruct hand-off (IH): the router's lesson reaches the learner, and the learner can answer back

**Status:** draft, Nov 8 2026. Not reviewed, not queued. All owner decisions are made (§8).

## 1. The owner's decisions

Verbatim, Nov 8 2026:

> We shouldn't have the action router forced into decisions with hard coded rules (like if you get 0 n times, serve instruct). The action router served instruct at one time, it just wasn't clearly acted upon within the UI to give to the user. As a form of further telemetry/data collection, we should allow the user to suggest what they would think would help them to the action router (like an override where you can choose the action router) which we can then log and use to inform the non-LLM parts of the action router. The offer it where you are is something I agree--instruct should start immediately after the feedback screen with "This looks like something to learn. Start a 15 minute lesson on X?"

What this rules out: any rule that maps a score, a miss count or a stuck flag to an action. Being stuck reaches the router only as evidence. The router may still draw something other than a lesson.

Also verbatim, Nov 8 2026, answering §8:

> lessons should compete with follow ups whenever a lesson is available. For 3, the LLM should see my recent preferences and notes as context.

And on question 2 and the proposed fallback change (§7a), Nov 8 2026:

> yes add it to the spec and mark question 2 as no

And on the router's wait (§3a), Nov 8 2026:

> let the LLM process for up to 40 seconds so that we don't get these timeouts

> Apply to all vaults and make it the new default

> add the phone prefetch to the spec and correct the notes. implement the spec via subagents as you see fit (Opus and sonnet subagents)

## 2. What happened (`arxiv_v2`, Nov 7-8)

| Local time (EST) | Record | Meaning |
|---|---|---|
| Nov 7, 9:16 and 9:41 am | Two attempts on `lo_render_a_classifier_s_decision_regions`, both 0; the second declared stuck | Evidence of not knowing the material |
| Nov 7, 9:11 and both 9:43 am decisions | Logged LLM status `timeout`; staged weight 0.8. Every call completed (13.2, 14.8, 11.6 s), after the serve stopped waiting at 8 s, and its answer was discarded | The LLM was not down: it was not given enough time (§3a). The lesson was not yet a candidate at 9:11, then got about 2% at 9:43 |
| Nov 8, 12:34 pm | `workbench_resumed` on the ReLU question | Work in progress |
| Nov 8, 12:37 pm | `01M6Y3SJNC6SVADXFW44VM3NTZ`: lesson offer drawn (LLM 0.43, propensity 0.33, `daily_plan`) | The router chose instruct |
| Nov 8, 1:08 pm | `workbench_closed`; attempt scored 0, stuck, empty | Next evidence of not knowing |
| Nov 8, 1:09:07 pm | Generated probe ready (`need` fulfilled) | Becomes a forced item |
| Nov 8, 1:09:10 pm | Block ended `withdrawn`, response `expired`, reason `forced_items` | A hard rule cancelled the router's choice |
| Nov 8, 1:13 pm | Next block: `lesson_offers: none:forced_items` | The same rule kept lessons out of the next decision |

The offer block has no `block_started`, so no step ever served it. An open offer also renders on any Today read (`view.py:148`) and that leaves no record, so whether the card was seen is unknown.

## 3. The hard rules this spec removes

Both are the kind of rule §1 objects to, and both already exist:

- `src/learnloop/daily_plan/lesson_offer.py:241`: forced items mean no offer is considered.
- `src/learnloop/daily_plan/engine.py:4826`: forced items arriving later withdraw a drawn offer.

A third is related. `plan_interrupt` is logged as `staged_v1` with `insert_now` as its only feasible candidate, so it decides nothing (Nov 7, 9:17 am: propensity 1.0).

## 3a. IH0: the LLM gets time to answer

**What the log shows.** The five objective plan decisions' LLM calls took 11.6-15.8 s and all completed, while a serving step waited 8 s. On Nov 7 the phone's three decisions gave up 1.5-7 s before the answer arrived. The two desktop decisions on Nov 8 were in time because the job had long finished. Five calls are a small sample.

1. **The wait is 40 s.** `router.timeout_seconds` defaults to 40, and the owner's three vaults set it (owner decision, Nov 8). It is operational in the parameter registry, with no measurement authority. `prefetch_timeout_seconds` stays 45. A serve stops waiting as soon as the job finishes, so 40 s is reached only by a stalled call.
2. **The phone starts the job while feedback shows.** The desktop's prefetch is `next_plan_item{serve: false}` (`app/dailyPlan.ts:105`). The phone makes no peek, on purpose: a read at a finished block crosses a boundary and writes its decision (`apps/learnloop-mobile/src/api/phone.ts:127`, `spec_mobile_frontend_v2.md` §4.5). On Nov 7 the phone sat on feedback for about 100 s, then started the call when Next was pressed.
   - Add a host RPC, `plan_prefetch{sessionId}`, that **starts** the boundary's objective job under the phone's device filter and origin, then returns at once.
   - It writes no `router_decisions` row, block event, presentation or serve, and it returns no step. It is idempotent, and it is a no-op when the next step is not a boundary or no model is set up.
   - The phone calls it after the grade lands and while feedback shows, never earlier: the decision depends on the outcome just graded (§4.5). A failed call is ignored.
   - Next's existing serve then finds the job by its prefetch key. The key must match the serve's, or the prefetch is wasted, so a test pins that.
   - If the key cannot be computed without a write, stop and report instead of relaxing "writes nothing".
   - **As built.** `daily_plan/engine.py::prefetch_boundary` walks `advance_with_context`'s path to the chooser on a read-only attach (`Repository.attach(read_only=True)`), so a write fails at the database, with the chooser `start_only` (`objective_chooser.py`). `reconcile`'s events are folded over the stored ones in memory. The reply's `reason` says why nothing started. What only a write can settle ends the walk and the serve decides as before: a moved reading, the day's first randomized-check draw or a check placed at this boundary, an AD deferral re-read, an offer the sweep would mark `ignored`, a waiting follow-up. `due_followup_tasks`' two lazy status marks are skipped on a read-only attach; they change nothing it returns. The host also no-ops while the session's diagnosis is out and the phone fires once it settles, since the serve waits for that diagnosis and what it finds can change the key.
3. **What remains.** Steps with nothing to start early, such as Keep going, wait up to 40 s on "Choosing what's next…". The cost of the prefetch is an LLM call for a boundary the learner may not reach, as on the desktop.

## 4. IH1: the offer page (no change to what the router decides)

1. When Next on the feedback screen resolves to a `lesson_offer` step, open a full offer page. Today it falls through to the Today screen (`app/dailyPlan.ts:78`, `app/App.tsx:1229`), where the card is one element among others.
2. The page reads: **"This looks like something to learn. Start a {minutes} minute lesson on {topic}?"** `{minutes}` is the offer's own duration estimate. Below it goes the router's rationale, when its guard allows showing it.
3. Actions: **Start** (opens the lesson at once through the existing `lesson.suggestion_respond`), **Not now**, up to two other topics, and "Something else would help" (IH3).
4. Starting takes one tap. A lesson never starts unasked.
5. The Today card stays for offers reached from Today.
6. Add an `offer_shown` block event, written when the card or page renders, with surface and time. `block_started` does not answer whether the learner saw it.
7. An offer never appears over an open item. Step 0 of the build: find what triggered the 12:37 pm draw during an open workbench session, and draw at the item's close instead if that read was the cause.

## 5. IH2: offers and follow-ups compete in one decision (algorithm change)

Follows `docs/algorithm-change-playbook.md`: new `mvp` tag and replay.

1. **Redraw instead of withdrawing.** When a follow-up becomes ready while an offer is open, the next boundary makes a new decision whose support holds both. The unanswered offer's response records `superseded_by_decision`, and the plan's act stays out of the acceptance model, as withdrawal does today.
2. **Forced follow-ups become candidates** at a boundary where a lesson is available. The objective and the two-policy mix choose, with exact logged propensities. Items the learner requested and randomized checks stay forced: those are the learner's act and the experiment's design.
3. **After a miss, the post-feedback Next is a real decision.** `plan_interrupt` gains the lesson offer as a candidate, and the router draws. This is the only way a lesson can follow feedback in mid-block, since plan decisions otherwise wait for block boundaries. The router already decides before the item is generated (`followup_run/router.py`), so a lesson that wins costs no generation.
4. **A value for probes.** The Nov 7-8 traces only hold the kinds `review`, `new_practice`, `repair`, `stop` and `lesson`. The build must confirm against RO §8.1 whether a probe interface exists and add one if not, using RO's existing machinery with no new constants.
5. **Latency.** The offer uses IH0's wait and the prefetch's existing budget. A call that still fails falls back as IH5 says. Router speed stage 2 is separate.

## 6. IH3: "Something else would help" (capture and override)

1. **Where:** on the feedback screen and at any plan boundary, one quiet link. Never a modal.
2. **What it offers:** that boundary's actual candidates in plain words (learn this, another question, review something earlier, something new, read the source, stop), plus an optional free-text note, in keeping with learner text over skip buttons.
3. **Effect:** the choice is served. Learner picks already win (`daily_plan/engine.py:16`); this extends them from one item to an action.
4. **Logging:**
   - A new append-only table, `router_learner_preferences`: `id`, `decision_id` (nullable: no draw may exist yet), `attempt_id`, `session_id`, `surface`, `offered_json` (refs, with the router's probabilities when known), `chosen_kind`, `chosen_ref`, `note_md`, `served_decision_id`, `algorithm_version`, `created_at`. Classify it in `db/table_roles.py`.
   - The served action is a `learner_pick` decision with `propensity_kind='none'` and its `parent_decision_id` set, so `router_outcomes` already reports the parent as `overridden`.
5. **Phone:** the phone logs preferences too. Lessons on the phone are phone V6; until then it holds offers for the desktop (`scheduling/device_eligibility.py:228`). A phone "learn this" is logged, and the phone says plainly that the lesson waits on the desktop.

## 7. IH4: how preferences inform the non-LLM parts

Two facts stay separate. "I would take this" is about acceptance. "This would help me" is a claim that needs checking against outcomes.

1. **Acceptance:** an unprompted request for a lesson updates TE1b's acceptance model, flagged as unprompted. That model shows `updates: 0` today.
2. **Choice model:** `P(chosen kind | decision features)`, with seeded priors and the same form as the acceptance model, frozen as a sensor in the decision trace.
3. **Entering the value:** through one learned coefficient, `w_pref`, which starts at 0 like RO6's `w-hat` and is fitted on cold-outcome residuals. A preference shifts the numeric policy only as far as the outcome data supports. No hand-set bonus for following the learner.
4. **What overrides can't show:** picks are self-selected and carry no propensity, so they stay out of `w`'s scoring and out of any causal claim. Comparisons of an override with a router draw of the same action carry RO5's `self-selected` label.
5. **Report:** a `learnloop data-capture report` section with router-versus-learner agreement by kind, override rate, follow-through and later cold results.
6. **The LLM's context (owner decision, §8.3):** the router's LLM card carries recent preferences and notes as context, marked as the learner's own statements.

## 7a. IH5: the LLM's share falls to numeric, not staged (algorithm change)

Follows `docs/algorithm-change-playbook.md`: its own `mvp` tag, a kill switch and replay. It amends the failure rule in `spec_router_objective_v1.md` §8.3, "Each failure moves only that policy's share" to staged.

**Why.** RO gives staged no serving share, yet it served 3 of the 5 objective plan decisions on Nov 7-8, each because the serve stopped waiting for an LLM that then answered. Numeric answered all five and disagreed with staged on those three. Staged can never pick a lesson (`daily_plan/objective_chooser.py:1145`), so whenever the LLM has no valid answer in time, 0.8 of the mix can't choose instruct. Five decisions from two days are a small sample: this shows what can happen, not a stable rate.

**IH0 comes first and should make this rare.** IH0 removes the cause seen on Nov 7. IH5 is the backstop for what remains: a stalled call, an invalid answer or a failed card build.

**The change** (`src/learnloop/router_objective/mix.py:39`):

| Failed | Today | After IH5 |
|---|---|---|
| Neither | LLM `w`, numeric `1 − w` | The same |
| LLM | Staged `w`, numeric `1 − w` | Numeric 1.0 |
| Numeric | LLM `w`, staged `1 − w` | LLM 1.0 |
| Both | Staged 1.0 | The same |

The uniform floor `ε` applies in every row, and propensities stay exact.

**What stays:** staged remains the last resort when both policies fail, and its pick is still logged on every decision as the baseline. Its ordering still limits the top-k support and breaks numeric's ties (§9).

**What this costs.** `π_Q` is an argmax, so with no LLM answer a decision is almost deterministic apart from the floor. That is less exploration than the LLM's distribution gives, and the same concentration staged has today. Numeric's picks are also largely untested on real outcomes.

**Replay's limit.** Replay can recompute each logged decision's `μ` under both rules (`mix.py:118`) and report how often the served choice would change. It can't show that numeric's picks would have taught better. The data capture report splits outcomes by `drawn_component` from this tag on, so the comparison builds up after landing.

## 8. Owner decisions

| # | Decision | State |
|---|---|---|
| 1 | The Nov 3 decision has follow-ups generate and serve at once after a miss. Does IH2 replace that wherever a lesson is available? | **Decided Nov 8: yes.** Lessons compete with follow-ups whenever a lesson is available. Where none is available, the Nov 3 behavior stands. |
| 2 | Does the staged policy read preferences too? | **Decided Nov 8: no.** Numeric only. Staged is fixed rules, so using preferences there would need hand-set thresholds. IH0 and IH5 remove most of the cost, since staged stops serving in the LLM's place. |
| 3 | Does the LLM card show recent preferences and notes? | **Decided Nov 8: yes,** as context (§7.6). |

## 9. Not in this spec

- **Rules from scores or miss counts to actions.** Ruled out by §1.
- **Repair suggestions not appearing on the phone.** The code exists (`apps/learnloop-mobile/src/practice/FeedbackScreen.tsx:225`) and the cause is unknown. Investigate separately.
- **`first_intervention` taking priority over `ladder_entry_stage`** (`scheduling/staged_policy.py:228`). Read from the code, not run; review separately.
- **Staged's ordering of the top-k support.** It limits what the LLM and numeric see, and IH5 doesn't change that. How often it hides a good option hasn't been measured; review separately.

## 10. Order and tests

Build order: IH0, IH1, IH5, IH2, IH3, IH4. IH0 and IH1 address the visible failures and change no decision rule. IH5 is small and independent. IH2 is the largest change to what the router decides. IH3's capture comes next, since data starts accruing as soon as it lands. IH4 needs IH3's data path, and its coefficient simply stays near 0 until data exists.

- **IH0:** `plan_prefetch` writes nothing in any decision table (row counts pinned across the call); a later serve finds the job and uses its answer without starting a second LLM call; it is a no-op in mid-block; it is allowlisted on the phone host; a slow fake LLM that answers within 40 s is served rather than falling back.
- **IH1:** a `lesson_offer` step opens the page; Start opens the lesson; `offer_shown` is written once per render path; no offer appears over an open item.
- **IH2:** replay this trace's shape, with a probe arriving during an open offer. The result must be a new decision holding both candidates with exact propensities, and never a `withdrawn` block with reason `forced_items`. A test also asserts that no code path maps a score or stuck flag directly to an action.
- **IH3:** an override serves the action, writes both rows in one transaction and is idempotent on retry; a preference with no draw is stored with a null `decision_id`; the phone hands a lesson pick to the desktop.
- **IH4:** with no preferences the decision matches the previous tag exactly; `w_pref` at 0 changes nothing; picks never enter `w`'s scoring.
- **IH5:** each row of §7a's table produces its weights, with the floor kept and exact propensities; a lesson offer in the support can be drawn with the LLM down; with the switch off or below the tag, the mix matches the predecessor exactly; a logged decision replays to its logged `μ` under its own tag.
