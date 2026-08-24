# Pipeline Augmentation Plan

*Finalized 2026-08-24 from the dialogue trace over [[Diagnostic Pipeline Synthesis]], [[Capability Gated Planning, Cost to Goal Discovery]], [[Agent dialogue]], [[Agent dialogue on modeling incorrect student thinking]], [[Agent dialogue on EduEmbed]], the RSIR / RecHarness / Q-matrix / L-HAKT / RouterXBench reviews, and a code survey of the shipped substrate. Every workstream is coupled to its learner-journey justification — if an item's justification is weak, cut the item.*

---

## The architecture picture

One stack, one division of labor. The backbone LLM keeps what it is good at — semantic compression (grader → canonical diagnostic text), zero-shot proposal (hypotheses, probes, response signatures on never-seen items), open-world expansion (new misconceptions without a fixed taxonomy). Everything else exists to supply what statelessness takes away: **memory**, **calibration**, **belief**, and **ground truth**.

```
                    ┌─ blind grader (backbone) ─ canonicalized causes ─┐
observed attempt ──►│                                                  ▼
                    │                                    A. TRACE MEMORY (embedding index,
                    │                                       factorized fields, MERIT payloads)
                    │                                                  │
                    │              B. LEARNER FIELD over content manifold
                    │                 (temporal state; two projections:
                    │                  typed vector → router, rendered card → backbone)
                    │                                                  │
                    │        E. BELIEF: RSIR-filtered trajectory ensemble = C_δ(b)
                    │           (BEAGLE-enforced generator + typed-validity + held-out fidelity)
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

Standing invariants (violating any of these is a bug, not a tradeoff):

1. **Blind grader stays blind** — hypotheses and retrieved memory enter the diagnostician/tutor/generator roles, never the grading role (self-confirming-loop firewall).
2. **Vector arithmetic never creates evidence** — the manifold informs priors, readiness, candidates; only observations certify. Same authority level as graph propagation.
3. **The router stays a deterministic state machine with a fixed observation vector** (Hey-Chat lesson). Learned components are sensors and within-slack selectors, never the route authority.
4. **Rewards and promotions key on delayed cold outcomes**, never same-session correctness (reward-hacking firewall).
5. **Synthetic trajectories are posterior samples, never training data** (RSIR-collapse firewall).

---

## Workstreams

### A. Trace memory — embedding index with MERIT-shaped payloads

**What.** Off-the-shelf embeddings (local sentence-transformer as an optional extra, or embedding endpoint via the AI transport layer — a *separate* model; interop with the backbone happens only at the text level) over canonicalized, deterministically-templated records: `CandidateCause` structures (already lossless at `attempts/grading.py:1062`), `causal_hypotheses` rows, probe instrument cards, **and positive demonstrated-capability records** stamped with reveal/assistance context. Factorized fields (surface / facet-operation / diagnosis / mechanism embedded separately; optional joint composite) because consumers need opposite invariances. Derived tables in SQLite, `embedding_model_version` stamped, rebuildable in replay; brute-force cosine at n=1 scale. Hybrid retrieval (semantic + exact-match on canonical ids).

Three consumers:
- **Recurrence detection**: kNN over hypothesis embeddings run *in shadow* beside the string-equality keys in `causal_factor_deferral.py:197` / `repositories.py:2372`, logging both, before granting deferral authority.
- **Diagnoser paradigm injection**: top-k prior trace records rendered as structured (observed / hypothesized / repair tried / cold outcome) text into the causal-attribution prompt. Claims still gate; retrieval only feeds the proposer.
- **Freshness/isomorph gating**: distance-to-administered on minted single-use surfaces; inverse query (same facet, different surface) serves the cold lane.

**Learner justification.** *"It remembers my mistake."* Today the third occurrence of a recurring misconception opens a fresh diagnostic episode — more probing — because string equality never connected the episodes. With recurrence working, K=3 fires and the learner gets escalated repair instead of re-interrogation. Paradigm injection means repairs target the *family* ("third applicability-condition failure across different theorems") instead of whack-a-mole on the surface instance. The isomorph gate stops near-duplicate questions that feel repetitive and quietly contaminate coldness measurement. Net: fewer questions, smarter repairs, probes that feel fresh. Learner attention is the scarce, non-renewable resource; this is the single biggest spend reduction available.

### B. Learner field + two-projection state communication

**What.** Kernel-weighted aggregation over trace records (recency-decayed, assistance-discounted, evidence-quality-weighted) into a field over the content manifold: per-region `p_available`, `p_cold(Δ)`, misconception mass, uncertainty. Derived, replayable. Two projections:
- **Typed observation vector → router**: upgrade `state_signals.py` inputs from rule-derived booleans to calibrated probabilities (`P(cold failure at Δ)`, recurrence counts, scaffold dependence). Shadow first.
- **Rendered learner-state card → backbone**: compact canonical text digest (demonstrated capabilities cold-vs-assisted, active hypotheses with counts and tried repairs, retention risks, interaction preferences) injected into diagnostician/tutor/generator prompts every call.

Folds in tutor-dialogue evidence: LLMKT-style turn annotation at discounted weight; learner questions split into the epistemic channel (evidence records near a facet region) vs. the preference channel (tutor policy, not mastery). "What does the learner ask about frequently / struggle with across questions" becomes readable as record density at a region.

**Learner justification.** Cross-session continuity the learner can feel: the tutor lane stops re-asking what has been demonstrated, references what was struggled with last week, and adapts mode to stated preferences without treating "just show me the solution" as evidence of ignorance. Prerequisite-revisit vs. escalate decisions (minimal unsatisfied cuts scored by where error mass and weak `p_cold` actually concentrate, horizon-aware) mean the learner is neither dragged back a chapter for a one-facet gap nor escalated into a task whose prerequisites will be cold when needed. Review happens because predicted decay threatens a goal-relevant hyperedge — not because a card is due.

### C. Arm A — pooled empirical likelihood channel

**What.** The one structural gap keeping the causal EVSI lane shadow (`causal_diagnostic_selector.py:12`). Hierarchical response model pooling telemetry over the shipped item-invariant keys (`surface_group_id`, `evidence_fingerprint.source_family`, `probe_instrument_class`) with shrinkage; embedding-neighborhood (from A) as the soft fallback for empty cells; prompt-based frozen-LLM response prior (Thinking-KT-style) as the prior the empirical counts shrink toward. Positive records from A fill the success half of the cells. Later, math-vault-only NTKT-style LoRA upgrade (deferred, H).

**Learner justification.** Every probe decision currently runs on a per-call LLM likelihood guess or stays dark. Grounded likelihoods promote the causal lane live, which the learner experiences as *minimally sufficient diagnosis*: the system asks a question only when the robust math says the answer would change the repair — and the stopping certificates (common-repair, EVPI bound, robust EVSI, all shipped in `evsi.py`) actually bind. Fewer questions before the smallest safe repair.

### D. External validity benchmarks (cheap, run early)

**What.** (1) **ConceptKT**: run the shipped candidate-cause pipeline against expert missing-concept labels and the slip-vs-conceptual distinction — first outside measurement of the layer everything depends on. (2) **Eedi Kaggle retrieval benchmark**: given a trace, rank misconception labels; compare off-the-shelf embeddings vs BM25 vs hybrid — this *arbitrates the EduEmbed-fork question with data* instead of vibes. (3) Later: the APIET **diagnosis-ablation A/B** (same tutor, diagnostic module removed, blind comparison) — the evaluation of the system's central value claim, never yet run.

**Learner justification.** Direct: the slip-vs-misconception separation is what stands between a learner who mistyped and a learner sent to remediation for a typo. Measuring it externally is the cheapest protection against systematically mis-diagnosing the person. The ablation A/B answers whether the diagnostic machinery is actually buying the learner anything over a plain tutor — the honest question the whole product rests on.

### E. W3 enforcement + trajectory-ensemble belief (one build)

**What.** Upgrade the sim harness's planted learner with the BEAGLE recipe: explicit flaw injection, strategist/executor decoupling (the LLM cannot silently fix its own injected mistake), observation filtering, and **non-applicability controls** (misconception fires where it should, stays quiet where it shouldn't — otherwise the sim models generalized incompetence). EvalConvoLearn certifies realism. The *same generator* then powers the sparse-log belief estimator: propose candidate cognitive trajectories consistent with the observed log; filter by (a) hard typed validity — epistemic-state rules, hypergraph prerequisite consistency, no mastery change without an event, plausible forgetting — and (b) RSIR-transplanted empirical fidelity — held-out *real* attempts must remain high-likelihood under the trajectory; resample. The surviving ensemble **is** `C_δ(b)` feeding `shared_optimal_action` and robust EVSI; its spread across repair-equivalence classes drives probe-vs-repair. Firewall: posterior samples only, never recursive training data (RSIR's own ablation: fidelity-ungated recursion collapses −27% by iteration 2).

**Learner justification.** Two distinct wins. (1) *Sparse-evidence honesty*: in the first sessions of a new vault — exactly when the system knows least — the learner gets calibrated uncertainty (wide ensemble → gentle common repairs or one well-chosen probe) instead of a confidently wrong route. (2) *Regression protection*: router recovery-rate evals against known planted misconceptions mean routing changes are tested against ground truth before any real learner pays for them, and predicted response signatures get calibrated against knowable h. The eventual labeled contrastive corpus (same-cause-different-surface pairs, same-answer-different-cause hard negatives) is what would honestly justify a trace-encoder fine-tune.

### F. Route-comparator completion (small engineering delta)

**What.** Most of synthesis-doc step 1 shipped (live EVSI ranking, propensity logging, decision receipts, shadow-parity gates). Remaining: (1) stamp the belief state `b_t` into `causal_probe_decision_receipts` alongside the already-logged candidates and propensities — the last sliver of the TSDR replay-conditioning discipline; (2) make the four-route race `{repair now / ask existing / construct / defer}` explicitly costed, now estimable because A turns "does a discriminator exist?" into a retrieval query and instrument-family telemetry prices construction; (3) route receipts record predicted vs. actual route cost for hindsight-trained cost-to-go later. Constructive route = inverse design in decision space: "generate an item where h_i and h_j produce divergent traces," mal-procedure-executed before any learner sees it.

**Learner justification.** The learner is never used as the instrument of a weak question when machine effort could build a sharp one: "construct a better probe" becomes a costed alternative to "ask now," and the zero-learner-cost mal-procedure filter rejects non-discriminating candidates before administration. Deferral gets honest bookkeeping — a queued construction instead of a silent drop.

### G. Equipoise contextual bandit + plateau jump trigger (last; needs C/E data)

**What.** Thompson-sampled Beta posteriors over pedagogy arms, context = learner-field region features, kernel-smoothed across the embedding geometry so n=1 pools instead of starving. **Authority only inside the robust near-tie set** the deterministic policy declares (`randomization_layer` propensities, `policy_experiment_assignments`, `controller_outcome_windows` — migration 098 — already shipped); SPIBB-style fallback to baseline everywhere else; reward = delayed cold-outcome window only. Plateau detection (cold-mastery-per-minute flat while local arms keep being pulled) activates **jump arms**: representation switch, prerequisite descent via minimal cut, alternative solution-route hyperedge, tutor-mode change, or capability construction (CG-Plan's constructive route wearing the RecHarness hat). Guardrails: source-aware pre-check (rule out instrument noise before pedagogy jumps); retuning window (judge a jump on its delayed window, since prerequisite descent looks bad on the immediate next attempt by construction); jumps confined to `A_feas`.

**Learner justification.** Repairs *personalize*: the system learns that this learner's applicability-condition errors respond to counterexamples but not worked examples, and starts choosing accordingly — at provably bounded regret, because it only ever experiments among actions already certified near-optimal. And plateaus stop feeling like grinding: when more-of-the-same practice stalls, the learner gets a structural change — a new representation, a targeted prerequisite hop, a differently-shaped probe — instead of the local minimum served indefinitely.

### H. Deferred trained artifacts (explicitly gated)

NTKT-style LoRA response prior (FoundationalASSIST + Eedi, math vaults only) and the trace-encoder fine-tune. Gate: D's Eedi benchmark shows off-the-shelf retrieval materially below ceiling, **and** E's synthetic corpus provides in-domain labels with an evaluation target independent of the pseudo-labeler (future behavior, never label recovery). Until both hold, the fork is low-ROI: canonicalization already delivers most of the invariance a contrastive fine-tune would learn, and pseudo-label training without independent evaluation is circular.

Also permanently out (unchanged verdicts): population KT models in the loop (PLKT / MOSAIC / NSKT / TSDR-as-model / L-HAKT), hyperbolic implicit hierarchy (the hypergraph owns hierarchy explicitly), bandit-as-router, LLM-as-state.

---

## Sequencing

| Order | Item | Depends on | Scale |
|---|---|---|---|
| 1 | **A** trace memory (write path + shadow recurrence first) | — | the foundation; start immediately |
| 1′ | **D** ConceptKT + Eedi benchmarks | — | weekend-scale each; parallel with A |
| 2 | **F** receipts delta + route race | A (retrieval costing) | small engineering |
| 3 | **B** learner field + state card | A | medium |
| 4 | **C** arm A pooling | A, D verdicts | medium; the causal-lane unlock |
| 5 | **E** W3 enforcement + trajectory belief | spec exists; A helps | large; co-requisite with W2 per spec |
| 6 | **G** equipoise bandit + jump trigger | C (likelihoods), E (evals), cold-outcome accrual | last learned layer |
| 7 | **H** trained artifacts | D + E gates pass | deferred |
| † | APIET diagnosis-ablation A/B | B (tutor lane stable) | run once E's harness can host it |

The through-line, stated once: **memory (A) makes the stateless backbone longitudinal; the field (B) makes state legible to both consumers; calibration (C) makes probe decisions arithmetic instead of guesses; benchmarks (D) keep the diagnosis honest; the ensemble (E) makes sparse evidence honest and changes testable; the comparator (F) prices building against asking; the bandit (G) personalizes repair inside proven-safe slack. Every layer exists so the learner answers fewer questions, gets smaller and better-aimed repairs, and spends the reclaimed minutes at the frontier.**

---

*Related: [[Diagnostic Pipeline Synthesis]] · [[Capability Gated Planning, Cost to Goal Discovery]] · [[Agent dialogue]] · [[Agent dialogue on modeling incorrect student thinking]] · [[Agent dialogue on EduEmbed]] · [[Knowledge Tracing]] · [[Datasets]] · spec_causal_learner_model.md (W0–W4)*
