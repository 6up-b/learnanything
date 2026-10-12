# Bitter Lesson Research Sweep

*Compiled 2026-10-11 from six parallel literature sweeps on how to make LearnLoop more "bitter-lesson-pilled" in service of [[User intentions]] / [[LearnLoop_User_Intentions_v2]]. Applied to `docs/specs/spec_blind_grading_diagnosis_split_v1.md` (Slice 1) and `docs/specs/spec_embedding_consumers_v1.md` (Slice 2) on the same day; §10 maps citations to the edits.*

**What "bitter-lesson-pilled" means at n=1.** The scalable resource is frontier-model inference and verification compute, not learning from ~10³ graded events a year. So:
- spend more model compute per decision: longer context, solve-first grading, rollouts, generate-many-then-verify;
- take priors and candidate blocking from components pretrained on public data;
- keep a thin hand-built layer only where the evidence shows general models misbehave: over-assisting, leaking answers, rejecting valid alternatives, the synthetic-vs-real grading gap, and the identity of the retention target;
- build machinery that only *saves* model compute last.

**How the sweeps ran.**
- Six research agents covered six angles:
  1. long context vs retrieval;
  2. grading and verification;
  3. tutoring policy;
  4. retention;
  5. practice generation;
  6. learning with AI assistance.
- The arXiv API and arxiv.org search returned HTTP 429 for most of the session. Agents switched to web search, OpenAlex, Scry's arXiv catalog and the OSF API for discovery. Each agent then opened every paper it reported on its abs, HTML or PDF page, or for non-arXiv work on the journal, OSF or publisher page.
- **Coverage of July–October 2026 is incomplete.**

**Legend.**

| Tag | Meaning |
|---|---|
| `[pre]` | Preprint |
| `[PR: venue]` | Peer-reviewed or accepted, per the paper's comment field, DOI or proceedings page |
| ✔ | Abstract re-checked by Claude on 2026-10-11 (six papers) |
| A | Numbers as reported by the research agent that opened the page; not re-checked |
| FT | The number appears in the full text, not the abstract |
| ext | Not on arXiv (PsyArXiv, journal, working paper, report, or leaderboard) |

---

## 1. Long context, retrieval, and memory (the diagnoser's history)

**2603.04814**: *Beyond the Context Window: A Cost-Performance Analysis of Fact-Based Memory vs. Long-Context LLMs for Persistent Agents* (2026-03-05) `[pre]` ✔ (numbers FT)
- **Finding:** Mem0 (`text-embedding-3-small`, top-20) against full long context with GPT-5-mini:

  | Benchmark | Long context | Mem0 |
  |---|---|---|
  | LongMemEval (~101.6K tokens) | 82.4 | 49.0 |
  | LoCoMo | 92.85 | 57.68 |
  | PersonaMem v2 | 69.75 | 62.48 |

  A cached 100K-token turn costs about $0.0036. Mem0 only becomes cheaper after about 10 turns.
- **Use:** with a strong reader, full context wins on accuracy, and at LearnLoop's volume it costs a few dollars a year.

**2601.14287**: *Chain-of-Memory* (2026-01-14) `[pre]` A
- **Finding:** LongMemEval at ~105–115K tokens:

  | Setup | Score |
  |---|---|
  | Full context, Gemini-2.5-pro | 89.20 |
  | Oracle evidence only, GPT-4o-mini / Qwen3-32B | 80.2 / 81.8 |
  | Best memory system, same two models | 74.2 / 76.4 |
  | Turn-level RAG, same two models | 64.2 / 66.0 |
  | Full context, same two models | 55.8 / 55.2 |
- **Use:** reader strength matters more than retrieval design. Retrieval mainly rescues weak readers.

**2609.09664**: *PRAGMA: Personalized Guidance with Memory Alignment* (2026-09-09) `[PR: EMNLP 2026]` A
- **Finding:** guidance tasks over ~160K-token histories with GPT-5-mini:
  - Event-Align: full context 67, Dense-S 90, A-MEM 97.
  - Traj-Correct: full context 19, memory systems 32–42.
  - Corrective queries score 0–13 for every system.
  - The authors: "Full-Context remains ineffective."
- **Use:** this is the closest analogue to the diagnoser's job, and here selection helped. Only mid-size readers were tested. It is the main argument for an aggregation-capable arm (tools or sub-calls), not just raw long context.

**2608.25655**: *Reconstructing the Right Episode* (SCALE-QA / TSIM) (2026-08-26) `[PR: EMNLP 2026 Main]` A
- **Finding:**
  - GPT-4o-mini with full context drops from 62.5% at 16K tokens to 29.8% at 128K.
  - At the same scale, standard RAG scores 27.1, and a tuned BM25 + BGE + HyDE + RRF + MMR chunk pipeline scores 56.2. Episode-segmented memory scores 73.8.
  - At 1M tokens with Gemini 2.5 Flash: full context 87.2, episode memory 96.5 using about 1.3K tokens.
- **Use:** structure beats both raw long context and flat RRF chunk retrieval, which is close to the hybrid that Slice 1 planned. LearnLoop's typed traces already are episodes, so exact filters over them are the analogue of the winning method.

**2511.02817**: *Oolong* (2025-11-04) `[PR: COLM 2026]` A
- **Finding:** on aggregation tasks, GPT-5, Claude-Sonnet-4 and Gemini-2.5-Pro all score under 50% at 128K.
- **Use:** finding a pattern across many traces is an aggregation task. Single-pass long context is weak at it.

**2512.24601**: *Recursive Language Models* (2025-12-31) `[pre]` A
- **Finding (GPT-5):**
  - OOLONG-Pairs at 32K: plain 0.1 vs recursive 58.0.
  - OOLONG at 131K: plain 44.0, recursive 56.0, CodeAct + BM25 38.0.
- **Use:** the bitter-lesson fix for aggregation is test-time compute (code and sub-calls over the store), not embeddings. This motivates M1 arm (e).

**2605.12366**: *Classifier Context Rot* (2026-05-12) `[pre]` A
- **Finding:**
  - Needle recall for Opus 4.6 (thinking) is 99.7% at 100K tokens and 69% at 800K.
  - On MonitorBench, recall with an 800K benign prefix falls from 98.6 to 88.
  - Dangerous actions are missed 2–30× more often at 800K, across Opus 4.6, GPT 5.4 and Gemini 3.1.
- **Use:** cap the diagnoser's context at about 100K tokens.

**2510.05381**: *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval* (2025-10-06) `[PR: Findings of EMNLP 2025]` A
- **Finding:** performance drops 13.9–85% as input grows, even with perfect retrieval and with irrelevant tokens masked. Reciting the evidence first recovers up to 4% (GPT-4o on RULER).
- **Use:** filter hard. The diagnoser lists the trace ids it relies on before diagnosing (Slice 1 `evidence_attempt_ids`).

**2605.15184**: *Is Grep All You Need?* (2026-05-14) `[pre]` A
- **Finding (116 LongMemEval questions):**
  - With results delivered inline, grep beats vector search in all 10 harness × model pairs. For example, GPT-5.4 in Codex scores 93.1 vs 75.9.
  - With results delivered programmatically, vector search wins 5 of 10.
  - The harness moves results more than the retrieval method does: Haiku 4.5 scores 83.6 in one harness and 55.2 in another.
- **Use:** embedding kNN is not the main lever; exact or lexical tools and the harness are.

**2608.06305**: *READ* (structural navigation) `[pre]` A
- **Finding:** structural navigation 58.8% vs dense retrieval 15.7% (35.3% tuned). BM25 was statistically tied with structural navigation.
- **Use:** source search (Slice 2 T6) starts with FTS5 plus LLM query rewriting.

**2510.27246**: *BEAM* `[PR: ICLR 2026, per the PDF header]` A
- **Finding:**
  - At 100K tokens, RAG beat full context for 3 of 4 weaker or older models. For example, GPT-4.1-nano scored 0.309 with RAG vs 0.239 with full context.
  - At 10M tokens, full context collapsed to 0.104–0.133.
- **Use:** retrieval helps weak readers and enormous histories, neither of which is LearnLoop's regime.

**2508.14817**: *Retrieval vs long context on EHR records* `[PR: JAMIA]` A
- **Finding:**
  - Extraction: under 8K retrieved tokens beat long context by 0.17–9.83 F1.
  - Timelines: the two tied (−3.26 to +3.24 Jaccard).
- **Use:** retrieval wins on extraction tasks, not on reasoning over a timeline.

**2609.05339**: *Memory portability across embedding upgrades* `[pre]` A
- **Finding:**
  - After an embedding upgrade, a half re-embedded index regained 4.96 points; a full re-embed regained 11.90.
  - 81% of the RAG accuracy shortfall came from retrieval failures.
  - Recovery was possible in 34 of 48 cases, and only when the raw history had been kept.
- **Use:** vectors are a disposable cache over raw history. Fully re-embed on any model change.

## 2. Distillation and cost (the calibrator "flywheel")

**2605.14752**: *Cognitive-Uncertainty Guided Knowledge Distillation for … Student Misconceptions* (2026-05-14) `[PR: ACL 2026 Findings]` A
- **Finding:**
  - A distilled 4B student scores 84.38% vs GPT-5's 67.73% on a 220-item algebra set, with the full label list in the prompt.
  - It was trained on MAP-Charting: 36,695 samples and a closed label set.
- **Use:** distillation wins with about 10⁴ labels and a closed label set. LearnLoop has about 10³ events a year, and new material is always unseen.

**2606.28823**: *Labeling Training Data for Entity Matching Using LLMs* (2026-06-27) `[pre]` A
- **Finding:**
  - LLM labelling costs $5.86–$8.11 per training set, and the distilled students are 34–459× faster.
  - But the students "substantially underperform their teachers" when many items are unseen.
- **Use:** argues against calibrators that skip the LLM on open-world identity tasks.

**2511.23455**: *The Price of Progress* (2025-11-28) `[pre]` A
- **Finding:** the price of a fixed capability falls 5–10× a year. Running frontier models costs 3–18× more each year.
- **Use:** machinery that saves LLM calls depreciates quickly.

**2603.28576**: *Tiered Super-Moore's Law* (2026-03-30) `[pre]` A
- **Finding:**
  - Token prices fell about 600× from 2020 to 2026.
  - Price half-lives: 1.10 years for the economy tier, 1.55 years for the mid tier.
  - Flagship prices show no clear trend (R² = 0.031).

**2601.06007**: *Don't Break the Cache* (2026-01-09) `[pre]` A
- **Finding:** prompt caching cuts cost by 41–80% and time-to-first-token by 13–31%, but only when dynamic content goes at the end of the prompt.
- **Use:** in the full-history diagnosis context, the stable history goes first and the current attempt last.

## 3. Grading and verification

**2606.10254**: *RealMath-Eval: Why SOTA Judges Struggle with Real Human Reasoning* (2026-06-08) `[pre]` ✔
- **Finding:** 224 real high-school exam responses, with a reference solution and a stepwise rubric.
  - Judge MSE on real responses is 2.96, vs about 1.2 on synthetic ones. The abstract gives about 1.17; the agent read 1.24 for Gemini 3 Pro in the full text.
  - GPT-5.2: 5.28 vs 2.55 (A).
  - Changing only the surface style of the synthetic responses does not close the gap.
  - Multi-agent self-consistency moved exact match only from 37.7% to 38.8% (FT).
- **Use:**
  - A grader validated on synthetic anchors will look better than it is on the owner's real answers.
  - Validate the grader only on real traces.
  - Synthetic anchor sets are not built by default (Slice 2 §5.5).

**2608.17938**: *Grading Needs a Rubric, Not Intelligence* (2026-08-18) `[pre]` ✔
- **Finding:** 3,456 grades over 24 questions.
  - Which answer was graded explained 95.6% of score variance; which judge, 0.2%.
  - Raising judge effort changed scores by at most 0.006.
  - Removing the rubric's criteria and levels had no measurable effect.
  - Removing the official answer dropped ICC from 0.888 to 0.628, inflated scores, and made judge effort matter again.
- **Use:**
  - Spend frontier compute once, at ingestion, on a *verified* reference.
  - Stop hand-tuning rubric criteria.
  - Caveat: the graded answers were model-written, so 2606.10254 applies.

**2608.28725**: *Beyond the Answer Key: Robustness Evaluation of LLMs for Step-Level Mathematical Verification* (2026-08-28) `[PR: ICMLA 2026]` A
- **Finding:**
  - Base models falsely rejected 75.6–85.3% of valid traces that differed from the canonical form.
  - SFT, distillation and test-time compute helped only some models, sometimes at a cost to canonical-form accuracy.
  - Only small models were tested: GPT-OSS-20B, Qwen3-14B, Phi-4-Reasoning.
- **Use:** a reference can bias the grader against a valid alternative. This motivates the valid-alternative path, the regression suite, and the Slice 1 E1 probe.

**2510.13744**: *Hard2Verify* (2025-10-15) `[pre]` A, FT
- **Finding:**
  - The best first-error identification was GPT-5 at 70.61 balanced accuracy; gpt-oss-120B scored 63.97.
  - Higher effort raised gpt-oss-120B's step-level F1 from 61.46 to 74.64.
  - Best-of-N majority voting "does not meaningfully improve."
- **Use:**
  - Use one high-effort pass, not voting.
  - First-divergence calls are contestable proposals.

**2509.01395**: *First-error localization in student solutions* `[PR: EMNLP 2025]` A
- **Finding:** even with the gold solution, the best model localizes the student's first error at only 64.07 (VtG) and 49.69 (PRM800K).
- **Use:** same as Hard2Verify.

**2607.05904**: *More Convincing, Not More Correct: Self-Play Reward Hacking of Reference-Free LLM Judges* (2026-07-07) `[pre]` A
- **Finding:**
  - Judge pass rate rose from 0.72 to 0.94 while true accuracy stayed at 0.20.
  - A strict three-judge ensemble still accepted 55% of wrong answers.
  - Having the judge solve the problem first cut false positives from 0.719 to 0.012.
- **Use:** solve-first grading for items without a reference: teach-back, project defense, open "why" items.

**2607.12885**: *Judges without references* (2026-07-14) `[pre]` A
- **Finding:** judges over-credit when no reference is given. Adding one flips up to 85% of decisions.

**2603.14732**: *LLM-as-a-judge validity is strongly task-dependent across physics assessment formats* (v1 2026-03-16, v3 2026-09-26) `[pre]` A
- **Finding:**
  - Structured questions: giving the official solution improved Claude Opus 4.5 from ρ 0.820 to 0.885 (fMAE 0.120 to 0.065). A false solution pushed fMAE to 0.249.
  - Essays: exemplar anchoring fixed the score level but not rank agreement (ρ 0.034).
  - The committee did not consistently beat the best single model.
- **Use:**
  - Verify every reference before use.
  - Anchors fix the score level, not discrimination.
  - No judge ensembles.

**2608.00004**: *Cost-Effective Automated Judging of Natural-Language Mathematical Proofs* (2026-05-29) `[PR: MATH-AI @ NeurIPS 2026]` A
- **Finding:**
  - With a reference proof, cheap judges matched frontier ones, and the consensus did not beat its best member (0.855 vs 0.875).
  - Precision / recall by decision rule:

    | Rule | Precision | Recall |
    |---|---|---|
    | All three judges agree | 0.855 | 0.777 |
    | Majority vote | 0.744 | 0.912 |
- **Use:** an asymmetric rule. Writing negative evidence requires all runs to agree; otherwise the result is recorded as `unverified`.

**2604.02450** `[pre]` A
- **Finding:** without a reference, small judges trail frontier judges by up to ~10%.

**2606.08400**: *Impacts of Histories and Models on LLM Grading* (2026-06-07) `[PR: ISET 2026]` A
- **Finding:** accumulated interaction history caused systematic drift away from expert scores, and simple ensembling did not fix it. The abstract gives no numbers.
- **Use:** direct support for the learner-blind grader (Slice 1 S1).

**2607.28210**: *AI-based scoring systematically underestimates conceptual understanding of linguistically weak students' explanations in physics* (2026-07-30) `[pre]` A
- **Finding:** across all 11 AI scorers, weaker language raised the odds of underestimating understanding (116 explanations).
- **Use:** score claims, not prose. Combined with 2607.05904, fluency cuts both ways.

**2604.26954** (presented at NCME 2026; treated as `[pre]`) A
- **Finding:** ensembles of 1–7 votes gave no significant gain on 900 student math conversations. Higher reasoning effort helped.

***Rethinking LLM Judges*** (ICLR 2026 Logical Reasoning workshop, OpenReview vdXPorr099; no arXiv ID) ext
- **Finding:** G-Eval, Chain-of-Verification and Debate underperform single-pass comparison against a reference.

**2603.27076** `[pre]` A
- **Finding:** a stacked verifier helps when upstream feedback is under 70% accurate. Above 85%, it costs 4–6 points.

**2602.20629**: *QEDBench* `[PR: ICML 2026]` A
- **Finding:** judge score inflation of up to +0.28 for Claude 4.5 Opus (+0.18 in arXiv v1).

**2603.18221**: *Scalable and Personalized Oral Assessments Using Voice AI* (2026-03-18) `[PR: Communications of the ACM 2026]` A
- **Finding:**
  - Council agreement rose from α 0.52/0.65 to 0.86/0.90 after deliberation. This is agreement between models, not validity.
  - Prompts did not stop the examiner from asking several questions per turn; a code-level turn validator cut that from 31.2% to 10.9% of turns.
  - When the LLM was asked to choose a case at random, 86% of its choices were the same case.
- **Use:** hard-code turn discipline and topic selection; use models for semantics. This matches LearnLoop's doctrine.

## 4. Tutoring policy and the router

**2610.04825**: *DICE: Decoupling Capability from Intervention Necessity in LLM Tutoring* (2026-10-04) `[PR: NeurIPS 2026]` A
- **Finding:**
  - Six actions including "accept-and-advance". Each action's value is estimated by simulator rollouts and an LLM judge, compared against the no-op.
  - Over-intervention: 0.024–0.036, vs 0.42–0.90 for Socratic baselines.
  - Nearly half of prescribed interventions have zero or negative value.
  - Simulated students only.
- **Use:** make "let them continue" a scored first-class action. Estimate its value with frontier-model rollouts.

**2607.21306**: *AI Assistants Overassist* (2026-07-23) `[pre]` ✔ (direction; numbers FT)
- **Finding:**
  - LLM teachers intervene in 90% of episodes vs 74% for humans, and much earlier (relative timing 0.18 vs 0.74).
  - "Only intervene if truly necessary" left GPT-5.2's rate unchanged.
  - Post-test transfer was about zero.
- **Use:** restraint cannot be prompted in. Keep a deterministic defer-by-default gate.

**2610.06446**: *The Assistance Dilemma: Learning to Teach via Multi-Turn RL* (2026-10-05) `[pre]` A
- **Finding:**
  - Every ablation arm lands within 0.03 Δtransfer of the others.
  - Answer leakage: 61% without the hand-set binary gates, 31% with the full recipe.
  - Failure modes: "answer-echo laundering", and support fading dropped to 0% because each episode was a single problem.
  - Eduardo-27B scores 0.79 vs Gemini 3.1 Pro's 0.80 on MathTutorBench.
- **Use:** end-to-end RL does not beat prompted frontier models and still needs hand gates.

**2608.16907**: *Effective Personalized AI Tutors via LLM-Guided RL* (v1 2026-07-10) `[pre]` ✔ (RCT and effect; the planner detail is FT)
- **Finding:**
  - RCT in 10 Taipei high schools, 770 students analyzed: +0.15 SD on the unassisted exam (SE 0.067).
  - The policy is a POMDP: a particle-filter belief plus model-predictive control. The LLM supplies observations only.
  - Randomizing the pedagogy prompt had no significant effect.
- **Use:** the best real-learner result in the sweep has LearnLoop's shape: an explicit belief and planner, with the LLM as a sensor.

**2610.11135**: *Can a System-One LLM Perform Knowledge Tracing When Few or No Learners Are Logged?* (2026-10-08) `[pre]` ✔
- **Finding:**
  - With zero platform data, the commercial "Jev" model reaches AUC 0.706, vs 0.689 for the best of 28 deep KT models trained on 8 learners.
  - Supervised KT catches up at 64–128 learners.
  - Going from 25 to 100 interactions of history adds 0.002 AUC. ECE is 0.084.
  - Deep KT stays ahead on unseen items.
  - This is a single preprint using a commercial model.
- **Use:** an LLM P(correct) sensor is worth shadowing in LearnLoop's data regime.

**2601.01708**: *Thinking-KT* (2026-01) `[pre]` A
- **Finding:** when population data exist, reasoning LLMs (including GPT-5-mini) trail AKT by about 0.06–0.11 AUC.
- **Use:** the counterweight to 2610.11135.

**EdWorkingPaper 26-1598**: *The Effects of Course-Integrated AI Tutoring on Student Performance and Engagement* (Liu et al., 2026-09-30; doi 10.26300/y3f8-vh05) `[pre]` ext
- **Finding:**
  - 2,379 undergraduates used a default-mode GPT-4o tutor.
  - Final grades fell by 0.37 SD and LMS participation by 0.90 SD.
  - 73.8% of requests asked for a direct answer.

**EdWorkingPaper 26-1551** (Oreopoulos & Low, 2026-08) `[pre]` ext
- **Finding:** Khanmigo in coach mode gave 0.06–0.08 SD per year. Students messaged it in only 17% of sessions where they made a mistake.
- **Use:** tutoring that the learner has to start fails in both directions. LearnLoop should start the probes and repairs itself, behind gates.

**2609.28470**: *StudentBench: AI and human tutoring yield equivalent GRE learning gains* (2026-09-23) `[pre]` A
- **Finding:**
  - 2,383 participants, 13 tutors with minimal scaffolding.
  - AI minus human: −0.58 pp (equivalence p = .015). AI vs no tutor: +6.15 pp.
  - Faster replies went with more engagement (ρ = −0.81).
- **Use:** turn-level wording needs little engineering. The router earns its keep in decisions across sessions.

**2606.20138**: *Learning to Prompt* (2026-06-18) `[PR: EMNLP 2026 Industry]` A
- **Finding:** a PPO router trained on simulated students won in simulation (0.694 vs 0.647) and tied in a live A/B test (0.565 vs 0.569, p = .635).
- **Use:** never train a policy on a simulator. Evaluate in shadow on real logs.

**2609.01591**: *StudentSim* (2026-09-01) `[pre]` A
- **Finding:**
  - A tutor trained with a GPT-5.4-simulated student as its reward scored 71.6%, below the no-RL tutor (75.7%). A StudentSim reward reached 90.5%.
  - Specializing to one student needs pooled data first (7.8k–23.4k instances).
- **Use:** an n=1 simulator is not available to LearnLoop.

**2603.17373**: *SafeTutors* (2026-03-18) `[PR: EMNLP 2026]` A
- **Finding:** pedagogical failures rise from 17.7% in single-turn to 77.8% in multi-turn dialogue, and scale does not reliably help.

**2610.08778**: *Sherpa* `[pre]` A
- **Finding:** an RL-trained 8B tutor reached 69.0% simulated-student accuracy, vs 70.1% for prompted Gemini 3.8 Flash.

**2505.15607**: *TutorRL* `[PR: EMNLP 2025 oral]` A
- **Finding:** a 7B RL tutor is roughly on par with LearnLM.

**2609.38346**: *Examining Variation in How Guided AI Tutors Resolve Student Impasses* (2026-09-29) `[pre]` A
- **Finding:**
  - 1,260 real chemistry-tutor sessions. Each extra impasse turn cuts the odds of recovery by 12.7% (AOR 0.873).
  - After a failed question, re-asking it recovered 28.1% of the time, vs 39.8% when the tutor addressed the error.
- **Use:** escalate to error-specific repair after one or two failed probes.

**2609.21154**: *CoLearn* `[PR: EMNLP 2026]` A
- **Finding:** uses the LLM as the observation function inside a BKT-style model (LearnLoop's pattern). The evaluation is preference only (68–69%).

**2604.01594** `[pre]` A
- **Finding:** LLM teaching choices fit a Bayes-optimal teacher best, and scaffolding prompts did not reliably help.

**2606.01182**: *CA-BED* `[pre]` A
- **Finding:** explicit expected-information-gain search over LLM likelihoods gave +21.8% success over direct prompting.

**2609.24290**: *CIGAsk* `[PR: EMNLP 2026 Findings]` A
- **Finding:** prompting alone cannot decide when to ask; RL works. This is a QA result, not tutoring.

**2605.30666** `[pre]` A
- **Finding:**
  - Pedagogical GRPO training moved the student's solve-rate change from +0.180 to −0.012.
  - Training-free best-of-8 selection raised the improvement rate from 59.0% to 81.9%.
- **Use:** test-time selection beat training.

**2512.23633**: *LearnLM / Eedi RCT* `[pre]` A
- **Finding:** with N = 165, novel-problem success was 66.2% with the supervised AI tutor vs 60.7% with human-only tutoring.

**2607.28128** `[pre]` A
- **Finding:** helpfulness rubrics cannot detect answer leakage.
- **Use:** use deterministic leak detectors.

## 5. Retention and scheduling

**PsyArXiv g97u4**: *What Should Be Spaced? Variability Constrains Spacing Effects in Classroom Learning* (Cao, Ling, Pavlik, Carvalho; 2026-06-08) `[pre]` ext A
- **Finding:** 52 classrooms, 1,050 students.
  - Spacing helped practiced items only when variability was low (b = 0.046, p < .001); under high variability it did not (b = 0.007, p = .27).
  - Spacing gave a modest transfer benefit in both conditions. High variability added no transfer.
  - 56% attrition, and the authors flag a confound between repetition count and spacing.
- **Use:**
  - The retention key is the *idea*, with a fixed retrieval target.
  - Sibling questions do not count as repetitions of each other.
  - Far variants are transfer probes, not maintenance reps.
  - This motivates the `idea_id` retention key in Slice 2 §5.2.

**2610.10548**: *Interpretable Memory Models for Spaced Repetition* (Schill; 2026-09-14) `[pre]` A, plus the **srs-benchmark** leaderboard (GitHub; not peer-reviewed) ext
- **Finding (SBD):** a 7-parameter model vs FSRS-7 on held-out users scored BCE 0.3279 vs 0.3237. The paper argues that offline accuracy cannot validate a scheduler.
- **Finding (srs-benchmark, about 350M reviews):**

  | Model | Log loss | AUC |
  |---|---|---|
  | RWKV-Curve (population-trained, tested on unseen users) | 0.3193 | 0.768 |
  | FSRS-7, fitted per user | 0.3401 | 0.717 |
  | FSRS-7, default parameters | 0.3620 | 0.703 |

  No benchmarked model uses card text.
- **Use:**
  - Memory parameters come from population pretraining, not from per-user fitting on about 10³ events.
  - LearnLoop fits FSRS-6 per user today (`scheduling/fsrs_fitting.py`).

**Memory Machines report** (Kirkby & Matuschak, April 2026; memory-machines.com/report) ext
- **Finding:**
  - About 1,500 highlight-anchored prompts. GPT-5.2's prompts were unusable 36% of the time; a year earlier, GPT-4o's "needs refactor" rate alone was 59%.
  - No judge model exceeded 70% accuracy.
  - Fine-tuning only matched frontier models.
  - A grounded judge, shown labelled prompts for the same highlight, raised Sonnet 4.5's precision from 56% to 78%.
- **Use:**
  - Judge generated prompts with exemplars from the same passage.
  - Treat item quality as a per-item statistic.

**2609.27063**: *Student Use of LLMs and the Limits of AI-Generated Question Difficulty in Data Science Courses* (An & Wang; 2026-09-22) `[pre]` A
- **Finding:** on 311 deployed questions, the LLM's difficulty label correlated with real difficulty at ρ = 0.06, and its Bloom level at ρ = 0.02.
- **Use:** never select "deep" or hard items by LLM self-label.

**2601.09953**: *Take Out Your Calculators* (2026-01-15) `[pre]` A
- **Finding:** role-played classrooms plus IRT correlate with NAEP item statistics at r = 0.75 / 0.76 / 0.82 (grades 4 / 8 / 12).
- **Use:** difficulty priors come from simulated solvers, updated by the learner's own results.

**Leong et al.**, AIME-Con 2026 Vol. 1 `[PR]` ext
- **Finding:** n = 791. LLM-written retrieval items were easier (−1.01 difficulty) and less discriminating (−0.19). Non-frontier models.

**Tang, Li & Patz**, AIME-Con 2026 Works-in-Progress `[PR]` ext
- **Finding:** AI-written calculus variants were ready for formative use 78–80% of the time, vs 88% for human-written items. A root-item reference mattered most.

**2602.17542**: *Using LLMs for Knowledge Component-level Correctness Labeling in Open-ended Coding Problems* (2026-02-19) `[pre]` A
- **Finding:** per-concept correctness labels from the LLM gave a better learning-curve fit than spreading the problem-level outcome. The abstract gives no effect sizes.
- **Use:** per-concept credit from the grader: demonstrated, failed, or not exercised.

**2604.03246**: *Personalized AI Practice Replicates Learning Rate Regularity at Scale* (2026-03-09) `[pre]` A
- **Finding:**
  - 366k interactions. Initial knowledge varied widely (IQR 2.78–12.18 opportunities), while learning rate was consistent (IQR 7.01–8.25).
  - Median 7.22 opportunities to mastery, vs 6.54 for expert curricula.
- **Use:** take learning rates from population priors, and spend the learner's evidence on placement.

**2608.11245**: *Towards Sustainable Learning in Online Education: A Reinforcement Learning Approach* (MaiMemo; 2026-08-02) `[pre]` A
- **Finding:**
  - In simulation, the RL policy got course completion of 31.1% vs 11.2%, and removing its engagement model hurt most.
  - A greedy "lowest recall first" policy lost almost all simulated users by about day 20.
  - Counter-evidence: MaiMemo's own 2025 A/B test (about 8,900 users). MMX-6 won offline but showed about 10% relatively lower Day-30 user retention (p = 0.11).
- **Use:** add an engagement and dropout term. Do not train an RL scheduler.

**2606.22328**: *Do Gains from Generative AI-Enabled Adaptive Pretesting Persist?* (2026-06-21) `[PR: AIED 2026]` A
- **Finding:** 7-week retention, N = 89:

  | Condition | Adjusted mean |
  |---|---|
  | Adaptive spaced retrieval | 78.19 |
  | Fixed spaced retrieval | 74.55 |
  | Learner-directed AI study | 67.28 |

  Adaptive vs learner-directed: d = 0.92. Adaptive vs fixed: p = .83.
- **Use:**
  - Scheduled retrieval matters more than adaptivity.
  - Reader and tutor chats do not reset retention clocks without a graded cold retrieval.

**PsyArXiv sj3w7**: *Retrieval Practice in Higher Education: Causality and Content Transfer Effects in a Gateway Math Course* (2026-01-19) `[pre]` ext A
- **Finding:** three cohorts with an instrumental-variable design. Retrieval practice raised quiz scores by 4–5 pp. The effect was strongest on isomorphs, weaker on near transfer, and limited on far transfer.
- **Use:** tag each variant isomorph, near or far, and measure transfer separately.

**Contrarian and negative results**
- ***Striking the Balance*** (Cao & Carvalho), Educational Psychology Review 38(1), 2026 `[PR]` ext: after instruction, retrieval practice generalized better than worked examples whether items were repeated or varied.
- **PsyArXiv jgqsh** (2026-09-03) ext: no overall transfer effect from spaced retrieval.
- **PsyArXiv tgm3w** (2026-08-13; N = 122, pre-registered) ext: the testing effect was weak to absent for naturalistic event memory.
- **PsyArXiv m46vf** (2025-10-30) ext: interleaving disadvantaged low-prior-knowledge learners on complex physics.
- **2508.03275** LECTOR `[pre]`: simulation only.

## 6. Practice generation

**2605.29277**: *Code-QA-Bench: Separating Code Reasoning from Documentation Memorization in Repository-Level QA* (2026-05-28) `[pre]` A
- **Finding:**
  - An agent produces a verified answer first, then derives the question from it.
  - Each question is tested closed-book, code-only, and with full documentation.
  - Code access gave +0.23 over closed-book; documentation added +0.071.
- **Use:**
  - Generate the answer first, citing `file:line`.
  - The closed-book filter rejects generic items.

**2511.02922**: *Faster but Not Wiser* (2025-11-04) `[pre]` A
- **Finding:** comprehension did not improve with Copilot (p = 0.59). Higher-comprehension students made write-then-view transitions 4.7× more often.

**2601.14289**: *RPC-Bench: A Fine-grained Benchmark for Research Paper Comprehension* (2026-01-14) `[PR: ACL 2026]` A
- **Finding:** 15K human-verified why / what / how questions built from reviewer–rebuttal exchanges. GPT-5 scored 68.2%, or 37.46% after a conciseness adjustment.
- **Use:** OpenReview rebuttals are the authors' *stated* rationale. Anchor "why did the authors…" items to them.

**2606.12071**: *On the Limits of LLM-as-Judge for Scientific Novelty Assessment* (2026-06-10) `[pre]` A
- **Finding:** a "novelty mirage". LLM judges rate model-generated questions as highly novel, while experts prefer questions anchored in the authors' framing.
- **Use:** never use an LLM judge to grade or select novelty items.

**2606.08251**: *Contemporary AI lacks the imagination to diverge or negate in science* (2026-06-06) `[pre]` A
- **Finding:**
  - 6,749 scientists. LLM judges agree only weakly with experts, and no model proposes null hypotheses unprompted.
  - A reward model trained on human ratings beat state-of-the-art judges by up to 27%.

**2504.20781**: *Using LLMs in Generating Design Rationale for Software Architecture Decisions* (2025-04-29) `[PR: TOSEM 2025]` A
- **Finding:**
  - Against expert rationale: precision 0.267–0.278, recall 0.627–0.715.
  - 64–69% of the generated arguments were helpful points the experts had not mentioned; 1.6–3.2% were potentially misleading.
- **Use:** generated rationale mostly invents motives that are plausible but never stated.

**2506.14649**: *IsComment* (2025-06-17) `[pre]` A
- **Finding:** rationale candidates were generated from issue reports and filtered for verifiability against them. Coverage of manual comments rose from 33.6% to 72.2% (ChatGPT) and from 35.8% to 88.4% (GPT-4o).
- **Use:** rationale must cite a span (commit, issue, comment, ADR, paper, or rebuttal), or it is labelled `inferred`.

**2511.07932**: *Computational Blueprints: Generating Isomorphic Mathematics Problems with Large Language Models* (2025-11-11) `[PR: EMNLP 2025 Industry]` A
- **Finding:** 17.8% lower error rate than expert-written items; deployed to 6,732 learners.

**2504.09763**: *EFAGen* (2025-04-14) `[pre]` A
- **Finding:** an LLM writes an executable generator program for each problem class, with unit tests acting as verifiable rewards.
- **Use:** with Computational Blueprints, one generator program per family (Slice 2 §5.3).

**2602.05114**: *Scalable Generation and Validation of Isomorphic Physics Problems with GenAI* (2026-02-04) `[pre]` A
- **Finding:**
  - 73% of deployed banks had statistically homogeneous difficulty.
  - A panel of 17 open models (0.6B–32B) predicted student performance at ρ up to 0.594. Models under 4B hit a floor and models over 14B a ceiling.
  - Variation was mainly surface features and numbers.
- **Use:**
  - Pre-screen variants with a solver panel.
  - Store a per-variant difficulty offset.
  - This method covers the "same capability, different surface" slot only.

**2607.13190** (2026-07-14) `[pre]` A
- **Finding:** 89% of generated isomorphs were fully specified and directly usable.

**2608.27953**: *The Illusion of What If: Evaluating the Breakdown of Counterfactual Reasoning in LLMs* (2026-08-28) `[PR: EMNLP 2026]` A
- **Finding:** 220 open-form what-if questions. The best of six frontier models scored 64.62%, with premise drift.
- **Use:** check what-if answer keys by running the perturbation where possible (math, code, or a short training run). Grade the causal chain, not the narrative.

**2604.23733**: *Multimodal QUD: Inquisitive Questions from Scientific Figures* (2026-04-26) `[pre]` A
- **Finding:** open vision-language models mostly ask questions the figure alone can answer.
- **Use:** a figure-only filter.

**2510.04721**: *BrokenMath: A Benchmark for Sycophancy in Theorem Proving with LLMs* (2025-10-06) `[pre]` A
- **Finding:** GPT-5 wrote sycophantic "proofs" of false statements 29% of the time.
- **Use:**
  - A template for "method does not apply" items.
  - The reference must store the counterexample, because LLM graders are sycophantic too.

**Generate-at-scale evidence**
- **2508.08314** `[pre]` A: critique-and-revise cycles produced items with IRT quality comparable to expert items (91 classes).
- **2512.23601** CreativeDC `[PR: EDM 2026 poster]` A: about 1.6× more distinct high-utility tasks, and the gap grows with more samples.
- **2512.10110** Generate-Then-Validate `[PR: LAK 2026]` A.
- **2606.18257** `[PR: KDD 2026]` A: prompting raised higher-order output by only 11.53% (20,700 questions).
- **2607.13901** `[PR: LREC 2026]` A: teachers judged only about half of answerable questions to be high-order.

## 7. Learning with AI assistance (projects, Quest, reading)

**2602.20206**: *Mitigating "Epistemic Debt" in Generative AI-Scaffolded Novice Programming using Metacognitive Scripts* (2026-02-22) `[pre]` A
- **Finding:**
  - N = 78. An LLM-judged "Explanation Gate" required a teach-back before generated code could be integrated.
  - On functional output, both AI arms beat manual work and did not differ from each other.
  - On a later maintenance task without AI, 77% of unrestricted users failed vs 39% of gated users.
- **Use:** an explain-to-accept gate on agent diffs. Not specced yet; it is the project-understanding vertical.

**2601.20245**: *How AI Impacts Skill Formation* (Shen & Tamkin; 2026-01-28) `[pre]` A
- **Finding:**
  - n = 52. The AI group scored 17% lower on the quiz (d = 0.738, p = .010), with no significant speedup.
  - Conceptual-inquiry patterns kept learning intact (65–86%); delegation patterns did not (24–39%). These subgroups are small.

**2607.08849**: *Experimental Evidence on the Learning Impact of Generative AI* (Contractor & Reyes; 2026-07-09) `[pre]` A
- **Finding:**
  - 211 students. AI access gave +0.28 SD immediately and +0.21 SD at one week (p = .068).
  - Augmentation users scored +0.34 SD. Automation users' advantage was gone in their unaided essays a week later.
  - An LLM labelled chat logs as augmentation or automation with 87% / 82% agreement.

**2604.04721**: *AI Assistance Reduces Persistence and Hurts Independent Performance* (2026-04-06) `[pre]` A
- **Finding:**
  - Three RCTs, N = 1,222. Unassisted solve rate fell (d = −0.42 / −0.19 / −0.42).
  - Giving up rose after about 10 minutes of answer-on-demand help.
  - Hint users skipped less than direct-answer users.

**2607.26375**: *(Im)Paired Programming: Coding Agents Improve Productivity but Harm Understanding* (2026-07-29) `[pre]` A
- **Finding:**
  - 54 students. Comprehension was worse with the coding agent (d > 0.80).
  - Comprehension was 0.615 for those who auto-accepted edits vs 0.777 for those who accepted them one at a time.
  - Participants still preferred the agent.

**2609.22993**: *Adaptive Scaffolding Needs Contingency* (CoMeT; 2026-09-19) `[pre]` A
- **Finding:**
  - A ladder of three asks of rising specificity, then a concession.
  - Answer give-away: 6.1% of sessions, vs 59.5% for an unrestricted assistant and 16.0% for a question-only tutor.
  - Frustration was lower than with the question-only tutor. No learning outcome was measured.

**Kreijkes et al.**, *Effects of LLM use and note-taking on reading comprehension and memory*, Computers & Education 243 (2026) 105514 `[PR]` ext A
- **Finding:** 405 students, tested after 3 days. Note-taking beat LLM-only on comprehension (4.89 vs 4.00 of 12) and on retention (10.80 vs 8.83 of 20). Students preferred the LLM.

**2510.15234**: *LLM-based In-situ Thought Exchanges for Critical Paper Reading* (2025-10-17) `[PR: IUI 2026]` A
- **Finding:** critical-thinking gains of d = 1.28 with multiple agents and d = 1.18 with one; no significant change without an agent. Comprehension was not measured.

**2609.12600**: *TraceMind* (2026-09-11) `[pre]` A
- **Finding:** information that ends up in a final draft is often not actually taken in by the user, and uptake can be predicted from interaction logs.
- **Use:** accepting generated output is not evidence.

**Also checked**
- **2605.21629** `[pre]`: in ALEKS data, retention odds fell 25%.
- **2609.23958** `[pre]`: a structured MBA tutor gave +6.63 points.
- **2606.06253** `[pre]`: in competitive programming, people who use AI as a substitute for practice lose skill; those who use it as a complement do not.
- **2604.23486** `[PR: ACL 2026]`: students mostly use tutors to extract answers.
- **2506.17006** `[PR: EC-TEL 2025]`: LLM feedback helped only learners who chose to use it.
- **2604.09158** `[PR: LAK 2026]`.
- **2607.06101** `[PR: ASE 2026 NIER]`: concept paper only.
- **2610.12125** `[pre]`: tuning a tutor to a hand-built pedagogy metric raised the metric while expert ratings fell from 4.46 to 3.03.

## 8. Searched, found nothing useful

These are gaps worth rechecking in later sweeps.

- **Memory and retrieval**
  - No 2026 controlled comparison of current frontier models in full context vs RAG on LongMemEval or LoCoMo.
  - No Eedi MAP@25 follow-ups on arXiv beyond 2024.
  - Nothing compares chronological vs topic-grouped history rendering.
  - Learned memory operations (Memory-R1, MEM1, Memory-R2) were tested on 3–14B models only.
- **Grading**
  - No paper assesses the quality of a teach-back explanation.
  - No process reward models applied to student work in 2026.
  - No RL-trained educational grader compared against prompted frontier models.
  - No conformal grading specific to education.
- **Tutoring policy**
  - No sim-trained tutor evaluated on real learning gains.
  - No real-learner comparison of LLM-chosen next items against IRT or bandit sequencing.
  - No n=1 or long-horizon RL tutoring.
- **Retention**
  - No large-scale real-log test of content-aware memory models.
  - No controlled evaluation of FIRe or implicit repetition.
  - No online learned scheduler.
  - No randomized study of regenerating prompts at each review.
  - No academic evidence on re-entry after a lapse.
- **Practice generation**
  - No learner-facing item generation for method selection, counterfactuals, or analogies.
  - No quality-vs-N curves for best-of-N question generation.
- **AI assistance**
  - No 2025–26 study measured comprehension or retention with LLM reading companions for scientific papers.
  - No RCT of hypothesis-driven debugging pedagogy.
  - No study measured learning outcomes from letting learners choose the hint level.
  - No study compared applying an idea immediately with scheduled review.

## 9. Experiments the sweeps proposed

| Experiment | Cost | Decision it informs | Where it lives now |
|---|---|---|---|
| M1 arms (d) full filtered history, (e) read-only tools, plus a context-length sweep | Same ~40 items; one more review pass | Which history mode M2 uses | Slice 1 §12.1 |
| Grader grid: reference vs none × solve-first vs direct × low vs high effort; real vs synthetic answers; valid-alternative false rejection | A few hundred calls, one evening of labelling | Reference policy; whether synthetic anchors are ever built | Slice 1 E1 (probes); Slice 2 §5.5 (policy) |
| Idea-identity log-loss replay: memory state per item vs per idea vs per LO, plus a variant-distance covariate, with the same FSRS weights across keys | Offline, no learner time | Whether `idea_id` becomes the live retention key | Slice 2 §5.2 |
| Source-anchored item pilot (one paper or one repo): 60 candidates through closed-book, provenance, and perturbation filters | An afternoon, a few dollars | Filter survival rates; depth vs single-shot items | Slice 2 §5.6 |
| Router replay on ~300 logged decision points: router vs frontier model choosing vs frontier model as sensor | Offline | Whether the router shrinks to gates plus value math | Not specced |
| Explanation gate on the next 20 agent diffs, randomized, with probes 7 days later | 20 diffs, ~2 min each | Whether explain-to-accept becomes the default for project evidence | Not specced (project vertical) |

## 10. Where this was applied (2026-10-11)

| Spec change | Main citations |
|---|---|
| Slice 1: M1 arms (d) full filtered history and (e) read-only tools; context cap ~100K; evidence ids before diagnosis; cache-friendly layout | 2603.04814, 2601.14287, 2608.25655, 2609.09664, 2511.02817, 2512.24601, 2605.12366, 2510.05381, 2605.15184, 2601.06007 |
| Slice 1: M1 uses one embedding model; four-model comparison moves to Slice 2 B1 | 40 items can't separate models; 2609.05339 (re-embed on change) |
| Slice 1: E1 valid-alternative and real-vs-synthetic probes | 2608.28725, 2606.10254, 2608.17938 |
| Slice 1: M2 history mode defaults to `full` unless kNN beat it in M1 | as above |
| Slice 2: PF track (practice families) absorbs T2 and T3 and runs in parallel with M2 | g97u4, sj3w7, 2610.10548, srs-benchmark, 2606.22328, 2511.07932, 2504.09763, 2602.05114, 2605.29277, 2601.14289, 2504.20781, 2506.14649, 2606.12071, 2608.27953, 2604.23733, 2510.04721, 2609.27063, 2601.09953 |
| Slice 2: synthetic anchor sets dropped from grading; verified reference, valid-alternative path, solve-first, one high-effort pass | 2606.10254, 2608.17938, 2608.28725, 2607.05904, 2607.12885, 2510.13744, 2603.14732, 2608.00004, 2604.26954 |

**Recommended but not yet applied** (owner decision pending):
- **T1:** drop the calibrator, conformal-zone, and skip-the-LLM machinery, and keep the adjudication ledger as evaluation data (2605.14752, 2606.28823, 2511.23455).
- **Router:** keep it thin, add a scored "let them continue" no-op, and shadow an LLM P(correct) sensor (2610.04825, 2607.21306, 2610.11135, 2608.16907).
- **Project-understanding vertical:** an explain-to-accept gate and Code-QA-style items (2602.20206, 2607.26375, 2605.29277, 2607.08849).


## 11. Facet representation and the learner-field kernel (second sweep, 2026-10-11)

Three research agents asked whether deep metric learning should separate facet dossiers. Their conclusion: separation is the wrong target. Similarity should predict **ability transfer**, and the learner's own data can't supervise a metric. ✔ marks papers Claude re-checked.

**Text similarity vs measured co-performance**
- **Hommel & Arslan**, *Language models accurately infer correlations between psychological items and scales from text alone*, AMPPS 2025 (doi 10.1177/25152459251377093) `[PR]` ✔.
  - A model fine-tuned on empirical item correlations predicts them at r = .71 (pilot) and .59 on new items (preregistered).
  - Frozen SBERT reached about .19 (A, from the full text).
  - Metric learning pays when its target is co-variation, not separation. These were survey items, not ability items.
- **Fitzpatrick, Heusser & Manning**, Nat Commun 17:2055 (2026) `[PR]` A. Knowledge smoothed over text-embedding distance predicted held-out answers within a lecture (OR 15.9). Across lectures it did so only after both had been taught. A generic encoder squeezed course content into a tiny region.
- **2609.31976** `[pre]` A. Over 40 TIMSS items, a single-factor 2PL beat all 12 Q-matrix structures. **2509.23484** `[pre]` A: topic profiles added nothing over one latent ability. This motivates the field's general factor.
- **2409.20167** `[PR: EDM 2025]` A. GPT-4o KC descriptions clustered by embedding did worse than human KCs on masked items (e.g. Statics RMSE .465 vs .407).
- **2502.18632** KCGen-KT `[PR: Findings ACL 2026]` A. LLM KCs beat human KCs (AUC .816 vs .797). Coarse merging by embedding clusters hurt.
- **2604.16398** `[PR: AIED 2026]` A. LLM Q-matrices revised against response fit beat the expert one (AUC .780 vs .717). The LLM proposes; the data selects.

**LLM pair verdicts as the metric**
- **2510.06747**, *LLMs Enable Bag-of-Texts Representations for Short-Text Clustering* (2025-10-08) ✔ (training-free; numbers FT, A).
  - The LLM's verdicts on embedding candidates become the representation.
  - E5 NMI/Acc 66.59/49.10 → 70.87/59.30, ahead of fine-tuning the embedder on LLM triplets (69.63/53.23).
- **2505.06469** KCluster `[PR: EDM 2025]` ✔. LLM question-similarity clustering beat expert KCs and embedding cosine on student-performance prediction. The margins are small (FT, A).

**Contrastive descriptions and training-free conditioning**
- **2311.07593** FuDD `[PR: ICLR 2024]` A. Descriptions that contrast a class with its confusable neighbours beat generic ones.
- **2505.21239** LMCD `[pre]` A. KC descriptions written against distractor KCs gain about 0.01 AUC.
- **2605.22544** `[pre]` A. Qwen3-Embedding's best-minus-worst spread across 15 prompts is about 0.15 on clustering and STS.
- **2511.11041** `[PR: ICML 2026 workshop]` A.
  - Projecting out the mean direction: wins/ties/losses 29/9/0 on classification, 22/12/4 on retrieval across 38 models.
  - Full PCA whitening hurt all 5 models tested.

**Learned adapters and their limits**
- **2505.24754** GSTransform `[PR: ACL 2025]` A. The LLM rewrite carried most of the gain (74.22 → 56.56 without it). The adapter needs about 10³ labelled texts.
- **2310.08750** Search-Adaptor `[PR: ACL 2024]` A. A residual, anchored adapter on frozen API embeddings helps. Unregularized customization fell below zero-shot on 5 of 8 BEIR sets.
- **2409.02343** NUDGE `[PR: ICLR 2025]` A. Bounded per-item offsets work for closed sets; normalization matters out of distribution.
- **2405.12442** SKarREC `[pre]` A. A contrastive adapter cut the Davies-Bouldin index from 2.03 to 0.66, while HR@1 rose only from .773 to .792. Separation is not usefulness.
- **2609.00100** `[pre]` A. A contrastive objective raised retrieval but preserved behavioural structure worse than PCA.

**Kernels, collapse and identifiability**
- **2608.09058**, *When Can Text Embeddings Replace Item Calibration?* (2026-08-10) `[pre]` ✔.
  - Embedding-derived loadings recovered traits at r = .825, vs .857 for calibrated loadings.
  - But they had κ = 137, mean inter-trait cosine 0.90, and about 4× posterior uncertainty.
  - The condition number is a collapse diagnostic that can run before any data exists.
- **2109.08215** HyperBO `[PR: JMLR 2024]` A and **2602.12082** Empirical GPs `[pre]` A. Fit GP priors on a population, then freeze them for new tasks.
- **2102.12108** `[PR: UAI 2021]` A (and AVDKL, ICML 2024). Marginal-likelihood deep kernel learning overfits on small data and learns spurious non-local correlations.
- **1303.0426**, **1803.04353** A. Skills measured only together form identifiability equivalence classes determined by the item–skill design matrix.
- **2608.00201** `[pre]` A: weighted A-optimal adaptive design for the multidimensional 2PL. **2608.24721** KENDO `[pre]` A: kernel ensembles in place of hyperparameter sampling.
- **Metrics:**
  - 2602.14486 `[PR: ICML 2026]` A: after a permutation-null correction, only local-neighbourhood agreement survives.
  - 2403.00642 `[PR: ICLR 2024]` A: uniformity misses dimensional collapse.
  - 2402.03191 `[PR: ACL 2024]` A: strict isotropy conflicts with cluster structure.

**Applied to `spec_learner_field_v1.md` (§4.1, §4.3, §5.1–5.2, §6.2, §8.4 6c/6d, D15–D19):**
- frontier-written facet dossiers with contrastive fields, embedded per field;
- LLM-adjudicated text edges;
- a general factor;
- a cap on correlation from text alone;
- co-measured classes taken from the loading matrix;
- a placement kernel ensemble;
- population-fit kernel scalars;
- an optional co-performance projection trained on public data and gated by a transfer guard;
- no separation-targeted metric learning, and no per-learner metric learning.

---

*Related: [[Pipeline Augmentation Plan]] · [[Embedding Integration Map]] · [[User intentions]] · [[LearnLoop_User_Intentions_v2]] · `docs/specs/spec_blind_grading_diagnosis_split_v1.md` · `docs/specs/spec_embedding_consumers_v1.md`*
