# Recognition, effort and memory (RE)

**Status:** draft, Nov 8 2026; placement decided Nov 9, RE0 building; §10's other decisions open. The owner asked for all of `docs/brainstorming/Colin Galen.md` plus `S_eff` to become one spec, "maybe after the refactor". §10 lists the decisions still open. Nothing here is built.

**Source:** `docs/brainstorming/Colin Galen.md`, which holds the evidence, the video timestamps and what was rejected. This spec holds only what to build.

## 1. The problem

Three gaps, found in the review and checked against the code on Nov 8 2026:

1. **Little practice at recognizing which idea a problem needs.** `method_selection` is 40 of 268 items but only 4 of 94 attempts. 17 of 19 consecutive attempts in a session were on the same concept, so context can give the method away. A rep costs a full written answer.
2. **The value model can't see effort.** Every graded opportunity earns the same `γ`, so a 30-minute honest attempt and a one-minute guess are worth the same, and the longer one pays more attention price.
3. **Good surfaces exist that can't be reached.** The objective router has never had a teach-back candidate on real data, because nothing creates the items.

## 2. Rules every stage follows

- **No rule maps a score, miss count or stuck flag to an action** (`spec_instruct_handoff_v1.md` §1). New actions are candidates the router or chooser draws, with exact logged propensities.
- **No made-up constants.** New weights start at zero or at an existing seeded prior, and are learned. Purely operational values are registered as `keep`.
- **Help is never certification.** The evidence tiers stay as they are.
- **Changes to persisted meaning follow `docs/algorithm-change-playbook.md`,** each with its own tag and kill switch. "Off" serves exactly as the predecessor.
- **Exam and held-out material is never served, quoted or used as supply.**
- **At n=1, no stage claims a benefit.** Each adds a section to `learnloop data-capture report`, labelled observational where nothing was randomized.

## 3. Stages and placement

| Stage | What | Persisted meaning? | When |
|---|---|---|---|
| **RE0** | Capture: active seconds and the cue label | No | **Before the refactor,** because data can't be collected backwards |
| **RE1** | "Leave it open" | No | After the refactor, beside the UX audit (owner, Nov 9) |
| **RE2** | One retrievability function | No | **Inside the Opus refactor** |
| **RE3** | Spot it reps and near-miss reps | Yes | After the refactor |
| **RE4** | The cue map | No | With RE3 |
| **RE5** | Teach-back offers | Yes | After RE3 |
| **RE6** | `search_move` hints | Yes | After RE5 |
| **RE7** | The effort coefficient | Yes | Once RE0 has data |
| **RE8** | `S_eff` | Yes | After RE2 and RE0 |
| **RE9** | Black-box steps in lessons | No (RE9b: yes) | Later |
| **RE10** | Rebuild checks | No | Later |
| **RE11** | Figures from memory | No | Later |

**Queue position (owner, Nov 9).** RE0 lands before refactor step 1, after IH. RE2 is a refactor step. RE1 and RE3-RE8 follow the refactor, beside the UX audit; the overhaul reviews their screens before it finishes, and Codex docs stay last. RE9-RE11 can follow or be dropped. The refactor's stated goal, that objective and router changes become easy, should make RE3, RE5 and RE7 smaller, which is the reason to wait.

**Why RE0 doesn't wait.** It's small and changes no decision, and every week without it is data that can't be recovered.

## 4. RE0: capture

**4.1 Active seconds on every attempt.** Only 19 of 94 attempts have a `latency_seconds`, and wall-clock time overstates work on a resumed problem (`probability` has attempts near an hour).
- Step 0: list which surfaces don't send latency. Clients that do include `PracticeScreen.tsx:1396`, `workbench/Workbench.tsx` and `handlers/teach_back.py`. Lesson checks and the phone need checking.
- Add a nullable `practice_attempts.active_seconds`, written as RO0 wrote its columns on older tables (`db/stores/router_objective.fill_receipt`), from the same active clock as RO's `m_a`. It sums across resumes. Never blend it with `latency_seconds`, as RO's two-clocks rule says (`spec_router_objective_v1.md` §3).
- **What reads it:** only reports, until RE7 and RE8. It reaches no AD state (A12).

**4.2 The cue label.** A pure function, `attempt_cue_v1(attempt, ledger)`, returns which cues were present:

| Field | From |
|---|---|
| `same_lo_before`, `same_concept_before` | The previous attempt in the session |
| `after_reading`, `after_lesson` | `reveal_events` and warmth sources, within the warmth window |
| `method_stated` | The item's frozen `required_method` |
| `followup_of_miss` | The follow-up binding |
| `randomized_check` | `policy_experiment_assignments` (RO5's draw) |

It is derived, so it needs no table or migration and works on old attempts. An attempt with every field false is **uncued**. The report splits `method_selection` results and goal-date reads by uncued against cued. A model reading whether the stem names the method waits for RE3.

**Tests:** the same ledger gives the same label; a synthetic trace with no cues present is uncued; `active_seconds` is unchanged by a pause or a day's gap; nothing in `adaptive_difficulty/` reads it.

## 5. RE1: "Leave it open"

**Correction to the review.** The review proposed adding this to IH3's list, but IH3 appears on the feedback screen, after the solution can be seen. Incubation needs the problem unsolved, so this belongs **on the answer surface, before submitting.**

1. **Where:** beside "I'm stuck" on the practice screen and the workbench. One quiet link: "Leave it open, come back tomorrow".
2. **Effect:** nothing is submitted, graded or revealed. The draft stays (`practiceDraft.ts`, workbench autosave), and the plan moves on.
3. **Coming back:** the problem appears in Today's threads, as a thread and never as debt (UX U12). `open_sessions` (`db/stores/workbench.py:161`) only lists problems with a source today, and `abandoned` isn't a thread. Extend it to problems from `practice` and `plan` origins, which means a practice-screen problem needs to open a workbench session or a thread of its own. Step 0 chooses between them.
4. **Scheduling:** an open problem isn't forced back. The router may still choose something else tomorrow. It stays out of ordinary draws while open, so the learner doesn't meet it by surprise.
5. **Coldness:** it stays cold if nothing was revealed, and any help already held stays counted (`attempts/hint_fold.py`). Time passing changes nothing.
6. **Logging:** a row in IH3's `router_learner_preferences`, `chosen_kind = 'leave_open'`, with no draw (`decision_id` null). If RE1 ships before IH3, it waits for that table.
7. **Report:** how often it's used, whether the learner came back, and later results, labelled self-selected.

The router has no value for this action, and this stage adds none.

## 6. RE2: one retrievability function

More than a dozen sites compute retrievability themselves: `learner_context.py:1572`, `scheduling/review_log.py:154`, `goals/goal_projection.py:404`, `scheduling/family_memory_model.py:77`, `scheduling/scheduler.py:2974`, `field/outcomes.py:740`, `daily_plan/objective_inputs.py:413`, `daily_plan/reentry.py:64`, `daily_plan/router_card.py:548`, `teacher/brief.py:329`, `router_objective/decision_state.py:115` and `router_objective/memory.py:274` (a vectorized copy, called hundreds of thousands of times a decision).

- One read function with a scalar and a vectorized form, sharing one definition.
- **Exempt:** FSRS fitting and its evaluation, which must keep reading plain stability.
- **No behaviour change.** Replay on the migration-head fixture is identical, and the objective's decision latency doesn't regress.
- A test fails on a new direct call to `forgetting_curve` outside the allowed modules.

**A required scope item for the Opus refactor** (owner, Nov 9), step in `refactor_strategy_v3.md`.

## 7. RE3: Spot it

**7.1 The rep.** One problem the learner hasn't seen, one text box: "The key idea, and what in the problem points to it." An optional confidence tap, as elsewhere. "I'm stuck" works as usual. Target: under a minute, on desktop or phone.

**7.2 Feedback.** Show the **idea card** at once: the key idea and the feature that cues it, authored with the item. Not the full solution. It doesn't wait for the grader. Then one optional line, "When I see __, try __ because __", goes to RE4. Below that, "Work it through" opens the workbench, labelled as no longer cold.

**7.3 Grading.** Blind, in the background (`post_attempt_jobs`; step 0 confirms it can run after the next rep starts). The rubric has two criteria: it names an idea that would work, on any valid route; and it cites a real feature of this problem. Check with `content/proposals/method_phrasing.py` that these aren't flagged as method-phrased. `method_targets` already returns nothing for `method_selection`, so "Use {method}" never appears.

**7.4 The near-miss shape.** The same stem with one condition changed: "Does the same idea still work? Why?" Capability `schema_interpretation`. The verdict and reason are committed at authoring. Where no code check ran, feedback reads "model's reading, not checked".

**7.5 Supply: the hard part.** Showing the idea reveals the problem (`attempts/reveal_ledger.py`), so that surface can't later be a cold attempt.
1. **First, surplus exercises:** source exercises the curriculum path won't use (`deliverable_path_sections.exercise_span_id` shows which it will).
2. **Then generated variants:** when the pool is dry, raise a need through FG1's path. A new surface on the same idea at the same difficulty, background only, on the ChatGPT plan. `rung_variants.py` changes difficulty, so this is a new authoring contract.
3. **Near-clones count:** a variant registers in `activity_exposure_events`, so a later near-clone is treated as seen by the existing rule.

**7.6 Serving.** A Spot it block is a new action kind in `router_objective/value.py`, in the two-policy mix like any other. Per-rep decisions are too slow, since an LLM decision takes 12-16 s, so the router decides on the block. Its size comes from the existing block minutes (`engine.py:3266`). Within a block, reps span learning objects wherever the pool allows: that is what makes them uncued, and it defines the block rather than ranking anything. It's also the first thing that pushes mixing, since `scheduling/interleaving.py` only filters.

**7.7 Value.** With the same `γ`, a one-minute rep would look like a bargain and the numeric policy would over-serve it. It gets its own learned dose curve, in place of `γ`, as in-passage questions and lessons do (`spec_adaptive_difficulty_v1.md` §5.11).
- **Prior:** the in-passage question's prior, which is the closest existing kind.
- **Cost:** an owner amendment to A12 limit 1 and D20, a migration for the `ad_reading_opportunities` CHECK, and an AD successor, the same list TE3a needed (`spec_teacher_v1.md`).

**7.8 Evidence.** A graded, unassisted rep is a real attempt on the (facet, `method_selection`) cell, with existing values: `independent_attempt` mass and `short_answer` coverage. A near-miss files under `schema_interpretation`. A rep served after the idea was revealed carries the existing primed rules.

**7.9 Report.** Accuracy and calibration over time; later uncued `method_selection` results and RO5's draws; rep minutes; how much of the supply is used, by source.

**Tests:** no solution text in the idea card; the card shows before a grade exists; an alternative valid idea scores; a held-out item never appears as supply; the block's candidates carry exact propensities; with the switch off, the mix matches the predecessor exactly.

## 8. Other features

### RE4: the cue map
One append-only table, `learner_cue_lines` (`RAW_LEDGER`): `id`, `attempt_id`, `practice_item_id`, `learning_object_id`, `cue_text`, `idea_text`, `source`, `created_at`, `superseded_by`. Sources: Spot it's line, and the existing optional lines (`attempts/trace_evidence.py:84-88`) when the learner wrote one.
- **Tier 2 text:** it can inform hints, routing context and gaps. It's never evidence.
- **Reads:** `search_move` quotes it (RE6), the router card and teacher brief carry it as the learner's own words, and RE10 can draw on it.
- **Disagreement:** a line that conflicts with the source's cue enters the existing learner-text-gaps pipeline. There's no new diagnoser.
- **UI:** a plain list on the topic's glass-box view. It's not a notes product, so no folders, tags or editor beyond superseding a line.

### RE5: teach-back offers
Let the router consider a teach-back before its item exists, as `followup_run/router.py` decides before generating.
1. **Candidate:** a teach-back on an LO with a graded attempt and no held-out restriction, using the source item's facets for its value.
2. **Form:** an offer-type action (`spec_router_objective_v1.md` §8.1): "Explain this to a curious student? About {minutes} minutes." Valued as accepted and declined branches, with its own acceptance model, seeded like TE1b's.
3. **On accept:** `ensure_teach_back_item(source_practice_item_id=…)` writes it. If authoring fails, its existing conservative fallback applies.
4. **Phone:** holds the offer for the desktop, as lessons do.
5. **Small fix:** the `session_cap` comment at `config/schema.py:677` is stale against `scheduler.py:2599`.

**Tests:** no item is written until accept; a decline writes nothing but its response row; propensities are exact.

### RE6: `search_move` hints
A new level-1 kind in `hints/kinds.py`, offered by the chooser, drawn with a logged propensity.
- **Moves:** `small_case`, `simpler_version`, `change_detail`, `similar_solved`, `wild_ideas`, `step_away`. Stored in `help_assists.strategy`.
- **Contract, in `hints/contracts.py`:** no solution content, as for `approach_question`, and it names one move applied to this problem.
- **Keeps G37:** with two or more rivals open, level 1's only option stays `discriminating`.
- **"More stuck, looser filter" is learned, not coded:** the chooser sees the moves already tried. No fixed progression.
- **`similar_solved`** may quote a cue-map line or an earlier solved problem of the learner's, never this item's solution.
- **`step_away`** links to RE1.
- **Fallback:** unchanged, `approach_question` on rung 1.

### RE7: the effort coefficient
One coefficient, `w_effort`, in the **objective's forward value only.** It has the same form as IH4's `w_pref`.
- **Input:** `x = log(active_seconds / the learner's running median for that capability)`, crossed with outcome and whether a solution was studied afterwards. "Studied" means a logged discrete reveal or a guided redo, never dwell.
- **Effect:** a candidate's learning effect becomes `γ · exp(w_effort · x̂)`, with `x̂` from its predicted minutes. `w_effort` starts at 0, which changes nothing.
- **Fitting:** on cold-outcome residuals, frozen as a sensor in the decision trace, with AD's predicted success as a control, since long attempts are also hard ones.
- **AD is untouched.** A12 bars active time from AD's state. **This corrects the review's §4a.1, which proposed a multiplier on `γ` inside AD.**
- **Honest limits:** nothing randomizes effort, so this is observational and reported that way. Expect `w_effort` near zero for a long time.

**Tests:** at `w_effort = 0` the decision matches the previous tag exactly; a null `active_seconds` is excluded, never imputed; no AD module reads it.

### RE8: `S_eff`
Builds `spec_learned_parameters_v1.md` §4.6: `S_eff = S_fsrs · exp(ŵᵀu)`, with one algorithm successor and the kill switch `scheduling.liquid_stability.enabled`. This spec adds:
1. **Read side only.** `S_eff` changes retrievability reads through RE2's function. FSRS's own state, updates and fitted weights stay plain, so replay of FSRS is unchanged.
2. **An effort input,** the same `x` as RE7, from RE0.
3. **Inputs derived from ledgers for every review.** Today's `stability_inputs` covers only lesson receipts. Reading stays out (the firewall).
4. **A true hint depth.** `_stability_inputs` (`teacher/service.py:2370`) stores `hints_used`, a count, under `hint_depth`. Use the highest level from `help_assists`.
5. **First consumers:** the lesson's delayed-check dates (`teacher/delayed.py`), then the objective's `R`.
6. **Overlap:** `P(perform)` already learns an overall trust in `R` (`aR`), so the report shows what `S_eff` adds beyond it.

Expect only small effects soon, with at most 19 same-item repeats so far. It learns from same-item reviews, so it doesn't speak to transfer.

**Tests:** at `ŵ = 0`, every read equals plain FSRS; FSRS state after replay is byte-identical with the switch on and off; reading events never appear in `u`.

### RE9: black-box steps
- **RE9a, in lessons:** a plan node may be a labelled black box, a stated assumption used before it's opened, on the ansatz pattern (`spec_teacher_v1.md`, Principle i). The teacher chooses when, as pedagogy. Code ensures an unopened box is named at the lesson's close and appears in the next brief.
- **RE9b, in the curriculum, only if RE9a looks useful:** the sweep's unbuilt order randomization at prerequisite near-ties, with exact propensities.

### RE10: rebuild checks
An authoring contract for items whose stem states the problem or goal and not the result's name, on conceptual LOs. Graded by rubric-by-fact, on any valid route, with remembered and rederived treated alike. Supply goes through the existing need step, since the teacher never authors its own checks (`teacher/delayed.py`). No new attempt type.

### RE11: figures from memory
Opt-in. On a return visit to a figure already explored, hide it and ask for one prediction first, then show it. Recorded as `figure_predictions`, tier 2, never evidence. Off by default, given the weak evidence.

## 9. Not in this spec

Reasons are in `docs/brainstorming/Colin Galen.md` §5: invent-first everywhere, reviewing when it feels forgotten, solution reading as the main practice, speed as a goal, a public explanation ecosystem, trained LTC networks, liquid drift and error recency, and making `κ` liquid. The fixed `practice_band` (§4a.4 there) stays an open question outside this spec.

## 10. Owner decisions

| # | Decision | Recommendation |
|---|---|---|
| 1 | Placement | **Decided, owner, Nov 9:** RE0 before the refactor, RE2 inside it, RE1 and RE3-RE8 after it beside the UX audit |
| 2 | "Leave it open" before submitting, not on the feedback screen | **Yes.** Otherwise the solution may already be seen |
| 3 | Spot it's own dose curve, which amends A12 limit 1 and D20 | **Yes.** Without it, one-minute reps are overvalued |
| 4 | Supply: surplus exercises first, generated variants after | **Yes** |
| 5 | The effort coefficient stays out of AD, in the objective only | **Yes.** A12 bars active time from AD's state |
| 6 | Does active time in an objective draw fit A12's "a draw or an offer"? A12's list concerns reading events; this is practice | **Allow it** for practice attempts, and record the ruling. If not, RE7 becomes report-only |
| 7 | `S_eff` is read-side only | **Yes.** It keeps FSRS replay untouched |

## 11. Build order

RE0, RE1 (needs IH3's table), RE2 (in the refactor), RE3 with RE4, RE5, RE6, RE7, RE8. RE9-RE11 as wanted. RE3 is the largest, and its supply work (§7.5) should be specified further before it starts.
