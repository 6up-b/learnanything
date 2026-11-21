# Teacher v2: three independent reviews of the multi-session and delayed-check proposal (2026-11-20)

Reviewed: the first draft of `docs/specs/spec_teacher_v2.md` §7-§8, given to each reviewer as the brief below. Each reviewer read the code independently, read-only, with no model or network calls and no access to the owner's vaults (the arxiv_v2 counts in the brief came from a backup-API copy read by the orchestrator). How each finding was taken up is in the spec's §8.2 table and the reviewer names cited in §7-§8.

## The brief

### Review brief: multi-session lessons through the deliverable curriculum, and the router's lesson action

Repository: this one (LearnLoop, a local-first learning system). Read-only review: do not edit any file, do not run the test suite, make no model or network calls, never open the owner's vaults (outside the checkout) or search the filesystem for them.

### Context you need

LearnLoop has a Teacher (LLM-run lessons, `src/learnloop/teacher/`, spec `docs/specs/spec_teacher_v1.md`) and an action router whose decisions are an objective function with rollouts (`src/learnloop/router_objective/`, spec `docs/specs/spec_router_objective_v1.md`). The objective is cold (unassisted, unprimed) performance at the goal date, with a rising price on attention/minutes. Lesson offers are candidates of the objective at reversible plan-block boundaries (teacher spec §15.1a, "TE3b"). The deliverable curriculum (`docs/specs/spec_deliverable_curriculum_v1.md`, built C0-C5) resolves a goal/exam/project the learner states into LOs and a curated reading path across all sources (`deliverable_path_sections`); C1 makes the plan's reading block follow it; C4 makes a lesson's brief read the deliverable's sentence and the path's sections.

Owner principles that bind any proposal: no made-up constants (every number is a seeded prior with a basis, a structural bound, or `keep` with a reason); no hard-coded routing rules ("if missed n times, serve a lesson"): the router chooses, stuckness is evidence; no kill switches by default; honest labels, frictionless defaults; one place to edit objective/policy specifics; lesson checks never certify; LearnLoop is a permanent habit, learning past a goal's end is fine.

### What we found (verify against the code)

1. **A lesson is atomic to the router.** An offer is valued as ONE LO: `src/learnloop/daily_plan/objective_inputs.py:620` builds `OT.Action(kind=LESSON, item_los=(offer["lo"],), minutes=...)`; `src/learnloop/daily_plan/lesson_offer.py` `build` (around :273-381) picks one LO, one duration (log-normal learned from lesson activity intervals). In the rollout (`src/learnloop/router_objective/rollouts.py:629-656`) a lesson is one dose per LO at the lesson's learned mass (AD's gamma x mass, plus TE3a's lesson curve `ad_link.LessonCurve` at the topic's "lesson window" position n = lessons since its last graded attempt). Its committed delayed checks enter the rollout as outcomes at their dates (`rollouts.py` ~:785, :969).
2. **A real lesson teaches more than one LO.** The lesson brief covers the goal LO plus its prerequisite closure (`teacher/brief.py`, spec §8.1 `nodes`, depth `teacher.brief.depth` default 2). On the owner's arxiv_v2 vault, the first lesson's receipt has 4 nodes on 4 different LOs. AD (TE3a) records one lesson opportunity per landed/taught node; the router credits only the offered LO.
3. **No cross-lesson structure exists** except the lesson window n and TE2's "where you left off" (the newest earlier lesson's latest plan on the same LOs, in `lesson_brief_v2`). On arxiv_v2: 9 lessons in 10 days, 3 LOs taught in more than one lesson, 4 lessons left open, 0 deliverable resolutions (the C4 path into lessons never fired).
4. **Delayed checks never happened.** All 24 delayed checks (19 retention, 5 transfer) from arxiv_v2's 5 closed lessons were recorded `missing`: the picker (`src/learnloop/teacher/delayed.py`) found no unseen, non-lineage vault item. So the lesson-check weight (§12.1), the forecast pool (§12.2), TE3a's curve and the router's lesson value have no lesson-caused cold outcome to learn from.

### The proposal to review

A. **The arc is the deliverable path plus lesson receipts.** No new curriculum or "course" object. A multi-session arc toward a goal/exam/project = the deliverable's resolved LOs and path order + the receipts and delayed-check results of lessons on them.

B. **The router still decides one sitting at a time** (reversible block boundaries; the objective at the goal date). Changes:
   - B1. A lesson action carries every LO it will teach (the plan's node LOs the brief would build: offered LO + prerequisite closure, or the deliverable path's next unfinished LOs), each with its dose, instead of one LO.
   - B2. When a deliverable is active, a lesson candidate can be "the next step on the deliverable's path" (next unfinished/unlanded LOs in path order), valued at the deliverable's deadline by the same objective. No rule forces it; it is one more candidate, drawn by the existing logged mix.
   - B3. The lesson window / curve reads arc position, so the second and third lessons of an arc are valued by what earlier ones did (already partly true via n).
C. **The teacher's brief gets an arc header**: "lesson k toward <deliverable>; lessons 1..k-1 covered X; delayed checks showed Y; path next: Z", extending `where_you_left_off` from the last lesson to the arc. The teacher may plan for the session at hand and propose what the next session should cover (logged, not binding).
D. **Delayed checks are generated** (owner-approved): single-use, machine-admitted questions through FG1's generation path (as TE2's lesson probes are: `followup_run.lesson_probe`, `generated_probe_items`), served cold at their retrievability date, never practice items afterwards, never served again. Vault unseen items remain preferred when they exist? (open: the owner's Nov 3 rule says generation is superior for probes).
E. **Separately approved by the owner (context, not under review):** lesson-check misses (and hedged correct answers) go to the split diagnoser as non-independent `taught_then_checked` hypotheses with a learned tempering weight; the after-a-miss learner-input prompt applies to lesson checks.

### What to return

A review in under ~1200 words:
1. Is A-D sound? For each, the strongest objection, and whether it breaks an owner principle above.
2. Things in the code that make B1-B3 harder or easier than stated (cite file:line). In particular: what valuing a multi-LO lesson does to the objective's rollouts, the price of minutes, offer acceptance modelling (TE1b's acceptance model), and the eve-of-exam regression; whether B2 needs the router to model a sequence or whether one-step valuation suffices.
3. For D: risks (generated-check quality vs. vault items, exposure from the lesson's own teaching, whether a generated item is a valid "unseen item of the same LO" for §12.1's learning of the lesson-check weight and for RO5's randomized checks).
4. Anything missing that a multi-session lesson design needs (e.g. open lessons left hanging, lessons on LOs outside any deliverable, multiple active deliverables).
5. Your recommended changes, ranked.
Be concrete and skeptical; say plainly where the proposal is wrong.



## Fable

### Review: multi-session lessons and the router's lesson action

**Verdict:** D and B1 are worth building, B2 needs a different entry point, B3 should be dropped, and A defines the arc on an object that has never existed in the owner's vault.

Paths below are under `S = src/learnloop`. I read code and specs only: no tests run, and the arxiv_v2 counts are taken from the brief, not checked.

### Your findings, checked
- **1 holds, with a nuance.** The atomicity is in the offer record (`S/daily_plan/lesson_offer.py:342-348`, `S/daily_plan/objective_inputs.py:620`), not the rollout. The rollout's LESSON branch already loops over LOs (`S/router_objective/rollouts.py:633`).
- **2 holds.** Spec §15.1a already says "on each target and goal LO"; the as-built narrowed it to one.
- **3 is understated.** The brief already carries `last_lessons` over goal plus closure LOs, with node summaries, recaps and delayed-check results (`S/teacher/brief.py:600-624`, `:918`).
- **4 is consistent with the code.** Picks happen once at close and are never retried (`S/teacher/service.py:2166`). A `missing` check has no commitment, so `pending_delayed_checks` skips it (`S/db/stores/lessons.py:194`). The offer's rollout still credits a check that never happens.

### 1. A-D
- **A: wrong as a definition.** With 0 resolutions against 9 lessons, "arc = deliverable path" is empty for every lesson taken. Define the arc as lessons chained by LO overlap (what `last_lessons` reads); a deliverable adds order and a date. The path's `done` is section-read state (`S/source_retrieval/deliverable_path.py:1084-1091`), so "unlanded" is a second fact you must define. No principle broken.
- **B1: right direction, inflates lessons as stated.**
  - Every LO gets a full dose with certainty. Real nodes close `held` or `uncertain` (no opportunity, `S/adaptive_difficulty/lessons.py:10`), prerequisites most often, and 4 of 9 lessons never closed.
  - Minutes are one pooled log-normal with no size term (`lesson_offer.py:171-185`), so N doses cost the same as one.
  - Each committed check is a graded attempt at mass 1.0 charged no minutes (`rollouts.py:845-849`), so N LOs means N free reviews.
  - A closure LO outside goal scope gets `undated_use_density` just for being a candidate's LO (`objective_inputs.py:770-771`). The rollout has no prerequisite coupling, so prerequisites are valued as independent end uses.
  - Doses or minutes per LO set by hand would break "no made-up constants".
- **B2: not "one more candidate drawn by the mix".** Exactly one offer reaches the objective, pre-selected by TE1b's staged `log P(accept) + log(1−p)` (`lesson_offer.py:340-342`, `S/router/lesson_suggestions.py:624-634`), which sees no deadline. Path step versus `cold_missed` would be settled outside the objective. That is a quiet routing rule and a second place to edit.
- **B3: wrong.**
  - `n` is lessons since the last graded attempt, and any graded attempt zeroes it, including the delayed check D makes real (`rollouts.py:563`).
  - The offered LO is excluded while taught and unattempted (`S/daily_plan/lesson_suggestion.py:241-244`).
  - `n` is a diminishing-returns window fitted by AD on AD's definition; redefining it in the router breaks TE3a's "one learned quantity".
  - What earlier lessons did is already in η and the belief.
- **C: mostly exists.** New are only the ordinal, path-next and the proposal.
  - The proposal is sound only as input to the next brief. If candidate generation reads it, the teacher is routing (§1.5: the teacher values nothing).
  - Each earlier lesson must pass `admitted_recap` (`brief.py:608-614`).
  - It is a brief version bump.
- **D: necessary.** The strongest objection is self-confirmation, covered in section 3.

### 2. Code: easier and harder than stated
**Easier**
- Candidate LOs enter the topic set first (`objective_inputs.py:719-731`).
- An accepted lesson as a SEQUENCE of per-node LESSON steps under one `accept` nearly works: `_do(replace(action, accept=None))` walks `_steps`, and commitments read from the outer action (`rollouts.py:1029-1032`, `:944-952`, `:970`).
- That gives each node its own mass, minutes and landing time, so a learner stop or a date mid-lesson credits only finished nodes.
- It needs the validation at `S/router_objective/types.py:170-173` and the `kind == LESSON` tests at `objective_inputs.py:814` and `rollouts.py:1040`.

**Harder**
- `Action.mass` is one float (`types.py:144`), while the mass is per LO (`lesson_offer.py:188`).
- §8.4's effect correction is added to every LO of an action (`rollouts.py:660-662`), so one LLM forecast counts N times; a sequence gets none (`:961`).
- There are 4 duration streams and 8 commitment streams (`rollouts.py:146`, `:153`, `:848`, `:952`). Past those, steps share draws, and correlated durations raise Var(D), which the price charges.
- **Price of minutes:** `DURATION_LOG_SD = 0.7` is fixed (`lesson_offer.py:61`), so the variance term grows with the median squared. An honestly longer lesson is penalised superlinearly. Sum per-node durations or learn the spread.
- **Acceptance:** there is no size or deliverable term, and `minutes_short` is normalised to the fixed 15-minute card (`lesson_suggestions.py:290-292`).
  - A 40-minute lesson gets the 15-minute `P(accept)` and can never learn otherwise.
  - `_open_unprompted` (`:331-340`) shows how to add a term without moving old posteriors.
  - Refs and declines are per single LO (`lesson_offer.py:88`).
- **Eve of exam:** the form is untouched, since crossed dates score on the pre-effect state (`rollouts.py:925-930`). But N free checks dated before the exam let a lesson beat cramming for the wrong reason. Add that regression.
- **Identity:** `OFFER_VERSION`, the definition hash and RO6's `lesson` indicator all move, which is a change point.

**Does B2 need sequence modelling?** No, one-step suffices. The tail holds only practice (`rollouts.py:705-760`) and LOs are independent, so the objective cannot value order at all. Order comes from the path, as candidate generation. If order should be valued, the missing piece is a learned prerequisite-readiness term in the lesson effect, not a planner.

### 3. D risks
- **The cold guards are per item and vacuous for a fresh item.** First attempt and no reveal row (`S/learner/lesson_weight.py:750-753`) and lineage (`S/teacher/delayed.py:165-167`) all pass trivially. A generated question can restate the lesson's worked example and still qualify.
- **The only text test is bigram overlap** (`delayed.py:63-72`). Use the Decider's reveal judgment (owner, Nov 18) plus FG1's manipulation audit against the lesson's own checks and examples. That audit is `not_applicable` for lesson probes (`S/followup_run/lesson_probe.py:20-22`), but here a comparator exists.
- **Precedent cuts the other way.** A lesson probe answered after topic text was shown is `instructional_diagnostic` and resolves nothing (`S/attempts/attempts.py:2783-2788`). D needs an explicit item-level exposure rule, not a topic-level one.
- **Difficulty bias feeds a loop.** §12.1's likelihood is the mastery prediction for the item. If generated checks run easier, η₀ rises, the lesson mass rises, and lessons are valued higher. Log the item source. Where an unseen vault item exists, randomize vault versus generated with a logged propensity; that answers the open question with data.
- **Timing.** §12.2's forecasts are about "the committed cold item" at node landing, with a shared seed (`delayed.py:139-142`). Generate when a node lands, screen at close, and add a "being written" state that the receipt, the brief and the population all read.
- **Plan down.** The author runs only on the subscription plan (`lesson_probe.py:10-11`), so checks go `missing` again. Label it.
- **RO5.** D items are not valid randomized checks: their administration depends on an accepted lesson, and RO5's draw must read only the date and the eligible set (`S/router_objective/checks.py:3-8`). Keep them withheld. Lesson LOs stay at `r_L = 0` until ordinary need-generated items exist.
- **Transfer.** "Never filled by a look-alike" stands, so start with retention only.

### 4. Missing
- **Open lessons.** Their LOs are excluded from offers indefinitely (`lesson_suggestion.py:238-240`), with no receipt, AD opportunity or checks, and I found no auto-close. The arc needs "resume lesson k" as a candidate and a partial receipt for landed nodes.
- **Lessons outside any deliverable.** Today that is all of them.
- **Multiple deliverables.** The code is nearest-first (`deliverable_path.py:1776-1779`, `brief.py:765`); the objective should weigh each one's next step.
- **Reading block and lesson on the same path step.** They have separate dose windows with no cross-diminishing, and C4 feeds the lesson the same sections.
- **Learner-started lessons** inside an arc, and what the arc does after the date passes.

### 5. Recommended changes, ranked
1. Build D first, with item-level exposure by the Decider and the manipulation audit, generation at landing, source logged and randomized, and D items excluded from RO5.
2. Fix open lessons: a resume candidate and partial receipts.
3. Build B1 as per-node steps with a learned landing probability and per-node minutes, charge check minutes, add a size term to acceptance, and show real minutes on the card.
4. For B2, let the objective value path-step candidates directly (one per active deliverable) instead of the staged pre-filter, and define the arc by LO overlap.
5. Drop B3.
6. For C, add only the ordinal, path-next and the proposal, with the proposal read by the next brief alone.

## Codex Astra (gpt-6-astra, effort high)

A, B2, C and D are sound directions with conditions. B1 overstates what is knowable before a lesson; B3 is wrong if "arc position" replaces the existing dose window.

The single-LO mismatch is verified: objective_inputs.py:620 creates one target, while lessons.py:70 records each qualifying receipt node. The vault census remains unverified, as required. "Missing delayed checks imply no calibration outcomes" is too strong: any qualifying later cold attempt on the same LO can resolve checks and forecasts (lesson_weight.py:724, lesson_weight.py:851).

A. Reuse the deliverable path, but distinguish coverage from mastery.
The strongest objection is "unfinished/unlanded": reading-path labels, taught nodes, landed nodes and cold-demonstrated knowledge describe different things. Existing path planning excludes already-shown, assumed, skipped and pending-check sections (deliverable_path.py:1611); those exclusions are not automatically appropriate lesson eligibility rules. Treating "landed" as completion would violate "lesson checks never certify."

No course object is necessary, but persist the deliverable ID and resolution/path revision used by each offer and lesson. Inferring membership afterward from overlapping LOs will misattribute lessons when goals overlap or paths change.

B. Keep reversible decisions; revise the action model.

- B1: The brief supplies prerequisite context (teacher/brief.py:244); the teacher separately writes its plan (teacher/contracts.py:111). Neither guarantees teaching every node. Value forecast coverage/doses with uncertainty, then reconcile against receipts. Promising every closure LO violates honest labels and risks invented gains.
- B2: A path-derived candidate can compete without committing to an arc. However, today only TE1b's top-ranked offer reaches the objective; alternatives are merely displayed (daily_plan/lesson_offer.py:344). Adding a path candidate upstream does not guarantee it receives objective valuation or positive mixture support. Specify candidate construction and logging explicitly.
- B3: Keep the per-LO dose window. Its meaning is lessons since the last graded attempt, and simulated observations reset it (router_objective/ad_link.py:155, router_objective/rollouts.py:603). Arc lesson three may teach a new LO; an intervening check changes the window. Substituting session ordinal silently changes the fitted model. Arc position can be metadata or a separately justified learned feature.

Multi-LO valuation already partly works, but simply expanding item_los is unsafe:
- router_objective/rollouts.py:633 deduplicates LOs and grants each the same scalar mass plus one curve step. AD records doses per node, including multiple nodes on one LO. Represent per-LO node doses and distinguish dose count from lesson-check evidence mass.
- One sitting should incur one duration cost, with benefits across its actual targets. The current pooled duration fit ignores scope (daily_plan/lesson_offer.py:171). Crediting additional LOs at unchanged minutes produces unsupported bargains. Preserve sampled durations and accepted/declined branches; with a rising price, pricing expected minutes is incorrect (tests/test_te3b_value.py:34).
- TE1b's acceptance features assume a fixed 15-minute card and contain no scope or continuation feature (router/lesson_suggestions.py:282). Carry forward the model as an explicitly limited prior; version any feature changes.
- Expanded targets must enter the valued population consistently: candidate LOs currently precede goals under a topic cap (daily_plan/objective_inputs.py:730).

One-step selection with continuation suffices initially. The existing continuation practises adaptively; it does not model future teaching sessions or prerequisite unlocks (router_objective/rollouts.py:21). It may therefore undervalue foundations whose payoff requires later lessons. Explicit sequence modelling is necessary only to claim those benefits.

All candidates must retain the same objective over all active goals, undated uses and continuation, not candidate-specific deadlines (daily_plan/objective_inputs.py:101). The eve-of-exam test asserts cram-versus-stop values, not that stop beats the lesson (tests/test_te3b_value.py:66). It cannot validate multi-LO lesson economics.

C. Useful, but more already exists than the brief acknowledges.
last_lessons already includes earlier receipts and delayed results, with recap protection checks (teacher/brief.py:600). Extend that view with explicit arc membership and path provenance. Label missing, pending, exposed and cold outcomes distinctly; "checks showed Y" must not collapse them. Preserve protection checks and distinguish teacher-proposed next steps from router decisions. Otherwise C risks dishonest progress labels; it introduces no inherent principle violation.

D. Appropriate, but reuse admission machinery, not the placement-probe lifecycle unchanged.
Generated probes are explicitly excluded from delayed candidates (delayed_checks.py:70); the current lesson generator refuses closed lessons (followup_run/lesson_probe.py:126). Define a delayed-check origin, durable commitment, generation failures/retries, reservation, burn-on-first-serve and retirement.

Machine admission verifies structural contracts and freshness, not psychometric validity; adversarial review is explicitly absent (followup_run/lesson_probe.py:182). Neither generated nor vault origin guarantees quality. Require independently specified target facets, blind grading, generator provenance and exclusion of lesson examples/lineage. Existing novelty checks do not establish semantic independence from teaching.

A generated item can satisfy §12.1's unseen-same-LO requirement, but a new ID alone cannot. Recheck exposure at administration; the existing lesson probe path already checks topic-wide reveals (teacher/probes.py:417). Transfer requires its own established relation, not merely a new question.

Lesson-triggered checks are not RO5 randomized checks. RO5 fixes assignment independently of action draws (router_objective/checks.py:132). Generated questions could support RO5 through independently established eligibility and assignment, not retrospective relabelling.

Most urgently, rollouts currently execute committed checks regardless of return, without charging check minutes (router_objective/rollouts.py:844). Multiplying commitments amplifies fictitious free information.

Recommended changes, ranked:
1. Repair delayed-check lifecycle and valuation together: availability, completion, exposure, cost and calibration provenance. Prefer generation consistently with the owner's stated probe rule.
2. Specify one shared, versioned lesson-action contract for forecast coverage, doses, duration, acceptance and realized receipts. Keep policy parameters centralized and priors justified.
3. Preserve the existing dose-window semantics; implement arc summaries and explicit deliverable/path bindings.
4. Define resume/close/abandon handling for open lessons (AD currently reads only closed receipts), plus goal-free lessons, overlapping deliverables and post-deadline continuation. Do not let "next unfinished" become a hard routing rule or certification shortcut.


## Opus 5.5 (effort high)

I checked the proposal against the code. A and C are mostly sound. B1 is right in direction but would over-value lessons if built as a one-line change. B2 rests on a wrong assumption about how offers reach the objective. B3 should be dropped. D is worth building, but it reverses two explicit rules and needs a way to separate item difficulty from the lesson's effect.

### 1. Is A–D sound?

**A (the arc is the deliverable path plus lesson receipts).** Sound as "no new object". The strongest objection is that it defines the arc by something the owner's real vault doesn't have: arxiv_v2 has 0 deliverable resolutions. `deliverable_for` (`teacher/brief.py:754-787`) needs a resolution that names the lesson's LO, so on actual usage there is no arc at all. With several deliverables it takes the first match from `nearest_deliverables` (`:765`). The arc needs a fallback: goal scope plus per-LO lesson history. No owner principle is broken.

**B (one sitting at a time).** Deciding one sitting at a time at reversible boundaries is correct. B1 is right in direction and wrong in mechanism (§2). B2 is wrong about how a candidate reaches the objective (§2). B3 has no mechanism behind it and would need an unlearnable new number, which breaks the no-made-up-constants rule. Drop B3.

**C (arc header in the brief).** Smaller than stated. The brief already includes `last_lessons` over the whole prerequisite closure: each earlier lesson's nodes, its recap and its delayed-check results (`brief.py:600-625`, `:916`). It also has `where_you_left_off` (`te2.py:131`). What is genuinely new is lessons on other LOs of the same deliverable, and "path next". Risk: if the teacher's "next session should cover…" reaches the learner as "next time we'll…", the router may not keep it. That breaks "honest labels". Log it, never show it as a promise.

**D (generated delayed checks).** Worth doing. Risks in §3.

### 2. B1–B3 against the code

- **B1 is mechanically trivial, and that is the danger.** The rollout already loops `for lo in dict.fromkeys(los)` (`rollouts.py:633`). Widening `item_los` at `objective_inputs.py:620` gives every node:
  - the full γ·mass;
  - the same `gamma_z` draw;
  - RO6's effect correction once per LO (`rollouts.py:657-659`), although it was fitted per action.

  Meanwhile:
  - `Action` carries one `mass`, read for the offered LO only (`lesson_offer.py:188`, `:333`).
  - The minutes come from `duration_model` (`lesson_offer.py:171`), pooled over whole closed lessons and not conditioned on how many nodes a lesson has.
  - κ (`rollouts.py:438`) depends on minutes only.

  So value grows with node count while cost doesn't, which favours LOs with large prerequisite closures. Today the bias runs the other way: minutes for about 4 nodes, credit for 1. Planned is also not landed (4 of 9 lessons are open), so B1 needs a landing probability learned from receipts.
- **Prerequisite LOs outside the population get nothing.** The rollout drops them (`if lo in self.index`, `rollouts.py:624`). The population must stay frozen without candidates (`objective_inputs.py:454-467`, F11). There is no prerequisite coupling in the rollout, so teaching a prerequisite has no modelled path to the goal LO. B1 adds less than it appears to.
- **Committed checks are free practice that never happens.** Each commitment applies a full practice dose at mass 1.0 with no κ (`rollouts.py:844-849`). The offer always commits one retention check on the offered LO (`lesson_offer.py:331-332`) whether or not any item exists. That is a bug today: the router credits a check that happened 0 of 24 times. Per-node commitments would multiply it, and the `commit_u` streams wrap at 8 (`slot % 8`).
- **Eve-of-exam regression.** The test pins a one-LO lesson (`tests/test_te3b_value.py:66`), so it keeps passing while the property it guards (gain per minute below the rising price means stop) can flip once a lesson carries N LOs. Add a multi-LO case.
- **Acceptance (TE1b).**
  - The offer's topic is chosen by TE1b's staged score, `log p_accept + log(1 − predicted)` (`router/lesson_suggestions.py:624-634`).
  - Only one offer reaches the support per decision (`docs/reviews/teacher-te3b.md:29`).
  - Candidates are single-LO by construction (`daily_plan/lesson_suggestion.py:270`).
  - The design vector (`lesson_suggestions.py:282-298`) has no size or duration term; `minutes_short` uses the fixed `CARD_MINUTES`.
- **So B2's "drawn by the existing logged mix" is false.** A path-next candidate reaches the objective only if it beats the others on TE1b's score, which knows nothing about deadlines. B2 needs either several offers valued in the support or the objective ranking the lesson candidates. Separately, "valued at the deliverable's deadline" is already true: a deliverable is a `Goal`, C0 writes its `facet_scope`, and `_goal_uses` turns that into dated uses (`objective_inputs.py:92-118`). B2 only changes which candidates are generated.
- **One-step valuation is enough as receding horizon.** But the tail is practice-only and topics are independent, so path order has no value in the model. "Next on the path" wins only when its LOs happen to have the largest one-step gain. What the arc idea actually needs is prerequisite coupling in the learning model, not sequence modelling.
- **B3.** The lesson window is per facet and resets on any graded attempt (`rollouts.py:563`; `adaptive_difficulty/state.py:353`). An arc mostly teaches different LOs, so n per LO stays 0 or 1. "Arc position" would be a new parameter with nothing to learn it from (9 lessons).

### 3. D: risks

- **It reverses explicit rules.** `delayed_checks.candidates` excludes generated probes ("FG1 §4.2 … never a delayed check", `delayed_checks.py:62-70`). `teacher/delayed.py`'s docstring says "the teacher never authors its own". FG1 §4.2's lifecycle (burn at first serve, retire when hypotheses close) has no rule for an item reserved for days with no hypotheses. All three need amending.
- **Difficulty is confounded with the lesson's effect (§12.1).** A generated check qualifies structurally: `qualifying_outcomes` (`learner/lesson_weight.py:724`) accepts any first cold attempt on an unseen item. But the likelihood uses item IRT parameters (`:784`), and a single-use item never gets calibrated, so it falls back to LO defaults. If generated items are systematically easier or harder, that offset is absorbed into η₀, the lesson weight itself, with no way to separate them when every lesson outcome is generated. The fix also settles D's open question without a rule: when both a vault item and a generated one exist, choose between them by a logged randomized draw, and learn a per-source difficulty offset.
- **Finding 4 overstates the gap.** §12.1 also learns from ordinary cold outcomes. It got none because these LOs have no unseen items at all. That same scarcity starves RO5's randomized checks, whose eligibility rule reuses `D.candidates` (`objective_inputs.py:485-508`) and so excludes generated items. D fixes lessons only; say so or extend it to RO5.
- **Exposure from the lesson's own teaching.** The teacher and the check author are likely the same frontier model family, so they may reach for the same canonical example. Before admission, gate on `question_overlap` against the lesson's displayed text (`teacher/delayed.py:65-90`) plus lineage. Give the author the LO and the taught facets, not the transcript.
- **Availability.** The lesson generation path runs on the subscription plan only (`followup_run/lesson_probe.py`, docstring). If the plan is down, checks go missing again. Generate asynchronously at close, retry until the due date, and record a miss honestly.
- **Transfer checks.** Generation must emit criterion targets, or `measures_facet` cannot establish the relation to what was taught.

### 4. What a multi-session design still lacks

- **Open lessons hang.** Nothing closes a lesson automatically. An open lesson's LOs are excluded from offers (`router_suggestions.py:214`), checks are committed only at close (`teacher/service.py:2166`), and the duration model reads closed lessons only. `where_you_left_off` does read open lessons, but the router can't offer to resume one. "Resume this lesson" is the most natural multi-session step, and it is missing.
- **Lessons on LOs outside any deliverable.** The arc needs to fall back to goal scope or LO history.
- **Several active deliverables.** Today it takes the first match.
- **Lesson duration by node count, and the probability a node lands.**
- **The daily ceiling** (`ceiling_per_day`, 3) interacting with arcs.

### 5. Recommended changes, ranked

1. **Fix commitment valuation now.** Commit a check in the rollout only when one can actually be committed (`delayed_check_words` already computes this), or weight it by a probability learned from receipts. Charge its minutes.
2. **D, with its safeguards:** the randomized vault-or-generated draw, a per-source difficulty offset, the overlap gate, a reservation lifecycle, and explicit amendments to FG1 §4.2 and `delayed.py`. Decide whether it covers RO5.
3. **B1, done properly:**
   - a mass per LO;
   - a landing probability per node, from receipts;
   - duration with a node-count slope (prior zero);
   - RO6's correction once per action, not per LO;
   - a multi-LO eve-of-exam test.
4. **Open lessons:** a resume candidate, and checks committed per landed node when a session ends rather than only at close.
5. **B2 as candidate generation only:** value the top lesson candidates in the objective instead of TE1b's staged score. Don't claim the deadline valuation is new.
6. **A:** arc = goal scope plus receipts, with the deliverable optional.
7. **C:** extend `last_lessons` to the arc's scope; log the next-session proposal and never show it as a promise.
8. **Drop B3.**
