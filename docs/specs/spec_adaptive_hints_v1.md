# Adaptive hints: waypoints, subgoals and help written for the learner's current work (v1)

**Status:** draft for owner review (2026-10-13). Docs only; nothing here is built.

**The owner's request (2026-10-13):** "look into this specific insight from an excerpt I read about properly constructed hints as 'waypoints' instead of simply 'next steps'. Maybe we could use this to inform our hint prompt generation to also be adaptive to the learner instead of minted upon initialization." The excerpt is from Tithi, Fazeli, Droujkov, Yasir, Tian & Barnes, *Data-Driven Hints in Intelligent Tutoring Systems* (Encyclopedia of AI in Education chapter; arXiv 2603.07311, March 2026; `docs/brainstorming/data-driven-hints-in-ITS.pdf`).

**What this spec does:** hints are written **when the learner asks**, from their current work and their learner state, instead of being minted once when the item is created. It adds the kinds of hint the literature distinguishes (next steps, **waypoints**, labelled subgoals, backward-worked chunks, error-specific and discriminating hints). It derives a small **approach map** (subgoal structure with alternative routes) per item at n=1, from the reference solution, the learner's own textbook and the learner's own successful solutions. A judgment over typed learner state chooses the kind, following the expertise-reversal effect. Every choice is logged with its propensity, so kinds can be compared on this one learner's data and the choice can later be learned.

**Owner preferences in force** (`daily_loop_frictionless_defaults.md`; Reader workbench spec §2; owner decisions 2026-10-11/12):
- **Honest labels, generous defaults;** live behind kill switches, no shadow stages.
- **LLM judgment over hand-picked constants.** The chooser is a judgment; numbers here are caps on money, time or display only.
- **Learner text over skip buttons:** "Doesn't connect to my work" is a text box with shortcuts, not a button.
- **No artificial count caps.** Money and time bound hints, not a count. The learner can always ask for more.
- **Frictionless by default, details on demand.** A tester found the UI confusing, so this spec adds no control the learner must manage.

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_reader_workbench_v1.md` (branch `docs/reader-workbench-spec`, being edited) | Its RW2b help ladder, reconciliation contract and first-offer chooser (§5.2–5.5) are the workbench face of this spec. This spec generalizes them into one hint service for every surface and adds kinds, horizon, approach maps and propensities. **Proposed edits are in §8.2; this spec does not edit that file** |
| `spec_learner_field_v1.md` | Hints keep reaching the field only through `hints_used` and `primed` (§3.1 there). The `lo_general+hints` arm counts hints; weighting by kind is a named successor (§10.1) |
| `spec_action_router_v1.md` | The router's logged-mixture pattern and "a propensity only has to be the distribution actually sampled from" (§0, §7.3 there) are reused for the hint chooser. Hints are in-attempt help, not a router decision |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind to hints, kinds and maps. Hypotheses come from the diagnoser's overlay |
| `spec_slice_a_practice_and_field_v1.md` (PF) | PF's solution skeletons (`item_skeletons`) seed approach maps; PF-published variants currently carry no hints, which this spec fixes without touching PF |
| `docs/brainstorming/Pipeline Augmentation Plan.md` workstream G | The learned chooser deferred in §13 is that plan's equipoise bandit, applied to hint kinds |

**Citation convention.** Every `file:line` was checked on `main` at `57d31c63` (migration head 180, latest algorithm `mvp-0.14`). Python paths are relative to `src/`, frontend paths to `apps/learnloop-tauri/src/`, migrations to the repo root. Research claims say what was read (full text, abstract, or a secondary source); anything inferred for LearnLoop's setting is marked **(inference)**.

---

## 0. Thesis

LearnLoop's hints today are a list of strings written when an item is created, shipped to the client with the item, and revealed one at a time by Ctrl+H (§3). The same hints come out in the same order for every learner, every attempt and every state of the work. Many items have none at all: practice-family variants drop their parent's hints, and most generation prompts never ask for them. The owner's own complaint, recorded in the Reader dialogue, is the consequence: "when I would be given a hint I wouldn't be able to reconcile with the work I have already did so far."

The research the owner read says two things that a pre-minted list cannot do:
1. **Hints differ in kind, not only in amount.** A next-step hint names the immediate action. A **waypoint** names a goal state two or three steps ahead and leaves the path to the learner. A subgoal hint decomposes the rest of the task into labelled pieces; a backward-worked chunk starts from the goal. Subgoal labels and backward-strategy examples improved transfer and proof efficiency in controlled studies (Catrambone 1998; Shabrina et al. 2023; §1.3).
2. **Which kind helps depends on the learner.** The expertise-reversal effect is robust: more guidance helps learners with less prior knowledge and hinders those with more (Tetzlaff et al. 2025 meta-analysis, strongest in higher education; §1.5).

**For waypoints specifically, the evidence is weaker than the excerpt says** (§1.2). In the preprint of Cody et al. (2022), unsolicited waypoints given at random intervals did not significantly help high-prior-knowledge students, cost low-prior-knowledge students time and steps, and cognitive load was never measured; learners who *adopted* the waypoints did become more efficient, and waypoints given only when a learner needed help did help the weakest (Alam et al. 2023). So the honest version of the owner's idea is: **waypoints as one kind among several, offered when this learner's state says they can bridge to one, with a way down when they cannot, and measured.**

The data-driven tutors in the chapter get both from a population: thousands of student paths mined into interaction networks and approach maps. LearnLoop has one learner and an LLM. So this spec replaces the population with three things LearnLoop has (the reference solution and its existing checkpoint structures, the learner's own textbooks, and the learner's own successful solutions), and replaces the population-trained policy with a judgment over the learner's typed state whose choices are logged so they can be evaluated and, later, learned.

**The design rule:** a hint is a deliberate, recorded piece of help, written for the learner's current work, in the form most likely to let them continue on their own, and logged so LearnLoop can find out whether it did.

---

## 1. Research: what the literature says and what transfers

### 1.1 The source chapter (read in full)

Tithi et al. (2026) survey data-driven hint generation. Read in full (12 pages), it covers:
- **A taxonomy** (p. 2): procedural next-step hints; strategic or metacognitive hints ("overarching problem-solving frameworks and goal setting"); and bottom-out hints, which give the answer or final step. The **assistance dilemma** (Koedinger & Aleven 2007) frames all of it: enough information to move on without circumventing learning.
- **Next-step hints** (p. 3) reduce immediate load and raise completion (Stamper et al. 2013), but can invite **hint abuse** (rapid requests without engagement; Cody et al. 2018), often fail to teach transferable strategy ("what to do next … but not the why"), and do nothing about **help avoidance** (Maniktala et al. 2020).
- **Waypoints and subgoals** (p. 3–4): the excerpt the owner quoted; see §1.2–1.3.
- **Data types** (p. 4–5): solution traces (states and actions, unioned into an **interaction network**) and behavioural features (timing, accuracy, help-seeking) used for *when* to hint, e.g. Maniktala et al.'s HelpNeed predictor and Marwan et al.'s proactive feedback. Eagle & Barnes (2014) proposed feedback beyond next steps: temporal ("you are taking longer than expected"), hazard ("off-track compared with others"), and **high-level hints with intermediate targets**.
- **Methods across domains** (p. 5–6): Hint Factory (MDP over interaction networks; correct next-step hints over 80% of the time on four semesters of logic data), its extensions to programming (the sparse-state problem; Continuous Hint Factory; ITAP canonicalization), ASSISTments experiments, and the Help Tutor (Roll et al. 2011).
- **LLM hints** (p. 6–7): fluent, personalised, often competitive with human-authored content in surface quality, but weak at justification, metacognition and steering learners toward good solution paths; generate-then-verify pipelines help (Worden et al. 2025). The chapter's conclusion: "LLMs do not inherently model student knowledge or learning trajectories, [so] adapting hint content to individual students' current understanding requires additional scaffolding mechanisms" (p. 8). This spec is such a mechanism.
- **Discussion** (p. 7): solution-space methods are interpretable and grounded but need data; RL policies adapt but need much training data; LLMs need no data but lack grounding. The open question is how to combine them.

### 1.2 Waypoints (Cody et al. 2022) and higher-level hints (Cody et al. 2018)

**Cody, Maniktala, Lytle, Chi & Barnes (2022)**, "The impact of looking further ahead: a comparison of two data-driven unsolicited hint types on performance in an intelligent data-driven logic tutor", IJAIED 32(2):263–296 (**full text read of the arXiv preprint**, 2102.05741, Feb 2021; the journal version may differ).
- **How a waypoint is made.** The Hint Factory merges about four semesters of logs (250–300 students each) into an interaction network treated as an MDP. A next-step (NS) hint is the highest-value state one rule application away. A **waypoint (WP)** is chosen among states two to three steps away, picking the one most frequent in prior correct solutions; in practice mostly two steps. The idea came from approach maps, where subgoals appeared every two to three states in five-to-twelve-step proofs.
- **How it is shown.** As a "Goal" node with a "?" placed in the learner's workspace: the target statement only, with the rule, premises and bottom-out levels disabled. Hints were **unsolicited**, inserted periodically (NS capped at a third of the problem's length); on-demand hints had the same content.
- **Design.** Fall 2018, 143 students randomized and stratified on a one-problem pretest (56 NS, 58 WP after attrition); 18 training problems, then 4 harder posttest problems; ANCOVA; **no effect sizes reported.**
- **Results** (WP first, NS second). WP students justified fewer of their hints (84% vs 89%), adopted fewer (74% vs 83%), took twice as many steps to justify one (2.2 vs 1.1), and spent longer in training (77 vs 58 min). On the posttest **WP was worse overall:** more steps (127 vs 99, p = .02), lower accuracy (66% vs 71%, p = .05). In the **high-pretest group there was no significant difference** (98 vs 81 steps); the hypothesis that waypoints help high-proficiency students was rejected. In the **low-pretest group WP was worse** (128 vs 99 steps, p = .02). No condition × pretest interaction was found. Within WP, adopting waypoints correlated with fewer posttest steps (r = −.40) and less time (r = −.35). WP students had *tried* 72.6% of the waypoints they never justified: they worked toward the goal, failed, and gave up.
- **Cognitive load was not measured;** the authors speculate about it.

**Alam, Maniktala, Mostafavi, Chi & Barnes (2023)**, "Does knowing when help is needed improve subgoal hint performance…" (full text read, https://par.nsf.gov/servlets/purl/10525850): waypoints given *only when a HelpNeed classifier fired*, against no proactive hints (N = 138). No overall difference; low-prior students wrote shorter final posttest proofs (95 vs 119 steps, p = .047), and help avoidance in training fell from 14.6% to 3.6% (p < .01).

**What the excerpt overstates.** The chapter says waypoints "slightly increase cognitive load for low-proficiency students" but "significantly improved problem-solving efficiency for learners with higher prior knowledge." In the preprint, cognitive load was not measured, waypoints were significantly *worse* for low-pretest students, and the high-pretest benefit was not significant; what held was a correlation between *adopting* waypoints and efficiency. The defensible reading: **a waypoint is the right hint when the learner can bridge to it; given at random, it costs weaker learners time; given at need, it helped the weakest.** This spec therefore treats a waypoint as one option chosen from the learner's state, always with a way down (§4.2: "More" after a waypoint can give the next step toward the same target), and never unsolicited in v1.

**Cody, Mostafavi & Barnes (2018)**, AIED 2018, pp. 58–62 (full text read, https://par.nsf.gov/servlets/purl/10065909): next-step hints (NSH) against high-level hints (HLH), a subgoal two to three rule applications ahead, both with proactive hints after a median-length pause, about 36 students per arm. There was no significant difference on the performance metrics. On the hint-free problems at the end of each level, the next-step group did progressively worse (Level 5: more incorrect steps, 24 vs 11, p = .042; longer time, 36.1 vs 13.2 min, p = .021). The authors read the high step counts as possible gaming; that is their inference, since hint-request counts are not reported. Small sample; consistent with, not proof of, waypoints building strategy.

### 1.3 Subgoals, approach maps and backward strategy

**Catrambone (1998)**, "The subgoal learning model: creating better examples so that students can solve novel problems", JEP: General 127(4):355–376 (full text read, an OCR'd scan). A label on a group of steps cues the learner to group them, self-explain why they belong together, and form a goal for the group; that goal transfers to novel problems with the same subgoal structure but different steps. Experiment 1 (N = 150): labels interacted with mathematical background (p = .039): with a stronger background both abstract and superficial labels beat none; with a weaker background only the superficial label helped. Experiment 2: after a one-week delay, learners with **abstract** labels still solved 3.00 of 4 novel problems against 1.80 for superficial labels and 1.77 for none. Experiment 3: abstract labels transferred better when the mapping from surface features to roles changed.

**Margulieux, Guzdial & Catrambone (2012, ICER) and Margulieux, Catrambone & Guzdial (2016)**, Computer Science Education 26(1):44–67 (**abstracts only**; the publishers refused access), with **Margulieux & Catrambone (2016, CogSci)** (full text read, https://escholarship.org/content/qt35z8842x/qt35z8842x.pdf). Subgoals are "functional pieces of procedures"; labels describe their purpose. Subgoal-labelled materials improved novel-task performance (2012 abstract) and problem solving across two lab experiments and one online experiment (2016 abstract). In the CogSci study (N = 200), learners who *wrote* labels for steps already grouped for them did best when they got either hints or feedback on their labels, and worse when they got both (17.5 vs 21.0–21.5 of 25); unguided learners formed over-long, context-specific subgoals. Morrison, Margulieux & Guzdial (2015, abstract only) found the benefit of given labels did not replicate in one intro-CS task.

**Eagle & Barnes (2014)**, "Exploring differences in problem solving with data-driven approach maps", EDM 2014, pp. 76–83 (full text read). An approach map clusters an interaction network (about 330 attempts and 6.5k interactions per problem) into about 15 regions by Girvan–Newman community detection; paths through regions are approaches. Comparing a hint group with a control, the control dropped out more after level 1 (28% vs 9%) and entered and stayed in unproductive regions. A warning the authors call **trailblazing**: the hints only worked forward, and hinted students kept preferring forward work on a later problem with no hints, so hints narrowed the range of approaches. They propose hints toward subgoals and warnings on entering unproductive regions.

**Shabrina, Mostafavi, Chi & Barnes (2023)**, "Impact of learning a subgoal-directed problem-solving strategy within an intelligent logic tutor", AIED 2023, LNCS 13916:389–400 (full text read, https://par.nsf.gov/servlets/purl/10525848; the paper the chapter cites). Treatment students got **mixed-strategy worked examples** (the tutor works the first two to three steps *backward*, refining the goal into subgoals, then derives them forward) and **mixed-strategy problems** (the first three steps must be backward). With 50 control and 45 treatment students, the treatment scored higher on the unaided posttest (74.1 vs 70.4, p = .04) with shorter proofs (10.1 vs 13.4 steps, p = .031), and no difference in time or rule accuracy. The first mixed-strategy problem took longer; later ones did not. Approach maps were used to *analyse* students' routes, not to build the examples. **Cognitive load is not measured in the paper.**

**Shabrina et al. (2023, IJAIED; arXiv 2208.04696)** and **Shabrina et al. (2023, EDM, "Chunky Parsons problems")** (both full text read). The IJAIED study (N = 168) found backward worked examples *plus* backward problem solving beat control and examples alone on the posttest, after more struggle during training. The EDM paper is the data-driven chunking: approach maps plus three rules that pick "pivot" propositions where approaches merge or fork recovered every expert-identified subgoal on 15 problems; learners completed proofs from these chunks, and **chunks with a short explanation of what each derives, how, and why it is needed** raised normalized learning gain to 0.31, against 0.20 for control and 0.16 for chunks without explanation. No paper titled "Approach Mining" was found; the chapter's term appears to name this approach-map-plus-pivots method **(inference)**. None of the three Shabrina papers read reports a cognitive-load measure, so the chapter's "reduced cognitive load" could not be confirmed.

**Transfer (inference):**
- The *definitions* transfer without a population: a subgoal is a functional chunk with a purpose label; a waypoint is a goal state two or three inferences ahead on a good route; a backward chunk works from the goal toward a subgoal the learner can reach.
- The *selection* methods (frequency over interaction networks, community detection, pivot rules) need many solutions and do not transfer. LearnLoop's substitute is an LLM reading the reference solution, the existing checkpoint structures, the source's worked examples and the learner's own solutions (§4.3). That substitute is unvalidated, which is why §6 measures it.
- **Label register should follow the learner:** concrete labels for weaker background, abstract labels when the background is there, and abstract labels for durability over the days between reviews (Catrambone).
- **A chunk needs its explanation** (EDM 2023), and **hints anchored to one route herd learners onto it** (trailblazing), so alternative routes must be first-class.

### 1.4 Goal specificity (Sweller & Levine 1982)

**Sweller & Levine (1982)**, JEP: LMC 8(5):463 (**primary not accessed**; read through two secondary full texts: Vollmeyer, Burns & Holyoak 1996, *Cognitive Science* 20, and Ayres 1998, MERGA proceedings). With a specific goal, learners subgoal by means-ends analysis, which occupies working memory and teaches little about the problem's structure; with a non-specific goal ("find all you can"), they induce the rules and later solve better. Ayres (56 Year-8 students) found the no-goal group more successful at test than conventional or forward-directed groups (p < .05).

**Transfer (inference):** this is the mechanism the chapter invokes for waypoints: a goal representation that is not "the next move" pushes attention to structure. It also predicts the expertise reversal below: novices without the schema cannot use the freedom.

### 1.5 The expertise-reversal effect

**Kalyuga, Ayres, Chandler & Sweller (2003)**, Educational Psychologist 38(1) (abstract only), and **Kalyuga (2007)**, "Expertise reversal effect and its implications for learner-tailored instruction", Educational Psychology Review 19:509–539 (full text read). Guidance that helps novices becomes redundant load for more expert learners, for example worked examples against problem solving (effect sizes 0.90 for novices, 0.23 for experts) and worked examples against exploration (0.69 vs −0.33). Higher-prior-knowledge learners did better with fast fading of worked steps, lower with slow fading. Two **rapid diagnostics** let instruction adapt within a session: the **first-step test** (show the task briefly and ask for the learner's first move; experts skip intermediate steps; correlations with full tests up to .92 at up to 4.9× less time) and rapid verification (judge whether candidate steps are correct). Adaptive tutorials built on them improved knowledge gain (effect sizes 0.46 and 0.55; Kalyuga & Sweller 2004 and 2005, as reported in the 2007 review).

**Adaptive fading.** Salden et al. (2009), as reported by Otieno, Schwonke, Renkl, Aleven & Salden (2011, CogSci; full text read): fading worked steps according to the learner's self-explanations beat fixed fading (d = .49 immediately, .59 delayed); self-explanation quality predicted outcomes better than answer correctness. Renkl & Atkinson (2003) and Atkinson, Renkl & Merrill (2003): abstracts only.

**Tetzlaff, Simonsmeier, Peters & Brod (2025)**, "A cornerstone of adaptivity – A meta-analysis of the expertise reversal effect", *Learning and Instruction* 98, 102142 (bibliographic record read via Crossref; the publisher page refused access; **findings read from a secondary source**, a Learning and the Brain blog summary): 60 studies, 176 effect sizes, about 6,000 participants. Low-prior-knowledge learners learned more from high-support instruction (d = 0.505); high-prior-knowledge learners learned more from low-support instruction (d = −0.428). The effect grew with age and was strongest in higher education. Prior knowledge and support are continuous; there is no cut line. This is the meta-analysis the Reader dialogue cites.

**Transfer (inference):** the effect is about the *same learner on different material*, not a fixed trait. LearnLoop's learner is an adult working university-level maths, the population where the effect was strongest, and their prior knowledge varies by LO and facet. So the choice belongs per item at request time, from the learner's state on that item's facets, and no single threshold exists to hand-code. Kalyuga's first-step test is a ready n=1 tool: when a hint is requested before any work, asking for the learner's first move both helps them start and tells the next hint where they are (§4.2, `approach_question`). Adaptive fading's result (fade on what the learner shows, not on a fixed schedule) is the same principle applied over attempts: the chooser reads how the learner did after earlier hints of each kind.

### 1.6 Help seeking: abuse, avoidance, timing and contingency

**Koedinger & Aleven (2007)**, "Exploring the assistance dilemma in experiments with Cognitive Tutors", Educational Psychology Review 19(3) (full text of the submitted manuscript read). A table of the benefits and costs of giving versus withholding help, and a "rough criterion": give help when the probability of error or unproductive thinking is high. Cognitive Tutors withhold first, then add feedback, hints and problem selection as needed.

**Aleven, Stahl, Schworm, Fischer & Wallace (2003)**, RER 73(3) (abstract only), and **Aleven, McLaren, Roll & Koedinger (2006)**, IJAIED 16(2) (**not accessed**; its model read through Roll, Baker, Aleven & Koedinger 2014, JLS 23(4), and Koedinger, Aleven, Roll & Baker 2009, both full text). The help-seeking model is about 80 hand-written rules: attempt a step only if you think you know it; ask for a hint if you don't; after an error, reflect, then hint or retry; with hand-set skill bands (above 0.6 high, below 0.4 low) and time thresholds. **Help abuse** is clicking through to the bottom-out hint, or asking instead of trying on a skill one has; students asked for the bottom-out hint in 82% of hint episodes. Yet long dwell on a bottom-out hint correlated with learning: clicking through can turn a step into a worked example. In Roll et al. (2014; N = 38 over two months, step-level analysis), desired help seeking raised the odds of getting the next same-skill step right by 45%, and on low-skill steps **trying without help first, even failing, helped novices.**

**Roll, Aleven, McLaren & Koedinger (2011)**, Learning and Instruction 21(2) (abstract only), and Aleven et al. (2016), IJAIED 26, "Help helps, but only so much" (abstract only). The Help Tutor's metacognitive feedback improved in-tutor help seeking, and the better help seeking persisted into new content a month later; but there was **no difference in domain learning**, and students disliked the comments.

**Razzaq & Heffernan (2010)**, "Hints: is it better to give or wait to be asked?", ITS 2010 (full text read). Within subject, 61 eighth-graders: on-demand hints produced larger gains than hints shown on every wrong answer (0.137 vs 0.04, p = .04, effect size 0.35), driven by students who asked for many hints.

**Contingent tutoring** (Wood & Middleton 1975; Wood, Bruner & Ross 1976; **primaries not accessed**): after failure give more specific help, after success less. A 2025 preregistered replication with three-year-olds (Smit, de Kleijn, Wicherts & van de Pol, J. Ed. Psych., abstract read) matched tutor accuracy but **did not replicate** the benefit for independent problem solving.

**Maniktala, Cody, Isvik, Lytle, Chi & Barnes (2020)**, "Extending the Hint Factory for the Assistance Dilemma: A Novel, Data-driven HelpNeed Predictor for Proactive Problem-solving Help", JEDM 12(4) (full text read, arXiv 2010.04124). Steps were labelled after the fact by duration × efficiency. One quick unproductive step (a plausible guess, "Opportunistic") was deliberately *not* help need; a second consecutive one ("Far Off"), or one long unproductive step ("Futile"), was. With 123 students randomized, proactive partially worked steps at predicted need improved posttest solution optimality (.71 vs .59, d = 0.4) and time (18 vs 29 min, d = 0.8). Random, frequent proactive hints in earlier semesters correlated with *longer* posttest times (r = .49). The authors: "providing hints when they are needed is more important than simply providing more." Their predictor ignored hint use, so steps taken after a hint looked expert-like.

**Maniktala, Cody, Barnes & Chi (2020)**, "Avoiding help avoidance", IJAIED 30(4):637–667 (full text read, arXiv 2009.13371; the chapter dates it 2021). An **assertion** is the whole next statement, inserted into the learner's workspace as an unjustified "subgoal" node that the learner must justify before using. Against the same content shown as a text message, assertions were justified far more often (0.93 vs 0.63) and were more often needed in the final proof (0.82 vs 0.62). Low-prior-knowledge students in the assertion group wrote shorter posttest proofs and finished faster. Confound: assertions came more often and on a different schedule.

**VanLehn (2006)**, "The behavior of tutoring systems", IJAIED 16(3) (relevant sections read in full). Hints live in the inner loop, once per step. The standard sequence is **point, teach, bottom-out**. Two pieces of guidance matter here: contingent tutoring (Wood): start the next hint one level *more* specific if the last help needed deep hints, and *less* specific if the first hint worked; and the step to hint should be the one the student is trying for, a plan-recognition problem for which "ask the student" is a legitimate answer. When a step involves several pieces of knowledge, "a complex hint sequence might be worse than none."

**Transfer (inference):**
- Proactive hints help only when targeted; untargeted frequency hurts, and on-demand beat show-on-every-error in the one direct comparison. LearnLoop v1 stays on-demand (§13 defers unsolicited hints with a trigger).
- Failing first is useful for novices, and help-seeking nagging improved help seeking without improving learning. So abuse and avoidance are measured and fed to the chooser, never lectured about or gated (H4).
- Contingent shift and "plan recognition by reading the work" are things an LLM writer with the learner's draft can do; the replication failure means they are advice to the judge, not a rule (§4.5).
- The hand-set skill bands of the help-seeking model are exactly the kind of constant this spec replaces with a judgment over the learner's state.

### 1.7 LLM-written hints

**Tithi, Ramesh, DiMarco, Tian, Alam, Fazeli & Barnes (2025)**, *Computers and Education: AI* 9, 100490 (full text read, arXiv 2505.04736). On 1,050 real student states in propositional logic, DeepSeek-V3 hints were 75% accurate, falling from 87.9% to 63.2% as problems got harder; a hint counted as wrong if invalid, already in the student's work, or dependent on statements not yet derived. Experts rated explanations high on consistency (3.90/4) and clarity (3.09) but low on **justification (2.24)** and **subgoaling (1.66)**. An LLM judge using the same rubric over-rated subgoaling (2.47 vs 1.66) and agreed with experts poorly there (QWK 0.16). The model sometimes built on redundant student steps and failed to steer students back to a good path.

**Worden, Vanacore, Haim & Heffernan (2025)**, L@S '25 (full text read, https://par.nsf.gov/servlets/purl/10652694). GPT-4 explanations generated **with the correct answer in the prompt**, then a separate GPT-4 self-verification pass that discards flagged items (59 of 422 flagged, 14%), with a 20% human spot check and a learner-facing "report a mistake" button. Against answer-only, the explanations improved next-problem correctness (OR ≈ 4.2; 188 students); against expert-written explanations they did no worse (6,371 students). There is no measured error rate before verification. The authors expect college-level domains to need more review.

**Price, Dong, Zhi, Paaßen, Lytle, Cateté & Barnes (2019)**, IJAIED 29(3):368–395 (full text read via the author preprint), with **Price, Zhi, Dong, Lytle & Barnes (2018)**, AIED 2018 (full text read). The 2019 paper's QualityScore rates hint algorithms against a gold set of tutor-written hints and penalizes invalid hints even when valid ones are also offered. Every algorithm failed most on large code, **divergent attempts unlike other solutions**, and when generating many hints; the authors suggest *not* hinting on divergent attempts and asking instead. The 2018 paper (not 2019, as the chapter has it) found hint quality plateaued after 15–20 student solutions, and that a comprehensive set of expert solutions was competitive with student data.

**Haim, Worden & Heffernan (2024)**, AIED 2024 companion (abstract only; closed access). Its two questions match Worden et al.'s two experiments; no numbers verified.

**Bastani et al. (2025)**, PNAS; SSRN 2024 version "Generative AI can harm learning" (SSRN version partly read; PNAS abstract via search). About 1,000 Turkish high-school students. Unrestricted GPT-4 ("GPT Base") raised practice performance 48% but **lowered the later unassisted exam by 17%**; students copied answers, and the model made logical errors 42% of the time. "GPT Tutor", whose prompt **included the correct solutions and teachers' notes on common mistakes** and asked for incremental hints without the answer, raised practice performance 127% and left the exam roughly unchanged. GPT Tutor students believed they had done better than they had.

**Pardos & Bhandari (2024)**, PLOS ONE (first ~100k characters read, https://pmc.ncbi.nlm.nih.gov/articles/PMC11125466/). ChatGPT-3.5 help (one worked solution per problem, not adapted to the learner) with **self-consistency** (ten samples, majority answer) cut the share of hints failing checks from 32% to 0–13% by topic. With 274 adult crowd workers, learning gains were 17.0% (ChatGPT), 11.6% (human) and 1.9% (control); ChatGPT and human did not differ significantly.

**Kumar, Rothschild, Goldstein & Hofman** (SSRN 4641653; abstract only). N = 1,200, preregistered: LLM explanations beat answers alone, most when learners attempted the problem first; explanations containing errors still helped somewhat.

**Phung et al. (2024)**, LAK (arXiv 2310.03780; results read). GPT-4 writes a programming hint; GPT-3.5 acting as a student tries to repair the bug with and without it, and the hint is kept only if it helps. Precision 95–98% at 73–88% coverage, against about 92% for human tutors (expert annotation only, 79 programs).

**Roest, Keuning & Jeuring (2024)** (arXiv 2312.10055; abstract only): LLM next-step hints for programming were mostly one specific next step tailored to the student's code; some misled, and they were too thin near the end of a task.

**Adaptation to learner state.** TutorLLM (arXiv 2502.15709; abstract only) combined knowledge tracing with retrieval (30 students; +5% quiz scores). **No randomized study was found that shows learning gains from LLM hints conditioned on a knowledge-tracing state.** The central premise of this spec is therefore plausible from the human-instruction literature but unvalidated for LLM hints, which is why §6 measures it from the first day.

**Transfer (inference):**
- Generate with the reference solution in hand, check before showing, and re-ask or fall back rather than show a doubtful hint (§4.6). Bastani et al.'s two arms are the clearest evidence that this matters: the same model harmed later unassisted performance without the solution and incremental-hint instructions, and did not with them.
- Count every hint as assistance and judge learning only by later *unassisted* attempts (§5, §6): practice performance with AI help overstated learning by a wide margin, and learners misjudged it.
- Do not trust an LLM judge to grade the "big picture" quality of hints (Tithi et al.'s QWK 0.16 on subgoaling). Measure hints by what the learner does next (§6), and give the learner the "doesn't connect" path, the n=1 equivalent of Worden's report button.
- Free-form maths has no symbolic checker for most steps, so expect accuracy no better than the logic numbers on hard items. Anchoring to the reference route and to stored structure (§4.3) addresses the "failed to steer back" failure.
- When the learner's work is unlike every known route, prefer a question about what they are trying (Price et al.; VanLehn's plan recognition) over a confident hint (§4.4).
- Phung et al.'s simulated-student check (keep a hint only if a model "student" does better with it) is a plausible later verifier for free-form maths; deferred (§13).

### 1.8 What transfers to LearnLoop

| Setting difference | Literature assumes | LearnLoop has | Consequence here |
|---|---|---|---|
| **Population** | Thousands of solution paths per problem, mined into interaction networks and approach maps | One learner; items authored from their own textbooks | Approach maps from the reference solution, existing checkpoint structures, source worked examples, a few model-written routes and the learner's own successful solutions (§4.3). Price et al. 2018's finding that a set of expert solutions is competitive with student data is the (inferred) justification |
| **Answers** | Logic proofs or code: discrete states, symbolic checkers | Free-form maths in markdown and LaTeX | Placement is an LLM reading of the learner's draft against the map, quoted and checked structurally, never a symbolic state match (§4.4) |
| **Writer** | Hint text from templates over a mined next state | An LLM | The writer is constrained by kind contracts, the reconciliation contract and leak control (§4.6) |
| **Policy** | RL or randomized experiments over many students | n=1; ~10² decisions a month | A judgment (the Decider) chooses; its own probabilities are the sampling distribution, so propensities are exact and off-policy evaluation is possible later (§4.5, §6) |
| **Timing** | Proactive hints from a HelpNeed predictor | On-demand only | On-demand in v1; avoidance measured; proactive deferred with a trigger (§13) |
| **Outcomes** | Posttest scores, time, optimality | Every attempt logged, with later unassisted attempts on the same facets | Later independent success is the primary outcome; immediate progress is secondary (§6) |
| **Evidence for the premise** | Human-tutor and ITS studies of hint kinds and of adapting guidance to prior knowledge | No randomized study of LLM hints conditioned on a learner's state (§1.7) | The premise is plausible, not established; every hint is logged so it can be checked on this learner (§6) |

---

## 2. Standing constraints

- **H1. Hints are help, never evidence.** A hint never writes an observation, mastery, FSRS or certification row. It reaches evidence only through the attempt it was part of, through `hints_used`, `primed` and `reveal_events` with their existing meaning (§5).
- **H2. The grader stays blind.** Hints, kinds, maps, placements and learner state never enter `BlindGradingContext` (Reader W8).
- **H3. Judgment over constants.** No constant in this spec decides which kind of hint a learner gets. Numbers are caps on money, time or display.
- **H4. Help is never withheld.** The learner can always ask for more, ask for a different approach, or ask for the worked answer. Abuse and avoidance are measured, never gated.
- **H5. Honest labels.** Every hint shows where it came from (AI-written, from the item, from a named source) and what kind it is. A hint that counts as heavy help says so.
- **H6. Replay makes no model calls.** Maps, hints, placements and chooser outputs are persisted paid outputs; replay and rebuild never regenerate them.
- **H7. Items are not rewritten.** `hints` and `hint_policy` are part of `practice_item_hash` (`vault/hashes.py:44-58`), so writing a hint onto an item would mint a new revision. Nothing in this spec writes to an item's YAML; maps and hints live in their own tables.
- **H8. Reuse before building.** One hint service for every surface; the Decider client for the choice; the spend framework; `answer_leaks_expected` for leak control; T6 for source passages; the existing trace contracts and PF skeletons as map seeds; the router's propensity convention.
- **H9. Kill switches restore today exactly.** With `hints.adaptive_enabled = false`, the practice screen and its RPCs are byte-identical to `main`.

---

## 3. Code truth (audited 2026-10-13 on `main` at `57d31c63`)

### 3.1 Where hints are minted

| Path | Where | Hints today |
|---|---|---|
| Item schema | `learnloop/vault/models.py:692-693` (`hints: list[str]`, `hint_policy: HintPolicy`); `HintPolicy` at `:370-374` (`max_useful_hints = 0`, three empty per-count maps) | No validator; no count bound except exercise import's |
| Storage | Vault YAML (`vault/loader.py:191`; `vault/writer.py:122-123`); part of `practice_item_hash` (`vault/hashes.py:44-58`) | Changing hints makes a new item revision |
| Exercise import | `learnloop/content/authoring/ai_contracts.py:43-46` ("2-4 progressive hints: orient first, near-give-away last"), rule 6 at `:182-184`; `exercise_authoring.py:61` (`MAX_HINTS = 4`), applied at `:503` | Two to four; no `hint_policy`; attempt types `independent_attempt` only (`:510`) |
| Tutor promotion | `learnloop/tutor/ai_contracts.py:186-190` | Hints "for LOW mastery" only |
| Generation (expansion, diagnostic, cross-source) and rung variants | `content/authoring/practice_generation.py:1901-1963`, `:1966-1990`, `:1038`; `content/authoring/rung_variants.py:820-878` | **No hint instruction.** The patch schema has an undescribed optional `hints` (`content/proposals/ai_contracts.py:653-654`), so hints exist only when the model volunteers them |
| Practice-family publication | `ops/pf_publish.py:86-133` | **Drops the parent's hints:** published variants have none |
| Reader quick-check escalation; "write my own question" | `reader/reader_quick_check.py:238` (`"hints": []`); `reader/reader_authoring.py:267` | None |
| Write-a-card | `content/authoring/item_authoring.py:108,145`; `components/WriteCardDialog.tsx:167` | Optional, typed by the learner; split card drops them (`item_authoring.py:392`) |
| Synthesis, probes, teach-back | `content/synthesis/ai_contracts.py:303`; `diagnosis/probe_instance_generation.py:619`; `tutor/teach_back.py:595` | None |

Hints in the textbook itself: ingest maps a "Hints" heading to role `solution` (`ingest/block_roles.py:87`), which item-bound retrieval excludes (`source_retrieval/corpus.py:157`). Worked examples other than the one an item was made from stay available to the practice tutor as "the tutor's best scaffold" (`:150-155`), which is what `worked_parallel` hints draw on.

### 3.2 How hints are served and recorded

- **Shipped with the item.** The serializer sends `hints`, `hint_policy` and `expected_answer` to the client (`learnloop_sidecar/handlers/serializers.py:368-377`). The sidecar never sees an individual reveal.
- **The practice screen.** Ctrl+H calls `revealHint` (`screens/PracticeScreen.tsx:516-518`), which reveals the next authored hint, refuses during a diagnostic block, and does **nothing at all when the item has no hints** (`:576-584`). Revealed hints render as "hint i/N" banners (`:1189-1192`). The key bar lists `^h hint` (`:1235`), but key-bar entries are not clickable (`components/ui.tsx:380-389`): **hints are keyboard-only.** On a cold check a banner says hints will void the measurement (`:920-929`).
- **The count.** A 350 ms debounced draft flush (`PracticeScreen.tsx:456-463`; `handlers/practice.py:431`) stores the answer and the hint count in the session checkpoint. Submit sends `hints_used`. The handler folds in hint-equivalent tutor questions and clamps to `max_useful_hints` only when that is set (`handlers/practice.py:556-561`; `hint_equivalents_for_submission` at `tutor/tutor_qa.py:741`). `submit_dont_know` does neither (`handlers/practice.py:676-717`). **Nothing records when each hint was shown:** the field spec lists "the timing of ordinary hints (each attempt keeps only its total)" as not recorded (`field/probability_states.py:99-101`).
- **What a hinted attempt means** (`diagnosis/causal_activity_policy.py:121-142`, `:166-186`): any `hints_used > 0` or `primed` makes the attempt assisted. It earns no certification credit (`learner/capability_mapping.py:246`), is rejected as a cold retry (`attempts/attempts.py:2018-2020`), counts half in probe episodes (`diagnosis/probe_episodes.py:1661-1664`), is not "learner-side clean" for placement (`placement/rules.py:105-113`), and is excluded from the retention evaluation (`outcome_contract.py:46`). `primed` without diagnosis makes it `repair_activity`: no FSRS feed either.
- **Hints do not dampen mastery or FSRS under the default policy.** `hinted_attempt` has evidence mass 1.0 (`config/schema.py:1266`); the per-count dampening and rating-cap maps are empty by default; `_hint_dampening` has no caller (`attempts/attempts.py:4287-4289`) and `hint_dampening` is hard-coded to 1.0 (`:3407`).
- **The reveal ledger** has kinds `tutor_answer`, `repair_display`, `guided_redo`, `source_review`, `answer_display` (`attempts/reveal_ledger.py:37`). **Authored hint reveals write nothing there,** not even the "near-give-away" last hint. Auto-prime fires when reveals since the last attempt sum to 0.35 (`attempts/attempts.py:147`, `:1870`, `:1893`).
- **The tutor.** Contexts `library`, `practice`, `feedback`, `reader` (`tutor/tutor_qa.py:72`). Answer modes (`answer_directly`, `help_me_reason`, `ask_me_first`) exist only in the Reader and follow the learner's pick, never their state (`:81-82`). The practice-context prompt is Socratic and may not "confirm or deny whether the learner's current approach or partial answer is correct" (`tutor/ai_contracts.py:255-262`); its context has the stem, answer and rubric but **neither the learner's draft nor the item's hints** (`tutor/ai_contracts.py:20-35`). Questions of type `prerequisite`, `mechanism` or `strategy` count as hints (`tutor_qa.py:115`); answers overlapping the key write `tutor_answer` reveals; practice allows three questions (`config/schema.py:540`).
- **The closest thing to an adaptive help policy** is `build_typed_transition_decision` (`diagnosis/probe_blocks.py:188`): a deterministic tutor move from a fixed taxonomy (`elicit_reasoning`, `localize_error`, `contrast_cases`, `counterexample`, `explanation`, `transfer_question`, `state_subgoal`; `:146-185`) and a hand-set scaffold formula (`:220`). It runs only after a probe episode closes.
- **Guided redo** (`diagnosis/guided_redo.py:1-31`, `:272`) serves the preserved prefix of a wrong answer read-only and asks the learner to rewrite the repaired part, as a primed attempt. It uses no hints.
- **Grading and scheduling.** Neither grading context carries hints or `hints_used` (`attempts/ai_contracts.py:351-374`; `attempts/blind_grading.py:120-150`); the diagnoser sees an `assisted` flag (`diagnosis/split/history.py:592`). The scheduler infers a scaffold level from the hint count (`scheduling/selection_rewards.py:411`, `:602-605`).

### 3.3 Learner state available when a hint is requested

| State | Where | Notes |
|---|---|---|
| LO placement intent (assumed, learning, maintenance) | `placement/state.py:1241` (`load_placement_state`), intents at `:313-390` | The learner-side status; `LearningObject.status` is content lifecycle |
| LO mastery | `db/repositories.py:1062` (`mastery_states`) | `logit_mean`, `logit_variance` |
| P(success) for the item | `placement/predictor.py:164` (`active_predictor`) → `LiveMasteryPredictor.predict_item` (`:98-104`) | The field's challenger predictors are offline (`FieldConfig.enabled = False`, `config/schema.py:1721-1728`) |
| Capability ledger, facet timeline | `facet_capability_evidence` (`migrations/037_canonical_facet_state.sql:44`); `learner/facet_evidence_timeline.py:830`, `:865`; `learner/capability_grid.py:108` | Demonstrated unaided vs assisted-only |
| Misconceptions and hypotheses | `db/repositories.py:2202` (per LO), `:14460` (causal hypotheses), `:16425` (open cause factors); the diagnoser overlay `error_events_for_attempt` (`:1978`) | Read the overlay, not raw `active_errors_by_learning_object` (`:1966`), which misses the diagnoser's statements on split vaults (Reader §3.4 item 1) |
| Misconception discrimination | `diagnosis/followups.py:1482`; probe EIG at `diagnosis/probe_families.py:467`, `diagnosis/probes.py:786` | Feeds `discriminating` hints |
| Prior attempts; family | `db/repositories.py:1289`; `PracticeItem.family_id` (`vault/models.py:743`) | Outcomes and `hints_used` per attempt |
| Live draft | `session_checkpoints.current_answer` via `fetch_session_checkpoint` (`db/repositories.py:10012`) | Saved within 350 ms of typing |
| Stuck text | `declared_stuck` (`migrations/178_stuck_prompt.sql`); `attempts/stuck.py:122`, `:271` | A submitted answer, not mid-attempt text |
| **Solution structure** | `expected_answer` (a worked solution, per `content/authoring/ai_contracts.py:166`); **`trace_contract`** recipes of checkpoints with dependencies (`vault/models.py:392-401`; prompt at `ai_contracts.py:173-177`); **PF `item_skeletons`** (technique sequence, operation graph, checkpoints; `migrations/174_pf_generation.sql:58-71`, prompt `content/authoring/pf_contracts.py:173`, written by `ops/pf_generation.py:458`); guided redo's `learner_work_prefix` (`diagnosis/guided_redo.py:74-80`) | Trace contracts are sparse and keyed by rubric criterion ids (9 of 69 items in the `fixtures/arxiv` copy have recipes). Skeletons exist where PF has run. Neither carries labels, intermediate states or alternative routes |

### 3.4 Routes, the Decider and decision logs

- **The Decider** answers typed questions with probabilities: for a `choice`, a probability for every option plus the most likely one (`ai/decisions.py:1-19`, `:74`, `:124`); several named questions share one request and one state (`:153`). Decider tasks are listed in `DECIDER_TASKS` (`ai/routing.py:77`) and never fall back to chat; the default profile is `openrouter_decider` (`config/schema.py:969`).
- **A new chat route** needs an `AITask` entry (`ai/routing.py:22-70`), a `ROUTE_FOR_OPERATION` entry (`:82-147`), an `AIRoutingConfig` field (`config/schema.py:1073-1150`), the Settings use-case list (`screens/SettingsScreen.tsx:22-29`), and `tests/test_provider_resolution_parity.py`.
- **The ChatGPT-plan provider** is merged (`config/schema.py:1005-1045`; `learnloop ai latency` at `cli/ai.py:231`); the owner's sign-in is pending, so its real latency is unmeasured (`docs/reviews/chatgpt-plan-provider.md`, "Latency comparison").
- **Propensity logs exist for scheduling** (`policy_experiment_assignments`, migration 098; `scheduling/randomization_layer.py:47`) and the router spec's mixture. **No tutor-move or hint log carries a propensity.**
- **Kill-switch pattern:** a config section with `enabled`, read when an answer is recorded or a surface drawn, while replay reads persisted per-attempt flags (example: `StuckPromptConfig`, `config/schema.py:1575-1586`).

### 3.5 What does not exist

- No hint is written for the learner's work; no hint knows the learner's state.
- No per-reveal record, no hint timing, no hint kind, no outcome per hint.
- No subgoal structure with labels, intermediate states or alternative routes.
- No hints at all on PF variants and on most generated items; Ctrl+H silently does nothing there.
- No clickable hint control on the desktop practice screen.

---

## 4. Design

### 4.1 One hint service, four surfaces

A new package, `learnloop/hints/`, owns one function:

```text
request_hint(conn, vault, HintRequestV1) -> HintResultV1
```

Four surfaces call it, and none writes hint text of its own:

| Surface | Today | With this spec | Phase |
|---|---|---|---|
| Practice screen hint | Reveals the item's authored hints in order; nothing when there are none (§3.2) | Asks the service; authored hints become seed and fallback (§4.7); every item gets hints | H2 |
| Reader workbench Help (RW2b, not built) | Specified with its own writer and level chooser (Reader §5.2–5.5) | RW2b calls the service; its ladder keeps its levels and gains kinds (§8.2) | H3, inside RW2b |
| Guided redo after a wrong answer | Preserved prefix plus a rewrite, no hints (§3.2) | A Hint during the redo calls the service, starting from the preserved prefix and the diagnosis | H4 |
| Practice-context tutor | Socratic, blind to the draft (§3.2) | Reads the draft and the map placement; a strategy question ("how do I go on?") is answered as a hint of a chosen kind | H4 |

`HintRequestV1`: the surface; the item; the practice session; the learner's **current work** (the practice-screen draft read from the session checkpoint, or the workbench steps with ids, or the redo's prefix and rewrite); this attempt's earlier hints with kinds and feedback; and the request: `more` (the default), or a feedback shortcut (`different_approach`, `too_big_a_jump`, `notation`), or "show me the book's way".

`HintResultV1`: the hint text; kind, level and horizon; the placement (§4.4); labels (§4.8); the evidence it carries (§5); the assist row id.

### 4.2 Kinds, levels and horizon

The Reader spec's ladder measures **how much of the solution the help does for the learner** (levels 1–5). That stays, and it alone decides evidence (§5). This spec adds two axes the ladder lacks:
- **kind:** the form the help takes at a level;
- **horizon:** for waypoints, how many steps ahead of the learner's current state the hint points.

| Kind | Level | What it says | Basis (§1) | Contract checked in code, beyond §4.6's shared rules | Existing tutor move (§3.2) |
|---|---|---|---|---|---|
| `approach_question` | 1 | A question about the approach, an assumption or the goal ("What does F have to be at the left end of the support?"). With no work yet, often **"What would your first move be?"**: it helps the learner start and its answer places them for the next hint | Strategic and metacognitive hints; VanLehn's "point"; Kalyuga's first-step test | Declares what it asks about (approach, assumption, goal or first move); states nothing about the solution | `elicit_reasoning` |
| `discriminating` | 1 (as a question) or 3 | A check whose result differs between two open explanations of the learner's trouble ("Before changing anything: what does your formula give at x = 0?") | Error-specific feedback; LearnLoop's misconception discrimination | Names at least two open hypothesis ids from the state, and the result each predicts; the predicted results differ | `contrast_cases`, `counterexample` |
| `localize` | 2 | Names the first questionable part of the learner's work, without the correction | Reader §5.2 level 2 | Quotes the learner's work; contains no corrected expression | `localize_error` |
| `waypoint` | 3 | **An abstract intermediate goal state on the learner's route, `horizon` ≥ 2 steps ahead: what will be true, not how to get there** ("Aim for a CDF that is 0 at the left end and 1 at the right; you are about two steps from that") | Cody et al. 2022 and Alam et al. 2023 (mixed evidence, §1.2); Sweller & Levine 1982 | Targets a map node on the learner's route at the chosen horizon, reachable from their placement; names no transformation between here and there; never a node marked `leak` (§4.3) | `state_subgoal` |
| `subgoal_plan` | 3 | The rest of the route as a few **labelled subgoals**, the current one marked, with no step content ("Find the CDF on the support ✓ · Fix the constant with a boundary value ← here · Extend to the whole line"). Labels are concrete for a weaker background and abstract when the background is there | Catrambone 1998; Margulieux et al. 2016; Eagle & Barnes 2014 | Every label maps to a map node; labels carry no expression from later nodes; the writer declares the register (concrete or abstract) | `state_subgoal` |
| `next_step` | 3 | The single next action from the learner's checkpoint, in their notation, without doing it ("Differentiate your third line and compare it with the given density") | Next-step hints (Hint Factory) | Targets the adjacent node (horizon 1); one action | — |
| `error_specific` | 3 | Names what is wrong in a quoted step and the principle it violates, without the corrected result | The chapter's error-specific feedback; VanLehn's "teach" | Quotes the step; names a principle; contains no corrected value | `explanation` |
| `worked_parallel` | 3 | The same move worked on a *different* instance, preferably a worked example from the learner's own source, labelled with its origin | Worked examples (Renkl & Atkinson) | The item's own values absent; a source quote passes T6 verification; T6's item-bound exclusions apply (`source_retrieval/corpus.py:150-163`) | `worked_example` |
| `worked_chunk` | 4 | A chunk of *this* problem worked **backward from the goal** ("To show X it is enough to show Y; Y follows once you have Z"), each piece saying what it establishes, how, and why the next piece needs it, and leaving the bridge from the learner's last valid state to Z for them | Shabrina et al. 2023 (backward-first worked examples; chunks with explanations); Maniktala et al.'s assertions | Leaves at least one gap the learner fills; every piece carries its what/how/why; carries heavy-help evidence (§5) | `worked_example` |
| `walkthrough` | 5 | The full solution, keeping the learner's route where it is valid | Bottom-out hints | Heavy help | — |
| `authored` | 3 | One of the item's authored hints, verbatim, labelled "from the item" | — | Used when it fits the placement, or as the fallback (§4.7) | — |

**Horizon** for a waypoint counts map edges along the learner's route, with two named ends: "the end of the current subgoal" and "the goal". It is chosen with the kind (§4.5), never fixed. A horizon of 1 is a next step, so `next_step` and `waypoint` are two ends of one scale.

**"More", "different approach", "too big a jump".** The learner can always ask again. "More" lets the chooser raise the level or shorten the horizon; **after a waypoint, its options always include the next step toward the same target**, because waypoint learners in Cody et al. who could not bridge tried, failed and gave up (§1.2). "Different approach" keeps the level and requires a different kind or route. "Too big a jump" requires a shorter horizon or a finer kind. These constrain the options the chooser sees; they are not rules about what helps.

The crosswalk to `probe_blocks.py`'s tutor moves lets a closed probe episode's typed decision reach the chooser as one more input ("the diagnosis recommends `state_subgoal`"). The two taxonomies stay separate; neither replaces the other.

### 4.3 Approach maps: subgoal structure at n=1

The data-driven literature finds subgoals by mining many students' solution paths (Eagle & Barnes 2014; Shabrina et al. 2023). LearnLoop has one learner. It has, per item:

1. the reference solution (`expected_answer`), rubric, authored hints and, where present, the **trace contract's checkpoint recipes** (alternative recipes are alternative routes) and **PF's solution skeleton** (technique sequence and operation graph, written to be identical across isomorphic siblings);
2. the learner's **own textbook's worked examples** for the item's LO, through T6 retrieval with ingest's block roles, with T6's item-bound exclusions;
3. the learner's **own successful solutions** to the item and its family siblings (graded correct, or a PF-c valid alternative).

An **approach map** is a small graph built from these by one model call (route `approach_map`):

```text
ApproachMapV1
  nodes:  id; label (a subgoal label: short, structural, no answer values);
          state (what is established at this point; LaTeX allowed);
          recognizers (what in a learner's work shows the node is reached);
          checkpoint_id (the trace-contract or skeleton checkpoint it matches, if any);
          leak (true when the state contains or gives away the expected answer)
  edges:  from; to; technique (a short name); principle; facet ids
  routes: id; name ("CDF route"); node path from the givens to the goal;
          origin (reference | trace_contract | skeleton | source:<span ids> | model | learner:<attempt ids>)
```

- **Small by design:** a handful of nodes per route and only the routes that are genuinely distinct. Its job is a waypoint a few steps ahead and the labels for a plan, not a step-level proof graph (Reader §17 defers those).
- **Alternative routes are first-class.** The builder records the reference route, the source's route where a worked example differs, the trace contract's recipes, and the distinct routes it judges a capable student would take. This is the n=1 stand-in for a population of solutions **(inference**, from Price et al. 2018's result that a set of expert solutions is competitive with student data).
- **Approach mining at n=1: the learner's own routes.** When a map is refreshed (§4.3.1), the learner's correct answers since the last version are compared with its routes: a new route is added with `origin = learner`; a matching route gains the attempt id. Across a family this gives the learner's **route preference**, which the chooser and writer read: a learner who solves by CDFs gets waypoints on the CDF route.
- **Checkpoint links** tie the map to what already exists: a grader's `structured_trace.first_invalid_id` (`diagnosis/probe_blocks.py:249-258`) and guided redo's `changed_checkpoint_ids` (`diagnosis/guided_redo.py:321`) place directly on the map.
- **Families.** A sibling's builder receives the family's existing map as a template. Each item still has its own row, with its own values and leak marks.
- **Validation in code** before a map is stored: a DAG; every route runs from a given to the goal; every edge's facets belong to the item; labels are non-empty and contain no expression from a `leak` node; the goal node agrees with the expected answer (by exact key where one exists; otherwise the builder's declaration, stored as unverified). A failing map is re-asked once, then not stored; hints work without one (§4.4).
- **Keyed by item revision and seeds.** The row records `practice_item_hash` and a hash of its seeds; a revised item, or a changed trace contract or skeleton (which `practice_item_hash` does not cover), gets a new map.
- **Never shown whole and never graded against.** The map contains the solution. It reaches the learner only through hints, and the grader never sees it (H2).

#### 4.3.1 When maps are built

| Trigger | Why | Default |
|---|---|---|
| **The item is shown** (practice screen, workbench, guided redo) and has no map | By the time the learner asks for help the map is ready. It is built once per item revision and reused at every later review | On (`hints.maps.build_on_serve`); background; never on the request path |
| **A hint is requested** and there is still no map | The writer builds the map inline in the same call (a larger output, a few seconds slower) and it is stored | On |
| **A hint is requested** on an item whose map predates the learner's latest correct answers in its family | Merges the learner's new routes. Lazy, so only items the learner needs help on pay for it | On; background, after the hint is shown |
| `learnloop hints maps build [--item \| --family \| --lo] [--dry-run] [--json]` | Backfill, owner-run | Dry-run first |

Map building and merging are background work, so they may use Codex (`codex_low`) as well as the fast route.

### 4.4 Placing the learner's work

Each hint starts with a placement: which route the learner is on, the last node their work reaches, and the first questionable point, each with a quote from their work. The writer produces it as part of its structured output, so it adds no call.

- **Practice screen:** the work is the answer draft, read from the session checkpoint when Hint is pressed (the client flushes the draft first). An empty draft places the learner at the givens; the hint is about getting started.
- **Workbench:** the step list, with "Check my work" verdicts when they exist (Reader §5.2).
- **Guided redo:** the preserved prefix plus the rewrite so far; the diagnosis's failed checkpoints mark the questionable point.
- **A valid route the map lacks** is placed as `new_route` and treated as the learner's route (Reader §5.2 contract rule 4). It is merged at the next refresh if the attempt succeeds.
- **Work unlike any route and not clearly valid** gets an `approach_question` about what the learner is trying, rather than a confident hint toward a route they are not on (Price et al. 2019; VanLehn's plan recognition).
- **No map** (none yet and the inline build failed): placement is relative to the reference solution, and waypoint and subgoal kinds are not offered for that hint.

Placements are logged; they are what make outcomes measurable in map terms (§6).

### 4.5 The chooser: kind, level and horizon as a judgment

**Who chooses.** The Decider, in one request with two named questions over one state (route `hint_chooser`, added to `DECIDER_TASKS`):
- `kind_level`: a `choice` over the (kind, level) options the request allows. Options whose preconditions fail are absent: `discriminating` without two open hypotheses on the item's facets, `waypoint` and `subgoal_plan` without a map, `worked_parallel` without a usable source example or another instance, options excluded by the learner's shortcut.
- `horizon`: a `score` over an ordinal rubric (next step · two steps · end of the current subgoal · the goal), asked only when a waypoint is among the options.

**The state it reads** (typed and short; the Reader §5.5 list, extended):
- the item's LO placement intent and mastery; facet evidence split into demonstrated unaided and assisted-only;
- the live predictor's P(success) and variance for the item;
- open hypotheses and misconceptions on the item's facets, as typed records from the diagnoser's overlay, with probabilities where the hypothesis machinery has them; a closed probe episode's recommended tutor move, if any;
- the learner's history with hint kinds on these facets: kinds shown, whether they continued without more help, "doesn't connect" replies, later independent outcomes (§6);
- the learner's route preference (§4.3);
- this attempt: time since the item was shown; whether there is work yet; the previous hint's placement, kind and whether the work changed since; feedback given;
- the help style: **let me struggle · balanced · guide me** (default balanced). "Let me struggle" asks for the least specific help that could work (questions and waypoints first, in line with Roll et al.'s finding that trying first helps novices); "guide me" asks for more specific help sooner. It is a stated preference the Decider weighs, never a block: "More" still goes up.

**The instructions** state the research, not thresholds: less specific help (approach questions, waypoints, abstract labels) tends to suit higher prior knowledge and steady progress, and more specific help (next steps, concrete labels, error-specific hints, worked chunks) lower prior knowledge or a learner who is stuck (§1.5); a waypoint is for a learner whose state says they can bridge to it, and the direct evidence for waypoints is mixed (§1.2); after help that did not work, be more specific, and after progress, less (§1.6); with no work yet, asking for the first move is cheap and informative; with competing explanations for an error, a discriminating check both helps and tells them apart; keep the learner's route; when the work matches no route, ask. The Decider weighs these against the typed state. **No constant in this spec decides the kind.**

**How the served option is picked: sampled from the Decider's own probabilities.** The Decider returns a probability for every option. The service samples the (kind, level) option, and the horizon, from those probabilities and logs the probability of what it drew as the **propensity**, as the router's mixture does ("a propensity only has to be the distribution actually sampled from", router spec §0). This is not an experiment that withholds better help. When the Decider is confident it puts nearly all the probability on one option, which is then served nearly always. When it spreads probability it is unsure which kind is best, and acting in proportion to that uncertainty is Thompson-style probability matching. It is also what makes kinds comparable later (§6). `hints.choice_policy = "argmax"` serves the top option instead and logs propensity 1 (no off-policy evaluation is then possible; D4).

**Fallback.** On the chooser's time box (3 s, as in Reader §5.5), an unavailable or spent-out Decider, or `hints.chooser_enabled = false`: the authored hints in order while they last, then `next_step`; after "different approach", the next kind in a fixed list. Logged as `chooser = 'fallback'`, propensity 1.

**The learner's explicit pick wins.** "Show me the book's way" selects the reference route; "show me the worked answer" selects `walkthrough`. A pick is logged as `learner_pick` with no propensity, as in the router.

### 4.6 The writer and its contracts

The writer is one chat call (route `hint_writer`) with structured output. It receives the item (stem, reference solution, rubric, authored hints), the map, the learner's work, earlier hints and feedback, the chosen kind, level and horizon, the route preference, and for `discriminating` the hypothesis records. It returns the placement, the hint, its target node and route, a `strategy` slug, and the fields its kind's contract needs.

**Shared rules**, checked in code before anything is shown (the Reader §5.2 reconciliation contract, generalized to every surface):
1. **It cites the learner** when there is work: at level 2 and up it quotes the draft or names a step id that exists.
2. **It continues from a real checkpoint:** the placement node is reached by the quoted work, and is no later than the first questionable point.
3. **It says what stands** when there is work ("your first three lines stand").
4. **It keeps the learner's route** unless that route is invalid or the learner asked for another.
5. **It changes strategy when it isn't working:** after a "doesn't connect" reply, or a second hint at the same placement, the new hint's kind or strategy slug differs from the earlier ones there.
6. **It is placed:** with a map, it names its route and target node, and the target's distance matches the chosen horizon (or is the last node short of the goal when the route is shorter).
7. **It obeys its kind's contract** (§4.2).

A hint failing a rule is re-asked once with the failure named; then it is shown as a `next_step` from the last valid checkpoint without its unverified claims (Reader §5.2).

**Leak control.** Every hint at level 3 or lower passes `answer_leaks_expected` (`tutor/tutor_qa.py:816`); waypoints and subgoal labels never carry a `leak` node's state. A leaking hint is re-asked once, then withheld with "this hint would give the answer away; see a worked piece instead?".

**What the practice tutor's rule becomes.** The practice-context tutor may not confirm whether partial work is correct (§3.2). A hint that says "your first three lines stand" does exactly that, deliberately: it is help, and it is recorded as help (§5).

### 4.7 Authored hints: seed and fallback, not the source

The `hints` list stays on every item, and the authoring paths keep writing it in v1.
- **Seed.** The writer receives the authored hints; when one fits the placement it may serve it verbatim (`kind = authored`, "from the item").
- **Map seed.** The map builder receives them too; an authored sequence is usually a coarse subgoal list.
- **Fallback.** With `hints.adaptive_enabled = false`, a capped day, an unavailable writer or a time-out, the practice screen shows the authored hints exactly as today.
- **Deferred (§13):** authoring could emit a map instead of finished hint strings, since the map is the reusable structure and the hint is now written at request time.

### 4.8 What the learner sees

Frictionless by default, details on demand.
- **The hint control becomes clickable.** The key bar's `^h hint` becomes a clickable control with the same label and shortcut (today it is a non-clickable label; §3.2). Nothing else is added to the screen.
- **Pressing it** shows "Writing a hint for your work…" and then the hint. If the item has authored hints and the wait passes `hints.authored_offer_after_seconds` (4, a display cap), a quiet link "use the item's hint instead" appears; taking it cancels the adaptive request so only one hint is recorded.
- **Each hint has a small label:** its kind in plain words ("A goal to aim for", "Plan", "Next step", "Check this part", "Which is it?", "Worked example", "Worked piece", "Full solution", "From the item") and "AI-written". A worked piece or full solution says on the same line that it counts as heavy help.
- **Under each hint, one quiet line: "Doesn't connect to my work".** It opens the Reader's feedback box: optional text, shortcuts "Different approach", "Too big a jump", "I don't understand the notation". An empty submit is allowed. The next hint reads it at once.
- **Earlier hints stay visible** in order, so a waypoint can be reread while working.
- **The help style** is not on the screen. It sits in the hint panel's "⋯" menu and in Settings, default balanced, remembered. The chooser reads it; it never blocks a request.
- **Cold checks and probes are unchanged:** the cold-check banner still says hints void the measurement, and hints stay disabled during a diagnostic block.
- **No unsolicited hints** in v1 (§13).

---

## 5. Evidence semantics: no new rules

| Assist | Recorded as | Existing meaning (§3.2) |
|---|---|---|
| Any hint shown at level 1–3, any kind, adaptive or authored | `hints_used` += 1 | Assisted: no certification credit, rejected as a cold retry, half weight in probe episodes, not learner-side clean for placement, excluded from the retention evaluation. Mastery and FSRS unchanged under the default `HintPolicy`; an item's own per-count caps and dampening still apply by count |
| A hint at level 4–5 (`worked_chunk`, `walkthrough`) | `primed = true` (and `hints_used` += 1) | `repair_activity`: no FSRS feed, no certification (the matrix at `diagnosis/causal_activity_policy.py:17-22`; the class at `:121-142`) |
| Hint text overlapping the key | A `reveal_events` row of the existing kind `tutor_answer`, `basis = 'hint:<kind>:L<level>'`, with its overlap amount | Production admissibility, reveal-aware cold lanes and auto-prime's 0.35 sum (`attempts/attempts.py:147`) |
| A learner's reply to a `discriminating` check | Part of their work, so part of the submitted answer if they keep it | No evidence of its own |
| "Doesn't connect" text | A `learner_card` verdict in `judgment_ledger` (task `hint_fit`); a learner text for learner-text gaps once that merges | None |

**Recorded server-side.** Adaptive hints are written to `help_assists` when shown (§9). At submit, the handler counts shown assists since the item's last attempt in this session, exactly as it folds hint-equivalent tutor questions today (`handlers/practice.py:556-559`), and sets `primed` when any was at level 4 or 5. The client's own `hints_used` keeps counting only the authored hints it revealed itself, so nothing is counted twice (gate G-H3). `submit_dont_know` gets the same fold for adaptive hints, so a shown hint is never lost (its existing asymmetry for tutor questions is left for the reviewer to rule on).

**The clamp.** `max_useful_hints`, when set on an item, still clamps the folded total (`handlers/practice.py:560-561`). Any value above zero is assisted, so the clamp changes no classification; the assist rows keep the true count for reports.

**No successor (§10.1).** Every mapping uses an existing field with its existing meaning, as the Reader spec's D6 does. What changes is how many attempts carry assistance: items that had no hints can now be hinted, and a hint on them makes the attempt assisted. That is the meaning `hints_used` already has.

---

## 6. Measurement: which kinds help this learner

The chapter's closing question is the one to answer: not "is the hint accurate?" but "did it help, and did the learning last?" At n=1 every number here is a **report with its sample size and interval, never a threshold**.

### 6.1 Outcomes per hint

Derived at report time from assist rows, attempts and placements; never stored as evidence.

| Outcome | Definition | Horizon |
|---|---|---|
| **Unaided next progress** | After the hint, the learner's work reaches the hint's target node (or, for kinds without one, the next node) before any further help: from the next hint's placement, the workbench's next valid step, the grade (a correct answer reaches the goal), or the outcome placement below | Within the attempt |
| **More help needed** | Another hint in the same attempt, and its level | Within the attempt |
| **Time to solution** | Hint shown → submit; in the workbench, hint shown → next valid step. Wall clock; idle excluded where the surface measures it | Within the attempt |
| **"Doesn't connect"** | A reply on this hint, by shortcut ("Too big a jump" is the cognitive-load proxy) | Within the attempt |
| **Grade** | The attempt's grade | The attempt |
| **Later independent success** | The next attempt on the same item, and the next on the item's LO, with `hints_used = 0` and not primed: pass or fail. **Pending until it happens;** never imputed | Days to weeks |

**Outcome placement.** On the practice screen a wrong answer after a hint does not say whether the learner got past the waypoint. For hinted attempts submitted not fully correct, one small background call (route `hint_outcome`) places the final answer on the map. It is measurement only: it never touches the grade, diagnosis or evidence (`hints.outcome_placement_enabled`).

### 6.2 What each decision logs

The option set offered; the Decider's full probability vectors; the drawn option and its propensity; the seed; the chooser (`decider` | `fallback` | `learner_pick`); the policy and question-set versions; the state hash; the placement; the map version. A hint the learner never saw (cancelled, withheld) is logged with `shown = false` and excluded from outcomes.

### 6.3 Comparing kinds at n=1

`learnloop hints report [--since] [--json]` (no model calls, no learner text):
- **Descriptive, per kind and level:** count, unaided next progress, more help needed, time to solution, "doesn't connect" by shortcut, grade, later independent success with how many are pending. Authored hints are a kind, so H0's rows are the baseline.
- **The expertise-reversal check:** the same columns split by the LO's placement intent and by the predictor's P(success) at request time. This is the n=1 check of the expertise-reversal prediction for waypoints, whose direct evidence is mixed (§1.2): do waypoints lead to unaided progress where this learner's state is strong, and to "too big a jump" where it is weak?
- **Off-policy estimates** (H5): for each kind, the estimated value of "serve this kind whenever it was offered", and of the Decider's argmax policy, by self-normalized inverse propensity weighting and a doubly robust estimator (outcome model: per-kind, per-intent means). Each shows its effective sample size and a bootstrap interval. Primary outcome: later independent success; secondary: unaided next progress. A kind the Decider never gave real probability has no support, and the report says so instead of estimating.
- **Help abuse and avoidance, as counts:** hints requested in quick succession with no change to the work (abuse in Aleven et al.'s sense), and wrong submissions after long work with no hint (avoidance; Maniktala et al.'s "futile" pattern). They are chooser inputs and report rows; nothing is gated on them (H4).
- **Latency and cost** per route: p50/p95 for chooser and writer, contract re-asks, leak withholds, fallbacks.

**Expected volume.** At roughly 5–20 hint requests a day, a month is about 150–600 decisions, a few dozen per kind. Descriptive rows are readable within weeks; off-policy intervals stay wide for months. Without logged propensities those months could not be used at all, which is why sampling (D4) matters.

### 6.4 From reports to a learned choice

When §13's trigger holds, a learned layer joins the Decider the way the router's mixture works: the served option is sampled from a logged mixture of the Decider and a per-context Thompson-sampling model over kinds (the Pipeline Augmentation Plan's workstream G), rewarded by later independent success. It changes which help is served, not evidence, so it needs a kill switch and no successor.

---

## 7. Latency, routes, spend and privacy

### 7.1 The request path

```text
Hint pressed → flush the draft
  ├─ assemble typed state (local reads)                   ~0.1–0.5 s
  ├─ chooser: one Decider request (3 s time box)           under 2 s for a few hundred tokens (router §6.1)
  ├─ writer: one structured chat call (placement + hint)    the bulk; target p50 ≤ 8 s, reported not enforced
  ├─ contracts and leak control (code)                     milliseconds
  └─ show; then in the background: map merge, workbench bridging, outcome placement after submit
```

The chooser and writer are sequential because the writer needs the choice; the chooser's time box falls back rather than delaying the hint. Writing hints speculatively before the learner asks is deferred (§13).

### 7.2 Routes

| Route | Type | Recommended profile | Why |
|---|---|---|---|
| `hint_chooser` | decider (in `DECIDER_TASKS`; never a chat fallback; not overridden by `LEARNLOOP_AI_PROVIDER`) | `openrouter_decider` | Typed probabilities give exact propensities; about $0.0004 a decision |
| `hint_writer` | chat, structured output | a `chatgpt_plan` profile (merged at `57d31c63`; sign-in pending), else a fast OpenRouter chat profile | Interactive. Codex took 29–37 s for blind grading on the stuck-prompt copy (Reader §5.8): too slow for a hint |
| `approach_map` | chat, structured output | any, including `codex_low` | Background |
| `hint_outcome` | chat, structured output | the fast route or `codex_low` | Background, after submit |

Unset chat routes fall back to the active provider and receipts record the resolved model. `learnloop ai latency --provider chatgpt --provider codex_low --runs 3` compares candidates before the switch.

### 7.3 Spend

- Every call uses the spend framework (`ai/spend.py`) with receipts; Codex and the ChatGPT plan are `estimated_only`.
- **Money caps, not count caps:** `hints.max_daily_cost_usd` ($1.00 a day on metered routes, writer and chooser) and `hints.maps.max_daily_cost_usd` ($0.50, maps, merges and outcome placement). No per-attempt or per-day hint count. A capped day falls back to authored hints and says so.
- `hints maps build` takes `--dry-run` and prints the estimate first.

### 7.4 Privacy

The learner's draft and the typed slice of their state go to the configured chat provider, as grading and diagnosis already do, and to the Decider on OpenRouter, which router D6 already discloses. Nothing else leaves the machine.

---

## 8. Where this lives

### 8.1 Surfaces, in order

1. **The practice screen (H2).** The largest reach: every daily-plan item, including PF variants and generated items that have no hints today.
2. **The Reader workbench (H3, inside RW2b).** The best-measured surface: steps give placement and progress directly.
3. **Guided redo (H4).** After a wrong answer, where `error_specific` and `discriminating` hints matter most. The redo is already primed, so hints there change no classification.
4. **The practice-context tutor (H4).** It gains the learner's draft and the map placement as context; a strategy question is answered as a hint of a chosen kind and stays a hint equivalent as today.

### 8.2 Proposed edits to the Reader workbench spec (§5.2–5.5 and related)

The Reader spec is being edited on its own branch, so these are proposals for its author, not edits:

1. **§5.2 ladder: add kinds.** Keep levels 1–5 as the amount of help and the evidence key. Add a column of kinds per level: L1 `approach_question`, `discriminating`; L2 `localize`; L3 `waypoint` (with horizon), `subgoal_plan`, `next_step`, `error_specific`, `discriminating`, `worked_parallel`, `authored`; L4 `worked_chunk` (backward from the goal, leaving the bridge to the learner) and the partial continuation; L5 `walkthrough`. Level 3's description changes from "the principle or a subgoal" to "one of the level-3 kinds".
2. **§5.2 "Authored hints first" → "Authored hints are seeds".** The writer receives them and may serve one verbatim, labelled; they are the fallback when capped or unavailable. Same behaviour, clearer role.
3. **§5.2 reconciliation contract: add rule 6, "It is placed".** When an approach map exists, a hint names its route and target node, and the target's distance matches the chosen horizon. Rule 5's "different strategy" is satisfied by a different kind *or* a different `strategy` slug. Add the kind contracts of §4.2 (a waypoint names a target state and no transformation; a discriminating hint names two hypotheses with differing predicted results; a worked chunk leaves a gap).
4. **§5.2 feedback shortcuts get defined effects.** "Different approach" switches route on the map (or kind at the same level); "Too big a jump" shortens the horizon or lowers the grain; "I don't understand the notation" is passed to the writer as a notation note.
5. **§5.5 chooser: one Decider request, two questions, sampled.** `kind_level` (a `choice` over the allowed (kind, level) pairs) and `horizon` (a `score`), sampled from the Decider's own probabilities with the drawn probability logged as the propensity. Replace "There is no randomization of help quality (§17)" with the §4.5 argument: sampling within the judge's own uncertainty is not a hint-quality experiment, and it is what makes kinds evaluable. Keep §17's row against deliberately worse help.
6. **§5.5 state: add** the approach-map placement from the last check, the learner's route preference, per-kind history on these facets (continued unaided, "doesn't connect"), time since the last hint and whether the work changed since it, and a closed probe episode's recommended tutor move.
7. **§5.7 data: share one assists table.** Name it `help_assists`, with a `surface` column (`practice` | `workbench` | `guided_redo` | `tutor`) and nullable workbench fields, created by whichever of RW2b and H0 merges first. Add `kind`, `horizon`, `route_id`, `from_node_id`, `target_node_id`, `map_id`, `options_json`, `probabilities_json`, `propensity`, `seed`, `policy_version`, `shown`, `counted_by`. RW2b's check and bridge rows stay in the same table with their kinds.
8. **§5.8 routes: share them.** `workbench_hint` becomes `hint_writer` and `workbench_level_chooser` becomes `hint_chooser`; add `approach_map`. One writer, one chooser, one set of receipts for every surface.
9. **§5.3 "Check my work" reads the map.** Step verdicts can name the map node a step reaches, which gives placement for free.
10. **§17: the "Full solution graphs" row** is partly superseded: approach maps (small graphs with alternative routes) are built by this spec's H1 and RW2b reads them when present. Keep the deferral for full step-level graphs with every branch.
11. **§15 workbench block: add per-kind rows** with propensities (§6.3) beside "help level taken vs offered".
12. **§16 D8:** the first offer becomes a (level, kind, horizon) choice, sampled from the Decider's probabilities, default style "balanced"; fallback "authored hints, then level 1 and up".

---

## 9. Data

Migrations are numbered when they land (`ls migrations/`; head 180 on this base). Follow `CLAUDE.md`'s head-fixture procedure.

| Table | Role (`db/table_roles.py`) | Phase | Contents |
|---|---|---|---|
| `help_assists` | RAW_LEDGER | H0 (or RW2b, whichever first) | `id`, `surface`, `practice_item_id`, `practice_item_hash`, `practice_session_id`, `attempt_id` (filled at submit), `workbench_session_id?`, `kind`, `level`, `horizon?`, `route_id?`, `from_node_id?`, `target_node_id?`, `map_id?`, `strategy?`, `body_md?` (null for authored reveals: the item has the text), `authored_index?`, `work_hash`, `work_chars`, `placement_json?`, `chooser` (`decider` \| `fallback` \| `learner_pick` \| `none`), `options_json?`, `probabilities_json?`, `propensity?`, `seed?`, `policy_version?`, `request` (`more` \| shortcut \| pick), `feedback_text?`, `feedback_shortcut?`, `contract_failures_json?`, `leak_flags_json?`, `shown`, `counted_by` (`client` \| `server`), `model?`, `prompt_version?`, `input_hash?`, `latency_ms?`, `requested_at`, `shown_at?` |
| `approach_maps` | WORKFLOW (paid output, never rebuilt) | H1 | `id`, `practice_item_id`, `practice_item_hash`, `family_id?`, `version`, `map_json`, `seeds_json` (which trace contract, skeleton, spans, attempts and authored hints it was built from), `validation_json`, `verified_goal`, `model`, `prompt_version`, `input_hash`, `created_at`, `supersedes_id?` |

- **No DERIVED table, so no replayer.** Replay never reads either table: evidence lives in `practice_attempts` (`hints_used`, `primed`) and `reveal_events`.
- **No table rebuild:** no new `interaction_events` kind and no new reveal kind (`tutor_answer` with a `hint:` basis).
- **`judgment_ledger` tasks:** `hint_choice` (judge `decider`), `hint_fit` (judge `learner_card`, the "doesn't connect" replies), `approach_map_valid` (judge `verifier`, the code validation). The ledger's judge CHECK already admits `decider`, `verifier` and `learner_card` (`migrations/175_decider_judgments_and_receipt_labels.sql:36`).
- **Model-call receipts** carry `judge` (`decider` or `llm`), `question_set_version` and `state_hash` (migration 175), as the router's do.
- **H0's authored-reveal rows** are written by a fire-and-forget RPC (`practice.record_hint_reveal`) with `counted_by = 'client'`. They are telemetry only; submit keeps using the client's count for authored hints.

**Config** (`[hints]`, modelled defaults; each phase recomputes the latest `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry with a "no scoring, scheduling, projection or serving change" note, as the Reader spec's phases do): `telemetry_enabled`, `adaptive_enabled`, `chooser_enabled`, `choice_policy` (`sample` | `argmax`), `chooser_timeout_seconds` (3), `outcome_placement_enabled`, `guided_redo_enabled`, `tutor_enabled`, `authored_offer_after_seconds` (4), `max_daily_cost_usd` (1.00), `price_per_million`; `[hints.maps]`: `enabled`, `build_on_serve`, `max_daily_cost_usd` (0.50). Routes: `ai.routing.hint_chooser`, `hint_writer`, `approach_map`, `hint_outcome`.

---

## 10. Phases, successors and kill switches

Every phase goes through `implementation_goal.md` §2's loop (implement, adversarial review, fix, gate, integrate) and merges alone. Sizes use the Reader spec's key: **S** about a day, **M** two to four days, **L** one to two weeks.

| Phase | Builds | Needs | Size | Data it starts | Kill switch (restores) |
|---|---|---|---|---|---|
| **H0. Hint telemetry** | `help_assists` (migration); `practice.record_hint_reveal` for authored reveals with time and draft hash; the report's descriptive rows with authored hints as the baseline kind. No model call; no visible change | `main` | **S** | The baseline: how today's hints are used and what follows | `hints.telemetry_enabled` (no rows) |
| **H1. Approach maps** | `approach_maps` (migration); builder and validator (route `approach_map`); build on serve; inline build; lazy learner-route merge; family templates; `hints maps build --dry-run` | H0 | **M** | Maps for served items; validation failures by reason; route counts by origin | `hints.maps.enabled` (no builds; nothing reads maps) |
| **H2. Adaptive hints on the practice screen** | `practice.request_hint`; the service (state, chooser, writer, contracts, leak control); server-side fold and `primed` at submit; `tutor_answer` reveal rows; labels; "Doesn't connect"; the style menu; the clickable hint control; authored fallback; outcome placement; per-kind report rows | H1 (works without maps, with fewer kinds); the Decider (merged); a fast chat profile signed in | **L** | Decisions with propensities and outcomes | `hints.adaptive_enabled` (byte-identical practice screen); `hints.chooser_enabled`; `hints.choice_policy`; `hints.outcome_placement_enabled` |
| **H3. The workbench** | Inside RW2b: Help calls the service; ladder kinds; "Check my work" reads the map; shared table and routes (§8.2) | RW2b; H2 | **S** on top of RW2b | Kinds with step-level outcomes | RW2b's switches |
| **H4. Guided redo and the tutor** | Hints during the redo from the prefix and diagnosis; the practice tutor reads the draft and placement; strategy questions answered as a chosen kind | H2 | **S–M** | Kinds after a wrong answer | `hints.guided_redo_enabled`, `hints.tutor_enabled` |
| **H5. Off-policy report** | Self-normalized IPS and doubly robust estimates per kind, with effective sample sizes and bootstrap intervals; the expertise-reversal split; abuse and avoidance counts | H2 plus about a month of rows | **S** | — | Report only |

**Order.** H0 now: it is small and starts the baseline clock. H1 next. H2 when a fast chat profile is signed in; it is the phase the owner sees. H3 rides on RW2b whenever that lands; if RW2b lands first, it builds `help_assists` and calls the service rather than writing its own (§8.2). H4 after H2's checkpoint. H5 after a month of H2 data.

**Owner checkpoint after H2:** two weeks of ordinary practice, then the report: kinds served by placement intent, unaided next progress, "doesn't connect" by kind and shortcut, latency p50/p95 by route, cost.

### 10.1 Successor ruling

**No successor in v1.** Every hint maps onto `hints_used`, `primed` and `reveal_events` with their existing meaning (§5); the new tables are RAW_LEDGER and WORKFLOW, and replay reads neither. Precedents: the Reader spec's D6, the stuck-reading context extension. The H2 reviewer confirms the §5 table against `resolve_attempt_activity_policy` and both certification projections; if any mapping needs a new rule, that part stops and takes the next free `mvp-0.N` tag at merge.

**Named successors for later** (each the next free `mvp-0.N` at its merge):
1. **Kind-aware assistance weights.** Weight help by level or kind instead of counting hints, in `HintPolicy`'s per-count maps and in the field's `lo_general+hints` arm (`1 − 0.2k`) and S5 signals. Trigger in §13.
2. **Unsolicited hints.** A proactive offer changes how many attempts become assisted, and so what can certify. Deferred (§13).
3. **Authored reveals in the reveal ledger.** Today a "near-give-away" authored hint writes no reveal row (§3.2), so it can never contribute to auto-prime. Recording it would change evidence; not proposed for v1, listed so the inconsistency is on record.

---

## 11. Gates and tests

| # | Gate |
|---|---|
| G-H1 | **Kill-switch parity.** With `hints.adaptive_enabled = false`, the practice RPCs and screen are byte-identical to `main` on fixture copies; with `hints.maps.enabled = false` no map is built or read; with `hints.telemetry_enabled = false` no `help_assists` row is written |
| G-H2 | **Evidence mapping.** For each kind and level, shown on the practice screen, in guided redo and through the tutor, the submitted attempt's `hints_used`, `primed` and reveal rows match §5, and `resolve_attempt_activity_policy` gives the stated eligibility. A rebuild reproduces evidence identically |
| G-H3 | **No double count, no lost hint.** Authored reveals counted by the client and adaptive hints counted by the server never overlap; a cancelled or withheld hint counts nothing; an authored fallback cancels the pending adaptive request; `submit_dont_know` and `submit_attempt` both include shown adaptive hints |
| G-H4 | **The grader stays blind.** The rendered blind-grading prompt for a hinted attempt contains no hint, kind, map, placement or learner state |
| G-H5 | **Leak control.** A level-1–3 hint containing the expected answer (including short numeric answers) is never shown; no waypoint or label carries a `leak` node's state |
| G-H6 | **Contracts.** A fake writer that cites no learner work, continues past the first questionable point, repeats a strategy after "doesn't connect", misses the chosen horizon, or breaks a kind contract is caught, re-asked once, then downgraded as §4.6 says |
| G-H7 | **Propensities.** The logged propensity equals the sampling probability of the drawn option; seeds reproduce draws; `argmax` logs 1; fallback logs 1; a learner pick logs none; options whose preconditions fail are never offered |
| G-H8 | **Chooser fallback.** Time-out, unavailability or a spent-out Decider produce the fallback order, flagged on the row; the Decider route never falls back to chat |
| G-H9 | **Maps.** The validator rejects cycles, routes that do not reach the goal, foreign facets and leaking labels; a failing map is never stored; a revised item does not reuse its old map; learner routes come only from correct or PF-c-valid attempts |
| G-H10 | **Replay.** Rebuild and replay make zero model and embedding calls with `help_assists` and `approach_maps` populated |
| G-H11 | **Spend.** Daily money caps hold and fall back to authored hints; Codex and plan receipts are `estimated_only`; `hints maps build --dry-run` writes nothing |
| G-H12 | **Labels.** Every adaptive hint carries "AI-written" and its kind label; authored hints carry "from the item"; heavy help says so. A wording lint rejects "you don't understand", "you struggle", "weak" |
| G-H13 | **Boundaries.** An import-linter contract: `learnloop.hints` imports no evidence writer; new RPCs are pinned desktop-only in `tests/test_mobile_allowlist.py`; new tables are classified in `db/table_roles.py` |
| G-H14 | **Cold and probe parity.** On a cold check the banner and rejection are unchanged; during a diagnostic block no hint request reaches a model |

**Tests** (fakes only: `tests/structured_ai.py`, `tests/decider_fakes.py`, `tests/openai_fakes.py`; vault builders from `tests/helpers.py`):
- **H0:** `test_hint_telemetry.py` (rows, timing, `counted_by`, kill switch, no evidence change).
- **H1:** `test_approach_maps.py` (seeds from trace contracts, skeletons and authored hints; validator; build on serve; inline build; learner-route merge; revision keys; dry-run); `test_approach_map_replay.py`.
- **H2:** `test_hint_service.py` (state assembly, options and preconditions, sampling and propensities, fallback); `test_hint_contracts.py` (G-H5, G-H6); `test_hint_evidence.py` (G-H2, G-H3); `test_hint_blind.py` (G-H4); `test_hint_kill_switch.py`; `test_hint_report.py`; vitest for the hint panel, labels, feedback box, cancel and the clickable control.
- **H3:** RW2b's `test_workbench_hints.py` and `test_workbench_chooser.py` call the shared service.
- **H4:** `test_guided_redo_hints.py`; `test_tutor_practice_context.py` (draft and placement in context; strategy questions as hints; hint-equivalent count unchanged).
- **H5:** `test_hint_ope.py` (IPS and doubly robust on synthetic logs with known values; no-support reporting).

**Every phase runs** `uv run lint-imports --no-cache`, `uv run pytest -n auto`, `uv run pytest -m durability`, `npm run typecheck && npm test` when the frontend changes, and the DB reference scripts when the schema changes.

---

## 12. Owner decisions: recommended defaults

| # | Decision | Recommended default |
|---|---|---|
| D1 | Where adaptive hints start | The practice screen (H2), before the workbench; H0 telemetry first |
| D2 | Kinds in v1 | All of §4.2, each offered only when its preconditions hold |
| D3 | Who chooses | The Decider over typed state plus the help style, time-boxed; fallback authored hints, then next step |
| D4 | How the served kind is picked | **Sampled from the Decider's probabilities**, propensity logged, no exploration floor. Alternative: argmax (no off-policy evaluation). If support turns out too thin to compare kinds after a month, decide on a floor then (the router uses 0.02) |
| D5 | Help style control | Three settings in the hint panel's "⋯" menu and Settings; default balanced; never on the main screen |
| D6 | Approach maps | Built in the background when an item is shown; inline on the first hint if missing; learner routes merged lazily; Codex allowed for building |
| D7 | Authored hints | Kept as seed and fallback; authoring unchanged in v1 |
| D8 | Evidence | Each shown hint adds to `hints_used` (counted server-side); levels 4–5 set `primed`; key overlap writes `tutor_answer` reveals; no successor |
| D9 | Writer route | A `chatgpt_plan` profile once signed in; until then a fast OpenRouter chat profile; never Codex for interactive hints |
| D10 | Spend | $1.00 a day for writer and chooser, $0.50 for maps and outcome placement (metered only); no count caps |
| D11 | Outcome placement for hinted wrong answers | On |
| D12 | Unsolicited hints | None in v1 (§13) |
| D13 | The hint control | The key bar's `^h hint` becomes clickable; nothing else is added |
| D14 | The practice tutor | Gains the learner's draft and the map placement as context (H4) |

---

## 13. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **A learned chooser** (a logged mixture of the Decider and a per-context Thompson-sampling model over kinds; workstream G) | ≥ 300 decisions with matured later outcomes, and at least two kinds each with an effective sample size ≥ 30 in one placement-intent band |
| **Kind-aware assistance weights** (successor 1) | H5 shows two kinds' later independent success differ with non-overlapping intervals in some band |
| **Unsolicited hints** (Maniktala et al.'s targeted proactive help; assertions placed in the workbench) | The avoidance count shows wrong submissions after long work with no hint in ≥ 20% of a month's wrong attempts, *and* the owner opts in. Targeted only: random proactive hints hurt in the literature (§1.6) |
| **Speculative hint writing** (write the likely hint before Hint is pressed) | H2's writer p50 exceeds 8 s on the chosen route for two weeks |
| **Authoring emits maps instead of hint strings** | At the H2 checkpoint, `authored` is served for under 10% of hints |
| **Symbolic checks on map edges** (PF's sandbox pattern) | "Doesn't connect" or contract failures are traced to wrong map edges in ≥ 5 cases |
| **The diagnoser reads the map** (placing errors on routes) | H1 maps exist for most served items and the diagnoser's reports name route confusion; a prompt-version suffix, probably no successor |
| **An offline hint-quality harness** (Price et al.'s QualityScore pattern: replay logged stuck points under a new prompt) | A prompt or model change to `hint_writer` is proposed. LLM judges alone are not trusted for subgoaling quality (Tithi et al. 2025) |
| **Bottom-out plus self-explanation** (VanLehn's alternative: show the step, ask why it works) | Walkthroughs are a large share of hints for a month |
| **Learner-written subgoal labels** ("What is the purpose of your lines 2–4?", with hints *or* feedback on the label, not both; Margulieux & Catrambone 2016) as a hint kind and a placement signal | The workbench (RW2b) is live, so chunks of the learner's own work are addressable |
| **A simulated-student verifier** (Phung et al. 2024: keep a hint only if a model "student" does better with it) | "Doesn't connect" exceeds a quarter of hints in a month, or contract checks pass hints the learner rejects |
| **Hint timing as a field signal** (H0 makes it recordable) | The field's S5 signals are activated; consuming it changes serving, so it is a successor there |

---

## 14. Open questions

1. **Will the Decider spread its probability?** If it nearly always puts ~1.0 on one kind, sampling buys little support and D4's floor question returns early.
2. **Is a single answer box enough work to place?** Many practice-screen drafts are one line or empty. Placement then defaults to the givens, and waypoint hints may matter most in the workbench. H2's report will show how often the draft is empty at Hint.
3. **Per item or per family?** Maps are stored per item revision with family templates. If siblings' maps turn out identical in structure, a family-level row would be cheaper.
4. **Is outcome placement worth its call?** It is the only way to measure "got past the waypoint" on the practice screen; the H2 checkpoint should look at whether it changes any conclusion.
5. **`submit_dont_know`'s asymmetry** (it folds no tutor questions and applies no clamp) predates this spec. Should H2 fix it, which changes `hints_used` on those attempts, or leave it?
6. **The practice tutor's "never confirm partial work" rule** conflicts with hints that say what stands. This spec treats them as different kinds of help, both recorded; the owner may prefer one rule.
7. **Should discriminating checks feed the hypothesis machinery** directly (as a cheap observation), rather than only through the diagnoser's reading of the final answer? That would be a new observation source and a successor.

---

## 15. Cross-spec notes (record when each phase merges)

- **Reader workbench.** §8.2's twelve proposals. RW2b's hint writer, chooser and assists table become this spec's shared ones; whichever merges first creates them.
- **Learner field.** H0 records hint timing, which `field/probability_states.py:99-101` lists as not recorded. No new signal source in v1; kind-aware weights are a successor (§10.1).
- **Router.** The hint chooser borrows the router's propensity convention and receipt fields; hints stay out of router decisions.
- **Blind grading and diagnosis.** The grader is unchanged; the diagnoser's `assisted` flag is unchanged.
- **PF.** Published variants keep `hints = []`; adaptive hints cover them. PF skeletons gain a consumer (map seeds).
- **Exercise import and authoring.** Unchanged in v1; `MAX_HINTS = 4` stays as authoring's own limit, not a limit on hints served.
- **Learner-text gaps.** "Doesn't connect" text becomes a learner-text source (`hint_feedback`) once that pipeline merges, beside the Reader's `workbench_stuck`.
- **Count caps elsewhere, for the owner's look** (as Reader §20.7 did): the practice tutor's `max_questions_practice` (3, `config/schema.py:540`) is a count cap on help of the same kind this spec leaves uncapped.

---

*Related: `docs/brainstorming/data-driven-hints-in-ITS.pdf` (the source) · `docs/brainstorming/Improving Reader's design.md` (the owner's dialogue, on the Reader spec branch) · `spec_reader_workbench_v1.md` §5 · `spec_action_router_v1.md` §0, §6, §7.3 · `spec_learner_field_v1.md` §3.1, §4.3 · `docs/brainstorming/Pipeline Augmentation Plan.md` workstream G · `daily_loop_frictionless_defaults.md`*
