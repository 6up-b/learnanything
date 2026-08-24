[arXiv](https://arxiv.org/html/2608.05085v1)

*Review + integration with KT/datasets survey: [[Diagnostic Pipeline Synthesis]]*

> **A hypothesis is not a capability. A capability is something that makes a better hypothesis test possible.**

In the paper, the hidden system (M^_) is queried through experiments; the agent maintains a weighted ensemble (B) of executable hypotheses; and the capability set (I) determines which experiments are currently available. Constructive actions add to (I), while interventional experiments produce evidence about (M^_). ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

For LearnLoop, the corresponding objects would be:

|Paper|LearnLoop|
|---|---|
|Hidden system (M^*)|Learner’s latent knowledge state, misconception state, strategy, and noise state|
|Weighted model ensemble (B)|Posterior over candidate explanations for the learner’s behavior|
|Query (q)|“What is the smallest safe repair?” or “Which repair-relevant gap caused this failure?”|
|Interventional experiment|A diagnostic probe presented to the learner|
|Capability (I)|A prerequisite that makes a more discriminating probe expressible, available, or reliably gradable|
|Constructive experiment|An action that builds such a diagnostic capability|
|Goal (G)|Enough decision confidence to choose a repair—not necessarily complete identification of the learner|
|Intervention/repair|A separate action that deliberately changes the learner’s state|

That last row matters: the paper’s experiments mostly **observe a fixed hidden system**. LearnLoop’s repair actions change the hidden system. Therefore, the paper gives you the right planning architecture, but LearnLoop needs an extension that represents both **epistemic actions** and **pedagogical state transitions**.

---

## 1. What should count as a capability?

A capability should generally be a property of the **tutoring system’s diagnostic apparatus**, not a hypothesis about the student.

For example:

|Capability|What it unlocks|
|---|---|
|`has_canonical_solution_graph`|Step-level comparison between the student’s reasoning and a grounded derivation|
|`has_facet_decomposition`|Questions targeting individual subskills instead of the whole concept|
|`has_executable_hypothesis_set`|Predictions about how each candidate misconception would answer future probes|
|`has_validated_contrastive_probe`|A question designed to distinguish two repair-relevant hypotheses|
|`has_step_level_grader`|Process evidence rather than only correctness|
|`has_symbolic_response_channel`|Inspection of intermediate algebraic transformations|
|`has_diagram_response_channel`|Spatial or geometric diagnostic probes|
|`has_calibrated_response_model`|Estimates of (P(o\mid h,e)) rather than uncalibrated LLM guesses|
|`has_targeted_repair`|A repair grounded in the exact facet or misconception|
|`has_transfer_audit`|A delayed question that tests whether the repaired understanding generalizes|

A set of questions is not quite the capability. The capability is the machinery or validated representation that **makes those questions safely usable**.

For example:

- “Question 17” is an action.
    
- “A calibrated bank of contrastive questions for distinguishing sign errors from rotation-composition misconceptions” is a capability.
    
- “The student misunderstands rotation composition” is a hypothesis.
    
- “The student can multiply complex numbers” is part of the hidden learner state.
    

The paper explicitly allows capabilities to be representational or computational, though its theorem is formally restricted to action-space gating. It also identifies state-dependent hypothesis languages and query sets as a natural extension. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

### System-side versus learner-side capability

It is useful to reserve two different symbols:

# [  
I_t^{\text{sys}}

\text{diagnostic capabilities currently available to LearnLoop}  
]

and

# [  
z_t^{\text{learner}}

\text{learner’s latent knowledge and misconception state}.  
]

A learner’s ability to apply the chain rule is colloquially a “capability,” but it should be represented inside (z_t^{\text{learner}}), not inside the paper’s capability set (I).

This separation prevents a serious conceptual confusion:

- **Constructing a step-level rubric** changes what LearnLoop can measure.
    
- **Teaching the chain rule** changes what the learner knows.
    

Those are different transitions.

---

# 2. The four kinds of action LearnLoop should model

I would expand the paper’s two action types into four.

## A. Constructive diagnostic actions

These modify (I_t^{\text{sys}}) while adding little or no new evidence about the learner.

Examples:

- Retrieve the canonical section and derivation associated with the failed problem.
    
- Decompose the problem into concepts, facets, operations, representations, and prerequisites.
    
- Convert an LLM grader’s free-form explanation into executable hypotheses.
    
- Generate a contrastive probe for two competing misconceptions.
    
- Construct and validate a scoring rubric for that probe.
    
- Search the question bank for items that isolate a specific facet.
    
- Build a temporary symbolic or diagram-based response interface.
    
- Calibrate an item’s predicted response signatures using previous learner data.
    
- Compile several near-duplicate hypotheses into one repair-equivalence class.
    

These are the cleanest analogue of the paper’s constructive experiments. They may take computation and latency, but they do not necessarily consume learner attention.

This is potentially where the paper is **most valuable for LearnLoop**: you can spend machine effort to create a high-value measurement rather than spending learner effort on a sequence of weak questions.

## B. Diagnostic probes

These correspond to the paper’s interventional experiments. They query the learner and generate evidence about the latent state.

Examples:

- Multiple-choice probe with misconception-specific distractors.
    
- Free-response explanation.
    
- “Show the next step only.”
    
- Ask for confidence.
    
- Ask the learner to compare two nearly identical solutions.
    
- Ask for a counterexample.
    
- Switch representation: equation to diagram, diagram to verbal explanation.
    
- Test a prerequisite or adjacent facet.
    
- Give a transfer problem with changed surface form.
    
- Ask the learner to predict what would happen under a counterfactual change.
    

In LearnLoop terminology, it may be clearer to call these **measurement probes**, because “intervention” usually implies teaching or changing the learner.

## C. Repair actions

These deliberately change the latent state.

Examples:

- Minimal hint.
    
- Contrastive explanation.
    
- Counterexample.
    
- Two-line prerequisite refresher.
    
- Worked example.
    
- Guided practice.
    
- Targeted practice sequence.
    
- Minimal backtracking to one prerequisite.
    

The original paper does not fully model this because its hidden mechanism is fixed within an episode. LearnLoop must explicitly model repair effects.

## D. Audits

Audits measure the learner after repair:

- Immediate audit.
    
- Near-transfer audit.
    
- Delayed retrieval check.
    
- Representation-switch audit.
    
- Far-transfer check.
    

Audits are diagnostic probes, but they occur after a state transition and answer a different query: not “what caused the original failure?” but “did the repair produce durable and transferable understanding?”

---

# 3. LearnLoop needs a dual-effect state-transition model

Let the hidden learner state be

# [  
z_t

(m_t,\xi_t,\sigma_t,\nu_t),  
]

where:

- (m_t): facet-specific mastery;
    
- (\xi_t): misconception variables;
    
- (\sigma_t): strategy or representation being used;
    
- (\nu_t): slip, guessing, fatigue, language, attention, and off-task variables.
    

For every action (a_t), LearnLoop should represent both:

[  
o_t \sim P(o_t\mid z_t,a_t)  
]

and

[  
z_{t+1}\sim T(z_{t+1}\mid z_t,a_t,o_t).  
]

The first is the **measurement model**. The second is the **learning transition model**.

The action types then have different signatures:

|Action|Information about (z_t)|Changes (z_t)|Changes (I_t^{\text{sys}})|
|---|--:|--:|--:|
|Constructive system action|Usually none|No|Yes|
|Diagnostic probe|Yes|Slightly, through retrieval/cueing|Usually no|
|Repair|Sometimes|Intentionally|Possibly|
|Audit|Yes|Slightly|No|

This captures an important educational complication: even a “pure” diagnostic question can create retrieval practice, reveal a hint through its wording, or induce a strategy change. LearnLoop therefore cannot assume perfectly nondestructive measurement.

A useful transition equation is:

[  
s_t =  
(B_t,D_t,I_t^{\text{sys}},\mathcal L_t,\mathcal Q_t),  
]

where:

- (B_t) is the belief over learner-state hypotheses;
    
- (D_t) is the permanent interaction archive;
    
- (I_t^{\text{sys}}) is the current capability set;
    
- (\mathcal L_t) is the executable hypothesis language;
    
- (\mathcal Q_t) is the currently expressible probe and repair set.
    

A constructive action can expand (I_t^{\text{sys}}), (\mathcal L_t), or (\mathcal Q_t).

---

# 4. What should the target query be?

The target should usually **not** be:

> “Identify the learner’s exact misconception.”

That invites overdiagnosis and excessive questioning.

The better target is:

> “Determine enough about the learner to choose the smallest repair whose expected regret is acceptably low.”

Suppose the credible hypotheses are

# [  
C_\delta(B_t)

{h: B_t(h)\text{ is sufficiently credible}}.  
]

Let

[  
A_\epsilon(h)  
]

be the set of repairs whose loss is within (\epsilon) of optimal under hypothesis (h).

Then your existing intersection rule fits perfectly:

[  
\bigcap_{h\in C_\delta(B_t)}A_\epsilon(h)\neq\varnothing  
\quad\Longrightarrow\quad  
\text{stop diagnosing and repair now}.  
]

For example, suppose LearnLoop is uncertain between:

- the learner forgot a sign convention;
    
- the learner made an isolated algebraic slip;
    
- the learner weakly remembers the inverse-rotation identity.
    

If the same 20-second contrastive reminder is safe and near-optimal under all three, there is little reason to ask another question merely to assign the learner a more precise label.

By contrast, if the credible hypotheses imply very different repairs—

- two-line algebra repair;
    
- prerequisite lesson on dot products;
    
- review of complex multiplication;
    
- no repair because the answer was merely mistyped—
    

then further diagnosis has decision value.

This makes the query’s support

[  
\operatorname{supp}(q)  
]

the set of latent components whose value could change the repair decision. The paper similarly defines the target around components relevant to the query rather than requiring the entire hidden system to be learned. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

---

# 5. Turning a free-form LLM hypothesis into an executable hypothesis

This is one of the closest points of contact with the paper.

The paper explicitly requires executable models and excludes free-text hypotheses from the formalism because free text does not, by itself, support automated consistency checking, prediction of experimental outcomes, localization of failures, counterfactual queries, or rolling candidate actions forward. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

So an LLM grader saying:

> “The learner may understand rotation but be confusing the transpose with an ordinary rotation.”

is useful as a **proposal**, but it is not yet a model that your planner can use.

An executable LearnLoop hypothesis could be represented as

[  
h_k =  
\left(  
F_k,,  
\Xi_k,,  
P_k(o\mid e),,  
T_k(z'\mid a),,  
L_k(a),,  
W_k  
\right),  
]

where:

- (F_k): implicated facets and prerequisites;
    
- (\Xi_k): structured misconception predicates;
    
- (P_k(o\mid e)): predicted response distribution for diagnostic probe (e);
    
- (T_k(z'\mid a)): predicted effect of repair (a);
    
- (L_k(a)): repair cost and risk;
    
- (W_k): witnesses or falsifiers that distinguish this hypothesis.
    

A practical hypothesis record might contain:

|Field|Example|
|---|---|
|Natural-language claim|“Treats (R(a)^T) as (R(a)), rather than (R(-a))”|
|Target facet|Rotation inverse|
|Prerequisites|Matrix transpose; orthogonality|
|Predicted error signature|Produces (R((m+n)\theta)) or (R((m-n)\theta)) inconsistently|
|Predicted correct items|Can compose rotations without transpose|
|Discriminating probe|Ask only for (R(a)^TR(b))|
|Competing hypotheses|General composition gap; isolated sign slip|
|Minimal repair|Explain transpose-as-inverse with one geometric counterexample|
|Falsifier|Correctly derives (R(a)^T=R(-a)) in a novel context|
|Confidence|Posterior distribution, not a binary label|
|Provenance|Original response, grader evidence, canonical source|

The central executable object is a probe–hypothesis likelihood tensor:

[  
M_{e,h,o}=P(o\mid e,h).  
]

Without some estimate of this tensor, you cannot meaningfully compute:

- expected information gain;
    
- expected reduction in repair regret;
    
- expected cost to diagnosis;
    
- whether a question actually distinguishes two hypotheses;
    
- whether two hypotheses are observationally equivalent.
    

## A compilation pipeline

The free-form grader output could go through the following transformation:

1. **Evidence extraction.** Convert the raw response into evidence atoms: incorrect step, omitted relation, terminology used, confidence, latency, self-correction, hint use, and rationale structure.
    
2. **Facet grounding.** Link evidence to nodes and relations in the generated concept graph.
    
3. **Hypothesis proposal.** Produce multiple explanations, including slip/noise and (h_{\text{other}}), rather than one confident diagnosis.
    
4. **Canonicalization.** Match each proposed explanation to a known misconception template or create a provisional structured hypothesis.
    
5. **Prediction compilation.** For each hypothesis, generate predicted response signatures on candidate probes.
    
6. **Consistency checking.** Reject or downweight hypotheses that contradict the existing interaction archive.
    
7. **Repair-equivalence clustering.** Merge hypotheses that imply essentially the same minimal repair.
    
8. **Witness generation.** Generate probes specifically targeting remaining repair-distinct hypotheses.
    

The LLM remains useful, but it becomes a **proposer and compiler assistant**, not the final Bayesian state estimator.

---

# 6. How EduEmbed could fit

[[EduEmbed]] is a promising substrate, but generic semantic similarity should be treated as a **candidate-retrieval mechanism**, not as the diagnostic decision rule.

EduEmbed learns role-specific representations for learners, exercises, and concepts, aligns learner and exercise representations in concept space, and integrates textual semantics with conventional ID embeddings. It is also evaluated in cognitive diagnosis and computerized adaptive testing settings. (
For LearnLoop, I would extend it into something closer to a **Diagnostic-EduEmbed** with additional entity roles:

[  
{  
\text{learner},  
\text{item},  
\text{concept},  
\text{facet},  
\text{misconception},  
\text{response trace},  
\text{probe},  
\text{repair}  
}.  
]

Instead of one generic item embedding, represent an item as approximately factorized components:

[  
v_e =  
[  
v_e^{\text{content}},  
v_e^{\text{facet}},  
v_e^{\text{operation}},  
v_e^{\text{representation}},  
v_e^{\text{misconception sensitivity}},  
v_e^{\text{difficulty}},  
v_e^{\text{transfer}}  
].  
]

Then item retrieval can be conditioned on the purpose:

- Same concept, different representation.
    
- Same facet, different surface language.
    
- Adjacent prerequisite facet.
    
- Same misconception sensitivity.
    
- Same operation but different concept.
    
- Contrastive item that changes exactly one relation.
    
- Near-transfer versus far-transfer audit.
    

### Why raw semantic similarity is insufficient

Two questions can be semantically similar while testing exactly the same ambiguous combination of facets. Asking both may produce two correlated failures without explaining either.

Conversely, a question that looks semantically dissimilar may be the best diagnostic witness because it isolates a prerequisite operation.

For example:

- Original question: apply the chain rule in a neural-network derivative.
    
- Semantically similar item: another neural-network derivative.
    
- More diagnostic item: differentiate (f(g(x))) in a minimal symbolic setting.
    
- Even more diagnostic contrast: distinguish (f'(g(x))) from (f'(g(x))g'(x)).
    

The retrieval pipeline should therefore be:

[  
\text{semantic/graph retrieval}  
\rightarrow  
\text{facet filtering}  
\rightarrow  
\text{hypothesis discrimination scoring}  
\rightarrow  
\text{cost-to-go reranking}.  
]

EduEmbed can help with the first two stages. The final score should depend on the learner posterior and predicted probe outcomes.

### Training objectives

Useful positives and hard negatives would include:

**Positive pairs**

- Different surface questions sensitive to the same misconception.
    
- Responses displaying the same reasoning error across domains.
    
- Repairs that work for the same structured hypothesis.
    
- Transfer items requiring the same facet.
    

**Hard negatives**

- Semantically similar questions testing different operations.
    
- Same concept but different misconception sensitivity.
    
- Same final wrong answer arising from different reasoning.
    
- Same vocabulary but different prerequisite structure.
    
- Same item answered incorrectly due to a slip versus a stable misconception.
    

This would move the embedding space away from “questions about similar topics” toward “questions that provide similar evidence about latent cognitive state.”

---

# 7. The LearnLoop version of capability-aware planning

Suppose the credible hypothesis set is

[  
H_t={h_1,\ldots,h_m,h_{\text{other}}}.  
]

For each pair (h_i,h_j), first ask whether the distinction matters:

[  
A_\epsilon(h_i)\cap A_\epsilon(h_j)  
\neq\varnothing.  
]

If they have a common acceptable repair, distinguishing them is low priority.

Define the unresolved, repair-relevant pairs:

[  
U_t=  
\left{  
(i,j):  
A_\epsilon(h_i)\cap A_\epsilon(h_j)=\varnothing  
\right}.  
]

A probe (e) distinguishes a pair if its predicted response distributions differ sufficiently:

[  
D!\left(  
P(o\mid h_i,e),  
P(o\mid h_j,e)  
\right)  
\geq \eta,  
]

where (D) could be KL divergence, Jensen–Shannon divergence, expected log Bayes factor, or expected reduction in repair regret.

A system capability (k) unlocks a probe family (E(k)). The capability planner asks:

> What is the least costly capability subgraph that unlocks enough probes to resolve the repair-relevant hypothesis pairs?

This is the LearnLoop analogue of the paper’s

[  
h_{\mathrm{cap}}.  
]

Conceptually:

# [  
h_{\mathrm{cap}}(s)

\min  
\left{  
\text{cost of capability builds that cover unresolved repair distinctions}  
\right}.  
]

For a simple chain:

[  
\text{canonical source}  
\rightarrow  
\text{facet graph}  
\rightarrow  
\text{executable hypotheses}  
\rightarrow  
\text{validated discriminator},  
]

the cost is just the remaining chain cost.

For a large capability hypergraph, it becomes closer to a weighted set-cover or directed-Steiner problem, which is also consistent with the complexity caveat discussed in the paper. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

## The experimentation term

Once the appropriate probe family is available, LearnLoop still has to estimate how much learner interaction is needed.

A practical multiclass analogue is:

[  
h_{\mathrm{diag}}(s)  
\approx  
\max_{(i,j)\in U_t}  
\frac{  
[\ell^*_{ij}-|\ell_{ij}(s)|]_+  
}{  
\max_{e\text{ reachable}}  
D_{ij}(e)/c(e)  
},  
]

where:

- (\ell_{ij}(s)) is current log posterior odds between (h_i) and (h_j);
    
- (\ell^*_{ij}) is the decision-confidence threshold;
    
- (D_{ij}(e)) is the expected discrimination supplied by probe (e);
    
- (c(e)) is learner burden.
    

This should initially be treated as a heuristic rather than a proven lower bound. The paper itself notes that its experimentation lower-bound guarantee is clean in its binary witness but need not extend to general adaptive experimental design. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

## Compare routes rather than always building

The route-aware heuristic should compare at least three possibilities:

# [  
\widehat C(s)

\min  
\begin{cases}  
C_{\text{repair-now}}(s),\  
C_{\text{direct-probes}}(s),\  
h_{\mathrm{cap}}(s)+h_{\mathrm{targeted-probes}}(s).  
\end{cases}  
]

This is crucial.

Sometimes one existing question is sufficient. Sometimes a tiny repair is safe across all hypotheses. Sometimes it is worth spending computation to construct a precision probe. The paper similarly compares a build-then-resolve route with a direct route so that its planner does not construct unnecessary capabilities when the target is already cheaply observable. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

---

# 8. Optimize for repair risk, not merely hypothesis entropy

A pure EIG objective might ask the question that most reduces uncertainty over the full hypothesis set. But the most informative question is not necessarily the question that most quickly identifies the correct repair.

Suppose the posterior is:

[  
\begin{aligned}  
P(h_1)&=0.30,\  
P(h_2)&=0.25,\  
P(h_3)&=0.20,\  
P(h_4)&=0.15,\  
P(h_{\text{other}})&=0.10.  
\end{aligned}  
]

If (h_1,h_2,h_3) all require the same repair, distinguishing among them may generate substantial information while producing zero decision value.

Define repair risk:

# [  
R(B)

\min_{a\in A_{\text{safe}}}  
\sum_h B(h)L(h,a).  
]

Then value a probe by expected reduction in repair risk:

# [  
V(e;B)

## R(B)

## \mathbb E_o[R(B_{e,o})]

\lambda_T c(e).  
]

This should remain part of LearnLoop. The capability-aware paper adds the warning that even this one-step value can undervalue a build action whose benefit only appears after several later actions.

So the planner needs both:

1. **Decision-relevant value of observations**, and
    
2. **Value of changing the future action set**.
    

That produces:

# [  
Q(a;s)

c(a)  
+  
\mathbb E_{o}  
\left[  
\widehat V(s')  
\right],  
]

where (\widehat V) includes the future cost of diagnosis, repair, and audit—not just immediate entropy reduction.

---

# 9. Mapping the “jagged boundary of understanding”

The latent state should not be a single mastery scalar. It should be a posterior over a structured graph whose dimensions include:

- Concept.
    
- Facet.
    
- Operation.
    
- Prerequisite.
    
- Representation.
    
- Context.
    
- Transfer distance.
    
- Misconception relation.
    
- Strategy.
    
- Confidence and execution noise.
    

For example, a learner might:

- understand vector rotation geometrically;
    
- manipulate rotation matrices correctly;
    
- forget that transpose equals inverse for orthogonal matrices;
    
- know Euler’s formula;
    
- fail to connect complex multiplication to relative positional encoding;
    
- succeed when given equations but fail when reasoning verbally.
    

That is a jagged boundary.

A concept graph can be used to propose boundary probes at:

- the parent immediately above an uncertain node;
    
- the child immediately below it;
    
- a sibling that separates two confusions;
    
- the same facet in another representation;
    
- the same operation in a different surface context;
    
- a transfer item one graph edge beyond the current boundary.
    

But the graph should not by itself decide which probe to ask. The graph proposes reachable distinctions; the belief and cost-to-go planner decide whether they are worth measuring.

---

# 10. A concrete RoPE example

Suppose the learner is asked why the RoPE attention score depends on relative position and writes something implying

[  
R(m\theta)^TR(n\theta)=R((m+n)\theta).  
]

The LLM grader proposes:

> “The learner may understand rotations generally but may be treating the transpose as another positive rotation.”

That creates an initial ensemble:

[  
\begin{aligned}  
h_1 &: \text{isolated sign slip},\  
h_2 &: \text{does not know }R(a)^T=R(-a),\  
h_3 &: \text{incorrect rotation-composition rule},\  
h_4 &: \text{algebra is correct but relative-position interpretation is missing},\  
h_5 &: \text{Euler/complex-number prerequisite gap},\  
h_{\text{other}} &: \text{unmodeled explanation}.  
\end{aligned}  
]

## The myopic direct route

LearnLoop retrieves another semantically similar RoPE explanation question.

That question may have positive EIG, but the learner can make the same composite mistake again. It weakly distinguishes the hypotheses and imposes another cognitively expensive response.

## The constructive route

LearnLoop performs system-side builds:

[  
b_1:  
\text{retrieve and decompose the canonical derivation}  
]

[  
b_2:  
\text{compile predicted signatures for }h_1,\ldots,h_5  
]

[  
b_3:  
\text{generate and validate a one-step symbolic discriminator}.  
]

These actions provide little new evidence about the learner, but they unlock a better probe:

> Complete only the missing transformation:
> 
> # [  
> (R(m\theta)q)^T(R(n\theta)k)
> 
> q^T\underline{\hspace{2cm}}k.  
> ]
> 
> Is the missing term (R((n-m)\theta)), (R((m-n)\theta)), or (R((m+n)\theta))? Explain only the transpose/composition step.

This probe separates:

- transpose/inverse understanding;
    
- composition understanding;
    
- sign slip;
    
- downstream interpretation.
    

If the learner performs the algebra correctly but still cannot explain relative position, LearnLoop does not backtrack to Euler’s formula. It gives a minimal geometric interpretation repair.

If the learner cannot derive (R(a)^T=R(-a)), the repair focuses there.

If the learner knows the identity and self-corrects immediately with high confidence, LearnLoop may classify the event as execution noise and provide no substantive repair.

The audit then changes symbols or representation:

[  
R(i\theta)^TR(j\theta)  
]

or asks why shifting both positions by (c) leaves the score unchanged. That tests whether the repair generalized beyond memorizing (n-m).

---

# 11. How this fits into the complete LearnLoop episode

## Trigger

A diagnostic episode starts after:

- incorrect response;
    
- unexpectedly correct response;
    
- high surprisal under the current learner model;
    
- contradiction with previous mastery;
    
- unusual rationale;
    
- confidence–performance mismatch;
    
- delayed-audit failure.
    

## Initial belief update

The grader extracts evidence and proposes multiple candidate explanations. Historical responses on the same and adjacent facets provide priors and likelihood evidence.

## Repair-equivalence check

Before asking anything else, determine whether credible hypotheses share a safe minimal repair.

If yes, repair immediately.

## Capability check

Ask whether currently available probes can distinguish the remaining repair-relevant hypotheses cheaply.

If not, consider constructive actions:

- build facet decomposition;
    
- retrieve canonical examples;
    
- compile hypotheses;
    
- construct contrastive probe;
    
- establish process-level response channel.
    

## Route planning

Compare:

- repair now;
    
- ask an available direct probe;
    
- build then ask a precision probe;
    
- postpone to a delayed audit;
    
- take no action.
    

## Probe and posterior update

Collect the full observation:

[  
o_t=  
(  
\text{correctness},  
\text{answer},  
\text{rationale},  
\text{step trace},  
\text{confidence},  
\text{latency},  
\text{hints},  
\text{edits}  
).  
]

Update the executable hypothesis ensemble, retaining a diversity floor and (h_{\text{other}}).

## Minimal repair

Choose:

# [  
a^*

\arg\min_a  
\sum_h B_t(h)  
\left[  
\text{learner time}  
+  
\lambda_{\text{cold}}  
P(\text{delayed failure}\mid h,a)  
+  
\lambda_{\text{harm}}  
\operatorname{Harm}(h,a)  
\right].  
]

## Audit and learning

Immediate and delayed audits evaluate:

- retention;
    
- near transfer;
    
- representation transfer;
    
- whether the diagnosis was right;
    
- whether the repair was effective;
    
- whether the capability/probe prediction model was calibrated.
    

These outcomes update not only the learner model but also the reusable system models:

[  
P(o\mid h,e),  
\qquad  
P(z'\mid z,a),  
\qquad  
c(a),  
\qquad  
h_{\text{cost-to-go}}.  
]

---

# 12. Two timescales of capability construction

LearnLoop has an advantage over the paper’s single-episode setup: many diagnostic capabilities can be reused.

## Offline/global construction

Build once and reuse across learners:

- canonical concept/facet graph;
    
- misconception library;
    
- validated item bank;
    
- contrastive probe templates;
    
- rubrics;
    
- item–misconception likelihood models;
    
- repair-effect models;
    
- delayed-audit bank.
    

## Online/local construction

Build for the current learner and anomaly:

- personalize the hypothesis set;
    
- retrieve relevant history;
    
- construct one targeted probe;
    
- choose response modality;
    
- compile a local rubric;
    
- estimate likely repair outcomes.
    

The planner should price reusable capabilities differently. A costly capability may not be justified for one learner but may be highly valuable when amortized over thousands of future episodes.

Eventually, the system can estimate:

# [  
\text{net capability value}

## \text{current episode savings}  
+  
\text{expected future reuse value}

\text{construction cost}.  
]

That goes beyond the paper’s within-episode shortest-path model but follows the same topological principle.

---

# 13. What I would implement first

A full stochastic CG-Plan implementation is not necessary for the first version. The highest-value approximation would be a route-aware controller with four choices:

[  
{  
\text{repair now},  
\text{ask existing probe},  
\text{construct targeted probe},  
\text{stop/defer}  
}.  
]

The minimum viable architecture would contain:

1. **Structured hypothesis compiler.** Convert grader prose into facet-grounded hypotheses with predicted response signatures, repair sets, and falsifiers.
    
2. **Repair-equivalence clustering.** Stop diagnosing when remaining distinctions do not alter the intervention.
    
3. **Capability registry.** Represent what probe generators, rubrics, modalities, sources, and calibrations are currently available.
    
4. **Facet-conditioned retrieval.** Use a modified EduEmbed plus graph constraints to retrieve candidate probes.
    
5. **Decision-relevant reranking.** Rank candidates by expected reduction in repair risk per learner cost, rather than generic semantic similarity.
    
6. **Build-versus-direct comparison.** Estimate whether constructing a tailored discriminator is cheaper than asking several weak probes.
    
7. **Persistent audits.** Use delayed outcomes to calibrate hypothesis likelihoods, repair effects, and the cost-to-go model.
    

The planner can initially use a shallow rule such as

# [  
a_t

\arg\min_a  
\left[  
c(a)+  
h_{\mathrm{cap}}(s_{t+1})  
+  
h_{\mathrm{diag}}(s_{t+1})  
+  
h_{\mathrm{repair}}(s_{t+1})  
+  
h_{\mathrm{audit}}(s_{t+1})  
\right]  
]

and replan after every observation.

Over time, the heuristic can be learned from hindsight-labeled episodes while retaining explicit capability-graph features. The paper itself identifies hindsight-trained cost-to-go and learned capability structures as natural extensions, while warning that its formal guarantees depend on a known capability graph and idealized action models. ([arXiv](https://arxiv.org/html/2608.05085v1 "Capability-Gated Planning: Cost-to-Goal Discovery and theLimits of Myopic Experiment Selection"))

## The central LearnLoop interpretation

The paper’s lesson for LearnLoop is not merely:

> “Plan more than one question ahead.”

It is:

> **Sometimes the best next action is not a question or a repair. It is to build the representation, probe, rubric, response channel, or executable hypothesis model that makes the right question possible.**

And the complementary lesson is:

> **Do not identify the learner more precisely than is necessary to choose a safe minimal repair.**

Those two principles combine into a particularly natural LearnLoop policy:

[  
\boxed{  
\text{Construct only the diagnostic capabilities required to distinguish hypotheses that imply materially different repairs.}  
}  
]

That gives you a route from free-form LLM interpretations to executable hypotheses, from executable hypotheses to targeted probes, and from targeted probes to minimal, decision-relevant repair without turning the tutoring interaction into an unnecessarily long adaptive test.