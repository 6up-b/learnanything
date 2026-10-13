# ITS Research Sweep 2026-10

*Compiled 2026-10-13 on branch `docs/its-research-sweep` (from main `f2f02e32`), at the owner's request: "review the following papers on arxiv and see if there's any additional intuition or product direction or research direction we should pursue via learnloop based off of the insights found in the papers".*

**Scope.**
- The four papers the owner named: 2605.23048, 2606.23015, 2606.28881 and 2605.12988.
- The 50 most recent arXiv results for "Intelligent Tutoring Systems", fetched 2026-10-13. There are 393 hits in total; the listing includes three of the four named papers.
- Ten listing papers were read in full as deep reads. Two more were read in full but get short notes. Every one of the 50 has a line in Appendix A.

**Baseline.** Each paper was compared against what LearnLoop already does or plans:
- main at `f2f02e32`;
- `docs/specs/` and `docs/brainstorming/`, especially [[Bitter Lesson Research Sweep]], [[Pipeline Augmentation Plan]] and [[Diagnostic Pipeline Synthesis]];
- the in-flight branches `docs/reader-workbench-spec`, `sources/canonical-practice`, `evsi/calibration`, `docs/learnloop-ux` and `docs/adaptive-hints`. The last is still empty.

The point is to report what is *new*. Where a paper only confirms an existing decision, it is listed under "confirms", with the decision it confirms.

**Legend.**

| Mark | Meaning |
|---|---|
| *(inferred)* | My inference; not stated in the paper or the spec |
| **Strength** | My grade of the evidence: weak, moderate or strong, with the reason |
| §n | Section in the paper, or in the LearnLoop spec named next to it |
| S1 | `docs/specs/spec_blind_grading_diagnosis_split_v1.md` |
| S2 | `docs/specs/spec_embedding_consumers_v1.md` |
| FIELD | `docs/specs/spec_learner_field_v1.md` |
| ROUTER | `docs/specs/spec_action_router_v1.md` |
| DL | `docs/specs/spec_daily_loop_v1.md` |
| ME | `docs/specs/spec_measurement_efficiency_v1.md` |
| EIG | `docs/specs/spec_probe_eig_redesign.md` |
| PLAN | [[Pipeline Augmentation Plan]] |
| RW | `spec_reader_workbench_v1.md` (branch `docs/reader-workbench-spec`) |
| SRC | `spec_source_practice_and_probes_v1.md` (branch `sources/canonical-practice`) |

---

## 0. Summary: what matters for LearnLoop

1. **The grader is weakest on answers that look finished. One of LearnLoop's guards stops short of proofs.**
   - The evidence:
     - Correct answers reached by wrong reasoning are missed 16% of the time by the best setup, and up to 46% of the time by fine-tuned classifiers (2605.23925).
     - LLM judges reject valid but unusual steps 13–91% of the time and accept wrong ones 7–71% of the time. Which error a judge makes depends on the model, not on the prompt or on being shown the reference solution (2605.16207).
   - LearnLoop's defences have the right shape: the valid-alternative path, the clarification question, and one careful pass with no juries.
   - The gap: the valid-alternative path only switches on when a machine can check the final answer (`attempts/grading_support.py`, `apply_valid_alternative_gate`; S2 §5.5).
   - Proofs, "show that" items and explanations get no such protection, and they are a large share of the owner's practice. A keyword count found 19 of 99 linear-algebra prompts and 36 of 78 probability prompts asking to prove, show, justify, explain why or derive.
   - Proposed fix: extend route re-derivation to items without a checkable conclusion, and measure over-rejection and over-acceptance together.

2. **Fix the correct-answer trap in the items, not in the grader.**
   - The trap concentrates in a few items whose particular numbers let a wrong rule produce the right answer. Two items held 71% of all cases (2605.23925 §4.1–4.2).
   - LearnLoop's persona gate already refuses diagnostic items that a misconception-holder could pass (ME §3.0).
   - Extend the same check in three places:
     - to generated practice instances: choose numbers so known wrong rules give wrong answers;
     - to verbatim textbook exercises: record where a wrong rule passes, so a correct answer there isn't counted against that misconception;
     - to the EVSI calibration's response model: a misconception-holder's chance of answering correctly varies by item.

3. **Don't let one simulator pick a policy (2609.26069, RankCert).**
   - Simulators that fit the same data equally well named the same best tutoring policy only about 27% of the time. How well a simulator fit barely predicted whether it ranked policies correctly.
   - The `evsi/calibration` branch compares policies (EVSI vs EIG vs today's caps) under a single fitted response-model family.
   - Proposed rule: add at least two structurally different simulators, and call a policy or parameter "supported by simulation" only if it wins under all of them.
   - LearnLoop's EVSI already abstains when grader models disagree (`scheduling/evsi.py`); this applies the same rule one level up.

4. **Judge the diagnoser by what it predicts, not by who agrees with it (2603.29141).**
   - The field's measurement researchers argue that agreement statistics, including LLM-vs-LLM agreement, cannot show a label is *right*. What can is predictive validity: do the labels forecast later outcomes?
   - Proposal: when a diagnosis is written, it freezes a forecast of the learner's next relevant cold answer, and the forecast is scored when that answer arrives.
   - LearnLoop is unusually well placed to do this, with a single learner, a judgment ledger and cold reviews. It would also give the M1 history-mode arms (S1 §5.2) a criterion grounded in real outcomes.

5. **The learner's own confidence is probably the best cheap predictor LearnLoop has. It is collected, but no prediction uses it.**
   - Weak evidence (2606.28881, n=27):
     - a 1–5 confidence tap before answering predicted correctness at AUC 0.89 on its own;
     - students were worse calibrated than the model but better at telling their right answers from their wrong ones;
     - most miscalibration was situational, not a stable trait.
   - LearnLoop already collects an optional confidence tap and runs a learner-vs-model Brier "duel". The probe spec keeps confidence "logged-only … until a calibrated model exists" (EIG §7.1), but nothing is building that model.
   - Proposal: add two confidence arms to the offline harness, at no friction:
     - one from the tap;
     - one from the hedging the grader already reads in the learner's text.

6. **Behaviour is not mastery (2608.16963; about 5,000 EdNet learners).**
   - Clusters of study style (how much video, reading, revising) predicted later persistence (η² 0.106). They did not predict later unassisted accuracy (η² 0.003).
   - This is direct support for "reading is not evidence" (RW W1).
   - Use reading and help telemetry for plan size and re-entry, never for P(success). The Reader workbench, with its rich telemetry, is where this line is most at risk.

7. **Left alone, learner choice drifts toward comfort practice, and engagement rewards drift toward easy wins.**
   - Evidence:
     - 2605.21613 (simulation): risk-averse self-selection produced about 9–17× the overpractice of other strategies.
     - 2604.04251: engagement-rewarded tutors farm easy successes.
     - 2606.23015's "flow" reward is success weighted by difficulty, an engagement-style proxy.
   - LearnLoop's reward (cold retrieval, S = 0.75 R_cold + 0.25 R_next) and its value-of-information stop rules are on the right side of this line.
   - The new product move is to *show* value at the moment the learner picks something off-plan, not to block the pick.

8. **The router's logs already allow an "adaptivity audit" (2606.23015 §3.3).**
   - Plot what the router actually served against the learner state it saw, week by week. A flat curve means the router is not adapting; a curve far from the target band means it serves the wrong difficulty.
   - It is cheap, needs no new data, and nobody has drawn it.

**Contradictions found** (§6, with recommendations):
- C1, valid alternatives on proofs: **change**.
- C2, reference-first grading on multi-route items: **test**.
- C3, showing the grader the final-answer match first: **test**.
- C4, confidence logged-only: **keep the rule, start the arm**.
- C5, single-family EVSI simulation: **change the protocol**.
- C6, S1's correct-answer citation: **keep, update the number**.

Two further checks found no contradiction:
- the success band and reward choice (§6 C7);
- learner autonomy (§6 C8).

---

## 1. Baseline: what LearnLoop already has that these papers touch

LearnLoop is already past most of the systems in this listing. The table below is what each paper was compared against. All of it is on main unless marked otherwise.

| Area | Already in LearnLoop | Where |
|---|---|---|
| Learner-blind grading | One high-effort pass; no voting, juries or debate; verified reference first; solve-first when no reference; one clarification question allowed for "a correct answer possibly reached by invalid reasoning" | ADR-016; S1 §4; S2 §5.5; `attempts/blind_grading.py` |
| Valid alternatives | Divergent route plus a final answer that verifies → re-derive the learner's route; unlocated shortfalls become *unassessed*. **Only when `final_answer_check.status == "matches_reference"`** | `attempts/grading_support.py`; S2 §5.5 |
| Correct-answer diagnosis | Off live (`diagnosis.correct_answer_sample_rate = 0.0`), citing "The Correct Answer Trap" | S1 §5.1, O5 |
| Item gate for diagnostics | A persona holding the misconception must fail the item, or it doesn't ship | ME §3.0; `content/authoring/persona_gate.py` |
| Discrimination profiles | Per-item "what a holder visibly produces", with a two-tailed fill-rate revert rule | `diagnosis/discrimination_profiles.py` |
| Judge evaluation | E1 report: κ, anchor accuracy, GradeFlipRate, valid-alternative false rejection (CAS-checkable alternatives only), real-vs-synthetic gap; no numeric thresholds; `judgment_ledger`; adjudication store; B5 scoreboard | S1 §13; `diagnosis/diagnosis_adjudication.py`; `diagnosis/scoreboard.py` |
| Decision value | Minutes-denominated EVSI over a credible set of grader matrices; abstains if the winner flips | `scheduling/evsi.py`; DV §6 |
| Experiments at n=1 | Micro-randomised reversible near-ties with propensities logged before selection; outcomes at the next spaced cold review; DR replay; effective sample size per comparison | `scheduling/randomization_layer.py`; ROUTER §10; R1 on `merge/r1` |
| Learner model | FSRS-6 plus a per-LO 2PL EKF incumbent; prequential arms including `lo_general` (θ_general + θ_L), `idea_hier`, and the `llm_probability` arms raw and recalibrated; "can't tell keeps the incumbent" | FIELD §4, §7 |
| Confidence | Optional 1–5 answer confidence in diagnostic blocks, logged only; learner-vs-model Brier duel; the grader tags learner text `confident` / `hedged` | EIG §7.1; RW D22; `goals/exam_calibration.py`; `attempts/grading.py` |
| Signal firewall | Reading, dwell and help are engagement or steering signals, never evidence | RW W1 (branch); P3 invariant 6 |
| Value-of-information stopping | Owner decision 2026-10-12: lift count caps onto EVSI/EIG; EVSI calibration on Eedi in progress | RW §18, §20.7; SRC §8.3; `evsi/calibration` (uncommitted) |

**Papers in this listing that LearnLoop's docs already cite:**
- 2605.16207, in PLAN §C ("valid alternative as a third outcome");
- 2606.03822, in EIG §18 and the "modeling incorrect student thinking" dialogue;
- 2604.08263, in the Synthesis as NSKT, verdict "skip";
- 2604.04237, in the same dialogue;
- the correct-answer-trap paper, cited by title (AIED'26 workshop version) in S1 §5.1.

---

## 2. The four papers the owner named

### 2.1 StanBKT: full Bayesian knowledge tracing (arXiv 2605.23048)

Pradhan, Pei, Lee, Zhang, Ottmar, Sales (WPI). Preprint, cs.HC, 21 May 2026.

**What it claims.**
- It is a Python package that fits Bayesian Knowledge Tracing in Stan. BKT is a two-state hidden Markov model with learn, forget, guess, slip and initial-mastery parameters.
- It offers four inference engines: NUTS MCMC, ADVI, Pathfinder and MAP. It offers three pooling structures: one parameter set for everyone, one per group, and hierarchical partial pooling on the logit scale (§3.2–3.4).
- Guess and slip are bounded to [0, 0.5]. That rules out the degenerate solution where "guessing" means "knowing" (§3.5).
- The argument is that going Bayesian pays off in the posterior, not in prediction.

**Evidence.**
- **Prediction.** On ASSISTments 2020 (top 10 skills, 794k training and 189k test interactions), every engine reports the same numbers as pyBKT's EM: accuracy 0.694, AUC 0.711, RMSE 0.449 (§4.1, Table 6). MCMC took 822 s; EM took 3.35 s.
- **Parameter recovery.** This was tested on one simulated data set. The text says the true values were recovered (§5). In fact the forget and slip posteriors sit about 2.4 posterior SDs from the truth (Table 4).
- **Condition comparison.** A re-analysis of a 3×3 perceptual-cue experiment (688 sixth-graders, about 20k observations).
  - The cues moved the **guess** parameter: incongruent colour −0.082, 95% CrI [−0.121, −0.040].
  - No condition moved **learn** (§4.2, Table 7).
  - Priors and convergence diagnostics for this analysis are not reported.

**Strength.** This is a software paper. Its useful result is the null one: the estimator does not change predictive accuracy. The substantive claim, that cues act on guessing, rests on one re-analysis by an overlapping author group.

**What transfers.**
- **Change learner models for calibration, not AUC.** A learner-model change justified by AUC alone deserves suspicion; the reason to change is calibrated uncertainty per concept. FIELD's switching rule (log loss, overall and on first attempts) and its G11 requirement for calibrated uncertainty already encode this.
- **Pooling.** At n=1 the useful pooling runs across *concepts within one learner*, not across students. LearnLoop's `lo_general` arm (θ_general + θ_L) and the `idea_hier` family arm already do this.
- **Item design changes how often a non-knower succeeds.** The cue result says this: an item a non-knower can pass carries little evidence. It is the measurement-side twin of the correct-answer trap (§3.1).

**What doesn't transfer.** BKT itself. LearnLoop does not use BKT, and a binary mastery state would be a step back from the 2PL EKF. PLAN §H puts population KT models "permanently out" of the loop. This paper does not change that.

**Implication.** Nothing to build. It confirms FIELD §7.4.

### 2.2 Counterfactual learning of adaptive instructional policies from logs (arXiv 2606.23015)

Girard, Minn, Bouzeghoub, Vie (Inria SODA / IP Paris). ECML-PKDD 2026, according to the journal-ref field.

**What it claims.** A better difficulty policy can be learned offline, without new experiments. The method:
- Fit a Rasch model (1PL IRT). Treat each student's estimated ability as the context, and the difficulty of the item served as a continuous action.
- Define a "flow" reward r = y·(a − a_min): zero for a failure, and larger for success on harder items (§3.1–3.2, Eqs. 1–2).
- For each round t, estimate the logged system's behaviour as a Gaussian over difficulty given ability (§3.3). Use that estimate twice:
  - as the propensity for off-policy evaluation, with IPS, SNIPS, a pooled "mixture IS", the direct method and doubly robust (§4.3–4.4);
  - as a picture of how adaptive the deployed tutor really was.
- Then optimise a 5-parameter Gaussian policy against the chosen estimator (§4.5).

**Evidence.**
- Four large logs (Table 1):

  | Data set | Students | Interactions |
  |---|---|---|
  | RoboMission | 20.5k | 259k |
  | ASSISTments 2015 | 14.6k | 474k |
  | ASSISTments 2009 | 4k | 98k |
  | Pix | 100k | 3M |

- On the reward the model itself defines, learned policies beat the logged one: +23.8% (ASSIST2015, DR), +22.5% (RoboMission, MIS), +38.9% (Pix, DR) (Tables 4, 6, 7).
- On ASSIST2009 the gains are small, and two estimators come out *below* the logged policy (Table 5). The abstract's "consistent improvements" overstates.
- No confidence intervals and no online test.

**Threats to validity.**
- **Circular evaluation.** The reward comes from the same Rasch model that the direct and doubly robust estimators use. The authors say the reward is "not a direct measure of learning gains" (§3.2).
- **Leakage.** Ability is fitted on each student's whole trace, including responses after the decision being evaluated (§3.1, §5). The authors acknowledge this (§6).
- **No dynamics.** Ability is one static scalar per student.

**What transfers.**
- **The behaviour policy as a diagnostic.** Each week (the n=1 version of "each round"), fit what the router actually served as a function of the state it saw, and plot it. LearnLoop logs everything this needs: DL1 logs every block choice with its candidate set, and R1 records exact head propensities in `router_decisions`. Nobody has drawn the plot. See Product P7.
- **Estimator hygiene confirms ROUTER §10.** The paper's failure modes are IPS and SNIPS disagreeing as the target policy moves away from the logged one, and the effective sample size collapsing. LearnLoop will meet both with a few hundred decisions a month. ROUTER §10 already reports effective sample size per comparison, and the prequential discipline ("an arm sees outcome-free features", `field/evaluation.py`) already avoids the full-trace leakage. Keep both for any router OPE.

**What doesn't transfer.**
- **Learning a policy offline.** A continuous policy needs thousands of learners. ROUTER §13 already sets a four-condition bar before any learned scorer.
- **The flow reward.** It is an engagement-style proxy; see §6 C7. LearnLoop scores outcomes at the next spaced cold review, which is the better target.

**Implication.** Draw the adaptivity audit (P7). Do not adopt the reward.

### 2.3 UBP-CAP: performance prediction and metacognitive calibration (arXiv 2606.28881)

Virdee, single author (Fergana State Technical University). Preprint, cs.LG, 11 pages.

**What it claims.** One pipeline answers three questions (§III):
- predict correctness, using LightGBM with SHAP;
- measure how well students' own confidence is calibrated, using ECE, MCE and the Brier decomposition;
- split calibration error into student, task and residual variance, using a crossed mixed model.

**Evidence.**
- **Data.** 1,195 interactions from 27 undergraduates on 45 programming tasks. The platform, course and collection procedure are not named (§IV-A). Features: pre-task dwell time, a 1–5 confidence rating given *before* the attempt, position in session, a difficulty tag, and prior accuracy.
- **Models.** Logistic regression did best (AUC 0.903) and LightGBM worst (0.878). The differences are not significant (§V-A, Table I).
- **Confidence alone, used as a probability, reached AUC 0.888** (Table I's naive baseline).
  - It carried 60.8% of mean |SHAP|.
  - Removing it cut LightGBM's AUC from 0.878 to 0.649 (§V-B–C).
- **Calibration vs resolution.** Students were worse calibrated than the model (ECE 0.109 vs 0.068) but had **higher resolution** (0.123 vs 0.107). They sorted their right and wrong answers better than the model did, and were off only in absolute level (Table V).
- **Variance split.** Of the variance in calibration error, 12.3% was between students, 1.2% between tasks and 86.5% residual (§V-E): "situational rather than dispositional". The one significant predictor was dwell time: looking longer before answering went with more overconfidence (β = 0.046, p = 0.003).

**Strength: weak.**
- n = 27, single author.
- The hypotheses are called pre-registered, but no registry is named.
- The mixed model was fitted by a two-stage approximation after the proper fit failed. The author says this may bias the student share downward (§VII-B).
- Captions disagree with the tables.
- SHAP and the mixed model appear to use the whole data set rather than held-out folds.

The direction matches a long literature on judgments of learning; the magnitudes should not be quoted.

**What transfers.**
- **Confidence is probably the most informative cheap feature, and LearnLoop already collects it.** LearnLoop has:
  - the optional answer-confidence tap (`PracticeScreen.tsx`, EIG §7.1);
  - a learner-vs-model Brier "duel" (`goals/exam_calibration.py`);
  - the grader's `learner_confidence` tag (confident, hedged or absent), read from the learner's own text (`attempts/grading.py`).

  None of these feeds a predictor. EIG §7.1 holds confidence as "logged-only … until a calibrated model exists". PLAN §F specifies a self-report observation channel, but it is not built. See Product P4.
- **Resolution vs reliability.** If the owner's confidence sorts outcomes better than the field does, combining the two should beat either alone. The prequential harness is where to find out.
- **Situational calibration.** Do not model a fixed "this learner is overconfident" trait. Recalibrate per context. RW §15 already avoids showing a calibration *score* ("confident misses and unconfident successes, never a score"). Keep it that way.

**What doesn't transfer.** The PEDI index, the LightGBM pipeline and the effect sizes.

**Implication.** Add confidence arms offline (P4), and add the reliability/resolution split to the calibration duel. See §6 C4.

### 2.4 KITE: retrieval-augmented tutoring for algorithm tracing (arXiv 2605.12988)

Jain, Bhatt, Pitts, Pandya, Brusilovsky, Norouzi, Hellas, Leinonen, Akram. BEA 2026 workshop (ACL).

**What it claims.** KITE is a teaching assistant for an undergraduate AI course.
- Keyword rules sort each question into one of five intents: direct, conceptual, validation, debugging and tracing (§3.4).
- It retrieves from the course's slides and textbook (§3.3): dense embeddings plus BM25 (70/30), MMR, a cross-encoder rerank, and a boost for official course material.
- It answers in a style that depends on the intent:
  - validation is Socratic and never names the error;
  - debugging gets a hint progression;
  - tracing steps through algorithm state (OPEN/CLOSED lists).
- The paper calls KITE multimodal, but it describes no image processing.

**Evidence.**
- **RAGAs** on 58 questions (judge: gpt-4o-mini). Context relevance 0.94 and faithfulness 0.85, but **factual correctness 0.45** and answer correctness 0.64 (§5.1, Table 1).
- **Expert rubric** on 44 interactions. 93% "yes" on scaffolding, guidance, coherence and tone; 64% on mistake remediation (§5.2). The paper says three experts in one place and two in another.
- **"Simulated students."** Llama-3.1-70B revised its answers after KITE's feedback, and 24 of 27 non-correct answers improved. Three N/A cases are inside that denominator (Table 3).
- **No baseline.** There is no plain-LLM or non-RAG condition and no real learners.

**Strength: weak.** This is a system description with self-evaluation. Its one robust result is negative: high retrieval and grounding scores sat alongside low factual correctness.

**What LearnLoop already has:**
- T6 retrieval: FTS5 BM25 + `qwen3-embedding-8b`, fused by RRF, with listwise LLM verification on consequential paths (S2 §9);
- Reader answer modes;
- "Check my work" and an intent box routed by the Decider (RW1–RW2);
- `find_sources` intents (SRC S3).

KITE adds nothing architectural.

**What transfers.** One evaluation rule: **grounding metrics overstate answer quality.** RW §15 measures learning outcomes, which is right. It should also spot-check Guide and Ask answers for *correctness against the source*, not just whether the retrieved spans were relevant (P9).

**What doesn't transfer.**
- Keyword intent classification: the Decider does this better.
- The simulated-student evaluation: a strong model revising its own answer after feedback shows the feedback is usable, not that anyone learns from it.

---

## 3. Deep reads from the search listing

### 3.1 The correct-answer trap (arXiv 2605.23925)

Imran, Bulathwela (UCL). Preprint, cs.CY. S1 §5.1 cites the AIED'26 workshop version by title.

**Claim.** When a student reaches the right answer by wrong reasoning, AI analysers mostly miss it, because they lean on the answer.

**Evidence.**
- **Data.** 20,964 real Eedi maths responses with student explanations, labelled by experts into three classes (§3.2):
  - True_Correct, 60%;
  - False_Misconception (wrong, with a misconception), 38%;
  - True_Misconception (correct answer, but holding a misconception; "TM"), about 1.6–2%, 343 cases.

  Rater count and agreement are not reported. The label names match Eedi and Vanderbilt's public Kaggle set "MAP – Charting Student Math Misunderstandings" (2025) *(inferred: the paper calls it "the Eedi benchmark")*.
- **Results on 61 held-out TM cases** (Table 2):
  - Fine-tuned T5-small and BERT-base caught 57% and 54%.
  - Gemini 3 Flash with a task-specific prompt caught 84% (95% CI 72–91), at 87.6% balanced accuracy.
  - The two Llama models caught 82–84%, but only by over-flagging: true-correct recall was 68% and 55%.
  - A larger thinking budget did not help (§4.3).
- **PRM800K** (model-written competition maths). Gemini's detection of reasoning errors fell from 93.5% to 83% when the final answer was correct (p < 0.003; §4.4).
- **False alarms.** At the observed base rate, the best model raises about **4.3 false alarms per genuine catch** (§4.4). S1 §5.1 quotes "about 8" from the workshop version. Either number supports O5.

**Where the failures live.**
- Two items held 71% of all TM cases: (−8)−(−5) and A/10 = 9/15. For those particular numbers, a common wrong rule happens to give the right answer (§4.1, Table 1).
- Remove those two items, and the gap between procedural and conceptual items disappears (odds ratio 5.6 → 1.0; §4.2).
- In the authors' words, the trap is "item-driven, not category-driven". They cite Barton's design rule: "it should not be possible to answer the question correctly whilst still holding a key misconception."
- Exploratory attribution analysis: the TM cases the model missed weighted the answer more heavily relative to the explanation (ratio 1.19 vs 0.68; §4.4).

**Strength: moderate.** Real student data at scale, and honest intervals. Against that: a small TM test set (61), 15 questions, one researcher classifying items, unreported annotation reliability, and single runs at temperature 0.

**What LearnLoop already has.**
- Correct answers are not diagnosed live (S1 O5).
- The blind grader may ask one clarification about "a correct answer possibly reached by invalid reasoning".
- The persona gate applies Barton's rule to authored diagnostic items (ME §3.0).

**What is new.**
1. **The trap is in the items, and the gate covers only diagnostic items.**
   - LearnLoop generates ordinary practice from one generator program per family (S2 §5.3). With known wrong rules for a facet (the registry's misconceptions, or a malrule library; MalruleLib is P0 in the "modeling incorrect student thinking" dialogue), the generator can pick instance numbers so that each wrong rule gives a wrong answer.
   - Verbatim textbook exercises cannot be rewritten (SRC S1). SRC §8.4's exercise discrimination screen can record "holder of H passes this exercise". The likelihoods should then treat a correct answer on that exercise as carrying no information about H. A generated twin with different numbers can supply the missing information.
2. **The EVSI calibration's response model should let holder success vary by item.**
   - The `evsi/calibration` branch fits a three-class latent model (knows / holds / unsure) to Eedi 2020 answers (`evsi_calibration/response_fit.py`).
   - This paper says a holder's chance of answering correctly is near zero on most items and high on a few. A single pooled holder-success parameter will be wrong both ways.
3. **Order of information in the grading prompt.** The blind grader is handed the deterministic `final_answer_check` ("never re-litigate it") along with the work. Given the paper's answer-anchoring result, this is worth an ablation (§6 C3).
4. **A free source of real hard cases.** If the inferred match holds, the MAP Kaggle rows labelled True_Misconception are real student explanations with correct answers and named misconceptions. They are maths, and they are real traces, as the Bitter Lesson sweep requires (§3). They are a ready gold-set cell for P2.

### 3.2 Confirming correct, missing the rest (arXiv 2605.16207)

Yasir, Li, Gilson, Tithi, Tian, Barnes (NC State). Preprint (the repository is named for BEA 2026). Already cited in PLAN §C as "valid alternative as a third outcome".

**Claim.** LLM feedback agents are nearly perfect on textbook-optimal steps and unreliable on the two cases that matter: valid but non-optimal steps, and wrong steps.

**Setup.**
- 516 proof states from 32 propositional-logic problems in a Discrete Maths tutor (§3.2).
- A knowledge graph enumerating every valid derivation gives exact ground truth (§3.3).
- Next steps came from LLM-simulated students and were then labelled optimal, valid-alternative or incorrect (§4.2).
- Seven models × three prompt conditions (§4.3):
  - a peer that sees only the correct next step;
  - a teacher that sees the full reference solution;
  - a judge that reviews the peer's feedback.

**Results** (Table 2; §6):
- Optimal-step F1 was 0.94–0.99 for every model.
- Valid-alternative F1 ranged from 0.00 to 0.76. **Over-rejection of valid steps ran from 13% (Gemini 1.5 Pro) to 91% (Llama-3.3-70B).**
- Incorrect-step F1 ranged from 0.04 to 0.55. **Over-acceptance of wrong steps ran from 7% to 71%.**
- Models traded one error for the other: those that over-rejected least over-accepted most.
- **Model choice explained more than 95% of the variance; prompt condition less than 1%** (§6.2).
- Showing the full reference solution did not help.
- The judge-of-the-peer loop "did not consistently improve feedback quality" and sometimes passed the peer's errors along (§6.3).
- The authors read the failures as models "relying on surface alignment with the provided solution context rather than reasoning validity" (§7).

**Strength: moderate for the pattern, weak for the numbers.** Exact ground truth is a real strength. Against it:
- the student steps are simulated, not real;
- single runs at temperature 0;
- unfilled placeholders and inconsistent Ns;
- the annotators are co-authors;
- the models are dated (no GPT-5-class grader).

**What LearnLoop already has:**
- the valid-alternative path, which exists because of 2608.28725's 75–85% false rejection (S2 §5.5);
- "one high-effort pass; no voting, juries, or debate", which this paper supports: the judge loop didn't help;
- stronger models for evaluation roles.

**What is new.**
1. **The gate stops at machine-checkable answers.** The path switches on only when the final answer verifies by CAS, exact key or execution (S2 §5.5; `apply_valid_alternative_gate` returns early unless `matches_reference`). This paper's setting, multi-route proofs, is exactly what falls outside it. The E1 valid-alternative probe also uses only "CAS/sympy or the exact key" alternatives (S1 §13), so it cannot see this gap. See §6 C1.
2. **Over-rejection and over-acceptance trade off.** Any valid-alternative fix has to be measured on both at once, per model.
3. **Model choice dominates prompt work, by about two orders of magnitude here.** Per-route model selection, measured on a LearnLoop gold set, is the main lever (P2).
4. **The reference did not help on multi-route items, and may anchor.** This sits uneasily with "a verified reference is the grader's main input" (S2 §5.5, citing 2608.17938). See §6 C2.

### 3.3 Modernizing ground truth (arXiv 2603.29141)

Thomas, Borchers, Vanacore, Kizilcec, Koedinger (CMU / Cornell). A position paper with no new experiments.

**Claim.** In AI-in-education work, a single agreement coefficient (Cohen's κ > 0.8) is misused as proof that labels are right. The paper proposes four shifts:
1. Treat agreement as a diagnostic that shows *where* raters disagree, not as a pass mark (§4.1).
2. Report raters, codebooks and how disagreements were resolved (§4.2).
3. Audit LLM annotators and judges (§4.3) for:
   - circular validation, where one AI checks another;
   - authority, beauty and position bias;
   - being "right for the wrong reasons".
4. Add validity evidence (§4.4): predictive validity against later outcomes, and close-the-loop evidence that acting on the labels helps learners.

Cited numbers (Table 1): LLM vs expert κ was 0.38–0.58 on classroom talk moves. Multimodal LLM grading of handwritten work reached κ 0.90 on arithmetic but about 0.47 on illustrations. In the authors' words: "Matching a human coder does not mean the AI is 'right'" (Table 3).

**Strength.** An argument backed by cited evidence. The recommendations are standard measurement practice.

**Transfer: high.** LearnLoop already avoids "κ as a pass mark" in spirit:
- E1 has no thresholds and reports noise floors (S1 §13);
- PLAN §D says "do not count multiple LLM judges as independent evidence";
- adjudications and the scoreboard keep numerators, denominators and availability.

The missing piece is **predictive validity**. Does a diagnosis written today predict the *shape* of the learner's next cold error on that facet better than the facet's base rates? That turns the diagnoser's quality from "agrees with a stronger LLM" into "predicts this learner" (R1, P5).

The paper's "alternative annotator test" (an LLM against at least three humans on 50–100 items) cannot be run at n=1, because there is one human. The realistic panel is the owner's own adjudications plus a model from a different family.

### 3.4 RankCert: when simulated learners can choose a tutor (arXiv 2609.26069)

Kadir (SUTD). Preprint, single author.

**Claim.** Simulators that fit learner data equally well can disagree about which tutoring policy is best. Choose a policy from simulation only when it wins robustly across simulator families; otherwise abstain.

**Setup.**
- Five simulator families: BKT-like, PFA, dynamic IRT, attentive-history and causal-threshold.
- All were calibrated on an EdNet-KT1 derivative (5,000 learners, 590k responses).
- Each had to pass an adequacy gate: AUC ≥ 0.55, NLL gain ≥ 0.002, ECE ≤ 0.08 (§3.2, §6).
- Eight candidate policies were compared in 1,280 held-out settings, rotating which family played the "true" learner (§5).

**Results.**
- At the minimum domain, families agreed on the best policy in about **27%** of cases (H1, §8.2).
- How well a family predicted responses **barely predicted** whether it ranked policies correctly (Kendall τ = 0.14; H4).
- More simulated learners reduced noise but not the disagreement between families (H2).
- RankCert certified a winner in only 3.75% of settings, all of them "stable" scenarios with large cohorts (§8.4).
- It lowered total decision loss compared with taking the winner of one simulator (H3).
- It did not beat a simpler confidence-gated selector on selective risk (H5, p = 0.93). Its advantage holds only at the chosen abstention cost (§8.7).

**Strength: moderate.** Careful, pre-declared hypotheses and honest negative results. Against that: the oracle is synthetic, there are no human learners, the abstention cost and utility scale were designed for this benchmark, and the author discloses AI-assisted drafting.

**Transfer: high, and timely.**
- **What the branch does.** `evsi/calibration` fits one response-model family, the latent-class EM in `response_fit.py`. Under it, the branch compares the policies `evsi`, `eig`, `caps`, `random`, `max_entropy` and variants, and sweeps `PERTURBATION_DELTA`, `ROBUST_QUANTILE`, `VALUE_PER_NAT_MINUTES` and others.
- **What RankCert says about that.** Fit quality does not license a ranking. A result such as "EVSI beats caps by X minutes" or "the best ROBUST_QUANTILE is Y" is a statement about that one family.
- **The proposal.** Run the same comparison under at least three structurally different simulators, and report a ranking or parameter as supported only if it holds under all of them (R3). Candidates:
  - the existing Eedi latent-class family;
  - an IRT nominal-response family fitted to the same Eedi answers;
  - the planted-state student (`sim/student.py`).
- **Consistent with existing rules.**
  - EVSI already applies this logic one level down: it evaluates over a credible set of grader likelihood matrices and abstains if the winner flips (`scheduling/evsi.py`).
  - PLAN invariant 10 already forbids personas from calibrating human quantities. That rule concerns *which* data calibrate; RankCert concerns *how many model structures* a decision must survive.

### 3.5 Learner-chosen practice and system constraints (arXiv 2605.21613)

Noh, Chowdhary, Ooge, Aleven, Borchers (NYU / CMU / Utrecht). Preprint.

**Claim.** When learners choose which skill to practise, risk-averse choosers over-practise badly. Constraints that *bound* the choice, without removing it, fix most of this.

**Evidence.**
- **The simulation.** 1,000 simulated learners per condition, with an AFM response model and BKT mastery updates. Both were fitted to two DataShop data sets, equation solving and graph interpretation, from 261 students in total (§3.1–3.2).
- **Strategies.** Eight fixed choice strategies (§3.4).
- **Without constraints.** The risk-averse "minimise worst-case loss" strategy over-practised already-mastered skills by about 30 opportunities (30.3 and 28.9). Every other strategy came in at about 2–3 (§4.1).
- **With constraints.** Limiting the menu to the skills closest to mastery cut it to 1.8 and 3.2 (Cohen's d ≈ 1.9). "Prefer harder problems" also worked (§4.2).

**Strength: weak to moderate.** The conclusions hold only if AFM and BKT describe the learners. The models were fitted on the same data used to evaluate them, overpractice is the only outcome, and strategies never change.

**Transfer: moderate.**
- **LearnLoop's current stance.** The learner's pick always wins and carries no propensity (ROUTER §7). The UX doc avoids "homework" framing (S15).
- **What the paper predicts.** The owner, choosing under uncertainty, will drift toward already-demonstrated material.
- **How LearnLoop already pushes back.** Lifting count caps onto value of information already down-values that material in the plan: an already-demonstrated item has low information and a low expected gain.
- **The missing piece is the moment of choice.** At that moment, show a quiet one-line value hint and order the learner's own picks by value, without blocking (P6). This is "details on demand", and it heeds the paper's own warning that "overly prominent system constraints may undermine student autonomy perceptions" (§5.2).

### 3.6 Study-strategy clusters track engagement, not mastery (arXiv 2608.16963)

Lyu, Li, Yang. Preprint (it mentions LAK27).

**Claim.** Clusters of study behaviour (how much video, reading, revising, or studying before answering) describe engagement, not knowledge.

**Evidence.**
- **Data and clusters.** EdNet-KT3 (TOEIC prep), 5,000 active learners. Nine behaviour features formed eight stable styles (bootstrap ARI 0.94; §3–4.2).
- **The test.** Features came from each learner's first half and outcomes from the second half (§3.3, Table 5).
- **What early clusters explained:**
  - late persistence, η² = 0.106;
  - completion, η² = 0.021;
  - **late unassisted accuracy, essentially none: η² = 0.003, not significant after Holm correction.**
- **Two independence checks:**
  - clusters built on activity volume alone did not line up with the styles (ARI 0.064);
  - a knowledge-tracing probe found its own learner clusters, independent of the styles (ARI 0.007; §4.6).

**Strength: moderate.** A large sample, a split that avoids leakage, and multiple-comparison control. Against that: one platform (English test prep), active users only, and an in-app proxy for mastery.

**Transfer: confirms.** This is direct evidence for "reading is not evidence" and for RW's signal firewall:
- dwell, scrolling and highlights are `salience_only` (RW §2);
- interaction signals "steer routing, never the record" (FIELD §3.1).

**New use.** The same telemetry *does* predict engagement, so it belongs to:
- plan sizing, through DL Q12 (per-item time estimates);
- re-entry;
- the engagement term the Bitter Lesson sweep took from MaiMemo (§5).

### 3.7 Warning about AI fallibility increases help-seeking (arXiv 2606.03822)

Nagashima, Hladký, Rief (Saarland). Preprint. Already cited in EIG §18.

**Claim.** A one-line warning that the tutor's agent "can make mistakes" made students ask for more hints.

**Setup.**
- 252 seventh-graders analysed, in seven classes with one teacher, practising linear systems in a CTAT tutor for about 30 minutes (§2).
- About 12 students per class saw "Maddox can make mistakes, so be careful to read his messages thoughtfully". The rest saw "Please read Maddox's messages carefully!"
- The agent never actually erred (§2.2).

**Results** (§3, Table 1):
- Hint requests per step: 1.09 vs 0.75 (p = .02).
- No difference in errors (p = .61) or time (p = .39).
- Post-tests were mostly lost to class cancellations. There are no learning, trust or help-quality measures.

**Strength: weak.**
- The degrees of freedom don't match the sample.
- Class clustering is not modelled.
- Only one of three outcomes reached significance.

**Transfer: low.** The owner built the system and knows the judges err, so a generic warning tells him nothing. LearnLoop already shows claim-level honest labels: "possible cause — not yet checked", "answer key not verified", `provisional_pending_clarification`, verified/uncertain/unverified, and the `doesnt_fit` contest.

What carries over is the mechanism: telling learners the judge can be wrong shifts them toward checking. That matters for a tester or a second user. The version worth having is *specific*, placed next to a grade that really is low-confidence, and it already exists.

**Implication.** No change. Optionally, measure whether those labels change contest and verification behaviour (R8, low priority).

### 3.8 Practitioner-led "micro-randomised" trials of an AI tutor (arXiv 2609.14789)

Harrison, Khowaja, Dobson, Uwimpuhwe, Higgins (What Worked Education / Durham). Preprint.

**Correction to the title.** This is **not** a micro-randomised trial in the technical sense of repeated randomisation at decision points within one person. Each student was randomised *once*, to the Medly AI tutor or to self-directed revision, for four weeks (§2.2–2.3).

**Evidence.**
- 929 GCSE science students were pre-tested and 644 post-tested. Attrition was 30.7% (27.7% vs 33.2% by arm).
- The effect was **g = 0.33 (95% CI 0.18–0.48)** on a curriculum-aligned post-test, which was AI-marked and teacher-amendable (§3.2).
- More questions answered went with higher scores (0.18 marks per question). The authors call this associational only (§3.5).
- Medly commissioned and funded the evaluation.

**Strength.** Moderate for "an LLM tutor for written exam answers beat business-as-usual revision over four weeks". Weak for anything about *which features* matter, because no feature was randomised.

**Transfer: low.** LearnLoop already runs the real within-person version (`randomization_layer.py`; ROUTER §7, §10), and CLM §7 already ranks a within-learner randomised contrast as its highest evidence grade.

The paper's other lessons are useful as hygiene: record the exact version and intent under test (§4.2), keep randomised comparisons at the causal centre (§4.3), and accumulate small trials with forest plots (§4.4). At n=1 that means keeping randomised contrasts tagged by algorithm version and pooling only across versions that did not touch the contrast. Before/after comparisons across versions are confounded with the learner's own change over time (R7).

### 3.9 The missing evaluation axis: does feedback get used? (arXiv 2605.05648)

Niousha, Boatright Smith, Akram, Brusilovsky, Hellas, Leinonen, DeNero, Norouzi (UC Berkeley et al.). Preprint.

**Claim.** AI tutor feedback should be judged partly by what students *do* with it, not only by rubric scores of the message.

**Setup.**
- 10,235 failed-test submissions in UC Berkeley's CS61A over two semesters.
- Two tutors were compared: a baseline GPT-4 tutor, and a "misconception-first" tutor that picks a misconception from an instructor list before writing feedback (§3.1–3.2).
- Uptake was measured by a GPT-4.1 judge (κ against humans 0.67–1.00, on 20 interactions; §3.3):
  - *RelScore*: the share of feedback sentences that shaped the next code edit;
  - *SuccScore*: the share of those whose suggested change was applied correctly.

**Results.**
- The misconception-first tutor had higher RelScore in all five assignments (for example 84.9 vs 64.0), and higher SuccScore in two (§4.2).
- **Messages that revealed the answer produced more successful edits** (79.4% vs 53.0%), in other words copying (§4.3).
- Neither uptake nor rubric quality predicted students' helpfulness ratings beyond pseudo-R² 0.01 (§4.4).
- Tutor and semester are fully confounded, and there are no learning outcomes.

**Strength: weak to moderate.** Large, but observational and confounded.

**Transfer: moderate.**
- **LearnLoop already guards against the copying confound.** The reveal ledger and coldness receipts (`answer_leakage`, `unassisted` and `retrieval_delay` in `attempts/coldness_receipt.py`) exist so that immediate success after a reveal is never read as learning.
- **The new piece is a per-message uptake label.** Did the next attempt use this hint or feedback? Pair it with that facet's next cold outcome. That separates feedback that is used and sticks, used and fades, or ignored. It belongs in RW2c's "what helps" record, and could be written as a `judgment_ledger` task (P8).

### 3.10 From explanation to diagnosis: a video coach with misstep awareness (arXiv 2606.02970)

Jin, Dass, Goel (Georgia Tech). AIED 2026 workshop.

**Claim.** Ivy is a coach that sits beside course videos in Georgia Tech's OMSCS Knowledge-Based AI course. It gives better feedback on quiz errors once each wrong option has an instructor-written record (§3.2) giving:
- the error type: execution slip, conceptual gap, causal misunderstanding or teleological error (§3.3);
- where the error sits in the procedure;
- the belief behind it;
- how to scaffold it.

**Evidence.**
- 9 questions, with 22 or 38 wrong-answer cases (the paper is inconsistent).
- Expert ratings on a 0–2 scale (§5.2, Table 3):

  | Dimension | Before | After |
  |---|---|---|
  | Targeting | 0.95 | 1.50 |
  | Actionability | 0.47 | 1.32 |
  | Transferability | 0.55 | 1.32 |
  | Scaffolding | 0.71 | 1.42 |

- Accuracy did not change significantly.
- No rater count or agreement, no learner outcomes, and every submission is diagnosed independently, with no history.

**Strength: weak** (proof of concept).

**Transfer: low.** LearnLoop is past this design:
- discrimination profiles are the per-option records;
- failure-triage routes map each reason to its first intervention (`diagnosis/failure_triage.py`);
- the diagnoser reads history, which Ivy lists as future work (§7);
- SRC reads each misconception's `correction_source_span_ids`, which corresponds to Ivy's link from the diagnosis to the right place in the source.

**One small idea.** The "teleological error" means knowing the steps but not what they are for. Example: "I can run Gram–Schmidt but can't say why the result is orthogonal". LearnLoop's built-in error types (`arithmetic_slip`, `conceptual_slip`, `procedure_misapplication`, `recall_failure`, `scaffold_failure`, `incomplete_answer`) do not name it. The EIG templates `recall_without_mechanism` and `procedure_without_selection` sit close *(inferred overlap)*. Check that overlap before adding anything (P10).

### 3.11 Also read in full: MC-CPO, engagement without mastery (arXiv 2604.04251; companion 2604.04237)

Olukola, Rahimi. Listed for *Computers & Education: AI*.

**What it claims.**
- It defines an "engagement-without-mastery" event: a correct answer with no platform mastery upgrade. Such events made up 26.5% of analysed Junyi interactions and 3.1% of XES3G5M interactions (§6.4.2).
- It then constrains an engagement-rewarded RL tutor so that it may only take actions whose prerequisites are mastered. It reports +18.3% and +54.0% simulated mastery gain (Table 8).

**Strength: weak.**
- Evaluation is in simulation only.
- The event definition is circular on XES3G5M, where mastery is itself estimated from correctness.
- The baselines are thin.

**What transfers.** A warning, not a method: a policy rewarded on success or engagement learns to farm easy wins. LearnLoop's objective sits on the right side of that line:
- the outcome contract S = 0.75 R_cold + 0.25 R_next;
- a false-remediation ceiling;
- minutes-denominated EVSI.

Keep it there (§6 C7).

### 3.12 Also read in full: self-efficacy and favourability, tutor vs paper (arXiv 2606.17470)

Cen, Aleven, Koedinger, Borchers, Carvalho. EC-TEL 2026.

**Evidence.** A within-subject crossover with 97 ninth-graders, 54 of them analysed.
- Tutor practice beat paper practice on average (p = .02).
- Students with lower self-efficacy gained more in both formats.
- A three-way interaction suggests that how favourably a student views each format matters for low-self-efficacy students.

**Strength: weak.** Small and short.

**Transfer: minor.** Textbook exercises worked on paper lose step-level feedback. The planned photo capture (`spec_image_dropin_ingest.md`) turns paper work back into graded, diagnosable evidence, and that matters more once canonical-source practice (SRC S1) ships.

---

## 4. Product directions (ranked)

Ranked by return on effort for one learner, given what is already built.

| # | Direction | What the learner experiences differently | Where it fits | Size | ROI |
|---|---|---|---|---|---|
| P1 | **Valid-alternative protection for proofs and explanations** | A correct proof by a different route is judged on its own logic. It is marked down only where the grader quotes a concrete error; otherwise the criterion is unassessed, not failed | S2 §5.5 PF-c; the next blind grading prompt version; `apply_valid_alternative_gate` | S | **High** |
| P2 | **Gold set of hard grading cases, with over-rejection and over-acceptance measured per judge route** | Fewer wrong grades. Model and prompt choices per route are backed by numbers from the owner's own subjects | S1 §13 E1 (extends its probes); `judgment_ledger`; `diagnosis_adjudications` | S–M | **High** |
| P3 | **Coincidence-aware items** | A correct answer means more, and misconceptions surface sooner. A textbook exercise that a wrong rule passes is paired with a twin | PF generator programs (S2 §5.3); SRC §8.4 exercise discrimination screen; ME §3.0 persona gate; EVSI-cal response model | M | **High** |
| P4 | **Confidence arms (`+confidence_tap`, `+hedge`) and a reliability/resolution split in the calibration duel** | Nothing until an arm wins. Then better P(success), so better due dates and plan sizes. On demand: calibration by topic, never as a trait | FIELD §7.2 harness; PLAN §F; `goals/exam_calibration.py` | S | Medium–high |
| P5 | **Diagnosis forecast receipts** | Diagnoses that don't predict this learner lose weight. "Possible cause" can show a track record on demand | S1 §5 and §13; B5 scoreboard; `judgment_ledger` | M | Medium–high |
| P6 | **Value at the point of choice** | Picking something off-plan shows one quiet line, such as "already shown; cold check due in 9 days". The learner's own picks are ordered by value and never blocked | DL2 (intent); UX doc S15; ROUTER §7 (the learner's pick wins) | S | Medium |
| P7 | **Adaptivity audit** | Indirect. The owner can see whether the router adapts and whether served difficulty stays in band | ROUTER §10 reports over R1 `router_decisions` and DL1 block logs | S | Medium |
| P8 | **Feedback uptake label** | Hints and feedback that go unused, or get used and then fade, are retired sooner | RW2c "what helps" record; `judgment_ledger` | S | Medium–low |
| P9 | **Correctness check for Reader answers** | Fewer confidently wrong Guide and Ask answers | RW §15 evaluation | S | Medium–low |
| P10 | **"What is this for?" hypothesis** (teleological error) | When the steps are right but the learner can't say why they work, the repair is a passage on purpose, not more drills | EIG hypothesis templates; failure-triage routes | S | Low (check overlap first) |

### P1. Valid-alternative protection for proofs and explanations

**Why.** 2605.16207 measured 13–91% over-rejection of valid non-optimal proof steps, and the Bitter Lesson sweep already cites 2608.28725 at 75–85% false rejection of non-canonical traces.

LearnLoop's remedy only fires on `matches_reference`. `final_answer_check` returns one of five statuses: `no_reference`, `no_conclusion`, `matches_reference`, `undecidable` and `differs_from_reference` (`attempts/answer_check.py`). A proof or "explain why" answer will usually be `undecidable` or `no_conclusion`. The gate then returns unchanged, and the prompt's re-derivation rule, which is worded for `matches_reference`, does not apply.

A crude count over the two working vaults' item YAML (read-only, 2026-10-13):
- linear algebra: 19 of 99 prompts ask to prove, show, justify, explain why or derive;
- probability: 36 of 78; none of its 78 expected answers is shorter than 40 characters.

*This is a keyword proxy.* The real share should be measured by counting `final_answer_check` statuses on graded attempts.

**What.** When `route_check.divergent_route` is true and the status is anything other than `differs_from_reference`, the grader must re-derive the learner's route and may mark a criterion down only on a located, quoted error. Otherwise the criterion is `unverified`, which already means unassessed.
- The deterministic gate gains a second trigger: divergent route + non-verifiable conclusion.
- Over-acceptance is held in check because a located error still counts, and a proof that skips a needed step can be cited at the skip ("missing_required_step" against a trace checkpoint).

**Cost.**
- One prompt-version bump and a gate change with fail-first tests.
- A calibration-identity bump (S1 §4.3).
- No new decision parameter.

**Risk.** More `unverified` criteria means less evidence per proof attempt. That is the honest outcome when the grader cannot tell, and it matches the owner's 2026-10-12 ruling on unassessed criteria.

### P2. Hard-case gold set, both error rates, per judge route

**What.** A small, fixed set of real or reference-checked traces across four cells:
1. **Valid alternative, checkable answer.** This is E1's existing probe.
2. **Valid alternative, proof or explanation.** New. Sources: the owner's own adjudicated proofs, plus frontier-written alternatives checked by the owner.
3. **Correct answer, flawed reasoning.** New. Sources: the MAP Kaggle `True_Misconception` rows *(inferred availability)*, plus the owner's own cases found by R5.
4. **Wrong answer that looks fluent.** New. This measures over-acceptance.

**Report.** Over-rejection and over-acceptance *together*, per judge route and model, with E1's noise floor. Cells 3 and 4 come from real traces, as the Bitter Lesson rule "validate the grader only on real traces" requires.

**Also run two ablations from §6:**
- show the reference vs solve-first on cell 2 (C2);
- show the final-answer check early vs late on cell 3 (C3).

**Why first.** 2605.16207 found that model choice explains more than 95% of grading variance. LearnLoop has several judge routes with independent model choices (`config/schema.py`). This set is how to choose them.

**Size.** S–M: assembly plus a harness entry. Most of the machinery exists: E1, `learnloop diagnose review` and `judgment_ledger`.

### P3. Coincidence-aware items

**What.** Three changes:
- **Generated practice.** When a family generator draws instance numbers, evaluate the facet's known wrong rules on them, and redraw if any wrong rule gives the correct answer. The wrong rules are deterministic malrules where they exist, or a persona simulation. This is Barton's rule as a generator constraint, and it costs no learner time.
- **Verbatim textbook exercises.** Record in SRC §8.4's discrimination screen which hypotheses' holders would *pass* the exercise. A correct answer there then carries no information against those hypotheses, which a likelihood-based EIG handles naturally. Offer a generated twin whose numbers break the coincidence when that hypothesis is live.
- **EVSI calibration.** Let holder success vary by item, at minimum split "coincidence items" from the rest, rather than fitting one pooled holder-success parameter (§3.1).

**Why.** The correct-answer trap is item-driven (2605.23925 §4.2). LearnLoop deliberately does not diagnose correct answers live (S1 O5). So the item side is the only cheap defence.

**Size.** M.

### P4. Confidence arms and calibration decomposition

**What.**
- Add prequential arms to `learnloop eval`, all offline and never active (G11):
  - `+confidence_tap`: a recalibrated logit offset from the 1–5 answer confidence, only where it was given;
  - `+hedge`: the grader's `learner_confidence`, as confident/hedged/absent from the learner's own text, which costs zero friction;
  - optionally `+dwell_before_answer`, which the weak paper found predicted overconfidence.
- Use the same one-parameter recalibration as the `llm_probability` "+recal" arms.
- In the calibration duel, report Brier as reliability − resolution + uncertainty for both learner and model.

**What not to do.**
- Do not show a calibration score or a trait label (RW §15).
- Do not add a mandatory tap. "Never add a step for the learner just to protect the model" (FD).

**Why.** 2606.28881 (weak) and the judgments-of-learning literature *(general background, not reviewed here)* both point the same way. The arms are the route EIG §7.1 anticipates, "until a calibrated model exists", and no one is building it.

**Size.** S.

### P5. Diagnosis forecast receipts

**What.** When the diagnoser writes a hypothesis on facet f, it also freezes a forecast. That is a distribution over the outcome of the next qualifying cold attempt on f: pass, a match to that hypothesis's discrimination profile, or another error. When the attempt is blind-graded, the receipt resolves and is scored by log loss against a baseline that sees only blind grades and base rates.

**Why.** It turns 2603.29141's predictive validity into a number LearnLoop can compute alone.
- It gives the M1 history arms (exact, hybrid kNN, full long context, snapshot) a criterion grounded in real outcomes, rather than planted cases and an LLM judge.
- It feeds the "possible cause" label with a track record.
- Cold outcomes still "never rewrite the original diagnosis" (DV §3.8). The receipt is a separate record.

**Size.** M: a new RAW_LEDGER table, a writer at diagnosis time, a resolver at blind-grade time, and a report.

### P6. Value at the point of choice

**What.** When the learner picks a block or item off-plan, show a quiet line on demand. It covers, for example:
- whether the material is already demonstrated, and when the next cold check is due;
- the expected value per minute relative to the plan's top offer.

Order the learner's own picks by value. Never block, and never add a confirmation.

**Why.** 2605.21613 predicts risk-averse comfort practice when choice is unguided. Its remedy, bounding without removing, fits "frictionless defaults, details on demand".

**Size.** S. It reuses DL1's logged candidate sets and the plan's value.

### P7. Adaptivity audit

**What.** A weekly report, with one panel per lane:
- served items' predicted P(success) against the learner's ability state, the "behaviour policy" of 2606.23015 §3.3;
- the target band, `practice_success_band = (0.70, 0.85)`;
- the realised success.

A flat or off-band curve is a bug report. It needs no new data.

**Size.** S.

### P8. Feedback uptake label

**What.** For each hint or feedback message, an LLM-judged label: was it used in the next attempt? Joined to the facet's next cold outcome. It goes in RW2c's "what helps" record.

**Size.** S.

### P9. Correctness check for Reader answers

**What.** Sample Guide and Ask answers and check their claims against the cited spans, scoring correctness rather than retrieval relevance. KITE's grounding scores of 0.85–0.94 sat beside a factual-correctness score of 0.45 (2605.12988 §5.1).

**Size.** S.

### P10. "What is this for?" hypothesis

**What.** Check whether the existing templates `recall_without_mechanism` and `procedure_without_selection` already cover "can execute, can't say why". If they don't, add a hypothesis whose first intervention is a Reader passage on purpose (2606.02970 §3.3).

**Size.** S.

### Ideas from these papers we recommend *not* adopting

| Idea | Paper | Why not |
|---|---|---|
| Rasch "flow" reward; offline policy learning | 2606.23015 | An engagement proxy; needs thousands of learners |
| BKT, Bayesian or not | 2605.23048 | A step back from the 2PL EKF; no predictive gain |
| Judge-of-judge loops, juries | 2605.16207 §6.3; 2604.07883 | Didn't help; already rejected (S2 §5.5) |
| A generic "AI can make mistakes" banner | 2606.03822 | The owner knows; specific labels already exist |
| Keyword intent classification; RAGAs as the quality bar | 2605.12988 | The Decider is better; grounding ≠ correctness |
| PEDI index, LightGBM pipelines | 2606.28881 | No value at n=1 |
| Fine-tuned remediation tutors | 2606.21502 | PLAN §H defers fine-tunes; the authors say evaluation is unreliable |
| Constrained RL over a prerequisite DAG | 2604.04251 | LearnLoop's constraint engine and value-based selection already cover this |
| Style or engagement clusters as learner state | 2608.16963 | They predict engagement, not knowledge |

---

## 5. Research directions LearnLoop is unusually placed to answer

LearnLoop has five things almost no ITS study has:
- one learner followed for months, so learner-level effects are not averaged away;
- exact logged propensities on randomised near-ties;
- receipts: coldness, judgment ledger, adjudications;
- a learner-blind grader whose grades can serve as a fixed instrument for the diagnoser;
- free-text maths derivations, not multiple choice.

The studies below exploit that. Each says what it would decide.

### R1. Do diagnoses predict this learner? (predictive validity at n=1)

- **Question.** Does a diagnosis on facet f improve the forecast of the next cold attempt's outcome *shape* (pass / profile match / other error) over a baseline that sees only blind grades?
- **Data.** P5's forecast receipts, resolved by blind grades. The coldness receipt guarantees each outcome is genuinely cold.
- **Analysis.**
  - Prequential log-loss difference per resolved receipt, with a clustered bootstrap by facet.
  - Separately per M1 history arm, run in shadow on the same attempts.
  - Pre-register the baseline and the minimum number of resolved receipts, about 40 at the owner's pace *(inferred)*.
- **Decides:**
  - which history mode the diagnoser uses (S1 §5.2: kNN goes live "only if it beats the `full` arm", and this is the criterion);
  - whether "possible cause" deserves more or less prominence.
- **Why it's novel.** Diagnosis papers validate against expert labels. 2603.29141 says that cannot establish rightness. A forecast scored against the same learner's later behaviour can.

### R2. Grader hard cases, both error rates, in the owner's subjects

- **Question.** In linear algebra and probability, how often do judges reject valid alternative proofs and accept fluent wrong ones? Does P1's re-derivation rule lower the first without raising the second? Do show-the-reference and show-the-final-answer-check anchor the grader?
- **Design.** P2's four cells, each case graded under arms crossing three factors:
  - with or without the extended re-derivation rule;
  - reference shown vs solve-first;
  - final-answer check shown early, or only after `local_analysis_md`;
  - × the candidate judge models.
- **Analysis.** Over-rejection and over-acceptance per arm and cell, with E1's repeat-run noise floor.
- **Decides:** C1, C2 and C3, and the model per judge route.
- **Cost.** Paid model calls, owner-run and spend-capped.

### R3. Do EVSI calibration results survive a change of simulator? (RankCert protocol)

- **Question.** Do the rankings and best settings found under the Eedi latent-class simulator hold under structurally different simulators? The rankings are `evsi` vs `eig` vs `caps`; the settings include `ROBUST_QUANTILE`, `PERTURBATION_DELTA` and `VALUE_PER_NAT_MINUTES`.
- **Design.**
  - Add at least two families, each fitted to the same Eedi 2020 answers where it can be: a nominal-response IRT family; the planted-state `sim/student.py`; optionally a BEAGLE-style persona family, in the stress role only (PLAN invariant 10).
  - Rotate which family plays "truth", as in 2609.26069 §5. Report top-1 agreement and regret across families.
  - Label a result "simulation-supported" only if it holds in every family. Otherwise label it "simulation-ambiguous" and keep the conservative default.
- **Decides.** Whether simulation can justify the cap-lift parameters, or whether they must wait for the live `voi_forecasts` report (EVSI-cal Part B; SRC §11.4).
- **Note.** The branch's own code comment expects that "in the fitted regime every value-based rule stops at once", because Eedi multiple choice is a weak instrument. If the families disagree on even that, the live report becomes the only calibration source.

### R4. The owner's confidence: signal, situation or trait?

- **Question.** Each of these is worth knowing in itself, and none is answerable from population studies:
  - Does the confidence tap, or the hedging the grader reads in the learner's text, reduce prequential log loss over the incumbent?
  - Is the owner's miscalibration explained by topic, item family, time since last seen or dwell, or is it a stable offset?
  - Does it shrink over months?
- **Data.** P4's arms; `answer_confidence`; the grader's `learner_confidence`; dwell from `interaction_events`.
- **Analysis.**
  - Prequential comparison as in FIELD §7.4.
  - A within-person variance decomposition by facet family and month, in the spirit of 2606.28881 §III-D but at n=1.
  - Trend in the reliability term of the Brier decomposition.
- **Decides.**
  - Whether confidence leaves "logged-only" (C4).
  - Whether a calibration view by topic is worth offering on demand.

### R5. How common are correct answers reached by flawed reasoning in the owner's maths?

- **Question.** What is the base rate in the owner's own free-text derivations? 2605.23925's ~2% comes from multiple choice with explanations.
- **Design.**
  - Set `diagnosis.correct_answer_sample_rate` above 0 in shadow, which S1 already allows, at roughly 5–10%.
  - The owner adjudicates the flagged cases plus a random sample of unflagged ones.
- **Decides.**
  - How much effort P3 deserves.
  - Whether O5 should stay at 0 for every route. A base rate near zero means O5 is free; a base rate near 5% means the item-side fix matters more.

### R6. Does behaviour predict mastery at n=1? (a pre-registered null test)

- **Question.** Beyond the incumbent's P(success), do Reader dwell, help level reached, Ask count or re-reading predict the next cold outcome?
- **Expectation.** No, from 2608.16963.
- **Why run it.**
  - A clean null permanently closes a tempting door for the Reader workbench.
  - A positive result would be a new n=1 finding. Even then it would be a routing signal only, under RW W1's firewall.
- **Analysis.** Prequential arms as in FIELD §7.2, with telemetry features read only from before the attempt.

### R7. Learner choice and router adaptivity over time

- **Questions.**
  - Do the owner's own off-plan picks realise lower S per minute than the plan's offers?
  - Are they skewed toward already-demonstrated material, as 2605.21613 predicts?
  - Does the router's served P(success) stay in band week to week (P7)?
- **Data.**
  - DL1's logged candidate sets and the learner's picks. Picks carry no propensity, so this comparison is observational and should be stratified by lane and state.
  - R1's `router_decisions`.
  - For causal claims, use only the ε near-tie randomisations already logged.
- **Also.** Keep randomised contrasts tagged by algorithm version, and pool only across versions that left the contrast untouched (the lesson of 2609.14789 §4.4).

### R8. Do specific uncertainty labels change verification behaviour? (low priority)

- **Question.** When a grade carries a specific uncertainty label, does the learner contest, open the evidence or re-check the source more often? This is the n=1 version of 2606.03822.
- **Design.** Mostly an observational association. A randomised version would vary the *wording* of labels among near-equivalent forms, which is safe because it never withholds information. It is worth doing only if a second user or tester appears.

---

## 6. Contradictions

Each entry states where the evidence contradicts or strains a current LearnLoop choice, and what to do.

**C1. The valid-alternative gate stops at machine-checkable answers. → CHANGE (P1), then measure (R2).**
- *LearnLoop:* the valid-alternative path runs only "when … the final answer verifies (CAS, exact key, or execution)" (S2 §5.5). In code, `apply_valid_alternative_gate` returns early unless the status is `matches_reference`.
- *Evidence:* LLM judges over-reject valid alternative proof steps 13–91% of the time; the reference solution does not fix it, and the judge loop does not either (2605.16207 Table 2, §6.2–6.3). This is consistent with 2608.28725's 75–85%, which LearnLoop already cites.
- *Why change rather than test first:* the remedy is the one LearnLoop already trusts for checkable answers. The proof-heavy working vaults suggest the gap is large.

**C2. "A verified reference is the grader's main input" (S2 §5.5, citing 2608.17938), for multi-route items. → TEST (R2).**
- *Evidence:* for multi-route proofs, giving judges the full reference solution did not change classification accuracy (condition η² < .01). The authors attribute the failures to "surface alignment with the provided solution context" (2605.16207 §6.2, §7).
- *Recommendation:*
  - **Keep** reference-first grading for items with a checkable answer; there, verification is real and 2608.17938 applies.
  - **Test** reference-shown vs solve-first on proof and explanation items in P2's cell 2.
  - If solve-first does no worse on over-rejection and no worse on over-acceptance, use it for multi-route items.

**C3. The grader sees `final_answer_check: matches_reference` alongside the work ("never re-litigate it"). → TEST (R2).**
- *Evidence:* models defaulting to "correct answer means correct reasoning". When final answers were correct, Gemini's detection of reasoning errors fell from 93.5% to 83% (PRM800K, p < 0.003). The attribution analysis is exploratory (2605.23925 §4.4).
- *Recommendation:*
  - Ablate on P2's cell 3: give the check to the deterministic gate and reveal it to the model only after `local_analysis_md`, or not at all.
  - **Keep** the current order unless the ablation shows a difference beyond E1's noise floor. The prompt already makes the grader write its local analysis first, which may be enough.

**C4. Confidence is "logged-only … until a calibrated model exists" (EIG §7.1; RW D22). → KEEP the rule; START the arm (P4, R4).**
- *Evidence:* pre-answer confidence as the dominant predictor of correctness (2606.28881; weak, n=27).
- *Recommendation:* this is a strain rather than a contradiction. The rule is sound: no unvalidated likelihood term. But nothing produces the "calibrated model" it waits for. The offline arms are G11-safe and cost little.

**C5. EVSI calibration compares policies and tunes parameters under one simulator family (`evsi/calibration`, uncommitted). → CHANGE the protocol (R3).**
- *Evidence:* simulator families that pass the same adequacy gate agree on the best policy only about 27% of the time, and fit barely predicts ranking agreement (2609.26069 H1, H4).
- *Recommendation:* add families before any simulation result is quoted as support for a parameter or for the cap-lift. Keep the work itself; it is the right work.

**C6. S1 §5.1 cites "about 8 false positives per true detection" for correct-answer diagnosis. → KEEP O5; update the citation.**
- *Evidence:* the arXiv version (2605.23925 §4.4) reports about 4.3 false alarms per genuine detection for its best model (Gemini 3 Flash). The figure "about 8" comes from the AIED'26 workshop version.
- *Recommendation:* both figures support not routing on correct-answer flags. Update the citation to the arXiv ID and add the paper's item-side remedy (P3).

**C7. Checked, no contradiction: the success band and the reward.**
- `practice_success_band = (0.70, 0.85)` steers generated-item difficulty. The router's reward is cold retrieval with a false-remediation ceiling, not immediate success.
- The "flow" reward (2606.23015) and the engagement-reward failure (2604.04251) both warn against *rewarding* success. LearnLoop does not. **Keep.**

**C8. Checked, tension only: "the learner's pick always wins and carries no propensity" (ROUTER §7).**
- 2605.21613 (a simulation) predicts that unguided choice drifts to comfort practice.
- The paper's own remedy bounds choice and does not override it, and it warns against prominent constraints.
- **Keep** the rule. Add P6 and measure (R7).

**Decisions these papers support (no change):**
- one grading pass, no juries (2605.16207 §6.3);
- population KT stays out of the loop (2605.23048's predictive null; 2605.04727 shows attention-KT gains shrinking under controlled protocols);
- the signal firewall (2608.16963);
- outcomes read at the next cold review rather than immediately (2605.05648 §4.3: revealed answers inflate immediate success);
- EVSI's abstain-on-flip rule (2609.26069).

---

## Appendix A. All 50 search results, triaged

Listing: arXiv search "Intelligent Tutoring Systems", all fields, newest announcements first, 50 per page, fetched 2026-10-13.

| Code | Meaning |
|---|---|
| **H** | Read in full in this sweep |
| M | Abstract-level, relevant |
| L | Little relevance |
| — | Not relevant |
| ★ | Already cited in LearnLoop docs |

| # | arXiv | Title (short) | Rel. | One line |
|---|---|---|---|---|
| 1 | 2609.36930 | NuPaD: GenAI framework for subatomic physics | L | A graduate course design: a textbook prepared for local AI parsing, plus companion files so the AI tutors instead of answering. No empirical results |
| 2 | 2609.26069 | RankCert: when can simulated learners select an AI tutor? | **H** | §3.4. Simulator families disagree on the best policy; certify only under agreement. Directly relevant to EVSI calibration |
| 3 | 2609.14789 | Practitioner-led micro-randomised trials, GCSE science | **H** | §3.8. Actually one randomisation per student; g = 0.33 vs revision; vendor-funded |
| 4 | 2609.08254 | CircuTutor: static circuit problems → dynamic tutoring | M | Textbook problems turned into interactive tutoring with misconception mapping and adaptive follow-ups. Same move as SRC S1; no sample size given |
| 5 | 2609.02611 | LLMs for emotional and reflective support in maths | L | Grade-7 algebra; "mindful" chat gave similar learning with less time and fewer hints; no significant learning difference |
| 6 | 2608.16963 | Study-strategy clusters track engagement, not mastery | **H** | §3.6. Confirms "reading is not evidence" |
| 7 | 2608.03524 | Dr. AGENTONOMICS | L | A RAG course tutor tech report; no evaluation |
| 8 | 2607.11417 | GenAI in lab learning: epistemic scaffolding | L | Qualitative, 7 students; argues for verification routines, as W2 already does |
| 9 | 2607.05412 | Bibliometric analysis, AI in STEM | — | Bibliometrics |
| 10 | 2606.30662 | ELEVATE: local-first GenAI avatar tutors | L | Local-first architecture with teacher governance; the avatars are irrelevant |
| 11 | 2606.28881 | UBP-CAP: prediction and metacognitive calibration | **H** | §2.3 (named by the owner). Confidence dominates prediction; weak evidence |
| 12 | 2606.23015 | Counterfactual learning of instructional policies | **H** | §2.2 (named by the owner). Behaviour-policy audit transfers; reward doesn't |
| 13 | 2606.21502 | Pedagogically aligned LLM tutors for maths mistake remediation | M | SFT + DPO on an open model, competitive with proprietary; "reliably evaluating tutoring quality remains difficult". Fine-tunes stay deferred (PLAN §H) |
| 14 | 2606.17470 | Self-efficacy and favourability, tutor vs paper | **H** (short) | §3.12. Small crossover; minor relevance to photo capture |
| 15 | 2606.15509 | Human–AI collaboration functions (Cukurova) | L | Conceptual taxonomy |
| 16 | 2606.14113 | Simulating students' Java errors with LLMs | M | LLM-made errors judged hard to tell from real ones (N = 401, unit unclear); harder problems give less student-like errors. Relevant to `persona_realism.py`; contrasts with 2602.01015 ("LLM students too coherent"). Java, not maths |
| 17 | 2606.09845 | PeteChat: a guardrailed "tutor, not solver" | L | Local Llama-3 + retrieval; design principles; no outcome data |
| 18 | 2606.03822 | Warning about AI fallibility increases help-seeking | **H** ★ | §3.7. Weak; transfer low |
| 19 | 2606.02970 | Video coach with misstep awareness | **H** | §3.10. LearnLoop is past this; "teleological error" idea only |
| 20 | 2606.02950 | Validating a unified data architecture for AI agents | L | Data-pipeline validation, 2.7M requests; privacy issues |
| 21 | 2606.01410 | What LLMs must forget to teach (Classical Japanese) | L | Prompted tools that avoid over-explaining; anecdotal. Echoes restraint |
| 22 | 2606.01020 | LFTutor: teaching logical fallacies Socratically | L | Beats plain LLMs on automatic and human ratings; different domain |
| 23 | 2605.30670 | RL for special education | L | Persona-aware reward, 690 dialogues; not applicable |
| 24 | 2605.23925 | The correct-answer trap | **H** ★ | §3.1. Item-driven trap; item-side fix; ~4.3 false alarms per catch |
| 25 | 2605.23048 | StanBKT | **H** | §2.1 (named by the owner). Estimator doesn't change prediction; uncertainty is the point |
| 26 | 2605.21962 | AI-enabled serious games (chapter) | — | Review chapter |
| 27 | 2605.21613 | Learners' task-selection strategies and constraints | **H** | §3.5. Risk-averse choice → overpractice; bound, don't block |
| 28 | 2605.18761 | Teacher/student co-orchestration of pairing | L | Classroom orchestration |
| 29 | 2605.17468 | Interpretable ITS for presentation training | L | 204 learners, 30 days, d = 0.39–0.90 pre/post; unrelated domain |
| 30 | 2605.17263 | Expert cognition dashboard | L | Conceptual, no evaluation |
| 31 | 2605.16207 | Confirming correct, missing the rest | **H** ★ | §3.2. Over-rejection and over-acceptance; model choice dominates; drives C1 and C2 |
| 32 | 2605.12988 | KITE: retrieval-augmented tutoring for algorithm tracing | **H** | §2.4 (named by the owner). Grounding ≠ correctness |
| 33 | 2605.12788 | Forecasting effort and progress in online learning | M | 425 middle-schoolers; feature models cut weekly practice-time and mastery forecast error 22–33% vs heuristics. Relevant to DL Q12 time estimates *(transfer inferred)* |
| 34 | 2605.05648 | The missing evaluation axis: 10,000 submissions | **H** | §3.9. Uptake labels; revealed answers inflate success |
| 35 | 2605.04816 | AI companions that prioritise learning over performance | L | Design framework; aligned with LearnLoop's stance |
| 36 | 2605.04727 | Reliability in programming KT: re-evaluation | M | Attention-KT gains shrink under controlled protocols and depend on sequence ordering. Supports PLAN §H; use strict temporal splits in any KT benchmark |
| 37 | 2604.24808 | ITAS: multi-agent LLM tutoring | L | 5-student pilot; system behaviour only |
| 38 | 2604.24807 | ITS for quantum education | L | The same system in another domain |
| 39 | 2604.24110 | Latency and cost of multi-agent tutoring | L | Priority pay-as-you-go stays under 4 s; relevant only to hint latency (RW D7) |
| 40 | 2604.21432 | One algorithm for restless and rested rotting bandits | M | RAW-UCB for arms whose value decays with their own use. Relevant only if PLAN §G's equipoise bandit runs; VOI recomputation already covers diminishing value per repetition *(inferred)* |
| 41 | 2604.16117 | SCRIPT: a programming ITS in a German university | L | Plug-in hint mechanisms; regulatory compliance |
| 42 | 2604.11373 | Minimal embodiment, number concepts in a robot | — | Robotics |
| 43 | 2604.08947 | MuTSE: evaluating text simplification | — | CEFR simplification tooling |
| 44 | 2604.08263 | Neural-symbolic knowledge tracing (Responsible-DKT) | L ★ | Already "skip" in the Synthesis (NSKT) |
| 45 | 2604.07883 | Agentic historical-bias detection in textbooks | L | A jury plus meta-agent; separating narrative from quoted sources cut false positives. Juries are rejected; "sources keep their identity" already covers the rest |
| 46 | 2604.04741 | AI and cost reduction in public higher education | — | Scoping review |
| 47 | 2604.04251 | MC-CPO: mastery-conditioned constrained policy optimisation | **H** (short) | §3.11. A warning against engagement rewards |
| 48 | 2604.04237 | Reward hacking in AI tutoring (RHSI) | M ★ | Simulation, 120 sessions: an engagement-optimised agent farms a low-mastery action; constraints cut RHSI from 0.317 to 0.102. Companion to #47 |
| 49 | 2603.29950 | Physiological synchrony in medical-team ITS | — | Four dyads; not relevant |
| 50 | 2603.29141 | Modernizing ground truth | **H** | §3.3. Predictive validity over agreement; drives P5 and R1 |

## Appendix B. Method and caveats

- **How papers were read.** Every paper marked H was fetched in full from its arXiv HTML page and read through a summarising fetch, with a prompt asking for method, data, results with exact numbers, limitations and threats to validity, by section. Numbers were checked for internal consistency where the papers report the same quantity twice. The inconsistencies found are noted in the entries: KITE's expert count; the "micro-randomised" title; StanBKT's "recovered" claim; CAT's 1.6% vs 2%. Before quoting a number in a decision, re-check it against the PDF.
- **Abstract-level entries.** Rows marked M, L or — in Appendix A rest on abstracts only.
- **LearnLoop baseline.** Built from main `f2f02e32`, from direct reads of the cited source files (`attempts/blind_grading.py`, `attempts/grading_support.py`, `attempts/answer_check.py`, `scheduling/evsi.py`, `scheduling/randomization_layer.py`, `goals/exam_calibration.py`, `content/authoring/persona_gate.py`, `field/*`), and from two read-only digests of the specs, brainstorming notes and in-flight worktrees. The in-flight branches are uncommitted and may change.
- **Vault counts.** The proof-share figures in §0 and P1 come from a keyword scan of the working vaults' practice-item YAML. SQLite was opened read-only and immutable; no fixture file was modified. They are a proxy, not a measurement of grading outcomes.
- **No paid API calls were made.**
