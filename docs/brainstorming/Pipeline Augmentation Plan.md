# Pipeline Augmentation Plan

*Finalized 2026-08-24 from the dialogue trace over [[Diagnostic Pipeline Synthesis]], [[Capability Gated Planning, Cost to Goal Discovery]], [[Agent dialogue]], [[Agent dialogue on modeling incorrect student thinking]], [[Agent dialogue on EduEmbed]], the RSIR / RecHarness / Q-matrix / L-HAKT / RouterXBench reviews, and a code survey of the shipped substrate. Amended same day with six adoptions from the forked multi-view/alignment research review (decision-conditioned shared–private alignment, escalation rule, controlled-confound benchmark, ASNR/flip-rates, exposure density, action capability embeddings), the trace-record feature pass, the outcome/cost + embedding-authority decisions below, and the architecture review summarized in [[Learner Field and Directional Models Augmentation]]. Every workstream is coupled to its learner-journey justification — if an item's justification is weak, cut the item.*

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

### Outcome and cost contract

Every workstream uses the same episode-level outcome:

\[
S = \alpha R_{\text{cold}} + (1-\alpha)R_{\text{next}},
\qquad \alpha = 0.75 \text{ initially},
\]

where `R_next` is success on the first fresh, unassisted, independently attempted item after the action, and `R_cold` is success on the next eligible delayed cold-retrieval attempt under the reveal ledger. `R_next` is available early and marks the receipt provisional; `R_cold` later finalizes it. The initial 0.75/0.25 weighting states the product preference for durable retrieval without discarding the value of immediate uptake; it is a declared policy parameter, not a fitted per-learner quantity.

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

### H. Deferred trained artifacts (explicitly gated)

NTKT-style LoRA response prior (FoundationalASSIST + Eedi, math vaults only) and the trace-encoder fine-tune. Gate: D's Eedi benchmark shows off-the-shelf retrieval materially below ceiling, **and** E's controlled planted-example corpus provides in-domain labels with an evaluation target independent of the pseudo-labeler (future behavior, never label recovery). Posterior trajectory samples are excluded. Until both gates hold, the fork is low-ROI: canonicalization already delivers most of the invariance a contrastive fine-tune would learn, and pseudo-label training without independent evaluation is circular.

**Flagship paper formulation (fork review): decision-conditioned shared–private learner alignment.** Semantic, behavioral, structural, and causal views share only the decision-relevant subspace — aligned by their induced *regret profiles* (‖ρ̂⁽ᵛ⁾ − ρ̂⁽ᶠᵘˢᵉᵈ⁾‖², two views count as aligned when they imply the same repair, not when their vectors are close) — while private coordinates are preserved for prediction, explanation, and open-set detection. This formalizes the plan's factorized-fields and authority-narrowing decisions; recent alignment analysis likewise finds that alignment helps only when views carry genuinely redundant information and can harm when it suppresses private signal ([ICML 2025](https://proceedings.mlr.press/v267/tjandrasuwita25a.html)). Same gate as the other trained artifacts (E's corpus + D's verdicts); its Phase-1 alignability logging runs from day one inside A's research appendix; MechanismGeneralizationRate from E's confound benchmark is its acceptance metric. Parked from the same review, for the record: the OT alignment arsenal (entropic OT eigenmaps, partial GW, JK-EGW) as paper-comparators only, and Mapper/persistent-homology probe targeting (decision-boundary targeting is strictly more disciplined; topology stays an offline audit curiosity).

**Population systems are comparators, not live authority.** Coral's disentangled collaborative learner representation ([NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/013f9cd52b38e3e53475605d2b8e7c23-Abstract-Conference.html)) is an offline representation/ablation comparator; its multi-learner assumptions do not transfer to LearnLoop's n=1 state ownership. ExeGen's learner-conditioned exercise generation ([NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/85dbd2fb8b355e4231b51e454c08ec1c-Abstract-Conference.html)) is a pipeline comparator whose agents map to proposer/verifier roles, never routing or evidence authority.

**Second flagship paper (research sweep, Aug 24): "Decision-Revealing Active Measurement in State-Changing Systems."** AOMDP ([arXiv:2510.14315](https://arxiv.org/abs/2510.14315)) proves selective measurement tames partial observability, but assumes measurement is *exact* and leaves the current state untouched (effects arrive only through the next transition). LearnLoop's setting strictly generalizes it: the joint kernel K_q(h′, e | h) models noisy observation *and* contemporaneous state mutation, with AOMDP recovered as the special case K_I(u′,e|u) = 𝟙[u′=u]·δ(e−u). The central theoretical target: replace AOMDP's weakly-revealing condition (full state identifiability) with **decision-observability** — ker M ⊆ ker Dᵀ, with quantitative constant α_D(M) — so an instrument is admissible when it reveals the state *modulo repair-equivalence*, and sample complexity is conjectured to scale with rank(D) ≤ |A|−1 rather than |H|. One open technical requirement: the static condition must be *closed under the write kernels* (beliefs indistinguishable now must stay decision-equivalent after dynamics), which is exactly where the decision-closure dimension d★ from the DSED work re-enters — the two results are one paper. Contributions ladder: AOMDP as special case → α_D condition + closure → read/write value decomposition → robust ambiguity over the decision projection → CG-Plan capability construction as actions that raise future decision-observability → evaluation on planted context-contamination and synthetic-learner domains. ActiveVOO independently supports measuring task-relevant/subgoal state rather than reconstructing the whole latent state ([NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/995c4e28ac35b90ca841053f80d2f1f8-Abstract-Conference.html)). Three-axis taxonomy unifying the frameworks: **reachability** (CG-Plan: can the decisive experiment be executed?), **observability** (AOMDP/DSED: does it reveal enough, exactly or decision-sufficiently?), **performativity** (LearnLoop: does asking change the answerer mid-observation?). This paper leads the theory track; decision-conditioned shared–private alignment (above) remains the representation-learning track, gated on E's corpus.

Also permanently out (unchanged verdicts): population KT models in the loop (PLKT / MOSAIC / NSKT / TSDR-as-model / L-HAKT), hyperbolic implicit hierarchy (the hypergraph owns hierarchy explicitly), bandit-as-router, LLM-as-state, end-to-end regret-trained routing outside the equipoise slack.

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
| 0 | **Event/outcome contract + F receipt envelope** (`R_next`, `R_cold`, `Q`, `F`, provisional/final state, decision-time `b_t` hash/version/support fields) | — | smallest irreversible decision; instrument first |
| 1 | **A** trace memory (write path + shadow recurrence first) | outcome/cost record fields from 0 | the foundation; start immediately |
| 1′ | **D** ConceptKT + Eedi benchmarks | — | weekend-scale each; parallel with A |
| 2 | **B0** `RouterStateV1` + no-smoothing deterministic `LearnerStateCardV1`; F decision-snapshot persistence | A, receipt schema from 0 | small, replayable state contract first |
| 3 | **F** executable-hypothesis / repair-equivalence pipeline + four-route comparator + provisional/final outcome joins | B0, A (retrieval costing) | mostly shipped; complete receipts and construction route |
| 4 | **C** arm A pooling + decision-EVSI likelihood authority | A, D verdicts, F contract | medium; the causal-lane unlock |
| 5 | **E1** W3 enforcement + controlled-confound simulator suite | spec exists; A helps | large; ground-truth regression harness first |
| 5′ | **I** hypergraph edge authority + elicitation hygiene | pairs with existing authoring; stress tests need E1 | small-medium; soft-prior semantics can start early |
| 6 | **E2** particle/trajectory belief in shadow | E1, C calibration where available | large; model-relative ambiguity only |
| 7 | **B1** graph-kernel learner-field smoothing in shadow | B0 baseline, A, E2 uncertainty checks | only if no-smoothing baseline leaves a measured gap |
| 8 | **G** equipoise bandit + jump trigger | C, E evaluations, cold-outcome accrual; B0 sufficient initially | last learner-facing learned layer |
| 9 | **H** trained trace/response/alignment artifacts | D + E gates pass; independent future-behavior target | deferred |
| † | APIET diagnosis-ablation A/B | B (tutor lane stable) | run once E's harness can host it |

The through-line, stated once: **the outcome/cost contract says what improvement means; authored/reviewed `G` owns feasible topology; episodic memory (A) makes the stateless backbone longitudinal without becoming evidence; the explicit state projections and later field (B) make learner-specific `b_t` legible without becoming one mutable profile; calibration (C) makes decision-EVSI arithmetic only when its authority tier permits; benchmarks (D) keep diagnosis honest; the ensemble (E) makes sparse ambiguity explicit without turning simulation into evidence; the comparator (F) prices building against asking and stops at repair equivalence; the bandit (G) personalizes repair only inside proven-safe slack. Every layer must either raise finalized `S` or reduce diagnostic questions `Q` without crossing the false-remediation ceiling, so the learner spends reclaimed minutes at the frontier.**

---

*Related: [[Diagnostic Pipeline Synthesis]] · [[Capability Gated Planning, Cost to Goal Discovery]] · [[Learner Field and Directional Models Augmentation]] · [[Agent dialogue]] · [[Agent dialogue on modeling incorrect student thinking]] · [[Agent dialogue on EduEmbed]] · [[Knowledge Tracing]] · [[Datasets]] · spec_causal_learner_model.md (W0–W4)*
