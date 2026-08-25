# Learner Field and Directional Models Augmentation

*Research and architecture addendum, 2026-08-24. Extends [[Pipeline Augmentation Plan]], [[Diagnostic Pipeline Synthesis]], and [[Capability Gated Planning, Cost to Goal Discovery]]. Dataset decisions refine [[Datasets]]; representation and retrieval decisions refine [[Embedding index]], [[EduEmbed]], [[Knowledge Tracing]], and [[Latent learner manifold topology estimation]]. Synthetic-learner limits remain governed by [[Simulating students or sycophantic problem solving?]].*

> [!decision]
> LearnLoop should model the learner as a **versioned posterior field over an authored content/capability hypergraph**, not as one mutable embedding. Natural-language embeddings provide metric neighborhoods; a frozen GRU or SSM may provide bounded predictive residuals; neither creates evidence, owns learner state, or routes actions directly.

> [!note]
> The earlier phrase "GNU/SSM" is treated here as **GRU/SSM**, matching the existing [[Datasets#New consumers for existing "use" verdicts|V2 GRU/SSM behavioral residual]] entry.

## 1. What this augments

The current pipeline already separates:

- immutable attempts and dialogue events;
- canonical facets, capabilities, prerequisites, and recipe hyperedges;
- learner-state projections with explicit evidence authority;
- diagnosis hypotheses and repair-equivalence classes;
- probe EIG / EVSI;
- deterministic routing;
- optional LLM proposals.

The missing bridge is a disciplined way to use semantic geometry and population sequence models to answer four **prediction-only** questions:

1. Given this learner's real history and a fresh item, what response distribution should we expect?
2. Where is available knowledge likely to have decayed by horizon \(\Delta\)?
3. Is an observed error likely to recur across a genuinely different surface?
4. Which already-feasible repair is likely to work for this learner now and remain effective at the cold audit?

These predictions feed the learner field and the route comparator from [[Pipeline Augmentation Plan#B. Learner field + two-projection state communication]] and [[Pipeline Augmentation Plan#F. Route-comparator completion (small engineering delta)]]. They do **not** replace the evidence, diagnosis, or policy layers.

## 2. The three objects that must stay separate

Let

\[
G=(V,E,\mathcal H)
\]

be the authored and reviewed concept/facet/capability graph with typed ordinary edges \(E\) and recipe/prerequisite hyperedges \(\mathcal H\). Let \(d_\phi\) be a versioned semantic metric over factorized item, trace, hypothesis, and repair records. Let

\[
b_t(v,c,r)
=
\bigl(
p_{\text{available}},
p_{\text{cold}}(\Delta),
p_{\text{misconception}},
p_{\text{scaffold-dependent}},
n_{\text{eff}},
u
\bigr)
\]

be the learner-specific posterior field at content region \(v\), capability \(c\), and representation \(r\).

The roles are:

| Object | Owns | Does not own |
|---|---|---|
| \(G\) | admissible pedagogical structure, edge authority, prerequisites, recipes | learner evidence or a learner-specific topology |
| \(d_\phi\) | retrieval neighborhoods, soft pooling candidates, novelty/isomorph checks | pedagogical adjacency, mastery, certification |
| \(b_t\) | versioned predictions and uncertainty derived from real events | raw evidence, authored truth, policy authority |

Only metric/neighborhood claims are made about the embedding space. Coordinates, axes, intrinsic dimension, and a separately estimated per-learner topology are out. This is the sharper version of [[Latent learner manifold topology estimation]]: estimate a **field on shared structure**, not a new manifold from sparse n=1 logs.

## 3. A learner gradient is a graph decision gradient

"Move in the direction of the learner gradient" should not mean vector addition in the embedding space. It means choosing a feasible graph/hypergraph transition with the best robust change in a goal-conditioned outcome.

For a candidate action \(a\), define the research score

\[
g_t(a)
=
\inf_{\theta\in\mathcal C_\delta(b_t)}
\Delta P_\theta(\text{cold goal success}\mid a),
\]

where \(\mathcal C_\delta(b_t)\) is the robust belief/trajectory ambiguity set from [[Pipeline Augmentation Plan#E. W3 enforcement + trajectory-ensemble belief (one build)]]. The live policy still applies the declared lexicographic contract:

1. enforce hard eligibility and reveal/freshness constraints;
2. reject policies above the false-remediation ceiling;
3. maximize finalized cold-weighted outcome;
4. minimize diagnostic questions inside an outcome near-tie.

The resulting direction may be:

- advance to the next learning object;
- revisit the smallest weak prerequisite cut;
- switch representation;
- repair one error mechanism;
- serve a decision-revealing probe;
- construct a missing probe, rubric, response channel, or hypothesis compiler;
- defer until a cold observation is possible.

Actual learner-state movement occurs through the joint action kernel

\[
K_a(h',o\mid h),
\]

not through an embedding update. The embedding proposes where to look; the action and later observed outcome determine what changed.

### Prerequisite revisit versus escalation

For every goal frontier, compute a minimal unsatisfied cut over reviewed prerequisite/recipe edges. Score each member using:

- cold availability at the goal horizon;
- error or misconception mass concentrated on the cut;
- scaffold dependence;
- independent evidence support \(n_{\text{eff}}\);
- edge authority and uncertainty;
- predicted cost of proceeding while the prerequisite is weak.

If the cut is supported as weak and controls downstream success, revisit minimally. If it is satisfied and the next object is feasible, escalate. If evidence is sparse or the edge is uncertain, probe or abstain rather than forcing remediation.

## 4. Persistent state contract

The same replayable learner state should have two projections:

### `RouterStateV1`

A typed, compact observation consumed by the deterministic action router:

- `as_of_event_id`, state hash, schema version, algorithm version;
- current goal and eligible frontier;
- per-region cold and assisted estimates;
- uncertainty, exposure density, and evidence propensity;
- recurrence and scaffold-dependence features;
- active repair-equivalence classes plus `h_other`;
- response-likelihood authority tier and support counts;
- repair history with immediate and matured cold outcomes;
- fresh-probe and construction availability;
- missingness and out-of-domain flags.

### `LearnerStateCardV1`

A deterministic text rendering for the diagnostician, tutor, and item generator:

- demonstrated cold capabilities;
- assisted-only capabilities;
- repeated error families with source event ids;
- evidence for and against active hypotheses;
- repairs already tried and their outcomes;
- retention risks;
- interaction preferences;
- explicit unknowns and unsupported regions.

The card is regenerated from ledgers and versioned projections. It is not an LLM-authored persistent profile. The blind grader receives neither card nor retrieved hypotheses; this preserves the firewall in [[Pipeline Augmentation Plan#The architecture picture]].

Every action receipt should include the exact state snapshot/hash used, candidate routes, propensities, predicted next/cold outcomes, predicted question cost, selected route, and later realized outcomes.

### Recurrent hidden-state persistence

A GRU/SSM hidden state is a cache, not learner authority. It must be reproducible from:

- the ordered immutable event sequence;
- the frozen model artifact and model hash;
- the feature schema and normalization version;
- the final consumed event id.

It may be cached for latency, but rebuild must be able to discard and recompute it. Predictions derived from it remain `inferred`; they cannot enter certification or direct evidence mass.

## 5. Three learned artifacts, not one latent model

### A. Fresh-item behavioral residual

The primary learned artifact is a bounded residual over an explicit baseline:

\[
\operatorname{logit}\hat p(y_{t+1}=1)
=
\operatorname{logit}p_{\text{explicit}}
+
\operatorname{clip}(r_\theta(H_t,x_{t+1}),-\rho,\rho).
\]

`p_explicit` comes from interpretable evidence, difficulty, assistance, familiarity, and retention features. `r_theta` is a trained-once GRU or SSM sensor conditioned on the real interaction history \(H_t\) and fresh item features \(x_{t+1}\).

Required output heads:

- first-attempt correctness;
- exact response/distractor distribution where available;
- cold correctness by time-gap bin;
- abstention/OOD support;
- optionally, a recurrence proposal over canonical error signatures.

The residual must shrink toward zero off support. It never updates the learner field by itself; it proposes a prediction that later real evidence can confirm or reject.

### B. Retention and forgetting lane

Use a small, declared temporal kernel before a deep sequence model. Fit population-level decay forms once, then update only bounded per-learner strengths from real observations. Inputs should distinguish:

- elapsed time;
- fresh versus familiar surface;
- hints, answer reveal, and retries;
- representation and response type;
- prior cold evidence;
- session boundaries.

The target is `p_cold(Delta)`, not generic next-response AUC. EdNet can stress long-gap robustness, while FoundationalASSIST is the primary in-domain math source. This extends [[Pipeline Augmentation Plan#B. Learner field + two-projection state communication]] without making the smoother a structure discoverer.

### C. Action-conditioned repair-effect model

Tutor moves and repairs require a separate model because "predict the next answer" and "predict the effect of this intervention" are different estimands.

Represent each action as

\[
u=(\operatorname{req}(u),\operatorname{gain}(u),K_u(h',o\mid h),c(u)).
\]

The action-effect state-space model predicts two outcomes:

- immediate fresh uptake `R_next`;
- delayed cold retention `R_cold`.

Its inputs include the [[Datasets|Tutor Move Taxonomy]], action capability embedding, learner-field context, assistance/reveal level, and prior repair outcomes. It remains a shadow effect prior until propensity-aware or randomized data support causal interpretation. Dialogue corpora alone can pretrain action representations; they cannot identify repair effects without outcomes and treatment assignment information.

## 6. GRU first, SSM only when the data justify it

The model race should be:

1. explicit logistic/IRT + time-gap baseline;
2. bounded GRU residual;
3. matched-parameter selective SSM challenger;
4. optional staged/hybrid architecture only after the simpler residuals saturate.

Why GRU first:

- lower implementation and audit cost;
- strong baseline on medium histories;
- easier state replay and ablation;
- enough capacity to test whether sequential residual signal exists at all.

Why keep an SSM challenger:

- long histories and irregular temporal dependencies may exceed a small GRU's effective memory;
- selective SSMs can offer linear sequence scaling;
- [ACE-KT](https://openreview.net/pdf/fd2105d5d5780bc1f850a4b8d9f85b4b1c02e24e.pdf), accepted at AISTATS 2026, reports gains from a staged encoder ending in a selective structured SSM;
- [MCSKT](https://doi.org/10.1016/j.engappai.2026.114312) separately reports a dual question/concept Mamba encoder, reinforcing factorization rather than one hidden student vector.

Why the SSM needs a gate:

- [State-space Logit Correction](https://arxiv.org/abs/2606.14123), accepted at ECML PKDD 2026, derives a Bernoulli information floor and finds that temporal tracking adds no benefit at the studied densities even when state-space shrinkage helps static item bias;
- many LearnLoop regions will be much sparser than population KT benchmarks;
- long-sequence efficiency is irrelevant when the decision-relevant local history is short;
- a larger hidden state can improve AUC while worsening calibration, OOD confidence, or repair decisions.

Define a `temporal_detectability_gate` before promoting the SSM. It must show, on held-out learners and fresh items:

- significant cold NLL/Brier improvement over GRU and explicit baselines;
- benefit concentrated in supported sequence-length/time-gap strata rather than item-id leakage;
- stable calibration under problem-type and new-skill shift;
- lower downstream repair regret or fewer diagnostic questions without breaching the false-remediation ceiling;
- reproducible hidden-state replay and acceptable latency.

If it fails, retain the GRU or explicit kernel. "SSM is newer" is not an acceptance criterion.

## 7. Dataset-to-artifact audit

This table refines [[Datasets]] for directional learned artifacts.

| Dataset | Useful signal | Best consumer | Verdict | Main caveat |
|---|---|---|---|---|
| Eedi NeurIPS 2020 | longitudinal correctness, distractors, confidence | response calibration; believed-vs-doubted recurrence; hard negatives | **Use for calibration and evaluation** | map item/KC identities to canonical text carefully; competition terms must be checked |
| Eedi NeurIPS 2022 follow-up | causal discovery and CATE tasks | hyperedge confirmer; offline repair-effect/OPE methods | **Methods benchmark** | not a production learner prior |
| Eedi Mining Misconceptions | wrong-answer-to-misconception labels | recurrence encoder; same-answer/different-cause hard negatives; predicted-signature evaluation | **Primary diagnostic benchmark** | labels are item/distractor anchored, not longitudinal learner truth |
| TutorMoments-Preview | 462 real sessions, 520 frozen moments, human/LLM-assisted tutor-quality labels | tutor-action evaluator; judge anchors; simulator/response-policy benchmark | **Evaluation and action-representation data** | too small and too confounded to estimate causal learning effects; one program |
| ASSISTments 2009/2015 | standard KT sequences | legacy comparability only | **Skip for training** | FoundationalASSIST is richer and closer to the required data contract |
| FoundationalASSIST | 1.7M interactions, 5,000 learners, full item text, first answer text, distractors, hints, reveal, time, 224 skills | primary GRU/SSM response residual; exact-response head; forgetting fit; cold-start protocol | **Primary trained-artifact source** | first answer only; `discrete_score` conflates first-try correctness with help; CC BY-NC 4.0 and gated responsible-use access |
| EdNet | 131M timestamped interactions, long histories, elapsed time, richer action streams in KT2-4 | forgetting/time-gap robustness; long-sequence efficiency; action-sequence pretraining | **Use narrowly** | Korean TOEIC domain and ID-heavy semantics; not evidence for math transfer or causal tutoring effects |
| Tutor Move Taxonomy | theory-aligned discrete action vocabulary | action capability schema and labels | **Adopt as schema** | taxonomy supplies action identity, not effect size |
| Million Tutoring Moves v1 | 4,654 authentic math tutoring transcripts | tutor-move sequence encoder; action representation pretraining; dialogue annotation | **Use for representation and observational priors** | outcome and assignment structure must be audited before any effect claim |
| ConceptKT | expert concept-deficiency and first-divergence-style supervision | trace/hypothesis encoder validation; mechanism generalization; slip-vs-gap audit | **Primary diagnostic evaluation** | not the main long-sequence training corpus |
| EvalConvoLearn | conversation quality and learner-simulation evaluation | simulator admission and dialogue-policy evaluation | **Evaluation only** | realism does not establish cognitive or causal fidelity |
| QATD-2k | 1,971 question-anchored tutoring conversations, turn order, speaker, talk-move predictions, topic metadata | dialogue event compiler; question-intent classifier; simulator evaluation | **Use early for dialogue models** | GPT-applied move labels need human-anchor calibration; CC BY-NC-SA 4.0; not mastery evidence |
| BePKT | programming KT traces | future programming-vault response prior | **Park** | domain mismatch for current math vaults |
| GenAICanHarmLearning | intervention and learning-harm evaluation patterns | false-remediation and over-helping safety benchmark | **Use as evaluation design** | does not provide a general learner-state training corpus |
| MediQ | adaptive question-asking before diagnosis | route-comparator and probe-policy benchmark | **Evaluation only** | medical diagnosis is an analogy; responses do not model learning transitions |
| LongMemEval / LoCoMo / PrecisionMemBench | longitudinal memory retrieval stress tests | trace-memory retrieval harness | **Use harness shapes** | agent memory is not learner modeling or certification |

### Primary FoundationalASSIST feature contract

The public dataset card confirms the unusually useful combination of item text, exact first answer, distractor options, hint count, reveal status, timestamp, learner id, problem type, and skill links. Normalize it into the same factorized trace form proposed by [[Diagnostic Pipeline Synthesis#Layer 2 — Memory & retrieval (the reshaped EduEmbed fork)]].

Do not train directly on `discrete_score` without reconstructing the event semantics. It is one only for an unassisted first-try success; a correct answer following support can be scored zero. The model must receive separate fields for:

- first-answer correctness;
- answer content/distractor;
- hint count;
- answer reveal;
- problem/answer type;
- elapsed/session gap where recoverable;
- skill and text-derived canonical mapping.

### What the tutoring datasets can and cannot train

[[Datasets#New consumers for existing "use" verdicts|Tutor Move Taxonomy and Million Tutoring Moves]] can initialize an action encoder or an observational transition prior. QATD-2k can train dialogue-turn annotation and learner-question routing. TutorMoments can score whether a move preserves productive struggle.

None of these alone can answer "did move \(u\) cause durable learning?" That requires:

- pre-action learner state;
- action propensity or assignment mechanism;
- immediate fresh outcome;
- delayed cold outcome;
- reveal and assistance accounting;
- enough overlap between alternative actions.

Until those fields exist, the action-effect SSM is predictive and shadow-only.

## 8. Training and evaluation protocol

### Split design

Random interaction splits are prohibited because they leak learner, item, and skill identity. Report at least:

1. held-out learners;
2. held-out items/surfaces;
3. held-out skills or concept regions where possible;
4. chronological future windows;
5. early-history windows separately from mature histories;
6. problem-type strata;
7. same-concept/new-surface transfer;
8. source-dataset-to-LearnLoop domain shift.

[The 2026 FoundationalASSIST cold-start replication](https://arxiv.org/abs/2606.11004) shows that performance changes both across practice opportunities and across problem types. These strata become required reports, not optional analysis.

[MAML-KT](https://arxiv.org/abs/2603.00137) contributes a useful held-out-new-student and early-window protocol. Adopt the protocol, not online one-or-two-step per-learner gradient adaptation: LearnLoop's artifact should remain frozen and replayable until a separate safety case exists.

### Metrics

Predictive metrics:

- cold-window Brier score and NLL;
- ECE/reliability by support and problem type;
- exact-response or distractor top-k accuracy;
- held-out item/skill performance;
- abstention risk and OOD false confidence;
- AUC only as a secondary discrimination report.

Decision metrics:

- finalized `S = 0.75 R_cold + 0.25 R_next`;
- diagnostic questions `Q`;
- confirmed false-remediation rate `F` and ceiling violations;
- RepairFlipRate under notation/register perturbations;
- MechanismGeneralizationRate under broken surface/mechanism correlation;
- action regret versus the explicit no-model baseline;
- `no_data`/abstention frequency.

Operational metrics:

- full and incremental replay equality;
- artifact and feature-version provenance;
- inference latency and memory;
- state-cache invalidation correctness;
- coverage by learner-history and region-density strata.

### Required ablations

- explicit baseline only;
- explicit + recency/BM25 retrieval;
- explicit + frozen embeddings;
- explicit + GRU residual;
- explicit + matched SSM residual;
- with and without item text;
- with and without item ids;
- with and without assistance/reveal fields;
- random versus chronological split;
- learner/item/skill cold-start slices;
- response predictor versus action-effect predictor kept separate.

The item-id ablation is load-bearing: a high-performing model that collapses without ids may be an item memorizer, not a transferable fresh-item prior.

## 9. Supplementary 2026 research adoptions

These papers were not yet referenced in the existing brainstorming plan.

### Adopt: specialized temporal models before LLM prediction

[Faster, Cheaper, More Accurate: Specialised Knowledge Tracing Models Outperform LLMs](https://arxiv.org/abs/2603.02830) finds small KT models more accurate, faster, and cheaper than LLMs for future-response prediction. This reinforces the architecture split:

- backbone LLM: semantic compiler, hypothesis/probe/repair proposer;
- GRU/SSM: frozen numeric prediction sensor;
- deterministic domain layer: evidence, state, and routing authority.

FoundationalASSIST independently reports that frontier LLMs barely beat a trivial KT baseline and fall below chance on item discrimination ([dataset paper](https://arxiv.org/abs/2602.00070)). The backbone should not supply load-bearing numeric response likelihoods without empirical calibration.

### Adopt: a temporal detectability gate

[Recovering Stranded Discrimination in Knowledge Tracing](https://arxiv.org/abs/2606.14123) shows both sides of the decision: empirical-Bayes state-space shrinkage can repair sparse item bias, but temporal drift is undetectable below an information floor. Add a pre-fit and post-fit detectability report per prediction head and region. If the data cannot resolve dynamics, use static shrinkage and widen uncertainty.

### Compare: staged SSM, do not copy its cognitive semantics

[ACE-KT](https://openreview.net/pdf/fd2105d5d5780bc1f850a4b8d9f85b4b1c02e24e.pdf) is a useful SSM challenger because it separates rhythm, contextual structure, and temporal integration. The pattern maps to LearnLoop as:

1. time/exposure features;
2. canonical content and operation features;
3. temporal residual integration.

Its hidden state is still a response-prediction representation, not demonstrated knowledge or a causal cognitive state.

### Adopt: value-of-sequencing before expensive sequencing

[Stochasticity Is Not the Hard Part](https://arxiv.org/abs/2608.05455) studies instruction over prerequisite DAGs and provides a computable \(m\Delta\) upper bound on the value of optimizing sequence. It suggests a new gate ahead of the learner-gradient planner:

- if estimated sequence value is small, use a simple feasible topological order and spend no learner/model budget on fine-grained optimization;
- if value is high but graph width is small, use exact or bounded dynamic programming;
- otherwise use the existing route-aware heuristic and report the unresolved combinatorial uncertainty.

The paper assumes failure leaves learner state unchanged, so it does not replace LearnLoop's dual-effect model. Its value-of-sequencing diagnostic is the transferable result.

### Adopt protocol only: cold-start meta-learning

[MAML-KT](https://arxiv.org/abs/2603.00137) makes new-student evaluation honest and shows that new-skill encounters can look like model instability. Use its learner-held-out early-window evaluation and report skill novelty. Do not introduce per-learner online fine-tuning until it can preserve replay, uncertainty, and the evidence firewall.

## 10. Connection to CG-Plan and probe selection

The directional models supply sensors to the four-route comparator, not a fifth route. The route set remains:

\[
\{\text{repair now},\ \text{ask existing},\ \text{construct},\ \text{defer}\}.
\]

For a probe \(q\), use decision-EVSI rather than hypothesis entropy alone:

\[
\operatorname{EVSI}_D(q)
=
R_{\text{repair}}(b_t)
-
\mathbb E_o R_{\text{repair}}(b_{t,q,o})
-
C_{\text{question}}
-
C_{\text{write}}.
\]

The GRU/SSM may improve \(P(o\mid q,h)\) or the joint \(K_q(h',o\mid h)\), but only at its recorded likelihood-authority tier. If calibration/support is incomplete, fall back to:

- a common safe repair;
- an ordinal discriminator;
- construction of a better instrument;
- deferral/abstention.

Stop probing when plausible hypotheses are repair-equivalent, when robust EVSI is non-positive, when the answer cannot flip the action, or when the burden cap binds. This preserves the central interpretation of [[Capability Gated Planning, Cost to Goal Discovery#The central LearnLoop interpretation]].

## 11. Sparse logs and trajectory simulation

The trajectory generator and GRU/SSM must remain separate artifacts:

- the GRU/SSM predicts real future observations from real past observations;
- the generator proposes possible latent paths under sparse evidence;
- the RSIR-like filter weights paths against real observations and typed transition constraints;
- the surviving ensemble supplies robust ambiguity to the router;
- no posterior particle or generated response becomes evidence or recursive training data.

Hard filters should cover actual impossibilities and accounting rules: no unrecorded instructional transition, reveal/familiarity consistency, valid activity contracts, plausible time evolution, and misconception applicability. Uncertain prerequisite edges are soft priors, not physics. The result is a **model-relative validity envelope**, not the true boundary of the learner's cognitive manifold.

Acceptance still requires the non-applicability and Selective Flip checks in [[Simulating students or sycophantic problem solving?]] and the controlled-confound benchmark in [[Pipeline Augmentation Plan#E. W3 enforcement + trajectory-ensemble belief (one build)]].

## 12. Revised build order

### Phase 0 — instrumentation and baselines

- finalize factorized event features and assistance/reveal semantics;
- add state snapshot/hash to route receipts;
- implement explicit response, retention, and item-bias baselines;
- build learner/item/skill/chronological split harnesses;
- add temporal-detectability and value-of-sequencing reports.

### Phase 1 — bounded GRU residual in shadow

- train on FoundationalASSIST;
- use text/KC features rather than relying on item ids;
- predict first response, exact response where possible, and cold/time-gap heads;
- freeze artifact and replay from immutable events;
- commission only as a router sensor if cold calibration and decision metrics improve.

### Phase 2 — SSM challenger

- matched feature set, parameter budget, and splits;
- include EdNet only for long-sequence/time-gap robustness;
- promote only in strata passing `temporal_detectability_gate`;
- otherwise retain GRU or static shrinkage.

### Phase 3 — action representation and repair-effect prior

- adopt Tutor Move Taxonomy;
- pretrain on MTM and QATD-2k;
- calibrate action quality on TutorMoments;
- remain shadow until LearnLoop accumulates propensity-stamped next/cold outcomes.

### Phase 4 — robust trajectory ensemble

- propose sparse-log trajectories;
- filter against real observations and typed validity;
- preserve `h_other` and misspecification alarms;
- feed only the robust ambiguity set to shared-optimal-action and decision-EVSI.

### Phase 5 — optional trained trace geometry

Only after [[Pipeline Augmentation Plan#D. External validity benchmarks (cheap, run early)]] shows that canonicalized off-the-shelf retrieval is materially below ceiling and the synthetic controlled-confound suite supplies an independent future-behavior target.

## 13. Changes to carry back into the main plan

1. Rename the deferred "V2 GRU/SSM behavioral residual" as two challengers: **V1 bounded GRU residual; V2 density-gated SSM**.
2. Add `temporal_detectability_gate` and static empirical-Bayes shrinkage fallback.
3. Split response prediction from the action-conditioned repair-effect state-space model.
4. Add held-out learner, item, skill, problem-type, and early-history reporting.
5. Add an \(m\Delta\)-style value-of-sequencing gate before expensive learner-gradient optimization.
6. Treat recurrent hidden state as a replayable cache with event cursor and artifact hash.
7. Keep exact response/distractor prediction as a first-class head; binary correctness throws away diagnostic information available in FoundationalASSIST and Eedi.
8. Record dataset license, access conditions, domain, and intended artifact in every model card.

## 14. Final recommendation

Build the explicit learner field and deterministic state card first. Train a small bounded GRU residual on FoundationalASSIST as the first population sensor. Give an SSM the opportunity to beat it under honest learner/item/skill cold-start and delayed-outcome evaluation, but require evidence that temporal dynamics are detectable. Use EdNet for time robustness, not semantic transfer. Use tutoring datasets to learn action representations and evaluate productive struggle, not to claim causal repair effects prematurely.

The intended architecture remains:

> **real events own evidence; authored/reviewed structure owns feasible topology; versioned projections own learner state; learned sequence models supply bounded predictions; LLMs propose semantic artifacts; the deterministic route comparator owns learner-facing action.**

Related notes: [[Pipeline Augmentation Plan]] · [[Diagnostic Pipeline Synthesis]] · [[Capability Gated Planning, Cost to Goal Discovery]] · [[Datasets]] · [[Knowledge Tracing]] · [[Embedding index]] · [[EduEmbed]] · [[Latent learner manifold topology estimation]] · [[Simulating students or sycophantic problem solving?]]
