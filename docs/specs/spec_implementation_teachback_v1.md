# Work questions: implementation teach-back (WQ)

**Status:** queued (owner, 2026-11-20). After the refactor and UX stages: evidence packets → AD memory → reveal adjudication → WQ teach-back → projects-as-goal → notebook activities → teacher v2 (TE5 to TE10). WQ0 runs beside the queue; WQ1 lands with the UX overhaul; WQ2 waits for NA2, and for NA5 on coding surfaces (§4). §12 records the decisions and the feedback-arm rate owed by the owner. Nothing here is built.

**Source:** the owner's request of Nov 20:

> "In marimo notebooks could we also have a teachback when the model asks the learner a question about something they are implementing? This could also be a broader feature within learnloop such as in the reader workbench if not existing already."

Read with `docs/specs/spec_notebook_activities_v1.md` (NA) §6, §9, §12.4 and §14, and `docs/brainstorming/Active Formats Brainstorm 2026-11-18.md` §1, §7, §8 and §19. The evidence is there; this spec holds what to build.

## 1. The problem

1. **Nothing asks about the learner's own work while they do it, and records the answer.** §1.1 lists what exists. The one built feature that asks about a learner's own artifact, project probes, is delayed by a week, is about agent-written code and sits outside learner state.
2. **Passing code and a valid derivation can be copied, memorised or pattern-matched.** The brainstorm's coding review (§7) says "teach-back level" holds only for a success, and proposes one generated "why this line?" follow-up.
3. **Three specs originally proposed the same thing:** NA §6.2's `ll.explain(after=)`, NA §9.3's "why this change?" one-liner after kept edits, and two deferred hint kinds, learner-written subgoal labels and "bottom-out plus self-explanation" (`spec_adaptive_hints_v1.md:698-699`). Decided (owner, 2026-11-20): fold them into one work-question service (NA §12.4, WQ5), so they do not become three more silos.

**Evidence, briefly** (brainstorm §8): self-explanation g = 0.55 (Bisra 2018); proof self-explanation training d = 0.95 (Hodds, Alcock & Inglis 2014); Lead-and-Reveal, which asks for the step in words before code, was the strongest AI-coding design tested (Kazemitabaar 2025); learner-written subgoal labels are among the best labels (Morrison, Margulieux 2020). **Against:** unsolicited help at random times cost low-prior learners time (Cody et al. 2022, `spec_reader_workbench_v1.md:479`); on-demand hints beat hints on every error (Razzaq & Heffernan 2010); being watched roughly halved interview performance (Behroozi 2020); Trace-and-Predict took 2.66× the time for no significant gain. So when to ask is a priced, randomized decision, not a habit.

### 1.1 What exists

| Feature | Where | About the learner's own in-progress work? | Answer recorded? |
|---|---|---|---|
| Teach-back conversation: the learner explains, a naive student asks rubric-planned follow-ups, the transcript is graded blind as one attempt | `tutor/teach_back.py:1-29`; planner `:244`; question `:375`; "# Teach-back transcript" `:476`; finish `:504`; `criterion_teach_{i}` `:1241`; prompt `tutor/ai_contracts.py:578`; sidecar `learnloop_sidecar/handlers/teach_back.py:68`, `:138`, `:190` | No. About a source item or LO; the explanation is the only artifact | Yes: `teach_back` attempt (`attempt_types.py:16`), mass 0.8 (`config/schema.py:1836`), capability `schema_interpretation` (`learner/capability_mapping.py:32`); summarized into the router card (`daily_plan/router_teach_back.py:1-33`) |
| RE5 teach-back offers | `spec_recognition_and_effort_v1.md` §8 | No. A router offer to explain a topic | Unbuilt |
| Lesson checks and predictions | `teacher/checks.py:1-23`; `teacher/contracts.py:66` (`PredictionV1`), `:74` (`CheckV1`, committed solution, rubric by fact); the "your thinking" note, never to the grader (`teacher/service.py:1054-1064`) | No. About the lesson's content | Checks yes, at a learned mass (`learner/lesson_weight.py:896`) |
| Workbench "Check my work" | `workbench/check.py:1-35`; symbolic verdicts `workbench/symbolic.py:84`; steps ledger `migrations/207_workbench.sql:83` (`kind` `step` or `stuck`) | Judges the learner's steps; asks nothing | No |
| `approach_question` hint | `hints/kinds.py:49`; contract `hints/contracts.py:440-444` (`asks_about`: approach, assumption, goal, first move) | Asks about the approach, as level-1 help | No. Replies are "doesn't connect" shortcuts about the hint |
| Reader after-section check, pattern `self_explanation` | `reader/reader_guidance.py:581`; `substrate/activity_patterns.py:471` | No. About a passage | As a quick check |
| Project probes (`what_does`, `where_change`, `predict`, `why`) | `projects/probes.py:1-25`; `projects/ai_contracts.py:22` | **Yes**, the learner's diffs; answer-first with cited spans, a closed-book filter for generic questions | Yes, but sealed for `probe_delay_days`, practice only, in `project_store.sqlite` |
| Explain-before-accept gate | `spec_project_understanding_v1.md:54` | Yes, an agent diff | Spec only, opt-in |
| "What do you think went wrong?" | `spec_learner_input_after_miss_v1.md` §3 | About a miss, after submit | Accepted, unbuilt |

## 2. In plain words

Decided (owner, 2026-11-20): internally these are **work questions**; the learner sees **"A question about your work"**.

While the learner works, in a notebook cell, a workbench derivation or the coding dialog, LearnLoop may ask **one short question about a line or step they wrote**: "Why `+=` here and not `=`?", "What does this loop guarantee when it ends?", "What would change if the bias moved after the ReLU?" The learner answers in their own words, and can point at a line. It is not a quiz on the topic: it is anchored on their artifact and refused if a model could answer it without seeing that artifact.

The question's key is written and logged before the question is shown. The reply is graded blind against it. The diagnoser reads the reply. A good answer counts as in-context evidence at a learned weight and never certifies. Whether and when to ask is drawn with a logged propensity, priced in minutes and interruption, and randomized by session so its effect can be measured.

## 3. Rules every stage follows

- **No rule maps a score, miss count, stuck flag or elapsed time to asking.** Asking is a candidate drawn with a logged propensity (§7): `exact` when the probability vector is computed, `estimated` (with its method and uncertainty) for a Thompson draw.
- **No made-up constants.** Values, burdens and masses start at a seeded prior or zero and are learned. Payload bounds (schema maximums, text lengths) are registered `keep`.
- **Help is never certification.** Every reply is `in_context` (NA §7.4).
- **Ask, don't assert, don't fix.** A question quotes only the learner's own work, never says whether the anchored line is right, and is refused if what it names would repair the work (§6.3). WQ never writes code or a step, so the ask-before-code rule (owner, Nov 18) holds.
- **The key comes first.** It is committed and logged before the question is shown, as lesson checks commit their solution and project probes write the answer first.
- **The grader stays blind** (`BlindGradingContext`): the question, the anchored excerpt, the reply and the key; never the session, history or other questions.
- **Commits are frozen first** (NA §6.3). No question is shown before the commit it follows is frozen, and none is anchored on or downstream of an open mask.
- **One question at a time, enforced in code.** Prompts alone did not hold this (`spec_project_understanding_v1.md:63`).
- **Persisted meaning follows `docs/algorithm-change-playbook.md`.** **At n = 1, no stage claims a benefit.** **Exam and held-out material is never served, quoted or used.**

## 4. Stages and placement

| Stage | What | Persisted meaning? | Needs |
|---|---|---|---|
| **WQ0** | Offline replay: generate and validate questions on stored work | No | Nothing |
| **WQ1** | The service, receipts, the workbench surface, the randomized arm | Yes (burden and question choices) | RW2b (built) |
| **WQ2** | Notebook and coding surfaces, executable checks | No | NA2; NA5 for coding |
| **WQ3** | The diagnoser, text gaps and router card read replies | Yes | WQ1 |
| **WQ4** | Replies as evidence at a learned weight | Yes | WQ3; NA decision 9 (§8.4) |
| **WQ5** | Lessons, and folding the three question features into one service | Yes (teacher schema) | TE; NA4 |
| **WQ6** | Simulated-novice arm (optional) | No | NA §9.7 |

**Placement:** Decided (owner, 2026-11-20): WQ0 runs beside the queue; WQ1 lands with the UX overhaul. Its learned interruption burden and question choices change persisted meaning and follow the playbook; its card is learner-visible and receives UX review. The remaining WQ work sits after reveal adjudication and before projects-as-goal in the queue above, subject to dependencies: WQ2 waits for NA2, and for NA5 on coding surfaces.

## 5. One service

One proposed package, `src/learnloop/work_questions/`. Decided (owner, 2026-11-20): notebooks use this shared service, including `ll.explain` and "why this change?", instead of separate notebook-only features. Surfaces call it through an adapter; it imports no surface. An import-linter contract keeps learner-model modules from reading its tables before WQ3 and WQ4.

### 5.1 The artifact view

`WorkArtifactV1`, built by each surface's adapter:
- **Units:** stable id, kind (cell, step, diff hunk, line range, answer paragraph), text, revision hash, author (learner, teacher, AI, unknown) and position. Authorship comes from NA §9.3's patch events, the workbench steps ledger, or the coding dialog's accepted offers.
- **Verdicts where they exist:** RW2b's per-step valid / questionable / unchecked with `checked`, `checked_numerically` or `model`; execution receipts (checks passed, errors, outputs); StateViewer and LiveEdit traces as values at named points; NA §8's mutant matches with their noise model.
- **Context:** the public stem; the target facets and cold item family (NA §6.1's contract target, or the item's facets); the open diagnoser claims (EP's claim card); facet uncertainty from `mastery_diagnostic_view`, as `plan_followups` reads it; open masks and their dependants, for exclusion.
- **Never in it:** `key.py`, masked values, the open item's expected answer or worked solution, held-out text, unshown reveal units.

Adapters: workbench (steps and the last check), notebook (NA §9.1's observe verbs), coding dialog (the learner's solution hunks), lesson (the learner's free answers in it).

**Only learner-authored units can be anchors.** A teacher edit or worked chunk the learner kept is anchored only by `why_this_change`.

### 5.2 Question types

| Type | Asks | Reply | Checked by code |
|---|---|---|---|
| `justify` | Why this line or step | Text | Rubric only |
| `predict` | What changes if one named change is made to their line | Value or direction, and a reason | The value: run in the scratch worker (NA §9.4) or RW2b's symbolic check |
| `invariant` | What holds after this loop or step | Text | Where code allows, the stated property evaluated on their run |
| `compare` | Why this and not a named alternative | Text | The alternative passes §6.3 |
| `locate` | Where X happens | A pointer and text | The pointer, against the key's anchor set |
| `purpose` | What lines a to b accomplish (a subgoal label) | A short label | Rubric only |
| `why_this_change` | Why a kept teacher edit or worked chunk works | Text | Rubric only |

Qualitative answers come first where the type allows (NA §7.1).

### 5.3 Generation

- **One structured call** on a new route, `work_question` (plan transport by default, under the existing spend envelopes), given the artifact view. It returns candidates, each with: type, anchor unit ids and line range, the change (`predict`) or alternative (`compare`), the **key first** (expected points and criteria named by fact, each with its facet map), then the question text.
- **Lazy:** the call runs only after the moment draw says ask (§7.2), so a "not now" draw costs nothing.
- The schema's candidate maximum is a payload bound, not a policy.

### 5.4 Validation, before anything is shown

1. The anchors exist at the snapshot's revision and are learner-authored.
2. Every code or LaTeX quote is verbatim from the anchored units.
3. Not a yes/no question, and nothing a bare "yes" answers (learner-input §4.2).
4. **Leakage:** `practice_leakage.check_leakage` (`content/authoring/practice_leakage.py:180`) against the held-out inventory; `answer_leaks_expected` (`tutor/tutor_qa.py:1714`) against the open item's expected answer, sidecar-side; NA §11.2's dataflow rule (nothing derived from the key or an unshown reveal unit). When the Decider's shared per-criterion reveal judgment is built (owner, Nov 18), it replaces the overlap checks here.
5. **Not a fix** (§6.3).
6. **Not generic.** Project probes' closed-book check, adapted. A question quotes the learner's line, which makes it self-contained, so the check runs with the quoted excerpt stripped, or tests whether the key changes on a perturbed artifact. If a model without the artifact still answers it correctly, the question is about the topic, not this work, and is dropped (topic questions belong to teach-back). Run unadapted, the check would drop exactly the best justify and compare questions (second review, Nov 20).
7. **The key is checked** where code can: `predict` values run, `locate` anchors exist. An unchecked key is labelled "model's reading" on the receipt, and so is its grade.

Every drop writes its rule to the receipt.

## 6. Leakage and not doing the work

### 6.1 Open attempts
**Which commit a rule concerns (ruling, second review):** §3's "no question before the commit it follows is frozen" concerns the commit the question is *about*. A question about earlier, frozen work may appear while a *different* attempt is open, and this section prices that.

A question shown while an attempt is open (a workbench session before submit, a notebook before its commit) can cue that attempt. It writes a `help_assists` row, `assist_kind = 'work_question'`, and becomes a fact on that attempt (EP Part A). Decided (owner, 2026-11-20): unasked work questions are allowed, and a question during open work is also level-1 help that makes the attempt assisted until EP's facts replace that label. The randomized arm and learned burden price interruptions. A question after the commit or submit costs that attempt nothing. The value in §7.2 prices the difference, so the policy can learn to prefer post-commit moments.

### 6.2 Where it never asks

Cold checks, probes (`diagnostic_probe`, `masked_cell_probe`, any probe presentation), RO5's randomized checks, exam sittings, and held-out or exam-protected items: the list in `spec_learner_input_after_miss_v1.md` §4.6.

### 6.3 A question is not a fix

`predict` and `compare` name a change. The validator applies it: in code, the learner's cell or function runs with the change in the scratch worker against the activity's checks; in a derivation, RW2b's symbolic check runs on the changed step. If the change turns a failing check into a pass, or a questionable step into a valid one, it is a hint (`error_specific`), not a question, and is dropped. The anchor draw covers right and wrong lines alike, so being asked is not itself a sign the line is wrong; the line's verdict at ask time is logged so the report can check that.

### 6.4 Replies that ask back

A reply that asks a question or asks for code goes to the surface's own dialog (tutor, teacher, coding dialog) under its rules, including ask-before-code. WQ does not answer.

## 7. When to ask

### 7.1 Moments

Events, never timers:
- `commit_frozen` (NA §6.3);
- `run_passed`: an execution receipt whose checks pass, the first time or after a failure;
- `behaviour_edit`: an edit whose next run changed an output or a check result;
- `check_returned`: RW2b's check with at least one valid step;
- `step_written` (workbench);
- `idle`: RE0's active clock leaves active, by its own definition, with no new threshold;
- `edit_kept`: a teacher edit or worked chunk kept (NA §9.3);
- `work_closed`: the learner closes the work with nothing open.

**Not after a submitted miss.** The step between submit and feedback belongs to the learner-input spec's one-question rule (`spec_learner_input_after_miss_v1.md` §8).

### 7.2 Value and the draw

At a moment the candidates are `not_now` and `ask`. The value of `ask`:
- **plus** the reply's expected information on the target facets: EIG over the diagnoser's open claims and AD's facet belief, converted to minutes through the shared candidate-valuation adapter (`spec_reader_workbench_v1.md` §18);
- **plus** a learning effect of explaining, one coefficient per question type, starting at zero;
- **minus** the objective's existing attention price times the expected reply minutes, learned per type and surface from WQ's receipts, seeded from teach-back turns' active seconds;
- **minus** the interruption burden: the resumption lag (settlement to the learner's next edit, less their usual gap between edits on that surface), learned per moment kind from a prior centred on zero;
- **minus** lost coldness on an open attempt (§6.1), at the value the objective already gives a cold outcome.

The draw is a Thompson draw over these posteriors (NA §7.5's pattern). One posterior sample does not give a selection probability, so the propensity is **estimated** by resampling and logged as `estimated` with its method and uncertainty (this needs migration 236's `propensity_kind` CHECK widened; NA §12.2). Alternatively, a softmax over posterior means gives an exact one. On `ask`, the validated candidates are drawn the same way; the joint propensity includes the session's experiment assignment and the conditional candidate selection. There is no count cap and no cooldown: a second question is valued with the first's reply and burden in hand.

### 7.3 Showing it

- Generated in the background. Shown only if the anchor's revision is unchanged; otherwise re-validated on the new revision or settled `superseded`.
- **Notebook:** a gutter mark on the anchored line and a callout beside the cell, drawn by the host, not by notebook code (annotations are host-owned like commits; marimo's `Hint` widget only runs inside marimo, brainstorm §13.1). **Workbench:** a card under the anchored step. **Coding dialog:** a message with an anchor chip. **Lesson:** a turn.
- It never takes focus and never blocks typing or running.
- Decided (owner, 2026-11-20): the phone accepts text answers once it shows workbench sessions.

### 7.4 "Not now" is text

There is no skip button. The card holds one text box and, on code, "point to a line". The learner can keep working; the card stays docked.
- **Settles** at the first of: a reply; the next commit or submit on that work; the session's end; the startup sweep. No timer. Unanswered is `ignored`.
- **The reply is read** by the blind grader's existing `StuckReading` (`attempts/stuck.py:108`). It has no deferral field today, so WQ1 adds one (a `defers` reading), with its own tests. If it doesn't attempt an answer and names a deferral ("later, I'm mid-loop"), it is `deferred`: no grade, and the same question is a candidate again at the next moment on that anchor, re-validated. "I don't know" is an answer that scores low, as in teach-back.
- Deferrals and ignores feed the burden model.

## 8. Grading, diagnosis and evidence

### 8.1 The grade

The blind grader, on `grading`, sees the question, the anchored excerpt (part of the question's stimulus), the reply, any pointer, the key and the criteria. Deterministic parts (a `locate` pointer, a `predict` value) are checked in code first.

### 8.2 What the learner sees

While the work is open there is no verdict, only "Noted". A verdict on open work would be a hint. The graded result and the key appear with the work's own feedback after its commit or submit, held as FG1 holds causes. Decided (owner, 2026-11-20): with nothing open, feedback timing is a logged draw.

### 8.3 Diagnosis (WQ3)

- The exchange goes to the diagnoser as an attributed block, in the shape the learner-input spec gives stated reasons (§3.3 there), on this work and as history later; to the learner-text gaps pipeline as a new source (`diagnosis/text_gaps/sources.py`); and to the router card as the learner's own words, beside teach-back summaries.
- A wrong or vague reply reweights hypotheses through the diagnoser's fit reading (learner-input §7) and never removes one. **A follow-up is not a rule:** the updated claims change the next moment's value, a follow-up on the same anchor is a candidate there, and a probe is the router's draw.
- Line-by-line recitation (brainstorm §4.2, Smith & Zilles 2024) is a rubric criterion ("relates the line to its purpose"), not a separate classifier.

### 8.4 Evidence (WQ4)

- **Coldness:** always `in_context`. Never certification, never R_cold, never AD's unassisted success.
- **Mass** `m_wq = σ(η_wq + u_L + β_type)`, learned as `learner/lesson_weight.py` learns a lesson check's mass: only from the next qualifying cold outcome on an unseen item of the same LO. The posterior mean as of the question is recorded on its receipt, so replay never moves it. Decided (owner, 2026-11-20): the logit-mass seed is N(0, 1), matching the lesson check's seed.
- **Path A:** Decided (owner, 2026-11-20): use the adopted cross-surface observation stream (NA §12.4), with an `activity_observations` row of kind `work_question` under the work's administration, with the `measurement_events` attempts write, under a versioned payload.
- The alternative of minting a held item and a separate attempt for each reply is rejected; shared observations keep work questions in the same evidence stream. No number of work-question observations may change certification.
- **Acceptance** is the emission ablation (Pipeline Augmentation Plan §D): replies earn mass only for predictive gain they add in replay.

## 9. Logging and storage

### 9.1 The receipt (WQ1)

A new `RAW_LEDGER` table, `work_questions`, at the next free migration number when WQ1 lands, one row per moment decision, including `not_now` draws and dropped candidates:
1. **Identity:** id, surface, work reference (workbench session, notebook instance, coding session, lesson), the attempt or administration when bound, learning object, target facets.
2. **Moment:** kind, triggering event id, artifact snapshot hash, anchor unit ids, revision hash, line range, anchor author, anchor verdict at ask time.
3. **Decision:** candidate set with values and posterior draws, moment and candidate propensities, `propensity_kind`, policy version, RNG seed, experiment assignment id (§10).
4. **Question:** type, text, key (sidecar-only, never sent to the client), code-check result, validator verdicts and drop reasons, route, model, prompt version, spend.
5. **Timing:** generated, shown, first keystroke, settled; reply active seconds; resumption lag.
6. **Outcome:** disposition (`answered`, `deferred`, `ignored`, `superseded`, `dropped`, `not_now`), reply, pointer, `StuckReading` fields, grade reference, coldness class, whether an attempt was open, the `help_assists` id.

The passive receipt table alone needs no successor tag. WQ1 also learns burden and chooses questions, so service activation does need a successor tag (§11). Learner-model reads wait for WQ3 and WQ4.

### 9.2 Grades

The blind grade is a raw grade in the substrate (path A). Until WQ4 it is stored and read by no learner model, as NA2 stores commits.

## 10. Evaluation at n = 1

- **Randomized by session.** When a work session opens, a seeded draw assigns it `questions` or `none`, through `policy_experiment_assignments` (RO5's mechanism). In `none`, every moment is `not_now` with propensity 1. Session-level assignment keeps carryover within a session out of the comparison. Decided (owner, 2026-11-20): the owner sets the randomized `none` arm's rate as an experiment design value, registered `keep`; decided in principle; the value is owed by the owner.
- **Pre-registered outcome** at assignment: the next cold attempt on an unseen item of the session's target facet within a window, recorded as NA §12.1's `outcome_target_json`.
- **Time cost:** the session's active minutes, reply minutes, resumption lags, completion and abandonment.
- **Report** in `learnloop data-capture report`: asked, answered, deferred and ignored by moment kind and surface; drops by rule; grader agreement with the owner's spot checks; gain per minute against `none` with effective sample size. Everything not randomized, such as the effect of question type, is labelled observational.
- **Power first:** NA0.6's calculation, run for g ≈ 0.55. If a year of sessions can't detect it, the report says the router won't learn the difference.

## 11. Stage details and acceptance

### WQ0: offline replay
Generate and validate questions on stored work: owner-supplied workbench-session exports, the NA prototype's notebooks (kept outside the repo), and captured project diffs. Nothing is shown to a learner. The owner rates a sample. **Acceptance:** a report of candidates per moment, drops per rule, the closed-book generic rate, fix-check drops, and spend and latency per question.

### WQ1: service, receipts, workbench
**Moments in WQ1 are limited to stable ones** (`commit_frozen`, `check_returned`, `work_closed`). Generation plus validation takes long enough that anchors change mid-edit, so most questions on unstable moments would settle `superseded`. WQ0 reports show latency and the supersede rate before more moments are added. WQ1 learns the interruption burden and chooses questions, so it is persisted meaning, not receipts only: it follows the playbook (NA §15's correction).
The package, `WorkArtifactV1` with the workbench adapter, the moments, the draws, validation, the card, settlement, the blind grade stored, the receipt table, the randomized arm and the report section. No kill switch (owner, Nov 16); the `none` arm is the off state.
**Tests:** the key is logged before the question is shown; a question with code the learner didn't write is refused; a fix candidate is dropped; held-out text never appears; teacher-authored anchors are refused except for `why_this_change`; the grading context has no history field; propensities are exact and reproducible from the seed; in a `none` session the workbench behaves byte-identically to today; no learner-model module reads `work_questions`.

### WQ2: notebooks and coding
The notebook adapter on NA §9.1's observe verbs, the host callout, `predict` and `compare` checks in the scratch worker, the coding-dialog adapter with NA5's ask-before-code validator.
**Tests:** no anchor on or downstream of an open mask; no question before its commit is frozen; the scratch snapshot is permission-filtered; the callout never runs as notebook code.

### WQ3: diagnosis
The diagnoser block, the text-gaps source, the router-card line. Successor tag, `UPGRADES` row, replay tests; below the tag, and on work with no answered question, the diagnoser's input is byte-identical.

### WQ4: evidence
`m_wq` on path A, with a logit-mass prior of N(0, 1). Successor tag; identity pins for the new kind; replay below the tag identical; **no number of WQ rows changes certification** (test).

### WQ5: lessons and one service
Decided (owner, 2026-11-20): use one work-question service across surfaces. A proposed teacher action `ask_about_work` in all eight turn-schema variants (four base and four TE2 variants in `src/learnloop/teacher/contracts.py`), with NA §9.2's cost list. NA §6.2's `ll.explain(after=)`, NA §9.3's "why this change?" one-liner and the hint spec's two deferred kinds become WQ types (`why_this_change`, `purpose`) instead of separate features.

### WQ6: simulated novice (optional, later)
After NA §9.7's "debug the interpreter" exists: the learner explains their implementation to a novice whose belief is a mutant interpreter in `key.py`. Code runs the belief; it changes only when the grader judges that the explanation names the discriminating reason. Prompted LLM novices flip 73–98% under any feedback and leak expert knowledge (brainstorm §8, Lane A and C), so a voiced persona is an arm only if it beats a plain WQ question on cold gain per minute.

## 12. Owner decisions

| # | Decision | Decided wording |
|---|---|---|
| 1 | Name | Decided (owner, 2026-11-20): "work questions" internally; "A question about your work" to the learner. |
| 2 | Unasked questions | Decided (owner, 2026-11-20): allow them. The randomized arm and learned interruption burden guard against over-asking. |
| 3 | Open work | Decided (owner, 2026-11-20): count the question as level-1 help that makes the attempt assisted until EP's facts replace the label; post-commit questions cost that attempt nothing. |
| 4 | Seed of `m_wq` | Decided (owner, 2026-11-20): N(0, 1) on the logit mass, matching `learner/lesson_weight.py`, because the answer is given with the work in view. |
| 5 | Feedback with nothing open | Decided (owner, 2026-11-20): a logged draw. Feedback on open work stays held. |
| 6 | Randomized `none` arm's rate | Decided (owner, 2026-11-20): the owner sets the design rate; decided in principle; the value is owed by the owner. |
| 7 | Evidence storage | Decided (owner, 2026-11-20): path A, one `work_question` observation per answer in NA's adopted stream; never certification. |
| 8 | Phone | Decided (owner, 2026-11-20): text answers once the phone shows workbench sessions. |
| 9 | Placement | Decided (owner, 2026-11-20): WQ0 beside the queue; WQ1 with the UX overhaul; remaining WQ work after reveal adjudication and before projects-as-goal, with WQ2 waiting for NA2 and, on coding surfaces, NA5 (§4). |

## 13. Not in this spec

- Multi-turn conversations about the work: that is teach-back. A follow-up is a new candidate.
- Grading code by its explanation alone ("explain then execute").
- A voiced novice before WQ6's test.
- Count caps or cooldowns.
- Changing teach-back's `plan_followups`, whose fixed ordering and `max_followups` count the workbench spec's §18 already plans to lift.
- Delayed own-work items (NA §10). Answered questions may seed them; NA §10 governs them.
