# Adaptive hints: waypoints, subgoals and help written for the learner's current work (v1)

**Status:** draft for owner review (2026-10-13); aligned with the Reader workbench spec the same day (§16). Docs only; nothing here is built.

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
| `spec_reader_workbench_v1.md` (merged on `main` at `c46b403c`) | Its RW2b help ladder, reconciliation contract and first-offer chooser (§5.2–5.5) are the workbench face of this spec (this spec's phase H3). This spec generalizes them into one hint service for every surface and adds kinds, horizon, approach maps and propensities. That spec ruled on this spec's §8.2 proposals in its §20.11 (all twelve applied, seven with an adaptation) and made nine requests of this spec in its §18; **§16 records how each was applied here.** The rule for conflicts is shared: this spec wins on hint generation (kinds, the writer and its contracts, approach maps, the chooser and how it picks, hint spend); the Reader spec wins on the Reader's presentation (the ladder, labels, step anchors) and on evidence mapping, which this spec adopts on every surface (§5) |
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
- **H4. Help is never withheld.** The learner can always ask for more, say a hint doesn't connect, ask for the book's way, or take worked help up to the worked answer. Abuse and avoidance are measured, never gated.
- **H5. Honest labels.** Every hint shows where it came from (AI-written, from the item, from a named source) and what kind it is. Worked help (levels 4–5) says so before it is taken, not after (Reader §5.2; UX principle U11).
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
| Reader workbench Help (RW2b, not built) | Specified in Reader §5.2–5.5, which since its §20.11 calls this service and defines no writer, chooser or map builder of its own (Reader G64) | RW2b calls the service; the Reader keeps its ladder and levels, its step rules of the reconciliation contract, the evidence mapping and the presentation (§16) | H3, inside RW2b |
| Guided redo after a wrong answer | Preserved prefix plus a rewrite, no hints (§3.2) | A Hint during the redo calls the service, starting from the preserved prefix and the diagnosis | H4 |
| Practice-context tutor | Socratic, blind to the draft (§3.2) | Reads the draft and the map placement; a strategy question ("how do I go on?") is answered as a hint of a chosen kind | H4 |

`HintRequestV1`: the surface; the item; the practice session; the learner's **current work** (the practice-screen draft read from the session checkpoint; in the workbench the steps with ids, the check's verdicts and step graph, the about-step and `continue_from`, Reader §5.2; the redo's prefix and rewrite); this attempt's earlier hints with kinds and feedback; the open rival explanations the surface knows of (§4.2); the help style in force (§4.5); a **level the learner took**, if any (a workbench rung other than the suggested one, or worked help elsewhere; §4.2); and the request: `more` (the default: Hint pressed, or a rung taken), `feedback` (a "doesn't connect" reply with one of four shortcuts, `not_where_stuck`, `too_big`, `learner_route` or `notation`, and optional text; §4.2), or a learner pick, `book_way` ("show me the book's way") or `smaller_step` ("a smaller step toward this goal").

`HintResultV1`: the hint text; kind, level and horizon; the placement (§4.4); labels (§4.8); the evidence it carries (§5); for a `discriminating` question, its rivals, the answer each predicts and its EIG (§4.2); the assist row id.

### 4.2 Kinds, levels and horizon

The Reader spec's ladder measures **how much of the solution the help does for the learner** (levels 1–5). That stays, and it alone decides evidence (§5). This spec adds two axes the ladder lacks:
- **kind:** the form the help takes at a level;
- **horizon:** for waypoints, how many steps ahead of the learner's current state the hint points.

| Kind | Level | What it says | Basis (§1) | Contract checked in code, beyond §4.6's shared rules | Existing tutor move (§3.2) |
|---|---|---|---|---|---|
| `approach_question` | 1 | A question about the approach, an assumption or the goal ("What does F have to be at the left end of the support?"). With no work yet, often **"What would your first move be?"**: it helps the learner start and its answer places them for the next hint | Strategic and metacognitive hints; VanLehn's "point"; Kalyuga's first-step test | Declares what it asks about (approach, assumption, goal or first move); states nothing about the solution | `elicit_reasoning` |
| `discriminating` | 1 (as a question) or 3 | A check whose result differs between two open explanations of the learner's trouble ("Before changing anything: what does your formula give at x = 0?"). Never states either rival or the correction | Error-specific feedback; LearnLoop's misconception discrimination | Names at least two open rivals from the request, and the answer each predicts; the predicted answers differ. **Chosen among candidates by expected information gain** on every surface (below); a zero-EIG question is never shown | `contrast_cases`, `counterexample` |
| `localize` | 2 | Names the first questionable part of the learner's work, without the correction | Reader §5.2 level 2 | Quotes the learner's work; contains no corrected expression | `localize_error` |
| `waypoint` | 3 | **An abstract intermediate goal state on the learner's route, `horizon` ≥ 2 steps ahead: what will be true, not how to get there** ("Aim for a CDF that is 0 at the left end and 1 at the right; you are about two steps from that") | Cody et al. 2022 and Alam et al. 2023 (mixed evidence, §1.2); Sweller & Levine 1982 | Targets a map node on the learner's route at the chosen horizon, reachable from their placement; names no transformation between here and there; never a node marked `leak` (§4.3) | `state_subgoal` |
| `subgoal_plan` | 3 | The rest of the route as a few **labelled subgoals**, the current one marked, with no step content ("Find the CDF on the support ✓ · Fix the constant with a boundary value ← here · Extend to the whole line"). Labels are concrete for a weaker background and abstract when the background is there | Catrambone 1998; Margulieux et al. 2016; Eagle & Barnes 2014 | Every label maps to a map node; labels carry no expression from later nodes; the writer declares the register (concrete or abstract) | `state_subgoal` |
| `next_step` | 3 | The single next action from the learner's checkpoint, in their notation, without doing it ("Differentiate your third line and compare it with the given density") | Next-step hints (Hint Factory) | Targets the adjacent node (horizon 1); one action | — |
| `error_specific` | 3 | Names what is wrong in a quoted step and the principle it violates, without the corrected result | The chapter's error-specific feedback; VanLehn's "teach" | Quotes the step; names a principle; contains no corrected value | `explanation` |
| `worked_parallel` | 3 | The same move worked on a *different* instance, preferably a worked example from the learner's own source, labelled with its origin | Worked examples (Renkl & Atkinson) | The item's own values absent; a source quote passes T6 verification; T6's item-bound exclusions apply (`source_retrieval/corpus.py:150-163`) | `worked_example` |
| `continuation` | 4 | The **next portion forward** from the learner's last valid checkpoint, on their route and in their notation ("writes step 5 for you"), stopping short of the goal | Partially worked steps (Maniktala et al. 2020's proactive partially worked steps); the Reader's level 4 | Starts at the placement node (in the workbench, the node `continue_from` reaches); stays on the learner's route; with a map, ends at a node short of the goal; carries worked-help evidence (§5) | — |
| `worked_chunk` | 4 | A chunk of *this* problem worked **backward from the goal** ("To show X it is enough to show Y; Y follows once you have Z"), each piece saying what it establishes, how, and why the next piece needs it, and leaving the bridge from the learner's last valid state to Z for them | Shabrina et al. 2023 (backward-first worked examples; chunks with explanations); Maniktala et al.'s assertions | Leaves at least one gap the learner fills; every piece carries its what/how/why; carries worked-help evidence (§5) | `worked_example` |
| `walkthrough` | 5 | The full solution, keeping the learner's route where it is valid | Bottom-out hints | Worked help (§5) | — |
| `authored` | 3 | One of the item's authored hints, verbatim, labelled "from the item" | — | Used when it fits the placement, or as the fallback (§4.7) | — |

**Horizon** for a waypoint counts map edges along the learner's route, with two named ends: "the end of the current subgoal" and "the goal". It is chosen with the kind (§4.5), never fixed. A horizon of 1 is a next step, so `next_step` and `waypoint` are two ends of one scale.

**"More", the learner's picks and the "doesn't connect" shortcuts.** The learner can always ask again. Each of these constrains the options the chooser sees; none is a rule about what helps. The meanings are the Reader's (Reader §5.2, D21, §20.11 C2, C16, C17), the same on every surface:
- **"More"** (Hint pressed again; in the workbench, a rung taken) lets the chooser raise the level or shorten the horizon. **After a waypoint, every option at level 3 or above aims at the same target node, and `next_step` toward it is among them**, because waypoint learners in Cody et al. who could not bridge tried, failed and gave up (§1.2).
- **"A smaller step toward this goal"** (`smaller_step`, under a waypoint; the workbench's `Ctrl+Shift+H`) is the learner's pick of `next_step` toward the same target at the same level: the way down that never depends on the chooser.
- **"Show me the book's way"** (`book_way`, under every hint) asks for the next hint on the reference route at the same level. It is the only way a hint leaves the learner's route while that route is valid (rule 4).
- **Worked help is the learner's to take** (Reader §5.2: each rung states its consequence before it is taken; C16: a higher rung is the learner's). In the workbench the learner takes rung 4 or 5 on the ladder. On surfaces without a ladder (the practice screen, guided redo, the tutor) a Hint press is served from levels 1–3, and levels 4–5 come only from the hint panel's picks *work a piece of it for me* (level 4) and *show me the worked answer* (level 5), each labelled *worked help ◌* before it is taken (§4.8). A taken level fixes the level; the kind at it is still chosen (§4.5).
- **A "doesn't connect" reply** (`feedback`) is answered at once, **at the level of the hint it answers**, so a reply never raises the help without the learner taking it. Its shortcut:
  - **"That's not where I'm stuck"** (`not_where_stuck`) moves the hint. In the workbench the picked step becomes the next hint's `about_step` (Reader §5.2). Elsewhere the learner may select the part of their draft they mean, or say it in the text; the next hint quotes that part and is placed from there. Either way it must not repeat the earlier localization.
  - **"Too big a jump"** (`too_big`) asks for a smaller step: after a waypoint, a shorter horizon toward the same target (down to `next_step`); otherwise a finer kind at the same level (a plan becomes the next step; a worked parallel becomes a step in the learner's own problem).
  - **"I'm using a different approach"** (`learner_route`) **keeps the learner's route** (rule 4): the next hint is placed on the learner's route (an existing route of the map, or `new_route` when the map lacks it) and names the part of their work it builds on. It never switches to the reference route; only `book_way` does. *This reverses this spec's first draft*, where "different approach" asked to switch route; the stored value is `learner_route` so the shared column cannot be read both ways.
  - **"The notation"** (`notation`) keeps the idea and restates it in the learner's symbols, quoting at least one of them and defining any it introduces. It is the one reply exempt from rule 5's change of strategy (§4.6).
  - Every reply, with or without a shortcut or text, appends a `learner_card` verdict `different` on task `hint_fit` (§5).

**Discriminating questions: chosen by expected information gain** (Reader §5.2, on every surface). The `discriminating` kind is offered only when two or more rival explanations of the learner's trouble are open. The rivals come from the request: on every surface, the open hypotheses and durable misconceptions on the item's facets (the diagnoser's overlay), the rival causes of a diagnosed earlier attempt on the item (`unresolved_cause_factors.candidate_causes_json`), and gaps named from this attempt's learner text; the workbench adds its check's error-kind guess and the alternatives to it.
- **Selection.** The writer proposes a few candidate questions, each with the answer it predicts under each rival. The service compiles each candidate as an instrument with one conditional row per rival and ranks them with the existing `instrument_expected_information_gain` (`diagnosis/probe_families.py:467`) under the rivals' current weights: an open probe episode's posterior or the facet's `hypothesis_marginal` where they exist, uniform otherwise (labelled). A candidate whose rivals all predict the same answer has zero EIG and is dropped by construction; the best is shown; nothing is hand-weighted. The ranking is computed, so it adds no model call.
- **No positive EIG:** no discriminating question is shown. At level 1 the hint is an `approach_question`, at level 3 a `next_step`, and it says why ("no question separates these two readings; here is a question about your approach", or "… here is the next step"). The row keeps the drawn option and its propensity and records the served kind, as a contract downgrade does (§4.6).
- **Its label says what it is before it is answered:** *a question that tells apart two explanations · not graded · counts as a hint* (at level 3, *a check that tells them apart*).
- **The answer** is typed in the question's own one-line answer box, never in the answer draft or a step, so it is never part of the submitted answer and the blind grader never sees it (Reader C5). It is a `help_assists` row (`assist_kind = 'discriminate_answer'`); one line then says what it settled, or that both readings still stand, and the next hint's context carries it. In the workbench it also enters the diagnoser's trace (Reader §5.4). It is learner text (§9). It moves no posterior and writes no probe observation.
- **One at a time.** After one has been answered at a placement (in the workbench, on a step), `discriminating` leaves the chooser's options there; in the workbench, taking rung 1 again asks for another, which must clear the same ranking.

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
- **Workbench:** the step list with ids, and "Check my work"'s verdicts and step graph when a check has run (Reader §5.2). The check names the map node and route each `valid` step reaches (`map_node_id`, `route_id`), so the placement starts from **the node the `continue_from` step reaches** (Reader rule 7, D45: a standing step that does not depend on the questionable one), and the horizon is measured from there; the writer's quoted placement is used only when no check has run. The hint is shown under its `about_step`, which may differ from its checkpoint (Reader rule 3). This is stricter than, and compatible with, rule 2 below (Reader C3).
- **Guided redo:** the preserved prefix plus the rewrite so far; the diagnosis's failed checkpoints mark the questionable point.
- **A valid route the map lacks** is placed as `new_route` and treated as the learner's route (Reader §5.2 contract rule 4). It is merged at the next refresh if the attempt succeeds.
- **Work unlike any route and not clearly valid** gets an `approach_question` about what the learner is trying, rather than a confident hint toward a route they are not on (Price et al. 2019; VanLehn's plan recognition).
- **No map** (none yet and the inline build failed): placement is relative to the reference solution, and waypoint and subgoal kinds are not offered for that hint.

Placements are logged; they are what make outcomes measurable in map terms (§6).

### 4.5 The chooser: kind, level and horizon as a judgment

**Who chooses.** The Decider, in one request with two named questions over one state (route `hint_chooser`, added to `DECIDER_TASKS`):
- `kind_level`: a `choice` over the (kind, level) options the request allows. Options whose preconditions fail are absent: `discriminating` without two open rivals (§4.2) or once one has been answered at this placement, `waypoint` and `subgoal_plan` without a map, `worked_parallel` without a usable source example or another instance, options excluded by the learner's shortcut or pick. **Levels 4–5 are options only where the learner takes the level:** in the workbench, whose suggestion may be any rung because the learner still takes it (Reader §5.5); elsewhere, only after the learner picked worked help (§4.2). In the workbench, with two or more rivals open on the about-step, level 1's only option is the discriminating question (Reader G37).
- `horizon`: a `score` over an ordinal rubric (next step · two steps · end of the current subgoal · the goal), asked only when a waypoint is among the options.

**The state it reads** (typed and short; the Reader §5.5 list, extended):
- the item's LO placement intent and mastery; facet evidence split into demonstrated unaided and assisted-only;
- the live predictor's P(success) and variance for the item;
- open hypotheses and misconceptions on the item's facets, as typed records from the diagnoser's overlay, with probabilities where the hypothesis machinery has them; a closed probe episode's recommended tutor move, if any;
- the learner's history with hint kinds on these facets: kinds shown, whether they continued without more help, "doesn't connect" replies by shortcut, later independent outcomes (§6.1's per-hint outcomes; in the workbench through RW2c's `help_outcomes` once it lands, which reads them rather than deriving them again, Reader §5.10);
- the learner's route preference (§4.3);
- this attempt: time since the item was shown; whether there is work yet; the previous hint's placement, kind and whether the work changed since; feedback given; in the workbench also the map placement from the last check, this session's failed checks, hints, rivals and named gaps (Reader §5.5);
- the help style: **let me struggle · balanced · guide me** (default balanced). **One stored preference on every surface** (`hints.help_style`), set in Settings or from the hint panel's "⋯" menu; in the workbench the header's per-problem override (`workbench_sessions.help_style`, Reader D31) wins for that session. "Let me struggle" asks for the least specific help that could work (questions and goals to aim for first, in line with Roll et al.'s finding that trying first helps novices); "guide me" asks for more specific help sooner (next steps, then worked steps where the learner takes them). It is a stated preference the Decider weighs, never a block: "More" still goes up.

**The instructions** state the research, not thresholds: less specific help (approach questions, waypoints, abstract labels) tends to suit higher prior knowledge and steady progress, and more specific help (next steps, concrete labels, error-specific hints, worked chunks) lower prior knowledge or a learner who is stuck (§1.5); a waypoint is for a learner whose state says they can bridge to it, and the direct evidence for waypoints is mixed (§1.2); after help that did not work, be more specific, and after progress, less (§1.6); with no work yet, asking for the first move is cheap and informative; with competing explanations for an error, a discriminating check both helps and tells them apart; keep the learner's route; when the work matches no route, ask. The Decider weighs these against the typed state. **No constant in this spec decides the kind.**

**How the served option is picked: sampled from the Decider's own probabilities.** The Decider returns a probability for every option. The service samples the (kind, level) option, and the horizon, from those probabilities and logs the probability of what it drew as the **propensity**, as the router's mixture does ("a propensity only has to be the distribution actually sampled from", router spec §0). This is not an experiment that withholds better help. When the Decider is confident it puts nearly all the probability on one option, which is then served nearly always. When it spreads probability it is unsure which kind is best, and acting in proportion to that uncertainty is Thompson-style probability matching. It is also what makes kinds comparable later (§6). `hints.choice_policy = "argmax"` serves the top option instead and logs propensity 1 (no off-policy evaluation is then possible; D4).

**A level the learner took** (Reader §5.5). When the request carries a level the learner took (a workbench rung other than the suggested one, or worked help picked elsewhere), the level is the learner's (`level_source = 'learner_pick'`) and the kind at that level is drawn from the Decider's probabilities over that level's options: renormalized from the suggestion's request where one was made (the workbench's ladder), otherwise from a request over that level's options alone. The propensity logged is that conditional probability (1 where the level has one option: level 5, and level 1 when rivals are open in the workbench). Taking the workbench's suggested rung serves the drawn option with its joint probability (`level_source = 'offered'`).

**Fallback.** The chooser falls back on its time box (3 s, as in Reader §5.5), an unavailable or spent-out Decider, or `hints.chooser_enabled = false` (the one chooser switch on every surface; the Reader's first-draft `workbench.level_chooser_enabled` is withdrawn, Reader C19). Fallback choices are logged as `chooser = 'fallback'`, propensity 1:
- **The practice screen, guided redo and the tutor:** the authored hints in order while they last, then `next_step`; after a "doesn't connect" reply, the next kind in a fixed list that satisfies the shortcut, at the same level.
- **The workbench keeps the Reader's rung progression** (Reader §5.5, C6): rung 1 is suggested, then on each further Help press on the same step one rung above the last offered or taken there. A rung taken under fallback has a fixed kind: level 1 `approach_question` (the discriminating question when rivals are open), level 2 `localize`, level 3 the item's next authored hint and then `next_step`, level 4 `continuation`, level 5 `walkthrough`.

**The learner's explicit pick wins.** "Show me the book's way" selects the reference route and "a smaller step toward this goal" selects `next_step` toward the same target, both at the same level; each is logged as `learner_pick` with no propensity, as in the router. Worked help picked outside the workbench fixes the level only, as above.

### 4.6 The writer and its contracts

The writer is one chat call (route `hint_writer`) with structured output. It receives the item (stem, reference solution, rubric, authored hints), the map, the learner's work, earlier hints and feedback, the chosen kind, level and horizon, the route preference, and for `discriminating` the rivals as typed records (statement and status, no prose). It returns the placement, the hint, its target node and route, a `strategy` slug, and the fields its kind's contract needs; for `discriminating`, a few candidate questions, each with the answer each rival predicts, from which the service picks by EIG (§4.2).

**Shared rules**, checked in code before anything is shown (the Reader §5.2 reconciliation contract, generalized to every surface). Rules 6 and 7 here are the Reader's rules 7 and 8; the Reader's rule 6, "it asks before it repairs", is the workbench's presentation of the `discriminating` kind (§4.2). The workbench's step ids, verdicts and step graph make rules 1–3 and 6 exact there (Reader §5.2):
1. **It cites the learner** when there is work: at level 2 and up it quotes the draft or names a step id that exists.
2. **It continues from a real checkpoint:** the placement node is reached by the quoted work, and is no later than the first questionable point.
3. **It says what stands** when there is work ("your first three lines stand").
4. **It keeps the learner's route** unless that route is invalid or the learner asked for another.
5. **It changes strategy when it isn't working:** after a "doesn't connect" reply other than "the notation", or a second hint at the same placement (in the workbench, two hints on the same step), the new hint's kind or strategy slug differs from the earlier ones there. After "the notation" it instead keeps the idea and restates it in the learner's symbols (§4.2).
6. **It is placed:** with a map, it names its route and target node, and the target's distance matches the chosen horizon (or is the last node short of the goal when the route is shorter).
7. **It obeys its kind's contract** (§4.2).

A hint failing a rule is re-asked once with the failure named; then it is shown as a level-3 `next_step` from the last valid checkpoint (in the workbench, `continue_from`) without its unverified claims (Reader §5.2).

**Leak control.** Every hint at level 3 or lower passes `answer_leaks_expected` (`tutor/tutor_qa.py:816`); waypoints and subgoal labels never carry a `leak` node's state. A leaking hint is re-asked once, then withheld with "this hint would give the answer away; take a worked piece instead? (worked help ◌)" (the workbench's wording is the Reader's: "take level 4?").

**What the practice tutor's rule becomes.** The practice-context tutor may not confirm whether partial work is correct (§3.2). A hint that says "your first three lines stand" does exactly that, deliberately: it is help, and it is recorded as help (§5).

### 4.7 Authored hints: seed and fallback, not the source

The `hints` list stays on every item, and the authoring paths keep writing it in v1.
- **Seed.** The writer receives the authored hints; when one fits the placement it may serve it verbatim (`hint_kind = 'authored'`, "from the item").
- **Map seed.** The map builder receives them too; an authored sequence is usually a coarse subgoal list.
- **Fallback.** With `hints.adaptive_enabled = false`, a capped day, an unavailable writer or a time-out, the practice screen shows the authored hints exactly as today. In the workbench, under the chooser's fallback, rung 3 serves them in order while they last, and a capped or unavailable service keeps them and says so (Reader §5.2, §5.5).
- **Deferred (§13):** authoring could emit a map instead of finished hint strings, since the map is the reusable structure and the hint is now written at request time.

### 4.8 What the learner sees

Frictionless by default, details on demand.
- **The hint control becomes clickable.** The key bar's `^h hint` becomes a clickable control with the same label and shortcut (today it is a non-clickable label; §3.2). Nothing else is added to the screen.
- **Pressing it** shows "Writing a hint for your work…" and then the hint. If the item has authored hints and the wait passes `hints.authored_offer_after_seconds` (4, a display cap), a quiet link "use the item's hint instead" appears; taking it cancels the adaptive request so only one hint is recorded.
- **Each hint has a small label:** "AI-written" when the writer wrote it, and its kind in the plain words the Reader uses (UX §5.6), the same on every surface: `approach_question` *a question about your approach* (with no work yet, *your first move?*); `discriminating` *a question that tells apart two explanations* (level 3: *a check that tells them apart*); `localize` *where it stops holding*; `waypoint` *a goal to aim for* with *about two steps ahead* / *at the end of this part* / *the goal itself*; `subgoal_plan` *a plan for the rest*; `next_step` *the next step*; `error_specific` *check this part*; `worked_parallel` *the same move on another example* (*from the book* or *AI-written*); `authored` *from the item*; `continuation` *the next part, written for you*; `worked_chunk` *a worked piece, from the goal back*; `walkthrough` *the rest, worked through*. Levels 4–5 also carry *worked help ◌*.
- **Under each hint, one quiet line:** *this doesn't connect to my work… · show me the book's way*, and under a goal to aim for, first, *a smaller step toward this goal*. "Doesn't connect" opens the Reader's feedback box (UX §5.7): the four shortcuts, each saying what it does (*that's not where I'm stuck*, where the learner may select the part of their draft they mean; *too big a jump*; *I'm using a different approach*; *the notation*), and *say more (optional)*. An empty submit is allowed. The next hint is requested at once, at the same level.
- **Worked help is a labelled pick in the hint panel:** *work a piece of it for me · worked help ◌* and *show me the worked answer · worked help ◌*. The consequence is stated before it is taken; a Hint press alone never serves worked help (§4.2).
- **A discriminating question** shows its label, a one-line answer box and *↵ answer · skip to a hint*; then one line says what it settled (§4.2).
- **Earlier hints stay visible** in order, so a waypoint can be reread while working.
- **The help style** is not on the screen. The hint panel's "⋯" menu and Settings edit the one stored preference that every surface reads (default balanced; in the workbench the header overrides it for one problem, Reader D31). The chooser reads it; it never blocks a request.
- **Cold checks and probes:** this spec changes neither the cold-check banner nor the refusal during a diagnostic block. A take step before help on a cold check is DL2's (Reader D42 asks DL2 for one, with the consequence in its header); it changes when a request is sent, not what the service serves.
- **No unsolicited hints** in v1 (§13).

---

## 5. Evidence semantics: no new rules

| Assist | Recorded as | Existing meaning (§3.2) |
|---|---|---|
| Any hint shown at level 1–3, any kind, adaptive or authored (a discriminating question, a waypoint, a plan and an item's own hint included) | `hints_used` += 1 | Assisted: no certification credit, rejected as a cold retry, half weight in probe episodes, not learner-side clean for placement, excluded from the retention evaluation. Mastery and FSRS unchanged under the default `HintPolicy`; an item's own per-count caps and dampening still apply by count |
| A hint at level 4–5 (`continuation`, `worked_chunk`, `walkthrough`) | `primed = true`, **not** added to `hints_used` (the Reader's D6, adopted on every surface; Reader §20.11 C4) | `repair_activity`: no FSRS feed, no certification (the matrix at `diagnosis/causal_activity_policy.py:17-22`; the class at `:121-142`), like a guided redo |
| Hint text overlapping the key | A `reveal_events` row of the existing kind `tutor_answer` with its overlap amount and a surface-prefixed `basis`: `'workbench_hint:<kind>:L<level>'` in the workbench, `'hint:<kind>:L<level>'` on the practice screen, in guided redo and through the tutor (Reader §5.4, C15) | Production admissibility, reveal-aware cold lanes and auto-prime's 0.35 sum (`attempts/attempts.py:147`) |
| A learner's answer to a `discriminating` question | A `help_assists` row (`assist_kind = 'discriminate_answer'`), typed in the question's own answer box; never part of the submitted answer and, in the workbench, never a step (Reader C5) | No evidence of its own: it reaches the next hint's context, the diagnoser's trace in the workbench (`+workbench-v1`, Reader §5.4) and learner-text gaps (§9); it moves no posterior and writes no probe observation |
| A "doesn't connect" reply | A `learner_card` verdict `different` in `judgment_ledger` on the shared task `hint_fit` (the Reader's first-draft `workbench_hint_fit` is withdrawn, Reader C11); its subject is the answered hint's `help_assists` row, which carries the surface. Its text is learner text for learner-text gaps once that merges (§9) | None |
| In the workbench only: a visible source, and each "Check my work" | `hints_used` += 1 each (Reader §5.4) | Assisted, as above |

**Recorded server-side.** Adaptive hints are written to `help_assists` when shown (§9). At submit, the handler counts shown hints at levels 1–3 since the item's last attempt in this session, exactly as it folds hint-equivalent tutor questions today (`handlers/practice.py:556-559`), and sets `primed` when any shown hint was at level 4 or 5, without counting it. The client's own `hints_used` keeps counting only the authored hints it revealed itself, so nothing is counted twice (gate G-H3). In the workbench the fold is the Reader's (its §5.4): one for a visible source, one per shown check and per shown hint at level 1–3, `primed` for levels 4–5, and no client count at all. The level alone decides the mapping on every surface; the kind and horizon change nothing here. `submit_dont_know` gets the same fold for adaptive hints, so a shown hint is never lost (its existing asymmetry for tutor questions is left for the reviewer to rule on).

**The clamp.** `max_useful_hints`, when set on an item, still clamps the folded total (`handlers/practice.py:560-561`). Any value above zero is assisted, so the clamp changes no classification; the assist rows keep the true count for reports.

**Why levels 4–5 add no count.** Worked help is already marked by `primed`, as a guided redo is (primed, with no hint count), and the classification is the same either way. The count does differ in the learner field's offline arms: a primed attempt reaches them through the IRT priming offset (`field/predictors.py:155`) rather than the `+hints` arm's count cap (`:231`) and hint signal (`field/signals.py:248`). The field's challengers are offline (`FieldConfig.enabled = False`), so nothing served changes; the H2 reviewer confirms this against both certification projections and `resolve_attempt_activity_policy` (§10.1).

**No successor (§10.1).** Every mapping uses an existing field with its existing meaning, as the Reader spec's D6 does, and the two specs now map identically. What changes is how many attempts carry assistance: items that had no hints can now be hinted, and a hint on them makes the attempt assisted. That is the meaning `hints_used` already has.

---

## 6. Measurement: which kinds help this learner

The chapter's closing question is the one to answer: not "is the hint accurate?" but "did it help, and did the learning last?" At n=1 every number here is a **report with its sample size and interval, never a threshold**.

### 6.1 Outcomes per hint

Derived at report time from assist rows, attempts and placements; never stored as evidence. **These are the one definition on every surface:** the Reader's RW2c `help_outcomes` reads them for hints instead of deriving them again, and keeps its own derivation only for help this service does not own (Reader §5.10, C13). In the workbench, progress and time are measured to the next valid step.

| Outcome | Definition | Horizon |
|---|---|---|
| **Unaided next progress** | After the hint, the learner's work reaches the hint's target node (or, for kinds without one, the next node) before any further help: from the next hint's placement, the workbench's next valid step, the grade (a correct answer reaches the goal), or the outcome placement below | Within the attempt |
| **More help needed** | Another hint in the same attempt, and its level | Within the attempt |
| **Time to solution** | Hint shown → submit; in the workbench, hint shown → next valid step. Wall clock; idle excluded where the surface measures it | Within the attempt |
| **"Doesn't connect"** | A reply on this hint, by shortcut (`not_where_stuck`, `too_big`, `learner_route`, `notation`; "too big a jump" is the cognitive-load proxy); after a waypoint, also whether *a smaller step toward this goal* was taken | Within the attempt |
| **Grade** | The attempt's grade | The attempt |
| **Later independent success** | The next attempt on the same item, and the next on the item's LO, with `hints_used = 0` and not primed: pass or fail. **Pending until it happens;** never imputed | Days to weeks |

**Outcome placement.** On the practice screen a wrong answer after a hint does not say whether the learner got past the waypoint. For hinted attempts submitted not fully correct, one small background call (route `hint_outcome`) places the final answer on the map. It is measurement only: it never touches the grade, diagnosis or evidence (`hints.outcome_placement_enabled`).

### 6.2 What each decision logs

The option set offered; the Decider's full probability vectors; the drawn option and its propensity (joint, or conditional on a level the learner took); the seed; the chooser (`decider` | `fallback` | `learner_pick`); the level source (`offered` | `learner_pick`) and, in the workbench, the offered level and the level taken; the policy and question-set versions; the state hash; the placement; the map version; for a `discriminating` question, the rivals with their weights, each candidate's predicted answers and the chosen one's EIG. A hint the learner never saw (cancelled, withheld) is logged with `shown = false` and excluded from outcomes.

### 6.3 Comparing kinds at n=1

`learnloop hints report [--since] [--surface] [--json]` (no model calls, no learner text):
- **Descriptive, per kind and level, per surface:** count, unaided next progress, more help needed, time to solution, "doesn't connect" by shortcut, grade, later independent success with how many are pending; for waypoints, goals reached without more help and *a smaller step toward this goal* taken. Authored hints are a kind, so H0's rows are the baseline. The Reader's workbench report block reads these rows for `surface = 'workbench'` rather than recomputing them (Reader §15).
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

The chooser and writer are sequential because the writer needs the choice; the chooser's time box falls back rather than delaying the hint. **The 8 s writer target is the hint target on every surface, the workbench included**; the Reader's "Check my work" keeps its own 10 s target, and both are reported, not enforced (Reader §5.8, C18). Writing hints speculatively before the learner asks is deferred (§13).

### 7.2 Routes

| Route | Type | Recommended profile | Why |
|---|---|---|---|
| `hint_chooser` | decider (in `DECIDER_TASKS`; never a chat fallback; not overridden by `LEARNLOOP_AI_PROVIDER`) | `openrouter_decider` | Typed probabilities give exact propensities; about $0.0004 a decision |
| `hint_writer` | chat, structured output | a `chatgpt_plan` profile (merged at `57d31c63`; sign-in pending), else a fast OpenRouter chat profile | Interactive. Codex took 29–37 s for blind grading on the stuck-prompt copy (Reader §5.8): too slow for a hint |
| `approach_map` | chat, structured output | any, including `codex_low` | Background |
| `hint_outcome` | chat, structured output | the fast route or `codex_low` | Background, after submit |

Unset chat routes fall back to the active provider and receipts record the resolved model. `learnloop ai latency --provider chatgpt --provider codex_low --runs 3` compares candidates before the switch. These are the only hint routes on every surface: the Reader's first-draft `workbench_hint` and `workbench_level_chooser` are withdrawn, and its `workbench_check` (checks and RW2c's compare line) is not a hint route (Reader §5.8, §11).

### 7.3 Spend

- Every call uses the spend framework (`ai/spend.py`) with receipts; Codex and the ChatGPT plan are `estimated_only`.
- **Money caps, not count caps:** `hints.max_daily_cost_usd` ($1.00 a day on metered routes, writer and chooser) and `hints.maps.max_daily_cost_usd` ($0.50, maps, merges and outcome placement). No per-attempt or per-day hint count. A capped day falls back to authored hints and says so. **These caps cover hint calls on every surface, the workbench included;** the Reader's `workbench.max_calls_per_session` and `workbench.max_daily_cost_usd` bound only its own calls (checks and the compare line) (Reader §5.8, C8).
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

These were proposals for the Reader spec's author. **The Reader spec ruled on them in its §20.11** (all twelve applied, seven with an adaptation; nineteen conflicts resolved as C1–C19) and answered with nine requests in its §18, which §16 applies here. The list is kept as the record; where a ruling adapted an item, the adaptation is noted in brackets, and item 9's section reference is corrected (Reader §18 request 9).

1. **§5.2 ladder: add kinds.** Keep levels 1–5 as the amount of help and the evidence key. Add a column of kinds per level: L1 `approach_question`, `discriminating`; L2 `localize`; L3 `waypoint` (with horizon), `subgoal_plan`, `next_step`, `error_specific`, `discriminating`, `worked_parallel`, `authored`; L4 `worked_chunk` (backward from the goal, leaving the bridge to the learner) and the partial continuation; L5 `walkthrough`. Level 3's description changes from "the principle or a subgoal" to "one of the level-3 kinds". [Adapted: the partial continuation is the kind `continuation`, now in §4.2's table (C10); with rivals open, rung 1 is the discriminating question (C1).]
2. **§5.2 "Authored hints first" → "Authored hints are seeds".** The writer receives them and may serve one verbatim, labelled; they are the fallback when capped or unavailable. Same behaviour, clearer role.
3. **§5.2 reconciliation contract: add rule 6, "It is placed".** When an approach map exists, a hint names its route and target node, and the target's distance matches the chosen horizon. Rule 5's "different strategy" is satisfied by a different kind *or* a different `strategy` slug. Add the kind contracts of §4.2 (a waypoint names a target state and no transformation; a discriminating hint names two hypotheses with differing predicted results; a worked chunk leaves a gap). [Adapted: they are the Reader's rules 7 and 8, since its rule 6 is "asks before it repairs"; placement starts from the node `continue_from` reaches (C3).]
4. **§5.2 feedback shortcuts get defined effects.** "Different approach" switches route on the map (or kind at the same level); "Too big a jump" shortens the horizon or lowers the grain; "I don't understand the notation" is passed to the writer as a notation note. [Adapted, and reversed here: the Reader's four shortcuts and meanings stand; "I'm using a different approach" keeps the learner's route (stored `learner_route`), "that's not where I'm stuck" moves the hint, every reply keeps the level, and "the notation" is exempt from rule 5 (C2, C16, C17). §4.2 now uses those meanings.]
5. **§5.5 chooser: one Decider request, two questions, sampled.** `kind_level` (a `choice` over the allowed (kind, level) pairs) and `horizon` (a `score`), sampled from the Decider's own probabilities with the drawn probability logged as the propensity. Replace "There is no randomization of help quality (§17)" with the §4.5 argument: sampling within the judge's own uncertainty is not a hint-quality experiment, and it is what makes kinds evaluable. Keep §17's row against deliberately worse help. [Adapted: a rung the learner takes draws the kind conditional on the level; the workbench keeps its rung progression as the fallback (C6). Both are in §4.5.]
6. **§5.5 state: add** the approach-map placement from the last check, the learner's route preference, per-kind history on these facets (continued unaided, "doesn't connect"), time since the last hint and whether the work changed since it, and a closed probe episode's recommended tutor move.
7. **§5.7 data: share one assists table.** Name it `help_assists`, with a `surface` column (`practice` | `workbench` | `guided_redo` | `tutor`) and nullable workbench fields, created by whichever of RW2b and H0 merges first. Add `kind`, `horizon`, `route_id`, `from_node_id`, `target_node_id`, `map_id`, `options_json`, `probabilities_json`, `propensity`, `seed`, `policy_version`, `shown`, `counted_by`. RW2b's check and bridge rows stay in the same table with their kinds. [Adapted: `kind` is `hint_kind`, beside the workbench's `assist_kind` (C9); §9 now lists the merged table.]
8. **§5.8 routes: share them.** `workbench_hint` becomes `hint_writer` and `workbench_level_chooser` becomes `hint_chooser`; add `approach_map`. One writer, one chooser, one set of receipts for every surface.
9. **§5.2 "Check my work" reads the map.** Step verdicts can name the map node a step reaches, which gives placement for free. (The first draft of this item cited §5.3, which is the Reader's symbolic checks.)
10. **§17: the "Full solution graphs" row** is partly superseded: approach maps (small graphs with alternative routes) are built by this spec's H1 and RW2b reads them when present. Keep the deferral for full step-level graphs with every branch.
11. **§15 workbench block: add per-kind rows** with propensities (§6.3) beside "help level taken vs offered". [Adapted: read from this service's report for `surface = 'workbench'`, not recomputed.]
12. **§16 D8:** the first offer becomes a (level, kind, horizon) choice, sampled from the Decider's probabilities, default style "balanced"; fallback "authored hints, then level 1 and up". [Adapted: the fallback is the Reader's rung progression, with authored hints serving rung 3 (C6).]

---

## 9. Data

Migrations are numbered when they land (`ls migrations/`; head 180 on this base). Follow `CLAUDE.md`'s head-fixture procedure.

| Table | Role (`db/table_roles.py`) | Phase | Contents |
|---|---|---|---|
| `help_assists` (shared with the Reader workbench; its first draft's `workbench_assists`) | RAW_LEDGER | H0 or RW2b, whichever lands first (Reader §5.7, §11) | **This spec's columns:** `id`, `surface` (`practice` \| `workbench` \| `guided_redo` \| `tutor`), `practice_item_id`, `practice_item_hash`, `practice_session_id`, `attempt_id` (filled at submit), `hint_kind?` (the first draft's `kind`, renamed so it cannot be confused with the assist kind; every kind in §4.2's table: `approach_question` \| `discriminating` \| `localize` \| `waypoint` \| `subgoal_plan` \| `next_step` \| `error_specific` \| `worked_parallel` \| `authored` \| `continuation` \| `worked_chunk` \| `walkthrough`), `level?` (1–5), `horizon?`, `route_id?`, `from_node_id?`, `target_node_id?`, `map_id?`, `strategy?`, `body_md?` (null for authored reveals: the item has the text), `authored_index?`, `work_hash`, `work_chars`, `placement_json?`, `chooser` (`decider` \| `fallback` \| `learner_pick` \| `none`), `options_json?`, `probabilities_json?`, `propensity?`, `seed?`, `policy_version?`, `request?` (`more` \| `feedback` \| `book_way` \| `smaller_step`), `feedback_text?`, `feedback_shortcut?` (`not_where_stuck` \| `too_big` \| `learner_route` \| `notation`; the first draft's `different_approach` is withdrawn, because it read the opposite way, §4.2), `contract_failures_json?`, `leak_flags_json?`, `shown`, `counted_by` (`client` \| `server`), `model?`, `prompt_version?`, `input_hash?`, `latency_ms?`, `requested_at`, `shown_at?`. **The Reader's columns** (its §5.7): `workbench_session_id?`; `assist_kind` (`hint` \| `check` \| `discriminate_answer` \| `bridge` \| `example` \| `compare_methods` \| `feedback`); `offered_level?`; `level_source?` (`offered` \| `learner_pick`); `step_snapshot_json?`; `step_verdicts_json?`; `first_questionable_step_id?`; `error_kind_guess?`; `about_step_id?`; `continue_from_step_id?`; `rivals_json?`; `predicted_answers_json?` and `eig_nats?` (a discriminating question); `feedback_step_id?`; `cited_span_ids_json?`; `retrieval_manifest_json?`; `alternatives_json?`. Outside the workbench this spec writes `assist_kind` `hint` and, for an answer to a discriminating question, `discriminate_answer`; it fills `level_source` when a level was taken, and `rivals_json`, `predicted_answers_json` and `eig_nats` on discriminating rows; the step columns stay null. A "doesn't connect" reply outside the workbench is carried on the next hint's row (`request = 'feedback'`); in the workbench it is also its own `feedback` row. **One migration: the table is created with every column and every CHECK value either spec writes**, so neither spec's later phase rebuilds it |
| `approach_maps` | WORKFLOW (paid output, never rebuilt) | H1 | `id`, `practice_item_id`, `practice_item_hash`, `family_id?`, `version`, `map_json`, `seeds_json` (which trace contract, skeleton, spans, attempts and authored hints it was built from), `validation_json`, `verified_goal`, `model`, `prompt_version`, `input_hash`, `created_at`, `supersedes_id?` |

- **No DERIVED table, so no replayer.** Replay never reads either table: evidence lives in `practice_attempts` (`hints_used`, `primed`) and `reveal_events`.
- **No table rebuild of this spec's own:** no new `interaction_events` kind and no new reveal kind (`tutor_answer` with a `hint:` or `workbench_hint:` basis). The learner-text widening below is the Reader's one rebuild, which this spec joins rather than adding a second.
- **`judgment_ledger` tasks, shared with the workbench** (Reader §11): `hint_choice` (judge `decider`), `hint_fit` (judge `learner_card`, verdict `different`: the "doesn't connect" replies; the Reader's first-draft `workbench_hint_fit` is withdrawn), `approach_map_valid` (judge `verifier`, the code validation). A verdict's subject is the `help_assists` row, which carries the surface. The ledger's judge CHECK already admits `decider`, `verifier` and `learner_card` (`migrations/175_decider_judgments_and_receipt_labels.sql:36`).
- **Learner-text gaps** (once `learner/text-gaps` merges; Reader §3.4 item 13). Text the learner writes back to a hint **outside the workbench** — a "doesn't connect" reply's text and an answer to a discriminating question — is source kind `hint_feedback`, whose adapter reads it from `help_assists` with its item, placement and role (`hint_feedback` \| `discriminate_answer`); inside the workbench the same texts are the Reader's `workbench_text` (roles `hint_feedback`, `discriminate_answer`, `stuck`). `hint_feedback` joins `workbench_text` and `reader_formative` in **the one migration that widens the `source_kind` CHECK** on `learner_text_gaps` and `learner_text_gap_jobs` (temp-then-rename with `PRAGMA foreign_keys = OFF`, a `foreign_key_check` before commit, a durability-lane test), so the tables are rebuilt once. Whichever of RW1b, RW2b and H2 first adds an adapter carries it with all three kinds; the others add only their adapters. Texts are queued when written, so a gap named mid-attempt joins the next hint's rivals. Until that pipeline merges, the text stays on the assist row.
- **Model-call receipts** carry `judge` (`decider` or `llm`), `question_set_version` and `state_hash` (migration 175), as the router's do.
- **H0's authored-reveal rows** are written by a fire-and-forget RPC (`practice.record_hint_reveal`) with `assist_kind = 'hint'`, `hint_kind = 'authored'`, `chooser = 'none'` and `counted_by = 'client'`. They are telemetry only; submit keeps using the client's count for authored hints.

**Config** (`[hints]`, modelled defaults; each phase recomputes the latest `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry with a "no scoring, scheduling, projection or serving change" note, as the Reader spec's phases do): `telemetry_enabled`, `adaptive_enabled`, `chooser_enabled` (the one chooser switch on every surface, the workbench included), `choice_policy` (`sample` | `argmax`), `chooser_timeout_seconds` (3), `outcome_placement_enabled`, `guided_redo_enabled`, `tutor_enabled`, `help_style` (`let_me_struggle` | `balanced` | `guide_me`, default `balanced`: the one stored preference every surface reads, written by Settings and the hint panel's "⋯" menu; the workbench's per-problem override is `workbench_sessions.help_style`), `authored_offer_after_seconds` (4), `max_daily_cost_usd` (1.00), `price_per_million`; `[hints.maps]`: `enabled`, `build_on_serve`, `max_daily_cost_usd` (0.50). The Reader's `[workbench]` keys govern only its own calls and switches (Reader §11). Routes: `ai.routing.hint_chooser`, `hint_writer`, `approach_map`, `hint_outcome`.

---

## 10. Phases, successors and kill switches

Every phase goes through `implementation_goal.md` §2's loop (implement, adversarial review, fix, gate, integrate) and merges alone. Sizes use the Reader spec's key: **S** about a day, **M** two to four days, **L** one to two weeks.

| Phase | Builds | Needs | Size | Data it starts | Kill switch (restores) |
|---|---|---|---|---|---|
| **H0. Hint telemetry** | `help_assists` (migration, with both specs' columns and CHECK values, §9, unless RW2b created it first); `practice.record_hint_reveal` for authored reveals with time and draft hash; the report's descriptive rows with authored hints as the baseline kind. No model call; no visible change | `main` | **S** | The baseline: how today's hints are used and what follows | `hints.telemetry_enabled` (no rows) |
| **H1. Approach maps** | `approach_maps` (migration); builder and validator (route `approach_map`); build on serve; inline build; lazy learner-route merge; family templates; `hints maps build --dry-run` | H0 | **M** | Maps for served items; validation failures by reason; route counts by origin | `hints.maps.enabled` (no builds; nothing reads maps) |
| **H2. Adaptive hints on the practice screen** | `practice.request_hint`; the service (state, chooser with conditional draws for a taken level, writer, contracts, leak control, discriminating questions ranked by EIG); server-side fold at submit (levels 1–3 counted, levels 4–5 `primed`); `tutor_answer` reveal rows with the `hint:` basis; labels; "Doesn't connect" with the four shortcuts; *show me the book's way*, *a smaller step toward this goal* and the worked-help picks; the style menu on the shared preference; the clickable hint control; authored fallback; outcome placement; per-kind report rows; the `hint_feedback` learner-text adapter (and the one widening migration if no Reader phase has carried it) once learner-text gaps has merged | H1 (works without maps, with fewer kinds); the Decider (merged); a fast chat profile signed in | **L** | Decisions with propensities and outcomes | `hints.adaptive_enabled` (byte-identical practice screen); `hints.chooser_enabled`; `hints.choice_policy`; `hints.outcome_placement_enabled` |
| **H3. The workbench** | Inside RW2b (Reader §5.2–5.5 as ruled in its §20.11): Help calls the service; ladder kinds; the Reader's fallback progression; "Check my work" reads the map; shared table, routes, ledger task and switches | RW2b; H2 (or the core RW2b builds, below) | **S** on top of RW2b | Kinds with step-level outcomes | RW2b's switches, plus the shared `hints.chooser_enabled`, `hints.choice_policy` and `hints.maps.enabled` |
| **H4. Guided redo and the tutor** | Hints during the redo from the prefix and diagnosis; the practice tutor reads the draft and placement; strategy questions answered as a chosen kind | H2 | **S–M** | Kinds after a wrong answer | `hints.guided_redo_enabled`, `hints.tutor_enabled` |
| **H5. Off-policy report** | Self-normalized IPS and doubly robust estimates per kind, with effective sample sizes and bootstrap intervals; the expertise-reversal split; abuse and avoidance counts | H2 plus about a month of rows | **S** | — | Report only |

**Order.** H0 now: it is small and starts the baseline clock. H1 next. H2 when a fast chat profile is signed in; it is the phase the owner sees. H3 rides on RW2b whenever that lands. **If RW2b is ready before H2, it builds the service's core once, in `learnloop/hints/`, to this spec's design, signatures and tests, and holds gates G-H5 to G-H8** (Reader G64, C14); it also creates `help_assists` if H0 has not. H2 then adds the practice screen to that core rather than building a second one. H4 after H2's checkpoint. H5 after a month of H2 data.

**Owner checkpoint after H2:** two weeks of ordinary practice, then the report: kinds served by placement intent, unaided next progress, "doesn't connect" by kind and shortcut, latency p50/p95 by route, cost.

### 10.1 Successor ruling

**No successor in v1.** Every hint maps onto `hints_used` (levels 1–3), `primed` (levels 4–5) and `reveal_events` with their existing meaning (§5), exactly as the Reader spec's D6 maps them; the new tables are RAW_LEDGER and WORKFLOW, and replay reads neither. Precedents: the Reader spec's D6, the stuck-reading context extension. The H2 reviewer confirms the §5 table against `resolve_attempt_activity_policy` and both certification projections, including that a primed attempt with no hint count is classified as a counted one is (§5, "Why levels 4–5 add no count"); if any mapping needs a new rule, that part stops and takes the next free `mvp-0.N` tag at merge.

**Named successors for later** (each the next free `mvp-0.N` at its merge):
1. **Kind-aware assistance weights.** Weight help by level or kind instead of counting hints, in `HintPolicy`'s per-count maps and in the field's `lo_general+hints` arm (`1 − 0.2k`) and S5 signals. Trigger in §13.
2. **Unsolicited hints.** A proactive offer changes how many attempts become assisted, and so what can certify. Deferred (§13).
3. **Authored reveals in the reveal ledger.** Today a "near-give-away" authored hint writes no reveal row (§3.2), so it can never contribute to auto-prime. Recording it would change evidence; not proposed for v1, listed so the inconsistency is on record.

---

## 11. Gates and tests

| # | Gate |
|---|---|
| G-H1 | **Kill-switch parity.** With `hints.adaptive_enabled = false`, the practice RPCs and screen are byte-identical to `main` on fixture copies; with `hints.maps.enabled = false` no map is built or read; with `hints.telemetry_enabled = false` no `help_assists` row is written |
| G-H2 | **Evidence mapping.** For each kind and level, shown on the practice screen, in guided redo and through the tutor, the submitted attempt's `hints_used`, `primed` and reveal rows match §5: levels 1–3 add one each, levels 4–5 set `primed` and add nothing, and a key overlap writes `tutor_answer` with `basis = 'hint:<kind>:L<level>'` (`workbench_hint:` in the workbench, Reader G5). `resolve_attempt_activity_policy` gives the stated eligibility. A discriminating answer changes none of them. A rebuild reproduces evidence identically |
| G-H3 | **No double count, no lost hint.** Authored reveals counted by the client and adaptive hints counted by the server never overlap; a cancelled or withheld hint counts nothing; an authored fallback cancels the pending adaptive request; `submit_dont_know` and `submit_attempt` both include shown adaptive hints; the workbench sends no client count (Reader G64) |
| G-H4 | **The grader stays blind.** The rendered blind-grading prompt for a hinted attempt contains no hint, kind, map, placement or learner state |
| G-H5 | **Leak control.** A level-1–3 hint containing the expected answer (including short numeric answers) is never shown; no waypoint or label carries a `leak` node's state |
| G-H6 | **Contracts.** A fake writer that cites no learner work, continues past the first questionable point, repeats a kind and strategy after a "doesn't connect" reply other than "the notation", misses the chosen horizon, or breaks a kind contract (including a `continuation` that reaches the goal) is caught, re-asked once, then downgraded as §4.6 says |
| G-H7 | **Propensities.** The logged propensity equals the probability the option was drawn with: the joint probability for a chooser-served option, the probability conditional on the level for a level the learner took (1 where the level has one option); seeds reproduce draws; `argmax` logs 1; fallback logs 1; `book_way` and `smaller_step` log `learner_pick` with none; options whose preconditions fail are never offered; on surfaces without a ladder a Hint press never serves level 4 or 5 |
| G-H8 | **Chooser fallback.** Time-out, unavailability, a spent-out Decider or `hints.chooser_enabled = false` produce §4.5's fallback for the surface (authored hints then `next_step`; in the workbench the Reader's rung progression, Reader G12, G62), flagged on the row; the Decider route never falls back to chat |
| G-H9 | **Maps.** The validator rejects cycles, routes that do not reach the goal, foreign facets and leaking labels; a failing map is never stored; a revised item does not reuse its old map; learner routes come only from correct or PF-c-valid attempts |
| G-H10 | **Replay.** Rebuild and replay make zero model and embedding calls with `help_assists` and `approach_maps` populated |
| G-H11 | **Spend.** Daily money caps hold and fall back to authored hints; Codex and plan receipts are `estimated_only`; `hints maps build --dry-run` writes nothing |
| G-H12 | **Labels.** Every adaptive hint carries "AI-written" and its kind label in the Reader's plain words (§4.8; UX §5.6); authored hints carry "from the item"; worked help says *worked help ◌* before it is taken. A wording lint rejects "you don't understand", "you struggle", "weak" |
| G-H13 | **Boundaries.** An import-linter contract: `learnloop.hints` imports no evidence writer; new RPCs are pinned desktop-only in `tests/test_mobile_allowlist.py`; new tables are classified in `db/table_roles.py` |
| G-H14 | **Cold and probe parity.** On a cold check the banner and rejection are unchanged by this spec; during a diagnostic block no hint request reaches a model |
| G-H15 | **Replies and picks** (Reader G33, G63, the same on every surface). A "doesn't connect" reply reaches the next request at once, appends a `learner_card` verdict `different` on `hint_fit`, and the next hint keeps the answered hint's level. `not_where_stuck` moves the placement and never repeats the earlier localization; `too_big` gives a shorter horizon toward the same target or a finer kind; `learner_route` stays on the learner's route (an existing route or `new_route`), names the work it builds on and never targets the reference route; `notation` restates the same idea quoting the learner's symbols. Only `book_way` places a hint on the reference route while the learner's route is valid; after a waypoint, `smaller_step` serves `next_step` toward the same target at the same level, and `next_step` toward it is among "More"'s options. No hint is shown unless the learner asked or replied |
| G-H16 | **Discriminating questions** (Reader G37, on every surface). Offered only with two or more open rivals; candidates are ranked by `instrument_expected_information_gain` (asserted by monkeypatch); a candidate whose rivals all predict the same answer is never shown; with no positive EIG the hint is served as §4.2 says and says why. The question passes leak control and states neither rival. Its answer is a `discriminate_answer` row, absent from the submitted answer and from the blind-grading prompt, and writes no posterior or probe observation. After one is answered at a placement, `discriminating` leaves the options there |
| G-H17 | **One schema, one preference.** `help_assists` is created once with every column and CHECK value both specs write (including `hint_kind`'s twelve kinds, `assist_kind`'s seven values, and `feedback_shortcut`'s four, with no `different_approach`), whichever of H0 and RW2b creates it; `hint_feedback`, `workbench_text` and `reader_formative` arrive in one `source_kind` widening migration (FK check, durability lane); the chooser reads `hints.help_style` on every surface and the workbench's per-session override where set |

**Tests** (fakes only: `tests/structured_ai.py`, `tests/decider_fakes.py`, `tests/openai_fakes.py`; vault builders from `tests/helpers.py`):
- **H0:** `test_hint_telemetry.py` (rows, timing, `counted_by`, kill switch, no evidence change); `test_help_assists_schema.py` (G-H17: every column and CHECK value of both specs).
- **H1:** `test_approach_maps.py` (seeds from trace contracts, skeletons and authored hints; validator; build on serve; inline build; learner-route merge; revision keys; dry-run); `test_approach_map_replay.py`.
- **H2:** `test_hint_service.py` (state assembly, options and preconditions, sampling and propensities, conditional draws for a taken level, fallback); `test_hint_contracts.py` (G-H5, G-H6); `test_hint_replies.py` (G-H15); `test_hint_discriminating.py` (G-H16); `test_hint_evidence.py` (G-H2, G-H3); `test_hint_blind.py` (G-H4); `test_hint_kill_switch.py`; `test_hint_report.py`; the `hint_feedback` adapter's test and the widening migration's durability-lane test when learner-text gaps has merged; vitest for the hint panel, labels, feedback box, the picks, the discriminating answer box, cancel and the clickable control.
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
| D3 | Who chooses | The Decider over typed state plus the help style, time-boxed; fallback authored hints, then next step; in the workbench, the Reader's rung progression (Reader D8). One switch, `hints.chooser_enabled`, on every surface |
| D4 | How the served kind is picked | **Sampled from the Decider's probabilities**, propensity logged, no exploration floor. Alternative: argmax (no off-policy evaluation). If support turns out too thin to compare kinds after a month, decide on a floor then (the router uses 0.02) |
| D5 | Help style control | One stored preference (`hints.help_style`) read on every surface: three settings, edited from the hint panel's "⋯" menu and Settings; default balanced; never on the practice screen itself. The workbench header overrides it for one problem (Reader D31) |
| D6 | Approach maps | Built in the background when an item is shown; inline on the first hint if missing; learner routes merged lazily; Codex allowed for building |
| D7 | Authored hints | Kept as seed and fallback; authoring unchanged in v1 |
| D8 | Evidence | The Reader's D6 on every surface: each shown hint at levels 1–3 adds to `hints_used` (counted server-side); levels 4–5 set `primed` and add no count; key overlap writes `tutor_answer` reveals with a surface-prefixed basis (`hint:` or `workbench_hint:`); no successor |
| D9 | Writer route | A `chatgpt_plan` profile once signed in; until then a fast OpenRouter chat profile; never Codex for interactive hints |
| D10 | Spend | $1.00 a day for writer and chooser, $0.50 for maps and outcome placement (metered only); no count caps |
| D11 | Outcome placement for hinted wrong answers | On |
| D12 | Unsolicited hints | None in v1 (§13) |
| D13 | The hint control | The key bar's `^h hint` becomes clickable; nothing else is added to the screen. A hint's own quiet lines (*doesn't connect*, *the book's way*, *a smaller step*, the worked-help picks) appear only in the hint panel, with a hint |
| D14 | The practice tutor | Gains the learner's draft and the map placement as context (H4) |
| D15 | "Doesn't connect" | The Reader's four shortcuts with its meanings on every surface (§4.2): "that's not where I'm stuck" moves the hint, "too big a jump" a smaller step, "I'm using a different approach" keeps the learner's route (`learner_route`), "the notation" restates in their symbols and is exempt from rule 5; every reply keeps the level |
| D16 | Discriminating questions | Offered only with two or more open rivals; candidates ranked by the existing EIG on every surface; zero-EIG questions never shown; the answer is an assist row, never part of the submitted answer |
| D17 | Worked help outside the workbench | The learner's labelled pick (*work a piece of it for me*, *show me the worked answer*, each *worked help ◌*); a Hint press serves levels 1–3 only. Alternative: let the chooser serve levels 4–5 on a press, which makes an attempt primed without the learner choosing it |

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

- **Reader workbench.** §8.2's twelve proposals, ruled on in Reader §20.11; its §18 requests, applied in §16. RW2b's hint writer, chooser, assists table, ledger task and chooser switch are this spec's shared ones; whichever of RW2b and H0 (for the table) or H2 (for the service's core) lands first creates them (Reader G64).
- **Learner field.** H0 records hint timing, which `field/probability_states.py:99-101` lists as not recorded. No new signal source in v1; kind-aware weights are a successor (§10.1).
- **Router.** The hint chooser borrows the router's propensity convention and receipt fields; hints stay out of router decisions.
- **Blind grading and diagnosis.** The grader is unchanged, and a discriminating answer never enters the submitted answer; the diagnoser's `assisted` flag is unchanged. In the workbench the diagnoser's `+workbench-v1` trace carries each hint's kind and level and any discriminating answer (Reader §5.4).
- **PF.** Published variants keep `hints = []`; adaptive hints cover them. PF skeletons gain a consumer (map seeds).
- **Exercise import and authoring.** Unchanged in v1; `MAX_HINTS = 4` stays as authoring's own limit, not a limit on hints served.
- **Learner-text gaps.** Text written back to a hint outside the workbench ("doesn't connect" text and discriminating answers) becomes a learner-text source (`hint_feedback`) once that pipeline merges, beside the Reader's `workbench_text` (the first draft of this note called it `workbench_stuck`) and `reader_formative`, in the one `source_kind` widening migration (§9).
- **Count caps elsewhere, for the owner's look** (as Reader §20.7 did): the practice tutor's `max_questions_practice` (3, `config/schema.py:540`) is a count cap on help of the same kind this spec leaves uncapped.
- **H0 (hint telemetry, `hints/h0`, 2026-10-17; `docs/reviews/adaptive-hints-H0.md`).** Migration 210 creates `help_assists` once, with every column of §9 and of Reader §5.7 and every CHECK value both specs write (G-H17), plus three nullable columns §6.2 and Reader §5.5 log on the row but neither §9 list names (`drawn_option_json`, `question_set_version`, `state_hash`) and two that bind a row to its attempt and time it (`submission_id`, the client's stable submission key the attach matches on alone; `submitted_at`, when the submission reached the sidecar before grading, the end of §6.1's "hint shown → submit"; Codex review F1, F2, `docs/reviews/hints-h0-codex-review.md`); a later binding (the workbench's practice session at Submit, the submission, the submit time, the attempt) goes from NULL to a value once and is then fixed (F3); `practice_item_id` / `practice_item_hash` / `work_hash` / `work_chars` are nullable (an unbound workbench problem has no item) and `counted_by` is nullable (NULL: counted by neither, e.g. a discriminating answer). The authored-reveal rows, `practice.record_hint_reveal`, the attach at submit, `hints.telemetry_enabled` and `learnloop hints report` (§6.3's descriptive rows, authored hints the baseline) are built; `learnloop.hints` holds only `telemetry` and `report`, under the import-linter contract `hints-never-write-evidence` (G-H13).
- **Known deviation from G-H17's "one widening migration" (recorded at H0, not fixed).** Migration 208 (Reader RW1b) widened `learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` with `workbench_text` and `reader_formative` but not `hint_feedback`, so the three kinds cannot arrive in one widening. H2, when it adds the `hint_feedback` adapter, carries a second widening of both tables (temp-then-rename with `PRAGMA foreign_keys = OFF`, a `foreign_key_check` before commit, a durability-lane test), adding `hint_feedback` and nothing else.

---

## 16. Alignment with the Reader workbench spec, 2026-10-13

**What was done.** The Reader workbench spec (`spec_reader_workbench_v1.md`, merged on `main` at `c46b403c`) folded this spec's twelve §8.2 proposals into its help ladder (its §20.11: all twelve applied, seven with an adaptation), resolved nineteen conflicts (C1–C19), and in its §18 made nine requests of this spec. This section applies them. The rule for conflicts is the Reader's, accepted here: **this spec wins on hint generation** (kinds, the writer and its contracts, approach maps, the chooser and how it picks, hint spend); **the Reader spec wins on the Reader's presentation and on evidence mapping**, which this spec now applies on every surface. On the practice screen, in guided redo and through the tutor this spec still owns the presentation, and it adopts the Reader's meanings and words there too, so the learner meets one hint vocabulary everywhere. **Nothing is rejected.** The code citations this alignment adds (`field/predictors.py:155`, `:231`; `field/signals.py:248`) were checked on `main` at `c46b403c`.

### 16.1 The requests

Requests 1–9 are the Reader's §18 list; 10–12 are §20.11 resolutions that also ask something of this spec.

| # | Request (Reader source) | Ruling | Where here | Adaptation, and why |
|---|---|---|---|---|
| 1 | Name the assists column `hint_kind` (this spec's `kind`), keep the workbench's separate `assist_kind`, and add the workbench's columns with every value, so the shared table has one migration (§18 req. 1; C9) | **Applied** | §9 `help_assists`; §10 H0; G-H17; `test_help_assists_schema.py` | No adaptation. The row now lists both specs' columns and every CHECK value. Outside the workbench this spec writes `assist_kind` `hint`, and `discriminate_answer` for an answer to a discriminating question (request 5) |
| 2 | Add `continuation`, the forward partial continuation, at level 4 (§18 req. 2; C10) | **Applied** | §4.2 table; §4.5 fallback; §4.8 label; §5; §9 CHECK; G-H6 | Its contract column is written here, because the Reader's rule 8 cites this table: it starts at the placement node (the node `continue_from` reaches), stays on the learner's route and, with a map, ends short of the goal |
| 3 | Give "doesn't connect" the Reader's four shortcut meanings: "I'm using a different approach" keeps the learner's route (stored `learner_route`), "that's not where I'm stuck" moves the hint; stored values as Reader §5.7 (§18 req. 3; C2, C16) | **Applied, adapted** | §4.1; §4.2; §4.6 rule 5; §4.8; §9 `feedback_shortcut`, `request`; G-H15; D15 | This reverses this spec's first draft, where "different approach" meant switching route; the only route switch is now `book_way`, a named request. Every reply keeps the level of the hint it answers (C16). **Adapted for surfaces without steps:** "that's not where I'm stuck" takes a selection of the draft, or the learner's text, instead of a step picker |
| 4 | Map levels 4–5 to `primed` without adding to `hints_used`, as D6 does, so the server's fold has one rule on every surface (§18 req. 4; C4) | **Applied** | §5 table and "Why levels 4–5 add no count"; §10.1; G-H2; D8 | No adaptation. Classification is unchanged. The learner field's offline arms now see worked help through the priming offset rather than the `+hints` count cap, as they already see a guided redo; the field is offline, so nothing served changes. The H2 reviewer confirms |
| 5 | Use the Reader's EIG ranking of candidate questions as the `discriminating` kind's selection step on every surface; exempt "the notation" from rule 5 (§18 req. 5; C1, C17) | **Applied, adapted** | §4.2 "Discriminating questions"; §4.5 options; §4.6 writer output and rule 5; §5; §6.2; G-H6; G-H16; D16 | (a) The rivals each surface supplies are named; the workbench adds its check's guesses. (b) The Reader defines the zero-EIG fallback for rung 1 only; at level 3 this spec serves `next_step`, saying why. (c) **The answer goes in the question's own box and is an assist row on every surface.** This spec's first draft let it become part of the submitted answer; the Reader rules that out in the workbench (C5), and doing the same everywhere keeps the blind grader's input to the learner's own answer and lets each answer be compared with the rivals' predictions |
| 6 | Write the reveal `basis` with a surface prefix: `workbench_hint:<kind>:L<n>` in the workbench, `hint:<kind>:L<level>` elsewhere (§18 req. 6; C15) | **Applied** | §5; §9; G-H2; D8 | — |
| 7 | If the practice screen needs a learner-text source kind for "doesn't connect" text (`hint_feedback`), add it to the one `source_kind` widening migration with `workbench_text` and `reader_formative`; this spec's §15 named `workbench_stuck`, which is `workbench_text` (§18 req. 7; C12) | **Applied, adapted** | §9 "Learner-text gaps"; §10 H2; §15; G-H17 | `hint_feedback` also carries discriminating answers outside the workbench (role `discriminate_answer`, mirroring `workbench_text`'s roles), because request 5 makes them learner text. H2 joins RW1b and RW2b as a phase that may carry the migration, so whichever adds an adapter first builds it once with all three kinds. §15's note is corrected |
| 8 | Read the help style as one stored preference on every surface, with the workbench header's per-session override on `workbench_sessions.help_style` (§18 req. 8; D31; C7) | **Applied** | §4.5 state; §4.8; §9 config; D5; G-H17 | No adaptation. The preference is named `hints.help_style`, which the Reader left unnamed; the hint panel's "⋯" menu and Settings edit it |
| 9 | Correct §8.2 item 9: "Check my work" is Reader §5.2, not §5.3 (§18 req. 9) | **Applied** | §8.2 item 9 | — |
| 10 | One feedback ledger task: the shared `hint_fit`, not `workbench_hint_fit` (§20.11 C11) | **Applied** | §4.2; §5; §9 ledger tasks; G-H15 | No adaptation. This spec already used `hint_fit`. Now stated: verdict `different`, its subject the answered hint's `help_assists` row, which carries the surface |
| 11 | One chooser switch: `hints.chooser_enabled`, replacing `workbench.level_chooser_enabled` (§20.11 C19) | **Applied** | §4.5 fallback; §9 config; §10 H3; G-H8; D3 | No adaptation. Already this spec's key. Now stated: it governs every surface, and with it off the workbench shows the Reader's rung progression |
| 12 | Hints take this spec's latency target (writer p50 ≤ 8 s, reported); checks keep 10 s (§20.11 C18) | **Applied** | §7.1 | No adaptation. Already this spec's target; now stated for every surface, the workbench included |

### 16.2 The other conflicts, as this spec now reads

The rest of C1–C19 are covered above (C2, C16: request 3; C4: 4; C7: 8; C9: 1; C10: 2; C11: 10; C12: 7; C15: 6; C17: 5; C18: 12; C19: 11) or here:

| Reader | Topic | This spec now says |
|---|---|---|
| C1 | Asking before repairing | `discriminating` stays a kind the sampled chooser draws (§4.5); in the workbench, with two or more rivals open, level 1's only option is the discriminating question, so it is always one key away on rung 1. The Reader's rule 6, "asks before it repairs", is the workbench's presentation of this kind (§4.6) |
| C3 | Where a hint starts | In the workbench the placement starts from the node the `continue_from` step reaches, and the horizon is measured from there; the hint is shown under its `about_step` (§4.4) |
| C5 | A discriminating answer | An assist row, never a step and never part of the submitted answer, now on every surface (§4.2, §5) |
| C6 | The fallback | Per surface: authored hints then `next_step` on the practice screen, in guided redo and through the tutor; the Reader's rung progression in the workbench, with authored hints on rung 3 (§4.5, §4.7) |
| C8 | Hint spend | Hint calls on every surface fall under this spec's money caps, with no count; the workbench's caps bound only its own calls (§7.3) |
| C13 | Hint outcomes derived twice | Defined once, in §6.1; RW2c's `help_outcomes` reads them, and the workbench's report block reads §6.3's rows for `surface = 'workbench'` |
| C14 | Build order | If RW2b is ready before H2, it builds the service's core once, in `learnloop/hints/`, to this spec's design, holding G-H5 to G-H8 (§10 "Order") |

### 16.3 Further alignment where the specs overlap

Not requested, but needed for the two specs to agree:
1. **A level the learner took** (Reader §5.5, G63): the kind is drawn conditional on that level and the conditional probability is logged; `level_source` records it (§4.5, §6.2, G-H7).
2. **The learner's picks** "a smaller step toward this goal" (`smaller_step`) and "show me the book's way" (`book_way`) exist on every surface, logged as `learner_pick` with no propensity (§4.1, §4.2, §4.8, §9; Reader §5.2, G63).
3. **Worked help is the learner's to take on every surface** (Reader §5.2: each rung states its consequence before it is taken; UX principle U11; C16). On surfaces without a ladder, a Hint press now serves levels 1–3 only, and levels 4–5 are labelled picks (§4.2, §4.5, §4.8, G-H7). The first draft let the chooser serve a worked chunk or walkthrough on a press, which would make an attempt primed without the learner choosing it. Recorded as owner decision D17, with that alternative.
4. **One set of plain-word kind labels**, the Reader's (UX §5.6), with *worked help ◌* in place of this spec's "heavy help" (§4.8, H5).
5. **Rule numbering:** this spec's rules 6–7 are the Reader's rules 7–8 (§4.6). Neither is renumbered, because each spec's citations use its own numbers.
6. **`request` values** (`more`, `feedback`, `book_way`, `smaller_step`) are defined for the shared column, which the Reader lists without values (§9).
7. **Cold checks:** the take step before help that Reader D42 asks DL2 for is compatible; it changes when a request is sent, not what is served (§4.8, G-H14).

### 16.4 Left for the Reader spec's next edit (wording only; no schema change)

1. Reader §5.7 says the workbench's columns are "null on other surfaces" and that every other surface writes `assist_kind = 'hint'`. After requests 1 and 5, other surfaces also write `discriminate_answer` rows and fill `level_source`, `rivals_json`, `predicted_answers_json` and `eig_nats`. The CHECK already holds every value, so the migration is unchanged.
2. Reader §11's list of `[hints]` keys can add `help_style` (request 8), and its §18 request 7 can note that `hint_feedback` also carries discriminating answers (request 7).
3. Reader §5.2's zero-EIG fallback names rung 1 only; a level-3 discriminating check the chooser drew falls back to `next_step` (§4.2), which the Reader can cite.

**What did not change.** No phase, table role, successor ruling, route or money cap moved. `approach_maps` is unchanged; replay reads neither table; there is still no DERIVED table, no new reveal kind and no new interaction-event kind; the learner-text widening is the Reader's one rebuild, joined rather than repeated. The grader stays blind (standing constraint H2). Phase H2 stays **L**: the shortcuts, the EIG ranking and the picks add little beside the service it already builds.

---

*Related: `docs/brainstorming/data-driven-hints-in-ITS.pdf` (the source) · `docs/brainstorming/Improving Reader's design.md` (the owner's dialogue) · `spec_reader_workbench_v1.md` §5.2–5.10, §18, §20.11 · `ux_reader_workbench_v1.md` §5.5–5.8, §5.11 · `spec_action_router_v1.md` §0, §6, §7.3 · `spec_learner_field_v1.md` §3.1, §4.3 · `docs/brainstorming/Pipeline Augmentation Plan.md` workstream G · `daily_loop_frictionless_defaults.md`*
