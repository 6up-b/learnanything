<User>https://github.com/6up-b/learnanything/blob/main/docs/brainstorming/Pipeline%20Augmentation%20Plan.md Tell me what you think of the current brainstorm for learnloop. I also really liked this approach in this preprint accepted into AISTATS 2026 for knowledge tracing https://openreview.net/pdf/fd2105d5d5780bc1f850a4b8d9f85b4b1c02e24e.pdf and wanted to brainstorm how it would fit into our larger revised pipeline/algorithm.</User>

<Agent># Overall assessment

This is the strongest version of the LearnLoop architecture so far. It no longer reads like a collection of promising models; it reads like an **epistemic system** with explicit answers to:

- What counts as evidence?
    
- What is merely a proposal or prior?
    
- Who may update learner state?
    
- Who may choose an action?
    
- How do we know an intervention helped?
    
- What failures are unacceptable even when average prediction improves?
    

The most important decision is the separation

G≠dϕ≠bt,G \neq d_\phi \neq b_t,

where the authored hypergraph owns pedagogical structure, the embedding space supplies only metric neighborhoods, and the learner-specific field records uncertain beliefs over that shared structure. That avoids the common mistake of treating one opaque student embedding as topology, memory, diagnosis, and mastery simultaneously.

The other particularly strong choices are:

- **The blind-grader firewall.**
    
- **Vector arithmetic cannot create evidence.**
    
- **The deterministic router remains the authority.**
    
- **Cold, independent use is the main outcome rather than guided redo success.**
    
- **False remediation is a constraint, not merely another weighted cost.**
    
- **Simulation particles and LLM-authored hypotheses are never promoted into facts.**
    
- **Probes stop at repair equivalence rather than trying to reconstruct the learner’s entire mind.**
    

Those are unusually good architectural invariants. They protect LearnLoop from several failure modes that would otherwise appear only after deployment.

My main concern is no longer the conceptual direction. It is that the document is becoming a **large research program rather than a sharply executable implementation specification**. The A–I workstreams are individually coherent, but several boundaries still need to become explicit APIs before more models are added.

ACE-KT fits this architecture very well, but only in one particular role:

> **ACE-KT should become a calibrated temporal sensor over immutable learner events—not the learner state, not the Bayesian posterior, and not the router.**

That is almost exactly the slot your Workstream B already leaves open for a replayable GRU/SSM cache.

---

# What ACE-KT contributes

ACE-KT was accepted as an AISTATS 2026 poster. The authors describe a cascade with three stages:

1. A **Rhythm Perception Module**, implemented with convolution, to extract local or “pre-attentive” patterns.
    
2. A **Context Structuring Module**, implemented with a Transformer encoder, to capture relational and contextual dependencies.
    
3. A **Cognitive Integration Module**, implemented with an enhanced selective state-space model, to integrate information over longer temporal scales.
    

The authors report evaluation on five real-world datasets against 22 KT baselines. ([JNU Institute of Smart Education](https://ise.jnu.edu.cn/2026/0127/c32421a850450/page.htm "https://ise.jnu.edu.cn/2026/0127/c32421a850450/page.htm"))

The released implementation makes the mechanism more concrete:

causal local filter  ⟶  causal attention  ⟶  selective state-space update.\text{causal local filter} \;\longrightarrow\; \text{causal attention} \;\longrightarrow\; \text{selective state-space update}.

The first module uses a causal depthwise convolution to form a low-pass component and a residual high-pass component, with a learned weight on the latter. The second uses question embeddings as queries and keys while interaction embeddings provide values under a causal mask. The third is structurally Mamba-like: it computes input-dependent Δ,B,C\Delta,B,C parameters and performs a selective scan through time.

That ordering is genuinely useful for LearnLoop:

- **Local deviation:** Was this event a transient slip, hesitation, or abrupt strategy change?
    
- **Relational context:** Which previous events are relevant to interpreting this attempt?
    
- **Temporal integration:** What persistent state is consistent with the resulting history?
    

However, the cognitive terminology should be treated as an **inductive-bias metaphor**, not as proof that the three modules recover actual human cognitive stages. In the released code, ACE-KT is trained with binary cross-entropy to predict the next response and evaluated primarily by AUC and accuracy. It is therefore fundamentally an observational next-response predictor.

That distinction matters enormously for LearnLoop.

---

# ACE-KT does not solve all three modeling problems

Your revised system contains three different prediction problems that should not be conflated.

## 1. Prognostic prediction

P(Rt+1=1∣Ht,xt+1)P(R_{t+1}=1\mid H_t,x_{t+1})

Given the history and a future item, will the learner answer correctly?

This is what ordinary KT—and ACE-KT in its current form—primarily estimates.

## 2. Diagnostic observation likelihood

P(o∣h,q,Ht)P(o\mid h,q,H_t)

Assuming misconception or latent hypothesis hh, what response would we observe on probe qq?

This is what Workstream C needs for robust decision-EVSI. A generic correctness predictor does not provide hypothesis-conditioned likelihoods.

## 3. Intervention or transition effect

P(Ynext,Ycold,h′∣h,do⁡(a),Ht)P(Y_{\text{next}},Y_{\text{cold}},h' \mid h,\operatorname{do}(a),H_t)

What happens if LearnLoop gives a counterexample, worked example, prerequisite repair, probe, or no intervention?

This requires treatment variation, action propensities, delayed outcomes, and usually causal assumptions or randomization. Passive KT data cannot identify it merely because the temporal predictor is accurate.

The current plan already distributes these responsibilities sensibly:

- B estimates learner state.
    
- C calibrates observation likelihoods.
    
- E represents trajectory uncertainty.
    
- F performs decision-EVSI and routing.
    
- G learns intervention effectiveness only within certified near-ties.
    

ACE-KT should not collapse these layers back together. Its initial role should be almost entirely in the first category, with carefully restricted contributions to the second. The third should remain a separate action-conditioned model trained from LearnLoop’s propensity-logged and randomized data.

---

# The correct insertion point: B0.5, a temporal evidence sensor

I would revise the architecture as follows:

```text
observed learner response
        │
        ▼
blind grader + reveal/assistance ledger
        │
        ▼
immutable EvidencePacket ───────────────┐
        │                               │
        ├── A. trace retrieval          │
        │      selects relevant         │
        │      existing event IDs       │
        │                               │
        ├── B0. explicit ledger state   │
        │                               │
        └── B0.5 ACE-style temporal ────┘
                evidence sensor
                       │
                       ▼
             C. calibrated fusion
       explicit baseline + temporal sensor
                       │
                       ▼
       authoritative learner field b_t
                       │
                       ▼
       E. ambiguity/trajectory ensemble
                       │
                       ▼
        F. deterministic route comparator
       repair | ask | construct | defer
```

The temporal model should emit a typed object, not expose its hidden vector directly:

```text
TemporalEvidencePacketV1
  as_of_event_id
  target_region: (content, capability, representation)
  consumed_event_ids
  model_version
  feature_schema_version

  predicted_next_independent_success
  predicted_cold_success_by_horizon
  predicted_representation_transfer
  predicted_scaffold_dependence
  predicted_slip_or_transient_error
  predicted_response_signatures_by_probe_family
  misconception_scores_by_repair_equivalence_class

  effective_support
  density_or_ood_score
  epistemic_uncertainty
  calibration_key
  evidence_authority_tier
```

Several restrictions should be part of its type contract:

- It cannot write mastery or misconception state directly.
    
- It cannot increment `n_eff`.
    
- It cannot convert retrieved similarity into an observation.
    
- Every output must list the real event IDs it consumed.
    
- It cannot feed the blind grader.
    
- A raw recurrent hidden state never appears in `RouterStateV1`.
    
- It begins as an externally trained, population-level prior—roughly your authority tier 1—not calibrated empirical learner evidence.
    

That preserves the existing Workstream B principle that a recurrent state may exist as a reproducible cache but cannot become application-state authority by itself.

---

# How I would adapt the three ACE stages

## 1. Rhythm Perception becomes a local-deviation encoder

ACE-KT’s first stage distinguishes a smoothed local trajectory from short-lived fluctuations. For LearnLoop, that is useful for separating:

- persistent error from one-off slip;
    
- stable misconception from uncertain guessing;
    
- ordinary difficulty from an abrupt strategy failure;
    
- accumulating fluency from temporary assistance-induced success;
    
- meaningful recurrence from a noisy behavioral event.
    

But I would change two things.

### Use real elapsed time, not merely interaction index

The released implementation’s convolution runs over sequence position. A response yesterday and a response six months ago can therefore be adjacent in the same mathematical sense as two responses ten seconds apart.

LearnLoop has a reveal ledger and actual spacing information. Feed the elapsed time into the filter or into the SSM discretization:

Δ~t=softplus⁡(WΔxt+wτlog⁡(1+Δtt)).\widetilde{\Delta}_t = \operatorname{softplus} \left( W_\Delta x_t+ w_\tau \log(1+\Delta t_t) \right).

This gives the state-space model an explicit forgetting clock rather than asking it to infer one from item order.

### Use multiple temporal bands

Instead of one generic low/high-frequency decomposition, maintain at least three interpretable temporal channels:

- **Transient availability:** very recent priming, working context, or guided uptake.
    
- **Durable availability:** cold retrieval and retained procedural access.
    
- **Mechanism persistence:** whether a misconception or strategy continues to recur.
    

This maps much more cleanly onto your field dimensions than one hidden notion of “knowledge.”

The local encoder’s output should be called something like `recent_deviation_features`, not “cognitive rhythm.” That keeps the empirical claim appropriately narrow.

---

## 2. Context Structuring becomes target- and graph-conditioned attention

A conventional KT Transformer attends over a sequence of concept/response tokens. LearnLoop has much richer structure:

- exact facets and operations;
    
- capability and representation axes;
    
- prerequisite and composition edges;
    
- error mechanisms;
    
- first-divergence and delta-vs-canonical fields;
    
- assistance and reveal context;
    
- positive demonstrated-capability records;
    
- prior repair outcomes.
    

It would be wasteful and potentially harmful to attend indiscriminately over the learner’s entire history.

For target region x=(v,c,r)x=(v,c,r), first retrieve a causal event set

Ht(x)={ei:relevant⁡G(ei,x)  ∨  retrieved⁡A(ei,x)}.\mathcal H_t(x) = \left\{ e_i: \operatorname{relevant}_G(e_i,x) \;\lor\; \operatorname{retrieved}_A(e_i,x) \right\}.

Then run one small target-conditioned attention layer over that set. The mask should combine:

- temporal causality;
    
- exact graph relations;
    
- representation and assistance compatibility;
    
- typed retrieval filters;
    
- event validity intervals;
    
- evidence-authority restrictions.
    

The retrieved events are still real events. Retrieval merely chooses which event IDs the model sees; it does not increase their weight as independent evidence.

This is a particularly natural interaction between Workstreams A and B:

> A answers “which prior observations may be relevant?”  
> The contextual encoder answers “how does their configuration affect this prediction?”

The attention weights should be retained only as an attribution/debugging artifact. They are not causal explanations.

---

## 3. Cognitive Integration becomes a long-horizon state proposal

The selective SSM is probably the most valuable ACE component for LearnLoop. It supports:

- efficient incremental updates;
    
- long histories without recomputing full attention;
    
- input-dependent retention and forgetting;
    
- separate behavior under different event types;
    
- replay from the immutable event stream.
    

But I would not use one global state. Maintain either separate state banks or graph-indexed caches for:

(content region,capability,representation).(\text{content region},\text{capability},\text{representation}).

A practical compromise is not literally one SSM per graph node. Instead, use a shared SSM whose input and state updates are conditioned on the target region and whose cached summaries are materialized only for active/frontier regions.

For example:

mt(k)=A(k)(Δtt)mt−1(k)+B(k)(xt)et,m_t^{(k)} = A^{(k)}(\Delta t_t)m_{t-1}^{(k)} + B^{(k)}(x_t)e_t,

with

k∈{warm,cold,misconception,scaffold,transfer}.k\in \{ \text{warm}, \text{cold}, \text{misconception}, \text{scaffold}, \text{transfer} \}.

This makes the model plural in the same way the learner field is plural. It also reduces the temptation to interpret one hidden state as the learner’s “true understanding.”

---

# The most important extension: separate pre-action and post-action state

Standard KT consumes a question and response, updates the recurrent state, and predicts the next response. LearnLoop cannot use that formulation unchanged because a diagnostic interaction is simultaneously:

1. a **measurement** of the learner;
    
2. a **practice opportunity**;
    
3. a possible **hint or reveal**;
    
4. a stimulus that can alter strategy, confidence, or misconception state.
    

Every read can write.

The temporal model should therefore distinguish:

zt−=fθ(H<t),z_t^- = f_\theta(H_{<t}),

the predicted state immediately before action ata_t, from

zt+=Tθ(zt−,at,ot,reveal⁡t,assistance⁡t),z_t^+ = T_\theta \left( z_t^-, a_t, o_t, \operatorname{reveal}_t, \operatorname{assistance}_t \right),

the proposed post-interaction state.

The observation head is evaluated from the pre-action state:

Pθ(ot∣zt−,qt),P_\theta(o_t\mid z_t^-,q_t),

while the future-outcome heads are evaluated from the post-action state:

Pθ(Rnext,Rcold∣zt+,x).P_\theta(R_{\text{next}},R_{\text{cold}}\mid z_t^+,x).

This avoids two serious errors:

- using the learner’s answer to a probe as part of the state that supposedly predicted that same answer;
    
- treating a diagnostic question as a passive sensor whose only effect was revealing information.
    

It also provides an empirical counterpart to your theoretical joint kernel:

Ka(h′,o∣h).K_a(h',o\mid h).

ACE-KT supplies a good computational motif for representing the sequence, but LearnLoop’s contribution would be explicitly separating the **observation channel** from the **write/transition channel**.

---

# Do not double-count the temporal model and the explicit ledger

This is a subtle but critical issue.

The no-smoothing ledger estimate and ACE sensor both consume the same learner events. They are not independent observations. Therefore, LearnLoop must not do something like

P(h∣E)∝Pledger(h∣E)PACE(h∣E)P(h\mid E) \propto P_{\text{ledger}}(h\mid E) P_{\text{ACE}}(h\mid E)

as though the two models supplied independent likelihoods. That would count the same evidence twice.

Use one of two safer schemes.

## Calibrated stacking

Fit an out-of-fold calibrator:

p^=Cal⁡ψ(pledger,pACE,neff,OOD⁡,assistance,horizon).\widehat p = \operatorname{Cal}_{\psi} \left( p_{\text{ledger}}, p_{\text{ACE}}, n_{\text{eff}}, \operatorname{OOD}, \text{assistance}, \text{horizon} \right).

The calibrator learns when the temporal model adds predictive information beyond explicit counts, decay, and graph fields.

## Disagreement as ambiguity

Until the calibrator has enough data, treat the two estimators as members of an ambiguity set:

Cδ=Hull⁡{btledger,btACE,btparticle},\mathcal C_\delta = \operatorname{Hull} \left\{ b_t^{\text{ledger}}, b_t^{\text{ACE}}, b_t^{\text{particle}} \right\},

possibly expanded according to calibration error and support.

When they disagree near an action boundary, the result should be wider uncertainty, a discriminator, a common safe repair, or deferral—not an average that creates false confidence.

This is a direct operationalization of the plan’s semantic–behavioral disagreement alarm.

---

# How ACE should interact with each workstream

## A. Episodic trace memory

A provides the relevant event subset and factorized event representations. ACE consumes actual event IDs selected by A.

Good uses:

- retrieve same mechanism on different surfaces;
    
- retrieve positive capability demonstrations;
    
- retrieve representation-switch and scaffold histories;
    
- retrieve prior repairs with next/cold outcomes.
    

Forbidden use:

- interpreting a close neighbor as an additional successful or failed attempt.
    

The model should log both the complete causal prefix and the retrieved subset so a replay audit can detect sensitivity to retrieval changes. The plan’s immutable leaf-event design is exactly right for this.

## B. Learner field

ACE is a **sensor underneath B**, not a replacement for B.

`RouterStateV1` may eventually contain calibrated outputs such as:

- cold-success estimate and interval;
    
- transient-versus-persistent error score;
    
- scaffold-dependence estimate;
    
- transfer-risk estimate;
    
- model disagreement and OOD flags.
    

It should not contain `ace_hidden_state: float[256]`.

`LearnerStateCardV1` should render claims derived from the authoritative field and source events, not generate prose by decoding the recurrent vector.

## C. Calibration

C is the gate through which ACE earns any decision relevance.

The initially pretrained model belongs at authority tier 1: an externally trained population prior. It can become tier 2 after local shadow validation. It should not be called tier 3 unless the relevant horizon, item family, representation, assistance condition, and density region have enough calibrated empirical support.

Calibration should be stratified by:

- next versus cold horizon;
    
- assisted versus independent response;
    
- item/probe family;
    
- representation;
    
- transfer distance;
    
- support and OOD bucket;
    
- grader version and confidence.
    

## D. Evaluation

ACE-KT’s standard AUC/accuracy evaluation is insufficient for LearnLoop. The relevant evaluation should include:

- log loss and Brier score;
    
- calibration error and coverage;
    
- cold prediction by delay horizon;
    
- assisted-to-independent transfer;
    
- same-mechanism/new-surface generalization;
    
- same-answer/different-mechanism separation;
    
- `RepairFlipRate`;
    
- `StateWriteFlipRate`;
    
- finalized SS, diagnostic questions QQ, and false-remediation rate FF.
    

Your controlled-confound benchmark is especially important because a sequence model may appear to diagnose mechanisms while actually exploiting surface correlations.

## E. Trajectory ensemble

ACE can serve as an **amortized proposal distribution** for the particle filter:

qθ(ht∣Ht).q_\theta(h_t\mid H_t).

It can suggest likely particles or initialize their temporal components, reducing the number of expensive LLM-generated proposals.

But ACE must not score its own particles. Particle weights should still come from C’s calibrated real-observation likelihoods:

wt(j)∝wt−1(j)pcal(ot∣ht(j),qt)qθ(ht(j)∣Ht).w_t^{(j)} \propto w_{t-1}^{(j)} \frac{ p_{\text{cal}}(o_t\mid h_t^{(j)},q_t) }{ q_\theta(h_t^{(j)}\mid H_t) }.

That preserves the distinction between a fast proposal network and the observation-grounded posterior. It also prevents the same learned model from proposing, judging, and confirming its own latent story.

The W3 simulator should use separate parameters and evaluation from the ACE sensor. Shared architecture is fine; shared self-confirming state is not.

## F. Deterministic router

ACE can improve the router’s fixed observation vector, but cannot select the route itself.

It may contribute:

- estimated probability of independent success;
    
- estimated cold risk;
    
- probability that an error is transient;
    
- predicted probe-response distribution;
    
- action-boundary uncertainty;
    
- disagreement alarms.
    

The deterministic comparator still applies feasibility, safety, false-remediation, burden, reveal, and robust EVSI gates.

A generic ACE prediction P(correct∣H,q)P(\text{correct}\mid H,q) is not automatically the required P(o∣h,q)P(o\mid h,q). The latter needs a hypothesis-conditioned head or C’s pooled empirical cells. Early ACE use should therefore improve prognosis and state uncertainty before it is allowed to influence diagnostic likelihood arithmetic.

## G. Equipoise bandit

Calibrated ACE outputs can become context variables inside the certified near-tie bandit. Raw hidden states should not.

Suitable context variables include:

- cold-risk bucket;
    
- scaffold-dependence interval;
    
- misconception persistence;
    
- representation-transfer history;
    
- support/OOD;
    
- recent volatility.
    

This keeps experimentation interpretable and makes off-policy evaluation less fragile.

## H. Shared–private alignment

The ACE cascade creates useful candidate views:

- local behavioral deviations from the convolutional stage;
    
- structural/semantic relations from contextual attention;
    
- temporal persistence from the SSM;
    
- explicit graph coordinates;
    
- LLM-authored semantic diagnoses.
    

Your decision-conditioned shared/private alignment idea fits naturally here. Align these views only when they induce similar repair-regret profiles. Preserve private coordinates when they help prediction, explanation, or OOD detection.

## I. Hypergraph authority

Use authoritative graph edges as attention priors or sparse masks. Use uncertain authored edges as soft biases. Do not infer a new prerequisite graph from ACE attention.

The direction of authority should remain:

G⟶ACE context bias,G \longrightarrow \text{ACE context bias},

not

ACE attention⟶certified G.\text{ACE attention} \longrightarrow \text{certified }G.

---

# An ACE-Lite architecture is probably better than importing ACE-KT unchanged

The released defaults use two cascaded blocks, 256-dimensional representations, four attention heads, and sequences up to 200 interactions.

For LearnLoop’s sparse, heterogeneous, n=1 product setting, I would begin with:

- one cascade block;
    
- d=64d=64 or 128128;
    
- a causal convolution over the most recent 8–16 relevant events;
    
- one target-conditioned attention layer over the top 16–32 typed events;
    
- one small selective SSM;
    
- separate warm, cold, scaffold, transfer, and mechanism heads;
    
- actual elapsed-time features;
    
- cached incremental inference.
    

The full ACE version should be an ablation, not the default assumption.

The most important comparisons are likely:

1. Explicit ledger/decayed logistic baseline.
    
2. Small GRU.
    
3. SSM only.
    
4. Convolution + SSM.
    
5. Attention + SSM.
    
6. Full ACE-Lite cascade.
    
7. Graph-conditioned ACE-Lite.
    
8. Graph-conditioned, action-aware ACE-Lite.
    

I would also ablate TeLU against SiLU rather than assuming the custom activation is load-bearing. The released implementation exposes independent switches for the convolutional, Transformer, SSM, and TeLU components, which makes this straightforward.

---

# LearnLoop-specific training objectives

The current ACE loss is next-response binary cross-entropy. LearnLoop should use a multi-task objective, but only where each target has genuine authority:

Lsensor=λnextLnext+λcoldLcold+λtransferLtransfer+λassistLassist+λsignatureLresponse-signature+λmechanismLmechanism+λcalLcalibration+λinvLdecision-invariance.\begin{aligned} \mathcal L_{\text{sensor}} ={}& \lambda_{\text{next}}\mathcal L_{\text{next}} +\lambda_{\text{cold}}\mathcal L_{\text{cold}}\\ &+\lambda_{\text{transfer}}\mathcal L_{\text{transfer}} +\lambda_{\text{assist}}\mathcal L_{\text{assist}}\\ &+\lambda_{\text{signature}}\mathcal L_{\text{response-signature}} +\lambda_{\text{mechanism}}\mathcal L_{\text{mechanism}}\\ &+\lambda_{\text{cal}}\mathcal L_{\text{calibration}} +\lambda_{\text{inv}}\mathcal L_{\text{decision-invariance}}. \end{aligned}

## Next-use head

Predict the first eligible fresh, independent attempt after the action. Do not train it on guided redos or isomorphic repetitions.

## Cold head

Predict success as a function of delay. Missing cold outcomes are censored, not failures. A survival or discrete-time hazard loss is more appropriate than ordinary BCE over a fabricated negative label.

## Transfer head

Predict performance on the same facet/capability under:

- a new surface;
    
- a new representation;
    
- a larger transfer distance;
    
- reduced scaffolding.
    

This is closer to “understanding” than same-item correctness.

## Assistance-dependence head

Distinguish:

- independent success;
    
- hint-assisted success;
    
- worked-example uptake;
    
- same-session priming;
    
- cold, unassisted recovery.
    

## Response-signature head

Predict exact or canonicalized response signatures where datasets provide them. This is the first bridge from generic KT toward C’s diagnostic likelihoods.

## Mechanism head

Train only from expert labels, externally anchored misconception data, or planted examples that pass the independent future-behavior gate. Do not use posterior particles as labels.

## Decision-invariance loss

Use the controlled-confound benchmark:

- same mechanism, different surface → similar repair-regret profile;
    
- same answer, different mechanism → different repair-regret profile when the repairs differ.
    

This is more aligned with LearnLoop than forcing generic embedding similarity.

---

# Action-effect learning must remain separate

The temporal sensor may eventually be extended to predict action-conditioned transitions:

μ^a(x)=E[Ycold∣X=x,do⁡(A=a)].\widehat \mu_a(x) = E[Y_{\text{cold}}\mid X=x,\operatorname{do}(A=a)].

But that head should be commissioned only after you have:

- action identifiers;
    
- action capability metadata;
    
- logged propensities;
    
- eligibility and feasibility records;
    
- next and cold outcomes;
    
- sufficient overlap between actions;
    
- equipoise randomization where ethical and safe.
    

Without that information, the model learns the historical policy’s selection biases:

> “Learners who received prerequisite repair did worse” may mean the repair failed, or merely that prerequisite repair was reserved for the hardest cases.

Use a separate causal outcome head with doubly robust or equivalent estimators. Do not backpropagate ordinary observational next-response loss and then reinterpret the result as a repair effect.

This preserves the clean boundary:

- **ACE sensor:** What state and risk are consistent with observed history?
    
- **C response model:** What would each hypothesis predict on a probe?
    
- **G/action model:** Which admissible intervention works for learners in this context?
    
- **F router:** What should be done now under uncertainty and safety constraints?
    

---

# A revised online algorithm

At event tt:

1. **Blindly grade the response.** Produce correctness, valid-alternative status, rubric-level observations, and grader confidence without exposing learner hypotheses.
    
2. **Compile one immutable `EvidencePacket`.** Include response, first divergence, delta-vs-canonical, item contract, assistance, reveal history, latency, edits, confidence, and exact event ID.
    
3. **Append it to the ledger and trace index.** No derived model may overwrite the event.
    
4. **Select relevant prior events.** Exact graph relations and typed filters first; semantic retrieval second.
    
5. **Compute the explicit B0 state.** Counts, cold demonstrations, recurrence groups, support, missingness, and reveal-aware statistics.
    
6. **Run the temporal sensor.**
    
    - local-deviation encoder;
        
    - target-conditioned contextual layer;
        
    - selective temporal integration;
        
    - typed predictive heads.
        
7. **Calibrate and reconcile.** Combine the explicit baseline and ACE outputs through an out-of-fold calibrator or ambiguity envelope. Disagreement increases uncertainty.
    
8. **Update the authoritative field.** Every update references the underlying event IDs and its algorithm/calibration version.
    
9. **Generate and lock hypotheses.** Include `h_other`, compile executable signatures, and cluster by repair equivalence.
    
10. **Evaluate the four routes.** Common safe repair, ask existing probe, construct a better probe, or defer.
    
11. **Serve the deterministic choice.** Randomize only inside G’s certified near-tie set.
    
12. **Join future outcomes.** First fresh independent attempt gives provisional `R_next`; delayed cold retrieval finalizes `R_cold`.
    
13. **Update calibration and action-effect models.** Never retroactively rewrite the decision-time state snapshot.
    

This is compatible with the current route-comparator and outcome contract.

---

# How I would change the sequencing

The current sequence correctly puts instrumentation, immutable trace memory, deterministic state, and the four-route comparator before learned policy components.

I would insert two ACE-related stages rather than making it one large new workstream:

### After B0: define the sensor contract

**2.5 — `TemporalEvidencePacketV1` and shadow feature extraction**

Implement:

- action/reveal-aware event tokens;
    
- consumed-event provenance;
    
- pre-action/post-action separation;
    
- actual elapsed-time features;
    
- baseline predictions and outcome joins.
    

No trained model needs authority yet.

### After C and E1: train the sensor

**5.5 — ACE-Lite temporal sensor in shadow**

Train and compare it against explicit and simple temporal baselines. E1’s controlled-confound suite is necessary before trusting a flexible sequence model.

### Before E2 promotion: use as proposal only

Let ACE initialize or propose particles, but continue weighting them with C’s calibrated likelihoods.

### Before B1 promotion: compare smoothers

Compare:

- no-smoothing B0;
    
- graph-kernel B1;
    
- ACE-Lite temporal sensor;
    
- calibrated combination;
    
- robust disagreement envelope.
    

This avoids implementing both a GP field and a recurrent field merely because each is theoretically attractive. The data should tell you whether they add distinct value.

---

# The minimum viable vertical slice

Before building all of A–I, I would require one end-to-end demonstration containing:

- one vault or narrow subject;
    
- a small authored facet/capability graph;
    
- one repair-equivalence boundary;
    
- two or three plausible mechanisms plus `h_other`;
    
- one existing discriminator;
    
- one constructable discriminator;
    
- two repair families;
    
- fresh next-use measurement;
    
- one delayed cold audit;
    
- explicit S,Q,FS,Q,F receipts.
    

Then compare:

1. Current deterministic policy.
    
2. Current policy plus trace recurrence.
    
3. Current policy plus explicit `RouterStateV1`.
    
4. Current policy plus ACE temporal sensor in shadow.
    
5. Current policy plus calibrated ACE features.
    

That experiment will reveal whether the cascade reduces meaningful uncertainty or merely improves conventional next-response prediction.

---

# The strongest potential research contribution

The most interesting research direction is not “apply ACE-KT to LearnLoop.” It is:

## **Cascaded learner-state estimation for state-changing diagnostic interactions**

The novelty would be that standard KT models a sequence

(qt,rt)→(qt+1,rt+1),(q_t,r_t)\rightarrow(q_{t+1},r_{t+1}),

whereas LearnLoop models

(ht,at)⟶(ot,ht+1),(h_t,a_t) \longrightarrow (o_t,h_{t+1}),

with:

- noisy observation;
    
- contemporaneous instructional write effects;
    
- assistance and reveal contamination;
    
- multiple time horizons;
    
- repair-equivalence rather than exact-state identification;
    
- decision-conditioned evaluation;
    
- causal action effects;
    
- open-world hypotheses.
    

An empirical paper could contribute:

1. An ACE-style local/contextual/temporal cascade over rich tutoring events.
    
2. Explicit pre-action versus post-action state.
    
3. Joint observation/write modeling.
    
4. Cold and transfer supervision instead of only next-response accuracy.
    
5. Decision-conditioned mechanism generalization.
    
6. Evaluation by intervention regret, learner burden, and false remediation.
    
7. A controlled benchmark where surface and mechanism correlations are deliberately broken.
    

That would pair extremely well with your theoretical “decision-revealing active measurement in state-changing systems” direction. The theory establishes when a measurement is decision-sufficient; the temporal model estimates the practical state and transition quantities needed by the decision rule.

---

# The exact change I would make to the brainstorm document

I would add this under Workstream B:

> **B0.5 — Cascaded temporal evidence sensor, shadow-only.** A population-trained, replayable temporal encoder may summarize immutable event histories using a local-deviation module, target/graph-conditioned contextual module, and selective state-space integrator. It emits only typed, calibrated proposals—next-use risk, cold-risk by horizon, scaffold dependence, transfer risk, transient-error probability, candidate response-signature distributions, support, uncertainty, and OOD—together with all consumed event IDs and artifact versions. Its hidden state is never learner-state authority, never enters the blind grader, never increments evidence counts, and never selects a route. Because the explicit ledger and temporal encoder consume overlapping events, their outputs are combined only through held-out calibration or a conservative disagreement envelope, never as independent likelihood factors. The model first earns authority as a router sensor by improving finalized SS or reducing QQ without crossing τF\tau_F, including on controlled surface–mechanism confound breaks.

I would also alter the “permanently out” language from:

> population KT models in the loop

to:

> population KT models are prohibited as learner-state or routing authority; population-trained temporal encoders may operate as calibrated, replayable sensors under the same evidence and product gates.

That is the important distinction. ACE-KT should not become the new center of LearnLoop, but its **cascade is probably the best temporal-sensor design you have considered so far**. It complements the revised architecture precisely because the architecture is strong enough to prevent a capable predictor from quietly turning into an unjustified model of the learner’s mind.

One source limitation: OpenReview served a browser-verification page rather than the PDF contents in this environment, so I have deliberately not quoted unverified numerical result tables. The paper description above is cross-checked against the official AISTATS listing, the authors’ institutional abstract, and the released implementation. ([OpenReview](https://openreview.net/submissions?page=4&venue=aistats.org%2FAISTATS%2F2026%2FConference "https://openreview.net/submissions?page=4&venue=aistats.org%2FAISTATS%2F2026%2FConference"))</Agent>

<User>Which parts of learnloop based on the Pipeline Augmentation Plan do you think we should and have the data to train a GRU/SSM or learned feature from? How much additional data would we feasibly need? Are there any high ROI bitter-lesson pilled learned/computation+data features we could add to our pipeline augmentation plan?</User>

<Agent>Yes. Looking at the current Pipeline Augmentation Plan plus the more specific learner-field addendum, I think LearnLoop is actually **underusing learned features in a few places where we already have abundant objective labels**, while correctly being conservative in places where the labels would mostly be LLM-generated or causally confounded.

The highest-ROI direction is not “replace the symbolic/Bayesian architecture with a neural learner model.” It is:

> **Pretrain relatively small predictive models on millions of externally available interactions, use them to produce learned features/residuals, and keep the deterministic/causal machinery as the authority layer.**

That is fairly “bitter lesson” compatible: let computation and data learn the ugly predictive functions that are difficult to hand-engineer, while retaining hard structure only where the problem actually requires guarantees, provenance, or causal semantics.

The current internal dataset plan already points in this direction: it identifies FoundationalASSIST as the source for a frozen GRU/SSM behavioral residual and response prior, EdNet for forgetting dynamics, Eedi for confidence calibration, and MTM for tutor-action representations. The learner-field addendum goes even further and explicitly proposes a bounded recurrent residual, a learned retention lane, and a separate action-effect model.

## What I think we can train **right now**

I would divide this by whether we have a real supervised target.

|Learned component|Train now?|Available data|Model I'd start with|Confidence|
|---|--:|--:|---|---|
|**Fresh-item correctness residual**|**Yes**|1.7M FoundationalASSIST + large KT corpora|64–128d GRU → SSM challenger|Very high|
|**Exact response / distractor distribution**|**Yes**|1.7M FoundationalASSIST exact first answers; Eedi exact choices|GRU/SSM + response head|Very high|
|**Time/forgetting representation**|**Yes**|131M EdNet + timestamps elsewhere|parametric hazard + GRU/SSM residual|Very high|
|**Behaviorally grounded item embedding**|**Yes**|millions–100M+ interactions|two-tower / contrastive embedding|Very high|
|**Confidence/correctness mismatch feature**|**Yes**|Eedi ~15.9M responses with confidence|calibration model / tiny MLP|Very high|
|**Transient-slip / sequence anomaly feature**|**Mostly**|derived from above sequences|recurrent residual / surprise head|High|
|**Scaffold-dependence predictor**|**Predictively yes**|FoundationalASSIST hints + answer reveal|GRU/MLP head|High|
|**Recurrence / response-signature representation**|**Yes-ish**|exact answers + Eedi misconception data + ConceptKT|contrastive encoder|Medium-high|
|**Tutor-move embedding**|**Yes**|4,654 MTM transcripts + tutor-move taxonomy|text encoder + sequence encoder|High|
|**Repair-effect model**|**Not causally yet**|observational tutoring data insufficient|later state-space/uplift model|Low now|
|**Probe-value model**|**Weak supervision now**|generated/offline labels possible|small ranker|Medium|
|**Learned router**|**No**|not enough randomized decision data|don't do yet|Low|

The remarkable thing is how much public data there now is. FoundationalASSIST alone has **1,722,169 interactions from 5,000 students**, including full question text, exact first answers, hints and answer reveals. ([arXiv](https://arxiv.org/abs/2602.00070 "https://arxiv.org/abs/2602.00070")) Eedi's 2020 release has roughly **15.9M interactions from 119k students**, including per-response confidence. ([GitHub](https://github.com/leemoomoo/SSM/blob/main/doc/dataset/Eedi_2020_Task1%262.md "https://github.com/leemoomoo/SSM/blob/main/doc/dataset/Eedi_2020_Task1%262.md")) And EdNet contains **131.4M interactions from 784k students**. ([PubMed Central (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/ "https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/"))

That is vastly more data than a 50K–500K parameter GRU/SSM needs to learn useful population-level dynamics.

---

# 1. The thing I would train first: a behavioral foundation sensor

Not a foundation model in the LLM sense. Something much smaller.

Define an event:

et=[item features,concept,correctness,response,latency,hint,reveal,Δt,representation,difficulty,…].e_t = [ \text{item features}, \text{concept}, \text{correctness}, \text{response}, \text{latency}, \text{hint}, \text{reveal}, \Delta t, \text{representation}, \text{difficulty}, \ldots ].

Then train

ht=fθ(ht−1,et)h_t = f_\theta(h_{t-1},e_t)

using either:

- small GRU;
    
- small selective SSM;
    
- ACE-style convolution → attention → SSM only if it beats the simpler models.
    

But critically, **do not ask it to learn one scalar “mastery.”**

Give it many easy-to-obtain prediction targets:

L=λ1Lnext-correct+λ2Lexact-response+λ3Ltime-to-next+λ4Lhint-use+λ5Lfuture-correct+λ6Lcross-surface+λ7Lconfidence.\mathcal L = \lambda_1 L_{\text{next-correct}} +\lambda_2L_{\text{exact-response}} +\lambda_3L_{\text{time-to-next}} +\lambda_4L_{\text{hint-use}} +\lambda_5L_{\text{future-correct}} +\lambda_6L_{\text{cross-surface}} +\lambda_7L_{\text{confidence}}.

The hidden representation becomes a learned behavioral feature vector.

Then LearnLoop asks the model questions such as:

P(fresh success∣Ht,x)P(\text{fresh success}\mid H_t,x)

rather than:

> “What is this student's true understanding?”

That's much more defensible.

### We have enough data already.

A 128-dimensional GRU with perhaps 200–500K parameters trained on 1.7M interactions is not data-starved.

With EdNet + Eedi, it is extremely far from data-starved.

I would actually worry more about **domain mixture and shortcut learning** than sample quantity.

---

# 2. A learned **behavioral item embedding** may be even higher ROI

This is an addition I would explicitly make to the plan.

Right now dϕd_\phi is predominantly semantic: an embedding tells you that two questions _mean similar things_.

But millions of student responses allow us to learn a second geometry:

zqbehaviorz_q^{\text{behavior}}

where two items are close when they produce similar patterns of:

- success/failure;
    
- distractor choices;
    
- learner-specific residuals;
    
- forgetting;
    
- confidence;
    
- transfer;
    
- hint dependence.
    

Think collaborative filtering/recommender systems, except the users are learners and the items are learning objects.

For example:

P(yuq=1)=σ(zu⊤zq+bq+bu)P(y_{uq}=1) = \sigma( z_u^\top z_q+ b_q+ b_u )

is already enough to learn surprising structure.

A richer two-tower model could learn:

zq=gθ(text,facet,representation,behavioral history).z_q = g_\theta( \text{text}, \text{facet}, \text{representation}, \text{behavioral history} ).

Then explicitly retain:

zqsem,zqbeh.z_q^{sem}, \qquad z_q^{beh}.

Their disagreement is useful.

If two questions are semantically nearly identical but have radically different behavioral profiles, **that is signal**.

Conversely, questions far apart semantically may expose the same latent capability.

This feels very bitter-lesson aligned: rather than deciding manually what every difficulty axis ought to be, let hundreds of millions of interactions discover predictive dimensions.

Recent KT work continues to find value from representations derived from student–question–concept interaction graphs, including behaviorally pretrained question embeddings. ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0020025525011995 "https://www.sciencedirect.com/science/article/pii/S0020025525011995"))

### Data requirement

Already satisfied.

Even FoundationalASSIST alone is enough to try it. Eedi and EdNet make it substantially stronger.

---

# 3. Learned **future-behavior embeddings** for error traces

This is the version of EduEmbed I now find more compelling than simply fine-tuning embeddings on LLM-generated misconception labels.

Instead of asking:

> “Do these two answers have the same semantic misconception label?”

learn:

> “Do these two response traces predict similar future learner behavior?”

Let a trace encoder produce

zi=fθ(responsei,itemi,contexti).z_i=f_\theta(\text{response}_i,\text{item}_i,\text{context}_i).

Train positive pairs when the learner subsequently shows similar patterns across:

- same facet/new surface;
    
- same representation/new item;
    
- delayed retrieval;
    
- transfer;
    
- response selection.
    

Negative pairs can specifically include:

- same wrong answer but different subsequent behavior;
    
- same surface but different future trajectory.
    

Something like

Lfuture-contrast=−log⁡exp⁡(sim⁡(zi,zj+)/τ)∑kexp⁡(sim⁡(zi,zk)/τ).L_{\text{future-contrast}} = -\log \frac{ \exp(\operatorname{sim}(z_i,z_j^+)/\tau) }{ \sum_k\exp(\operatorname{sim}(z_i,z_k)/\tau) }.

This gives us a representation grounded in **what happens next**, rather than what an LLM says the mistake means.

That is exactly the kind of feature I'd expect a bitter-lesson approach to uncover better than hand taxonomy design.

Eedi's misconception labels and ConceptKT can remain evaluation sets rather than the sole source of supervision.

---

# 4. Learned **surprise and state-change features**

These are almost free once the sequence model exists, and I think they're extremely high ROI for the router.

Suppose the temporal model predicts:

pt=Pθ(yt∣Ht−1,xt).p_t=P_\theta(y_t\mid H_{t-1},x_t).

An event gives us:

### Predictive surprise

St=−log⁡Pθ(yt∣Ht−1,xt).S_t=-\log P_\theta(y_t\mid H_{t-1},x_t).

### Residual

rt=yt−pt.r_t=y_t-p_t.

### Hidden-state movement

Δht=∥ht−ht−1∥.\Delta h_t = \|h_t-h_{t-1}\|.

### Model disagreement

Dt=∣pexplicit−pGRU∣.D_t = |p_{\text{explicit}}-p_{\text{GRU}}|.

### Ensemble uncertainty

Ut=Var⁡mpm.U_t=\operatorname{Var}_m p_m.

These are arguably better features than several manually engineered flags currently going into `state_signals.py`.

For example:

- wrong answer with p=0.51p=0.51: unsurprising;
    
- wrong answer with p=.98p=.98: potentially important;
    
- wrong answer causing huge Δh\Delta h: unusual learner event;
    
- explicit model says .90 but behavioral model says .35: model misspecification / transfer issue / hidden context.
    

I would give these directly to `RouterStateV1` as **sensors**, not evidence.

That requires no additional labeling whatsoever.

---

# 5. Forgetting / cold-risk model: train this now too

The current plan already correctly unparked EdNet for precisely this reason.

I would first learn:

P(Rt+Δ=1∣Ht,Δ,item features)P(R_{t+\Delta}=1\mid H_t,\Delta,\text{item features})

with a survival/hazard formulation or explicit time-conditioned head.

A reasonable hybrid is:

logit⁡pcold=β⊤x−α(x)log⁡(1+Δt)+rθ(Ht,Δt).\operatorname{logit}p_{\text{cold}} = \beta^\top x - \alpha(x)\log(1+\Delta t) + r_\theta(H_t,\Delta t).

So the model learns a flexible residual but is forced toward a sane prior.

EdNet's 131M timestamped interactions are ideal for learning generic temporal shapes. ([PubMed Central (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/ "https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/"))

### But there is an important distinction.

EdNet can teach:

> “What generic temporal patterns predict forgetting?”

It cannot teach LearnLoop's exact definition of:

> first eligible fresh independent cold audit after reveal contamination.

For that, we need LearnLoop data.

### Rough local-data targets

I would consider:

- **500–1,000 matured cold observations:** enough for crude calibration;
    
- **2,000–5,000:** useful horizon-stratified recalibration;
    
- **10,000+ matured cold observations:** enough to meaningfully fine-tune a small cold head;
    
- **50,000+:** enough to study meaningful interactions between representation × facet × assistance × interval.
    

Those are approximate engineering thresholds, not statistical laws.

---

# 6. Confidence mismatch is practically free

Eedi is unusually valuable here because its dataset contains per-response confidence at huge scale. ([GitHub](https://github.com/leemoomoo/SSM/blob/main/doc/dataset/Eedi_2020_Task1%262.md "https://github.com/leemoomoo/SSM/blob/main/doc/dataset/Eedi_2020_Task1%262.md"))

Instead of treating learner confidence manually, learn:

P(correct∣confidence,history,item,latency,...)P(\text{correct}\mid \text{confidence}, \text{history}, \text{item}, \text{latency}, ...)

and especially

P(recurring misconception∣wrong,confidence,Ht).P(\text{recurring misconception}\mid \text{wrong},\text{confidence},H_t).

The distinction:

- **wrong + low confidence**
    
- **wrong + high confidence**
    

is pedagogically meaningful, but the strength of that distinction should be learned rather than hand-coded.

A tiny calibration model probably requires only thousands of interactions, and we have millions.

---

# 7. Scaffold dependence: predictive model now, causal model later

FoundationalASSIST records hints and `saw_answer`. ([Hugging Face](https://huggingface.co/martinakaduc/FoundationalASSIST "https://huggingface.co/martinakaduc/FoundationalASSIST"))

So we can train features such as:

P(independent future success∣current success with assistance)P(\text{independent future success} \mid \text{current success with assistance})

versus

P(independent future success∣current independent success).P(\text{independent future success} \mid \text{current independent success}).

That's useful immediately.

But we should **not** infer:

effect of hint\text{effect of hint}

simply by comparing learners who asked for hints to learners who didn't.

That's confounded.

So I'd distinguish:

### trainable now

`predicted_scaffold_dependence`

### requires LearnLoop randomization

`causal_effect_of_scaffold`

---

# 8. Action representations: yes. Action effects: not yet.

MTM v1 currently has **4,654 authentic math tutoring transcripts**, which is enough to learn an initial sequence representation of tutoring actions but not enough by itself to establish treatment effects. ([Pith](https://pith.science/paper/2605.08092 "https://pith.science/paper/2605.08092")) The NTO's Tutor Move Taxonomy supplies a structured action vocabulary. ([arXiv](https://arxiv.org/abs/2603.05778 "https://arxiv.org/abs/2603.05778"))

So train:

ca=fθ(action text,move type,context)c_a=f_\theta(\text{action text},\text{move type},\text{context})

now.

This lets similar actions pool:

> contrastive counterexample about domain restrictions

and

> example illustrating when the theorem fails

might have nearby action embeddings.

That's much better than treating every generated intervention as a completely novel arm.

But this:

E[Rcold∣do⁡(a)]E[R_{\text{cold}}\mid \operatorname{do}(a)]

needs your own treatment/outcome data.

---

# What data do we need before training the **repair-effect model**?

This is where the biggest gap is.

We need tuples roughly like:

(xt,at,pt,Rnext,Rcold)(x_t,a_t,p_t,R_{\text{next}},R_{\text{cold}})

where:

- xtx_t = decision-time learner state;
    
- ata_t = actual repair;
    
- ptp_t = action propensity;
    
- RnextR_{\text{next}} = next independent outcome;
    
- RcoldR_{\text{cold}} = delayed outcome.
    

The current plan wisely already logs exactly these sorts of receipts.

My rough data ladder would be:

### ~1,000 intervention episodes

Enough to debug the pipeline and estimate coarse average effects of a handful of action families.

Not enough for personalization.

### ~5,000–10,000

Enough for a hierarchical effect model across perhaps 5–10 broad repair families if action assignment has decent overlap.

Could start shadow predictions.

### ~20,000–50,000

Now a learned action-effect state-space model becomes genuinely interesting:

θa,t+1=Fθa,t+ϵt.\theta_{a,t+1}=F\theta_{a,t}+\epsilon_t.

Could model interactions like:

- misconception family × action;
    
- scaffold dependence × action;
    
- representation × action;
    
- learner history × action.
    

### 100,000+

Now I would seriously investigate learned personalized treatment effects and more flexible policy learning.

But the relevant quantity isn't merely total NN.

You need **support per decision boundary**.

100,000 examples where worked examples were always given to novices and counterexamples always to experts is much worse for effect estimation than 15,000 well-overlapped/equipoise assignments.

---

# A useful rule of thumb for LearnLoop

There are really four data regimes:

### Regime A: labels are naturally free

Examples:

- correctness;
    
- exact answer;
    
- time;
    
- hint usage;
    
- confidence;
    
- next response;
    
- repeat performance.
    

**Learn aggressively.**

Millions of examples already exist.

### Regime B: labels require deterministic bookkeeping

Examples:

- fresh vs familiar;
    
- independent vs assisted;
    
- cold audit;
    
- recurrence;
    
- representation transfer.
    

**Build logging first, then learn fairly early.**

Thousands–tens of thousands suffice.

### Regime C: labels require human/expert semantic judgment

Examples:

- precise misconception mechanism;
    
- first divergence;
    
- valid alternative;
    
- repair equivalence.
    

**Use learned models as proposal/ranking systems.**

Don't make them authoritative.

### Regime D: labels require counterfactuals

Examples:

- “Would counterexample have worked better than worked example?”
    
- “Did this probe cause learning?”
    
- “Was this prerequisite review necessary?”
    

**No amount of passive next-response data solves these.**

Need randomization, overlap, IV assumptions, etc.

This distinction should probably become explicit in the Pipeline Augmentation Plan.

---

# The highest-ROI “bitter lesson” addition: pretrain one multi-domain Student Dynamics Encoder

Rather than training:

- one forgetting model;
    
- one correctness model;
    
- one scaffold model;
    
- one recurrence model;
    
- one exact-response model;
    

I would seriously test a **shared event encoder + temporal backbone + multiple heads**.

Something like:

et=EventEncoder⁡(qt,rt,text,skill,assistance,Δt,...)e_t = \operatorname{EventEncoder} ( q_t, r_t, \text{text}, \text{skill}, \text{assistance}, \Delta t, ... ) ht=SSM/GRU⁡(ht−1,et)h_t=\operatorname{SSM/GRU}(h_{t-1},e_t)

then:

y^correct=g1(ht,q),y^response=g2(ht,q),y^cold(Δ)=g3(ht,q,Δ),y^hint=g4(ht,q),y^confidence=g5(ht,q),y^transfer=g6(ht,q′).\begin{aligned} \hat y_\text{correct}&=g_1(h_t,q),\\ \hat y_\text{response}&=g_2(h_t,q),\\ \hat y_\text{cold}(\Delta)&=g_3(h_t,q,\Delta),\\ \hat y_\text{hint}&=g_4(h_t,q),\\ \hat y_\text{confidence}&=g_5(h_t,q),\\ \hat y_\text{transfer}&=g_6(h_t,q'). \end{aligned}

Pretrain across:

- FoundationalASSIST;
    
- Eedi;
    
- EdNet;
    
- perhaps Junyi and other KT corpora.
    

Put dataset/domain embeddings in the input.

Do **leave-one-dataset-out transfer evaluation**.

If a feature survives domain transfer, I trust it far more than a model that simply memorizes question IDs.

This could give LearnLoop something analogous to a small **student dynamics foundation model**, perhaps only tens of megabytes.

That is much more bitter-lesson-ish than crafting a separate mathematical functional form for every behavioral phenomenon.

---

# Another addition: self-supervised masked-event pretraining

Most of the public interactions do not have the exact labels LearnLoop wants.

But they have sequences.

So train things like:

### Masked event reconstruction

Hide:

- correctness;
    
- response;
    
- time gap;
    
- skill;
    
- assistance.
    

Predict them from surrounding history.

### Next-event prediction

P(et+1∣e≤t).P(e_{t+1}\mid e_{\le t}).

### Contrastive learner-state prediction

Two prefixes from the same learner nearby in time should be distinguishable from random learners, but we shouldn't force one global stable learner embedding.

### Future-window prediction

Predict aggregate behavior over:

[t+1,t+k].[t+1,t+k].

This gives the recurrent model richer representation-learning supervision than next-answer BCE alone.

EdNet's 131M interactions make this computationally cheap relative to LLM training and data-rich enough to meaningfully scale. ([PubMed Central (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/ "https://pmc.ncbi.nlm.nih.gov/articles/PMC7334672/"))

---

# A potentially very strong feature: learned **counterfactual separability**

Before administering a proposed probe qq, you currently use mal-procedure execution to see whether hypotheses produce different signatures.

I would add a learned estimator:

sθ(q,hi,hj)≈P(responses distinguish hi,hj).s_\theta(q,h_i,h_j) \approx P(\text{responses distinguish }h_i,h_j).

This doesn't replace EVSI.

It's a **cheap screening model**.

Training examples can be generated massively offline:

(q,hi,hj,predicted traces)(q,h_i,h_j,\text{predicted traces})

using the existing hypothesis execution framework.

Then expensive LLM execution or robust EVSI is performed only on the top candidates.

This is quintessential computation-scaling:

1. Generate millions of synthetic candidate probes offline.
    
2. Evaluate them using your expensive executable-hypothesis machinery.
    
3. Distill that into a cheap ranker.
    
4. Use the ranker at runtime.
    
5. Keep the exact verifier as authority.
    

Same basic pattern as AlphaZero/search distillation, reward models, theorem-prover guidance, etc.

I think this should be added to F.

---

# The same applies to **construction**

Currently the construction path invokes an LLM to generate a useful discriminator.

Over time, save:

(belief state,hi,hj,generated probe,valid?,ASNR,actual response,actual decision flip)( \text{belief state}, h_i,h_j, \text{generated probe}, \text{valid?}, \text{ASNR}, \text{actual response}, \text{actual decision flip} )

Then train:

Vθ(q∣b,hi,hj)V_\theta(q\mid b,h_i,h_j)

as a **probe critic**.

Eventually:

- LLM generates 32 probes;
    
- cheap learned critic ranks them;
    
- formal/domain verifier checks top 3;
    
- EVSI evaluates top 1–3;
    
- learner sees one.
    

More compute at generation time, less learner burden.

That is exactly where the bitter lesson should manifest in LearnLoop.

---

# What I would _not_ bitter-lesson away

There are several places where “just learn it” is wrong because the issue isn't prediction difficulty.

I would keep these explicit:

- evidence provenance;
    
- reveal/freshness ledger;
    
- false-remediation constraint;
    
- authored graph edge authority;
    
- repair-equivalence semantics;
    
- admissibility;
    
- route feasibility;
    
- propensity logging;
    
- causal interpretation;
    
- `h_other`;
    
- deterministic router envelope;
    
- cold-audit definition.
    

These are more analogous to the rules of the game than features within a model.

Chess programs learned evaluation and search policy; they didn't learn whether bishops are allowed to move diagonally from game outcomes.

---

# My revised learned-components stack

I'd now make the Pipeline Augmentation Plan look approximately like:

```text
                    IMMUTABLE EVENT LOG
                           │
              ┌────────────┼──────────────┐
              │            │              │
              ▼            ▼              ▼
        semantic       behavioral     temporal
        encoder         item model      model
       frozen/FT       learned from    GRU/SSM
                          responses
              │            │              │
              └───── learned sensors ─────┘
                           │
      ┌────────────────────┼─────────────────────┐
      ▼                    ▼                     ▼
 surprise/residual    cold-risk            response prior
 OOD/disagreement     forgetting           exact-response
 recurrence feature   transfer risk        confidence
      │                    │                     │
      └───────── calibrated RouterState ─────────┘
                           │
                    authoritative b_t
                           │
             executable hypotheses + EVSI
                           │
        ┌──────────────────┼────────────────────┐
        ▼                  ▼                    ▼
 learned probe       learned action       LLM generation
 candidate ranker    representation       / construction
        │                  │                    │
        └──── deterministic verification ───────┘
                           │
                     SAFE ROUTER
                           │
                    action + receipt
                           │
                 next/cold outcomes
                           │
              causal action-effect learner
                   [only once enough data]
```

---

# Concrete data roadmap

If I were prioritizing collection, I'd set these milestones:

|Data accumulated inside LearnLoop|What I would unlock|
|--:|---|
|**0**|Public-data GRU/SSM; behavioral item embedding; generic forgetting; Eedi confidence model|
|**500–1k fresh/cold outcomes**|basic calibration and sanity checks|
|**2k–5k cold audits**|LearnLoop-specific forgetting calibration|
|**5k diagnostic episodes**|first learned probe-quality/ranking model|
|**10k–20k intervention episodes with propensities**|coarse repair-family effect model in shadow|
|**20k–50k**|contextual repair effects, action embeddings become useful for pooling|
|**50k–100k+**|serious personalized CATE/effect SSM and offline policy-learning experiments|
|**much larger + genuine overlap**|consider learned policy components within safe envelope|

I wouldn't treat those numbers as hard thresholds—the effective sample size depends enormously on action balance and repeated learners—but they're reasonable engineering targets.

And importantly, you don't need **10,000 interactions from one person**. The neural network is population-trained. A new learner may become meaningfully personalized after **10–30 interactions**, and increasingly so after 30–100, because we're updating a latent state under a model whose weights were learned from millions of other interactions.

---

## So, what would I add to the plan?

My highest-priority additions would be, in order:

1. **Multi-task Student Dynamics Encoder** — GRU baseline, selective SSM challenger, trained across public datasets.
    
2. **Behavioral item/trace embeddings learned from future response patterns**, alongside—not replacing—semantic embeddings.
    
3. **Learned surprise/residual/disagreement/state-change features** as router sensors.
    
4. **Future-behavior contrastive trace encoder** rather than relying primarily on LLM misconception pseudo-labels.
    
5. **Distilled probe-separability/probe-value critic** trained from massive offline executable-hypothesis simulations.
    
6. **Learned action capability embedding** pretrained on MTM/tutor dialogue.
    
7. Later, **propensity-aware action-effect model** trained on actual LearnLoop outcomes.
    
8. Much later, policy-learning—but only inside your certified feasible/near-tie envelope.
    

The first five are particularly attractive because they let us spend arbitrary offline computation and public data **without gambling with a learner**. They turn expensive inference, human-designed heuristics, or hand-engineered similarities into learned proposal functions while keeping the verifier/router intact.

That strikes me as the right synthesis of the bitter lesson with the unusually safety- and evidence-conscious structure you already built into LearnLoop.</Agent>

<User>What are your thoughts about adapting something similar to the few shot robotics model approach of things like GEN-1.5 where they continuously fine tune a base model to do OOD tasks after seeing an example once? Could we  use this approach to make learned features more domain/canonical source agnostic? Or to make our other learned features more extensible? </User>

<Agent>Yes. I think a **GEN-1.5-like fast-adaptation layer may be one of the more important additions to the learned side of LearnLoop**, especially if the goal is to stop every learned component from implicitly becoming “the math model trained on FoundationalASSIST.”

There is one useful correction to the analogy. GEN-1.5’s most striking one-shot behavior does **not** update weights: a 3–12 second demonstration is inserted into context as a “physical prompt.” Separately, it can adapt with 1–10 gradient steps using roughly 1–5 minutes/10–50 demonstrations. Generalist reports 59% average success for one-shot prompting and 83% after 10 gradient steps; even those 10 steps move the pretrained weights by less than 0.15%. They interpret this as specialization of capabilities already latent in the pretrained model rather than learning a representation from scratch. ([Generalist AI](https://generalistai.com/blog/gen-1.5 "https://generalistai.com/blog/gen-1.5"))

That distinction gives us almost exactly the architecture I would want.

# The LearnLoop analogue: specialization after generalization

Instead of having

one frozen KT model→every possible subject,\text{one frozen KT model} \rightarrow \text{every possible subject},

I would have four distinct objects:

θbase,aD,hu,t,bu,t\boxed{ \theta_{\rm base},\quad a_D,\quad h_{u,t},\quad b_{u,t} }

where:

θbase=population-pretrained learner/content dynamics\theta_{\rm base} = \text{population-pretrained learner/content dynamics} aD=fast adapter for canonical source/domain Da_D = \text{fast adapter for canonical source/domain }D hu,t=recurrent predictive state for learner uh_{u,t} = \text{recurrent predictive state for learner }u

and

bu,t=authoritative replayable LearnLoop learner field.b_{u,t} = \text{authoritative replayable LearnLoop learner field}.

The last distinction is essential. aDa_D tells the learned model **how this source/domain should be interpreted**. hu,th_{u,t} tells the learned model **what this learner's history predicts**. Neither becomes evidence authority; btb_t remains the object governed by the Pipeline Augmentation Plan. That is compatible with the current rule that a GRU/SSM can provide bounded predictive residuals without owning learner state.

I would call the new mechanism something like **Source-Conditioned Fast Adaptation**.

---

## What is a "physical prompt" for LearnLoop?

A physical demonstration tells GEN-1.5:

> This is what “do the task” means in this environment.

For LearnLoop, a **canonical demonstration** could tell the student-dynamics model:

> This is what concepts, questions, valid performance, representations, and capability distinctions look like in this source.

For example, when ingesting a completely new organic chemistry textbook, give the learned sensor a small support set such as

```text
canonical source excerpts
       +
concept/facet/capability definitions
       +
question → verified solution
       +
question → canonical reasoning trace
       +
representation / assistance metadata
       +
a few observed learner interactions, when available
```

Call that

SD={s1,…,sK}.S_D=\{s_1,\ldots,s_K\}.

Then condition all learned features on

aD=Aϕ(SD).a_D = A_\phi(S_D).

The crucial point is that AϕA_\phi can initially be a **support-set encoder rather than SGD**.

So with one example:

aD=Aϕ(s1)a_D=A_\phi(s_1)

and the weights never change.

This is much closer to GEN-1.5's one-shot physical prompting.

Once we accumulate, say, 10–50 trustworthy domain examples, we can additionally run a few gradient steps:

aDk+1=aDk−η∇aDLD,a_D^{k+1} = a_D^k-\eta\nabla_{a_D} \mathcal L_D,

while keeping

θbase\theta_{\rm base}

frozen.

That gives us GEN-1.5's second regime.

---

# I would **not** continually fine-tune the whole GRU/SSM

This is probably the most important implementation choice.

A naive version would be:

> New biology event arrives → SGD on the Student Dynamics Model → new physics event arrives → SGD again...

I would strongly avoid this.

Continual test-time adaptation has well-known problems with accumulated pseudo-label error and catastrophic forgetting; the 2026 CTTA survey identifies both as central deployment failure modes. ([arXiv](https://arxiv.org/abs/2607.08164 "https://arxiv.org/abs/2607.08164"))

Instead:

```text
                   broad pretrained θ
                          │
                    [never mutated
                     online globally]
                          │
             ┌────────────┼────────────┐
             │            │            │
        Calculus      Mandarin      Biology
        adapter       adapter       adapter
           a₁            a₂            a₃
             │
             ▼
       learner-specific
       recurrent state hᵤ,t
             │
             ▼
        typed sensors
             │
             ▼
        authoritative bₜ
```

A bad biology update cannot destroy the calculus representation.

And every adapter is:

- tiny;
    
- versioned;
    
- reversible;
    
- rebuildable;
    
- source-scoped.
    

That is extremely compatible with LearnLoop's provenance philosophy.

---

# Where I think fast adaptation would help most

|Learned component|GEN-style adaptation potential|What adapts|
|---|--:|---|
|**Behavioral item embedding**|**Excellent**|mapping of novel content → shared behavioral geometry|
|**GRU/SSM behavioral residual**|**Excellent**|input projection + prediction heads|
|**Exact-response prior**|**Excellent**|source-specific answer/signature decoder|
|**Trace/error embedding**|**Excellent**|metric for what constitutes similar behavior in this source|
|**Probe separability critic**|**Excellent**|what makes a good discriminator in this source|
|**Probe-generator critic**|**Excellent**|source-specific item validity/informativeness|
|**Difficulty calibration**|**Excellent**|tiny source-level intercept/residual|
|**Confidence calibration**|Good|source/task-specific calibration|
|**Cold/forgetting dynamics**|Moderate|mostly calibration; temporal core should transfer broadly|
|**Action capability embedding**|Good|semantic meaning of repairs in a new domain|
|**Repair causal effect**|Poor one-shot candidate|needs actual intervention/outcome data|
|**Hypergraph authority**|Should not adapt this way|remains explicit evidence/authoring problem|
|**Router itself**|Should not adapt this way|remains deterministic authority|

The first five are particularly interesting.

---

# 1. This could solve a big problem with the behavioral embedding

Earlier I proposed learning both

zqsemanticz_q^{\rm semantic}

and

zqbehavioral.z_q^{\rm behavioral}.

The obvious problem with zqbehavioralz_q^{behavioral} is cold start.

A new topology textbook arrives. It has zero student interactions.

How do we know where its questions sit in behavioral space?

Currently we'd need something approximately like

zqbehavioral=fθ(text)z_q^{behavioral} = f_\theta(\text{text})

and hope that semantic information predicts behavioral structure.

Fast source adaptation gives us something stronger:

zqbehavioral=fθ(q,CD;aD),z_q^{behavioral} = f_\theta(q,C_D;a_D),

where CDC_D is canonical source context.

Initially:

aD=Aϕ(canonical examples).a_D=A_\phi(\text{canonical examples}).

Then after one real response:

aD(1)=U(aD,e1).a_D^{(1)} = U(a_D,e_1).

Then ten:

aD(10)=U(aD,e1:10).a_D^{(10)} = U(a_D,e_{1:10}).

The representation gradually transitions from

> “What should this problem behave like given everything learned from other domains?”

to

> “How do problems from this particular source actually behave?”

That seems much more powerful.

---

# 2. Make the GRU/SSM's **dynamics universal and its interfaces adaptive**

This is probably the architecture I would test first.

Don't let one biology example modify the SSM's entire model of learning dynamics.

Instead factor:

xt→  Eθ,aD  et→  Fθ  ht→  Gθ,aD  y^.x_t \xrightarrow{\;E_{\theta,a_D}\;} e_t \xrightarrow{\;F_\theta\;} h_t \xrightarrow{\;G_{\theta,a_D}\;} \hat y.

Here:

- EE turns a source-specific observation into a shared event language.
    
- FF learns generic temporal learner dynamics.
    
- GG maps the generic state back into source-specific predictions.
    

Make **EE and GG rapidly adaptable**.

Keep **FF** largely frozen.

That is a much stronger inductive assumption:

> The way a probability question and a Mandarin tone exercise are represented differs substantially; some underlying patterns such as forgetting, repeated error, assistance dependence, confidence mismatch, surprise, and practice effects are more transferable.

Not perfectly universal, of course. But it gives us a testable factorization.

Adapters could be extremely small:

aD∈R64a_D \in \mathbb R^{64}

with FiLM-style modulation

e~=γ(aD)⊙e+β(aD),\tilde e = \gamma(a_D)\odot e+\beta(a_D),

or tiny LoRAs on the input/output projections.

That means a few examples don't have to estimate hundreds of thousands of parameters.

---

# 3. We should explicitly train the base model to be fast-adaptable

GEN-1.5 claims this emerged from scaling without a meta-learning objective. Generalist says its model had been continuously pretrained for over eight months and progressively became more data-efficient at adapting to novel tasks; eventually even one gradient step became useful. ([Generalist AI](https://generalistai.com/blog/gen-1.5 "https://generalistai.com/blog/gen-1.5"))

There is now broader evidence for this “specialization after generalization” phenomenon. An ICLR 2026 analysis argues that test-time training can specialize a broad pretrained representation around the relatively small subset of concepts relevant to the current task. ([ICLR Proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/e1cd1db6fcd4a6df8618259f5b9cca0f-Abstract-Conference.html "https://proceedings.iclr.cc/paper_files/paper/2026/hash/e1cd1db6fcd4a6df8618259f5b9cca0f-Abstract-Conference.html")) And the ICML 2025 test-time-training work found that a few training examples can outperform leaving the same examples purely in context on structurally novel tasks. ([Proceedings of Machine Learning Research](https://proceedings.mlr.press/v267/akyurek25a.html "https://proceedings.mlr.press/v267/akyurek25a.html"))

But LearnLoop does **not** have GEN-1.5-scale proprietary pretraining.

So I wouldn't wait for fast adaptation to emerge.

I would explicitly meta-train it.

For every training episode, sample an entire source/domain DD:

D∼p(D).D\sim p(D).

Split it into

SD=support setS_D=\text{support set}

and

QD=query set.Q_D=\text{query set}.

Then optimize:

θ∗=arg⁡min⁡θED[LQD(Uϕ(θ,SD))].\theta^* = \arg\min_\theta E_D \left[ L_{Q_D} \left( U_\phi(\theta,S_D) \right) \right].

Critically, hold out the **entire canonical source** at evaluation.

Not merely unseen questions from the same dataset.

Something like:

```text
TRAIN:
algebra textbook A
algebra textbook B
geometry
statistics
biology
physics
...

TEST:
entire unseen calculus source
```

Give the model:

```text
0 demonstrations
1 demonstration
4 demonstrations
16 demonstrations
32 demonstrations
```

and plot adaptation curves.

That directly measures the capability we actually care about.

---

# Canonical-source diversity may matter more than raw interaction count

There is a subtle bitter-lesson implication here.

Suppose we can choose between:

100M interactions from one platform100\text{M interactions from one platform}

or

20M interactions across 100 very different domains/sources.20\text{M interactions across 100 very different domains/sources}.

For learning this particular capability, I'd strongly value the latter.

The model has to experience **changes in what a domain looks like** in order to learn what is invariant.

This has been observed quite broadly in domain-generalization research; controlled CLIP experiments at ICML 2025 found domain diversity to be crucial for unseen-domain and compositional generalization. ([Proceedings of Machine Learning Research](https://proceedings.mlr.press/v267/kempf25a.html "https://proceedings.mlr.press/v267/kempf25a.html"))

And this is already becoming a recognized KT problem. Conventional ID-based KT models transfer badly. A WWW 2026 paper, DTransKT, explicitly attacks cross-disciplinary transfer using semantic information and cross-domain representation alignment, reporting improvements across transferred KT backbones. ([DOI](https://doi.org/10.1145/3774904.3792501 "https://doi.org/10.1145/3774904.3792501")) A very recent cold-question KT study likewise found that replacing ID-only question representations with textual semantic embeddings particularly helped on unseen questions. ([MDPI](https://www.mdpi.com/2076-3417/16/17/8351 "https://www.mdpi.com/2076-3417/16/17/8351"))

I'd push considerably further than those methods:

> **Train the learner model itself to treat the source as a support-set-defined task.**

---

# The canonical source gives us a special advantage robotics does not have

A robot gets one demonstration because collecting robot trajectories is expensive.

When LearnLoop receives a new canonical source, we can manufacture enormous amounts of **verified self-supervision** before a single learner arrives.

Suppose the user imports Axler's _Linear Algebra Done Right_.

From the canonical source we can cheaply create training tasks such as:

source span→which item belongs here?\text{source span}\rightarrow\text{which item belongs here?} question→retrieve supporting source span\text{question}\rightarrow\text{retrieve supporting source span} question→verified answer\text{question}\rightarrow\text{verified answer} question1,question2→same capability?\text{question}_1,\text{question}_2 \rightarrow \text{same capability?} surface variant→representation invariance\text{surface variant} \rightarrow \text{representation invariance} generated question→canonical verifier accept/reject.\text{generated question} \rightarrow \text{canonical verifier accept/reject}.

This data is legitimate for adapting **content representations** because it is grounded in the canonical source.

What it cannot teach us is:

P(learner gets this wrong)P(\text{learner gets this wrong})

or

E[repair effect].E[\text{repair effect}].

Those still require actual learner behavior.

So I'd split the source adapter:

aD=(aDcontent,aDbehavior).a_D = (a_D^{content},a_D^{behavior}).

Immediately after ingestion, we can estimate

aDcontenta_D^{content}

very well.

Initially

aDbehavior≈0a_D^{behavior} \approx 0

or comes from the population prior.

As learner evidence arrives, the behavioral adapter gets updated.

This is another place where your shared/private alignment idea becomes extremely useful.

---

# One-shot **learner** adaptation should probably not use SGD

There's another level of the analogy.

Could an individual learner's first interaction act like a physical prompt?

Absolutely.

But rather than update neural weights, I would use:

hu,1=Fθ(h0,e1)h_{u,1}=F_\theta(h_0,e_1)

plus perhaps a small Bayesian/fast personalization vector

ru.r_u.

For example,

p(y=1)=σ(fθ(ht,q)+ru⊤zq).p(y=1) = \sigma( f_\theta(h_t,q)+r_u^\top z_q ).

Give rur_u a strong prior:

ru∼N(0,λ−1I).r_u\sim\mathcal N(0,\lambda^{-1}I).

One observation performs an exact Bayesian or ridge-style update.

That is essentially **fast weights with mathematically controlled uncertainty**.

So we get three different types of adaptation:

aD⏟what is this domain?,hu,t⏟what has this learner done?,ru⏟how does this learner systematically differ?.\underbrace{a_D}_{\text{what is this domain?}} ,\quad \underbrace{h_{u,t}}_{\text{what has this learner done?}} ,\quad \underbrace{r_u}_{\text{how does this learner systematically differ?}}.

This is far cleaner than continually fine-tuning a model separately for every student.

---

# Probe generation may be the sleeper application

Suppose LearnLoop encounters an entirely new subject.

The generic probe critic has learned abstract principles like:

- hold irrelevant factors fixed;
    
- make competing hypotheses predict different outputs;
    
- avoid answer leakage;
    
- use an independently gradable response;
    
- minimize learner burden.
    

But what constitutes a useful discriminator in abstract algebra is very different from Chinese pronunciation.

A canonical demonstration could adapt the critic:

Vθ(q,hi,hj,CD;aD)V_\theta(q,h_i,h_j,C_D;a_D)

after seeing just a few verified examples of:

(hypothesis pair,good discriminator,bad discriminator).(\text{hypothesis pair}, \text{good discriminator}, \text{bad discriminator}).

And here we can generate **lots** of training data without spending learner attention.

For a new source:

```text
LLM generates 1,000 candidate discriminators
        ↓
canonical-source verifier
        ↓
mal-procedure execution
        ↓
ASNR / separability calculation
        ↓
source-specific probe-critic adaptation
```

Then runtime becomes:

```text
generate 32
↓
cheap adapted critic ranks them
↓
verify top 3
↓
decision-EVSI
↓
serve 1
```

That is very GEN-like: broad competence plus tiny task-specific specialization.

It is also very bitter-lesson aligned.

---

# What I would make source-adaptive versus source-invariant

A useful decomposition is

f(x,D)=finvariant(x)+ΔfaD(x).f(x,D) = f_{\rm invariant}(x) + \Delta f_{a_D}(x).

The base should learn generic concepts like:

surprise,  recurrence,  forgetting,  assistance dependence,  response uncertainty.\text{surprise},\; \text{recurrence},\; \text{forgetting},\; \text{assistance dependence},\; \text{response uncertainty}.

The fast adapter should learn things like:

what counts as a difficult distinction here,\text{what counts as a difficult distinction here}, which semantic features matter in this source,\text{which semantic features matter in this source}, what response shapes are meaningful,\text{what response shapes are meaningful}, how source-specific representations map to capabilities.\text{how source-specific representations map to capabilities}.

This is also why I think **shared + private representations** are preferable to aggressive domain invariance.

A domain-agnostic representation isn't necessarily one where domain information has been erased.

It is one where the model knows:

> which dimensions should generalize and which should specialize.

That is more consistent with the shared/private alignment direction already in the plan than trying to collapse biology and calculus into the same vector space.

---

# I would use three adaptation speeds

This is the design I'd actually add.

### **Fastest: canonical prompting — zero gradient**

At ingestion or inference:

aDctx=Aϕ(SD).a_D^{ctx}=A_\phi(S_D).

One/few examples.

Ephemeral, safe, immediately reversible.

This is the closest GEN-1.5 analogue.

### **Fast: source adapter — 1–10 gradient steps**

After perhaps 8–50 verified examples:

aD←aD−η∇LD.a_D\leftarrow a_D-\eta\nabla L_D.

Only adapters/input-output projections change.

The base temporal model remains frozen.

Persistent, versioned, rollbackable.

### **Slow: global consolidation**

Periodically collect successful source adaptations from many domains and continue pretraining

θbase.\theta_{\rm base}.

Only offline.

Evaluate on completely held-out domains before promotion.

Over time the amount of source-specific adaptation required should fall, just as Generalist reports task adaptation becoming progressively cheaper as its base model scales. ([Generalist AI](https://generalistai.com/blog/gen-1.5 "https://generalistai.com/blog/gen-1.5"))

This creates a really attractive positive feedback loop:

new domain→fast adaptation→real outcomes→offline consolidation→better universal prior→less adaptation for next domain.\text{new domain} \rightarrow \text{fast adaptation} \rightarrow \text{real outcomes} \rightarrow \text{offline consolidation} \rightarrow \text{better universal prior} \rightarrow \text{less adaptation for next domain}.

---

# Guardrails matter much more for LearnLoop than robotics

I would make the fast-update contract unusually strict.

A source adapter can train on verified source semantics freely.

A behavioral adapter should only train on high-authority observations such as independent graded responses.

No gradient should ever come directly from:

LLM says learner has misconception h.\text{LLM says learner has misconception }h.

Otherwise our own hypotheses literally reshape the representation that later “confirms” them.

Likewise, every adaptation should preserve a frozen reference model and enforce something like

DKL(pθ,aD∥pθ,0)<ϵD_{KL} \left( p_{\theta,a_D} \Vert p_{\theta,0} \right) <\epsilon

outside the supported neighborhood.

And updates should pass a held-out source anchor suite before promotion.

One of the intriguing observations in GEN-1.5 is actually relevant here: Generalist reports that **lighter adaptation sometimes preserves more improvisational generalization**, presumably because the model remains closer to its broad pretrained prior. ([Generalist AI](https://generalistai.com/blog/gen-1.5 "https://generalistai.com/blog/gen-1.5"))

That's precisely the behavior we'd want.

Don't overfit LearnLoop's model to five calculus questions and lose the generic learning dynamics it acquired from millions of interactions.

---

# Data requirements become much more attractive under this formulation

We wouldn't need thousands of student responses before a new canonical source becomes useful.

I'd target roughly:

|Source evidence|Adaptation|
|--:|---|
|**0 learner examples**|canonical-source context + source-generated self-supervision|
|**1–4**|in-context/support-set conditioning; Bayesian calibration only|
|**8–32**|tiny source adapter starts becoming plausible|
|**32–100**|few-step behavioral input/head adaptation|
|**100–500**|meaningful source-specific calibration and hard-negative mining|
|**1k+**|consider source-specific temporal residuals|
|**many sources × many interactions**|consolidate improvements into base|

And the key research metric becomes an **adaptation curve** rather than one AUC:

performance(K),K∈{0,1,4,16,64,256}.\text{performance}(K), \qquad K\in\{0,1,4,16,64,256\}.

I'd want to know:

> How many examples does LearnLoop require before an entirely unseen source reaches 95% of its in-domain asymptotic performance?

That's a much better measure of extensibility.

---

# This could become a surprisingly coherent research direction

I think the architecture would become:

General learner dynamics+canonical-source prompting+few-step source specialization+online learner state\boxed{ \textbf{General learner dynamics} + \textbf{canonical-source prompting} + \textbf{few-step source specialization} + \textbf{online learner state} }

rather than

one KT model per dataset.\text{one KT model per dataset}.

There is already active work attacking the same underlying problem: cross-disciplinary KT, cold-question generalization, and cross-platform prediction all identify platform/question-ID dependence as a fundamental limitation. ([DOI](https://doi.org/10.1145/3774904.3792501 "https://doi.org/10.1145/3774904.3792501"))

But I'd make the LearnLoop objective stronger:

> **Can a pretrained learner-dynamics model ingest an unseen canonical source, infer the source-specific task representation from a handful of grounded demonstrations, and immediately produce calibrated behavioral features whose remaining error falls rapidly with each real learner event?**

That's very close conceptually to the capability GEN-1.5 is showing for physical tasks, but with an advantage robotics doesn't have: canonical sources let us perform extensive grounded source-specific adaptation before collecting expensive human behavioral labels.

So yes—I would add this to the Pipeline Augmentation Plan. More specifically, I'd change the GRU/SSM proposal from **“one frozen population residual model”** to **“a frozen/general population backbone with source-conditioned fast adapters and explicit K-shot adaptation evaluation.”** The frozen model would remain the baseline/fallback, while the adapter would have to earn its predictive authority source-by-source. That would make essentially every learned feature we're contemplating far less hostage to FoundationalASSIST/Eedi's particular content distribution.</Agent>

<User>We have datasets like FoundationalAssist but how do we know that a model that learned from 6th-8th grade math students will transfer well to students learning arxiv papers or linear algebra or other undergraduate/graduate level topics or any technical topic? Modern LLMs have massive pretraining which makes them well-equipped to handle most tasks pretty well (like how the backbone frontier LLM was able to identify student's mistakes pretty well just through prompting) whereas I fear that training learned models on these datasets that aren't entirely reflective of the domain question complexity might not be sufficiently transferrable to be better than just querying a frontier LLM. What sort of direction do you think I should move forward in? I want to use learned features when possible, use existing datasets as much as they can contribute, and play to the strengths of the frontier LLMs as much as possible. Compiling enough unique learnloop data is very difficult since cold retrieval inherently makes it very lengthy to test (wait 7 days), which we could augment with synthetic data from LLM personas who can act out counterfactuals. Would you revise any of your recommendations for learned features based on this unsure transfer? Out of all the learned features what do you think would have the highest ROI and highest transfer/generalizability across any canonical source or practice item card that the user might intend to learn? </User>

<Agent>Your concern is correct, and I would revise my earlier recommendation in a meaningful way:

> **Do not make a GRU/SSM pretrained on FoundationalASSIST the default learner model. Make the frontier LLM the semantic foundation, and let smaller learned models estimate only bounded, empirically testable residuals over its outputs and the explicit event ledger.**

There is currently no convincing evidence that a sequence model trained on middle-school mathematics will improve predictions for someone reading a new arXiv paper, constructing a proof in linear algebra, debugging a research implementation, or learning an unfamiliar technical vocabulary. Existing “cross-domain” KT evidence is much narrower than that phrase suggests. For example, DGKT transfers among ASSISTments, Junyi, and Algebra datasets and still performs target-domain fine-tuning; this does not establish transfer from school exercise behavior to open-ended graduate learning. ([arXiv](https://arxiv.org/html/2407.02547v2 "https://arxiv.org/html/2407.02547v2")) NTKT obtains strong unseen-question performance by retaining full question text and pretrained language representations, but its authors explicitly acknowledge that its evidence comes from English mathematics and provides little hard evidence about genuinely multi-domain transfer. ([arXiv](https://arxiv.org/html/2511.02599v1 "https://arxiv.org/html/2511.02599v1"))

That distinction strongly favors a hybrid architecture.

# Why a frontier LLM and a KT model have different comparative advantages

A frontier LLM has broad priors over:

- mathematical and scientific language;
    
- proofs, derivations, code, diagrams, and explanations;
    
- what operations a question requires;
    
- what a canonical source says;
    
- plausible misconceptions;
    
- whether two items are structurally analogous;
    
- how a response diverges from a reference solution;
    
- how to generate a new diagnostic or repair.
    

A small GRU trained on school mathematics has none of that semantic coverage. It can only learn statistical regularities present in its event representation and training population.

But the frontier LLM is not automatically good at:

- maintaining a reproducible longitudinal learner state;
    
- estimating calibrated frequencies from behavioral data;
    
- distinguishing persistent individual patterns from plausible narratives;
    
- remembering reveal and assistance history exactly;
    
- fitting forgetting curves;
    
- producing stable probabilities across model or prompt versions;
    
- estimating treatment effects;
    
- preventing repeated evidence from being double-counted.
    

FoundationalASSIST itself illustrates this division. Its authors evaluated LLM predictions of correctness and exact answer, but avoided treating LLM output as a reliable latent-mastery estimate, distinguishing surface-level constructs from harder latent constructs. ([arXiv](https://arxiv.org/html/2602.00070v1 "https://arxiv.org/html/2602.00070v1"))

The right synthesis is therefore:

frontier LLM for semantics+explicit ledger for evidence+small learned models for calibration and temporal residuals+deterministic/robust router for authority\boxed{ \text{frontier LLM for semantics} + \text{explicit ledger for evidence} + \text{small learned models for calibration and temporal residuals} + \text{deterministic/robust router for authority} }

That is already latent in the Pipeline Augmentation Plan: the LLM handles semantic compression, zero-shot proposal, and open-world expansion, while the surrounding system supplies memory, calibration, belief, provenance, and ground truth.

# The revised model architecture

I would implement a **foundation-model semantic layer with a bounded statistical residual**, rather than an independent KT model attempting to understand every domain.

## 1. The LLM compiles every source and event into a common typed language

At source ingestion:

ziitem=ΦLLM(canonical source,item,verified solution).z_i^{\text{item}} = \Phi_{\text{LLM}} ( \text{canonical source}, \text{item}, \text{verified solution} ).

The output is not just an embedding. It is a structured object containing fields such as:

```text
ItemContractV1
  canonical_source_spans
  content_facets
  prerequisite_facets
  required_operations
  capability_type
  representation_type
  solution_strategy
  solution_steps
  expected_response_form
  possible first-divergence points
  transfer_distance
  assistance_level
  verification_method
```

At response time, the blind grader produces:

```text
ObservedResponseV1
  correctness
  valid_alternative_status
  first_divergence
  delta_from_canonical
  demonstrated_operations
  omitted_operations
  response_signature
  grader_confidence
  ambiguity_flags
```

Using large language models to derive knowledge-component structure from educational content has already shown promise across multiple benchmark domains, including settings where manually defined components are missing. ([arXiv](https://arxiv.org/html/2409.20167v1 "https://arxiv.org/html/2409.20167v1"))

This is where the broad pretraining of the frontier LLM should do most of the work.

## 2. The ledger records what actually happened

The ledger contributes:

- correctness;
    
- exact response;
    
- latency;
    
- edits;
    
- hints;
    
- answer reveal;
    
- confidence before feedback;
    
- retries;
    
- item familiarity;
    
- elapsed time;
    
- immediate and delayed outcomes;
    
- exact source-event IDs.
    

These are facts, not model interpretations.

## 3. A small learned model processes the typed sequence

The GRU/SSM does not receive opaque question IDs and try to infer linear algebra from school mathematics. It receives a source-grounded semantic representation constructed by the LLM plus behavioral metadata:

et=[ztitem,ztresponse,correctness,assistance,reveal,confidence,latency percentile,Δt,…].e_t= [ z_t^{\text{item}}, z_t^{\text{response}}, \text{correctness}, \text{assistance}, \text{reveal}, \text{confidence}, \text{latency percentile}, \Delta t, \ldots ].

It then estimates a bounded residual:

rθ(Ht,x)r_\theta(H_t,x)

over an explicit or LLM-derived baseline.

A practical combination is:

p^=Cal⁡ψ(pLLM,pexplicit,rθ,nsupport,OOD⁡,source family).\widehat p = \operatorname{Cal}_{\psi} \left( p_{\text{LLM}}, p_{\text{explicit}}, r_\theta, n_{\text{support}}, \operatorname{OOD}, \text{source family} \right).

The learned component should be support-gated:

reffective=gsupport(x)⋅clip⁡(rθ,−ρ,ρ),r_{\text{effective}} = g_{\text{support}}(x) \cdot \operatorname{clip}(r_\theta,-\rho,\rho),

where

gsupport(x)→0g_{\text{support}}(x)\rightarrow 0

when the model is far outside its validated training support.

For a new arXiv paper, the system initially falls back almost entirely to:

- canonical-source grounding;
    
- the frontier LLM;
    
- explicit observations;
    
- conservative uncertainty.
    

As real events accumulate, the statistical residual may gradually earn weight.

This is a better interpretation of the learner-field addendum’s proposed frozen GRU/SSM residual: the recurrent model is a bounded predictive sensor, not a universal cognitive model.

# What FoundationalASSIST can and cannot teach us

I would keep FoundationalASSIST, but substantially narrow the claims attached to it.

## Reasonably transferable lessons

It may help initialize models of:

- how response sequences contain information beyond the latest answer;
    
- how hints and answer reveals alter evidence reliability;
    
- how recent success differs from repeated independent success;
    
- how exact responses add information beyond correctness;
    
- how time gaps interact with future performance;
    
- how confidence and behavioral history should be combined;
    
- how to encode variable-length interaction histories;
    
- how to regularize a small recurrent residual;
    
- how much simple temporal models tend to overfit item or learner IDs.
    

These are candidate invariants, not guaranteed invariants.

## Things it should not teach as production truth

I would not transfer its estimates of:

- absolute item difficulty;
    
- absolute learner ability;
    
- forgetting rates for graduate technical material;
    
- misconception prevalence;
    
- typical error mechanisms;
    
- effects of hints or worked examples;
    
- relation between response time and knowledge;
    
- typical learning rate;
    
- value of specific repairs;
    
- what constitutes mastery of proof, synthesis, or paper comprehension.
    

A sixth-grade arithmetic problem and an arXiv-paper comprehension question differ not only in subject matter but in the underlying response process. An advanced learner may spend 25 minutes on a question and understand it deeply; a school-platform model might interpret that latency as struggle. A correct proof can be generated through several valid strategies, while many KT datasets reduce behavior to a binary or multiple-choice response.

So FoundationalASSIST should be treated as:

pretraining and regularization data,\text{pretraining and regularization data},

not as

the population model of LearnLoop users.\text{the population model of LearnLoop users}.

# I would split learned features into content-facing and learner-facing models

This gives a clearer priority order.

## Content-facing learned features

These operate on the canonical source, items, solutions, hypotheses, probes, and repairs. They do not need to model human learning dynamics.

They are likely to transfer much better.

## Learner-facing learned features

These predict human behavior, retention, or intervention response.

They face much more severe population and domain shift.

The highest-ROI near-term investment should be in the first category.

# Revised ranking of learned features

## 1. Source-grounded retrieval, structural similarity, and isomorphism detection

**ROI: extremely high**  
**Transferability: extremely high**  
**Need for real LearnLoop data: low**

This is probably the strongest general-purpose learned component.

Given a new item or response, retrieve:

- the relevant canonical source passages;
    
- prior items testing the same operation;
    
- prior items with a deliberately different surface;
    
- prior errors with the same first divergence;
    
- alternative valid solution routes;
    
- probes that distinguish similar hypotheses;
    
- repairs that target an analogous mechanism.
    

The model should combine:

semantic similarity+solution-structure similarity+typed graph relations+LLM cross-encoder judgment.\text{semantic similarity} + \text{solution-structure similarity} + \text{typed graph relations} + \text{LLM cross-encoder judgment}.

The source itself supplies large amounts of self-supervision:

- source span ↔ generated question;
    
- theorem ↔ application;
    
- definition ↔ example;
    
- question ↔ verified solution;
    
- original ↔ paraphrase;
    
- same operation ↔ different surface;
    
- same surface ↔ different operation;
    
- valid ↔ invalid application.
    

This learned feature is useful whether the source is:

- a textbook;
    
- an arXiv paper;
    
- API documentation;
    
- a codebase;
    
- language-learning material;
    
- lecture notes;
    
- a legal or scientific reference.
    

It is also directly useful to trace memory, probe construction, repair selection, and cold-item freshness.

## 2. Calibration and error prediction for the frontier LLM

**ROI: extremely high**  
**Transferability: high**  
**Need for real LearnLoop data: modest**

Rather than training a model to replace the frontier LLM, train one to answer:

> Under what conditions should LearnLoop trust the LLM’s judgment?

Inputs could include:

- grader confidence;
    
- disagreement across prompts or model families;
    
- source-citation support;
    
- verifier availability;
    
- valid-alternative ambiguity;
    
- response length and structure;
    
- distance from retrieved examples;
    
- whether the answer uses a novel solution route;
    
- whether canonical-source passages agree;
    
- whether the LLM’s predicted response matches behavioral history.
    

Outputs could include:

P(grade error),P(\text{grade error}), P(diagnostic hypothesis is unsupported),P(\text{diagnostic hypothesis is unsupported}), P(repair choice would flip under evaluator variation),P(\text{repair choice would flip under evaluator variation}),

and

P(state write should abstain).P(\text{state write should abstain}).

This is a more transferable supervised task than learning “student mastery,” because the target is **system reliability**. The model learns recurring failure conditions of the LLM and pipeline rather than the entire semantics of every possible subject.

It can start as a hierarchical logistic model or gradient-boosted model. It does not need to be a GRU.

## 3. A learned probe and repair critic

**ROI: extremely high**  
**Transferability: high**  
**Need for real learner data: low for validity; high for actual effectiveness**

For every candidate probe, predict:

- source grounding;
    
- answerability;
    
- gradability;
    
- leakage;
    
- familiarity/isomorphism contamination;
    
- hypothesis separability;
    
- wording sensitivity;
    
- representation confounding;
    
- estimated learner burden.
    

For a hypothesis pair hi,hjh_i,h_j, learn:

Vθ(q,hi,hj,C)V_\theta(q,h_i,h_j,C)

where CC contains the canonical source and item contract.

Much of the training signal can be generated offline:

1. Generate many candidate probes.
    
2. Execute the candidate mal-procedures.
    
3. Compute whether they produce divergent response signatures.
    
4. Verify the correct answer.
    
5. perturb wording and notation;
    
6. measure whether the grade or chosen repair changes;
    
7. train the critic to rank candidates.
    

Synthetic data is appropriate here because many labels are mechanically or structurally verifiable. We are not asking the simulator whether a human will learn. We are asking whether a probe is valid, grounded, non-leaking, and theoretically discriminating.

At runtime:

```text
LLM generates 32 candidates
        ↓
learned critic ranks them
        ↓
verifier checks top 3
        ↓
robust decision-EVSI
        ↓
one question is shown
```

This spends computation to save learner attention.

## 4. Relative surprise, disagreement, and recurrence features

**ROI: high**  
**Transferability: high if source-relative**  
**Need for real data: low to moderate**

Avoid absolute claims such as:

> This item has difficulty 0.72.

Prefer relative features:

St=−log⁡PLLM(ot∣Ht−1,xt)S_t=-\log P_{\text{LLM}}(o_t\mid H_{t-1},x_t) Dt=∣pLLM−pexplicit∣D_t= \left| p_{\text{LLM}}- p_{\text{explicit}} \right| Rt=sim⁡(current first divergence,prior first divergences)R_t= \operatorname{sim} ( \text{current first divergence}, \text{prior first divergences} ) Lt=percentile⁡(latencyt∣learner, item family)L_t= \operatorname{percentile} ( \text{latency}_t \mid \text{learner, item family} ) Ct=reported confidence−predicted success.C_t= \text{reported confidence} - \text{predicted success}.

These are more domain-general than raw latency, raw difficulty, or fixed misconception IDs.

A 20-minute response is not globally “slow.” It can be unusually fast for proving a theorem and unusually slow for recalling a definition. Source-relative and learner-relative normalization removes some of that mismatch.

These features can feed the deterministic router immediately as sensors, while remaining non-authoritative.

## 5. A bounded GRU/SSM temporal residual

**ROI: potentially high**  
**Transferability: uncertain**  
**Need for public data: available**  
**Need for target validation: essential**

I would still build this, but later and in shadow.

The model should be trained to answer narrow questions:

- Does history improve the prediction beyond the LLM and explicit ledger?
    
- Does an error look transient or persistent?
    
- Is there evidence of scaffold dependence?
    
- Is a cold failure becoming more likely?
    
- Does the current response depart from this learner’s own recent pattern?
    

It should not emit a global “knowledge vector.”

The model race should be:

1. explicit hierarchical/logistic baseline;
    
2. LLM-only prediction;
    
3. calibrated combination;
    
4. small GRU residual;
    
5. matched-size SSM residual;
    
6. optional ACE-style cascade.
    

The GRU/SSM receives LLM-derived semantics rather than question IDs. Full question text has been shown to substantially improve cold-question KT performance relative to ID-only or concept-only inputs, but existing work also explicitly leaves genuinely cross-domain validation unresolved. ([arXiv](https://arxiv.org/html/2511.02599v1 "https://arxiv.org/html/2511.02599v1"))

I would promote the temporal residual only if it improves:

- source-held-out log loss or Brier score;
    
- calibration;
    
- cold prediction;
    
- downstream repair regret;
    
- diagnostic question count;
    

without increasing false remediation.

If it merely raises in-distribution AUC on FoundationalASSIST, it has not earned a place in LearnLoop.

## 6. Learned forgetting parameters

**ROI: moderate**  
**Transferability: moderate at best**

I would revise this downward from my earlier enthusiasm.

Generic data can help identify plausible functional forms:

pretain(Δ)=σ(α−βlog⁡(1+Δ)).p_{\text{retain}}(\Delta) = \sigma( \alpha-\beta\log(1+\Delta) ).

But the parameter β\beta should not transfer uncritically from school mathematics to research-paper understanding.

Use external data to specify:

- candidate decay families;
    
- regularization priors;
    
- monotonicity expectations;
    
- numerically stable parameterizations.
    

Then estimate source-, representation-, and learner-relative strengths from LearnLoop data.

A simple partially pooled model is likely safer initially than a large SSM:

βu,v=β0+βsource family+βcapability+ϵu,v.\beta_{u,v} = \beta_0+ \beta_{\text{source family}}+ \beta_{\text{capability}}+ \epsilon_{u,v}.

## 7. Behavioral item embeddings trained on school responses

**ROI: medium in-domain**  
**Transferability: low without semantic anchoring**

I would no longer make these a major foundational component by themselves.

A collaborative-filtering item embedding from FoundationalASSIST may discover useful arithmetic difficulty patterns, but a new theorem-proof item has no meaningful position in that space.

A better version is:

zq=[zqfoundation-semantic,zqcanonical-structural,zqobserved-behavioral].z_q = [ z_q^{\text{foundation-semantic}}, z_q^{\text{canonical-structural}}, z_q^{\text{observed-behavioral}} ].

The first two exist immediately. The behavioral component begins missing or highly uncertain and fills in as real observations arrive.

Behavioral geometry should refine the LLM/source geometry, not replace it.

## 8. Repair-effect model and learned router

**ROI eventually high**  
**Transferability currently low**  
**Defer**

Neither school KT data nor LLM personas can tell LearnLoop reliably whether a counterexample, worked example, prerequisite review, or direct explanation will improve cold performance for advanced learners.

This requires real actions and outcomes.

The router should therefore remain deterministic, with learned components acting as sensors or near-tie selectors, exactly as the plan currently specifies.

# A critical distinction: source-invariant versus source-relative

I would avoid trying to learn a representation that erases domain identity.

“Domain-agnostic” should mean:

> The same interfaces and estimands work for any canonical source.

It should not mean:

> The model treats abstract algebra like fraction arithmetic.

The universal representation should preserve both shared and private information:

z=[zshared,zsource-private].z= [ z^{\text{shared}}, z^{\text{source-private}} ].

Shared coordinates might represent:

- recall versus derivation;
    
- procedural versus conceptual demand;
    
- representation switch;
    
- assistance dependence;
    
- response surprise;
    
- recurrence;
    
- delay;
    
- confidence mismatch;
    
- evidence support.
    

Private coordinates might represent:

- mathematical notation;
    
- proof strategy;
    
- code semantics;
    
- scientific mechanisms;
    
- source-specific terminology;
    
- permissible solution routes.
    

This aligns with the plan’s decision-conditioned shared/private representation direction: only the decision-relevant overlap should be aligned, while private signal remains available for prediction and open-set detection.

# How to evaluate transfer honestly

Do not use random train/test splits as the primary transfer test.

Use a transfer ladder:

|Level|Held out at evaluation|
|---|---|
|0|interactions from known learners/items|
|1|new learners, same source|
|2|new items, same source|
|3|entirely new canonical source, same subject|
|4|entirely new subject at similar technical level|
|5|advanced/open-ended domain absent from training|
|6|new response modality: proofs, code, diagrams, paper synthesis|

The most important benchmark is levels 3–6.

For each level, compare:

1. Frontier LLM only.
    
2. Explicit ledger/rules only.
    
3. LLM plus explicit ledger.
    
4. Public-data GRU/SSM.
    
5. LLM plus bounded GRU/SSM residual.
    
6. Source-adapted residual.
    
7. Robust ensemble/disagreement policy.
    

A learned artifact should ship only when it improves source-held-out outcomes. In-domain gains are not enough.

For advanced domains, I would create a small but deliberately diverse **LearnLoop Transfer Suite**, perhaps containing:

- linear algebra;
    
- probability/statistics;
    
- an ML paper;
    
- an algorithms paper;
    
- programming/debugging;
    
- scientific mechanism comprehension;
    
- one non-mathematical technical source.
    

It does not need thousands of learners to be useful. It can first evaluate:

- source retrieval;
    
- question representation;
    
- response grading;
    
- first-divergence extraction;
    
- valid-alternative recognition;
    
- recurrence matching;
    
- probe validity;
    
- repair grounding;
    
- LLM calibration.
    

Only retention and intervention-effect evaluation inherently require delayed human outcomes.

# Synthetic personas: what they can and cannot solve

I would preserve synthetic learners, but change the language around what their data means.

## Good uses of synthetic learners

Synthetic data can support:

- code-path testing;
    
- hypothesis coverage;
    
- rare misconception generation;
    
- same-cause/different-surface pairs;
    
- same-answer/different-cause hard negatives;
    
- mal-procedure execution;
    
- probe-separability training;
    
- invalid-probe generation;
    
- grader perturbation tests;
    
- open-world stress testing;
    
- router recovery on planted ground truth;
    
- pretraining proposal networks;
    
- comparing algorithms under controlled assumptions.
    

Here the simulator functions as a **programmable benchmark generator**.

## Bad uses

Synthetic persona trajectories should not be treated as evidence about:

- actual human forgetting;
    
- probability of a particular human error;
    
- prevalence of misconceptions;
    
- frustration or dropout;
    
- cold retention;
    
- repair effectiveness;
    
- causal treatment effects.
    

Current LLM student simulators can be behaviorally unfaithful in a particularly relevant way: across multiple models and prompting schemes, simulated students often accept targeted and irrelevant corrections at similar rates, producing near-zero selective-flip scores. ([arXiv](https://arxiv.org/html/2605.12748v1 "https://arxiv.org/html/2605.12748v1"))

More generally, matching human-like response distributions does not validate counterfactual treatment effects. A recent cross-national evaluation found that descriptive realism and treatment-effect accuracy could diverge substantially; models that looked realistic could still estimate intervention effects poorly. ([arXiv](https://arxiv.org/pdf/2604.02458 "https://arxiv.org/pdf/2604.02458"))

The clean rule is:

synthetic data specifies and pretrains; real data calibrates and certifies\boxed{ \text{synthetic data specifies and pretrains; real data calibrates and certifies} }

Synthetic personas may propose priors or act as auxiliary data. They should never cause a learner-facing model to acquire a higher evidence-authority tier by themselves.

# The seven-day problem is real, but manageable

You do not need every training target to be “success exactly seven days later.”

Model retention as a function of actual delay:

P(R=1∣Ht,x,Δ).P(R=1\mid H_t,x,\Delta).

An observation after 2, 5, 9, or 18 days can all contribute. Until the event occurs, the outcome is pending or censored rather than negative.

I would maintain several outcome lanes:

Rimmediate,Rfresh-next,R1–3d,R4–10d,R11–30d.R_{\text{immediate}}, \quad R_{\text{fresh-next}}, \quad R_{1\text{–}3d}, \quad R_{4\text{–}10d}, \quad R_{11\text{–}30d}.

The short-horizon labels provide fast provisional supervision. Longer horizons gradually mature. The model can share structure across horizons while preserving the distinction:

pθ(RΔ=1).p_\theta(R_{\Delta}=1).

Several practical collection strategies reduce the burden:

- use naturally recurring related questions as opportunistic cold audits;
    
- schedule audits over a range of delays rather than exactly day 7;
    
- prioritize audits in regions where the router’s decision is sensitive;
    
- occasionally randomize audit timing;
    
- record pending outcomes explicitly;
    
- use new-surface near-transfer as an intermediate endpoint;
    
- batch multiple facets into one carefully designed audit when validity permits.
    

None of these makes an immediate outcome equivalent to retention. They simply produce a denser multi-horizon supervision stream.

# The direction I would move forward with

## Phase 1: foundation-model-first infrastructure

Build and freeze the universal typed contracts:

- `ItemContractV1`;
    
- `ObservedResponseV1`;
    
- `CandidateCauseV1`;
    
- `ProbeInstrumentV1`;
    
- `RepairActionV1`;
    
- `OutcomeReceiptV1`.
    

Use the frontier LLM to populate semantic fields with canonical-source citations and provenance.

This benefits every later model.

## Phase 2: learned content-facing critics

Train, in this order:

1. source-span retrieval/reranking;
    
2. item isomorphism and freshness;
    
3. probe validity/separability;
    
4. grading/state-write risk calibration;
    
5. recurrence matching over first-divergence and delta fields.
    

These can use large amounts of canonical-source-derived and mechanically verified data. They are likely to generalize better than human-behavior models.

## Phase 3: small learner-facing residuals in shadow

Train a small GRU first, then an SSM challenger, on:

- LLM-derived semantic events;
    
- explicit telemetry;
    
- actual time gaps;
    
- assistance/reveal history;
    
- source-relative normalization.
    

Predict narrow outcomes:

- next independent correctness;
    
- exact response class where defined;
    
- persistence/recurrence;
    
- cold success by delay;
    
- scaffold dependence.
    

The residual receives no state-writing or routing authority until it wins on entirely held-out sources.

## Phase 4: source-specific calibration and few-shot adaptation

For a new canonical source:

- create the semantic representation immediately;
    
- train content-facing adapters from source-derived self-supervision;
    
- keep behavioral residual weight near zero;
    
- update a tiny calibration adapter as real outcomes accrue;
    
- never continually fine-tune the shared backbone from one learner.
    

This retains the GEN-style adaptation idea, but applies it to small interfaces and calibration heads rather than assuming a school-trained temporal model already contains advanced learning dynamics.

## Phase 5: real-data action effects

Only after sufficient logged and preferably near-tie-randomized interventions should LearnLoop train:

P(Rnext,Rcold∣x,do⁡(a)).P(R_{\text{next}},R_{\text{cold}}\mid x,\operatorname{do}(a)).

Synthetic personas can help test the estimator, but not identify the effect.

# My final priority ranking

Across arbitrary canonical sources, I would rank the learned opportunities:

1. **Canonical-source-grounded retrieval and structural item/response representations.**
    
2. **Calibration, abstention, and disagreement models around the frontier LLM.**
    
3. **Probe/repair validity and separability critics trained from verified offline generation.**
    
4. **Source-relative surprise, recurrence, confidence-mismatch, and OOD features.**
    
5. **A bounded GRU/SSM temporal residual over LLM-derived event representations.**
    
6. **Partially pooled retention/forgetting calibration.**
    
7. **Behavioral item embeddings, only as an optional third view beside semantic and structural representations.**
    
8. **Repair-effect learning after real randomized or propensity-supported data.**
    
9. **A learned router or monolithic latent learner model—not currently justified.**
    

The single most promising learner-facing learned artifact is therefore **not a standalone knowledge tracer**. It is:

a source-conditioned, support-gated temporal residual over frontier-LLM semantic features\boxed{ \text{a source-conditioned, support-gated temporal residual over frontier-LLM semantic features} }

The single most promising overall learned artifact is:

a canonical-source-grounded representation and critic layer\boxed{ \text{a canonical-source-grounded representation and critic layer} }

That division plays directly to the data you actually have. Public KT datasets contribute generic behavioral priors. Frontier LLMs supply broad semantic competence. Canonical sources provide unlimited source-specific grounding and verification tasks. LearnLoop’s sparse real outcomes calibrate the final few quantities that actually depend on human learning.</Agent>

<User>Based off of your reading of ACE-KT and our current discussion, any further changes would you like to implement to Pipeline Augmentation Plan.md? </User>

<Agent>Yes. I implemented a revision rather than simply inserting “use ACE-KT” into the existing plan.

The central change is:

frontier LLM + canonical source  owns cross-domain semantics\boxed{ \text{frontier LLM + canonical source} \;\text{owns cross-domain semantics} }

while

GRU/SSM and other learned models  provide bounded, source-conditioned sensors and critics\boxed{ \text{GRU/SSM and other learned models} \;\text{provide bounded, source-conditioned sensors and critics} }

The original architecture’s strongest boundaries remain intact: the blind grader stays blind, embeddings cannot create evidence, the router remains deterministic, cold evidence remains primary, and neither recurrent state nor simulation becomes learner-state authority.

## What changed after reading ACE-KT more closely

ACE-KT’s high-level progression—local convolution, contextual attention, then selective SSM integration—is worth borrowing as a **model-development ladder**. But the paper’s ablations substantially changed how I would prioritize those pieces:

- Removing the contextual Transformer module causes by far the largest degradation, reportedly reaching a 7.2% AUC drop.
    
- Removing the SSM integration module causes a smaller drop, up to 0.8%.
    
- The local convolution and TeLU contribute roughly 0.1–0.3% and 0.1–0.2%, respectively.
    

So I no longer think “try an SSM because ACE-KT performs well” is the right interpretation. The more defensible interpretation is:

> **Relevant-history selection and contextual structuring may matter more than the choice between GRU and selective SSM.**

ACE-KT also predicts the next binary response from question, knowledge-component, and response sequences; its question representations depend on learned question difficulty, KC variation, and KC-response embeddings rather than canonical-source text. It is trained with next-response binary cross-entropy and evaluated by AUC and accuracy. Its five evaluation datasets are conventional tutoring or assessment datasets, and sequences are truncated to 200 interactions.

That is good evidence for the architecture’s **in-distribution KT utility**, but not evidence that it transfers to proofs, arXiv-paper comprehension, code, or arbitrary canonical sources.

## 1. I added a foundation-model-first doctrine

The plan now explicitly says that the frontier LLM and canonical source should compile:

- `ItemContractV1`
    
- `ObservedResponseV1`
    
- solution strategies and required operations
    
- first divergence and delta from canonical
    
- hypotheses, probes, and repairs
    

Smaller learned models operate over these typed representations. They do not receive opaque school-math question IDs and somehow infer that the new source is a linear algebra proof or a machine-learning paper.

This sharpens the plan’s existing division of labor, where the LLM supplies semantic compression, zero-shot hypotheses, and open-world expansion, while other components supply memory, calibration, belief, and ground truth.

I also added three invariants:

1. Public KT data is **pretraining and regularization**, not production truth about advanced learners.
    
2. Learner-facing learned predictions must be **bounded and support-gated**.
    
3. Synthetic data receives authority according to what is independently verifiable, not merely because it is plentiful.
    

## 2. I added `B0.5`: a source-conditioned temporal evidence sensor

The new model is not a replacement for the learner field. It adds a bounded residual over the explicit-ledger and frontier-LLM baseline:

logit⁡p^=logit⁡pbase+gsupport(x)clip⁡(rθ(Ht,x;aD),−ρ,ρ).\operatorname{logit}\widehat p = \operatorname{logit}p_{\mathrm{base}} + g_{\mathrm{support}}(x) \operatorname{clip} \left( r_\theta(H_t,x;a_D),-\rho,\rho \right).

Here:

- pbasep_{\mathrm{base}} is the calibrated LLM-plus-ledger estimate.
    
- rθr_\theta is the GRU/SSM prediction.
    
- aDa_D is a canonical-source adapter.
    
- gsupportg_{\mathrm{support}} approaches zero under source, capability, representation, or modality shift.
    

Thus a model trained mainly on FoundationalASSIST contributes little by default when the user starts reading an unfamiliar technical paper. It must demonstrate that it adds predictive signal beyond the frontier model.

The sensor emits a typed `TemporalEvidencePacketV1`, including:

- fresh-independent success prediction;
    
- cold success indexed by actual delay;
    
- exact-response probabilities where meaningful;
    
- recurrence and scaffold-dependence proposals;
    
- predictive surprise;
    
- LLM-versus-explicit-versus-temporal disagreement;
    
- source-support and OOD scores;
    
- uncertainty and calibration stratum;
    
- consumed event IDs and artifact versions.
    

It never exposes a recurrent hidden vector as the application API and never increments evidence support. This extends the plan’s existing rule that a GRU/SSM state is only a reproducible cache rather than learner authority.

## 3. I changed the architecture race

The revised experimental ladder is:

1. Explicit ledger plus canonical-source-grounded frontier LLM.
    
2. Bounded GRU residual.
    
3. Target- and graph-conditioned contextual attention plus GRU.
    
4. Matched-parameter selective SSM challenger.
    
5. Optional local convolution and full ACE-style cascade.
    

This reflects ACE-KT’s ablation results: first establish that sequence learning adds signal, then test whether contextual event selection adds signal, then test whether an SSM beats a GRU. The local convolution and TeLU are ordinary ablations rather than commitments.

I also changed the module terminology from cognitive claims to operational descriptions:

- `local deviation`
    
- `context selection`
    
- `temporal integration`
    

ACE-KT motivates these architectural roles, but next-response performance does not demonstrate that their hidden activations literally correspond to distinct human cognitive stages.

## 4. I added actual elapsed time and explicit read/write separation

ACE-KT’s formal interaction sequence is (qt,ct,rt)(q_t,c_t,r_t), and its rhythm module convolves across event positions.

For LearnLoop, the model must instead consume:

- actual elapsed time;
    
- session boundaries;
    
- hints and answer reveals;
    
- whether the surface is familiar;
    
- representation changes;
    
- assistance level;
    
- intervention identity.
    

I also added two temporal states:

zt−=f(H<t),z_t^- = f(H_{<t}),

the state used to predict the present response, and

zt+=T(zt−,at,ot,revealt,assistancet),z_t^+ = T(z_t^-,a_t,o_t,\text{reveal}_t,\text{assistance}_t),

the post-interaction proposal used to predict future behavior.

This prevents the system from:

- including a response in the state that supposedly predicted that response;
    
- pretending that a diagnostic probe passively observed the learner when it also provided practice, clues, or feedback.
    

That brings the learned model into alignment with the plan’s existing joint read/write kernel Ka(h′,o∣h)K_a(h',o\mid h).

## 5. I added two-channel source adaptation

The source adapter is split into:

aD=(aDcontent,aDbehavior).a_D= \left( a_D^{\mathrm{content}}, a_D^{\mathrm{behavior}} \right).

`a_D^content` can be constructed immediately using canonical-source-derived tasks:

- source span ↔ question;
    
- question ↔ verified solution;
    
- same operation ↔ different surface;
    
- valid ↔ invalid theorem application;
    
- isomorphic ↔ non-isomorphic problem;
    
- hypothesis pair ↔ discriminating probe.
    

`a_D^behavior` begins at zero or the population prior. It may only update from real target-source learner events.

The shared backbone is not continually fine-tuned from one user or one source. Adaptation is restricted to:

- support-set conditioning with no gradient;
    
- a tiny input/output adapter after enough verified examples;
    
- slow offline consolidation across many sources.
    

The plan now requires 0/1/4/16/64-shot adaptation curves rather than an unsupported claim that one-shot adaptation works.

## 6. I added a much stronger transfer gate

The old benchmark section primarily covered ConceptKT, Eedi retrieval, grader invariance, and the eventual diagnosis ablation.

The revised plan now requires evaluation at progressively harder levels:

1. New learner, known source.
    
2. New item, known source.
    
3. Entirely held-out canonical source.
    
4. Held-out subject.
    
5. Advanced or open-ended source absent from training.
    
6. Held-out response modality, such as multiple choice to proof, code, diagram, or explanation.
    

At each level, the learned feature must be compared against:

- explicit ledger;
    
- frontier LLM with canonical context;
    
- calibrated LLM plus ledger;
    
- public-data GRU/SSM alone;
    
- bounded residual;
    
- source-adapted residual;
    
- robust disagreement envelope.
    

A learned model receives no production credit merely for improving AUC on FoundationalASSIST or Eedi. It must improve calibration or decision quality over the **frontier-LLM-plus-ledger baseline** on held-out sources, or safely shrink to zero.

I also added a proposed `LearnLoop Transfer Suite` containing at least:

- school mathematics;
    
- undergraduate linear algebra or probability;
    
- an arXiv paper;
    
- a programming/API source;
    
- a non-mathematical technical source.
    

Many parts of this benchmark—retrieval, grading, valid alternatives, first divergence, probe validity, and source adaptation—can be built before enough delayed human outcomes accrue.

## 7. I separated the two kinds of synthetic data

The plan now distinguishes:

### `SyntheticSourceVerified`

Generated content whose labels are checked by a canonical source, solver, compiler, rubric, type system, or mal-procedure executor.

This may train:

- retrieval rerankers;
    
- isomorphism classifiers;
    
- probe-validity critics;
    
- separability critics;
    
- grader-risk models;
    
- structural trace encoders.
    

### `SyntheticPersonaTrajectory`

LLM simulations of learner behavior and counterfactual trajectories.

This may support:

- code-path testing;
    
- mechanism coverage;
    
- particle proposals;
    
- stress testing;
    
- synthetic benchmark construction.
    

It may **not** calibrate:

- human forgetting;
    
- misconception prevalence;
    
- cold retention;
    
- frustration or dropout;
    
- repair effectiveness.
    

This sharpens the original plan’s simulation firewall, which already prevented posterior synthetic trajectories from becoming evidence or recursive training data.

## 8. I added distilled probe and repair critics

This is probably the highest-ROI new learned component.

For each hypothesis pair, the system can generate many candidates offline and record:

- canonical grounding;
    
- verified answer;
    
- mal-procedure separability;
    
- ASNR;
    
- wording sensitivity;
    
- grader sensitivity;
    
- familiarity/isomorphism contamination;
    
- estimated learner burden;
    
- whether the candidate could flip the repair decision.
    

A learned `ProbeCriticV1` or `RepairCriticV1` then ranks candidates:

```text
frontier LLM generates broadly
            ↓
learned critic ranks cheaply
            ↓
deterministic verifier checks top candidates
            ↓
robust decision-EVSI
            ↓
serve one or reject all
```

This is where computation and synthetic data can scale safely: it improves machine-side search without pretending to know how humans learn from an intervention.

## 9. I added auxiliary multi-horizon delayed outcomes

The primary objective remains:

S=.75Rcold+.25Rnext.S=.75R_{\mathrm{cold}}+.25R_{\mathrm{next}}.

I did not weaken the cold-evidence requirement.

But every eligible independent follow-up is now logged as:

(RΔ,Δ),(R_\Delta,\Delta),

with reporting lanes such as:

- fresh next;
    
- 1–3 days;
    
- 4–10 days;
    
- 11–30 days.
    

Pending observations are censored rather than failures. These labels may train a time-conditioned hazard or retention model, while only the declared eligible cold event finalizes the product outcome.

## 10. I revised the sequencing and “permanently out” statement

The earlier sequencing placed nearly all trained artifacts at the end. The revision distinguishes:

- **early content-facing critics**, which can learn from source-verified supervision;
    
- **later learner-facing temporal models**, which require transfer validation;
    
- **much later repair-effect models**, which require real propensities or randomization.
    

The phrase “population KT models in the loop” has also been refined. What remains prohibited is a population KT model acting as:

- evidence;
    
- canonical learner state;
    
- learner topology;
    
- routing authority.
    

A population-pretrained GRU/SSM is allowed only as a bounded, source-conditioned residual sensor under the transfer gate.

## Edited plan

# Pipeline Augmentation Plan

*Finalized 2026-08-24 from the dialogue trace over [[Diagnostic Pipeline Synthesis]], [[Capability Gated Planning, Cost to Goal Discovery]], [[Agent dialogue]], [[Agent dialogue on modeling incorrect student thinking]], [[Agent dialogue on EduEmbed]], the RSIR / RecHarness / Q-matrix / L-HAKT / RouterXBench reviews, and a code survey of the shipped substrate. Amended same day with six adoptions from the forked multi-view/alignment research review (decision-conditioned shared–private alignment, escalation rule, controlled-confound benchmark, ASNR/flip-rates, exposure density, action capability embeddings), the trace-record feature pass, the outcome/cost + embedding-authority decisions below, and the architecture review summarized in [[Learner Field and Directional Models Augmentation]]. Amended 2026-08-31 after direct review of ACE-KT and the transfer/data discussion: foundation-model-first semantic contracts; content-facing learned critics before learner-facing KT; source-held-out transfer gates; a source-conditioned bounded GRU/SSM residual; zero/few-shot source adapters; a synthetic-data authority split; and auxiliary multi-horizon delayed outcomes. Every workstream is coupled to its learner-journey justification — if an item's justification is weak, cut the item.*

---

## The architecture picture

One stack, one division of labor. The backbone LLM keeps what it is good at — semantic compression (grader → canonical diagnostic text), zero-shot proposal (hypotheses, probes, response signatures on never-seen items), open-world expansion (new misconceptions without a fixed taxonomy). Everything else exists to supply what statelessness takes away: **memory**, **calibration**, **belief**, and **ground truth**.

```
                    ┌─ blind grader (backbone) ─ canonicalized causes ─┐
observed attempt ──►│                                                  ▼
                    │                                    A. TRACE MEMORY (embedding index,
                    │                                       factorized fields, MERIT payloads)
                    │                                                  │
                    │              B. LEARNER FIELD over shared content/capability topology
                    │                 (temporal state; two projections:
                    │                  typed vector → router, rendered card → backbone)
                    │                                                  │
                    │        E. BELIEF: RSIR-filtered trajectory ensemble = C_δ(b)
                    │           (BEAGLE generator + typed validity + real-observation fidelity)
                    │                                                  │
                    │   C. CALIBRATION: pooled likelihoods over item-invariant keys ("arm A")
                    │                                                  ▼
                    └─────────► F. DETERMINISTIC ROUTER (staged_policy, live EVSI)
                                  four-route comparator {repair / ask / construct / defer}
                                  G. equipoise bandit inside near-tie slack
                                     + plateau → jump-basin trigger (structural arms)
                                                                       │
                    D+E. EVALUATION: ConceptKT + Eedi benchmarks; W3 synthetic learner;
                         diagnosis-ablation A/B                        ▼
                                                              action served to learner
```

**Aug 31 learned-model amendment — foundation model first, small models second.** The frontier backbone plus the canonical source supplies cross-domain semantic competence: it compiles items, solutions, learner responses, hypotheses, probes, and repairs into typed, source-grounded contracts. Smaller learned components may then estimate bounded predictive residuals, reliability risks, retrieval/ranking scores, or proposal values over those contracts. They never have to infer linear algebra, an arXiv paper, or a programming API from question IDs learned on school-math platforms. Content-facing critics can be trained from source-derived, mechanically verified examples; learner-facing temporal/effect models remain shadow-only until they pass source-held-out and local calibration gates.

### Formal state interpretation — shared topology, learner-specific belief

The plan's "learner manifold" is three objects with different owners and authority:

\[
\begin{aligned}
G &= \text{authored concept/facet/capability hypergraph},\\
d_\phi &= \text{versioned semantic metric over items, traces, and hypotheses},\\
b_t &= \text{learner-specific posterior field over }G.
\end{aligned}
\]

- \(G\) owns prerequisite, composition, representation, transfer, and recipe structure.
- \(d_\phi\) supplies metric neighborhoods, retrieval candidates, and soft analogies.
- \(b_t\) records what is currently predicted about this learner, including missingness and uncertainty.

This is deliberately **not one student embedding**. Understanding is jagged across concept/facet, capability/operation, representation, assistance, immediate-vs-cold availability, misconception mechanism, and time horizon. The learner object is therefore a stratified field such as

\[
b_t(v,c,r)=
\left(
p_{\text{available}},
p_{\text{cold}}(\Delta),
p_{\text{misconception}},
p_{\text{scaffold-dependent}},
n_{\text{eff}},
u
\right)
\]

for content region \(v\), capability \(c\), and representation \(r\). Each component remains a versioned projection with its own authority; no LLM-authored summary or hidden recurrent state becomes the canonical learner profile.

Here `n_eff` is independent effective support and \(u\) is posterior uncertainty/missingness, not an extra mastery axis.

Only metric structure is claimed for the embedding space: distances, neighborhoods, and decision equivalence, never semantic meanings for coordinates ([ICML 2025 metric-identifiability result](https://arxiv.org/abs/2502.13757)). Matérn/heat kernels may smooth a field with uncertainty ([GeometricKernels, JMLR 2025](https://www.jmlr.org/papers/v26/24-1185.html)), but topology recovery itself requires sampling density absent from sparse n=1 histories ([NeurIPS 2024 topology-convergence analysis](https://proceedings.neurips.cc/paper_files/paper/2024/hash/47bb4eff6321ae7a11fb6e3352c63125-Abstract-Conference.html)). **Estimate the learner field on topology LearnLoop already owns; never infer a new topology per learner.**

Standing invariants (violating any of these is a bug, not a tradeoff):

1. **Blind grader stays blind** — hypotheses and retrieved memory enter the diagnostician/tutor/generator roles, never the grading role (self-confirming-loop firewall).
2. **Vector arithmetic never creates evidence** — the manifold informs retrieval, priors, readiness, and candidates; only observed learner events certify. Semantic recurrence can regroup existing observations, but it cannot manufacture another observation or double-count the source event. Same authority level as graph propagation.
3. **The router's authority stays a deterministic state machine with a fixed observation vector** (Hey-Chat lesson). Learned components are sensors; stochastic selectors may act only inside a deterministic certified near-tie set, never define feasibility or route authority.
4. **Outcome is immediate-use plus durable-use, with cold evidence primary** — the first eligible independent next attempt supplies a provisional outcome; the delayed cold attempt finalizes it. Guided redos, near-duplicate surfaces, and same-item correctness do not count as next-attempt success, and missing cold outcomes stay pending rather than becoming failures. Durable learner-state promotion still requires cold evidence.
5. **False remediation is a safety constraint, not an ordinary tradeable cost** — do not buy a higher success score by remediating more learners unnecessarily. Among policies below the false-remediation ceiling, prefer the one with better outcome and then fewer diagnostic questions.
6. **Posterior synthetic trajectories are never recursive training data** (RSIR-collapse firewall). Separately generated planted benchmark examples may enter H's eventual training corpus only behind an independent future-behavior evaluation gate; simulation output and posterior samples are different artifacts with different authority.
7. **Learner state remains plural, replayable, and provenance-bearing** — raw observations stay immutable; every inferred field/card/vector names its event horizon and algorithm version; an LLM output, embedding, recurrent hidden state, or simulated particle is never application-state authority by itself.
8. **Cross-domain semantics come from the canonical source and frontier backbone, not a population KT model** — any learner-facing sequence model consumes typed, source-grounded item/response contracts rather than opaque question/KC ids. Public KT corpora provide pretraining and regularization, never production truth about advanced technical learners.
9. **Every learner-facing learned prediction is a bounded, support-gated residual** — outside validated source/capability/response-modality support, its contribution shrinks to zero and uncertainty widens back toward the explicit-ledger + frontier-LLM baseline. A learned model may add a sensor; it may not erase missingness.
10. **Synthetic data has task-specific authority** — canonical-source examples whose labels are mechanically or formally verified may train content-facing retrievers and critics. LLM-persona trajectories may propose hypotheses, populate stress tests, and pretrain proposal networks, but never calibrate human forgetting, misconception prevalence, cold retention, or repair effects.

### Outcome and cost contract

Every workstream uses the same episode-level outcome:

\[
S = \alpha R_{\text{cold}} + (1-\alpha)R_{\text{next}},
\qquad \alpha = 0.75 \text{ initially},
\]

where `R_next` is success on the first fresh, unassisted, independently attempted item after the action, and `R_cold` is success on the next eligible delayed cold-retrieval attempt under the reveal ledger. `R_next` is available early and marks the receipt provisional; `R_cold` later finalizes it. The initial 0.75/0.25 weighting states the product preference for durable retrieval without discarding the value of immediate uptake; it is a declared policy parameter, not a fitted per-learner quantity.

**Auxiliary delay-indexed outcomes without redefining success.** To reduce seven-day label latency, log every eligible independent follow-up as `(R_Δ, Δ)` at its actual delay, with coarse reporting lanes such as immediate, fresh-next, 1–3d, 4–10d, and 11–30d. Pending outcomes are right-censored, not failures. These observations may train a time-conditioned hazard/retention head and provide provisional supervision, but only the declared eligible `R_cold` finalizes `S` or promotes durable learner state.

The primary learner-attention cost is

\[
Q = \text{number of diagnostic questions asked before repair or deferral}.
\]

Productive practice and scheduled audits remain logged but are not charged as diagnostic interrogation. `F` is a narrowly confirmed false-remediation indicator: the triggering grade was overturned, the response was a valid alternative, or later authoritative evidence established that the system repaired the wrong facet. Subsequent success alone never proves a repair was false, because the repair may have caused it.

Policy comparison is lexicographic and intentionally simple:

1. reject any policy whose confirmed false-remediation rate exceeds the declared ceiling `τ_F`;
2. among admissible policies, maximize finalized `S` (using provisional `R_next` only while `R_cold` is pending);
3. within an outcome near-tie, minimize `Q`.

For diagnostics that require a scalar receipt, log `J = S - βQ - γF`, with `γ` deliberately large and sensitivity reported over several declared values; the lexicographic rule, not an invented exchange rate, remains the live authority.

---

## Workstreams

### A. Episodic trace memory — embedding index with retrieval authority

**What.** An episodic retrieval layer, not a learner-state model and not a source of belief authority. The unit is an immutable `(learner, item, response)` trace event plus derived, versioned views — never one monolithic learner embedding. Use off-the-shelf embeddings (local sentence-transformer as an optional extra, or embedding endpoint via the AI transport layer — a *separate* model; interop with the backbone happens only at the text level) over canonicalized, deterministically-templated records: `CandidateCause` structures (already lossless at `attempts/grading.py:1062`), `causal_hypotheses` rows, probe instrument cards, **and positive demonstrated-capability records** stamped with reveal/assistance context. Factorized fields (surface / facet-operation / diagnosis / mechanism embedded separately; optional joint composite) because consumers need opposite invariances. Derived tables in SQLite, `embedding_model_version` stamped, rebuildable in replay; brute-force cosine at n=1 scale. Exact identifiers and typed filters narrow the candidate set before vector ranking.

Three consumers, implemented as separate namespaces with separate fields, thresholds, and acceptance metrics — no universal "trace similarity" score:
- **Error recurrence**: filter on canonical facet/operation and rank `first_divergence + delta-vs-canonical + mechanism`; run kNN *in shadow* beside the string-equality keys in `causal_factor_deferral.py:197` / `repositories.py:2372`. A proposed recurrence can regroup existing observed events, but the neighbor match is not an extra event. False merges are costlier than false splits, so no deferral/escalation authority until the same-answer/different-cause audit passes.
- **Diagnostic memory**: retrieve a small, diverse top-k of prior records rendered as structured (observed / hypothesized / repair tried / cold outcome) text into the causal-attribution prompt. Filter by authority and validity interval; mark resolved/superseded hypotheses rather than presenting them as current. Claims still gate; retrieval only feeds the proposer.
- **Item freshness**: search distance-to-administered over minted single-use surfaces, combined with exact item-contract and structural fingerprints because paraphrase distance alone cannot detect mathematical isomorphism. The inverse query (same facet, deliberately different surface/structure) serves the cold lane.

**Authority boundary.** Retrieval may identify related existing evidence; similarity is not itself learner evidence. The index may change candidate generation, record grouping, and prompt context, but cannot directly increment evidence counts, certify mastery/misconception, or write the learner field. Any downstream state change must name the underlying observed event ids so replay can detect double counting.

**MVP boundary.** Ship the immutable event write path and shadow recurrence query first. Defer per-record embedding nudges, automatic consolidation/abstraction, predicted-signature embeddings, and any fine-tuned encoder until the frozen off-the-shelf index beats exact-id, BM25, recency, and no-memory baselines. Consolidation, when enabled, creates a derived abstraction over preserved leaf events; it never overwrites or deletes the evidence-bearing episodes.

**Canonical-source self-supervision and three-view geometry.** Every ingested source can supply large amounts of content-facing supervision before a learner arrives: source-span↔item retrieval, question↔verified-solution matching, same-operation/different-surface pairs, original↔paraphrase pairs, valid↔invalid applications, and deliberately isomorphic/non-isomorphic item pairs. Train or distill rerankers/critics only where the target can be checked against the canonical source, solver, type system, or mal-procedure executor. Keep three views separate: `z_semantic` from the frontier embedder, `z_structural` from source/solution/graph contracts, and an initially missing/high-uncertainty `z_behavioral` learned only from real response outcomes. A tiny source-conditioned reranker/adapter may specialize the frozen base representations, but it is versioned, rollbackable, and cannot rewrite the underlying event or base embedding.

**Trace-record schema (settle before the backfill — schema-then-backfill is cheap, re-backfill is not).** Three channels per record:

*Text-to-embed* (canonical templated renderings, observable separated from hypothesized):
- **First-divergence step** (`first_error_step` / `error_span` / correct prefix) as its own field — process-level identity is the axis that separates same-wrong-answer-different-cause; the primary false-merge guard for recurrence kNN.
- **Delta-vs-canonical**: a compressed rendering of *what differs* from the canonical solution ("omits symmetry check; otherwise isomorphic") — contrast embeddings cluster by failure mode; response embeddings are dominated by shared problem content.
- **Solution strategy / route taken** (which hyperedge/recipe) — supports route-conditioned retrieval and alternative-expertise trajectories.
- **Teach-back / self-explanation transcripts** as positive-side records; distance to the canonical explanation is a cheap conceptual-structure diff.
- **Learner lexical/analogical register** (slow-updating profile) — retrieved at minting/repair-authoring time so generated content lands in the learner's own vocabulary; generation-side only, never diagnostic.

*Structured metadata riding alongside the vectors* (hybrid scoring weights/filters — never stuffed into embedded text; embedders handle telemetry poorly):
- Behavioral micro-telemetry: latency (normalized by learner and item family), edits/self-corrections, hints, retries, abandonment — fast-confident vs. slow-hesitant errors at the same embedding point are different evidence.
- **Confidence-before-feedback** as a scalar — distinguishes "recurring error the learner believes in" (stable misconception) from "recurring error the learner doubts" (fragile knowledge); different repairs.
- Item-contract axes as coordinates (retrieval demand, transfer distance, scaffold level, representation, difficulty axes) — makes purpose-conditioned retrieval precise ("same facet, +1 transfer, representation switched").
- Temporal/spacing context: time-since-exposure, session position, warm/cold status from the reveal ledger.
- **Exposure/support density**: `n_eff` and serving propensity for the record's region — see B.
- Grader/prompt version + evidence-authority tier — retrieval down-weights superseded-grader records; gives the flip-rate audits (D) their version axis.

*Derived/counterfactual (post-MVP, gated by the retrieval acceptance test)*:
- **Predicted-signature embeddings**: execute each candidate hypothesis's mal-procedure on the item and embed the predicted erroneous traces — observed-vs-predicted ranking is a soft retrieval-shaped likelihood proposal for C, never an empirical P(o|h), and a pre-administration divergence check (hypotheses whose predicted traces embed identically cannot be discriminated by this item → reject it at zero learner cost).
- **Repair-outcome annotations** on paradigm payloads: (repair tried → next-attempt outcome / cold outcome / diagnostic questions / confirmed false remediation) as first-class fields — what makes injection actionable, and the same records G's bandit later learns from.

**Research-logging appendix (Phase 1 of the alignment paper track, near-free).** Alongside each record, log the multi-view tuple (semantic embedding, behavioral features, graph coordinates, action-regret vector when available) and periodically run cheap alignability diagnostics — CKA/Procrustes, CCA shared directions, neighborhood overlap, unique predictive gain, decision agreement. No training; this accumulates the evidence that gates H's alignment work.

**Research-sweep adoptions (Aug 24, cited).**
- **Write policy**: every observed event remains an immutable leaf record. An embedding-density novelty gate may decide add / merge-and-increment / ignore only for *derived retrieval abstractions*, with no per-fact LLM call and no effect on evidence counts (SAGE, [arXiv:2605.30711](https://arxiv.org/abs/2605.30711)).
- **Consolidation**: "similarity proposes, LLM disposes" — hybrid retrieval nominates near-duplicate abstractions and the backbone decides whether to create or update a non-authoritative summary (MemRefine, [arXiv:2606.13177](https://arxiv.org/abs/2606.13177)); immutable leaf episodes remain addressable beneath temporal abstractions, reducing injected payload tokens without erasing provenance (TiMem, [arXiv:2601.02845](https://arxiv.org/abs/2601.02845)).
- **Durative records with validity intervals** in event time ("confuses X *since June, resolved Aug 3*"), retrieval conditioned on temporal intent — current-state vs. history-of-this-error ([arXiv:2601.07468](https://arxiv.org/abs/2601.07468)); composes with the reveal ledger and gives the state card its tense.
- **Embedder stays frozen — now evidence-backed**: full corpus fine-tuning buys ~2 recall points (CustomIR, [arXiv:2510.21729](https://arxiv.org/abs/2510.21729)) and narrow fine-tuning *degrades* strong embedders cross-domain ([arXiv:2605.24297](https://arxiv.org/abs/2605.24297)) — fatal for a learner spanning subjects. A possible later n=1 adaptation is **NUDGE-style non-parametric per-record embedding nudges** from the learner's own retrieval outcomes — training-free and reversible per record ([arXiv:2409.02343](https://arxiv.org/abs/2409.02343)) — but it remains deferred until the frozen index passes the MVP gate and enough independently scored retrieval outcomes exist.
- **Self-confirmation is a named, studied failure mode**: aggressive automated writes are the top memory-poisoning surface ([arXiv:2606.04329](https://arxiv.org/abs/2606.04329)) — hard support for provenance/confidence/supersession stamps and the blind-grader firewall.
- **Per-learner misconception prototype** (training-free MCTS reconstruction from past wrong answers, steering distractor/probe generation on *new* items — [arXiv:2508.11184](https://arxiv.org/abs/2508.11184)): the most n=1-compatible published mechanism found; lives in this index, consumed by F's constructive route.
- **Evaluation discipline**: hold embedder + backbone fixed and beat exact-id, BM25, recency, and no-memory baselines before crediting the memory (MemDelta, [arXiv:2606.29914](https://arxiv.org/abs/2606.29914)); measure recurrence precision, same-cause/different-surface recall, same-answer/different-cause false merges, retrieval-induced `RepairFlipRate`/`StateWriteFlipRate`, noise isolation, and mutability. Then require a product-level improvement in finalized `S` or a reduction in `Q` without increasing confirmed false remediation. Answer-quality metrics alone hide retrieval failure (PrecisionMemBench, [arXiv:2605.11325](https://arxiv.org/abs/2605.11325)). Design checklist: the five episodic-memory properties of [arXiv:2502.06975](https://arxiv.org/abs/2502.06975).

**Learner justification.** *"It remembers my mistake."* Today the third occurrence of a recurring misconception opens a fresh diagnostic episode — more probing — because string equality never connected the episodes. With recurrence working, K=3 fires and the learner gets escalated repair instead of re-interrogation. Paradigm injection means repairs target the *family* ("third applicability-condition failure across different theorems") instead of whack-a-mole on the surface instance. The isomorph gate stops near-duplicate questions that feel repetitive and quietly contaminate coldness measurement. Net: fewer questions, smarter repairs, probes that feel fresh. Learner attention is the scarce, non-renewable resource; this is the single biggest spend reduction available.

### B. Learner field + two-projection state communication

**What.** Kernel-weighted aggregation over trace records (recency-decayed, assistance-discounted, evidence-quality-weighted) into the learner-specific field `b_t(v,c,r)` defined above: per content × capability × representation region, track `p_available`, `p_cold(Δ)`, misconception mass, scaffold dependence, exposure/support `n_eff`, and uncertainty. Derived and replayable, never a monolithic learner embedding. Expose the same state through two deterministic projections:

- **`RouterStateV1` → deterministic router**: a compact typed object with `as_of_event_id`, state hash, schema/algorithm versions, goal/frontier, facet×capability cold/assisted estimates, active repair-equivalence classes plus `h_other`, deduplicated recurrence counts, scaffold dependence, exposure density and serving propensity, uncertainty and likelihood-authority tier, repair history with next/cold outcomes, fresh-probe/construction availability, and explicit missingness/OOD flags. Upgrade `state_signals.py` from rule-derived booleans to these calibrated features only after shadow acceptance.
- **`LearnerStateCardV1` → backbone**: a compact canonical rendering of demonstrated cold capabilities, assisted-only capabilities, repeated error families with source event ids, evidence for/against active hypotheses, tried repairs and delayed outcomes, retention risks, preferences, and explicit unknowns. Inject into diagnostician/tutor/generator prompts every call; never into the blind grader.

**Authority and staging.** A's index does not imply this field and never writes it. First ship both projections from explicit ledger records, with event ids and no embedding propagation. `LearnerStateCardV1` is regenerated from the ledger rather than edited by an LLM. A cached GRU/SSM hidden state is likewise only a reproducible derived cache keyed by artifact hash, feature-schema version, and final consumed event id. Run the probabilistic field in shadow against the no-smoothing baseline; it earns router-sensor authority only if it improves finalized `S` or reduces `Q` without breaching `τ_F`, and if sparse/unvisited regions remain conservatively uncertain. Semantic proximity alone is not a pedagogical adjacency claim.

**B0.5 — source-conditioned temporal evidence sensor (shadow-only).** The default predictor for a novel source is the explicit ledger plus a canonical-source-grounded frontier-LLM estimate. A population-trained GRU/SSM may add only a bounded residual:

\[
\operatorname{logit}\hat p
=
\operatorname{logit}p_{\text{base}}
+
g_{\text{support}}(x)
\operatorname{clip}\!\left(r_\theta(H_t,x;a_D),-\rho,\rho\right),
\]

where `p_base` is the calibrated explicit/LLM baseline, `a_D` is a source adapter, and `g_support→0` under source, capability, representation, or response-modality shift. Its input is the ordered sequence of typed `ItemContractV1` / `ObservedResponseV1` / reveal-and-assistance events—not question ids—and every prediction names the consumed event ids.

**Typed output, never a hidden-vector API.** Emit `TemporalEvidencePacketV1`: predicted fresh-independent success; `p_cold(Δ)` over actual delay; exact-response/signature probabilities where the response space is defined; scaffold-dependence and recurrence proposals; predictive surprise; explicit-vs-LLM-vs-temporal disagreement; support/OOD; calibration stratum; uncertainty; source-adapter/model/schema versions; and the final consumed event id. The recurrent hidden state remains a cache. Externally pretrained outputs begin at likelihood authority tier 1 and cannot increment `n_eff`, certify a misconception, or narrow `u` without local calibration.

**ACE-KT lesson: adopt the heterogeneous cascade as an ablation ladder, not a cognitive claim or default architecture.** [ACE-KT](https://openreview.net/pdf/fd2105d5d5780bc1f850a4b8d9f85b4b1c02e24e.pdf) applies causal convolution for local fluctuations, masked attention for contextual dependencies, and a selective SSM for temporal integration. Its ablations make the contextual structuring module the load-bearing component (up to a 7.2% AUC drop when removed), while RPM, CIM, and TeLU contribute smaller increments. Its evidence is conventional next-response BCE on five benchmark KT datasets with 200-interaction windows, not source-held-out graduate/open-ended learning. Therefore run this model race:

1. explicit ledger + frontier-LLM baseline;
2. bounded GRU residual;
3. target/graph-conditioned contextual attention + GRU;
4. matched-parameter selective SSM challenger;
5. optional local-deviation convolution and full ACE-style cascade only if each stage adds source-held-out calibration or decision value.

Use real elapsed time, session boundaries, reveal, assistance, and representation—not interaction index alone. Treat TeLU as an ordinary ablation against SiLU, not a design commitment. Name the modules `local deviation`, `context selection`, and `temporal integration`; their architecture does not establish that their hidden states are literal human cognitive stages.

**Read/write separation.** Every probe or repair is both an observation and a state-changing event. Preserve a pre-action proposal `z_t^- = f(H_{<t})` for predicting the current response and a post-action proposal `z_t^+ = T(z_t^-,a_t,o_t,reveal_t,assistance_t)` for predicting future performance. Never use a response inside the state that purportedly predicted that same response, and never model a diagnostic question as a passive sensor when it supplied practice, clues, or feedback.

**Fast source adaptation, with two private channels.** Let `a_D=(a_D^content,a_D^behavior)`. Build `a_D^content` immediately from canonical-source support examples and verified self-supervision; initialize `a_D^behavior` at the population prior/zero residual and update it only from real target-source outcomes. One/few examples may condition an ephemeral support-set encoder; 8–50 verified examples may update a tiny input/output adapter for a few gradient steps. The shared temporal backbone is never continually fine-tuned online from one learner or one source. Every adapter is source-scoped, versioned, held-out-anchor tested, rollbackable, and evaluated with 0/1/4/16/64-shot adaptation curves.

**Tutor-dialogue compiler and authority channels.** LLMKT-style turn annotation ([arXiv:2409.16490](https://arxiv.org/abs/2409.16490)) is an extraction proposal, not a mastery update. Classify each learner turn into one or more typed atoms:

- **validated performance evidence** — answer, explanation, derivation, or teach-back that passed the shared attempt/assessment contract;
- **epistemic signal** — confusion or a request about a facet; routing context, not automatic evidence of inability;
- **preference** — desired explanation mode, register, or interaction style;
- **goal/navigation** — why the concept matters or where it leads;
- **exposure/reveal** — viewed hint, answer, theorem, example, or worked step;
- **metacognitive/affective signal** — confidence, frustration, uncertainty, or perceived difficulty.

Question density can reveal where attention or unresolved uncertainty concentrates, but repeated questions are not repeated ability evidence. Likewise, "easy" and "hard" remain decomposed into self-report, observed correctness, latency/edits, hint/reveal dependence, cross-surface transfer, immediate-vs-delayed retrieval, and response-model surprisal. The LLM annotates; the domain validates, assigns authority, and persists. This guard is empirical as well as architectural: current LLMs remain weak and overconfident at cognitive-skill diagnosis ([MathCog](https://arxiv.org/abs/2504.00843)), while specialized temporal KT models still outperform LLM-only updating ([arXiv:2512.23036](https://arxiv.org/abs/2512.23036)).

**Learner gradient = robust graph decision, not vector motion.** For candidate action `a`, define the research quantity

\[
g_t(a)=
\inf_{\theta\in\mathcal C_\delta(b_t)}
\Delta P_\theta(\text{cold goal success}\mid a),
\]

then apply prerequisite/servability gates, the false-remediation ceiling, learner-burden limits, freshness/reveal constraints, and action capability requirements before comparison. The local "gradient" may advance, descend to the smallest weak prerequisite cut, repair a mechanism, switch representation, ask one discriminator, or construct a missing capability. Actual state movement is through `K_a(h′,o|h)`, never addition in the embedding space. For prerequisite-revisit versus escalation, score the minimum goal-relevant cut using horizon-aware cold availability, misconception mass, scaffold dependence, `n_eff`, edge authority, and cost of proceeding. Low support yields uncertainty/probing—not an automatic prerequisite failure.

Two amendments from the fork review:
- **Exposure/support density is a first-class field feature.** Each region carries `n_eff` and the serving propensity that generated its evidence, so sparse regions stay *uncertain* rather than implicitly looking strong because the system only served familiar surfaces. A learner who never sees diagram problems cannot reveal a diagram-transfer gap — low-support, goal-relevant regions become exploration-probe candidates instead of silently trusted.
- **Semantic–behavioral disagreement as an open-set alarm.** When the semantic view (what the LLM says the record means) and the behavioral record (what the learner actually did/transferred/retained) disagree about a region, that is a cheap misspecification signal feeding the existing open-world machinery (expand hypotheses / abstain) — the alarm proposes, it never writes state.

**Research-sweep candidate (Aug 24): if the no-smoothing baseline leaves a measured gap, use the field only as a smoother, not a structure-discoverer.**
- **Estimator**: Matérn/heat-kernel GP over the content kNN-graph — exact inference is cheap at hundreds of points, kernels respect semantic adjacency, posterior variance is the uncertainty (GeometricKernels, JMLR 2025, [arXiv:2407.08086](https://arxiv.org/abs/2407.08086)); **fixed parametric forgetting forms as the temporal kernel** — trained-once population artifacts, only per-learner scalar strengths update online (PsyINN line, [arXiv:2408.14492](https://arxiv.org/abs/2408.14492)); **density/distance-aware confidence guard** so unvisited regions report prior ignorance (DAEDL pattern, [arXiv:2409.08754](https://arxiv.org/abs/2409.08754)) — the principled implementation of the exposure-density amendment above; every computational shortcut must *widen*, never narrow, reported uncertainty (computation-aware GP principle, [arXiv:2411.01036](https://arxiv.org/abs/2411.01036)). Propagation-to-untested-concepts pattern per DisKCD ([arXiv:2405.16003](https://arxiv.org/abs/2405.16003)), with the GP replacing its population-trained GNN.
- **Refusal list (now identifiability-backed, not taste)**: no per-learner topology — even robust TDA needs sampling density we lack ([arXiv:2206.01795](https://arxiv.org/abs/2206.01795)); no per-learner intrinsic dimension ([arXiv:2507.13887](https://arxiv.org/abs/2507.13887)); no fitted regime discovery — switching-system identifiability needs long dense sequences ([arXiv:2305.15925](https://arxiv.org/abs/2305.15925)); no per-learner-fitted GP hyperparameters. **Raw per-region success averages are biased by construction under adaptive sampling** ([arXiv:2512.00222](https://arxiv.org/abs/2512.00222)) — the shipped propensity logging is what keeps debiased estimates possible; trust the model-based posterior, not empirical means. Only *metric* structure of embeddings is identifiable ([arXiv:2502.13757](https://arxiv.org/abs/2502.13757)) — phrase all field claims in distances and neighborhoods, never coordinates.

**Learner justification.** Cross-session continuity the learner can feel: the tutor lane stops re-asking what has been demonstrated, references what was struggled with last week, and adapts mode to stated preferences without treating "just show me the solution" as evidence of ignorance. Prerequisite-revisit vs. escalate decisions (minimal unsatisfied cuts scored by where error mass and weak `p_cold` actually concentrate, horizon-aware) mean the learner is neither dragged back a chapter for a one-facet gap nor escalated into a task whose prerequisites will be cold when needed. Review happens because predicted decay threatens a goal-relevant hyperedge — not because a card is due.

### C. Arm A — pooled empirical likelihood channel

**What.** The one structural gap keeping the causal EVSI lane shadow (`causal_diagnostic_selector.py:12`). Hierarchical response model pooling telemetry over the shipped item-invariant keys (`surface_group_id`, `evidence_fingerprint.source_family`, `probe_instrument_class`) with shrinkage; embedding-neighborhood (from A) nominates analogous cells for a soft prior but never contributes pseudo-counts; prompt-based frozen-LLM response predictions (Thinking-KT-style) are prior proposals, not empirical likelihoods. Positive observed records from A fill the success half of the cells. Post-MVP predicted-signature embeddings provide an ordinal separability proposal before any cell has counts. Later, math-vault-only NTKT-style LoRA upgrade (deferred, H).

Every likelihood carries an authority tier: `(0) ordinal LLM-authored separability`, `(1) externally trained population prior`, `(2) locally observed but sparse evidence`, `(3) calibrated empirical likelihood`. Robust EVSI must preserve that provenance and cannot silently turn tier 0/1 values into tier 3 arithmetic; below the declared completeness/calibration gate, the live router falls back to common-repair, direct-probe, or defer logic.

**Fusion, not evidence multiplication.** The explicit ledger, frontier LLM, retrieval context, and temporal residual often consume the same underlying events. Never multiply their posteriors as if they were independent observations. Fit an out-of-fold stacking/calibration layer over `(p_explicit, p_LLM, p_temporal, support, OOD, source family, response modality)` or retain their disagreement as an ambiguity envelope. If the learned sensor and explicit/semantic views disagree near an action boundary, widen uncertainty or escalate; averaging away disagreement is not calibration.

**High-ROI learned reliability head.** Before training a universal mastery model, train a small source-aware predictor of `GradeFlip`, `RepairFlip`, and `StateWriteFlip` from canonical support, verifier availability, valid-alternative ambiguity, evaluator disagreement, retrieval distance, response structure, and prompt/model version. This task directly predicts system failure, can use perturbation-generated labels plus human/expert anchors, and is more plausibly transferable across canonical sources than absolute student mastery.

Two amendments from the fork review:
- **Action signal-to-noise ratio (ASNR) per probe family**, tracked in the instrument-family telemetry: signal = how much the observation separates downstream repairs; noise = sensitivity to wording, grader version, slips. A probe can be highly informative about the semantic hypothesis and still have poor *action* signal — ASNR is the family-level quality metric commissioning and retirement should key on.
- **Machine-side escalation rule: Uncertainty × ActionSensitivity > τ.** For the evaluator cascade (deterministic verifier → cheap grader → strong diagnostician → learner clarification), escalate on decision impact, not raw uncertainty: a grader uncertain about a detail that changes no repair stays cheap; mild uncertainty at an action boundary escalates. Decision sufficiency applied to machine spend, via the AI-transport tiering.

**Research-sweep adoptions (Aug 24, cited) — grading as a calibrated instrument:**
- **Characterize the grader once via IRT on public data** (grader ability × response difficulty): flag hard-response signatures as low-trust evidence, especially partial credit, where "intermediate-label collapse" concentrates errors ([arXiv:2605.00238](https://arxiv.org/abs/2605.00238)).
- **Attach a hybrid confidence to every grading event** (verbalized + consistency + response-cluster heterogeneity against the learner's own history); route low-confidence grades to the clarification path ([arXiv:2605.00200](https://arxiv.org/abs/2605.00200)).
- **"Valid alternative solution" as an explicit third grading outcome**: LLM feedback agents systematically over-reject valid alternatives *and* over-validate incorrect solutions ([arXiv:2605.16207](https://arxiv.org/abs/2605.16207)) — a rubric class, not a judgment call.
- Post-hoc judge calibration against paired anchors as a trained-once artifact; mid-scale compression is a known judge pathology (matches the 4/4-rubric-forcing bug class already hit) ([arXiv:2605.09227](https://arxiv.org/abs/2605.09227)).
- **FoundationalASSIST now ships exact-response data** (which distractor was chosen, item text, 1.7M interactions — [arXiv:2602.00070](https://arxiv.org/abs/2602.00070)): the corpus for H's pooled response-prior artifact exists in the needed shape.

**Learner justification.** Every probe decision currently runs on a per-call LLM likelihood guess or stays dark. Grounded likelihoods promote the causal lane live, which the learner experiences as *minimally sufficient diagnosis*: the system asks a question only when the robust math says the answer would change the repair — and the stopping certificates (common-repair, EVPI bound, robust EVSI, all shipped in `evsi.py`) actually bind. Fewer questions before the smallest safe repair.

### D. External validity benchmarks (cheap, run early)

*Per-dataset assignments for every workstream, including the Aug 24 verdict upgrades (Eedi-2020 confidence, NeurIPS-2022 methods benchmark, EdNet forgetting kernels), live in the "Aug 24 update" section of [[Datasets]].*

**What.** (1) **ConceptKT**: run the shipped candidate-cause pipeline against expert missing-concept labels and the slip-vs-conceptual distinction — first outside measurement of the layer everything depends on. (2) **Eedi Kaggle retrieval benchmark**: given a trace, rank misconception labels; compare off-the-shelf embeddings vs BM25 vs hybrid — this *arbitrates the EduEmbed-fork question with data* instead of vibes. (3) **Grader-invariance flip-rate audit** (fork review): vary surface paraphrase, rubric-criteria order, hypothesis presence, notation, register, and grader version; measure GradeFlipRate, RepairFlipRate, StateWriteFlipRate — the *action-level* flips are the metrics that matter (a grader may tolerate wording drift while still making stable intervention decisions), and the version axis comes from A's record stamps. (4) Later: the APIET **diagnosis-ablation A/B** (same tutor, diagnostic module removed, blind comparison) — the evaluation of the system's central value claim, never yet run.

**Transfer gate added after ACE-KT review.** Random learner/item splits establish only in-distribution utility. ACE-KT's five-dataset results show that a heterogeneous convolution→attention→SSM cascade can improve ordinary KT prediction, but they do not establish transfer to a new canonical source, advanced technical content, open-ended proofs/code, or delayed retention. Every learner-facing artifact must therefore report a transfer ladder:

1. new learner, known source;
2. new item, known source;
3. entirely held-out canonical source in the same subject;
4. held-out subject at a similar level;
5. advanced/open-ended source absent from training (linear algebra, an arXiv paper, code/debugging, scientific mechanism);
6. held-out response modality (multiple choice → derivation/proof/code/diagram/explanation).

At each level compare: explicit ledger; frontier LLM with canonical context; calibrated LLM+ledger; public-data GRU/SSM alone; bounded residual; source-adapted residual; and robust disagreement envelope. Report NLL/Brier, calibration/coverage, cold-by-delay prediction, OOD abstention, `RepairFlipRate`, `StateWriteFlipRate`, downstream repair regret, `Q`, and `F`; AUC/ACC are secondary. A learned temporal feature receives no production credit for an in-domain KT gain unless it also adds value over the frontier-LLM+ledger baseline on held-out sources or safely shrinks to zero there.

**LearnLoop Transfer Suite.** Build a small, deliberately heterogeneous source suite early—at minimum school math, undergraduate linear algebra/probability, one technical arXiv paper, one programming/API source, and one non-mathematical technical source. The first version can evaluate retrieval, contract extraction, grading, valid alternatives, first divergence, recurrence, probe validity, and few-shot adaptation without waiting for seven-day outcomes. Human delayed outcomes are then layered onto the same frozen items as they accrue.

**Research-sweep adoptions (Aug 24, cited) — measurement hygiene:**
- **Chance-corrected agreement only** for any LLM-judged metric: raw agreement inflates by 33–41pp over kappa across 21 judges; high test-retest reliability coexists with severe position bias ([arXiv:2606.19544](https://arxiv.org/abs/2606.19544)). Debiasing recipe: position swap + budget-constrained rationale, which lets a mid-tier judge beat frontier judges at a fraction of cost ([arXiv:2604.23178](https://arxiv.org/abs/2604.23178)).
- **Do not count multiple LLM judges as independent evidence**: model errors remain highly correlated across model families ([ICML 2025](https://proceedings.mlr.press/v267/kim25e.html)). Use blinded human/expert anchors, model-family-aware uncertainty, and action-level flip rates; majority vote among similar judges is not a safety case. A separately trained response-bias detector is a useful evaluator-side sensor for verbosity, position, bandwagon, and sentiment effects, not a substitute for anchors ([RBD, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/095c7a06f229943c46bd0b519edf20f9-Abstract-Conference.html)).
- **Conformal risk control with an explicit abstention budget** for state-writing decisions: when base error risk exceeds target, distribution-free certification *must* abstain on a computable fraction — budget the escalate-to-learner path accordingly ([arXiv:2606.29054](https://arxiv.org/abs/2606.29054)).
- **PERRY-style prediction-powered OPE** for "would policy B have been better": the learner's sparse log as primary data, simulator rollouts as possibly-biased auxiliary data, honest confidence intervals without population training ([arXiv:2507.20068](https://arxiv.org/abs/2507.20068)).
- **Exposure-bias corrections validated in multi-round simulation only** — static replay systematically flatters policies inside a closed serve-observe loop ([arXiv:2509.00109](https://arxiv.org/abs/2509.00109)); the sim-sweep harness is the venue.

**Learner justification.** Direct: the slip-vs-misconception separation is what stands between a learner who mistyped and a learner sent to remediation for a typo. Measuring it externally is the cheapest protection against systematically mis-diagnosing the person. The ablation A/B answers whether the diagnostic machinery is actually buying the learner anything over a plain tutor — the honest question the whole product rests on.

**Product acceptance layer.** Dataset metrics commission instruments; the outcome/cost contract decides whether they help the learner. For every promoted A–I change, compare against the frozen current policy on finalized `S`, diagnostic questions `Q`, and confirmed false-remediation rate. A change may ship for lower `Q` at outcome parity or higher `S` at question parity, but never by crossing `τ_F`. Report provisional next-attempt results separately from mature cold-window results.

### E. W3 enforcement + trajectory-ensemble belief (one build)

**What.** Upgrade the sim harness's planted learner with the BEAGLE recipe: explicit flaw injection, strategist/executor decoupling (the LLM cannot silently fix its own injected mistake), observation filtering, and **non-applicability controls** (misconception fires where it should, stays quiet where it shouldn't — otherwise the sim models generalized incompetence). EvalConvoLearn certifies surface realism; Selective Flip and downstream predictive tests certify whether the simulator carries a usable belief state.

The *same generator* may then propose particles for the sparse-log belief estimator. A particle contains static slip/guess/forgetting/language/scaffold-response parameters plus a time-varying facet×capability state, active misconception mechanisms, strategy/representation, and exposure/reveal history. The filter:

1. proposes trajectories conditioned only on real events available before the decision;
2. hard-rejects only genuine accounting/contract impossibilities — unrecorded instructional transitions, reveal/familiarity inconsistency, invalid activities, impossible mechanism applicability — while treating uncertain prerequisite edges as finite-strength soft priors rather than physical laws;
3. weights particles by predictive likelihood of real observations, with sequentially masked past events available for offline calibration and genuinely future attempts reserved for evaluation rather than leaked into routing;
4. corrects simulator misspecification when a real calibration set permits (RoPE's small-real-sample correction pattern, [ICML 2025](https://proceedings.mlr.press/v267/wehenkel25a.html));
5. resamples while monitoring effective sample size, preserving diversity across repair-equivalence classes and an open-set `h_other` particle.

The surviving ensemble **is** `C_δ(b)` feeding `shared_optimal_action` and robust EVSI; its spread across repair-equivalence classes drives probe-vs-repair. This is a **model-consistent ambiguity set / validity envelope**, not a discovered boundary of the learner's true cognitive manifold. RSIR supplies the generate–filter pattern ([arXiv:2602.15659](https://arxiv.org/abs/2602.15659)), but its rank-fidelity test depends on known real targets; without a real anchor, generator-on-generator scoring measures only self-consistency. Firewall: particles never become evidence, never certify mastery, never train the next simulator, and never narrow uncertainty merely because the generator agrees with itself (RSIR's own ablation: fidelity-ungated recursion collapses −27% by iteration 2).

**Synthetic-data authority split.** Maintain two physically separate corpora and schemas. `SyntheticSourceVerified` contains generated items, paraphrases, distractors, counterexamples, mal-procedure traces, and probe candidates whose labels are checked against a canonical source, solver, compiler, rubric, or deterministic executor; it may train content-facing retrieval/ranking/validity critics because the target is independently knowable. `SyntheticPersonaTrajectory` contains simulated learner behavior and counterfactual trajectories; it may stress-test filters, improve proposal coverage, and pretrain amortized proposal networks, but it cannot calibrate human response probabilities, forgetting curves, cold outcomes, or repair effects. Only real learner observations can promote those quantities. Never merge the two tables or report their sample sizes as one training corpus.

**Amendment (fork review): the controlled-confound benchmark.** W3's flaw injection is exactly the machinery to build the Deep-Value-Benchmark analogue: plant mechanisms *correlated* with surface features in the training/eval distribution (branch-loss errors mostly in complex-number notation, method-selection errors mostly in word problems), then break the correlation at test — same surface different mechanism, same mechanism new surface, same answer signature different repair. The metric is **MechanismGeneralizationRate**: P(correct repair | surface correlation broken). This is the strongest available answer to the question next-response AUC never asks — did the system learn the mechanism or the surface cue — and it becomes the standing acceptance gate for A's recurrence detector and H's trained artifacts.

**Research-sweep adoptions (Aug 24, cited):**
- **AOMDP as the formal frame for the belief filter** ([arXiv:2510.14315](https://arxiv.org/abs/2510.14315), AISTATS 2026, Murphy-lab n=1 mHealth lineage): measurement is a first-class action with delayed state effects; the SMC posterior over *(static learner parameters, latent trajectory)* jointly is exactly this workstream's particle ensemble — adopt the framing, and its finding that measuring pays precisely when the latent state can flip the optimal action is the probe criterion restated. **Performative fixed-point semantics** for teaching: optimize for the policy best under the dynamics it *induces*; stability under regularization argues for conservative repairs when effect sizes are uncertain ([arXiv:2402.09838](https://arxiv.org/abs/2402.09838); survey: Statistical Science 2025).
- **Selective Flip Score as the synthetic-learner acceptance gate**: prompted simulators capitulate to *any* correction (SFS ≈ 0 across 4B–120B; only post-training recovers belief-consistency) — a planted learner must resist irrelevant feedback and yield to targeted feedback, or it carries no belief state ([arXiv:2605.12748](https://arxiv.org/abs/2605.12748)). Three-axis (linguistic/behavioral/cognitive) scoring rubric from [arXiv:2601.04025](https://arxiv.org/abs/2601.04025).
- **History-aware profiles validated**: compress history → condition generation on the compressed profile, scored by *downstream predictive fidelity*, not readability ([arXiv:2605.30051](https://arxiv.org/abs/2605.30051)) — the published endorsement of B's state card and its scoring rule.
- **Generator+examiner error minting** for class-labeled synthetic error corpora, grounded on the verified answer ([arXiv:2605.29007](https://arxiv.org/abs/2605.29007)).
- **Pinductor pattern**: LLM proposes POMDP world-model structure from few trajectories, refined against belief likelihood ([arXiv:2605.13740](https://arxiv.org/abs/2605.13740)) — the published version of this workstream's generator + fidelity filter.
- **Standing caution**: an amortized/trained-once discoverer's synthetic training distribution *is* its prior ([arXiv:2405.16924](https://arxiv.org/abs/2405.16924), TMLR 2025) — the synthetic-learner suite is the load-bearing specification of what any confirmer can ever detect, and must span the mechanism classes real learners exhibit.

**Learner justification.** Two distinct wins. (1) *Sparse-evidence honesty*: in the first sessions of a new vault — exactly when the system knows least — the learner gets calibrated uncertainty (wide ensemble → gentle common repairs or one well-chosen probe) instead of a confidently wrong route. (2) *Regression protection*: router recovery-rate evals against known planted misconceptions mean routing changes are tested against ground truth before any real learner pays for them, and predicted response signatures get calibrated against knowable h; the confound benchmark specifically protects the learner from a system that diagnoses by surface pattern-matching. The eventual labeled contrastive corpus (same-cause-different-surface pairs, same-answer-different-cause hard negatives) is what would honestly justify a trace-encoder fine-tune.

### F. Route-comparator completion (small engineering delta)

**What.** Most of synthesis-doc step 1 shipped (live EVSI ranking, propensity logging, decision receipts, shadow-parity gates). Remaining: (1) stamp the belief state `b_t` into `causal_probe_decision_receipts` alongside the already-logged candidates and propensities — the last sliver of the TSDR replay-conditioning discipline; (2) make the four-route race `{repair now / ask existing / construct / defer}` explicitly costed, now estimable because A turns "does a discriminator exist?" into a retrieval query and instrument-family telemetry prices construction; (3) make every route receipt outcome-contract complete: predicted `R_next`, predicted `R_cold`, predicted diagnostic-question count, chosen route and propensity, then realized `R_next`, matured `R_cold`, `Q`, confirmed `F`, provisional/final status, and the evidence ids supporting any false-remediation confirmation. Constructive route = inverse design in decision space: "generate an item where h_i and h_j produce divergent traces," mal-procedure-executed before any learner sees it.

The stamped `b_t` is a versioned decision snapshot, not a free-form profile: include `as_of_event_id`, state hash, schema/algorithm/model versions, support and missingness, likelihood-authority tiers, active repair-equivalence classes, candidate routes, and the source event ids needed to replay the choice. The later outcome join never rewrites the decision-time snapshot.

**Executable hypothesis and probe pipeline.** The target is not exact hidden-state identification; it is enough decision-relevant information to select the smallest safe repair.

1. Compile each candidate cause into an executable hypothesis: target facets/prerequisites, predicted first divergence and response signatures, applicability/non-applicability, expected repair effects, falsifiers, and provenance.
2. Lock the hypothesis set for the episode and retain `h_other`.
3. Cluster hypotheses by repair equivalence before asking anything.
4. If all plausible hypotheses share a safe repair, repair immediately.
5. Otherwise construct probes specifically for repair-distinct pairs/classes.
6. Reject any probe that is invalid, familiar/isomorphic, non-discriminating under mal-procedure execution, reveal-contaminated, ungradable, or too wording/grader sensitive (low ASNR).
7. Ask only if an admissible observation can plausibly flip the selected repair; otherwise repair, construct a better instrument, or defer.

**Distilled proposal critics — scale machine search, not learner interrogation.** Persist every generated candidate together with source-grounding checks, verifier result, mal-procedure separability, ASNR, wording/grader perturbation stability, familiarity/isomorphism status, burden estimate, and eventual decision flip. Offline, generate many candidates per hypothesis pair and train a cheap `ProbeCriticV1` / `RepairCriticV1` to rank them. Runtime pattern: frontier LLM generates a broad candidate set → learned critic ranks → deterministic/source verifier checks the top few → robust decision-EVSI chooses or rejects. The critic never certifies correctness or chooses a route; it amortizes expensive proposal search. This content-facing learned feature can improve before enough cold human outcomes exist because most of its labels are independently verifiable.

BED-LLM and related active-question systems validate LLM proposal plus information-gain scoring, but raw hypothesis entropy is the wrong live target: a question can identify the cause more precisely without changing the intervention. Define **decision-EVSI** over repair regret \(\mathcal R\):

\[
\operatorname{EVSI}_{D}(q)
=
\mathcal R_{\text{repair}}(b_t)
-
\mathbb E_o\!\left[\mathcal R_{\text{repair}}(b_{t,q,o})\right]
-
C_{\text{question}}(q)
-
C_{\text{write}}(q),
\]

where \(C_{\text{write}}\) prices retrieval practice, clues leaked by wording, induced strategy changes, familiarity/reveal contamination, and other contemporaneous state mutation. Evaluate the expectation with the joint \(K_q(h',o\mid h)\) and the recorded likelihood-authority tier; use robust/worst-case or lower-confidence value over \(\mathcal C_\delta(b)\) when likelihoods are incomplete. Stop on repair equivalence, non-positive robust decision-EVSI, an EVPI bound, no action-flipping observation, or learner-burden cap.

All four routes use one action object:

\[
u=
\bigl(
\operatorname{req}(u),
\operatorname{gain}(u),
K_u(h',o\mid h),
c(u)
\bigr),
\]

so constructive CG-Plan steps, probes, hints, repairs, practice, and audits differ by declared capability requirements/gains, read/write effects, and learner burden rather than by separate ad hoc policy machinery.

**Minimal repair and natural counterfactual contract.** A minimal repair is not the nearest explanation in embedding space. It is the smallest feasible causal intervention that covers the minimal unsatisfied prerequisite/mechanism cut, is acceptable across `C_δ(b)`, stays below `τ_F`, maximizes delayed cold success, and minimizes learner burden among outcome-equivalent actions. A natural counterfactual probe/repair keeps topic, difficulty, register, and irrelevant surface factors approximately fixed; intervenes on one suspected mechanism, representation, or prerequisite; stays inside the authored item contract; has a verified solution; and makes competing mal-procedures produce predictably divergent traces. This is causal backtracking/constrained recourse, not Euclidean nearest-neighbor generation ([Natural Counterfactuals, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/1b10264c77a2a1e0ef8abfbd68d36583-Paper-Conference.pdf); [BRACE, ICML 2025](https://proceedings.mlr.press/v267/fatemi25a.html)).

Every repair receives a fresh immediate check, a new-surface near-transfer check when appropriate, and a delayed cold audit. A guided redo measures uptake and can guide the next action, but cannot certify durable repair.

**Research-sweep adoptions (Aug 24, cited):**
- **BED-LLM / ASIG as probe proposers inside the EVSI wrapper**: EIG-scored next-question generation from the LLM's own predictive distributions ([arXiv:2508.21184](https://arxiv.org/abs/2508.21184)), amortizable into a small policy at ~25× cheaper inference with zero-shot transfer ([arXiv:2607.03426](https://arxiv.org/abs/2607.03426)) — both read-only and myopic, so they propose and the decision-EVSI+write-cost wrapper disposes. ASIG's MediQ benchmark and [MediQ's selective-question/abstention study](https://proceedings.neurips.cc/paper_files/paper/2024/hash/32b80425554e081204e5988ab1c97e9a-Abstract-Conference.html) are the closest public analogues to the diagnose-then-repair loop.
- **Sensing/control decomposition validated** (OCMDP, [arXiv:2411.07087](https://arxiv.org/abs/2411.07087)); anytime error-bounded planning for "is the expensive gold-standard probe worth it" (AEMS-SR, [arXiv:2407.18812](https://arxiv.org/abs/2407.18812)); **compressed beliefs are provably safe** within exponentially decaying value-loss bounds ([arXiv:2601.03132](https://arxiv.org/abs/2601.03132)) — structural backing for the fixed observation vector.
- **Unified action object applies across routes**: the `req / gain / K / c` contract above puts CG-Plan construction, AOMDP measurement, probes, hints, repairs, practice, and audits in one typed table, distinguished by which components are nonzero.
- **Construction-route item hygiene**: always pass the verified solution when generating distractors/probes (+8% human alignment; solution recovery, not misconception simulation, is where LLMs fail — [arXiv:2603.15547](https://arxiv.org/abs/2603.15547)); critique-then-classify rejection gate on minted items before serving (AUC .80 against expert rejection at scale — [arXiv:2608.06609](https://arxiv.org/abs/2608.06609)).

**Learner justification.** The learner is never used as the instrument of a weak question when machine effort could build a sharp one: "construct a better probe" becomes a costed alternative to "ask now," and the zero-learner-cost mal-procedure filter rejects non-discriminating candidates before administration. Deferral gets honest bookkeeping — a queued construction instead of a silent drop.

### G. Equipoise contextual bandit + plateau jump trigger (last; needs C/E data)

**What.** Separate Thompson-sampled outcome posteriors for next-attempt success `R_next` and cold success `R_cold` over pedagogy arms, context = learner-field region features, kernel-smoothed across the embedding geometry so n=1 pools instead of starving. Combine sampled heads using the declared `S = 0.75 R_cold + 0.25 R_next`; a pending cold window remains pending rather than being imputed from `R_next`. **Authority only inside the robust near-tie set** the deterministic policy declares (`randomization_layer` propensities, `policy_experiment_assignments`, `controller_outcome_windows` — migration 098 — already shipped), and only while the policy remains below `τ_F`; SPIBB-style fallback to baseline everywhere else. Amendment (fork review): **action capability embeddings** — represent each intervention by a `c_a` summarizing where it has historically worked (target mechanism, capability, burden, scaffolding, next/cold outcomes) rather than as a discrete arm, so effectiveness pools across similar repairs the same way workstream C pools likelihoods across similar items; the (repair → next/cold outcome) fields A stamps on paradigm payloads are the training data. Plateau detection (finalized `S` per diagnostic question flat while local arms keep being pulled) activates **jump arms**: representation switch, prerequisite descent via minimal cut, alternative solution-route hyperedge, tutor-mode change, or capability construction (CG-Plan's constructive route wearing the RecHarness hat). Guardrails: source-aware pre-check (rule out instrument noise before pedagogy jumps); retuning window (judge a jump on its delayed window, since prerequisite descent looks bad on the immediate next attempt by construction); jumps confined to `A_feas`.

**Research-sweep adoption (Aug 24): repair effectiveness is a *drifting* state, not a permanent fact.** Model per-arm effect as a latent state-space process (θ_{t+1} = Fθ_t + ξ) with anytime-valid inference, per the nonstationary adaptive-A/B design (AISTATS 2026) — "worked examples work for this learner" is a dynamic estimate that legitimately changes as prerequisites consolidate and fatigue patterns shift. Cautionary companion: grafting Bayesian uncertainty onto an active-measure heuristic *failed* in the realistic ADAPTS mHealth environment ([arXiv:2512.08950](https://arxiv.org/abs/2512.08950)) — structure (causal machinery, delayed feedback modeling) is what carries, not uncertainty bolted onto heuristics.

**Learner justification.** Repairs *personalize*: the system learns that this learner's applicability-condition errors respond to counterexamples but not worked examples, and starts choosing accordingly — at provably bounded regret, because it only ever experiments among actions already certified near-optimal. And plateaus stop feeling like grinding: when more-of-the-same practice stalls, the learner gets a structural change — a new representation, a targeted prerequisite hop, a differently-shaped probe — instead of the local minimum served indefinitely.

### H. Gated trained artifacts + source adaptation

**Priority split.** Source-grounded content-facing critics described in A/C/F are not blocked on large human-learning datasets and may train early when their labels are independently verified. This section governs learner-facing temporal/response models, source adapters, trace representation fine-tunes, and action-effect models—the artifacts most exposed to population/domain shift.

**External KT data is pretraining, not production truth.** FoundationalASSIST, Eedi, EdNet, and similar corpora may initialize sequence encoders, exact-response heads, confidence calibration, and generic time-gap features. They do not establish absolute difficulty, forgetting, misconception prevalence, response-time meaning, or pedagogical effects for learners studying proofs, arXiv papers, code, or other advanced/open-ended sources. The frontier LLM + canonical contract + explicit ledger is the zero-shot baseline; a public-data temporal model may only contribute through B0.5's bounded support-gated residual.

**Deferred response/trace artifacts.** NTKT-style LoRA response prior (initially math vaults only), the temporal residual backbone, and the trace-encoder fine-tune require D's source-held-out transfer gate. A trace encoder additionally requires E's controlled planted-example corpus with an evaluation target independent of the pseudo-labeler (future behavior or independently verified structure, never label recovery). Posterior trajectory samples are excluded. Until these gates hold, canonicalization and the frontier backbone deliver the transferable semantic prior; pseudo-label training without independent evaluation is circular.

**Source-adapter contract.** Preserve a frozen global backbone and train only small source-scoped support encoders, FiLM/LoRA input-output adapters, or calibration heads. `a_D^content` may learn from canonical-source self-supervision immediately; `a_D^behavior` must remain at zero/population prior until real target-source events arrive. Use three adaptation speeds: zero-gradient support-set conditioning; 1–10 gradient steps on a tiny adapter after enough verified examples; slow offline consolidation across many sources only after leave-one-source-out regression testing. Never continually update the shared backbone from one learner, and never let an adapter alter evidence, graph authority, or historical predictions without a new versioned replay.

**Flagship paper formulation (fork review): decision-conditioned shared–private learner alignment.** Semantic, behavioral, structural, and causal views share only the decision-relevant subspace — aligned by their induced *regret profiles* (‖ρ̂⁽ᵛ⁾ − ρ̂⁽ᶠᵘˢᵉᵈ⁾‖², two views count as aligned when they imply the same repair, not when their vectors are close) — while private coordinates are preserved for prediction, explanation, and open-set detection. This formalizes the plan's factorized-fields and authority-narrowing decisions; recent alignment analysis likewise finds that alignment helps only when views carry genuinely redundant information and can harm when it suppresses private signal ([ICML 2025](https://proceedings.mlr.press/v267/tjandrasuwita25a.html)). Same gate as the other trained artifacts (E's corpus + D's verdicts); its Phase-1 alignability logging runs from day one inside A's research appendix; MechanismGeneralizationRate from E's confound benchmark is its acceptance metric. Parked from the same review, for the record: the OT alignment arsenal (entropic OT eigenmaps, partial GW, JK-EGW) as paper-comparators only, and Mapper/persistent-homology probe targeting (decision-boundary targeting is strictly more disciplined; topology stays an offline audit curiosity).

**Population systems are comparators, not live authority.** Coral's disentangled collaborative learner representation ([NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/013f9cd52b38e3e53475605d2b8e7c23-Abstract-Conference.html)) is an offline representation/ablation comparator; its multi-learner assumptions do not transfer to LearnLoop's n=1 state ownership. ExeGen's learner-conditioned exercise generation ([NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/85dbd2fb8b355e4231b51e454c08ec1c-Abstract-Conference.html)) is a pipeline comparator whose agents map to proposer/verifier roles, never routing or evidence authority.

**Second flagship paper (research sweep, Aug 24): "Decision-Revealing Active Measurement in State-Changing Systems."** AOMDP ([arXiv:2510.14315](https://arxiv.org/abs/2510.14315)) proves selective measurement tames partial observability, but assumes measurement is *exact* and leaves the current state untouched (effects arrive only through the next transition). LearnLoop's setting strictly generalizes it: the joint kernel K_q(h′, e | h) models noisy observation *and* contemporaneous state mutation, with AOMDP recovered as the special case K_I(u′,e|u) = 𝟙[u′=u]·δ(e−u). The central theoretical target: replace AOMDP's weakly-revealing condition (full state identifiability) with **decision-observability** — ker M ⊆ ker Dᵀ, with quantitative constant α_D(M) — so an instrument is admissible when it reveals the state *modulo repair-equivalence*, and sample complexity is conjectured to scale with rank(D) ≤ |A|−1 rather than |H|. One open technical requirement: the static condition must be *closed under the write kernels* (beliefs indistinguishable now must stay decision-equivalent after dynamics), which is exactly where the decision-closure dimension d★ from the DSED work re-enters — the two results are one paper. Contributions ladder: AOMDP as special case → α_D condition + closure → read/write value decomposition → robust ambiguity over the decision projection → CG-Plan capability construction as actions that raise future decision-observability → evaluation on planted context-contamination and synthetic-learner domains. ActiveVOO independently supports measuring task-relevant/subgoal state rather than reconstructing the whole latent state ([NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/995c4e28ac35b90ca841053f80d2f1f8-Abstract-Conference.html)). Three-axis taxonomy unifying the frameworks: **reachability** (CG-Plan: can the decisive experiment be executed?), **observability** (AOMDP/DSED: does it reveal enough, exactly or decision-sufficiently?), **performativity** (LearnLoop: does asking change the answerer mid-observation?). This paper leads the theory track; decision-conditioned shared–private alignment (above) remains the representation-learning track, gated on E's corpus.

Also permanently out (refined verdicts): a population KT model as evidence, canonical learner state, topology, or routing authority; opaque question/KC-id models presented as cross-domain; global online fine-tuning from one learner/source; persona-simulated retention or treatment effects presented as human calibration; hyperbolic implicit hierarchy (the hypergraph owns hierarchy explicitly); bandit-as-router; LLM-as-state; and end-to-end regret-trained routing outside the equipoise slack. Population-pretrained, source-conditioned temporal models are permitted only as B0.5 bounded residual sensors under D's transfer gate.

### I. Hypergraph authoring & edge authority (added Aug 24 from the causal-discovery sweep)

**What.** The causal-discovery field converged on LearnLoop's exact architecture — LLM causal-graph benchmark scores are substantially memorization (collapse on post-cutoff graphs, [arXiv:2510.16530](https://arxiv.org/abs/2510.16530)), and LLMs should be restricted to non-decisional roles in structure discovery ([arXiv:2506.00844](https://arxiv.org/abs/2506.00844)) — direct published backing for producer–confirmer separation. Five upgrades to the hypergraph pipeline:
1. **Soft-prior edge authority** (KG-SoftMAP, [arXiv:2606.10358](https://arxiv.org/abs/2606.10358) — the closest published system to our sparse-discrete, education-domain setting): store every LLM-authored edge as a *finite-strength, confidence-weighted prior*, so the learner's longitudinal evidence can demote any authored edge; adopt its KG-corruption stress-test protocol over synthetic learners as the standing regression suite.
2. **Synergy test before certifying recipe hyperedges**: hyper-DAG identifiability theory ([arXiv:2511.03831](https://arxiv.org/abs/2511.03831)) plus the synergy signature — the *set* predicts failure while no member does ([arXiv:2409.08295](https://arxiv.org/abs/2409.08295)) — is the first principled test for whether a conjunctive edge is distinguishable from its pairwise shadow given behavioral data.
3. **PAG-style uncertain marks for the open world** (RelFCI idiom, [arXiv:2507.01700](https://arxiv.org/abs/2507.01700)): emit "latent cause possible here" as a first-class graph object instead of forcing closed-world edges — the graph-side formalization of h_other.
4. **Elicitation mechanics**: single-aspect queries (edge type / direction / necessity separately — TKDE 2025 harmonized-prior line), per-section full-local-context authoring rather than exhaustive pairwise (accuracy degrades with graph size — CausalGraphBench, ACL 2025 SRW), k-sample vote thresholds per typed edge with FP/FN control tuned on synthetic learners ([arXiv:2406.07378](https://arxiv.org/abs/2406.07378)), structure-respecting bootstrap aggregation across episode windows ([arXiv:2511.14206](https://arxiv.org/abs/2511.14206)), and **extract-then-canonicalize** for open-vocabulary node growth without fragmenting the facet inventory (EDC, [arXiv:2404.03868](https://arxiv.org/abs/2404.03868)).
5. **Decision-sufficient partial structure rather than full graph recovery**: commission only the edges/marks needed to distinguish feasible repairs or sequence choices. Partial causal structure can already support no-regret decisions under graph uncertainty and latent confounding ([NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c50e3c72bf45a361afc7c16d26c21a1a-Abstract-Conference.html)); unresolved structure remains uncertain instead of being completed for aesthetic closure.

**Learner justification.** Minimal backtracking lives or dies on edge quality: a wrongly authored hard-prerequisite edge forces the learner back through material they know, and a missed conjunctive edge sends them into tasks that fail confusingly. Soft priors mean no authored arrow ever outranks the learner's own demonstrated evidence; the synergy test means "you need A *and* B together" is claimed only when the data can actually support it; PAG marks mean the system says "something unmodeled is going on" instead of forcing a wrong diagnosis through a closed graph.

**Research-maturity rule.** The 2026 preprints in this plan are directional design evidence pending replication, not equivalent to accepted NeurIPS/ICML/JMLR results. No preprint-only claim can promote a state-writing or learner-facing policy without the same D/E/product acceptance gates as every other artifact.

---

## Sequencing

Construction order and authority-promotion order are intentionally different: receipt columns and shadow sensors can land early, but no probabilistic field, trajectory ensemble, or learned selector receives learner-facing authority until its explicit-record baseline and product gates pass.

| Order | Item | Depends on | Scale |
|---|---|---|---|
| 0 | **Event/outcome + typed-contract envelope** (`ItemContractV1`, `ObservedResponseV1`, `R_next`, delay-indexed `R_Δ`, `R_cold`, `Q`, `F`, decision-time `b_t` hash/version/support fields) | — | smallest irreversible decision; instrument and normalize first |
| 1 | **A** trace memory (write path + shadow recurrence first) | outcome/cost record fields from 0 | the foundation; start immediately |
| 1′ | **D0** ConceptKT + Eedi + grader flip audits; scaffold the LearnLoop Transfer Suite | — | parallel with A; source-held-out evaluation before model enthusiasm |
| 2 | **B0** `RouterStateV1` + no-smoothing deterministic `LearnerStateCardV1`; F decision-snapshot persistence | A, receipt schema from 0 | small, replayable state contract first |
| 2′ | **A/C/F content-facing critics in shadow** (source retrieval/reranking, isomorph/freshness, grader-risk, probe/repair critics) | typed contracts, canonical verification, D0 harness | high ROI; does not wait for cold human labels |
| 3 | **F** executable-hypothesis / repair-equivalence pipeline + four-route comparator + provisional/final outcome joins + critic telemetry | B0, A | mostly shipped; complete receipts and construction route |
| 4 | **C** arm A pooling + reliability stacking + decision-EVSI likelihood authority | A, D0 verdicts, F contract | medium; the causal-lane unlock |
| 5 | **E1** W3 enforcement + controlled-confound simulator suite + split synthetic schemas | spec exists; A helps | large; ground-truth regression harness first |
| 5′ | **I** hypergraph edge authority + elicitation hygiene | pairs with existing authoring; stress tests need E1 | small-medium; soft-prior semantics can start early |
| 6 | **B0.5** bounded source-conditioned temporal model race in shadow (LLM+ledger → GRU → contextual GRU → SSM → optional ACE cascade) | B0, typed contracts, D transfer gate; public data only as pretraining | medium; no authority until held-out-source gain |
| 7 | **E2** particle/trajectory belief in shadow | E1, C calibration; B0.5 may propose but never weight its own particles | large; model-relative ambiguity only |
| 8 | **B1 promotion decision** among no smoothing, graph-kernel smoothing, temporal residual, or calibrated disagreement envelope | B0 baseline, D verdicts, E2 uncertainty checks | only if a candidate leaves a measured product-level gain |
| 9 | **G** equipoise bandit + jump trigger | C, E evaluations, real cold-outcome accrual; B0 sufficient initially | last learner-facing learned layer |
| 10 | **H** K-shot source adapters, response/trace fine-tunes, shared-private alignment, and later action-effect models | D + E gates pass; real target-source or causal outcome data as required | explicitly gated and staged |
| † | APIET diagnosis-ablation A/B | B (tutor lane stable) | run once E's harness can host it |

The through-line, stated once: **the frontier backbone plus canonical source supplies transferable semantics; typed contracts and the explicit ledger preserve what actually happened; authored/reviewed `G` owns feasible topology; episodic memory (A) makes the system longitudinal without becoming evidence; content-facing learned critics spend machine computation to improve retrieval, grading risk, and probe construction before learner-facing data is abundant; the explicit state projections and bounded source-conditioned residual (B) make learner-specific predictions legible without one mutable profile; calibration (C) fuses overlapping sensors without double counting and makes decision-EVSI arithmetic only when its authority tier permits; source-held-out benchmarks (D) keep transfer claims honest; the ensemble (E) makes sparse ambiguity explicit without turning persona simulation into human evidence; the comparator (F) prices building against asking and stops at repair equivalence; the bandit (G) personalizes repair only inside proven-safe slack. Every learned contribution shrinks to the LLM+ledger baseline off support, and every promoted layer must either raise finalized `S` or reduce `Q` without crossing the false-remediation ceiling.**

---

*Related: [[Diagnostic Pipeline Synthesis]] · [[Capability Gated Planning, Cost to Goal Discovery]] · [[Learner Field and Directional Models Augmentation]] · [[Agent dialogue]] · [[Agent dialogue on modeling incorrect student thinking]] · [[Agent dialogue on EduEmbed]] · [[Knowledge Tracing]] · [[Datasets]] · spec_causal_learner_model.md (W0–W4)*



The plan’s core has not been replaced. The revision mainly makes the learned-model strategy more honest: **use the frontier LLM for broad semantic generalization, use canonical sources for scalable verified supervision, use small models where repeated data can beat prompting, and make those small models prove transfer before allowing them to influence learner-facing decisions.**</Agent>