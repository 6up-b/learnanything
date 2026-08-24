# Additional literature review for LearnLoop

I reviewed recent work through **July 2026**, together with several older methods papers that become especially relevant because LearnLoop already logs learner state, interventions, full scheduler slates, propensities, and later retention/transfer outcomes.

## Overall conclusion

The next major improvement([arXiv](https://arxiv.org/abs/2606.03822?utm_source=chatgpt.com "Warning About AI Fallibility Increases Help-Seeking in an Intelligent Tutoring System"))learner embedding. LearnLoop’s explicit architecture is already directionally stronger: it separates knowledge content from derived state, represents facet-level evidence, maintains misconception hypotheses, computes information gain, logs interventions, and can replay the learner state deterministically. t-value research directions are:

1. **Make misconception diagnosis and simulation genuinely process-valid.**
    
2. **Treat learner questions as policy-dependent behavioral observations.**
    
3. **Localize the first reasoning error before choosing a tutor response.**
    
4. **Psychometrically calibrate generated practice items from real outcomes.**
    
5. **Evaluate scheduler changes causally using the propensity data LearnLoop already records.**
    
6. **Select multi-question probe sets jointly rather than choosing several individually high-EIG but redundant questions.**
    

## Priority matrix

|Priority|Paper or paper family|Recommendation|
|---|---|---|
|**P0**|_Learning to Make MISTAKEs_; _MalruleLib_; _Misconception Acquisition Dynamics_|Replace the current canned-answer simulation gate with cycle-consistent, step-aware, applicability-bounded simulation|
|**P0**|_Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank_|Add a proper matcher between observed behavior and LearnLoop’s canonical misconception registry|
|**P0**|_Stepwise Verification and Remediation_; _Bridge_|Introduce first-error localization and a typed tutor-decision stage before response generation|
|**P0**|_Warning About AI Fallibility…_; _Rethinking Scaffolding…_|Contextualize the learner-question signal instead of treating all questions as equivalent mastery evidence|
|**P1**|_Assessing the Quality of AI-Generated Exams_; AutoIRT|Add iterative item critique and empirical item calibration|
|**P1**|Micro-randomized trials; doubly robust evaluation; SPIBB|Build causal and safe policy evaluation around the existing logged slates|
|**P1**|BatchBALD|Select whole diagnostic probe batches for joint information and diversity|
|**P1**|MathTutorBench; MRBench; Tutor Move Taxonomy|Create a permanent tutor evaluation suite and turn-level move telemetry|
|**P2**|DAS3H; dynamic cognitive diagnosis|Benchmark the current learner model against multi-facet forgetting and non-compensatory alternatives|
|**P2**|_Towards Valid Student Simulation with LLMs_|Formalize simulator epistemic states and detect simulator leakage|
|**P3**|LearnLM; TeachLM; pedagogical RL|Consider post-training only after LearnLoop has substantial validated interaction and outcome data|

Several 2026 papers here are recent preprints. Their designs are valuable, but their headline empirical results should be treated as provisional until replicated.

---

# 1. Rebuild the misconception pipeline around cycle consistency

This is the strongest group of papers for LearnLoop.

## 1.1 _Learning to Make MISTAKEs_

MISTAKE generates an incorrect answer, infers the latent misconception that could have caused it, simulates a learner holding that misconception, and checks whether the simulation returns to the original error. That cycle-consistency filter improved student simulation, misconception inference, and human-aligned distractor generation in the authors’ experiments. ([ar5iv](https://ar5iv.org/html/2510.11502v1 "[2510.11502] Learning To Make MISTAKEs: Modeling Incorrect Student Thinking And Key Errors"))ncept is:

[  
\text{wrong answer}  
\rightarrow  
\text{inferred misconception}  
\rightarrow  
\text{simulated reasoning}  
\rightarrow  
\text{wrong answer}  
]

A plausible-sounding misconception is not considered reliable merely because an LLM generated it. It must predict observable behavior.

### Why this matters for LearnLoop

The current diagnostic gate is already a good architectural decision: it evaluates generated misconception probes before accepting them. But its deterministic path is presently conservative string equality—the planted learner submits one recorded `misconception_consistent_answer` or registry signature, and the keyed fatal error fires when the normalized strings match and differ from the expected answer. :

> “Does this one canonical wrong answer trigger the rubric?”

It does not fully test:

> “Would a learner holding this misconception naturally produce recognizably wrong reasoning across different item surfaces?”

### Recommended implementation

For every generated diagnostic candidate:

1. Sample three to five answers from a learner conditioned on the target misconception.
    
2. Require each answer to include a concise step trace or structured explanation.
    
3. Pass the answer back through the misconception matcher.
    
4. Count a successful planted trial only when:
    
    - the answer is wrong;
        
    - the target misconception is recovered in the top (k);
        
    - the answer’s first divergent step is compatible with the misconception;
        
    - the answer is not merely a copy of the stored signature.
        
5. Run clean trials from an expert solver.
    
6. Update the existing Beta sensitivity/specificity posterior from these trials.
    

The deterministic canned-answer test should remain as a cheap first stage. More expensive cycle trials should run only after the candidate passes schema, source, facet, difficulty, and categorical-contrast checks.

---

## 1.2 _Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank_

This paper uses a three-stage pipeline:

1. generate a concise candidate misconception from the dialogue;
    
2. retrieve likely canonical misconception labels;
    
3. rerank those labels using another model.
    

It reports that both generation and reranking contribute to performance on real tutoring dialogues. ([arXiv](https://arxiv.org/abs/2602.02414 "[2602.02414] Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank"))tly fits LearnLoop’s misconception registry.

### Why raw embedding retrieval is not enough

A raw student answer or dialogue may contain:

- problem-specific numbers and symbols;
    
- incomplete or contradictory reasoning;
    
- tutor language;
    
- corrections made later in the conversation;
    
- irrelevant conversational material.
    

Generating a normalized hypothesis first creates an intermediate semantic representation:

```text
Observed:
“I divided the left side by 3 but kept the right side the same.”

Generated hypothesis:
“The learner believes inverse operations need only be applied to the side
containing the target variable.”
```

That description is much easier to compare with canonical registry entries than the raw dialogue.

### Recommended service

Add something equivalent to:

```text
services/misconception_matching.py
```

with this output:

```python
class MisconceptionMatch:
    generated_hypothesis: str
    generated_signature: str | None
    candidate_ids: list[str]
    retrieval_scores: dict[str, float]
    rerank_scores: dict[str, float]
    selected_id: str | None
    selected_probability: float | None
    runner_up_margin: float | None
    abstained: bool
    abstention_reason: str | None
```

The matcher should receive:

- the item prompt;
    
- expected answer;
    
- learner answer;
    
- criterion-level grading evidence;
    
- error attribution;
    
- first-error step, when available;
    
- recent substantive tutor questions;
    
- existing misconceptions on the same or confusable concepts.
    

It should be allowed to **abstain and propose a new misconception**. Forcing every new error into the nearest existing registry entry would gradually corrupt the registry.

---

## 1.3 _MalruleLib_ and _Misconception Acquisition Dynamics_

MalruleLib represents misconceptions as executable incorrect procedures and evaluates whether a model can infer a misconception from one error and apply it across a different problem template. Its reported results show substantial cross-template degradation, while step traces improve misconception prediction. ([arXiv](https://arxiv.org/abs/2601.03217 "[2601.03217] MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces for Modeling Student Thinking in Mathematics"))-up _Misconception Acquisition Dynamics_ finds two particularly important things:

- models trained to simulate one misconception tend to overapply it to contexts where it should not apply;
    
- final-answer-only supervision is insufficient for reliably acquiring the misconception; intermediate reasoning steps are critical. ([arXiv](https://arxiv.org/abs/2604.00818 "Misconception Acquisition Dynamics in Large Language Models"))ssing test: non-applicability
    

A valid simulated learner must satisfy both:

[  
P(\text{target error}\mid  
\text{misconception applies})  
\text{ is high}  
]

and

[  
P(\text{correct}\mid  
\text{misconception does not apply})  
\text{ remains high}.  
]

Otherwise the simulator is not modeling a misconception. It is modeling generalized incompetence.

### Recommended misconception schema extension

For procedural domains, add optional fields such as:

```yaml
procedure_model:
  trigger_conditions:
    - distribution over a sum
    - negative coefficient outside parentheses
  faulty_operator:
    description: "Distributes to the variable term but not the constant term"
  first_divergence_pattern:
    before: "a(bx + c)"
    after: "abx + c"
  applicable_item_families:
    - distributive-equation
  non_applicable_controls:
    - multiplication-without-addition
    - already-expanded-equation
```

This should be optional. Mathematical procedures and code transformations can often support executable rules; historical interpretation or conceptual philosophy usually cannot. For those domains, use natural-language trigger and contrast descriptions instead.

### Cross-surface gate

Generated diagnostics should be tested on:

- the generated item;
    
- a paraphrase with different numbers or entities;
    
- a structurally equivalent transfer item;
    
- at least one item on which the misconception should not apply.
    

This would test the actual latent rule rather than lexical similarity to the original mistake.

---

## 1.4 _Towards Valid Student Simulation with Large Language Models_

This paper describes the “competence paradox”: a highly capable LLM asked to imitate a partially knowledgeable learner may produce fluent but epistemically invalid behavior. It proposes an explicit Epistemic State Specification that defines what knowledge, strategies, errors, and transitions are accessible to the simulated learner. ([arXiv](https://arxiv.org/abs/2601.05473 "[2601.05473] Towards Valid Student Simulation with Large Language Models"))s synthetic-student harness is already valuable because it exercises the production scheduler, attempt pipeline, interventions, and misconception resolution rather than a parallel toy implementation. g layer is a simulator-validity report.

### Add an explicit simulator state

Each synthetic profile should declare:

```yaml
accessible_facets:
  - vector-linear-combination
inaccessible_facets:
  - eigenbasis-change-of-coordinates
misconceptions:
  - id: divides-only-one-side
    applicability: ...
strategies:
  - substitution
  - geometric-interpretation
slip_rate: 0.05
guess_rate: 0.10
learning_transitions:
  clean_success: ...
  corrective_feedback: ...
```

Every generated answer can then be audited for:

- use of inaccessible concepts;
    
- spontaneous disappearance of a misconception;
    
- knowledge improvements without an instructional event;
    
- logically incompatible combinations of strategies;
    
- answer correctness that contradicts the declared state.
    

This produces a much stronger distinction between:

- **behavioral realism**: “This sounds like a student.”
    
- **epistemic validity**: “This response follows from the student state the experiment claims to represent.”
    

---

# 2. Learner questions should remain evidence—but contextual evidence

LearnLoop currently treats substantive questions about a facet as evidence against `facet_solid`. The adjustment is read-side, capped, empirically calibrated, and resolved only after subsequent successful evidence, which are all thoughtful safeguards. terature suggests one more safeguard is necessary.

## The question-generating process is endogenous

A 2026 classroom experiment found that merely warning learners that the AI might be wrong increased hint-seeking, even though the system’s actual behavior was identical. ([arXiv](https://arxiv.org/abs/2606.03822?utm_source=chatgpt.com "Warning About AI Fallibility Increases Help-Seeking in an Intelligent Tutoring System"))alysis of benchmark and deployment conversations found that real users frequently bypass tutor scaffolding, often because the tutor’s framing does not match their immediate learning goal—not necessarily because the learner lacks knowledge or motivation. ([arXiv](https://arxiv.org/abs/2606.15766?utm_source=chatgpt.com "Rethinking Scaffolding in LLM Tutors: The Interactional Mismatch Between Benchmarks and Real-World Deployments"))cent study reports that curiosity-oriented tutor language can increase exploratory questioning without changing the tutor’s underlying instructional quality. ([arXiv](https://arxiv.org/abs/2606.22349?utm_source=chatgpt.com "Curiosity as Linguistic Intervention: Using LLM Tutoring Dialogues to Influence Exploratory Learning Behavior"))

[  
P(\text{asks question}\mid \text{knowledge state})  
]

is insufficient. LearnLoop ultimately needs:

[  
P(\text{asks question}\mid  
\text{knowledge state},  
\text{tutor move},  
\text{interface},  
\text{warning},  
\text{learner goal},  
\text{available help})  
]

## Recommended change

Do not remove question evidence. Instead, separate it into two channels:

### Epistemic signal

Evidence that the learner lacks or is uncertain about the target facet:

- “Why can we move the matrix to the other side?”
    
- “What does the inverse do geometrically?”
    
- “I don’t understand why the columns need to be independent.”
    

### Interaction-preference or goal signal

Evidence about how the learner wants to proceed:

- “Can you just show the full solution?”
    
- “Give me a visual explanation.”
    
- “Can we skip the Socratic questions?”
    
- “I know the calculation; I want the intuition.”
    

The second channel should alter the tutor policy, not the mastery belief.

### Telemetry to add

Persist alongside each `question_event`:

```text
preceding_tutor_move
scaffold_offer_id
scaffold_level
warning_or_disclaimer_state
learner_selected_mode
question_opportunity_shown
hints_already_used
direct_explanation_requested
time_since_prompt
attempt_progress
```

Then calibrate the question likelihood conditional on these features. Until enough data exists, use the current global likelihood ratio but damp it when the question appears strongly preference- or interface-driven.

---

# 3. Add first-error localization and a typed tutor-decision layer

## 3.1 _Stepwise Verification and Remediation of Student Reasoning Errors_

This work collected stepwise reasoning chains with the first erroneous step annotated and showed that grounding response generation in error verification produced more targeted and reliable tutoring responses. ([arXiv](https://arxiv.org/abs/2407.09136?utm_source=chatgpt.com "Stepwise Verification and Remediation of Student Reasoning Errors with Large Language Model Tutors"))s current facet-level grading and error attribution are useful, but two learners can fail the same rubric criterion for different reasons:

```text
Step 1: Writes the correct matrix equation.
Step 2: Multiplies both sides by Q⁻¹ in the wrong order.
Step 3: Simplifies correctly from the incorrect expression.
```

versus:

```text
Step 1: Believes matrix multiplication is commutative.
Step 2: Reorders AQ = QD as QA = DQ.
```

Both may map to a “matrix inverse/order” facet, but they need different interventions.

### Add structured reasoning evidence

Where the response format supports steps, grading should return:

```python
first_error_step: int | None
correct_prefix_length: int
error_span: str | None
error_operation: str | None
upstream_facets_demonstrated: list[str]
downstream_facets_unassessable: list[str]
```

Downstream steps that depend on an earlier error should not be interpreted as independent failures.

For free-form conceptual answers, the analogous unit may be a claim or causal link rather than a numbered algebraic step.

---

## 3.2 _Bridge: Bridging the Novice–Expert Gap_

Bridge decomposes expert remediation into:

1. identify the student error;
    
2. select a remediation strategy;
    
3. state the instructional intent;
    
4. generate the tutor response.
    

In its study, conditioning generation on context-sensitive expert decisions substantially improved preference ratings, while random remediation decisions were highly damaging. ([arXiv](https://arxiv.org/abs/2310.10648?utm_source=chatgpt.com "Bridging the Novice-Expert Gap via Models of Decision-Making: A Case Study on Remediating Math Mistakes"))should adopt the **structured decision**, not hidden free-form reasoning.

### Proposed `TutorDecision`

```python
class TutorDecision:
    target_facets: list[str]
    diagnosed_gap: str
    first_error_step: int | None
    misconception_id: str | None
    confidence: float
    tutor_move: str
    instructional_intent: str
    scaffold_level: float
    answer_reveal_budget: str
    expected_learner_action: str
    source_ref_ids: list[str]
```

Candidate `tutor_move` values could include:

```text
clarify_prompt
elicit_reasoning
localize_error
give_minimal_hint
state_subgoal
provide_partial_worked_step
contrast_cases
counterexample
explain_concept
worked_example
ask_transfer_question
encourage_reflection
```

The model then generates text from this validated decision.

This creates three distinct evaluation targets:

- Was the learner state diagnosed correctly?
    
- Was the right instructional action selected?
    
- Was that action verbalized well?
    

Without this split, a polished response can obscure an incorrect pedagogical decision.

---

## 3.3 Tutor Move Taxonomy and Tutor CoPilot

The 2026 Tutor Move Taxonomy organizes authentic tutor actions into tutoring support, learning support, social-emotional support, and logistical support, with learning moves ranging from eliciting reasoning to directly providing explanations. ([arXiv](https://arxiv.org/abs/2603.05778?utm_source=chatgpt.com "Tutor Move Taxonomy: A Theory-Aligned Framework for Analyzing Instructional Moves in Tutoring"))lot provides rare real-world experimental evidence: in a randomized deployment with human tutors, access to AI-generated expert-like suggestions increased topic mastery overall and produced larger gains among lower-rated tutors. It also changed the strategies tutors used, while revealing failure modes such as grade-level mismatch. ([arXiv](https://arxiv.org/abs/2410.03017?utm_source=chatgpt.com "Tutor CoPilot: A Human-AI Approach for Scaling Real-Time Expertise"))CoPilot result does not prove that an autonomous LLM tutor will produce the same gains. It does support two LearnLoop decisions:

- tutor actions should be represented and logged as discrete moves;
    
- pedagogical quality should be connected to later learning outcomes, not judged only from the wording of the response.
    

Every Tutor Q&A and teach-back turn should therefore record its move and intended learner action.

---

# 4. Improve generated items with real psychometric calibration

## 4.1 _Assessing the Quality of AI-Generated Exams_

This field study used iterative generation, critique, and revision and then evaluated AI-generated questions using student responses and item-response models across many real classes. The authors found that AI-generated items could perform comparably to expert items in their setting, while emphasizing that psychometric quality must be established empirically. ([arXiv](https://arxiv.org/abs/2508.08314?utm_source=chatgpt.com "Assessing the Quality of AI-Generated Exams: A Large-Scale Field Study"))already stores authored or estimated item difficulty, evidence facets, retrieval demand, transfer distance, scaffold level, surface family, rubrics, and misconception targets. tep is to stop treating “accepted by the authoring model and schema validator” as the end of item validation.

## Recommended item lifecycle

```text
generated
→ structurally validated
→ source-grounded
→ critique/revision
→ diagnostic simulation gate
→ provisionally active
→ empirically calibrated
→ trusted / revised / retired
```

### Separate item-quality dimensions

Do not collapse everything into one `bad_item_suspicion` value. Track:

```text
source_support
answer_unambiguity
rubric_reliability
empirical_difficulty
difficulty_calibration_error
empirical_discrimination
misconception_sensitivity
misconception_specificity
surface_novelty
answer_leakage_risk
retention_predictiveness
transfer_predictiveness
exposure_count
```

A question can be:

- unambiguous but too easy;
    
- difficult but highly discriminating;
    
- good for immediate diagnosis but poor for transfer;
    
- valid for one misconception but useless for general mastery;
    
- pedagogically useful despite low conventional test discrimination.
    

Those distinctions matter to the scheduler.

---

## 4.2 AutoIRT and BanditCAT

AutoIRT uses item content features to produce initial item-parameter estimates and then adds item-specific calibration. BanditCAT uses Bayesian updating and Thompson sampling to balance learning uncertain item parameters against selecting informative assessment items. ([arXiv](https://arxiv.org/abs/2410.21033?utm_source=chatgpt.com "BanditCAT and AutoIRT: Machine Learning Approaches to Computerized Adaptive Testing and Item Calibration"))ght LearnLoop analogue would be useful:

[  
b_i \sim \mathcal N(\hat b_{\text{text}}, \sigma_b^2)  
]

where (\hat b_{\text{text}}) is the current author or LLM estimate. Real responses then update the item-specific posterior.

Similarly, discrimination could start from a conservative prior informed by:

- practice mode;
    
- number and composition of facets;
    
- rubric structure;
    
- retrieval demand;
    
- scaffold level;
    
- transfer distance;
    
- diagnostic simulation results.
    

### Important boundary

Fisher information and Thompson sampling are appropriate for:

- initial probes;
    
- held-out examinations;
    
- item calibration;
    
- uncertainty-reduction intent.
    

They should not become the general practice reward. A maximally diagnostic question is not necessarily the activity with the highest expected learning gain.

---

# 5. Select probe sets jointly with BatchBALD logic

LearnLoop typically needs multiple initial or follow-up probes. Choosing the top three questions independently by EIG can yield:

```text
Question A: tests the same matrix-order misconception
Question B: paraphrases A
Question C: changes only the numbers
```

Each may have high individual EIG, but the set is redundant.

BatchBALD selects batches using joint mutual information and was developed specifically to avoid sets of individually informative but mutually redundant acquisitions. ([arXiv](https://arxiv.org/abs/1906.08158?utm_source=chatgpt.com "BatchBALD: Efficient and Diverse Batch Acquisition for Deep Bayesian Active Learning"))does not need a Bayesian neural network implementation. Its outcome space is already discrete and analytical.

## Greedy conditional probe selection

Choose:

[  
x_1 = \arg\max_x I(Y_x; H)  
]

then:

[  
x_2 = \arg\max_x I(Y_x; H \mid Y_{x_1})  
]

and continue until reaching the probe budget.

A practical approximation can penalize overlap in:

- evidence facets;
    
- surface family;
    
- misconception fire channels;
    
- expected outcome partitions;
    
- solution procedure;
    
- representation type.
    

This is a better extension of the existing EIG work than adding another scalar bonus to every item. LearnLoop already has exact predictive facet EIG over held-out items, although its default scheduler contribution is currently disabled. ended experiment

Compare:

1. top-(k) independent hypothesis EIG;
    
2. top-(k) independent predictive EIG;
    
3. greedy conditional/joint EIG;
    
4. diversity-penalized independent EIG;
    
5. random eligible probes.
    

Primary outcomes:

- posterior entropy after the full probe set;
    
- correct misconception identification;
    
- calibration of facet posteriors;
    
- number of probes to convergence;
    
- later held-out transfer prediction.
    

---

# 6. Keep the explicit learner model; benchmark it against DAS3H and cognitive diagnosis

## 6.1 DAS3H

DAS3H combines multi-skill item tagging with skill-specific learning and forgetting histories using temporally distributed practice features. The paper reports improvements over comparison models on three educational datasets. ([arXiv](https://arxiv.org/abs/1905.06873?utm_source=chatgpt.com "DAS3H: Modeling Student Learning and Forgetting for Optimally Scheduling Distributed Practice of Skills"))levant because LearnLoop items can cover multiple evidence facets, while conventional spaced-repetition state is strongly item-oriented.

### Implement it as a benchmark first

Build an offline prediction model using:

- per-facet successes and failures;
    
- logarithmic time windows;
    
- hints and coverage;
    
- item bias;
    
- facet bias;
    
- difficulty;
    
- retrieval demand;
    
- transfer distance;
    
- response latency;
    
- familiarity/surface-family exposure.
    

Compare against the current FSRS plus mastery/facet system on:

- next-attempt log loss;
    
- Brier score;
    
- calibration;
    
- same-item delayed retention;
    
- same-LO transfer;
    
- held-out exam performance.
    

A model that improves next-answer AUC but worsens delayed retention calibration should not replace the current system.

---

## 6.2 Do not replace learner state with an LLM

A 2025 study comparing an LLM with deep knowledge tracing found that the explicit knowledge-tracing model had better next-response discrimination and more coherent temporal mastery updates; the LLM showed inconsistent and sometimes wrong-direction state transitions. ([arXiv](https://arxiv.org/abs/2512.23036 "[2512.23036] Problems With Large Language Models for Learner Modelling: Why LLMs Alone Fall Short for Responsible Tutoring in K--12 Education"))rts LearnLoop’s present division of labor:

- deterministic/probabilistic code owns durable learner state;
    
- LLMs grade, classify, generate, explain, and propose;
    
- LLM output becomes typed evidence rather than an opaque replacement state.
    

This separation should remain a core architectural constraint.

---

## 6.3 Dynamic cognitive diagnosis

Recent dynamic cognitive-diagnosis work jointly estimates skill mastery and item-to-skill mappings while incorporating behavioral covariates and transitions. ([arXiv](https://arxiv.org/abs/2506.14531?utm_source=chatgpt.com "A statistical framework for dynamic cognitive diagnosis in digital learning environments"))should not automatically learn and overwrite its facet mappings from sparse single-user data. But it can use residual patterns to propose reviews:

```text
Item consistently behaves as though it requires facet B,
but its metadata only lists facet A.
```

Possible review triggers:

- residual errors concentrate among learners weak on an unlisted facet;
    
- two supposedly separate facets are observationally indistinguishable;
    
- one rubric criterion loads on multiple facets differently from the authored mapping;
    
- success appears conjunctive rather than compensatory.
    

These should produce reviewable metadata proposals, consistent with LearnLoop’s existing proposal-and-acceptance architecture.

---

# 7. Build causal scheduler evaluation before learned scheduling

This may be the highest-leverage infrastructure investment because much of the required logging is already present.

LearnLoop records full scheduler slates, candidate components, selected status, choice propensities, subsequent attempts, and same-item retention or same-LO transfer labels. ro-randomized trials

Micro-randomized trials repeatedly randomize intervention choices at eligible decision points, allowing estimation of whether an intervention works and under what contexts it works. ([arXiv](https://arxiv.org/abs/2107.03544?utm_source=chatgpt.com "The Micro-Randomized Trial for Developing Digital Interventions: Experimental Design and Data Analysis Considerations"))oop, appropriate randomized decisions include:

- intervene now versus defer;
    
- minimal hint versus guiding question;
    
- repair versus diagnostic probe;
    
- two near-tied eligible practice items;
    
- immediate sibling retry versus later reconstruction;
    
- teach-back versus constructed response for a high-mastery facet.
    

Randomization should occur only inside a predefined safe/near-tie set.

### Outcomes

Avoid same-turn answer correction as the primary outcome. It rewards tutors that simply reveal more.

Use:

**Proximal outcome**

```text
Next unhinted attempt on the targeted facet after a minimum delay
```

**Distal outcomes**

```text
Delayed retention
Same-LO transfer
Held-out exam performance
Goal attainment
Intervention burden
Session abandonment
```

Recent work also extends micro-randomized designs to distal outcomes, which is relevant when the true objective is later retention rather than the next interaction. ([arXiv](https://arxiv.org/abs/2502.13500?utm_source=chatgpt.com "Distal Causal Excursion Effects: Modeling Long-Term Effects of Time-Varying Treatments in Micro-Randomized Trials"))2 Doubly robust off-policy evaluation

Doubly robust evaluation combines:

- a model predicting the reward of each action;
    
- inverse propensity correction from the actual logging policy.
    

It remains consistent when either the reward model or the logging-policy model is correctly specified under the relevant assumptions. ([arXiv](https://arxiv.org/abs/1103.4601?utm_source=chatgpt.com "Doubly Robust Policy Evaluation and Learning"))arnLoop already persists propensities before exploration changes the queue order, it has the right foundation for this analysis. luation layer that reports:

```text
direct-method estimate
inverse-propensity estimate
self-normalized IPS
doubly robust estimate
effective sample size
maximum importance weight
action-support warnings
confidence interval
```

A single estimated policy value without overlap diagnostics would be unsafe.

---

## 7.3 Safe policy improvement

SPIBB-style methods make a learned policy fall back to the baseline in poorly supported state-action regions rather than freely extrapolating. ([arXiv](https://arxiv.org/abs/1712.06924?utm_source=chatgpt.com "Safe Policy Improvement with Baseline Bootstrapping"))p version could say:

```text
When this learner-state × item-intent × practice-mode region has
insufficient supported outcomes, retain selection_reward_v1.
Only deviate where the candidate policy has sufficient evidence
and a conservative lower confidence bound exceeds baseline.
```

This is preferable to globally replacing scheduler coefficients after fitting a model.

---

## 7.4 Reward-hacking caution

Recent educational-RL work illustrates how an agent can optimize engagement-like proxy rewards while failing to produce equivalent learning progress; its simulated results suggest that hard pedagogical constraints may be necessary in addition to multi-objective rewards. ([arXiv](https://arxiv.org/abs/2604.04237?utm_source=chatgpt.com "Pedagogical Safety in Educational Reinforcement Learning: Formalizing and Detecting Reward Hacking in AI Tutoring Systems"))any future scheduler-learning objective should retain constraints such as:

- minimum cognitive demand;
    
- held-out exam quarantine;
    
- no repeated low-value interaction loops;
    
- exposure and familiarity limits;
    
- prerequisite constraints;
    
- answer-leakage limits;
    
- per-session intervention caps.
    

---

# 8. Create a permanent tutor evaluation suite

## Relevant benchmarks

MathTutorBench evaluates subject expertise, student understanding, mistake localization, and pedagogical response generation. It finds that problem-solving ability does not automatically imply tutoring ability and that longer dialogues are particularly challenging. ([arXiv](https://arxiv.org/abs/2502.18940?utm_source=chatgpt.com "MathTutorBench: A Benchmark for Measuring Open-ended Pedagogical Capabilities of LLM Tutors"))fines eight pedagogical dimensions for responses grounded in student mistakes or confusion. ([arXiv](https://arxiv.org/abs/2412.09416?utm_source=chatgpt.com "Unifying AI Tutor Evaluation: An Evaluation Taxonomy for Pedagogical Ability Assessment of LLM-Powered AI Tutors"))ames educational alignment as **pedagogical instruction following**: developers should be able to specify the desired pedagogical behavior for a context rather than hard-coding one universal tutoring style. ([arXiv](https://arxiv.org/abs/2412.16429?utm_source=chatgpt.com "LearnLM: Improving Gemini for Learning"))nded `tutor-eval` dimensions

### Factual and diagnostic

- response correctness;
    
- source grounding;
    
- correct first-error location;
    
- misconception top-(k) recall;
    
- false-positive misconception rate;
    
- preservation of demonstrated facets.
    

### Pedagogical

- move matches the diagnosed state;
    
- actionable next step;
    
- appropriate scaffold level;
    
- encourages learner reasoning where appropriate;
    
- does not prematurely reveal the answer;
    
- does not continue Socratic scaffolding after an explicit request for explanation;
    
- adapts to the learner-selected mode.
    

### Interaction quality

- multi-turn consistency;
    
- no repeated question loop;
    
- concise enough for the context;
    
- grade and expertise appropriateness;
    
- acknowledges uncertainty;
    
- avoids claiming that the learner said or demonstrated something absent from the record.
    

### Downstream

- next independent correctness;
    
- delayed retention;
    
- transfer;
    
- time and turns to correction;
    
- unnecessary intervention count.
    

LLM judging can be one component, but not the only evaluator. Combine it with:

- deterministic answer-leak checks;
    
- formal or numerical verifiers where available;
    
- source-attribution checks;
    
- known synthetic misconception states;
    
- human review samples;
    
- real delayed outcomes.
    

---

# 9. Post-training papers are relevant later, not now

## TeachLM

TeachLM reports improvements from parameter-efficient post-training on a very large corpus of authentic longitudinal tutoring interactions and uses a synthetic student model for multi-turn evaluation. ([arXiv](https://arxiv.org/abs/2510.05087?utm_source=chatgpt.com "TeachLM: Post-Training LLMs for Education Using Authentic Learning Data"))ical RL

_From Problem-Solving to Teaching Problem-Solving_ trains tutor behavior through simulated multi-turn interaction and explores a trade-off between pedagogical quality and student answer accuracy. ([arXiv](https://arxiv.org/abs/2505.15607?utm_source=chatgpt.com "From Problem-Solving to Teaching Problem-Solving: Aligning LLMs with Pedagogy using Reinforcement Learning"))rs are relevant to LearnLoop’s future, but neither should drive an immediate model-training project.

LearnLoop first needs:

1. reliable tutor-move labels;
    
2. trustworthy misconception inference;
    
3. validated student simulations;
    
4. delayed outcome labels;
    
5. randomized policy support;
    
6. an evaluator that detects answer leakage and proxy gaming.
    

A sensible progression is:

```text
typed prompts
→ candidate generation and reranking
→ supervised learning from accepted decisions
→ contextual bandit over constrained tutor moves
→ only then consider multi-turn RL
```

Also avoid training one model indiscriminately as both simulated learner and expert tutor. The Student Data Paradox reports that training on student-like erroneous dialogue can damage a model’s factual and reasoning capabilities. ([arXiv](https://arxiv.org/abs/2404.15156?utm_source=chatgpt.com "Student Data Paradox and Curious Case of Single Student-Tutor Model: Regressive Side Effects of Training LLMs for Personalized Learning"))ommended implementation roadmap

## Stage 1: Misconception validity

Add:

```text
services/misconception_matching.py
services/misconception_simulation.py
tests/test_misconception_retrieve_rerank.py
tests/test_cycle_consistency_gate.py
tests/test_misconception_applicability_controls.py
```

Implement:

- generate–retrieve–rerank;
    
- calibrated abstention;
    
- multiple planted traces;
    
- reverse misconception inference;
    
- clean and non-applicable controls;
    
- cross-surface tests;
    
- first-divergence metadata.
    

This is the most important immediate workstream.

## Stage 2: Contextual question evidence

Extend `question_events` with interaction-policy context.

Update `question_signal.py` to resolve:

```text
knowledge_signal
interaction_preference_signal
question_likelihood_context
```

Do not let a question change durable mastery directly. Keep the current replay-safe, read-side design.

## Stage 3: Typed tutoring decisions

Introduce:

```text
TutorDecision
TutorMove
FirstErrorVerification
```

Every generated response should be traceable to:

```text
diagnosis → selected move → instructional intent → response
```

## Stage 4: Item calibration and joint probes

Add:

- candidate critique/revision;
    
- empirical difficulty and discrimination posteriors;
    
- provisional item status;
    
- greedy conditional EIG for multi-item probe sets;
    
- item-quality dashboards split by purpose.
    

## Stage 5: Causal policy evaluation

Implement:

```text
eval/off_policy.py
eval/micro_randomization.py
eval/safe_policy_improvement.py
```

Begin with near-tie randomization and doubly robust evaluation. Do not deploy a learned scheduler policy until conservative lower-bound performance exceeds the current baseline in adequately supported contexts.

## Stage 6: Model benchmarking and possible learning

Benchmark:

- current FSRS plus EKF/facet model;
    
- DAS3H-style multi-facet forgetting;
    
- a calibrated cognitive-diagnosis baseline;
    
- later, a constrained learned scheduler.
    

Only after these stages should LearnLoop consider tutor post-training or pedagogical RL.

---

# Final ranked reading list

The most important additional papers for the project are:

1. **Learning to Make MISTAKEs: Modeling Incorrect Student Thinking And Key Errors** — cycle consistency for misconception simulation and inference. ([ar5iv](https://ar5iv.org/html/2510.11502v1 "[2510.11502] Learning To Make MISTAKEs: Modeling Incorrect Student Thinking And Key Errors"))ception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank** — canonical registry matching. ([arXiv](https://arxiv.org/abs/2602.02414 "[2602.02414] Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank"))eLib** — executable, cross-template misconception procedures and step traces. ([arXiv](https://arxiv.org/abs/2601.03217 "[2601.03217] MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces for Modeling Student Thinking in Mathematics"))ception Acquisition Dynamics in Large Language Models** — applicability boundaries and the necessity of step supervision. ([arXiv](https://arxiv.org/abs/2604.00818 "Misconception Acquisition Dynamics in Large Language Models"))se Verification and Remediation of Student Reasoning Errors** — first-error localization. ([arXiv](https://arxiv.org/abs/2407.09136?utm_source=chatgpt.com "Stepwise Verification and Remediation of Student Reasoning Errors with Large Language Model Tutors"))ng the Novice–Expert Gap via Models of Decision-Making** — structured pedagogical decisions before response generation. ([arXiv](https://arxiv.org/abs/2310.10648?utm_source=chatgpt.com "Bridging the Novice-Expert Gap via Models of Decision-Making: A Case Study on Remediating Math Mistakes"))ing the Quality of AI-Generated Exams** — iterative critique plus real psychometric evaluation. ([arXiv](https://arxiv.org/abs/2508.08314?utm_source=chatgpt.com "Assessing the Quality of AI-Generated Exams: A Large-Scale Field Study"))cro-Randomized Trial for Developing Digital Interventions** — causal evaluation of repeated adaptive decisions. ([arXiv](https://arxiv.org/abs/2107.03544?utm_source=chatgpt.com "The Micro-Randomized Trial for Developing Digital Interventions: Experimental Design and Data Analysis Considerations")) Robust Policy Evaluation and Learning** — evaluation from logged propensities and outcomes. ([arXiv](https://arxiv.org/abs/1103.4601?utm_source=chatgpt.com "Doubly Robust Policy Evaluation and Learning"))BALD** — non-redundant joint probe selection. ([arXiv](https://arxiv.org/abs/1906.08158?utm_source=chatgpt.com "BatchBALD: Efficient and Diverse Batch Acquisition for Deep Bayesian Active Learning"))utorBench** and **MRBench** — permanent tutor-quality evaluation. ([arXiv](https://arxiv.org/abs/2502.18940?utm_source=chatgpt.com "MathTutorBench: A Benchmark for Measuring Open-ended Pedagogical Capabilities of LLM Tutors"))** — multi-facet learning and forgetting baseline. ([arXiv](https://arxiv.org/abs/1905.06873?utm_source=chatgpt.com "DAS3H: Modeling Student Learning and Forgetting for Optimally Scheduling Distributed Practice of Skills"))ds Valid Student Simulation with Large Language Models** — explicit simulator epistemic states. ([arXiv](https://arxiv.org/abs/2601.05473 "[2601.05473] Towards Valid Student Simulation with Large Language Models"))nking Scaffolding in LLM Tutors** — adapt tutoring to actual user uptake and goals. ([arXiv](https://arxiv.org/abs/2606.15766?utm_source=chatgpt.com "Rethinking Scaffolding in LLM Tutors: The Interactional Mismatch Between Benchmarks and Real-World Deployments"))Policy Improvement with Baseline Bootstrapping** — conservative deployment of learned policies. ([arXiv](https://arxiv.org/abs/1712.06924?utm_source=chatgpt.com "Safe Policy Improvement with Baseline Bootstrapping")) most defensible next product/research milestone is:
    

> **A cycle-consistent misconception pipeline that generates several diagnostic candidates, maps behavior to the canonical registry through generate–retrieve–rerank, tests each candidate on planted, clean, cross-surface, and non-applicable cases, and retains the best validated discriminator.**

That would strengthen the weakest assumption in the current system while reusing most of the architecture LearnLoop already has.