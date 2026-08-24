# Decision-Sufficient Causal Diagnosis and Repair

## Robust Experimental Design, State-Changing Queries, and Bounded-Regret Intervention Learning for LearnLoop

LearnLoop should not be framed primarily as a better knowledge-tracing model or adaptive item scheduler. Its strongest research opportunity is a more general problem:

> **How should an intelligent system diagnose and repair a latent human state when experiments are costly, observations are noisy and open-world, the experiments themselves may change the state being diagnosed, and only distinctions that change the downstream action are worth resolving?**

The central methodological principle is **decision sufficiency**. The system should not attempt to identify the learner's complete latent state. It should acquire only the information required to choose a safe, low-regret intervention.

This yields a research program built around four linked contributions:

1. **Decision-Sufficient Robust Experimental Design (DSED):** compress diagnostic uncertainty into the low-dimensional subspace that can alter downstream actions and select probes using robust expected decision value rather than entropy or hypothesis-identification accuracy.
    
2. **Open-world causal diagnosis with generated experiments:** represent learner errors as provisional, executable causal mechanisms, generate diagnostic probes on demand, and abstain or expand the hypothesis space when the current model is inadequate.
    
3. **Causal learning under robust equipoise:** when several repairs are already certified as near-optimal, randomize among them at bounded regret to collect genuine causal evidence about intervention effectiveness.
    
4. **Decision-predictive state representations for state-changing experiments:** generalize the one-step projection to situations where asking a question also teaches, anchors, fatigues, contaminates, or otherwise changes the latent state.
    

The same causal-repair kernel can also be applied to **LLM context contamination**, providing a high-throughput experimental environment in which causal states can be planted, context interventions replayed, and outcomes formally verified.

The goal is not one oversized paper containing everything. The research program should produce a focused first paper around decision-sufficient robust diagnosis, followed by causal-intervention and state-changing-query extensions.

---

# 1. The underlying LearnLoop problem

After observing a learner failure, LearnLoop maintains a provisional hypothesis set

[  
H_t={h_1,\ldots,h_m,h_{\mathrm{other}}}.  
]

Examples include:

- a missing prerequisite;
    
- a specific procedural misconception;
    
- inappropriate method selection;
    
- notation misinterpretation;
    
- a transient execution error;
    
- an item or grading problem;
    
- or an unenumerated cause (h_{\mathrm{other}}).
    

These hypotheses are **episode-local causal explanations**, not permanent learner types.

This distinction is important. LearnLoop already separates canonical knowledge facets from item-local errors, mechanisms, causal hypotheses, repair classes, and durable learner-state projections; a single response is explicitly insufficient for automatically creating a permanent misconception.

For each feasible repair (a\in A), define

[  
L(h,a)  
]

as the expected learner-minute loss if hypothesis (h) is true and action (a) is chosen.

Non-time harms are not converted into arbitrary scalar weights. Safety, learner intent, answer-reveal restrictions, false-certification limits, and similar requirements define the feasible action set first:

# [  
A_{\mathrm{feas}}(b)

{a:\text{all hard constraints are satisfied}}.  
]

Among feasible actions, learner time is the principal numeraire.

The current decision risk is

# [  
R(b)

\min_{a\in A_{\mathrm{feas}}}  
\sum_hb(h)L(h,a).  
]

The fundamental question is therefore not

> Which hypothesis is true?

but

> **Would knowing more change the intervention enough to justify asking the learner another question?**

---

# 2. Decision-Sufficient Experimental Design

## 2.1 One-step decision projection

Suppose diagnostic probe (q) produces response category

[  
e\in E  
]

through channel

[  
M_q(e\mid h).  
]

Choose an arbitrary baseline action (a_0) and define the centered loss matrix

# [  
D(h,a)

L(h,a)-L(h,a_0).  
]

For response (e), define the unnormalized hypothesis mass

# [  
x_{he}

b(h)M_q(e\mid h),  
]

and the **decision projection**

# [  
z_e(a)

\sum_hx_{he}D(h,a).  
]

The expected post-probe risk is

# [  
G(M_q)

b^\top L_{\cdot,a_0}  
+  
\sum_e\min_a z_e(a).  
]

Therefore the complete response channel is unnecessary for evaluating the current downstream decision.

The relevant object is

[  
Z_q=(z_e)_{e\in E}.  
]

### Decision-sufficiency theorem

For fixed

[  
(b,L,A_{\mathrm{feas}}),  
]

two response channels (M) and (M') that produce the same (Z) have exactly the same one-step expected downstream decision value.

Thus uncertainty directions in the channel that lie in the null space of the loss projection are irrelevant to the current intervention decision.

---

## 2.2 Dimension bound

Let

[  
r=\operatorname{rank}(D).  
]

Since one centered action column is zero,

[  
r\le |A|-1.  
]

Every (z_e) lies in an (r)-dimensional subspace.

Furthermore,

[  
\sum_ez_e=b^\top D  
]

is fixed regardless of the probe channel.

Therefore the affine dimension of the decision-relevant experiment representation is at most

[  
(|E|-1)r  
\le  
(|E|-1)(|A|-1).  
]

This is a central structural observation.

The dimensionality governing diagnostic decisions depends primarily on:

- the number of meaningfully different repair actions;
    
- and the number of decision-relevant response categories;
    

not on the number of semantic causal hypotheses the LLM can enumerate.

This makes open-world semantic reasoning compatible with low-dimensional decision making.

---

# 3. Robust EVSI in projected space

Ordinary EVSI is

# [  
V(q;b)

## R(b)

## G(M_q)

c(q),  
]

where (c(q)) is the learner burden of administering the probe.

The response channel is uncertain, so LearnLoop should operate over an ambiguity set.

Instead of robustifying the entire high-dimensional channel whenever possible, construct an ambiguity set directly over the decision projection:

[  
Z_q\in\mathcal Z_q.  
]

The robust lower decision value is

# [  
\underline V(q;b)

## R(b)

## \sup_{Z\in\mathcal Z_q}  
G(Z)

c(q).  
]

Nature maximizes future decision risk, equivalently choosing the plausible experiment realization with the smallest decision benefit.

Probe only when

[  
\underline V(q;b)>0.  
]

---

## 3.1 Exact versus conservative projected ambiguity sets

The exact feasible projected set can be written as

# [  
\mathcal Z_q

\left{  
Z:  
\exists X\ge0,;  
X\mathbf 1=b,;  
z_e=X_{\cdot e}^{\top}D,;  
X/b\in\mathcal P_q  
\right}.  
]

A simpler set defined only through:

- the decision subspace;
    
- nonnegativity/cone restrictions;
    
- the barycenter constraint;
    
- and calibrated uncertainty bounds
    

may contain projected points that no physical response channel can generate.

That produces an **outer relaxation**.

Because the adversary maximizes future risk, an outer relaxation is conservative: it may suppress some worthwhile probes, but it cannot create false robust value merely by enlarging the adversary's feasible set.

---

## 3.2 Convex hulls of sampled channels

The natural generative setting contains multiple uncertain components:

[  
P(\text{learner signature}\mid h,q),  
]

[  
P(\text{coder output}\mid\text{true signature}),  
]

off-task rates, slips, parser failures, and simulator uncertainty.

Rather than optimizing jointly over bilinear learner and coder parameters, draw joint samples

[  
(\phi^{(i)},\psi^{(i)})  
]

from the hierarchical model and numerically construct complete channels

[  
M^{(i)}.  
]

Then use

# [  
\mathcal P_q

\operatorname{conv}  
{M^{(1)},\ldots,M^{(N)}}.  
]

Crucially, robust value is **not** obtained by simply taking the minimum EVSI over the sampled channels.

The expected future risk

[  
G(M)  
]

is concave in the response channel. Its maximum over a convex hull can occur at an interior mixture.

A simple example is a mixture of:

- a channel that perfectly reports the hypothesis;
    
- and a channel that perfectly swaps the hypothesis labels.
    

Each vertex is individually perfectly informative, while their 50/50 mixture can become completely uninformative.

Therefore the robust adversary must optimize over mixture weights:

[  
\begin{aligned}  
\max_{\alpha,t}\quad&  
\sum_et_e\  
\text{s.t.}\quad&  
t_e  
\le  
\sum_hb(h)  
\left[  
\sum_i\alpha_iM^{(i)}(e\mid h)  
\right]  
L(h,a),  
\quad\forall e,a,\  
&\alpha\in\Delta_N.  
\end{aligned}  
]

This remains a small LP for LearnLoop-sized hypothesis, response, and action spaces.

LearnLoop's current robust-EVSI implementation already evaluates finite likelihood ensembles and abstains when downstream action recommendations are unstable, but currently uses ensemble quantiles and heuristic perturbations rather than a statistically calibrated convex ambiguity model.

---

# 4. Decision-collapse and cheap stopping certificates

Before solving any robust program, LearnLoop should test whether further diagnosis could possibly justify its cost.

For hypothesis (h), define regret

# [  
\rho_h(a)

L(h,a)-\min_{a'}L(h,a').  
]

Define the (\epsilon)-optimal actions

# [  
A_\epsilon(h)

{a:\rho_h(a)\le\epsilon}.  
]

Let (C_\delta(b)) contain at least (1-\delta) of current belief mass.

If

[  
\bigcap_{h\in C_\delta(b)}A_\epsilon(h)\neq\varnothing,  
]

there exists an action that is within (\epsilon) of optimal for every plausible hypothesis.

If regret outside the plausible set is bounded by (L_{\max}), choosing this common action has expected regret bounded by

[  
(1-\delta)\epsilon+\delta L_{\max}  
\le  
\epsilon+\delta L_{\max}.  
]

Therefore

[  
\operatorname{EVPI}(b)  
\le  
\epsilon+\delta L_{\max}.  
]

No diagnostic question can be worth more than perfect information.

Hence any probe satisfying

[  
c(q)>\epsilon+\delta L_{\max}  
]

is dominated without evaluating its response model.

This produces an efficient decision sequence:

[  
\text{hard constraints}  
\rightarrow  
\text{common-repair certificate}  
\rightarrow  
\text{EVPI upper bound}  
\rightarrow  
\text{robust EVSI}.  
]

This formalizes a central LearnLoop product principle:

> If every plausible explanation needs essentially the same small repair, do not interrogate the learner merely to resolve the explanation.

---

# 5. Cost-adjusted decision-collapse radius

A response channel need not become completely hypothesis-independent before its decision value vanishes.

Suppose the ambiguity family expands with radius (r):

[  
\mathcal Z_q(r).  
]

Define the **cost-adjusted collapse radius**

# [  
r_c^\dagger(q;b,L)

\inf  
\left{  
r:  
\sup_{Z\in\mathcal Z_q(r)}  
G(Z)  
\ge  
R(b)-c(q)  
\right}.  
]

Interpretation:

- below (r_c^\dagger), the probe remains robustly worth its learner cost;
    
- at (r_c^\dagger), plausible measurement-model uncertainty can erase the entire net decision benefit;
    
- when (c(q)=0), this reduces to a pure decision-collapse threshold.
    

This quantity is superior to asking when all hypothesis-conditioned likelihood sets overlap.

Decision collapse occurs whenever plausible post-response beliefs can all remain inside a single linear action region of Bayes risk, even if the response still contains considerable information about the underlying hypothesis.

The radius is therefore:

- belief-dependent;
    
- action-dependent;
    
- loss-dependent;
    
- and decision-state-dependent.
    

This removes the need for arbitrary statements such as “we need (n) observations for every hypothesis × probe-family cell.”

Data are valuable where they tighten the ambiguity set around **binding action boundaries**.

---

# 6. Regret-profile covers instead of hypothesis quotients

Approximate similarity such as

[  
d(h,h')\le\epsilon  
]

does not define a transitive equivalence relation.

Therefore LearnLoop should not quotient the semantic hypothesis space by an approximate similarity relation.

Instead define the decision metric

# [  
d_D(h,h')

|\rho_h-\rho_{h'}|_\infty.  
]

This automatically removes hypothesis-specific additive constants that do not affect action preference.

Construct an approximate **decision cover**.

If a subset (S) has

[  
\operatorname{diam}_{d_D}(S)\le\epsilon,  
]

then for any representative (h_0\in S),

[  
a^\star(h_0)  
\in  
\bigcap_{h\in S}A_\epsilon(h).  
]

Thus every diameter-(\epsilon) cover cell has at least one common (\epsilon)-optimal action.

A greedy (\epsilon/2)-net provides a tractable approximation.

The semantic hypotheses remain separately persisted. Decision compression affects only current policy computation.

This matters because two causes that currently imply the same repair may still differ in:

- later verification;
    
- recurrence interpretation;
    
- contextual activation;
    
- future actions;
    
- or evidence that would contradict them.
    

The rule is:

> **Persist causal distinctions broadly; grant decision authority only when they matter.**

---

# 7. Open-world diagnosis

(H_{\mathrm{other}}) should not be assigned one fabricated precise loss row.

Instead represent unknown-cause intervention regret by

[  
\rho_{\mathrm{other}}  
\in  
\mathcal R_{\mathrm{other}},  
]

a set of plausible regret profiles.

A conservative fallback or escalation action (a_\perp) should satisfy a known bound such as

[  
\sup_{\rho\in\mathcal R_{\mathrm{other}}}  
\rho(a_\perp)\le\eta.  
]

As open-world concern rises, the robust decision naturally shifts toward:

- bounded repairs;
    
- passive verification;
    
- escalation;
    
- or abstention.
    

Unknown-cause evidence should remain conceptually separate from posterior mass unless a calibrated model has actually been trained to estimate

[  
P(\text{enumerated hypothesis set is incomplete}\mid x).  
]

A conformal residual, e-process, or predictive misspecification statistic provides an **open-set alarm**, not automatically a Bayesian probability.

When the alarm fires:

1. freeze the current evidence;
    
2. ask the LLM to propose new semantic causes;
    
3. reject pure paraphrases through predictive and decision-profile checks;
    
4. preserve the proposals as provisional hypotheses;
    
5. generate prospective discriminating predictions;
    
6. give them decision authority only if they change the action;
    
7. require new evidence before promotion.
    

The component proposing a new cause must not confirm that cause itself, preserving LearnLoop's producer–confirmer separation.

---

# 8. Executable mal-procedures rather than a Q-matrix diagnosis model

LearnLoop's local causal hypotheses are often better represented as executable behavioral programs than binary skill vectors.

Examples include:

- retain only one sign branch;
    
- distribute a sign incorrectly;
    
- apply an affine rule outside its domain;
    
- confuse implication with converse;
    
- stop after finding one valid solution;
    
- choose a familiar but inapplicable method.
    

For hypothesis (h) and candidate item (q), execute the corresponding mal-procedure:

[  
\operatorname{trace}(h,q).  
]

If two decision-relevant hypotheses produce identical traces on (q), the item has no structural power to distinguish them and should be rejected before learner administration.

This gives a zero-learner-cost probe filter:

[  
\text{candidate generation}  
\rightarrow  
\text{executable divergence}  
\rightarrow  
\text{noise simulation}  
\rightarrow  
\text{coder uncertainty}  
\rightarrow  
\text{robust EVSI}.  
]

The canonical facet × capability model remains necessary for certification and knowledge measurement. Executable error programs are an episode-local causal layer, not a replacement for LearnLoop's canonical knowledge representation.

---

# 9. Generated experiments as inverse decision design

A generative item space creates a stronger opportunity than selecting from a fixed item pool.

Instead of prompting an LLM to:

> “generate an informative question,”

LearnLoop can identify the current **binding action boundary**.

For actions (a) and (a'), define the loss contrast

# [  
d_{a,a'}(h)

L(h,a)-L(h,a').  
]

The system identifies hypothesis pairs lying on meaningfully different sides of this boundary and asks the generator for an item expected to make those mechanisms produce different observable traces.

The pipeline becomes:

1. Identify the nearest or binding action boundary.
    
2. Rank hypothesis pairs by posterior mass and regret from confusing them.
    
3. Generate several candidate probes targeted at those pairs.
    
4. Check mathematical and contract validity.
    
5. Execute mal-procedures and reject candidates without structural divergence.
    
6. Simulate human-response noise using planted personas.
    
7. project each candidate to (Z)-space;
    
8. construct its ambiguity set;
    
9. score robust decision value against the entire hypothesis set;
    
10. administer the highest-value candidate only if robust net value is positive.
    

This is **inverse experimental design in decision space**.

The system tries to realize a desired low-dimensional projected experiment rather than merely generating semantically different questions.

---

# 10. Planted personas: admission and prior, not ground truth

LLM personas are useful because a newly generated item has no real learner-response history.

Their safest immediate roles are:

- reject obviously nondiscriminating probes;
    
- stress-test response categories;
    
- simulate noise around executable error traces;
    
- identify missing rubric categories;
    
- rank candidate probes approximately;
    
- and provide a broad prior over novel probe-family behavior.
    

They should not initially provide authoritative

[  
P(e\mid h,q)  
]

for live learner-state updates.

Synthetic channels should be compared prospectively with real response distributions. The relevant fidelity requirement is not perfect human linguistic imitation but **decision-projected fidelity**:

[  
Z_{\mathrm{sim}}  
\approx  
Z_{\mathrm{real}}.  
]

Real telemetry gradually shrinks the simulator-derived ambiguity.

This preserves LearnLoop's current authority ladder, in which simulated response behavior may support screening and routing before it earns real-learner likelihood authority.

---

# 11. Hierarchical calibration and telemetry

Generated items make item-specific calibration impossible at creation time.

Response models should therefore pool at the **probe-family level**.

A probe contract might contain:

# [  
\text{family}

(  
\text{target operation},  
\text{capability},  
\text{response mode},  
\text{representation},  
\text{surface regime}  
).  
]

The generator's family label is itself a proposal and must pass contract validation.

A hierarchical response-signature model can estimate

[  
P(z\mid h,\text{family})  
]

with shrunk item-level deviations.

The raw telemetry should preserve at minimum:

- learner's first unassisted response before hints;
    
- complete exposure/hint/answer-reveal trace;
    
- raw free response;
    
- graded criteria and checkpoints;
    
- first divergence;
    
- response confidence before feedback;
    
- latency normalized by learner and item family;
    
- edits;
    
- hint requests;
    
- retries;
    
- session position;
    
- prior exposures;
    
- immediate repair result;
    
- delayed independent verification;
    
- item and model versions.
    

Every decision should additionally log:

[  
b_t,  
]

the complete candidate set,

[  
A_{\mathrm{feas},t},  
]

all exclusion reasons,

[  
\mathcal Z_{q,t},  
]

robust values,

[  
\pi_t(a),  
]

and all relevant model, loss, and ambiguity-set versions.

A random small audit stream can receive deeper human adjudication, but these labels should be set-valued:

[  
{  
\text{supported},  
\text{contradicted},  
\text{underdetermined}  
},  
]

rather than pretending intensive review produces an infallible oracle label for the learner's internal cause.

---

# 12. Machine uncertainty versus learner uncertainty

The same decision-value framework should choose **which source of information** is worth acquiring.

LearnLoop faces at least four distinct uncertainty types.

|Uncertainty|Unknown|Appropriate information source|
|---|---|---|
|Causal-state uncertainty|Why did the learner fail?|Learner probe|
|Measurement uncertainty|Is the probe/parser/grader reliable?|Machine audit or human coding|
|Intervention uncertainty|Which safe repair causes cold success?|Controlled randomization|
|Structural uncertainty|Is the current hypothesis set incomplete?|Open-world expansion / escalation|

This yields a source-aware controller:

[  
\text{cause uncertainty}  
\rightarrow  
\text{probe learner},  
]

[  
\text{instrument uncertainty}  
\rightarrow  
\text{audit machine},  
]

[  
\text{repair uncertainty}  
\rightarrow  
\text{randomize under equipoise},  
]

[  
\text{model misspecification}  
\rightarrow  
\text{expand or abstain}.  
]

This formalizes LearnLoop's existing rule that machine-resident uncertainty—grader instability, missing contracts, symbolic ambiguity the machine could resolve—must not be paid for with learner effort.

---

# 13. Stability regions and value of machine information

Uncertainty in intervention-effect parameters may matter more than uncertainty in the response channel.

For model parameters (\theta), define the action stability region

# [  
\Theta^\star(a)

{  
\theta:  
a\in\arg\min_{a'}R_\theta(a')  
}.  
]

The **stability radius**

# [  
s^\star

\min_{\theta\notin\Theta^\star(a)}  
d(\theta,\hat\theta)  
]

measures how much parameter movement is required to change the chosen action.

This tells the system:

- whether the current decision is robust;
    
- which parameter is closest to flipping it;
    
- and what measurement would be useful.
    

Perfect-information measures such as EVPPI can screen uncertain parameter blocks:

> If perfect knowledge of a parameter would not change the decision enough to matter, no finite audit of that parameter can be worthwhile.

For a concrete audit (m), however, calculate its actual EVSI:

[  
\operatorname{EVSI}_{\mathrm{audit}}(m).  
]

Thus learner probing and machine auditing become two forms of information acquisition about different uncertain objects.

---

# 14. Causal learning under robust equipoise

Once several repairs are already certified as near-optimal, LearnLoop can safely collect randomized causal evidence.

Suppose each hypothesis has an uncertainty set over regret profiles

[  
\rho_h\in\mathcal R_h.  
]

Define the robust acceptable action set

# [  
S_t(\epsilon_{\mathrm{act}})

\left{  
a\in A_{\mathrm{feas},t}:  
\sup_{h\in C_t}  
\sup_{\rho\in\mathcal R_h}  
\rho(a)  
\le  
\epsilon_{\mathrm{act}}  
\right}.  
]

If

[  
|S_t|\ge2,  
]

several interventions are robustly near-optimal.

Any randomized policy supported on this set satisfies, on the uncertainty-coverage event,

[  
\operatorname{Regret}_t  
\le  
\epsilon_{\mathrm{act}}.  
]

If the confidence sets contain the true state/profile with probability (1-\delta), then a basic expected bound is

[  
\mathbb E[\operatorname{Regret}_t]  
\le  
\epsilon_{\mathrm{act}}  
+  
\delta L_{\max}.  
]

This creates **experimental equipoise from the same decision slack that already licensed acting**.

---

## 14.1 Separate acting and exploration tolerances

Use

[  
\epsilon_{\mathrm{explore}}  
\le  
\epsilon_{\mathrm{act}}.  
]

The first defines which actions are acceptable to serve.

The second defines how much of that accepted slack may be deliberately spent on causal identification.

Randomization probabilities can then optimize information about repair effectiveness subject to the regret constraint.

The objective can target

# [  
\eta(x,a)

P(  
\text{independent cold success}  
\mid  
do(a),x  
),  
]

rather than generic information about which action happens to be best today.

---

## 14.2 Local causal estimand

Randomization occurs only in states where both interventions are eligible.

Therefore the causal estimand must remain local:

# [  
\tau_\Delta(a,a')

\mathbb E[  
Y_{t+\Delta}(a)-Y_{t+\Delta}(a')  
\mid  
a,a'\in S_t  
].  
]

This is an eligibility-conditioned causal excursion effect.

Known adaptive propensities permit micro-randomized-trial or adaptively weighted causal estimation.

Do **not** extrapolate this effect to decisive states in which one treatment was not eligible.

Do not silently introduce forced exploration outside the robust equipoise set; doing so removes the per-learner regret guarantee and belongs in a separately consented research protocol.

LearnLoop already anticipates micro-randomization among near-equivalent safe decisions and requires logged propensities plus delayed cold outcomes before making intervention-effectiveness claims.

---

# 15. Causal claims and sequential evidence

LearnLoop should preserve three epistemic write types:

### Descriptive

> “The learner responded X to item Y under conditions Z.”

Immutable and freely persisted.

### Inferential

> “Cause (h) is currently supported.”

Persist as provisional, with bounded permitted uses.

### Causal

> “Intervention (a) performs better than (a') for eligible contexts of type (x).”

Requires randomized or otherwise defensible causal evidence.

Persistence and authority are separate.

A model-generated hypothesis may be stored for later comparison even if it currently has no policy authority.

Sequential e-processes or confidence sequences may eventually provide anytime-valid promotion criteria under adaptive probing, but this should initially be applied narrowly—such as confirming repeated fingerprint-distinct mechanism recurrence—rather than gating every ordinary evidence update.

Evidence before and after a state-changing intervention must remain segmented.

A successful repair does not retroactively prove the diagnosis. LearnLoop already treats delayed cold verification as evidence about learner capability and repair effectiveness separately from diagnosis support.

---

# 16. State-changing experiments

The one-step DSED model assumes the learner state is approximately fixed while the diagnostic response is generated.

Real tutoring violates this.

A question can:

- produce retrieval practice;
    
- reveal part of the solution;
    
- induce self-explanation;
    
- create doubt;
    
- anchor the learner;
    
- fatigue the learner;
    
- or partially repair the misconception.
    

The experiment is therefore both a **write** and a **read**.

---

# 17. Joint write–read kernel

Let

[  
K_u(h',e\mid h)  
]

be the joint controlled kernel:

# [  
K_u(h',e\mid h)

P(  
H_{t+1}=h',  
E_t=e  
\mid  
H_t=h,  
U_t=u  
).  
]

This captures both:

- the state change (h\rightarrow h');
    
- and the observation produced during that transition.
    

Given belief (b_t),

# [  
P(e\mid b_t,u)

\sum_{h,h'}b_t(h)K_u(h',e\mid h).  
]

After observing (e),

# [  
b_{t+1}(h')

\frac{  
\sum_hb_t(h)K_u(h',e\mid h)  
}{  
P(e\mid b_t,u)  
}.  
]

This joint formulation is necessary whenever the observed response is informative about which post-write state actually occurred.

Simply averaging the write transition before processing the response destroys this correlation and can lose decision value.

---

# 18. Exact write/read value decomposition

Let

# [  
\bar b_u(h')

\sum_{h,e}  
b(h)K_u(h',e\mid h)  
]

be the post-write belief before reading the observation.

Let (R_0) denote pre-write decision risk and (R_1) post-write decision risk.

Then the total value of interaction (u) decomposes exactly as

## [  
\begin{aligned}  
V(u;b)  
&=  
R_0(b)

## \sum_ep_u(e)R_1(b'_{u,e})

## c(u)\  
&=  
\underbrace{  
R_0(b)-R_1(\bar b_u)  
}_{\text{write value}}  
+  
\underbrace{  
R_1(\bar b_u)  
-\sum_ep_u(e)R_1(b'_{u,e})  
}_{\text{read value}}

c(u).  
\end{aligned}  
]

The read value is nonnegative by concavity of Bayes risk.

The write value can be:

- positive when asking the question itself teaches;
    
- zero for a state-preserving diagnostic;
    
- negative when the question confuses or fatigues;
    
- positive now but harmful to future diagnostic observability.
    

This is superior to treating all state movement as one unsigned “diagnostic disturbance.”

---

# 19. Timing semantics

Three interaction classes should be distinguished formally.

### Read before write

[  
h_t  
\rightarrow  
e_t  
\rightarrow  
\text{feedback}  
\rightarrow  
h_{t+1}.  
]

This is preferred when independent diagnostic evidence is needed.

Example:

> learner commits an answer → LearnLoop grades it → LearnLoop repairs.

### Write before read

[  
h_t  
\rightarrow  
\text{hint}  
\rightarrow  
h_{t+1}  
\rightarrow  
e_t.  
]

The observed success measures the supported post-hint state and cannot certify unaided capability.

### Entangled interaction

A multi-turn Socratic exchange continuously observes and alters the state.

This requires the full joint controlled model.

LearnLoop's existing contamination categories already distinguish pure diagnostic, instructional diagnostic, repair, and independent verification and forbid instructional interactions from silently producing certification evidence.

---

# 20. Sequential decision-predictive state representation

The most important theoretical extension is not that the local (Z_q) projection itself becomes Markov.

Instead, construct the smallest feature space containing the decision-loss features that is closed under every write–read operator.

For each control (u) and observation (e), let

[  
K_{u,e}  
]

be the (|H|\times|H|) sub-stochastic matrix with entries

# [  
K_{u,e}(h,h')

K_u(h',e\mid h).  
]

Let terminal loss vector (\ell_a\in\mathbb R^{|H|}) encode the cost of downstream action (a), and let (c_u) encode any state-dependent immediate control cost.

Initialize

# [  
\mathcal V_0

\operatorname{span}  
{  
\mathbf1,,  
\ell_a:a\in A,,  
c_u:u\in U  
}.  
]

Then repeatedly close the space under the controlled operators:

# [  
\mathcal V_{k+1}

\mathcal V_k  
+  
\operatorname{span}  
{  
K_{u,e}v:  
v\in\mathcal V_k,,  
u\in U,,  
e\in E  
}.  
]

Because the latent state space is finite, the sequence eventually stabilizes:

[  
\mathcal V_\star.  
]

Define

# [  
d_\star

\dim\mathcal V_\star.  
]

Call this the **decision-closure dimension**.

---

# 21. Sequential closure theorem

Let matrix (F) contain a basis for (\mathcal V_\star), with (\mathbf1) as its first column.

Closure implies that for every (u,e), there exists a low-dimensional matrix (B_{u,e}) such that

# [  
K_{u,e}F

FB_{u,e}.  
]

Define the compressed decision state

# [  
x_t

b_tF.  
]

Then

# [  
x_tB_{u,e}

b_tK_{u,e}F.  
]

Its first coordinate gives

# [  
P(e\mid x_t,u)

b_tK_{u,e}\mathbf1.  
]

The normalized next compressed state is

# [  
x_{t+1}

\frac{  
x_tB_{u,e}  
}{  
P(e\mid x_t,u)  
}.  
]

Because all action losses and stage costs lie in (\mathcal V_\star), they can also be computed directly from (x_t).

Therefore:

> **The projected state (x_t=b_tF) is an exact recursively sufficient information state for finite-horizon decision making whenever the loss-feature space is invariant under the joint write–read operators.**

The Bellman recursion closes entirely in (d_\star) dimensions.

This is the correct sequential analogue of the one-step rank result.

---

# 22. Why the sequential result matters

The one-step problem has effective dimension approximately

[  
r=\operatorname{rank}(D)\le|A|-1.  
]

Sequential planning may require additional dimensions when the write–read dynamics move information outside that loss subspace.

The key empirical quantity is therefore

[  
d_\star  
]

rather than simply (r).

If, in realistic environments,

[  
d_\star  
\ll  
|H|  
]

and especially if

[  
d_\star  
\approx  
r+O(1),  
]

then LearnLoop can maintain many semantic causal hypotheses while performing sequential planning in a state whose dimension is governed primarily by the available interventions rather than the number of causal stories.

This is a potentially strong result.

If closure instead expands to nearly (|H|), that is also informative: the low-dimensional one-step representation is not sufficient for non-myopic planning in that regime.

---

# 23. Approximate decision closure

Exact invariance will not always hold.

For representation (F), define an operator residual

# [  
\varepsilon_{\mathrm{op}}(F)

\max_{u,e}  
\min_B  
|  
K_{u,e}F-FB  
|.  
]

Define loss reconstruction error

# [  
\varepsilon_{\mathrm{loss}}(F)

\max_a  
\min_{\lambda_a}  
|  
\ell_a-F\lambda_a  
|.  
]

The research objective becomes a dimension–accuracy frontier:

[  
d  
\quad\text{vs}\quad  
\varepsilon_{\mathrm{op}}  
\quad\text{vs}\quad  
\varepsilon_{\mathrm{loss}}  
\quad\text{vs}\quad  
\text{policy regret}.  
]

A practical algorithm can:

1. initialize from decision-loss features;
    
2. repeatedly apply write–read operators;
    
3. append only decision-relevant singular directions above a tolerance;
    
4. fit low-dimensional (B_{u,e});
    
5. stop when incremental projected decision error becomes negligible.
    

The theoretical goal is an approximate-information-state guarantee of the form

[  
V^\star(b)-V^{\pi_F}(b)  
\le  
\mathcal B_H(  
\varepsilon_{\mathrm{loss}},  
\varepsilon_{\mathrm{op}}  
),  
]

with the bound expressed directly in downstream decision loss.

A careful derivation is required because posterior normalization can amplify approximation error for very rare observations.

---

# 24. Ambiguity for the sequential model

For one-step decisions, ambiguity can live in (Z)-space.

For sequential planning, the reusable uncertain objects are the **projected operators**

[  
B_{u,e}\in\mathcal B_{u,e}.  
]

The raw learner-response and causal-transition data remain preserved.

At decision time, the current (x_t) and projected operators induce the relevant local (Z)-geometry.

This avoids making ambiguity sets permanently dependent on one historical belief (b_t).

The sequential robust-control problem should initially remain short-horizon or episode-local. Fully dynamic distributional robustness requires careful assumptions about how uncertainty sets compose across time; this should not be hidden behind a naïve multistep worst-case Bellman recursion.

---

# 25. Context contamination as a second domain

The same causal-repair core can be used for an AI system whose behavior is altered by its context.

The abstract problem is no longer specifically a “learner.” It is:

> **A stateful system being diagnosed through interventions that may themselves alter the state.**

For an LLM or RAG system:

|LearnLoop|Context-integrity analogue|
|---|---|
|Learner response|Model answer / tool call|
|Learner hypothesis|Context-failure hypothesis|
|Diagnostic item|Controlled context mutation|
|Repair|Remove, replace, reretrieve, reset|
|Cold verification|Fresh paraphrase / fresh context / new seed|
|Learner burden|Tokens, latency, compute|
|Durable learner write|Persistent memory or trust write|
|(H_{\mathrm{other}})|Unknown contamination cause|

Possible context hypotheses include:

- irrelevant distractor;
    
- false retrieved fact;
    
- stale documentation;
    
- source conflict;
    
- prompt injection;
    
- misleading in-context example;
    
- generated-summary distortion;
    
- context-order effect;
    
- context dilution;
    
- corrupted tool output;
    
- persistent memory contamination;
    
- unknown cause.
    

Possible interventions include:

- remove one source;
    
- isolate one source;
    
- reorder context;
    
- replace a suspicious chunk;
    
- reretrieve;
    
- clear conversational memory;
    
- run without retrieval;
    
- rerun under a clean context;
    
- verify with an external checker.
    

Context contamination is an excellent first sequential testbed because interventions are largely:

- reversible;
    
- replayable;
    
- cheaply repeatable;
    
- and compatible with planted ground-truth contamination causes.
    

---

# 26. Auditing LearnLoop's own context

The context-contamination extension should first be used internally.

A dangerous loop is:

1. LearnLoop hypothesizes misconception (h).
    
2. Future grader prompts include (h).
    
3. The grader becomes anchored toward evidence for (h).
    
4. That output further strengthens (h).
    
5. The hypothesis becomes self-confirming.
    

Therefore LearnLoop should maintain separate context authorities.

### Blind measurement context

The grader receives:

- item;
    
- rubric;
    
- learner response;
    
- deterministic verifier output.
    

It does not receive provisional misconception hypotheses unless strictly necessary.

### Causal interpretation context

The diagnostician receives the blind grade, trace, history, and candidate hypotheses.

### Confirmation context

A confirmer or verifier receives only the information needed to test the claim and does not inherit unnecessary proposal context.

This operationalizes LearnLoop's existing rule that the component proposing a causal learner-state claim may not confirm its own claim.

---

# 27. GenAICanHarmLearning as an external benchmark

The Bastani et al. dataset is particularly useful for validating **evidence authority**.

It contains a natural distinction between:

[  
\text{assisted practice success}  
]

and

[  
\text{independent subsequent performance}.  
]

The first real-human benchmark should ask:

> Does LearnLoop incorrectly certify learners after AI-assisted warm success?

Construct one record per student × session × mapped practice/exam problem.

Compare:

- naïve correctness updates;
    
- treatment-arm discounting;
    
- transcript-aware assistance weighting;
    
- hard contamination firewalls;
    
- calibrated evidence-authority updates;
    
- calibrated authority plus independent verification.
    

Primary metric:

[  
P(  
\text{independent failure}  
\mid  
\text{system certified}  
).  
]

Secondary metrics:

- certification coverage;
    
- Brier score;
    
- log loss;
    
- selective risk;
    
- unnecessary verification questions;
    
- calibration.
    

This dataset cannot identify:

- ground-truth causal misconception (h);
    
- effects of individual hints or repairs;
    
- or long-term retention.
    

It should therefore serve as an **external false-certification and assistance-contamination benchmark**, not as the sole dataset for the causal-control model.

---

# 28. Experimental program

## A. Synthetic causal learner benchmark

Build executable learner environments with:

- known causal error programs;
    
- transient slips;
    
- multiple representations;
    
- known response channels;
    
- intervention transitions;
    
- delayed cold outcomes;
    
- open-set mechanisms.
    

Measure:

- causal set coverage;
    
- robust decision regret;
    
- number of probes;
    
- harmful writes;
    
- false certifications;
    
- open-world detection;
    
- repair-effect estimation.
    

## B. Context-contamination benchmark

Plant controlled context failures and permit exact counterfactual interventions.

Compare:

- exhaustive context ablation;
    
- random ablation;
    
- LLM self-critique;
    
- direct causal attribution;
    
- point EVSI;
    
- full-channel robust EVSI;
    
- projected robust EVSI;
    
- sequential D-Closure planning.
    

Primary outcome:

[  
\frac{  
\text{verified recovery}  
}{  
\text{model calls or token cost}  
}.  
]

Also measure useful-context preservation and false quarantine.

## C. One-step LearnLoop replay

Compare current selection against:

- entropy/EIG;
    
- point EVSI;
    
- minimum over channel samples;
    
- ensemble quantiles;
    
- convex-hull robust EVSI;
    
- projected robust EVSI.
    

Primary metric:

[  
\text{downstream action regret per learner-minute}.  
]

## D. Projection experiments

Measure

[  
r=\operatorname{rank}(D)  
]

and

[  
d_\star=\dim\mathcal V_\star.  
]

Compare:

- full latent belief;
    
- one-step (D)-projection incorrectly reused sequentially;
    
- exact decision closure;
    
- approximate closure;
    
- generic PCA;
    
- semantic embeddings.
    

The key empirical question is whether

[  
d_\star/|H|  
]

remains small.

## E. Generated diagnostic experiments

Compare:

- generic LLM question generation;
    
- semantic hypothesis-separation prompts;
    
- action-boundary targeting;
    
- boundary targeting plus executable mal-procedures;
    
- full robust DSED generation.
    

Measure realized, not merely simulated, downstream action value.

## F. Robust-equipoise simulation

Compare:

- deterministic modal repair;
    
- unrestricted exploration;
    
- conventional bandit exploration;
    
- point-estimate equipoise;
    
- robust equipoise.
    

Measure:

- learner regret;
    
- treatment-effect estimation error;
    
- overlap;
    
- cold success;
    
- and incorrect inclusion of inferior actions.
    

## G. Prospective human study

Once safe overlap exists, micro-randomize only among robustly near-equivalent interventions.

Use delayed independent cold performance as the causal outcome.

---

# 29. Publication strategy

The complete research program should not be submitted as one monolithic paper.

## Paper 1 — Primary target

### **Decision-Sufficient Robust Experimental Design with Generated Tests**

Core contributions:

1. exact one-step loss projection;
    
2. dimension bound
    
    [  
    (|E|-1)\operatorname{rank}(D);  
    ]
    
3. calibrated projected ambiguity sets;
    
4. convex-hull robust-EVSI LP;
    
5. cost-adjusted decision-collapse radius;
    
6. regret-profile decision covers;
    
7. executable generated-probe admission;
    
8. open-world abstention;
    
9. synthetic + context-contamination + real-human external evaluation.
    

This is the best first NeurIPS/ICML/ICLR direction.

---

## Paper 2

### **Causal Learning Under Robust Equipoise**

Core contributions:

1. robust near-optimal action sets;
    
2. per-decision regret guarantee;
    
3. adaptive experimental allocation inside the safe set;
    
4. known logged propensities;
    
5. eligibility-conditioned distal causal excursion effects;
    
6. delayed cold outcomes;
    
7. causal repair-effect learning.
    

This requires prospective randomization.

---

## Paper 3

### **Decision-Predictive State Representations for State-Changing Experimental Design**

Core contributions:

1. joint write–read kernel;
    
2. exact write/read value decomposition;
    
3. minimal decision-loss-generated invariant closure;
    
4. exact recursively sufficient state
    
    [  
    x_t=b_tF_\star;  
    ]
    
5. decision-closure dimension (d_\star);
    
6. approximate closure and policy-loss bounds;
    
7. robust projected operators;
    
8. generated state-changing experiments.
    

Evaluate first on context contamination and then on tutoring.

---

# 30. Novelty boundary

Several surrounding ingredients already have strong neighboring literatures:

- Bayesian experimental design;
    
- robust/DRO experimental design;
    
- decision-region determination;
    
- partially observable control;
    
- predictive-state representations;
    
- safe and conservative bandits;
    
- micro-randomized trials;
    
- causal excursion effects;
    
- generated diagnostic questions;
    
- LLM personas.
    

The research claim should therefore **not** be that LearnLoop invented any one of these individually.

The distinctive contribution is their decision-theoretic integration around a specific structural principle:

> **Only uncertainty directions that can change a safe downstream action deserve diagnostic effort or persistent state authority.**

The strongest technical novelty candidates are:

[  
\boxed{  
\text{loss-generated low-dimensional experiment projection}  
}  
]

combined with

[  
\boxed{  
\text{robust action-conditioned stopping and generated inverse experiments}  
}  
]

and, sequentially,

[  
\boxed{  
\text{minimal write–read invariant closure generated from downstream losses}.  
}  
]

A deeper related-work review should explicitly test novelty against:

- goal-oriented Bayesian experimental design;
    
- reward-predictive and value-equivalent representations;
    
- controlled invariant subspaces;
    
- approximate information states;
    
- bisimulation;
    
- partial monitoring;
    
- Blackwell/deficiency orderings;
    
- robust POMDPs;
    
- and performative prediction.
    

Novelty should be claimed only after that review.

---

# 31. Implementation architecture

The research system should not replace LearnLoop's immutable causal substrate.

Add a shadow decision layer.

### `decision_features`

Compile:

- feasible actions;
    
- empirical action-loss vectors;
    
- regret profiles;
    
- decision rank;
    
- action-boundary geometry.
    

### `projected_ambiguity`

Maintain:

- channel/posterior samples;
    
- projected samples;
    
- convex ambiguity representations;
    
- decision-collapse radius;
    
- calibration coverage.
    

### `decision_closure`

Compute:

[  
\mathcal V_\star,  
]

its basis (F), closure dimension, and approximation residuals.

### `projected_operators`

Estimate

[  
B_{u,e}  
]

for sequential write–read controls.

### `equipoise`

Compute robust near-optimal intervention sets and experimental propensities.

Every decision receipt should preserve:

```text
belief/hypothesis-set version
loss-matrix version
feasible-action-set hash
regret-cover version
decision rank
projected ambiguity version
robust EVSI
collapse/stability margin
closure-basis version
closure dimension
operator residual
projected-operator version
randomization propensity
pre-write evidence authority
post-write evidence authority
causal-effect authority
```

Raw responses and original observations are never replaced by compressed representations.

---

# 32. Final research framing

The broad research program can be summarized as:

[  
\boxed{  
\textbf{Decision-Sufficient Causal Diagnosis and Repair}  
}  
]

An intelligent system repeatedly faces four questions:

[  
\boxed{  
\begin{array}{ll}  
\textbf{What should I believe?}  
&  
\text{Maintain corrigible open-world causal hypotheses.}\[4pt]

\textbf{What should I ask?}  
&  
\text{Acquire only information with robust downstream decision value.}\[4pt]

\textbf{What should I do?}  
&  
\text{Choose the smallest safe repair justified across plausible states.}\[4pt]

\textbf{What should I learn from doing it?}  
&  
\text{Use near-equivalent actions for bounded-regret causal experimentation.}  
\end{array}  
}  
]

For static diagnosis, uncertainty collapses through the loss matrix into a low-dimensional decision projection.

For sequential diagnosis, the system expands that projection only as much as required for closure under state-changing write–read dynamics.

For generated experiments, the LLM proposes interventions that target the current decision boundary while executable verifiers and robust uncertainty sets determine whether those probes deserve learner effort.

For open-world failures, semantic hypotheses may grow without forcing proportional growth in the live decision state.

For intervention learning, decision indifference creates experimental equipoise.

And for context contamination, the same machinery diagnoses and minimally repairs the context of the AI system itself.

The resulting conceptual shift is:

> **LearnLoop should not try to know the learner completely. It should know exactly enough to make the next consequential decision safely, acquire more information only when that decision depends on it, and continuously learn better interventions without charging the learner unnecessary experimental cost.**
# My assessment

This is converging on a real paper. The strongest direction is indeed the sequential extension—but the theorem should **not** be:

> “If transitions respect the current action cells, then (Z_t) is Markov.”

That condition is insufficient, and (Z_q) is not quite the right sequential state. The better result is:

> **The one-step loss projection generates a minimal invariant subspace under the joint write–read operators. Belief projected onto that subspace is an exact recursively updatable information state.**

That gives you a precise theorem, an algorithm for computing the necessary dimension, and a clear failure mode when the one-step rank-(r) representation is not closed.

Before formalizing it, the latest brainstorm reintroduces several errors that matter.

---

# 1. The persona-hull extreme-point argument is still reversed

For a fixed belief (b), choose baseline action (a_0) and let

[  
D(h,a)=L(h,a)-L(h,a_0).  
]

For response channel (M),

# [  
z_e(a)

\sum_h b(h)M(e\mid h)D(h,a).  
]

The expected risk after the experiment is

# [  
G(M)

b^\top L_{\cdot,a_0}  
+  
\sum_e\min_a z_e(a).  
]

Because each pointwise minimum is concave,

[  
G(M)  
]

is concave in the channel. The robust lower value is

# [  
\underline V(q;b)

## R(b)

## \sup_{M\in\mathcal P_q}G(M)

c(q).  
]

Nature maximizes post-experiment risk. A maximum of a concave function over a convex set can occur in the interior.

Equivalently, the experiment value

[  
V(M)=R(b)-G(M)  
]

is convex in (M), and minimizing a convex function over a convex hull can also produce an interior optimum.

Therefore,

[  
\inf_{M\in\operatorname{conv}{M^{(1)},\ldots,M^{(K)}}}  
V(M)  
]

is **not** generally equal to

[  
\min_k V(M^{(k)}).  
]

## A simple counterexample

Take two latent hypotheses and two responses.

- (M^{(1)}) reports the hypothesis perfectly.
    
- (M^{(2)}) reports the opposite label perfectly.
    

If the experimenter knows which channel is used, either extreme channel is perfectly informative.

But the mixture

[  
\frac12M^{(1)}+\frac12M^{(2)}  
]

makes the response independent of the hypothesis. It has zero diagnostic value. The worst channel is the interior mixture, not either persona vertex.

So persona channels can define vertices, but the selector must solve

[  
\begin{aligned}  
\max_{\alpha,t}\quad&  
\sum_e t_e\  
\text{s.t.}\quad&  
t_e  
\leq  
\sum_h b(h)  
\left[  
\sum_k\alpha_kM^{(k)}(e\mid h)  
\right]  
L(h,a),  
&&\forall e,a,\  
&\alpha\in\Delta_K.  
\end{aligned}  
]

Taking the minimum over persona runs remains optimistically biased toward probing.

This is directly relevant to LearnLoop’s current robust EVSI implementation: it evaluates a finite ensemble and takes a lower quantile, rather than optimizing over mixtures of plausible channels.

## KL ambiguity is still tractable, but not automatically a single softmin

With row-wise KL constraints, the same epigraph formulation becomes a convex exponential-cone program:

[  
\begin{aligned}  
\max_{P,t}\quad&  
\sum_e t_e\  
\text{s.t.}\quad&  
t_e\leq\sum_h b_hP_{he}L_{ha},  
&&\forall e,a,\  
&D_{\mathrm{KL}}(P_h\Vert \widehat P_h)\leq\rho_h,  
&&\forall h.  
\end{aligned}  
]

Its dual will involve entropic or log-sum-exp terms, but the action epigraph constraints couple the response rows. It is not generally the same simple softmin transformation used for one linear expectation under a KL ball.

The convex-hull LP is the cleaner initial research object.

---

# 2. Put one-step decisions in (Z)-space, but sequential uncertainty in **operator space**

The statement

> “Every question should be posed in (Z)-space”

is correct for a one-step decision at a fixed belief and loss matrix.

It is not sufficient for sequential planning.

The projected object

[  
Z_q(b,L)  
]

depends on:

- the current belief (b);
    
- the current loss matrix (L);
    
- the current feasible action set;
    
- and the selected experiment (q).
    

After an observation, the belief changes. After a repair, the learner state and loss model may change. A static set around the current (Z_q) does not tell the system how to update the compressed state on the next step.

The sequential object should be a set of **projected controlled operators**, not merely projected points.

---

# 3. The exact sequential theorem to pursue

## 3.1 Joint write–read kernels

Let (H) be the finite latent-state space. A control (u) can be:

- a pure diagnostic probe;
    
- an instructional diagnostic;
    
- a repair;
    
- or another state-changing interaction.
    

For each observation (e), define the joint sub-stochastic matrix

# [  
K_{u,e}(h,h')

P(H_{t+1}=h',E_t=e\mid H_t=h,U_t=u).  
]

These satisfy

[  
\sum_eK_{u,e}\mathbf 1=\mathbf 1.  
]

Given row-vector belief (b_t),

# [  
P(e\mid b_t,u)

b_tK_{u,e}\mathbf 1,  
]

and the posterior over the post-write state is

# [  
b_{t+1}

\frac{b_tK_{u,e}}  
{b_tK_{u,e}\mathbf 1}.  
]

This single kernel handles both:

- the write (h\rightarrow h');
    
- and the read (h,h'\rightarrow e).
    

## 3.2 The starting loss subspace

Let:

- (\ell_a\in\mathbb R^{|H|}) be the terminal loss vector for downstream action (a);
    
- (c_u\in\mathbb R^{|H|}) be any state-dependent immediate expected cost of control (u).
    

Define

# [  
\mathcal V_0

\operatorname{span}  
\left{  
\mathbf 1,,  
\ell_a:a\in A,,  
c_u:u\in U  
\right}.  
]

Using centered losses,

[  
D_a=\ell_a-\ell_{a_0},  
]

gives the equivalent starting representation

# [  
\mathcal V_0

\operatorname{span}  
\left{  
\mathbf1,,  
\ell_{a_0},,  
D_a:a\in A,,  
c_u:u\in U  
\right}.  
]

The one-step action-discrimination dimension is

[  
r=\operatorname{rank}(D)\leq |A|-1.  
]

But sequential planning generally needs the baseline-loss feature and normalization feature as well, so the initial sequential dimension is bounded by approximately

[  
r+2  
]

before adding any state-dependent stage-cost directions.

## 3.3 Exact decision-closure condition

Let (F\in\mathbb R^{|H|\times d}) have columns forming a basis for a subspace (\mathcal V) that contains (\mathcal V_0).

Require that, for every control and observation,

[  
K_{u,e}\mathcal V\subseteq\mathcal V.  
]

Equivalently, there must exist a matrix (B_{u,e}\in\mathbb R^{d\times d}) satisfying

[  
K_{u,e}F=FB_{u,e}.  
]

Define the compressed state

[  
x_t=b_tF.  
]

### Theorem: exact decision-predictive closure

Under the containment and invariance conditions above, (x_t) is an exact information state for finite-horizon decision-making:

1. The response probability is computable from (x_t).
    
2. The next compressed state is recursively computable from (x_t,u,e).
    
3. Every immediate cost and terminal action loss is computable from (x_t).
    
4. Consequently, the optimal value and an optimal policy depend on (b_t) only through (x_t).
    

### Proof sketch

Choose the first column of (F) to be (\mathbf1). Then

# [  
y_{u,e}

# b_tK_{u,e}F

x_tB_{u,e}.  
]

Its first coordinate is

# [  
p_{u,e}

# b_tK_{u,e}\mathbf1

P(e\mid x_t,u).  
]

The normalized next compressed state is

# [  
x_{t+1}

\frac{x_tB_{u,e}}{p_{u,e}}.  
]

If

[  
c_u=F\theta_u  
\quad\text{and}\quad  
\ell_a=F\lambda_a,  
]

then

[  
b_tc_u=x_t\theta_u  
]

and

[  
b_t\ell_a=x_t\lambda_a.  
]

Thus the Bellman recursion closes:

# [  
V_t(x)

\min_u  
\left[  
x\theta_u  
+  
\sum_e  
p_{u,e}(x)  
V_{t+1}  
\left(  
\frac{xB_{u,e}}{p_{u,e}(x)}  
\right)  
\right],  
]

with

[  
V_T(x)=\min_a x\lambda_a.  
]

This is the exact sequential result the paper should pursue.

---

# 4. The minimal closure dimension can be computed

Define recursively

# [  
\mathcal V_{k+1}

\mathcal V_k  
+  
\operatorname{span}  
\left{  
K_{u,e}v:  
v\in\mathcal V_k,\ u\in U,\ e\in E  
\right}.  
]

Because the latent space is finite-dimensional, this stabilizes after at most (|H|) dimension increases:

# [  
\mathcal V_\star

\mathcal V_K  
]

for some finite (K).

Then (\mathcal V_\star) is the smallest subspace that:

- contains all decision and cost features;
    
- and is invariant under every controlled write–read operator.
    

Define

[  
d_\star=\dim\mathcal V_\star.  
]

This is the **decision-closure dimension**.

## What the rank-(r) insight really gives

The one-step result says:

[  
d_{\text{one-step}}  
\approx  
\operatorname{rank}(D).  
]

The sequential result says:

# [  
d_\star

\dim  
\operatorname{closure}  
\left(  
\mathbf1,\ell_{a_0},D,c;  
{K_{u,e}}  
\right).  
]

If the initial loss subspace is already invariant, then

[  
d_\star  
\leq r+2  
]

apart from extra stage-cost directions.

If it is not invariant, the dimension can grow, potentially all the way to (|H|).

That yields a meaningful empirical research question:

> How often do realistic tutoring and context-contamination systems have low decision-closure dimension even when their semantic hypothesis spaces are large?

That is a much stronger question than merely observing that the one-step loss matrix is low-rank.

---

# 5. “Transitions respect action cells” is insufficient

The current action cell of a hypothesis tells you which repair minimizes its immediate loss. It does not tell you:

- what observation the hypothesis generates;
    
- which post-write state it transitions into;
    
- or how much probability it assigns to future decision cells.
    

Two states can currently prefer the same action while producing different future evidence and transitioning to states requiring different future repairs.

## Partition-based sufficient condition

For a partition (\phi:H\to\mathcal C), aggregate block belief is recursively sufficient if, at minimum:

### Loss compatibility

For (h,\tilde h) in the same block,

[  
\ell_a(h)=\ell_a(\tilde h)  
\qquad  
\forall a,  
]

or an appropriately normalized equivalent when only action regret matters.

### Strong controlled lumpability

For every current block (C), target block (C'), control (u), and observation (e),

[  
\sum_{h'\in C'}K_{u,e}(h,h')  
]

must be identical for every (h\in C).

Merely requiring both states to transition “into the same collection of action cells” is not enough; the aggregate probabilities must also match.

The linear invariant-subspace theorem above is more general than a discrete partition and cleaner for the rank-based story.

This result is adjacent to existing information-state and predictive-state-representation theory. Approximate information-state work characterizes recursively updatable representations sufficient for predicting costs and future observations, while reward-predictive PSRs extend ordinary PSRs specifically so they can support correct control and value computation. ([arXiv](https://arxiv.org/abs/2106.03926 "Reconciling Rewards with Predictive State Representations"))

Therefore, the generic claim “a compressed recursively sufficient POMDP state exists under closure conditions” is not novel. The potential novelty is the **loss-generated construction**, its exact starting rank, the controlled write–read setting, and its use for robust generated experiments.

---

# 6. (Z_t) is not the Markov state; (x_t=b_tF_\star) is

This distinction will keep the paper conceptually clean.

- (Z_q) is an **experiment-specific local projection** used to evaluate one candidate experiment at the current state.
    
- (x_t) is the **recursively sufficient decision state**.
    
- (B_{u,e}) is the **projected write–read operator**.
    

The sequential ambiguity model should therefore be

[  
B_{u,e}\in\mathcal B_{u,e},  
]

possibly with a closure residual, rather than only

[  
Z_q\in\mathcal Z_q(b_t).  
]

At decision time,

[  
Z_q

]

can be computed from (x_t) and the relevant (B_{q,e}).

This also makes old data reusable when the belief changes. You preserve observations and estimate low-dimensional operators rather than storing only belief-specific projected points.

---

# 7. Approximate closure is probably the empirically important case

Exact invariance will often fail. Define an operator residual

# [  
\varepsilon_{\mathrm{op}}(F)

\max_{u,e}  
\min_B  
\left|  
K_{u,e}F-FB  
\right|.  
]

Also define a loss-reconstruction residual

# [  
\varepsilon_{\mathrm{loss}}(F)

\max_a  
\min_{\lambda_a}  
\left|  
\ell_a-F\lambda_a  
\right|.  
]

Then study the tradeoff:

[  
d  
\quad\text{versus}\quad  
\varepsilon_{\mathrm{op}}(F)  
\quad\text{versus}\quad  
\varepsilon_{\mathrm{loss}}(F).  
]

A likely algorithm is:

1. start with (\mathcal V_0);
    
2. apply the (K_{u,e}) operators;
    
3. append only singular directions above a tolerance;
    
4. stop when the incremental projected decision error is sufficiently small.
    

Approximate-information-state theory already shows that approximate recursive cost and observation prediction can lead to bounded policy loss. It would be better to adapt those results than to guess a new bound. ([arXiv](https://arxiv.org/abs/2010.08843 "Approximate information state for approximate planning and reinforcement learning in partially observed systems"))

The paper-specific bound should be expressed in terms of **decision loss**, not generic belief reconstruction error.

A promising target is something like

[  
V^\star(b)-V^{\pi_F}(b)  
\leq  
C_H  
\left(  
\varepsilon_{\mathrm{loss}}  
+  
\varepsilon_{\mathrm{op}}  
\right),  
]

where (C_H) depends on horizon or discounting. Care is needed around rare observations because normalization can magnify conditional-state error.

---

# 8. The response-binning claim is only one-step valid

Merging response categories (e,e') preserves current one-step value if their unnormalized posterior loss vectors always occupy one common linear region of Bayes risk.

A safe condition is:

[  
\exists a  
\quad\text{such that}\quad  
a\in\arg\min_{a'}z_e(a')  
\cap  
\arg\min_{a'}z_{e'}(a')  
]

for every channel in the entire ambiguity set, not merely for each sampled vertex.

Because an action cell is convex, merging two points in the same cell preserves the action and one-step risk.

However, merged responses may still differ in:

- future experiment value;
    
- open-world anomaly detection;
    
- post-write state transitions;
    
- or evidence relevant after the action set changes.
    

Thus response compression should be:

- decision- and horizon-specific;
    
- rebuilt when (L), (A), or the planning horizon changes;
    
- and used only as a derived view over preserved raw responses.
    

---

# 9. Delayed outcomes do not retrospectively reveal (h)

A repair outcome gives evidence about

[  
P(Y^{\mathrm{cold}}=1\mid do(a),x),  
]

not a direct label for the original causal hypothesis.

A failed repair can mean:

- the diagnosis was wrong;
    
- the repair was ineffective despite a correct diagnosis;
    
- execution failed;
    
- the verification item was bad;
    
- or the learner state changed for another reason.
    

Importance weighting does not convert a delayed outcome into a known (h). It can support causal estimation of repair effects when:

- treatment propensities are known;
    
- there is sufficient overlap;
    
- delayed-outcome missingness is handled;
    
- and the estimand is stated correctly.
    

Keep separate models for:

[  
P(e\mid h,q),  
]

[  
P(h'\mid h,a),  
]

and

[  
P(Y^{\mathrm{cold}}\mid h,a,h').  
]

LearnLoop already explicitly separates diagnosis support, repair-effect support, and capability evidence, and it forbids successful repair from retroactively proving the original diagnosis.

---

# 10. Conformal anomaly scores are not (b(H_{\mathrm{other}}))

A conformal residual or e-process can provide:

- an anomaly score;
    
- a calibrated rejection rule;
    
- or a prediction set with coverage.
    

It does not automatically produce a Bayesian posterior mass

[  
b(H_{\mathrm{other}}).  
]

Use separate quantities:

# [  
s_{\mathrm{open}}

\text{model-misspecification score},  
]

and, only if trained against historically adjudicated open-set events,

# [  
\widehat p_{\mathrm{open}}

P(\text{enumerated set incomplete}\mid x).  
]

The action model should represent unknown causes using a set of regret profiles:

[  
\rho_{\mathrm{other}}  
\in\mathcal R_{\mathrm{other}},  
]

not a single LLM-authored pessimistic row.

When open-set evidence rises:

1. restrict aggressive actions through robust feasibility;
    
2. let the LLM propose new semantic hypotheses;
    
3. derive or conservatively bound their repair effects;
    
4. preserve them as causal hypotheses;
    
5. place them into the current decision cover if their regret profiles are similar;
    
6. require prospective evidence before granting additional authority.
    

Do not ask the same LLM to invent the hypothesis and author an authoritative loss row for it.

---

# 11. The proposed quotient is still not a quotient

The relation

[  
h\sim h'  
\iff  
A_\epsilon(h)\cap A_\epsilon(h')\neq\varnothing  
]

is not transitive.

For example:

- (h_1) and (h_2) may share repair (a);
    
- (h_2) and (h_3) may share repair (b);
    
- (h_1) and (h_3) may have no common acceptable repair.
    

Use regret-profile covers:

# [  
\rho_h(a)

L(h,a)-\min_{a'}L(h,a'),  
]

# [  
d_D(h,h')

|\rho_h-\rho_{h'}|_\infty.  
]

Then construct diameter-(\epsilon) cover cells. Each cell has a guaranteed common (\epsilon)-optimal repair, but the cover is not claimed to be an equivalence quotient.

Semantic hypotheses should still remain separately persisted because they may make different future predictions even when they currently share a repair.

---

# 12. “No generated probe is worth it” requires a model of what can be generated

From (b) and (D) alone, you can compute a universal upper bound:

[  
\operatorname{EVSI}(q;b)  
\leq  
\operatorname{EVPI}(b).  
]

But you cannot obtain a meaningful tighter certificate for every possible generated experiment without constraining the generatable experiment class.

Mathematically, an unconstrained experiment could reveal (h) perfectly.

Define an outer approximation of attainable projected experiments:

# [  
\mathfrak Z_{\mathrm{gen}}

\left{  
Z(q):  
q\text{ satisfies the generation, validity, burden, and manipulation contracts}  
\right}.  
]

Then a valid certificate is

[  
\sup_{Z\in\mathfrak Z_{\mathrm{gen}}}  
\underline V(Z;b)  
\leq 0.  
]

The research problem becomes learning or verifying (\mathfrak Z_{\mathrm{gen}}).

For state-changing questions, the issue is stronger: an unconstrained question could directly repair the learner perfectly even with zero diagnostic information. A no-experiment certificate must bound both:

- the best attainable read value;
    
- and the best attainable write value.
    

---

# 13. Inverse experiment generation should target projected operators

The inverse-design idea is strong, but for the sequential paper its target should be

[  
{B_{q,e}}_e,  
]

or a local realization of those operators at current compressed state (x_t), rather than arbitrary full channels.

For an action boundary (a) versus (a'), define the loss contrast

[  
d_{a,a'}=\ell_a-\ell_{a'}.  
]

The generator should seek responses for which the projected post-observation states lie on decision-relevantly different sides:

[  
x_{q,e}\lambda_a  
<  
x_{q,e}\lambda_{a'}  
]

for one response, and the reverse inequality for another.

A practical loop is:

1. Find the binding or nearest action boundary.
    
2. Select decision-relevant hypothesis pairs whose regret profiles lie on different sides.
    
3. Ask the LLM to generate a natural probe designed to expose their behavioral difference.
    
4. Execute deterministic mal-procedures on the candidate.
    
5. Reject it if the predicted traces do not differ.
    
6. Add persona/noise simulations.
    
7. fit or bound the projected operators;
    
8. evaluate robust decision value over the entire plausible hypothesis set;
    
9. admit only if the manipulation and contamination contracts pass.
    

This is more principled than asking the generator to “maximize information.”

---

# 14. Where the novelty now sits

The latest 2026 literature makes the novelty boundary tighter than it initially appeared.

GoBOED directly optimizes expected downstream robust decision quality rather than an information-theoretic surrogate, and proves that its gradient ignores parameter directions outside a task-relevant linear subspace. It is single-step and parameter/posterior focused, but it means that “decision-focused design ignores irrelevant uncertainty directions” is no longer enough as the main novelty. ([arXiv](https://arxiv.org/abs/2605.26093 "Goal-driven Bayesian Optimal Experimental Design for Robust Decision-Making Under Model Uncertainty"))

GO-CBED is sequential and non-myopic, but it still optimizes information gain on specified causal quantities of interest rather than the final discrete action loss. ([arXiv](https://arxiv.org/abs/2507.07359?utm_source=chatgpt.com "Goal-Oriented Sequential Bayesian Experimental Design for Causal Learning"))

Predictive-state and approximate-information-state work already addresses recursively sufficient low-dimensional representations for partially observed control, including representations that preserve rewards as well as observations. ([arXiv](https://arxiv.org/abs/2106.03926 "Reconciling Rewards with Predictive State Representations"))

Track-and-stop causal discovery already provides adaptive intervention allocation and fixed-confidence stopping, but its target is recovery of causal structure rather than entry into a downstream action-equivalence region. ([Proceedings of Machine Learning Research](https://proceedings.mlr.press/v235/elahi24a.html "Adaptive Online Experimental Design for Causal Discovery"))

Therefore the defensible contribution is the conjunction:

1. **An exact loss-generated one-step projection.**
    
2. **A minimal controlled invariant closure under joint write–read kernels.**
    
3. **Ambiguity over the resulting low-dimensional operators.**
    
4. **Action-equivalence rather than model-identification stopping.**
    
5. **Generated experiments targeted at decision boundaries.**
    
6. **Explicit evidence authority for pre-write versus post-write observations.**
    
7. **Evaluation in contexts where the experiment itself changes the object being diagnosed.**
    

I would not yet claim that no equivalent invariant-subspace theorem exists under another name. A deeper literature review on reward-predictive representations, observable-operator models, bisimulation, and controlled invariant subspaces is needed before making that novelty claim.

---

# 15. The best paper formulation

## **Decision-Predictive State Representations for State-Changing Experimental Design**

### Central problem

An experiment (u) simultaneously:

- changes a hidden state;
    
- generates an observation;
    
- incurs a cost;
    
- and affects which downstream action is optimal.
    

The latent state may be enormous or semantically open-ended, but only a low-dimensional subspace may matter for future decisions.

### Main contributions

#### 1. One-step decision projection

Show that current experiment value depends on channel uncertainty only through the loss projection and has affine dimension bounded by approximately

[  
(|E|-1)\operatorname{rank}(D).  
]

#### 2. Minimal sequential decision closure

Define and compute

# [  
\mathcal V_\star

\operatorname{InvClosure}  
\left(  
\mathbf1,\ell,c;  
{K_{u,e}}  
\right),  
]

and prove that

[  
x_t=b_tF_\star  
]

is an exact information state.

#### 3. Approximate closure

Develop a low-rank approximation with explicit operator and decision-loss residuals, then derive a finite-horizon or discounted policy-loss bound.

#### 4. Robust projected operators

Estimate ambiguity sets

[  
B_{u,e}\in\mathcal B_{u,e}  
]

from:

- executable hypothesis models;
    
- simulator ensembles;
    
- real response telemetry;
    
- and coder uncertainty.
    

#### 5. Generated inverse design

Generate probes that realize desired movement across action boundaries in compressed decision space.

#### 6. Action-conditioned stopping

Stop when either:

[  
C_\delta(b)  
]

admits a common (\epsilon)-repair, or the best attainable experiment has nonpositive robust total value.

---

# 16. The algorithm

A concrete algorithm could be called **D-Closure**.

## Offline or periodic compilation

1. Build the current loss matrix and feasible action set.
    
2. Form
    
    # [  
    \mathcal V_0
    
    \operatorname{span}  
    {\mathbf1,\ell_a,c_u}.  
    ]
    
3. Estimate or simulate the joint kernels (K_{u,e}).
    
4. Iteratively close the subspace under (K_{u,e}).
    
5. Compress near-dependent directions with SVD or a decision-weighted low-rank method.
    
6. Fit projected operators (B_{u,e}).
    
7. Record:
    
    - closure dimension;
        
    - operator residual;
        
    - loss-reconstruction residual;
        
    - model and action-set versions.
        

## Online

1. Project current belief:
    
    [  
    x_t=b_tF.  
    ]
    
2. Apply safety and learner-intent constraints.
    
3. Test common-repair and EVPI upper bounds.
    
4. Evaluate existing probes using robust projected-operator value.
    
5. If none is adequate, generate probes targeted at the binding action boundary.
    
6. Administer the selected control.
    
7. Update:
    
    # [  
    x_{t+1}
    
    \frac{x_tB_{u,e}}  
    {p(e\mid x_t,u)}.  
    ]
    
8. Track whether the observed event is:
    
    - evidence about the pre-write state;
        
    - evidence about the post-write state;
        
    - or evidence about the causal effect of the control.
        
9. Stop on robust action stability or nonpositive attainable value.
    

---

# 17. Context contamination is the ideal first sequential testbed

The context-contamination version gives you much cleaner experimental access than human tutoring.

Define:

- hidden state (h): contamination mechanism;
    
- control (u): remove, reorder, isolate, replace, or re-retrieve context;
    
- observation (e): answer signature, verifier result, source citation, or tool behavior;
    
- post-state (h'): remaining contamination after context edit;
    
- downstream action: serve, quarantine, reretrieve, reset memory, or abstain.
    

You can plant known contamination states and replay the same query under many context mutations. This makes it possible to estimate the joint kernels

[  
K_{u,e}(h,h')  
]

and compare:

- full belief-state planning;
    
- one-step (D)-projection;
    
- exact decision closure;
    
- approximate low-rank closure;
    
- and heuristic context ablations.
    

Human tutoring can then be the harder external domain where writes are less reversible and latent states are only partially adjudicated.

---

# 18. The first experiments I would run

## Experiment A: Does one-step rank remain closed?

Across synthetic and context-contamination environments, measure:

[  
r=\operatorname{rank}(D)  
]

and

[  
d_\star=\dim\mathcal V_\star.  
]

The headline empirical question is:

[  
\frac{d_\star}{|H|}  
\ll 1?  
]

Also report how many closure iterations are required and which controls introduce new dimensions.

## Experiment B: Compression versus planning regret

Compare:

- full latent belief;
    
- current one-step (D)-projection used recursively even when invalid;
    
- exact invariant closure;
    
- truncated approximate closure;
    
- generic PCA;
    
- semantic hypothesis embeddings.
    

Measure:

- policy regret;
    
- stop/continue accuracy;
    
- robust calibration;
    
- computation;
    
- and state dimension.
    

This directly shows why the closure theorem matters.

## Experiment C: Persona hull versus mixture adversary

Compare:

- minimum value over persona vertices;
    
- lower quantile over personas;
    
- LP over the persona convex hull;
    
- convex hull plus empirical inflation;
    
- real held-out response channels.
    

The identity-versus-label-swap construction should appear as a synthetic sanity check.

## Experiment D: Generated projected experiments

Given a target action boundary, compare:

- generic LLM diagnostic generation;
    
- hypothesis-separation prompting;
    
- boundary-targeted generation;
    
- boundary targeting plus executable mal-procedure validation;
    
- full robust selection.
    

Measure realized rather than simulated action-value improvement.

## Experiment E: LearnLoop external evaluation

Use GenAICanHarmLearning for the one-step question:

> Does assistance-aware, decision-projected evidence authority reduce false certification of independent capability?

It cannot validate the full sequential write kernel, but it supplies an important real-human stress test.

---

# 19. How this should enter the LearnLoop codebase

I would keep it entirely shadow-only initially.

Add three conceptual components:

```text
decision_features.py
    compile initial loss/cost feature space

decision_closure.py
    compute invariant or approximate closure
    report dimension and residuals

projected_operators.py
    estimate B_{u,e}
    construct ambiguity sets
    score robust sequential controls
```

Every decision receipt should include:

```text
loss_matrix_version
feasible_action_set_hash
closure_basis_version
closure_dimension
closure_residual
projected_operator_model_version
ambiguity_set_version
pre_write_evidence_authority
post_write_evidence_authority
causal_effect_authority
```

No compressed representation should overwrite raw learner evidence. LearnLoop’s existing authority model already distinguishes immutable observations, model-proposed hypotheses, validated causal records, and learner-state projections; that separation is exactly what this work needs.

# Recommendation

The best next theoretical task is not merely proving a cell-respecting partition result. It is to formalize and prove:

# [  
\boxed{  
\mathcal V_\star

\text{the smallest write–read invariant subspace containing all decision-loss features}  
}  
]

and then establish that

[  
x_t=b_tF_\star  
]

is an exact information state.

The best empirical companion is to test whether

[  
d_\star  
]

remains close to

[  
\operatorname{rank}(D)+2  
]

in realistic generated-probe and context-contamination environments. If it does, the result is compelling: LearnLoop can reason over many open-ended causal hypotheses while planning in a decision state whose dimension is controlled primarily by the available repairs rather than the number of causal stories.