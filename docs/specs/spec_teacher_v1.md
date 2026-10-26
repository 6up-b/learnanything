# Teacher: LearnHarness-quality lessons on LearnLoop's latent learner state (v1)

**Status:** revision 4, draft for owner review, 2026-10-24. Nothing here is implemented.
- Revisions 3 and 4 apply the owner's decisions of 2026-10-24 (§1.3, items 1–7) to revision 2 of the same day.
- Every open question is now decided (§23). Every number is a seeded prior, a structural form or `keep` (§18.4).
- Code truth was re-audited at main `b7e0444b5` and at two in-flight branches (§5).
- Revision 1 (2026-10-23) is superseded. Its decided items TQ1, TQ3, TQ4, TQ5 and TQ7 are carried, narrowed or moved, as §1.4 lists, each with a reason.
- Code paths are under `src/learnloop/` unless they say otherwise.

**Sources:**
- LearnHarness, read at commit `6cba9c8` (AGPL-3.0). Its file paths are cited in §2.
- `docs/brainstorming/Teacher Research Sweep 2026-10.md` (paper ids A*, B*, C* refer to it).
- The Opus review of revision 1, 2026-10-24 (session scratchpad, `teacher-learned-params-review.md`; "the review" below).
- Specs: `spec_mcp_frontend_c1.md` and `spec_mcp_frontend_v1.md`; `spec_adaptive_difficulty_v1.md`, the AD23 worktree copy; `spec_knowledge_model.md` §8.3, §9.3; `spec_learner_field_v1.md`; `spec_blind_grading_diagnosis_split_v1.md`; `spec_reader_workbench_v1.md`; `spec_adaptive_hints_v1.md`; `spec_source_practice_and_probes_v1.md` §5; `spec_action_router_v1.md`; `docs/algorithm-change-playbook.md`.

---

## 1. Owner direction

### 1.1 The intent (2026-10-24)

> Use the best parts of LearnHarness to bring its teaching strengths into a teacher that is better informed of latent learner state. In LearnHarness each attempt is assumed independent, and in-session checks measure performance rather than learning. That is why LearnLoop optimizes for cold retrieval and transfer. Rewrite the teacher spec knowing this, and in the context of what is being built for the MCP and adaptive difficulty.

Read as three requirements:
1. **Teaching quality comes from LearnHarness.** Its doctrine, lesson arc and question craft give the best in-session lesson we have compared. We adopt the ideas, never the text or code: LearnHarness is AGPL-3.0, and this repository is public under Apache-2.0.
2. **The learner is not new each lesson.** The teacher starts from LearnLoop's persistent latent state and writes back into it honestly.
3. **The outcome is delayed cold retrieval and transfer.** In-lesson checks steer the lesson; they never certify it.

### 1.2 Carried from revision 1 (owner, 2026-10-23)

- Principle i (unconditional truths, and ansätze, first) and Principle ii ("how could I have discovered this?", with 3Blue1Brown as the standard).
- Ground the teaching in the learner's own sources.
- Prefer the frontier model's judgment to hand-written rules.
- Pass the learner's confidence and the hedge read to the model roles that read the learner.
- No zero-weight effort: an answered, graded lesson question carries evidence (TQ1, TQ4).
- A goal-scoped "Check what I already know" is allowed. It is a button and is never prompted (TQ3).
- A goal with no matching LO creates one (TQ5).

### 1.3 Owner decisions, 2026-10-24 (revision 3)

1. **The lesson-check weight is learned, not fixed at 0.5.** In the owner's words, "lesson checks may be more informative based on latent user skill and confidence".
   - It is a latent effect with prior N(0.5, wide), with a global term, per-LO offsets shrunk hard toward 0, and interactions with confidence and with AD's prediction.
   - It is learned only from later cold checks on unseen items of the same LO, and it changes only how much mastery moves (§12.1).
2. **The teacher's `lesson_step_retained` forecast is scored against the same cold outcomes, in parallel.** It is the planned path for retiring the parametric weight (§12.2). *Revision 4 replaces the one-time switch at a fixed margin with a continuously learned mixture (item 7).*
3. **The learned-parameters spec keeps one family** (the lesson-check weight), plus the tap/hedge → probability recalibration it needs, as LP-min beside the four claim fixes. This revises the review's "drop LP1–3" for this case only. The review's other LP verdicts stand (`spec_learned_parameters_v1.md` §0a).
4. **Confidence goes into routing as well as models** (TE0). The tap and the hedge read go to the diagnoser, hint writer, tutor and teacher contexts, and into the router's learner card as events (§15.2).
5. **The action router suggests lessons, and the learner opts in.** "Teach me X" stays available everywhere. Every suggestion and every response is logged, so the router can learn from them later (§15.1). This revises revision 2's Q3, "learner-started only".
6. **A chat model may run cold checks and probes where integrity allows.** This sits behind C2 and uses a learned weight whose prior is below an in-app cold check. An item served to a chat host is never an in-app cold check afterwards (§16.2). This revises revision 2's rule that probes and cold checks never run in chat.
7. **No made-up numbers (revision 4).** In the owner's words: "all these weights/margin values need to be learned and dynamic and not just made up, priors can be seeded otherwise. yes to defaults for all other open questions."
   - **No keep-or-switch margins.**
     - The forecast and the parametric mass are mixed by a learned pool weight (§12.2).
     - Liquid stability's prior width is a grid posterior, with no review-count threshold (`spec_learned_parameters_v1.md` §4.6).
   - **Every other number is one of three things** (the full list is §18.4):
     - a seeded prior, labelled with its `prior_basis` and width;
     - a structural bound written into the functional form;
     - or `keep`, with the reason it stays fixed.
   - **Router suggestion frequency and mute length** are learned from the learner's responses, under a `keep` ceiling against nagging (§15.1).
   - **Every remaining question is decided** with its recommended default (§23).

### 1.4 Deviations from revision 1 and from the review

The review's code-truth corrections are applied throughout without further note. Its scope cuts were recommendations, not decisions. This table says which ones were taken and why.

| # | Topic | Revision 1 | Review | This revision, and why |
|---|---|---|---|---|
| 1 | Entry | Executes the router's `instruct` blocks | Learner-initiated only | **Revised by the owner (2026-10-24).** The router *suggests* lessons as a new `instruct(lesson)` candidate, and the learner opts in (§15.1). Existing `instruct`-lane items are still served as ordinary practice (§5.1), and no lesson starts without the learner's yes |
| 2 | Lesson-check weight | New `lesson_check` type, primed, mass 0.5 | The existing `reconstruction_after_walkthrough` (0.5, assisted), not primed | **Type adopted; weight revised by the owner (2026-10-24).** It is still `reconstruction_after_walkthrough`, not primed: no rebuild of `practice_attempts` and no double discount (field §4.3). Its mass is a learned latent effect with prior centre 0.5 (§12.1) |
| 3 | Teacher-written probes (TQ4) | Full weight once admitted | Placement on vault items only | **Partly adopted.** Teacher-written probes stay allowed but count as lesson checks, at the learned lesson-check weight. Vault-item probes count fully. No admission gate exists for model-written items (§5.3), and the owner's "effort is meaningful" still holds (Q2) |
| 4 | Placement belief | Code-ranked EIG over a soft-edge graph | Cut | **Adopted.** The latent state (EKF, AD predictions) is the belief, and LearnHarness's bracketing is doctrine for the model (§11) |
| 5 | "Assumed" from structure | `teacher_placement` source | Cut | **Adopted.** The SQL CHECK forbids it, and so do KM §9.3 and field F4 |
| 6 | Plan object | Premise-set DAG, code validation, affected-set backtracking | An outline with anchors | **Adopted.** On ≤10 nodes the model tracks dependencies. One code check stays: anchors must resolve |
| 7 | Turn shape | One typed action per turn, 12 actions | One message plus requests | **Adopted.** It cuts round trips 2–4× (§17) |
| 8 | Sensors | Track records, percentile frames, `learner_surprise` | Cut; keep the raw event | **Adopted,** with two additions. The latent state is rendered in words with its uncertainty (§8.1), which is the owner's latent-state requirement. Confidence taps and hedge reads go into the router card as events (§15.2; owner, 2026-10-24) |
| 9 | Forecasts | Four kinds | Two | **Adopted,** and logged from TE1 rather than TE2. `lesson_step_retained` is also the bitter-lesson challenger to the learned weight (§12.2; owner, 2026-10-24) |
| 10 | Delayed checks | Their own mechanism | Through Check once, then RW6b | **Adopted,** with a **transfer** purpose added: the owner's outcome names transfer as well as retention (§13) |
| 11 | Grounding | Contextual embeddings from E1 | Sections whole | **Adopted.** The owner's 2026-10-24 adoption of local `pplx-embed-v2-context-9b` is a separate stage. The teacher depends only on the retrieval seam (§9.2) |
| 12 | Reveal kind | New `lesson` kind | One rebuild, shared with C2's chat kinds | **Not adopted.** A lesson writes the existing `tutor_answer`/`source_review` kinds with basis `lesson:<id>`, as the tutor does (§12). TE1 will land long before C2, and the tutor path already writes exactly these rows |
| 13 | Split diagnoser on lesson checks | One diagnoser per block | Not run on lesson checks | **Adopted.** The teacher's findings persist through `propose_gap` (TE2) |
| 14 | Router sensor mode (TQ7, owner-decided) | In this spec, with H0/H1/S/C arms | Defer; drop H1 | **Moved, not dropped.** It is a router question; it goes to the router spec, deferred with a trigger. H1 waits on the learned-parameters decision (Q6) |
| 15 | Experiments (doctrine A/B and others) | TE5 | Defer | **Adopted.** None can resolve at current volume (§21). The doctrine version is logged |
| 16 | Scaffolding-retirement rule | Build, then retire | Invert | **Adopted.** Structure is added only when a measured failure names it |
| 17 | Metered fallback | Cap $0.50 | Plan-only by default | **Not adopted.** T1 redesign D (the offer is the grant) is the owner's rule for every action. `teacher` gets a price setting so no offer is made until a price exists, plus a per-lesson cap (§17, Q7) |
| 18 | One stage | — | TE-min, including placement, goal LOs and gaps | **Split** into TE1 (the lesson core) and TE2 (probes, goal LOs, gaps, forecasts). The first lesson ships sooner, and TE1 needs no text-gap rebuild |
| 19 | MCP | Out of scope | A tool contract | **Adopted and specified** (§9, §16). Revised by the owner (2026-10-24): chat cold checks and probes are allowed behind C2, at a learned weight (§16.2) |
| 20 | Learned parameters | — | Drop LP1–LP3 | **Revised by the owner (2026-10-24) for this case only.** The lesson-check weight and the tap/hedge recalibration it needs are learned (LP-min), because lesson checks have a clean delayed-outcome signal. The review's other LP verdicts stand |

---

## 2. What we take from LearnHarness, and what we change

Paths in this section are in the LearnHarness repository. Everything here paraphrases an idea. Our doctrine files are written from scratch (§10).

### 2.1 Its teaching strengths

| Strength | What it does | Source |
|---|---|---|
| **A theory of why lessons fail** | A learner won't commit to a fact that something more basic might later overturn. That hedge, not the amount of material, is why lessons don't stick. Two principles remove it: start from facts that can be accepted at face value (i), and make every later step feel discovered rather than decreed (ii). The payoff is the click: facts the learner held separately turn out to follow from a few base facts | `docs/teaching-methodology.md` §2–6; `src/agent/prompts/teacher/05-method.md` |
| **Measure, plan, teach** | Teaching works only at the edge of what is held, so the edge is found first. The system absorbs the logistics (order, sources, fact-checking), so the learner's effort goes into the material | `src/agent/system-prompt.md`; `docs/teaching-methodology.md` §7a |
| **Goal interrogation** | A vague goal is questioned until it is concrete. A learner who doesn't know the terrain starts with orientation | `src/agent/prompts/prober/10-probe-doctrine.md` §2 |
| **The prober** | A bracket search per dependency strand: a floor the learner gets right and a ceiling they miss. Enter near the hardest thing the goal needs, jump after confident successes, step gently after hesitant ones, dig into misconceptions, never re-ask bracketed ground | `prober/10-probe-doctrine.md` §3–5; `docs/probe-teach-split.md` §2 |
| **The minimal tree and the map** | The smallest dependency tree from what is held to the goal. Every root is stress-tested: is it really accepted as-is, or a disguised theorem? The map shows landmarks, not a syllabus. It is presented briefly and moves whenever teaching shows the learner differs from it. A question's node tag is a position, never a completion | `teacher/10-planning.md`; `docs/probe-teach-split.md` §3; `docs/teaching-methodology.md` §7b |
| **One reasoning step at a time** | One fact per motivated move, so it lands as obvious and errors surface where they are made. Presentation is chosen per step, Socratic or expository by topic and the learner's energy. No "Node 3" chapters, no meta-narration | `teacher/20-teaching.md`; `docs/teaching-methodology.md` §5, §8 |
| **Predict, teach, check** | A prediction before a step is a nudge and need not be answerable; it arrives open. A check after the step must be answerable from the lesson, applied rather than recited, and built so each wrong option is a specific wrong model; it arrives collapsed until the learner has read. A miss means repair before building | `teacher/28-predictions.md`; `teacher/30-question-principles.md`; `teacher/20-teaching.md` |
| **Commit before posing** | Every graded question carries its committed answer, with the reasoning written before the key. Options are built by mutating the correct claim into believable wrong-model claims | `src/agent/prompts/shared/20-question-tools.md` |
| **Reading confidence** | Stated probability is read against the verdict. Confident and wrong is the strongest signal. Confidence at or below chance means the learner distrusts their own pick. "I don't know" is a gap, not an error | `shared/25-confidence.md` |
| **The learner's words as primary data** | A thinking field on every question, and a separate "while reading" channel. One answer is one bit; the thinking is the picture. Dictated text is read leniently | `shared/16-mental-model.md`; `shared/20-question-tools.md` |
| **Voice and accuracy** | No praise or agreement bias, and a wrong answer is named plainly. Verify doubts before teaching; flag what can't be verified | `shared/10-voice.md`; `shared/15-accuracy.md`; `teacher/40-jobs.md` |
| **Compaction that keeps the learner** | The summary keeps, in order: the learner's understanding and how it changed (the heaviest part), the teaching arc, the plan verbatim, and the current moment | `src/core/compaction.ts` (`buildCompactionPrompt`) |
| **Practice doctrine** | States the distinction this spec rests on: a teaching check asks about an idea still active in mind, so it measures comprehension, while practice must produce the idea from an inactive state in a fresh situation. Also: three modes, a minimal-reveal hint ladder, miss classes, fresh-surface retests | `src/agent/prompts/practice/10-doctrine.md` §I–IX |
| **Instruments over description** | For a dynamic idea, build a verified demo or a checked figure. *(LearnLoop: served by Reader RW5d, `spec_reader_show_me_figures_v1.md` §10.4: a figure as a manipulative in a discovery step, grammar or sketch tier.)* | `teacher/50-demos.md` |

### 2.2 What it lacks, and LearnLoop has

| LearnHarness | LearnLoop (§5 has the code) |
|---|---|
| The graph "stores the ideas and their connections, not ratings of your ability" (`README.md`). Understanding is never encoded, and its state model is unbuilt (`docs/vision.md` §1) | **Persistent latent state:** per-LO mastery with uncertainty (the evidence-side EKF), the router's learner card, AD's predicted unassisted success and subject level, learned couplings between LOs, misconceptions, open hypotheses and retention risk |
| The prober reads only session and proposition lists. Lessons run "fully standalone", with no graph context (`prober/10-probe-doctrine.md` §1; `docs/probe-teach-split.md` §5) | **A brief built from the ledger:** every earlier attempt, hint, tutor exchange, lesson and delayed check on the goal's LOs |
| Each answer is read on its own; nothing records what was shown before it | **Attempts are not independent.** The reveal ledger, hint windows and the eligibility decision mark later answers primed or assisted, and evidence weights follow |
| The teacher grades its own free-recall checks against its own answer (`shared/20-question-tools.md`) | **A blind grader** that never sees the lesson, the teacher's reasoning or the learner's history |
| Practice grades write nothing, and there is no spacing (`docs/architecture.md` §7). Retests happen in the same session | **Delayed cold checks** on unseen questions ("Check once", and RW6b's valuation when it lands), with retention and transfer as the outcome |
| No held-out material | **Exam and held-out protection** (AD's A8, `learner_protection`, `exam_withheld`, the owner rule that exam material is never taught) |

### 2.3 What we change

1. **The prober reads state first and probes second.** Most of what LearnHarness measures from scratch is already in the ledger. The teacher probes only where the state can't say, on vault items served cold (§11). The bracketing doctrine stays, to choose *which* probe.
2. **The teacher never grades.** Its committed solution is the blind grader's reference.
3. **In-lesson checks are recorded honestly as comprehension:** an assisted weight learned from what happens later, never certification (§12).
4. **The lesson is judged after it ends.** Each landed node commits a delayed cold check on an unseen question, plus one transfer check per lesson (§13). The next lesson's brief shows the results.
5. **The lesson writes into the latent state:**
   - graded checks;
   - exposure in the reveal ledger;
   - gaps and misconceptions through the text-gap pipeline;
   - later, a prediction-only learning opportunity in AD (§14).
6. **The runtime is a tool contract.** An MCP chat host can later be the teacher, with LearnLoop as the backend (§16).

---

## 3. Thesis

**A lesson changes a latent state that LearnLoop already estimates. It is judged by what that state does after the lesson ends.**

- **Performance is not learning.** A check right after a step catches the idea while it is still active. That is the right signal for steering (did the step land?) and the wrong one for judging the lesson (A3, A10, C8; LearnHarness's own practice doctrine). Retention is measured only by a delayed, unaided answer to a question the lesson didn't show. Transfer is measured only by such an answer in an unfamiliar situation.
- **Attempts are not independent.** What the learner saw, was hinted, was taught or forgot changes what each later answer means. The lesson writes into the ledger that encodes this, so later answers are read correctly. It also reads that ledger, so a primed success is never taken for knowledge.
- **Latent state replaces most probing.** The teacher reads mastery with its uncertainty, AD's predictions, the learner's past words and errors, and the results of earlier delayed checks. It asks only where those don't settle the question.
- **How much an in-lesson answer says is learned from what follows** (owner, 2026-10-24). A lesson check's weight is fitted to later cold outcomes on unseen items, never to later lesson checks. The teacher's own forecast competes to replace that weight (§12.1, §12.2).
- **The model owns pedagogy; code owns truth.**
  - **The model owns how to teach:** order, pacing, mode, when to probe, how to read an error, when to detour and when to stop. The doctrine steers it.
  - **Code owns what a smarter model would not improve:** what may be shown, who grades, what counts as evidence and at what weight, when the delayed check happens and on which item, and the receipts.

**The test for every piece of structure: would a smarter model make it unnecessary?** If so, it goes into the doctrine or nowhere.

---

## 4. Scope

**In scope:**
- Lessons on the desktop that the learner starts or accepts (TE1, TE2).
- The lesson contract: the brief, the turn, the receipt, and a tool surface that two drivers share (the desktop teacher model; later an MCP host).
- The doctrine.
- Evidence, reveal and delayed-check semantics, including the learned lesson-check weight and its forecast challenger (§12).
- AD reads, and the design of the AD lesson opportunity (TE3, an AD follow-up).
- Two router-spec amendments: lesson suggestions, and confidence on the learner card (§15).
- The chat lesson contract, including chat cold checks and probes behind C2 (TE4, built with the MCP track).
- Transport under T1.

**Out of scope:**
- **Router-started lessons without the learner's yes.** Not planned.
- **Grading changes.** None.
- **The retrieval embedding space.** A separate stage owns it.
- **Router sensor mode** (moved, §1.4 row 14), and the learned-parameters spec beyond LP-min.
- **LearnHarness's practice doctrine applied to practice and hints.** A separate track; this spec borrows only its learning/performance distinction.
- **Experiments and teacher-built demos.** Deferred (§22).

---

## 5. Code truth

Re-audited 2026-10-24 at main `b7e0444b5`, plus two branches:
- **T1** in `learnanything-merge2`, branch `merge/t1-onto-main`, head `ad6dad0c4` (the review cited `aac4307b2`);
- **AD23** in `learnanything-ad1`, branch `adaptive-difficulty/ad23`, head `32eee1da9` (the review cited `5e62cd0d6`).

Spec lines marked "wt:" are the AD23 worktree's copy of the AD spec.

### 5.1 Tutor surfaces, code-run tools and grounding

- **Tool requests are structured output.** No native tool calls exist.
  - `ai/tool_requests.py:22` defines `TUTOR_TOOLS = (find_practice, find_sources, compare_sources)`.
  - `find_sources` intents are `explain | remediate | alternative | worked_example` (`:37`). `find_practice` intents are `practice | discriminate | retention | remediate` (`:28`).
- **The dispatcher** is `instructional/tools.py` (`TOOLS` at `:129-153`, which adds `find_facets` and `practice_availability`).
  - It leak-checks the request text against the bound item's key (`:611`).
  - It records `request` and `run` rows in `source_tool_calls` (`request_tool` at `:487`, `run_requested_tool` at `:539`).
  - It never returns an expected answer, rubric, hint or solution (module docstring, `:1-19`).
- **Policy comes from the caller, never from arguments.**
  - Policies are `reading | assisted_practice | post_attempt | cold_attempt` (`source_retrieval/policy.py:19`).
  - Caller kinds are listed at `:22-23`; there is no teacher kind. `derive_policy` is at `:78`.
  - Every tool is refused during a cold administration, which includes exam-reserved items (`instructional/policy.py:33`).
- **Grounding seams:**
  - `teaching_scope` (`source_retrieval/corpus.py:588`; with an item bound it drops exercise, solution and item-linked spans) and `exam_withheld` (`:277`);
  - `TutorSpanProvider` (`source_retrieval/tutor.py:320`) and `PinnedSpanProvider` (`:468`);
  - citation validation: `tutor/tutor_qa.py:1061 _validated_citations` and `tutor/reader_modes.py:623 finalize`.
- **The tutor writes reveals.** `tutor/tutor_qa.py:904-915`: `source_kind = "tutor_answer"`, basis `tutor_qa:{context}`, and amount equal to the key overlap. Cited spans that overlap a key become `source_review` rows.
- **Precedents for model-authored questions:**
  - Reader quick checks are AI-authored, span-grounded and formative only: no attempt (`reader/reader_quick_check.py:1-17`).
  - `escalate` (`:831`) mints a `PracticeItem` with `origin = "codex_proposal"` and span `source_refs`.
  - RW1b's "reconstruct" then creates a `test_me_later` commitment on it (`reader/active_reading.py:104-116`).
  - Teach-back grades a whole conversation blind, as one `teach_back` attempt (`tutor/teach_back.py`).
- **No `instruct` executor exists.**
  - Items in instruct lanes are served as ordinary practice (`daily_plan/staged_frame.py:24-27`; `daily_plan/types.py:38` maps `new` to `instruct`).
  - Actions are at `scheduling/controller_actions.py:17-23`.
  - A learner pick is logged with no propensity (`db/stores/router.py:134`; the CHECK in migration 181).
- **Router decisions and randomization.**
  - On main, `scheduling/randomization_layer.py:57` admits four designs: `mrt_reversible`, `epsilon_tiebreak`, `commitment_parallel` and `model_mixture`. The AD23 branch adds two.
  - `mixture` samples over reversible candidates, with a floor and an exact logged propensity (`spec_action_router_v1.md:271-273`). Decisions are stored in `router_decisions` (`:302`).
  - The card (`spec_action_router_v1.md` §4, `:126-155`) carries interaction signals and "not now" preferences, but no confidence taps.

### 5.2 Latent state a teacher can read

- **The router card:** `router/card.py:88 LearnerStateCard`, with `CARD_VERSION = learner_state_card_v1` (`:34`) and `build_card` (`:244`).
  - Its inputs are gathered in `daily_plan/router_card.py`.
  - The router reads it at `router/requests.py:124-145`; its mode defaults to `mixture` (`config/schema.py:3264`).
  - It is never sent to the blind grader (`spec_action_router_v1.md:126-155`).
- **The guarded learner context** is `learner_context.py:1598 learning_context` (`KeyBook` at `:211`, `leaks_key` at `:284`). It holds misconceptions and candidates, open hypotheses, recurrence groups, recent answer traces, open learner-text gaps, retention risks, unknowns and labels.
  - Each trace carries `hints_used`, `assisted`, `revealed_before`, `cold_check`, `entry_surface` and `evidence_origin`.
  - MCP C1a already serves this read model.
- **Predictors:** `field/types.py:224 LearnerPredictor` (`predict_item`, `region_estimates`). The active predictor is `mastery_ekf`.
- **Confidence:**
  - `practice_attempts.answer_confidence` (1–5, migration 031) is read by no LLM role. Its only reader is a logged feature (`diagnosis/probe_episodes.py:2687`).
  - The map in `goals/exam_calibration.py:30` is fixed, not recalibrated.
- **Surprise:** `attempts/surprise.py:20-29, 55`.
- **AD (branch only):** see §5.7.

### 5.3 Evidence, attempts, reveals and help

- **Attempt types.**
  - Defined at `attempt_types.py:5-18`, with a SQL CHECK in `migrations/153_variable_rubric_scales.sql:22-37` that is unchanged since.
  - Masses (`config/schema.py:1612-1631`):

    | Mass | Types |
    |---|---|
    | 1.0 | `independent_attempt`, `open_text`, `diagnostic_probe`, `hinted_attempt`, `exam_attempt` |
    | 0.8 | `teach_back` |
    | 0.7 | `dont_know` |
    | **0.5** | **`reconstruction_after_walkthrough`** (`:1619`) |
    | 0.35 | `exam_evidence` |
    | 0.3 | `self_report` |
    | 0 | `guided_walkthrough`, `skip` |

  - **The mass is already a per-observation input.** `MasteryObservation.attempt_evidence_mass` (`learner/mastery.py:56`) overrides the type default where it is set (`:328-332`). The live path fills it from config by type (`attempts/attempts.py:4446`). A learned mass plugs in here (§12.1).
- **Assisted.**
  - `LEGACY_ASSISTED_ATTEMPT_TYPES` (`diagnosis/causal_activity_policy.py:93-99`) are `hinted_attempt`, `guided_walkthrough` and `reconstruction_after_walkthrough`.
  - `attempt_counts_as_assisted` is at `:189`. An assisted attempt is not eligible for certification (`:183`). A primed non-diagnostic attempt is `repair_activity` (`:140-141`).
- **Primed:**
  - mastery keeps `last_evidence_at` (`learner/mastery.py:57-60, 567, 620`);
  - IRT `b` is shifted by `priming_b_offset` 2.0 (`attempts/attempts.py:4290`; `config/schema.py:165`);
  - never discount twice through mass (`spec_learner_field_v1.md:236`).
- **The reveal ledger** is `migrations/179_answer_display_reveal.sql:23-42`.
  - Five kinds: `tutor_answer`, `repair_display`, `guided_redo`, `source_review`, `answer_display`.
  - Rows are keyed by `practice_item_id NOT NULL`, and the table is append-only.
  - Code: `attempts/reveal_ledger.py:48`. Auto-prime applies once the reveals sum to ≥ 0.35 (`serve_eligibility.py:81`).
- **Help:**
  - `help_assists` (`migrations/210_help_assists.sql:22`; its `surface` CHECK includes `'tutor'`);
  - the server fold (`attempts/hint_fold.py`; `db/stores/help_assists.py:198`);
  - `practice.request_hint` (`learnloop_sidecar/handlers/hints.py:176`).
- **No admission state.**
  - `PracticeItem` (`vault/models.py:752`) has no `admission_status`. It exists only on `diagnostic_pack_cards` (083:49-50) and `practice_pool_surfaces` (085:43-44).
  - Held grades are route-rule and contract holds only (`held_grades.py:1-36`; `outcome_contract.py:118, 138`).
  - The precedent for holding an item from serving is the rung-variant hold (`scheduling/serving_exclusions.py:13, 108, 137-138, 222`).
- **Origins:** `vault/models.py:41-43` allows `human | codex_proposal | canonical_extract | import | probe_remint`.

### 5.4 Scheduled checks ("Check once")

- **Creation.** `curriculum/commitments.py:300 create_commitment(action="test_me_later", targets, due_hint, provenance, …)`.
  - Provenance is free JSON (`migrations/072_commitments.sql:81`; `commitments.py:379`), and `via` may be any string (`scheduling/intent/resolution.py:119`).
  - The disposition is `one_check_pending` (`resolution.py:74`).
- **Dating.** `due_hint` is used if set, else `created_at + capture.test_me_later_days` (default 7) (`scheduling/intent/serving.py:130-150`; `config/schema.py:3191`).
- **Answering and settling.**
  - An assisted answer is practice and re-dates the check (`serving.py:103-117`).
  - The cold decision is `serve_eligibility.CHECK_ONCE` (`:112`).
  - Settling runs through `scheduling/intent/checks.py:65` and `commitments.py:717`.
- **Gotcha.** Target items, not LOs: a pending check holds the items it covers (`spec_daily_loop_v1.md:333, 365-369`).
- **RW6b is pending** (`spec_reader_workbench_v1.md:999-1046`):
  - candidates come from `find_practice` with `unattempted_only`, and revealed families are excluded;
  - EVSI valuation;
  - retention checks are dated at the effective due date, else 3 days, with `max_wait_days` 14;
  - provenance carries `via` and `purpose`.
  - W13 requires one scheduled-check mechanism and one question producer (`:132`).

### 5.5 Protection

- `learner_protection.py:190 withheld_items` covers exam, held-out, reservations, open cold checks and retries, and diagnostic probes. It fails closed.
- `content/sources/exam_material.py:3-7, 17-80` states the owner rule that exam material is "never taught, never shown to a model as teaching or explanation", and holds the predicate.
- AD's A8, with Option B: §5.7.

### 5.6 Gaps, LOs, placement and forecasts

- **Text gaps** (`diagnosis/text_gaps/actions.py`):
  - `write_created_prerequisite` (`:256`) creates a concept, LO and edge *beneath an existing LO*, with provenance `codex_proposal` / `learner_text_gap_v1` (`:271`);
  - `would_cycle` (`:125`), `add_prerequisite_edge` (`:188`), `creations_today` (`:223`), `undo_creation` (`:354`), `reverse_gap` (`:587`);
  - the cap is `learner_text_gaps.max_creations_per_day` = 3 (`config/schema.py:2561`), enforced at `pipeline.py:536`;
  - `source_kind` CHECK: `tutor_question, stuck_answer, diagnosis, workbench_text, reader_formative, hint_feedback` (`migrations/212_hint_feedback_source_kind.sql:27-29, 97-99`). There is no goal entry.
- **Placement:**
  - assumption sources are `self_report, fast_track, predictor, quick_check` (`migrations/172_placement_assumptions.sql:10`);
  - `diagnosis/quick_check.py:117 start_quick_check(…, learning_object_ids, …)`;
  - `placement.initial_probes = false` (`config/schema.py:3039`), `quick_check_k = 4` (`:3048`).
- **Forecasts:**
  - `scheduling/forecast_receipts.py:72` lists `diagnosis_next_observation, repair_cold_outcome, item_unassisted_success`;
  - binding kinds are at `:82-83`.

### 5.7 Adaptive difficulty (AD23 branch)

- **The band.**
  - `practice_band = (0.70, 0.80)`, `calibrate_below = 0.25` and `ready_threshold = 0.8` (`config/schema.py:3516-3522`).
  - Code: `model.band_probability` (`model.py:161`) and `predict.predict/score` (`predict.py:53, 65`).
  - Band mode engages late (G-AD2-18, wt:625-627).
- **Subject level** is `θ_G` (wt:377-384). There is no public API.
  - The read path is `replay.snapshot` (`replay.py:844`, a read-only entry) then `predict.predict` (`predict.py:152`).
  - Packaged reads: `readiness.lo_readiness` (`readiness.py:57`) and `readiness.card_fields` (`:104`: `p_band_next`, `p_bar_at_top`, `untested`). Untested stays untested (`:68-78`).
- **Couplings.** `relatedness.load_structure` (`:766`) and `.coupling(lo)` (`:705`). `learned_coupling` stays off until the owner adopts it (`schema.py:3512`).
- **The guard (A8, Option B):**
  - entry points are `@entry` (`operation.py:941-1011`) or `ad_operation` (`:761`);
  - unclassified tables are refused (`:213`, `tests/test_ad_guard.py:664`), and a denial fails closed (`:35-38, 855`);
  - `protected_tables.py`: `ROLES` at `:168`, `COLUMNS` at `:221`, `AD_WRITABLE` at `:485`, `READING` at `:540`;
  - the epoch is computed at `material_view.py:216-252`, and `reading_withheld` is at `:1289`;
  - windows close at `material_view.py:1635`;
  - **teacher code must not run inside an AD operation:** it would lose the DENIED tables and could not write.
- **AD's filter.** It is deterministic assumed-density filtering (Gauss–Hermite moment matching, back-projection, grid weights `W_t(ξ) ∝ W_{t−1}(ξ)·Z_t(ξ)`; §5.6, wt:492-527).
  - Its eligibility admits only `independent_attempt`, `open_text`, `diagnostic_probe` and `exam_attempt` (wt:503-512), so **AD never reads a lesson check**.
  - An ineligible graded attempt only closes the reading windows of facets its item weighs on (wt:524).
  - A2 forbids AD to write evidence or mastery (wt:79). A5 forbids hand-picked evidence weights (wt:82).
- **Opportunity kinds:**
  - `reading`, `reader_tutor_exchange`, `worked_example`, `in_passage_question` (`attempts/salience_firewall.py:283-298`);
  - the CHECK is in 213:119-120 and is rebuilt in 214:289-318;
  - the priors are versioned (`priors.py:145-151`);
  - new kinds are deferred, with a trigger (wt:1722), and A12 limit 1 and D20 name the current kinds;
  - the graded in-passage path (wt:525, 712) is not wired (`replay.py:154`).
- **Commissions.** `generation.commission_point` (`generation.py:172`) writes `ad_selections`. Commissions expire after 7 days (wt:872-873).
- **Version.** Successor mvp-0.30, migration 214, six switches (`successor.py:35`).
- **Randomization.** There are "six (and only six)" designs (`scheduling/randomization_layer.py:4, 71`).

### 5.8 Transport (T1 branch)

- **Task and route.**
  - `AITask` is at `ai/routing.py:33`; there is no teacher task.
  - `DEFAULT_SERVING_TASK_ROUTES` is at `config/schema.py:1581`: `tutor_qa`, `grading` and `teach_back` go to `chatgpt_low`; `authoring` goes to `chatgpt_medium`.
- **The offer.**
  - `METERED_PRICE_SETTINGS` (`ai/plan_fallback.py:73-91`) covers 18 tasks.
  - `offer_blocker` (`:126`) refuses only when a *listed* task has no price; an unlisted task is offered with no price gate.
- **Grants** are held in memory, keyed by vault and then origin RPC method (`_GRANTS` at `:418`, lock at `:430`). They are set by `answer_offer` (`:741`) and `grant_origin` (`:760`), cleared by `revoke` (`:767`) and checked by `is_granted` (`:807`).
- **Spawned jobs** capture `unit_origin` (`:523`) and `unit_token` (`:531`). `inherit_grant=True` is AST-pinned to one site (`tests/test_plan_first_transport_offer_grants.py:428`).
- **Spend.** T1 adds no cap of its own (`:25-31`). `SpendBudget` is `ai/spend.py:151` (`SpendCaps` at `:107`).

### 5.9 MCP (main)

- **C1a is landed.** `src/learnloop_mcp/server.py:477-590` serves six tools: `status`, `today`, `progress`, `library`, `find_sources` and `learning_context`.
  - Every call writes an `interaction_events` row (migration 203).
  - The model-written-text switch `diagnosis.chat_shows_recorded_text` is off (`config/schema.py:1850`).
  - The server tells the host that practice and grading happen in the app.
- **C1b and C2** are specified in `spec_mcp_frontend_c1.md:387-398` and `:377-385`. Neither is built.

### 5.10 Heads

- **Migrations.**
  - Main's head is 217, and 214 is absent.
  - T1's is 217.
  - AD23's is 217 and includes `214_adaptive_difficulty_serving.sql`.
- **Successor chain.** It ends at mvp-0.29 on main (`algorithm_versions.py:396-418`), and AD23 reserves mvp-0.30.

### 5.11 Revision 1 claims corrected here

- `reveal_events` has five kinds and is keyed by item.
- There is no admission state and no "pending" held grade.
- `find_sources` has none of revision 1's intents.
- The confidence map is fixed.
- The text-gap pipeline has no goal entry.
- `teacher_placement` is not an allowed assumption source.
- The quick check is `start_quick_check`, not `start_calibration_session(k)`.
- The card class is `LearnerStateCard`, with version string `learner_state_card_v1`.
- `SpendBudget` is in `ai/spend.py`.
- The `instruct` lane serves practice.
- MCP C1a exists on main.

---

## 6. Architecture

```
ENTRY  desktop (TE1): "Teach me this" on an LO, a Reader selection, or a new-topic offer in Today
       desktop (TE1b): an accepted router suggestion card in Today (§15.1)
       desktop (TE2): a typed goal
       chat (TE4):    MCP tool lesson_open, the host model as teacher
          │
          ▼
teacher/  (code: a composition layer like instructional/; nothing imports it back)
  1. resolve the goal to LOs; refuse protected material in one plain line
  2. build LessonBriefV1 from the ledger (§8.1)
  3. driver loop
       desktop: teacher model (AITask `teacher`, doctrine vN) → TeacherTurnV1 (§8.2)
       chat:    the host calls the same actions as MCP tools (§9, §16)
  4. execute actions: validate → run → write a turn row → return the result
       read_source, find_sources, find_practice → instructional dispatcher, caller kind `teacher`
       read_history → learning_context + learner_protection
       pose_check   → minted held item, committed solution → answer → attempt → blind grader
       serve_probe  → existing serve path, cold (TE2)
       write_plan, forecast, close; propose_gap, create_goal_lo (TE2)
  5. guard every learner-facing output: KeyBook keys, the open check's solution, citations
  6. close → LessonReceiptV1 → Check once commitments (§13)
          │
          ▼
LATER  DL2 serves the checks cold in Today → ordinary attempts → mastery and FSRS, AD → the next lesson's brief
```

**Who owns what:**
- **The teacher (the desktop model, or the chat host):** every pedagogical decision inside the lesson.
- **Code:**
  - what enters the model's context;
  - guards, grading, evidence, reveal accounting;
  - the delayed-check items and dates;
  - caps and receipts.
- **The router:** suggests lessons, and the learner accepts or declines (TE1b, §15.1). A lesson the learner starts unprompted is a `learner_pick`.
- **AD:** read by the teacher, and later fed a prediction-only opportunity (§14).

**Layering.**
- The new package is `teacher/`. An import-linter contract says:
  - it writes attempts only through the attempts path, and never writes mastery, FSRS or evidence directly;
  - it reads AD only through AD's read-only `@entry` functions.
- The sidecar handlers live in `learnloop_sidecar/handlers/lesson.py`. The MCP adapter reaches the same service through `learnloop.remote` (§16).

---

## 7. Lesson lifecycle

1. **Open.**
   - The entry point supplies the LOs:
     - an LO page gives that LO;
     - a Reader selection gives its section's LOs, as the Reader's active-reading actions already resolve them;
     - a new-topic offer gives the offered LO;
     - an accepted router suggestion gives its target LOs and the router's reason (§15.1). The suggestion's decision id is stored on the lesson row.
   - Typed goals come in TE2 (§11.5).
   - A goal that names protected material is refused with one plain line.
   - Code builds the brief.
2. **Goal.** When the goal is vague, the model makes it concrete in conversation. That is LearnHarness's goal interrogation, as judgment rather than a form.
3. **Find the edge** (§11).
   - The model reads the state.
   - Where the state can't settle a node, it chooses to:
     - confirm it cheaply inside teaching;
     - serve a vault probe (TE2);
     - or offer "Check what I already know".
4. **Plan.**
   - An outline map with anchors.
   - It is presented in a few sentences beside the map, and that turn ends.
   - The learner's reply is either the go-ahead or a change.
5. **Teach.** Predict → teach → check → repair or continue, one reasoning step at a time. A check's node tag is a position, never a completion.
6. **Detour** (TE2).
   - When a missing foundation surfaces, the model verifies the step against its reference and finds the first wrong step.
   - It then repairs in place, or inserts a foundation and re-teaches what depended on it.
   - Learner text that names a gap or misconception goes to `propose_gap`.
7. **Close.**
   - Close reasons: goal reached, learner stop, budget, plan unavailable, or contract failure.
   - **The recap** says what to retrieve later, not a summary.
   - **The receipt** is written.
   - **Delayed checks** are committed and named plainly: "I'll ask you one of these, cold, in about three days."
8. **After.**
   - The checks are served in Today.
   - Their results appear in the next brief on these LOs.
   - A later lesson on the same LOs resumes from the last plan and receipt.

**Compaction.** Past `teacher.context.compact_at`, the transcript is summarized. The summary keeps, in order:
1. the learner's understanding and how it changed;
2. the teaching arc;
3. the plan verbatim;
4. the current moment: an open check, and any commitments made.

The idea is LearnHarness's (`src/core/compaction.ts`); the prompt is our own.

---

## 8. Contracts

### 8.1 `LessonBriefV1` (code → teacher)

The brief is built deterministically from the ledger and versioned. It is the only learner context at open; anything more comes through actions.

| Field | Contents |
|---|---|
| `goal` | The text, the LO ids, and how they were resolved |
| `nodes` | Per goal LO and its prerequisite closure in the vault graph (to `teacher.brief.depth`, default 2), plus adopted AD couplings (§14). Each node carries: its statement; its label (untested, assumed or demonstrated, field F4); predicted unassisted success in words with its interval (AD readiness when AD serves, else the active predictor, saying which); retrievability; the last cold result and its date; open misconceptions and hypotheses; eligible vault probe items as **headers only** (id, truncated stem, predicted success) |
| `history` | An index of attempts, hints, tutor exchanges and lessons on these LOs. Each one-line header shows whether the attempt was assisted, primed or cold, with any confidence tap and hedge read. Raw text comes through `read_history` |
| `last_lessons` | Earlier receipts on these LOs, with **their delayed-check results** ("taught 4 days ago; cold check on X answered wrong, marked 5/5 sure") |
| `sources` | The goal's sections, whole, from `teaching_scope`, with exam and model-withheld roles removed, and with span ids. If they exceed `teacher.context.sources_tokens`, the section outline instead (§9.2) |
| `constraints` | Driver, caps, budget remaining |
| `doctrine` | Version |

**Never in the brief:**
- EVSI values, costs or policy scores (B1);
- cold-reserve or protected items;
- vault items' expected answers or rubrics;
- for a chat driver, model-written diagnosis prose while `diagnosis.chat_shows_recorded_text` is off.

### 8.2 `TeacherTurnV1` (desktop teacher → code)

One strict-schema object per model turn:
- **`message`:** Markdown with LaTeX. Optional `choices`; an optional `visual` spec (the existing figure and animation routes). *(RW5d: a figure `visual` is a `FigureRequestV1` with origin `teacher`, and the figure's own predictions are off in lessons; see `spec_reader_show_me_figures_v1.md` §6.5, §7.1.)*
- **`prediction?`:** `{node, prompt, choices?}`. It opens immediately.
- **`check?`:** `{node, question, form (choices | free), committed_solution, rubric (criteria named by fact), anchors}`. It opens collapsed, below the message.
- **`requests`:** zero or more actions from §9.

Validation errors go back to the model as correctable. After three consecutive failures, the lesson closes with `teacher_contract_failure`.

### 8.3 `LessonReceiptV1` (teacher → ledger)

| Field | Contents |
|---|---|
| Identity | `lesson_id`, driver (`desktop` or `chat:<host label>`), model and route, doctrine version, goal, LOs |
| `close_reason` | `goal_reached`, `learner_stop`, `budget`, `plan_unavailable`, `teacher_contract_failure` |
| `plan_versions` | Every stored outline |
| `nodes` | Final status (`held`, `uncertain`, `taught`, `landed`), anchors, checks (attempt ids and grades), probes |
| `exposure` | Items given reveal rows; passages shown |
| `gaps`, `created_los` | Text-gap job ids; goal LOs (TE2) |
| `delayed_checks` | Commitment ids, item ids, purpose, due date |
| `forecasts` | Receipt keys for `lesson_check_correct` and `lesson_step_retained` (TE1) |
| `weight_inputs` | Per lesson check: the tap, the hedge read, AD's (or the active predictor's) P(success) and subject level just before the check, the learned mass applied, and the forecast key. These are the pairs §12.1–12.2 learn from, logged from the first lesson |
| `stability_inputs` | Per landed node: the liquid-stability inputs `u` (§13; `spec_learned_parameters_v1.md` §4.6). How the LO was learned (`lesson:<id>` reveal, worked example or guided redo, hint depth, cold practice), the last tap or hedge with confident misses flagged, and the last attempt's surprise. Logged from TE1, before the family activates |
| `origin` | `learner_pick`, or the router decision id of an accepted suggestion (§15.1) |
| `cost` | Calls, tokens, estimated USD, route |
| `warnings` | Rejected citations, withdrawn checks, missing delayed-check items |

---

## 9. Teacher actions (the tool surface)

Every action is defined once, with a strict argument model. The desktop teacher requests actions in `TeacherTurnV1.requests`, the existing tool-request pattern. The MCP host calls them as tools of the same name.

| Action | Arguments | Executed by | May write |
|---|---|---|---|
| `lesson_open` | goal text or LO ids, origin (span, LO or item) | Teacher service | `lessons` row; returns the brief |
| `read_source` | section ref or span ids | `teaching_scope` | — (chat: `source_exposure_events`) |
| `find_sources` | query, intent ∈ existing four | Instructional dispatcher, caller `teacher` | `source_tool_calls` |
| `find_practice` | query, intent, LO ids, `unattempted_only` | Same | `source_tool_calls` |
| `read_history` | history ids | `learning_context` guards + `withheld_items` | — |
| `write_plan` | outline: nodes `{id, statement, lo_id?, anchors, premises[]}` | Plan store. One check: anchors resolve in scope | `lesson_plans` version |
| `pose_prediction` | node, prompt, choices? | UI | A `lesson_turns` row (formative) |
| `pose_check` | §8.2 `check` | Mint a held item and store the solution; on submit, an attempt and the blind grader | Item, attempt, `lesson_checks` |
| `serve_probe` (TE2) | vault item id | Existing serve path, cold | Attempt, as that path records it |
| `propose_gap` (TE2) | learner-text ref, kind (`prerequisite`, `misconception`), the gap in words | Text-gap pipeline | Gap job |
| `create_goal_lo` (TE2) | statement, anchors | §11.5 | LO (undoable) |
| `forecast` (TE1) | kind (`lesson_check_correct` when a check opens; `lesson_step_retained` when a node lands), ref, p | `forecast_receipts` | Receipt |
| `close` | reason, recap | Teacher service | Receipt and commitments (§13) |

**No action can:**
- grade;
- write evidence;
- pick or date a delayed check;
- create an edge;
- read protected material.

These hold structurally: no action exists for them.

### 9.1 Policy for a teacher caller

Add `teacher` to `CALLER_KINDS` (`source_retrieval/policy.py:22-23`), and a row to the sources spec's §5.2 table:

| Lesson state | Policy |
|---|---|
| No check open | `reading` |
| A lesson check open | `assisted_practice`, bound to the minted item |
| A served probe or quick-check item open | `cold_attempt`: nothing is returned, and the model is not called until the answer is graded (W7) |

### 9.2 Grounding

- **The goal's sections are delivered whole** where they fit in `teacher.context.sources_tokens` (default 24k; `keep`, a context budget). That is E0's direct-reading arm: every current source is ≤ ~40k tokens.
- **Everything else** goes through `find_sources` and `read_source`, whatever embedding space sits behind the seam. The teacher does not depend on the local contextual retrieval stage.
- **Claims about the source must cite span ids.** Quotes are verified against delivered spans with the existing validators. An uncited claim about the source is returned to the model as a correctable error.
- **The model's own knowledge** is allowed for motivation and intuition, labelled as such.
- **Unanchored committed solutions.** A check whose solution is not source-anchored shows it as "LearnLoop's answer" in feedback (W2's honest label).

### 9.3 Output guards (desktop)

Every learner-facing message passes three guards:
1. `leaks_key` against the vault's `KeyBook`;
2. while a check is open, overlap with that check's committed solution;
3. citation validation.

On a hit, the message is withheld and the model re-prompted. In chat, LearnLoop can guard only what it returns (§16).

---

## 10. Doctrine

**The doctrine is the teacher's policy.** It is a versioned prompt set (`teacher/doctrine/v1/*.md`), written from scratch in our own words and recorded on every receipt.
- Behaviour changes by editing the doctrine, not by adding code.
- A shorter **chat edition** is generated from the same files for MCP hosts (§16).
- The list below is the content outline, not the prompt.

1. **The goal of a lesson.** Understanding that feels obviously true: each new fact seen to follow from what is already held, until facts the learner held separately turn out to follow from a few base facts (the click).
2. **Start at the edge.** Read the state before asking anything.
   - A success that was assisted, primed or seen just before is not evidence it is held.
   - "Assumed" is not "held".
   - Last lesson's cold results outrank its in-lesson checks.
   - Ask only where the state can't tell you. When probing, bracket: enter where the learner is predicted to start failing, step down on a miss, and never re-ask settled ground.
3. **Principle i: unconditional truths first.** Foundations are facts the learner can accept at face value (universal statements, real definitions).
   - An ansatz is allowed: a stated guess at a form, whose verification is the payoff, labelled as a guess, with its closing step planned.
   - Prefer the book's definition, quoted.
   - Stress-test every root.
4. **Principle ii: motivated discovery.** Every step answers a felt problem: why this move, why this form. Nothing appears from nowhere.
5. **The plan.** The smallest tree from what is held to the goal. It is a map of landmarks, presented in a few sentences, and it waits for the learner's reply. It moves when the learner turns out different.
6. **One reasoning step at a time.** Choose the presentation per step (assert, narrate or draw it out) by topic and the learner's energy. Let connections carry themselves; no chapters or meta-narration.
7. **Predict, teach, check.**
   - **Predictions** nudge toward the next step and need not be answerable. Use one where there is something to anticipate. Priors, not rules: conceptual derivations usually open with a prediction or a motivating problem; procedural material for a novice usually opens with a worked example (C10–C13).
   - **Checks** come after the prose. Each must be answerable from the lesson, applied rather than recited, and built so that each wrong option is a specific wrong model. The solution is committed first.
   - **Pitch** checks so that a learner who followed would usually, not always, succeed. AD's 70–80% band is the house prior.
8. **Teach for the cold check.** The checks see the idea while it is active; the test that counts comes days later, on a question the lesson never showed. So:
   - vary the situation across checks;
   - prefer applying the idea to a new case;
   - when a later step needs an earlier fact, have the learner retrieve it rather than restating it;
   - close with what to retrieve.
9. **Read the learner.** Use their words (answer, thinking field), their confidence tap, the grader's hedge read, the history and the last lesson's results. There is no fixed rule for a confident error: decide from the trace whether it is a near-miss or a committed misconception (A1 as background).
10. **Repair before building.** A missed check means the step didn't land: repair and re-check before building on it. For a detour, verify the step against the reference, find the first wrong step, then repair in place or add the missing foundation, and re-teach what depended on it.
11. **Accuracy and grounding.** Claims about the learner's source cite it. When the source and the model disagree, the source's convention wins inside the lesson, and the difference is named. Doubts are verified or flagged.
12. **Honesty about evidence.** Never "you know this" or "you've mastered this". Say "that step landed", and say when the cold check will come.
13. **Voice.** No praise, no agreement bias, verdicts stated plainly. Every sentence installs understanding or earns its place.
14. **Protection.** Never teach, explain or quote exam or held-out material. Say so in one line.

---

## 11. Placement

### 11.1 Rules it respects
- **No placement after imports** (field §5.2; revision 1 called this F2). A lesson opens only when the learner starts or accepts it, never automatically after an import.
- **No structural evidence.** Nothing is assumed from graph structure (KM §8.3, §9.3; field F4; the assumption-source CHECK).
- **AD couplings are prediction-only.** They may inform the model ("these two move together for you"), but never become labels.

### 11.2 State first
- The brief's labels and predictions decide most nodes.
- **Demonstrated** (a cold success with high retrievability): held, no probe.
- **Assumed or uncertain:** confirm cheaply with an in-lesson check, or probe.
- **Untested:** teach, or probe.
- **The entry point** follows AD's predicted success. LearnHarness's "enter near the top" becomes "enter where the learner is predicted to start failing".

### 11.3 Probes (TE2)
- **Choice.** The model picks vault items from `find_practice` headers. They are served cold through the existing serve path, which records the attempt (full evidence when eligible).
- **While a probe is open,** the model is not called and every tool is refused.
- **Cap:** `teacher.placement.max_probes`, default 8. It is `keep`: a burden guardrail, while the model decides when to stop (§18.4).
- **One calibration probe.** With probability `teacher.placement.calibration_p` (default 1.0), code adds one uniformly random goal-path node that has an eligible item. It is logged, and is the only unbiased read of how well the model places (A19 in the review).
- **Teacher-written probe questions** are allowed, and are recorded as lesson checks at the learned lesson-check weight (§12.1), because no admission gate exists for model-written items.

### 11.4 The quick check
"Check what I already know" on a goal calls `start_quick_check(learning_object_ids = goal LOs)` (assumption source `quick_check`). It is offered at lesson open and is never prompted.

### 11.5 Typed goals (TE2)
- A typed goal resolves to LOs through the card and `find_sources`.
- **If nothing matches,** a new `create_goal_lo` action creates the LO at open. It reuses the text-gap write, cycle check, undo and daily cap (`actions.py:125, 188, 223, 354`), but not the judge: the learner's request is the decision.
  - Provenance: `origin = codex_proposal`, `mechanism = teacher_goal_v1`, anchors in `source_refs`.
  - An explicit goal may exceed the cap by one a day.
- **If the goal has no source:**
  - a library lookup is offered first;
  - then the LO is created, labelled "from LearnLoop's model", and the plan anchors are marked unsourced.

---

## 12. Checks and evidence

| Interaction | Record | Attempt type, mass | Assisted | Grader | Reveal |
|---|---|---|---|---|---|
| **Prediction** | A `lesson_turns` row; formative, tier 2 (W1) | None | — | None; the model reads it | None |
| **Lesson check** | A minted item (`origin = codex_proposal`, `mechanism = teacher_lesson_v1`, lesson and node ids, span `source_refs`), held from serving outside its lesson; a `lesson_checks` row | `reconstruction_after_walkthrough`, **learned mass** (§12.1; prior centred on 0.5), **not primed** | Yes: never certifies, never answers a Check once, whatever the mass | Blind, against the committed solution and rubric | The attempt itself |
| **Teacher-written probe** | As a lesson check | As a lesson check | Yes | Blind | — |
| **Vault-item probe** (TE2) | Serve path | As served (`diagnostic_probe` or `independent_attempt`, 1.0) | No, when cold | Blind | — |
| **Quick check** | Unchanged | Unchanged | — | Blind | — |
| **Teaching text** | — | — | — | — | `tutor_answer`, basis `lesson:<id>`, for each vault item on the lesson's LOs whose key the text overlaps (amount = overlap, as at `tutor_qa.py:904-915`) |
| **Cited passages** | — | — | — | — | `source_review` for items whose key a shown passage exposes |
| **Help while a check is open** | A `help_assists` row (surface `tutor`) | — | — | — | If the reply overlaps the committed solution at ≥ 0.35, the check is **withdrawn** (no attempt), and the learner is told |
| **Delayed check** (§13) | Check once | `independent_attempt`, 1.0 | No, when cold | Blind | — |

**Why each choice:**
- **Not primed.** A primed lesson check with a reduced mass would be discounted twice (field §4.3). `reconstruction_after_walkthrough` already classes it assisted. There is no new attempt type and no change to `practice_attempts`.
- **Why it counts at all.** The owner ruled out zero-weight effort. The answer is a real, blind-graded production on the idea just taught, so it is evidence of comprehension. It never stands in for the delayed check. How much it counts is learned from the delayed checks (§12.1).
- **Why a withdrawn check has no attempt.** An answer given after the teacher revealed the solution is not the learner's effort.
- **Why the teacher never grades.** It taught the step, so it is a conflicted judge. Revealed and assisted state stays in the existing ledger, so later answers on those items are read correctly.
- **The split diagnoser is not run on lesson checks.** Only practice attempts trigger it (`spec_blind_grading_diagnosis_split_v1.md:183`). The teacher's in-lesson reading is the diagnosis, and its findings persist through `propose_gap` (TE2): a missing prerequisite is created on first sighting; a misconception goes to the holding pen and must recur before it is promoted (KM :512-514). The delayed check is diagnosed as usual.
- **Minted items stay lesson-only in v1.** The hold works like the rung-variant hold (`serving_exclusions.py`). Joining the practice pool is deferred (§22).

### 12.1 The learned lesson-check weight (owner, 2026-10-24)

**What it is.** The mass `m` with which a lesson check enters mastery:

`m = σ(η)`, with `η = η₀ + u_L + β_c·z_c + β_p·z_p`.

Every number below is a **seeded prior** (owner, 2026-10-24: "priors can be seeded"), labelled with its `prior_basis` and width as `lp_priors_v1` requires. The data move all of them.

| Term | Meaning | Seeded prior (`lp_priors_v1`) |
|---|---|---|
| `η₀` | The global effect | N(0, 1.0²) on the logit scale, so the mass is centred on 0.5 with a 95% prior interval of about 0.12–0.88. **Basis `legacy`:** the centre is today's configured mass for the type (`config/schema.py:1619`), and the width is the LP spec's rule for legacy priors (≥1 logit) |
| `u_L` | A per-LO offset | N(0, τ²). τ is a grid posterior (AD's `ad_hyper` mechanism, `W_t(τ) ∝ W_{t−1}(τ)·Z_t(τ)`) over the support {0.1, 0.2, 0.4}, from uniform weights. **Basis `simulation`:** the support points are confirmed by the planted-recovery suite, which must tell them apart. Its weights are learned |
| `z_c` | Confidence, from the tap (the hedge read when there is no tap; 0 when neither), mapped to a probability by LP-min's tap/hedge recalibration, then put on the logit scale and centred | `β_c` ~ N(0, 0.5²). The centre is "no effect"; the width has **basis `simulation`** (the narrowest prior under which a planted ±0.5-logit effect is still recovered) |
| `z_p` | AD's predicted P(success) for the check's LO just before the check, on the logit scale and centred at the band's middle. Falls back to the subject level, then to the active predictor | `β_p` ~ N(0, 0.5²), with the same basis as `β_c` |

**The bound is structural, not a constant.** The logistic link makes `m` < 1, so a lesson check can never outweigh an unassisted answer. That is a property of the functional form, not a cap (revision 3's Q13).

**What it learns from.** It learns only from later cold checks on unseen items of the same LO.
- **What resolves it.** A qualifying outcome is a graded attempt on an item of that LO that:
  - is unassisted and unprimed;
  - was served cold;
  - is the item's first attempt, with no reveal row and no exposure-to-host mark (§16.2);
  - comes after the lesson check.

  The first qualifying outcome resolves every unresolved lesson check on that LO.
- **There is no resolution window** (revision 3's 30 days is removed). How much a late outcome says about the check is already in the likelihood: the mastery predictor carries the drift and every intervening observation between the check and the outcome. A long gap therefore makes the outcome less informative about `η` without any cut-off.
- **What never updates it.** Later lesson checks: that would be self-confirmation. Chat attempts train their own weight instead (§16.2).
- **The likelihood.** `p(y_cold | η)` is the mastery predictor's success probability for the cold item, computed with the resolving lesson checks entered at mass `σ(η)` and every other observation as recorded. That is a recomputation of one LO's updates.
- **The update.** AD's §5.6 step: moment matching by Gauss–Hermite quadrature on the one-dimensional projection carrying `η`, back-projection to the term vector, and grid weights for τ.
  - It is prequential: each update uses only outcomes resolved before it.
  - The mass applied to a lesson check is the posterior mean of `σ(η)` *as of that check* (filtering, never re-smoothed). Replay therefore reproduces the same mastery trajectory, and a past attempt's mass never changes within a version.

**What it changes, and what it does not.**
- **It changes only how far mastery moves on that check.** The seam is `MasteryObservation.attempt_evidence_mass` (`learner/mastery.py:56`), and the live path and replay call the same as-of function.
- **Fixed, whatever the mass:**
  - a lesson check never certifies;
  - it never answers a Check once;
  - it is never read by AD, whose eligibility excludes it (wt:503-512).

**Where it lives.** On the evidence side, not in AD, because A2 forbids AD to write mastery.
- The ADF and grid code is factored out of `adaptive_difficulty/model.py` into a neutral numeric module that both import. The import-linter contract that AD never writes evidence stays.
- The state is a DERIVED table, `lesson_weight_state`, plus its trace. Mastery replay is its one rebuild owner.

**Consistency with ratified rules.** The review found that learned evidence masses conflict with A2, field F2 and KM §9.1. For this family:
- **A2:** it is not in AD.
- **Field F2 and KM §9.1:** it writes no evidence row. It sets the mass of an existing attempt, at that attempt's time.
- **Drift with data:** masses are filtered as of each check, and the prior set is versioned, so a changed prior is a successor.
- **AD A5** ("no hand-picked evidence weights", wt:82) is the rule this decision satisfies.

**Logged from the first lesson.** `lesson_checks` and the receipt's `weight_inputs` (§8.3) hold, per check:
- the outcome;
- the tap and the hedge read;
- AD's prediction and the subject level;
- the teacher's forecasts;
- the mass applied;
- and later, the resolving cold outcome.

**Kill switch and monitoring.**
- **The switch is operational, not a statistical gate.** `teacher.weight.learned = false` uses the type's configured 0.5.
- **The report** (the LP report) shows:
  - prior→posterior contraction;
  - prior sensitivity, re-run with each prior mean shifted ±1 sd;
  - the prequential log-loss of the learned mass and of the fixed 0.5, side by side.

  Nothing switches on a margin. If the learned mass predicts worse, that shows in the posterior and in §12.2's mixture.

**Time to move off the prior** (§21).
- **The global term:** about 2–4 months at around 12 lessons a month.
- **Per-LO offsets:** stay near the global for a year or more. The hard shrinkage is deliberate.
- **The confidence term:** stays at its prior until the taps vary. **All of the owner's taps so far are 4 or 5** (29 of 70 attempts on linear_algebra).

Until then, the applied mass is close to the prior centre, which is revision 2's 0.5.

### 12.2 The forecast and the parametric mass, mixed by a learned weight (owner, 2026-10-24)

Revision 3 had a one-time switch after about 100 pairs, at a fixed 0.02-nat margin. **The owner ruled out fixed margins: the combination is learned and moves continuously.**

**The two predictors of the same cold outcome.** Both are made at the moment a node lands, for the committed cold item.
- `p_A`: the mastery prediction, with the lesson checks entered at §12.1's learned mass.
- `p_B`: the teacher's committed `lesson_step_retained` forecast. It is made from the trace, the confidence, hesitations and the history, and elicited without costs (B1).

**The rule chosen: Bayesian inference on a linear-pool weight.** This is AD's grid mechanism, applied to the pool weight.
- **The pool.** `p_λ = λ·p_B + (1 − λ)·p_A`, with λ ∈ [0, 1] on a grid of 21 points.
- **The update.** After each resolved cold outcome `y`, `W_t(λ) ∝ W_{t−1}(λ) · p_λ(y)`: the same update as AD's `ad_hyper` (`W_t(ξ) ∝ W_{t−1}(ξ)·Z_t(ξ)`, wt:492-527).
- **The applied value.** λ̂ is the posterior mean, as of each check.
- **Why this rule, and not the alternatives:**
  - *Plain model averaging over the two predictors* collapses to whichever predictor is better, even when a blend predicts best.
  - *Exponential weights or stacking* need a learning rate, which is another number to choose.
  - *Inference on the pool weight* keeps the blend when the blend predicts best. It has no tuning constant, it is deterministic and replayable, and it is the machinery AD already runs.
- **The seeded prior favours the parametric mass.** It is Beta(1, 4) over λ, discretized on the grid (mean 0.2, sd about 0.16).
  - **Basis `legacy`:** the owner's direction that the parametric weight starts ahead.
  - The width is wide enough that about 30–60 decisive outcomes move it.
- **The applied mass is the mass implied by the pool:** the `m` at which the mastery update makes predicted success on the committed cold item equal `p_λ̂`.
  - It is found by a one-dimensional search, and lies in (0, 1) by the same link.
  - At λ̂ = 0 it is exactly §12.1's mass.
- **A new teacher model or doctrine version** is a different forecaster, so it starts its own λ posterior from the seeded prior. The previous posterior is kept in the report.

**No activation step.** The pool ships inside TE1's successor, at its seeded prior.
- λ moving with the data is the same algorithm reading more data. Under LP §3.2 and the playbook, that is not a successor.
- The λ trajectory is written to `lesson_weight_trace`, so every applied mass is reproducible by replay.
- The kill switch `teacher.weight.source = pool | parametric` (default `pool`) is operational only.

**This is the planned path for retiring the parametric weight.** As models improve, `p_B` improves, and λ moves toward 1 by itself. There is no threshold and no switch.

**Time to move.** λ leaves its prior only where the two predictors disagree on outcomes.
- If the forecast is better by about 0.1 nats per outcome, λ̂ passes 0.5 within roughly 100 resolved pairs (3–4 months at the optimistic rate).
- If the two predictors are close, λ stays near its prior for years. That costs little, because they then agree.

---

## 13. Delayed cold and transfer checks

**One mechanism** (W13): DL2's Check once, the path RW1b's "reconstruct" already uses.

1. **At close, code picks the items, not the model.**
   - **Retention:** one per landed node that has an LO. A vault item of that LO that:
     - is unattempted;
     - has no reveal row from this lesson;
     - has never been served to a chat host (§16.2);
     - comes from a family the lesson didn't show.

     It is found through `find_practice` (intent `retention`, `unattempted_only`). That is RW6b's candidate rule.
   - **Transfer:** one per lesson. An item that applies a landed LO in a situation the lesson didn't use: either an item on the goal LO with a different presentation, or an item on a downstream LO whose rubric names a taught facet. It is found through `find_practice` (intent `practice`, with the lesson's families excluded).
2. **Commitment.** `create_commitment(action = "test_me_later", targets = [item], due_hint, provenance = {via: "lesson", lesson_id, node_id, purpose: "retention" | "transfer"})`.
   - **Dates come from retrievability, not day counts** (owner, 2026-10-24). A check is due on the first day the LO's predicted retrievability falls to the target `R*`. The prediction is FSRS's, with `S_eff` from liquid stability (`spec_learned_parameters_v1.md` §4.6), and a `lesson:<id>` reveal is one of its inputs.
     - **`R*` is a seeded prior:** 0.9, **basis `published`** (FSRS's default desired retention). RW6b's valuation replaces it when RW6b lands (step 6): it then dates each check by its EVSI, with no target constant.
     - **Seeded fallbacks, used only when the LO has no FSRS state yet:** 3 days for retention (basis `legacy`: RW6b's retention fallback) and 7 days for transfer (basis `legacy`: `capture.test_me_later_days`). Once the LO has state, the dates come from retrievability.
     - **`keep`:** nothing waits longer than 14 days (RW6b's `max_wait_days`). This is a guardrail so that a promised check is never silently dropped. It is not a model parameter.
   - **Logging.** The receipt logs the liquid-stability inputs from TE1 (`stability_inputs`, §8.3).
3. **No fitting item.** The receipt records it, and the existing need step may generate one, as an ordinary generated item. The teacher never authors its own delayed check.
4. **Serving.**
   - DL2 serves the check cold in Today: no source, hint or tutor (W7). Opening help makes it practice and re-dates it.
   - The answer is an ordinary attempt with full evidence and FSRS.
   - A transfer item on a downstream LO counts for the taught facet only through a criterion that visibly exercises it (KM §9.3).
5. **Undo.** The learner can drop a check, as with any commitment.
6. **When RW6b lands,** the lesson receipt becomes one of its session summaries. RW6b's valuation then chooses and dates the checks, and the lesson's own picker retires (one producer).
7. **Read back.** Results appear in the next brief (§8.1). They also resolve `lesson_step_retained` and the learned weight (§12.1–12.2), and any other qualifying cold attempt on the LO does the same.

---

## 14. Adaptive difficulty

### 14.1 What the teacher reads (read-only)

- **Readiness per brief node,** and predicted success for probe candidates. These come from `readiness.card_fields` / `lo_readiness` and `predict.score`, called through AD's own read-only `@entry` functions; each runs its own guarded operation.
- **When AD is off, below its tag, or denied,** the brief uses the active predictor and says which it used.
- **Subject level** enters through those predictions: `θ_G` sets where a new topic starts. There is no public API for `θ_G`, and v1 needs none.
- **Couplings.** When `learned_coupling` is adopted, coupled LOs join the brief's nodes as "tends to move with X for you". Couplings that are proposed but not adopted are not shown.
- **The band** is the house prior for pitching checks (§10, item 7). It is also the source of the close card's "practice now" offer, which AD's own band draw serves through the existing serve path.
- **The teacher never calls `generation.commission_point`,** because that call writes.

### 14.2 What the teacher feeds AD

**TE1, with no amendment.**
- AD never reads a lesson check, because its eligibility admits only `independent_attempt`, `open_text`, `diagnostic_probe` and `exam_attempt` (wt:503-512). A lesson check only closes the reading-dose windows of facets its minted item weighs on (wt:524). That is correct: the reading was followed by an answer.
- AD does read what follows: vault probes and the delayed checks, which are ordinary eligible attempts.

**TE3, an AD follow-up that needs the owner's amendment (Q5).** Add `lesson` as a §5.11 learning-opportunity kind:
- prediction-only, with its own learned dose curve and its own switch;
- subkinds by node outcome: `landed`, `taught`;
- a graded lesson check takes the kind's increment in place of γ, the same as the unwired in-passage path (wt:525, 712).

It needs:
- **an owner amendment** to A12 limit 1 and D20;
- **a migration** rebuilding the `ad_reading_opportunities` CHECK;
- **an AD successor,** for the version bump in `priors`;
- **code:** the `salience_firewall` allowlist, `View.reading`'s kind gate, and the report loops;
- **classification** of the lesson tables in `protected_tables` (`ROLES` and `COLUMNS`, and `READING` where a lesson cites a reading) and in `column_classes`.

Trigger: AD's own (wt:1722). Reading keeps its auto-flag clear through two consecutive reports, and the kind is logged with an LO mapping (TE1's receipts do this).

What it buys:
- **Serving.** AD knows a just-taught LO is easier, so the next serve lands in band.
- **Reporting.** AD's dose-and-burden report states what a lesson does to cold retrieval *for this learner*: a learned answer, not a hand constant. This replaces the learned-parameters spec's drift and `w_shift` ideas.

### 14.3 A8 compliance

- **No protected goals.** Goal resolution refuses protected material with the same predicate AD uses (`exam_material.py`).
- **Protected context.** Grounding uses `teaching_scope` with `exam_withheld`, and `read_history` filters through `withheld_items`.
- **Minted items** never carry protected provenance: that would move the protection epoch and reset adopted couplings.
- **Option B.** Once lessons are an AD kind, a lesson grounded in a reading that has withheld blocks is absent from AD's reading signals, as a reading is.
- **No new columns on protected tables.** v1 adds none, so AD23's column classification is untouched.

---

## 15. Router amendments (to be recorded in `spec_action_router_v1.md`)

This section is the amendment text. The router spec itself is not edited here.

### 15.1 The router suggests lessons; the learner opts in (owner, 2026-10-24)

> "Lessons should be suggested and prompted through the action router, and opted into/selected for by the user, so this information can be used to inform the action router later downstream."

- **A new reversible candidate subtype, `instruct(lesson)`.** At a block boundary, the planner may propose a lesson on target LOs:
  - new LOs on the learner's goals;
  - LOs whose cold checks keep failing after practice;
  - LOs where AD predicts success well below the band.

  Declining costs nothing, so the candidate is reversible. It joins the `mixture` draw with an exact logged propensity (router §7.3), or `epsilon_tiebreak` in `staged` mode.
- **What the learner sees.** One card in Today: "Learn *X* now? (about 15 min)", with the target in plain words and the reason (router §7.4's honest "why"). The learner can:
  - **start** it;
  - **pick an alternative:** one of up to two other `instruct(lesson)` candidates from the same decision, shown on the card;
  - press **"Not now"**;
  - or do nothing.

  "Teach me X" stays available everywhere, and is logged as `learner_pick` with no propensity.
- **Logging.**
  - Every shown suggestion is a `router_decisions` row (candidate set, design, seed, propensity, card hash).
  - The learner's response is a new outcome on that decision: `accepted`, `chose_alternative:<candidate>`, `declined` ("Not now"), or `ignored` (no response by the end of the session). It is also a preference line on the card ("not now on *X*, Oct 24").
  - An accepted lesson stores the decision id (§7 step 1; receipt `origin`). Its delayed checks then fall into that decision's `R_cold` window, so lesson outcomes flow back to the router.
- **How often suggestions come, and how long a "Not now" lasts, are learned** (owner, 2026-10-24).
  - **The acceptance model.** `P(accept | context)` is a logistic model with latent effects, updated by the same assumed-density step as §12.1 from every shown suggestion's response. Its inputs:
    - time of day, minutes left, and re-entry;
    - the LO's status;
    - days since the last suggestion;
    - for a goal the learner declined, `log(1 + days since the "Not now")`, with a per-learner recovery rate that is a grid posterior. Re-acceptance after a decline is what teaches this term.
  - **How it gates suggestions.** The `instruct(lesson)` candidate's value includes `log P(accept)`, so suggestions come as often as they are predicted to be taken. There is no per-day quota, and no fixed mute length.
  - **Seeded priors** (basis `legacy`: revision 3's defaults, width 1 logit on each effect):
    - the intercept and the days-since-last term reproduce about one suggestion a day when there is no data;
    - the recovery rate reproduces about a 7-day mute after a "Not now".
  - **`keep`, a guardrail against nagging:**
    - a hard ceiling, `router.lesson_suggestions.ceiling_per_day` = 3. It is never learned, and each bind is logged: a ceiling that binds often means the acceptance model is wrong;
    - suggestions are only a Today card: never a modal or a notification, and never during a cold check.
- **What the router can learn, and when.**
  - **Acceptance by context** (time of day, minutes left, re-entry, LO status, the reason given) is fast. Each shown suggestion is one observation, about 30 a month at the seeded rate. A coarse acceptance rate comes within weeks. Context effects of about ±20 points need a few hundred suggestions, so many months.
  - **Lesson value on `R_cold`** is slow. The suggestion policy is evaluated intention-to-treat (suggested or not, by propensity) on `R_cold`.
    - A first doubly-robust estimate comes at the router's 200-decision report.
    - A policy switch waits for the 600-decision rule (router §10.4).
    - The effect among those who accepted is confounded by self-selection and is never claimed.
- **Successor.** This changes what Today shows, so it is a router successor with the kill switch `router.lesson_suggestions.enabled` (below the tag, or off, no suggestion appears). It may share TE1's tag if they merge together. Phase TE1b.

### 15.2 Confidence on the learner card (owner, 2026-10-24; TE0)

- **What goes on the card.** The card (`router/card.py:88`; `CARD_VERSION` moves from `learner_state_card_v1` to `_v2`) renders confidence as events, never as raw scalars.
  - **Recent work:** each attempt line gains its confidence event in words, for example "marked 5/5 sure; wrong", "no tap; the grader read the answer as hedged", or "marked 2/5; right".
  - **Interaction signals** (the card's existing 7-day window), per candidate LO: the confidence events themselves, each tap or hedge read with its outcome. There are no threshold counts: the reading models decide what counts as confident.
  - **A stated limit:** "your taps so far are all 4–5" whenever the taps have no spread.
- **Where else it goes.** The same rendering goes into the diagnoser, hint-writer, tutor and teacher contexts. Never to the grader (blind-split S1).
- **Persisted meaning.** The card version is recorded on every decision. The change alters model inputs, not persisted meaning. **Decided (default, 2026-10-24):** no successor, since the card's content already changes daily, unless the playbook review at implementation finds persisted meaning.

### 15.3 Deferred: a within-session fatigue time constant

Accuracy decay within a session, by minutes on task, error streak and time of day, would inform the router's `burden_or_fatigue_cap` stop. It is deferred in `spec_learned_parameters_v1.md` §9. Trigger: ≥600 logged router decisions and ≥60 sessions of ≥10 attempts.

---

## 16. MCP and chat

**One contract, two drivers.**
- In chat, the host model is the teacher, and LearnLoop is the state, grounding, grading, evidence and scheduling.
- LearnLoop's own teacher model does not run, so there are never two tutors (`spec_mcp_frontend_v1.md:449`).

| Stage | What chat lessons can do | Needs |
|---|---|---|
| **TE4a** | A read-only `teaching_guide`: the doctrine's chat edition and a read-only brief for named LOs (`learning_context` plus sections plus readiness). No writes beyond C1a's telemetry and exposure | C1a (landed) |
| **TE4b** | `lesson_open` and `close` write lesson rows and **delayed checks served in the app**. Learner text goes to the gap pipeline as `external_chat` (`note_question`) | C1b: PR-5 request origin (`entry_surface`), PR-7 desktop freshness (Today changes) |
| **TE4c** | `pose_check` and `submit_check`: lesson-check attempts, blind-graded by LearnLoop. Also `serve_check` and `submit_answer`: chat cold checks and chat probes at a learned weight (§16.2) | C2's chat-integrity successor, plus §16.2's requirements |

### 16.1 What C2's integrity rules imply for a chat lesson
- **Lesson checks** are recorded as `reconstruction_after_walkthrough` with `assistance_observability = host_unobserved` and evidence origin `chat_relay`.
  - They are already assisted, so labelling them unobserved costs nothing.
  - Their mass is §12.1's learned weight plus a chat offset term, learned from the same in-app cold outcomes.
  - The offset's seeded prior is N(−0.5, 0.5²) on the logit scale. **Basis `legacy`:** the owner's direction that chat counts for less, with no chat data yet. The width lets the data remove or double the offset.
  - They are graded only by LearnLoop's blind grader, never through MCP sampling.
  - The host's committed solution must reach LearnLoop before it returns a check id. LearnLoop can't see what the host displayed, which is one more reason the attempt can never be cold.
- **The item's origin.** The minted item's origin needs a host value from C2's successor. `codex_proposal` is wrong for a host.
- **What stays in the app.** Calibration sittings, certification cold probes, repair cold retries, golden-path assessments and anything exam or held-out are never chat-eligible. Cold checks and probes may run in chat only on §16.2's terms (owner, 2026-10-24); otherwise they are served in the app ("a quick check is waiting in the app").
- **Reveal accounting.** The rows are C2's kinds (`host_reported`, `solution_request`), for items whose stem or answer LearnLoop returned to the host. Host-written text is an unknown exposure channel, so delayed checks after a chat lesson never use an item LearnLoop returned to the host.
- **What the host cannot claim.** It cannot assert a cold reading, a human origin, a grade or a propensity (V:443).
- **The chat brief is narrowed** like `learning_context`: structure, authored vault text and the learner's own answers. It carries no diagnosis prose while the switch is off, and it returns the minimum the host needs (R2 / D16).
- **The doctrine's chat edition** is returned by `lesson_open`. It is our own public text, and its version is recorded on the receipt (Q9).

### 16.2 Cold checks and probes in chat (owner, 2026-10-24; behind C2)

- **The mechanism.**
  - `serve_check` returns the item's text (stem and choices) only, never the key, rubric, hints or solution.
  - `submit_answer(served_id, answer_text)` carries the learner's answer verbatim.
  - LearnLoop grades blind on the server, and then returns the verdict and feedback. The key is allowed after submission (V:395).
- **What can be served.**
  - **Due Check once commitments** (delayed checks), always on a **fresh unseen item**. The committed in-app item stays unexposed (Q18).
  - **Vault-item probes** for a chat lesson's placement.

  This amends C2's eligibility class for these two kinds only. Every exclusion in §16.1 stands.
- **The integrity class.** C2's: `assistance_observability = host_unobserved` and evidence origin `chat_relay`. The attempt never counts as a cold reading for certification, held-out validation or repair verification, and it **never certifies on its own** until C2's successor says otherwise.
- **The evidence weight is learned,** with the same machinery as §12.1, as its own family:
  - `m_chat = σ(η_chat₀ + κ·[probe] + β_t·z_t + u_L)`, where `z_t` is the response time relative to the learner's own in-app distribution for similar items. That replaces a fixed "implausibly fast" threshold;
  - seeded priors:
    - `η_chat₀` ~ N(logit 0.6, 1.0²), so the mass is centred **below an in-app cold check** (95% interval about 0.17–0.92). **Basis `legacy`:** the owner's "below in-app" direction; no chat data exists yet;
    - `κ` ~ N(0, 0.5²) and `β_t` ~ N(0, 0.5²), with centre "no effect" and **width basis `simulation`**;
    - `u_L` shares §12.1's grid posterior;
  - it is learned **only from later in-app qualifying cold outcomes** on unseen items of the same LO, never from other chat attempts;
  - whether it also updates FSRS is C2's decision.
- **Exposed to the host.**
  - Every item whose text LearnLoop serves to a chat host gets an exposure mark: C2's `host_reported` reveal row, at amount 1.0.
  - Such an item is never afterwards an in-app cold check, a delayed-check candidate (§13) or a qualifying outcome for §12.1.
- **What C2's integrity successor must provide for this:**
  1. **The answerer's identity.** The answer is the learner's, not the host's. The preferred route is an answer surface the learner types into, whose text LearnLoop receives directly (V's open "widget vs chat relay" decision). The minimum is a per-answer learner attestation. A host-composed answer is labelled as such.
  2. **No host assistance.** The host is told, in the server instructions and in the `serve_check` result, to show the text unmodified and give no help before submission.
     - While a chat check is open, LearnLoop refuses `find_sources` and `learning_context` for its LO.
     - Host help outside LearnLoop can't be observed. That is why the weight is learned, with a lower prior.
  3. **Verbatim relay.** The submitted text is the learner's exact words. The record states how it arrived (`relay = answer_surface | host_args`).
  4. **Timing.** Served-at and submitted-at come from LearnLoop's own clock, and response time is an input to the learned weight (above).
     - **`keep`:** an open check expires after `chat_check.max_minutes`. This is an operational integrity bound, so that a check left open in a chat can't be answered hours later with help. It is not a model parameter.

**In short, a chat lesson may write:**
- lesson rows and receipts;
- exposure for the passages LearnLoop returned;
- C2's reveal kinds and exposure-to-host marks;
- `external_chat` gaps;
- delayed-check commitments;
- after C2:
  - assisted lesson-check attempts;
  - chat cold checks and chat probes, at the learned chat weight.

**It never writes:**
- certifying evidence;
- a cold reading that qualifies for certification or for §12.1;
- calibration;
- anything that touches exam material.

---

## 17. Transport and cost (T1 redesign D)

- **The task.**
  - Add `teacher` to `AITask` (`ai/routing.py:33`) and to the routing config.
  - Its default serving route starts at `chatgpt_medium` (`keep`: an operational route choice) until a dry-run comparison on a fixtures-local copy picks the tier.
- **One lesson is one origin action.**
  - Every model-calling lesson step goes through one sidecar method, `lesson.turn`. Open, learner replies, check submissions and close are its actions.
  - Grants are keyed by vault and origin method (`plan_fallback.py:418`), so one "Use OpenRouter instead" covers the whole lesson for the session, and "Not now" mutes it.
- **Grading a lesson check** runs inline inside `lesson.turn`, so the same grant covers it.
- **Spawned background work** (text-gap judging, delayed-check generation needs) captures `unit_token()` and `unit_origin()` at creation. The teacher never uses `inherit_grant` (AST pin).
- **Price.** Add `"teacher": "teacher.metered_price_per_million"` to `METERED_PRICE_SETTINGS`. Without it, an unlisted task is offered with no price gate (`offer_blocker`, `:126`), and the per-lesson cap couldn't be computed.
- **The per-lesson cap.** `teacher.budget` is built on `ai/spend.SpendBudget` (`SpendCaps.max_estimated_usd`). When it is exceeded, the lesson closes with `budget`. The default is set from one measured dry-run lesson (Q7). T1 adds no cap of its own.
- **Cost shape.** About 15–25 turns per lesson. Each turn's input is:
  - the doctrine (~4k tokens);
  - the brief (~6–12k);
  - the sections (typically ≤10k, whole source ≤40k);
  - the transcript.

  The prompt is ordered doctrine → brief → sources → transcript, for caching. That makes roughly 0.3–1M input tokens per lesson. On the plan this costs rate-limit headroom, not money.
- **Outages and restarts.**
  - Lesson state is durable (`lesson_turns`), so a lesson resumes after the plan returns or after the yes.
  - A sidecar restart loses the in-memory grant, and the next turn asks again.

---

## 18. Persistence and successor

### 18.1 New tables

| Table | Role | Contents |
|---|---|---|
| `lessons` | RAW_LEDGER | Id, driver, goal, LO ids, doctrine version, model and route, opened and closed, close reason |
| `lesson_turns` | RAW_LEDGER | Sequence, actor (teacher, learner or code), action, validation result, refs (attempt, item, commitment, gap), payload hash |
| `lesson_turn_payloads` | WORKFLOW, with retention | Raw model and learner text, as `router_decision_payloads` does |
| `lesson_plans` | RAW_LEDGER | Versioned outlines |
| `lesson_checks` | RECEIPT | `attempt_id`, `lesson_id`, `node_id`, `minted_item_id`, forecast keys, and the weight inputs (tap, hedge, AD prediction and subject level, mass applied) |
| `lesson_receipts` | RECEIPT | §8.3 |
| `lesson_weight_state`, `lesson_weight_trace` | DERIVED (rebuild owner: mastery replay) | §12.1's posterior and per-update trace, plus TE4c's chat family |
| `confidence_calibration_state` | DERIVED (same owner) | LP-min's tap/hedge → probability recalibration |
| `router_suggestion_responses` | RAW_LEDGER | Decision id, response (`accepted`, `chose_alternative`, `declined`, `ignored`), time, the lesson id when one was accepted (§15.1) |

### 18.2 Existing tables and settings

- **Practice items:** vault YAML, with `origin = codex_proposal` and a lesson hold reason.
- **`practice_attempts`:** existing type, no new column.
- **`reveal_events`:** existing kinds.
- **`help_assists`:** existing surface.
- **`commitments`:** existing action.
- **`forecast_receipts` (TE1):** `FORECAST_KINDS` gains `lesson_check_correct` and `lesson_step_retained`, with their binding kinds.
- **TE2:**
  - `learner_text_gaps` gets a CHECK rebuild adding `lesson`, together with C1b's `external_chat`, so C1b needs no rebuild of its own;
  - goal LOs use `mechanism = teacher_goal_v1`.
- **Config:**
  - a `teacher.*` section, with switches `teacher.enabled`, `teacher.weight.learned`, `teacher.weight.source`, `teacher.placement.*` and `teacher.delayed.*`;
  - `router.lesson_suggestions.*` (§15.1).

### 18.3 Successor

- **TE1 is one successor**, the next free tag at merge after mvp-0.30. It changes:
  - which new attempts are primed (lesson reveal rows), under the playbook's mvp-0.27 rule;
  - what is served (lesson holds, delayed checks);
  - how mastery moves on lesson checks (the learned weight and the tap/hedge recalibration, with priors in `lp_priors_v1`).

  Its kill switches:
  - `teacher.enabled`: below the tag, or with it off, no lesson can open;
  - `teacher.weight.learned`: off means the fixed 0.5.

  Replay:
  - lesson rows are RAW_LEDGER or RECEIPT and are never cleared;
  - attempts replay as existing types;
  - the weight state is DERIVED, rebuilt as of each check.

  Rebuild equivalence is tested on a lesson fixture.
- **TE1b** (router suggestions, §15.1) is a router successor. It may share TE1's tag.
- **The forecast–parametric pool** (§12.2) ships inside TE1's successor at its seeded prior. λ moving with the data is not a successor (LP §3.2), and every applied value is in `lesson_weight_trace`.
- **LP-min's four claim fixes** are their own small successor after AD23. The optional liquid-stability family is a successor at activation (`spec_learned_parameters_v1.md` §4.6).
- **TE2** is decided under the playbook at implementation. If it merges with TE1, it shares TE1's tag.
- **TE3** is an AD successor.
- **TE4c** rides C2's successor, which also needs the chat weight family and the exposure-to-host mark.

### 18.4 Every number: a seeded prior, a structural form, or `keep` (owner, 2026-10-24)

**Seeded priors.** These are learned; the data move them. `prior_basis` takes the values `population`, `published`, `llm_content`, `claim`, `simulation` or `legacy`.

| Quantity | Seed | Basis and width |
|---|---|---|
| Lesson-check mass, `η₀` (§12.1) | logit 0 (mass 0.5) | `legacy` (`config/schema.py:1619`); 1.0 logit |
| Per-LO offset scale τ | Grid {0.1, 0.2, 0.4}, uniform weights | `simulation` (planted recovery); the weights are learned |
| Confidence and AD-prediction effects `β_c`, `β_p` | 0 ("no effect") | `simulation`; 0.5 logit |
| Chat lesson-check offset (§16.1) | −0.5 logit | `legacy` (owner: chat counts for less); 0.5 logit |
| Chat check mass `η_chat₀` (§16.2) | logit 0.6 | `legacy` (owner: below in-app); 1.0 logit |
| Chat probe and timing terms `κ`, `β_t` | 0 | `simulation`; 0.5 logit |
| Pool weight λ (§12.2) | Beta(1, 4) | `legacy` (owner: parametric first); sd about 0.16 |
| Tap/hedge → probability (LP-min) | Today's map {1: .10 … 5: .90} | `legacy` (`goals/exam_calibration.py:30`); ≥1 logit on slope and intercept. `population` (Eedi) only after a licence check |
| Liquid-stability `w` (LP §4.6) | 0, which is plain FSRS | Centre `published` (FSRS); its width is a grid posterior with support from `simulation` |
| Retrievability target `R*` (§13) | 0.9 | `published` (FSRS default); replaced by RW6b's valuation |
| Delayed-check fallback dates (§13) | 3 days and 7 days | `legacy` (RW6b's fallback; `capture.test_me_later_days`). Used only while the LO has no FSRS state |
| Router acceptance model (§15.1) | About one a day, and about a 7-day recovery after "Not now" | `legacy` (revision 3's defaults); 1.0 logit per effect, with the recovery rate on a grid |
| Check pitch (§10 item 7) | 70–80% | AD's owner-decided band. A prior in the doctrine, not a code constant |

**Structural, in the functional form:**
- **Lesson-check and chat masses < 1:** the logistic link (revision 3's Q13).
- **The pool-implied mass:** in (0, 1), by the same link.
- **`w = 0` ⇒ plain FSRS:** the exp form.
- **Exposure to host at amount 1.0:** by definition, the whole item text was shown.
- **The 21-point λ grid and AD's quadrature nodes:** numerical resolution, not modelling choices.

**`keep`.** Each stays fixed, for the reason given.

| Setting | Why it stays fixed |
|---|---|
| `teacher.context.sources_tokens` (24k), `teacher.brief.depth` (2), `teacher.context.compact_at` | Context budgets: cost and latency, not a model of the learner |
| `teacher.placement.max_probes` (8) | Burden guardrail. The model decides when to stop; this only bounds it |
| `teacher.placement.calibration_p` (1.0) | A design probability, logged as the propensity |
| Three consecutive contract failures close the lesson | Contract guardrail |
| `teacher.budget` (per lesson, set from a dry run) | Spend |
| `max_wait_days` (14, RW6b) | A promised check is never dropped silently |
| `router.lesson_suggestions.ceiling_per_day` (3); card only, never a modal, never during a cold check | Anti-nagging guardrail. Binds are logged |
| `chat_check.max_minutes` | Integrity expiry |
| Up to two alternatives on the suggestion card | Presentation |
| One goal LO over the daily creation cap (TQ5a) | A guardrail on vault growth, on top of the existing cap (`config/schema.py:2561`) |

**Existing values reused, not new.** They are registered under LP0 and unchanged here:
- the auto-prime reveal sum 0.35 (`serve_eligibility.py:81`), which withdraws a check;
- `capture.test_me_later_days` (7);
- the router card's 7-day window;
- the other attempt types' evidence masses. They are not learned, because LP3 is dropped.

---

## 19. UI

**Lesson screen** (Tauri):
- document typography, not chat bubbles;
- learner input as interjection cards;
- a persistent plan map showing current, visited and upcoming nodes (position, not completion);
- predictions arrive open; checks stay collapsed until the learner opens them.

**Each check has:**
- the confidence tap, shown after a draft exists, as in practice;
- an optional "your thinking" field. It goes to the teacher, never to the grader, which sees only the answer (W8).

**Entry points:**
- "Teach me this" on an LO page, on a Reader selection, and on new-topic offers in Today;
- the router's suggestion card in Today (TE1b, §15.1): "Learn *X* now? (about 15 min)", with Start, up to two alternatives, and "Not now". At most one a day, and never a modal or a notification;
- "Check what I already know first" at open.

**The close card:**
- a short recap;
- "I'll check *X* and *Y* cold in a few days", promising only checks that were actually committed (W2);
- an offer to practise now, served by AD's band draw.

**Defaults:**
- Plan outage shows T1's standard offer.
- No jargon in learner copy.
- Forecasts, receipts and routes appear only in an inspector overlay.

---

## 20. Phases

| Phase | Contents | When | Persisted meaning |
|---|---|---|---|
| **TE0** | `answer_confidence` and the hedge read, rendered as events, passed into the diagnoser, hint-writer and tutor contexts, and onto the router card (`learner_state_card_v2`, §15.2) | Track P, a small item right after T1 lands | None (context and card only) |
| **LP-min claim fixes** | The four claim-defect fixes (`spec_learned_parameters_v1.md` §0a) | Right after AD23 lands | Own small successor |
| **TE1: the first good lesson** | Listed below | After T1 and AD23 land; in parallel with S0 → mobile PR-1..7 | One successor (§18.3) |
| **TE1b: router suggestions** | `instruct(lesson)` candidates, the Today card, response logging, caps and mutes (§15.1) | With TE1, or right after it | Router successor (may share TE1's tag) |
| **TE2** | Vault probes and the calibration probe; typed goals and `create_goal_lo`; `propose_gap` and detours; resume; `learnloop teacher report`, including the §12.2 pool weight's trajectory | After TE1 has run real lessons | Per the playbook |
| **TE3** | AD's `lesson` opportunity kind (§14.2) | AD follow-up, on AD's trigger, with Q5 | AD successor |
| **TE4a–c** | Chat lessons (§16). TE4c includes chat cold checks and probes (§16.2) | With C1a, C1b and C2 respectively | C2's successor for TE4c |
| **Liquid stability** (optional) | `S_eff = S_fsrs·exp(wᵀu)`, with the prior width of `w` itself a grid posterior (`spec_learned_parameters_v1.md` §4.6). Its inputs are logged from TE1 | When built: there is no review-count threshold and no keep margin. With few reviews it stays at plain FSRS | Successor when the family is introduced. `w` moving afterwards is data, not a successor |

**TE1 contents:**
- `teacher/` and `lesson.turn`;
- the `teacher` AITask and its price setting;
- doctrine v1;
- `LessonBriefV1` with AD readiness, `last_lessons` and whole sections;
- `TeacherTurnV1`;
- the actions `read_source`, `find_sources`, `find_practice`, `read_history`, `write_plan`, `pose_prediction`, `pose_check` and `close`;
- the output guards;
- minted held check items, recorded as `reconstruction_after_walkthrough` with `lesson_checks` rows;
- the learned lesson-check weight and the tap/hedge recalibration (§12.1; LP-min), with their DERIVED state and report lines;
- the two forecast kinds, and the `weight_inputs` and `stability_inputs` logs;
- reveal rows;
- delayed retention and transfer checks;
- the receipt;
- the lesson screen, and the quick-check button.

**Gate:**
- targeted tests while iterating, with `StructuredClientFake` and no model calls;
- the full suite once, at landing;
- one real lesson on a `fixtures-local` copy.

---

## 21. Measurement

**Data reality.** One owner-learner:
- about 70 graded attempts, lifetime, on the main vault copy;
- none between Sep 7 and Oct 19;
- working vaults at mvp-0.8.

**Nothing in this spec waits for significance.** Each lesson is useful when it happens, and each delayed check is useful when it is answered: it is a spaced retrieval for the learner, and its result shapes the next lesson. Everything else is a log kept for a future volume.

For each learned quantity, the last column is its time to move off its seeded prior at the owner's rate. For the rest, it is the time to signal.

| What | Available | Time to move off the prior, or to signal |
|---|---|---|
| In-lesson check outcomes | Immediately | Steering only. Never reported as learning |
| Each delayed retention or transfer result | 3–14 days after each lesson | None needed: read individually by the learner, the next brief, mastery and FSRS |
| Retention and transfer rates after lessons | From the first checks, as descriptive counts | ±0.15 (95%) needs about 40 checks: 10 lessons × 4 nodes, one to three months at an optimistic 12 lessons a month. Never, at zero lessons |
| **Learned lesson-check weight, global term** (§12.1) | From TE1, as cold checks resolve | About 30 resolving pairs a month at an optimistic 12 lessons a month (4 checks each, ~60% resolving). Each pair says little about `η`, so the term visibly contracts after about 60–120 pairs: **2–4 months**. Until then the mass stays near 0.5 |
| Learned weight, per-LO offsets | Same | 1–3 pairs per LO a month over 20–35 LOs, so they **stay near the global for a year or more** (hard shrinkage, by design) |
| Learned weight, confidence term | Same | **Stays at its prior until the taps vary.** All of the owner's taps so far are 4–5. The hedge read may give spread sooner |
| Learned weight, AD-prediction term | Same | Needs spread in the pre-check predictions: several months |
| Tap/hedge recalibration (LP-min) | Every tapped graded attempt, not only lesson checks | Faster than the weight, but limited by the same lack of spread in the taps |
| **Pool weight λ: forecast vs parametric** (§12.2) | From TE1 | It moves only where the two disagree on outcomes. With a forecast better by about 0.1 nats per outcome, λ̂ passes 0.5 in roughly 100 resolved pairs (3–4 months, optimistic). With a smaller gap it stays near its seeded 0.2 for years, which costs little because the two then agree |
| Chat cold-check and probe weight (§16.2) | After C2 | Needs chat checks followed by in-app cold checks on the same LO. **The slowest:** months to a year after C2, depending on chat use |
| Router: lesson value on `R_cold` (§15.1) | From TE1b | First DR estimate at 200 decisions; a switch waits for 600 (router §10.4). Acceptance effects are confounded and never claimed |
| Liquid stability `w` and its prior width (LP §4.6) | From its first review, once built | It stays at plain FSRS until reviews show an effect. Reviews are the densest outcome, but the owner has about 70 attempts in total and few eligible review pairs: months after real use resumes |
| Router acceptance model and decline recovery (§15.1) | From TE1b | The intercept moves within weeks (about 30 suggestions a month). Context effects and the decline-recovery rate need a few hundred responses and several re-acceptances after a "Not now": many months, during which the seeded one-a-day / 7-day behaviour holds |
| Retrievability target `R*` (§13) | Until RW6b | Seeded at 0.9; replaced by RW6b's valuation, not learned on its own |
| Chat timing term `β_t` and probe term `κ` (§16.2) | After C2 | Slowest of all, as the chat weight |
| What a lesson does to cold retrieval (AD dose report, TE3) | After TE3 | Prior-dominated until tens of lesson→check pairs. AD reports its interval and auto-flags |
| Placement accuracy (the calibration probe) | One per placement | Descriptive only |
| Variant comparisons: doctrine A/B, chat vs desktop, lesson vs reading | Not randomized in v1 | About 150 per arm: years. Deferred (§22). Observational comparisons are confounded and are never claimed |
| "LLM history-reading vs numbers" | Already logged by AD1 (`item_forecast_scores`: `llm_v3:*` vs `ad_threshold@*`, `mastery_ekf`) | Accrues with all attempts; no teacher code needed |

**Prerequisite:** the working vaults must be upgraded past mvp-0.8 before any of this exists for the owner (Q12).

---

## 22. Deferred, with triggers

The thresholds in these triggers are `keep`. They decide when to spend engineering effort, and they are never parameters of the learner model.

| Item | Trigger |
|---|---|
| Router sensor mode and its H0/H1/S/C arms | Moved to the router spec. Trigger: ≥600 logged router decisions (router §10.4). H1 waits on the learned-parameters decision |
| A within-session fatigue time constant for `burden_or_fatigue_cap` (§15.3) | ≥600 logged router decisions and ≥60 sessions of ≥10 attempts (`spec_learned_parameters_v1.md` §9) |
| Doctrine A/B and other randomized teaching arms (a seventh randomization design, or a reuse of `mrt_reversible`) | ≥150 resolved delayed checks per arm reachable within 6 months (about ≥25 lessons a month for a quarter) |
| Sensor rendering (track records, percentiles), the `learner_surprise` column, `tap_shown` | A consumer exists, and ≥200 tapped attempts with ≥20% of taps ≤ 3. (Confidence as events on the card and in model contexts is not deferred: it is TE0) |
| Lesson-check items joining the practice pool | The delayed-check picker finds no unseen-family item for >30% of landed nodes over a month |
| Split diagnoser on lesson checks | Lesson misconceptions recur on delayed checks without a gap proposal |
| Teacher-built demos with headless verification | Lessons asking for a dynamic demo the figure and animation routes can't express. *Superseded (2026-10-25): built as RW5d's sketch tier (`spec_reader_show_me_figures_v1.md` §9, phase P2) on the owner's direction, not on this trigger; lessons reach it through `visual`* |
| A background fact-check research agent | Citation validation rejects >10% of source claims, or the owner asks |
| Multi-session curricula | Three resumed lessons on one goal |
| Change-point variance after lessons (sweep §1.2.5) | Subsumed by TE3. Revisit if the field harness shows post-lesson first attempts miscalibrated |

---

## 23. Owner decisions (all decided 2026-10-24)

The owner, 2026-10-24: "yes to defaults for all other open questions". Every question that revisions 2 and 3 raised is decided below, and **none remains open**. Two need the owner to *act*, not to decide: Q7's dry run and Q12's vault upgrade.

1. **Lesson-check weight.** `reconstruction_after_walkthrough`, never certifying and never counting as a Check once. Its mass is learned from later cold checks only (§12.1), mixed with the teacher's forecast by a learned pool weight (§12.2). This settles TQ1a.
2. **Questions the teacher writes before teaching a step** count at the learned lesson-check weight. Probes using existing vault questions count fully. This narrows TQ4.
3. **Who starts lessons.** The router suggests, the learner opts in, and "Teach me X" is available everywhere. Suggestions and responses are logged (§15.1).
4. **After each lesson,** one cold check per landed topic and one transfer check, both through Check once, on questions the lesson never showed. The dates come from retrievability, with 3 and 7 days only as seeded fallbacks (§13). When RW6b lands, its valuation takes over.
5. **The AD amendment** adding "lesson" as a learning-opportunity kind is approved in principle. It is built when AD's own trigger fires (§14.2), and recorded in the AD spec then.
6. **Router sensor mode (TQ7)** moves to the router spec, deferred until about 600 logged router decisions.
7. **Plan outage.** Lessons get the usual "Use OpenRouter instead" offer. No offer is made until `teacher.metered_price_per_million` is set. The per-lesson cap is `keep` (spend), and is set from one measured dry run: **an owner action.**
8. **Chat lessons.** The chat model is the teacher; LearnLoop supplies state, sources, grading and scheduling. Cold checks and probes may run in chat behind C2, at a learned weight below the in-app one. An item served to a chat host is never an in-app cold check afterwards (§16).
9. **The doctrine's chat edition** (our own public text) is sent to the chat model.
10. **Teacher-written questions** stay inside their lesson in v1. Revisit on §22's trigger.
11. **A typed goal with no matching topic** creates one, one over the daily cap, even without a source. It is labelled "from LearnLoop's model", with a library lookup offered first (TQ5a).
12. **The working vaults** are upgraded past mvp-0.8 before the first real lesson: **an owner action.**

**Revision 3's questions, as revision 4 decides them:**

13. **The cap at 1.0** is not a constant. It is a property of the logistic link (§12.1).
14. **The forecast switch margin** is gone. A learned pool weight replaces it (§12.2).
15. **The chat cold-check weight** has a seeded prior: mass 0.6, basis `legacy`, 1.0 logit wide, learned from later in-app cold checks (§16.2).
16. **Suggestion frequency and mute length** are learned from the learner's responses. One a day and a 7-day mute are only the seeded starting point, under a `keep` ceiling of 3 a day (§15.1).
17. **The tap/hedge recalibration** starts from today's fixed map as a wide `legacy` prior. Eedi's confidence data is used only after a licence and scale check.
18. **A delayed check answered in chat on a fresh item settles the commitment.** The reserved in-app item is released unused.
19. **The liquid-stability keep margin** is gone. The prior width of `w` is a grid posterior, with no review-count threshold (`spec_learned_parameters_v1.md` §4.6).
