# Diagnostic Pipeline Synthesis

*Review of [[Capability Gated Planning, Cost to Goal Discovery]], the [[EduEmbed]] fork idea, every source in [[Knowledge Tracing]] and [[Datasets]], and an integrated pipeline proposal. Written 2026-08-24.*

The filter applied throughout: LearnLoop is **n=1**, evidence-not-mastery, with a **permanently cold item side** (single-use generated surfaces — every item is new) and a **permanently warm learner side** (one learner, rich history). Anything requiring population training on our own logs is out. What survives is either a *pattern* to adopt or a *trained-once, text-conditioned artifact* that generalizes to unseen items.

---

## 1. Capability-gated planning as the action router

Assessment of [[Capability Gated Planning, Cost to Goal Discovery]] ([paper](https://arxiv.org/html/2608.05085v1)):

**Mostly not new pipeline — a router over lanes that already exist.** The four-action taxonomy maps nearly 1:1 onto shipped substrate:

| Doc's action type | Existing LearnLoop substrate |
|---|---|
| Constructive diagnostic action | Probe commissioning: `probe_generation_needs`, `mint_single_use_probe_surface`, `item_misconception_discrimination` |
| Diagnostic probe | Probe episodes with single-use surfaces |
| Repair | Repair classes + remediation episodes + guided redo |
| Audit | Cold retrieval + coldness receipts |

The repair-equivalence stopping rule (§4's `A_ε(h)` intersection) is literally `action_loss.py` + `evsi.py`; the common-repair-before-diagnosis check already ships in Journey-B delivery. Honest reading: **this doc is the argument for promoting EVSI from shadow receipts to the router's core decision rule**, plus one genuinely new element — making "construct a better probe" a *costed route* compared against "ask now" and "repair now," rather than an unconditional background supply sweep.

**Pushbacks:**

1. **Don't justify with the paper's theorem — it doesn't bite here.** Theorem 1 needs build chains longer than the lookahead horizon, action-space-only gating, deterministic constructions. Our chains are depth 3–4 and known; our planner is an LLM that reasons over whole routes (not in Π_d). The real justification: *machine effort is cheap; learner attention is the scarce, non-renewable resource.*
2. **The likelihood tensor P(o|e,h) is load-bearing and unlearnable at n=1.** The n=1-honest version is ordinal, not metric: LLM-authored separable-pairs claims with completeness provenance (already exists as `order_probe_candidates`, `likelihood_completeness`). No divergence arithmetic over vibes. (History lesson: inert scheduler weights in sim-sweep; EVSI dark for months.)
3. **Dual-effect measurement is already built** — reveal ledger + reveal-aware cold lane + 8-dimension coldness receipts. Route through them; no second exposure-accounting layer.
4. **Cost units decide route structure.** Online decision = `{repair now, ask existing probe, defer}`; "defer" *queues* construction for the between-session sweep (`diagnostic_surface_generation_needs`). Full four-way race only when construction is one fast templated mint.

**First build:** post-attempt route comparator using existing signals (common-repair check → probe-pool availability against administered exclusions → else queue construction) + a **route receipt** recording route chosen, predicted outcome, and actual outcome at audit time. Precedent: `causal_shadow_selection_receipts`. This seeds hindsight-trained cost-to-go without committing to numeric machinery.

Two durable principles:
> Sometimes the best next action is building the representation/probe/rubric that makes the right question possible.
> Never diagnose past repair-relevance.

---

## 2. The EduEmbed fork — roles inverted

Assessment of [[EduEmbed]] ([paper](https://arxiv.org/html/2604.04088v1)):

The paper trains on 1,080–4,918 students / 52k–1.4M interactions, excludes students with <10–30 responses, and gains concentrate in **inductive/zero-shot CD and early-stage CAT** (transductive gains minimal). Its purpose — selecting from a fixed bank, rescuing history-less entities with text — is mooted by free generation. A literal fork is untrainable at n=1 (LoRA + BCE response prediction on a few hundred attempts memorizes).

But the setting is *inverted*, not absent: EduEmbed's core mechanism — **text as the bridge that transfers signal across ID-less entities** — is exactly what we need, pointed the other way: transferring the one learner's rich history *onto* freshly generated items. Three concrete uses:

1. **Misconception identity across surfaces and time.** Trace-to-trace similarity for recurrence detection (bounded deferral's K=3 recurrences currently keys on repair-class string equality). Embed the **compiled hypothesis record, not raw grader prose** — raw statements shift with every `GRADING_PROMPT_VERSION` bump, and same-wrong-answer-different-cause is only separable if the embedded text carries the causal claim (grader causal axes are now asdict-lossless).
2. **Calibration pooling over single-use items.** A single-use item accumulates zero calibration data individually; statistics must pool over item-invariant keys. Discrete versions exist (`surface_group_id`, `evidence_fingerprint.source_family`, `probe_instrument_class`); embeddings are the soft, generalizing version — a fresh probe inherits predicted response signatures from its neighborhood instead of a per-call LLM guess.
3. **Freshness/isomorph gating.** Distance-to-administered-surfaces strengthens the single-use freshness check; the inverse query (same facet, deliberately different surface) serves cold retrieval.

**Appending grader diagnosis statements onto EduEmbed:** mechanically trivial (profiles are just text) and a legitimate extension — but without RaIF training it reduces to "stock embedding of a diagnosis-enriched profile," and the AaRI ID-fusion half is degenerate at n=1. Also: the diagnosis belongs to the *(learner, item, response)* event, not the student alone — embed each trace as its own entity (extra roles per the capability doc's §6) alongside the enriched learner profile.

**Recommendation:** no fork/fine-tune now. Off-the-shelf embeddings over canonicalized, factorized trace records (facet / operation / misconception-claim fields embedded separately), per-vault, confined to retrieval/filtering stages — discrimination scoring stays with the hypothesis layer. The true fine-tuned fork becomes viable when the W3 synthetic-learner suite can generate a labeled contrastive corpus (see BEAGLE below).

---

## 3. Knowledge tracing papers — verdicts

Per-source verdicts for [[Knowledge Tracing]]:

### PLKT — probabilistic embeddings + pattern reasoning ([arXiv](https://arxiv.org/html/2605.09369v1)) — **skip**
Population-trained, correctness-only, no misconceptions. Cold-start for unseen items = flat 0.5 difficulty prior — i.e., every item we generate. Beta-distributed mastery-with-uncertainty is subsumed by the typed evidence ledger.

### TSDR — doubly robust debiased KT, IJCAI '26 ([preprint](https://ijcai-preprints.s3.us-west-1.amazonaws.com/2026/2191.pdf)) — **skip the model, steal the discipline**
Core insight: logged interactions are MNAR — the policy selects what gets observed, so training on logs confounds knowledge with selection. LearnLoop has this acutely: the router picks probes from current beliefs, so the interaction archive is a maximally biased sample. Can't run propensity/imputation at n=1, but we're in the rare setting where **propensity doesn't need estimating — the router computed it**. → Stamp selection propensity (what was considered, why this won, at what belief state) into serving/route receipts so replay calibration can condition on selection.

### Neural-Symbolic KT ([arXiv](https://arxiv.org/html/2604.08263v1)) — **skip**
Evidence that structure beats black-box at small data (0.80 AUC at 10% of a small dataset) — consonant with claim discipline — but the rules are trivial mastery thresholds and differentiable logic is the wrong tool when an LLM is the inference engine.

### MERIT — memory-enhanced retrieval, training-free ([arXiv](https://arxiv.org/html/2603.22289v1)) — **adopt the pattern**
Frozen LLM + retrieved memory bank of "Annotated Cognitive Paradigms": structured (knowledge state, behavioral pattern, difficulty context, causal reasoning) entries, hybrid semantic+BM25 retrieval, incremental memory updates without retraining. **This is the missing payload design for the trace memory**: retrieval returns structured diagnostic paradigms with causal reasoning attached, injected into the diagnoser prompt — not just nearest-neighbor items. Their logic constraints were decisive (−18% AUC when removed): retrieval feeds the LLM, claims still gate the decision. Same division of labor as ours.

### Thinking-KT — training-free LRM KT ([pdf](https://arxiv.org/pdf/2601.01708), [code](https://anonymous.4open.science/r/lokt_thinking_anonymous-2A16/README.md)) — **closest published neighbor; mine, don't build**
Frozen large-reasoning-model doing unified prediction + prescription over question text + history, beating trained baselines, cold-start via world knowledge. Published validation of LearnLoop's core bet. Mine the prompt structure and released code as a comparison harness.

### NTKT — next-token KT ([arXiv](https://arxiv.org/html/2511.02599v2)) — **most important empirical result in the list**
LoRA-tuned LLaMA, KT as next-token prediction over question *text* + history. **Question cold-start F1 = 0.843 on both seen and unseen questions** (baselines drop 0.777→0.732); ablations show text carries it (AUC 90.3 full text vs 77.1 ID-only). Direct evidence that text transfers response-prediction signal onto never-before-seen items — the exact permanent regime single-use generation creates. Needs Eedi-scale training (1.9M interactions), but the artifact is item-general: a small LoRA trained once on public math data could serve as a **response prior** for generated items in math-adjacent vaults. Risk: domain transfer beyond K-12 math.

### MOSAIC ([arXiv](https://arxiv.org/html/2606.29049v1)) — **skip; borrow one invariant**
Population-scale, no cold-start/misconception story. Borrow the cross-granularity consistency constraint (concept ↔ topic ↔ global mastery coherence) as a cheap doctor-style audit over facet/LO/concept projection levels.

### Diagnostic-driven multi-agent Socratic, APIET '26 ([ACM](https://dl.acm.org/doi/full/10.1145/3796114.3796119), local PDF in this folder) — **validation only; thin paper**
Four agents, 4-scalar C/A/S/R state with exponential forgetting, 13 hand-built samples, LLM-judge wins vs GPT-3.5. LearnLoop's substrate is far past it. Take two things: the **mastery validation checkpoint** (claimed mastery → immediate generated-quiz verification) confirms the audit lane; and their **diagnosis-ablation A/B** (same tutor, diagnostic module removed, blind comparison) is the evaluation of our system's central value claim that we have never run.

### BEAGLE — enforced-flaw learner emulation ([arXiv](https://arxiv.org/html/2602.13280v2)) — **sleeper hit; W3's missing recipe**
BKT-gated knowledge constraints + explicit flaw injection + strategist/executor decoupling (LLM cannot silently fix its own injected mistakes) + observation filtering. Traces indistinguishable from real students (52.8% detection ≈ chance); **error recurrence 86.2% vs 7.8% for naive LLM personas** — naive persona prompting does not hold misconceptions stably, which is exactly why a synthetic-learner suite for router testing has been hard. Unlocks: (a) end-to-end router evals against known injected misconceptions, (b) calibration of predicted response signatures against knowable h, (c) the labeled contrastive corpus for the eventual trace-encoder fine-tune. See [[causal-learner-model-spec]] W3.

### LLMKT — KT in tutor dialogues ([arXiv](https://arxiv.org/html/2409.16490v2)) — **adopt the annotation scheme**
GPT-4o auto-annotates each dialogue turn for correctness + knowledge components (human-validated 0.93). Ready template for extracting evidence atoms from tutor-lane conversations. Calibration on expectations: even with full context, dialogue KT tops out ~76 AUC → dialogue evidence should carry lower weight than attempt evidence in folds.

### Hey Chat — Socratic in the wild ([arXiv](https://arxiv.org/html/2606.11744v1)) — **strongest design validation in the list**
Small RL policy sequencing over an explicit prerequisite graph + LLM only conducting dialogue: 78–82% curriculum mastery vs 3–23% for frontier end-to-end LLMs, 0% for KT baselines. Three 1:1 mappings: (1) **structure beats scale** — fixed observation vector beats LLM-reads-own-transcript, which degrades over long horizons → keep the route comparator a deterministic state machine, LLM stays proposer/grader; (2) **negative-evidence asymmetry** — wrong answers are ambiguous across the prerequisite chain while right answers propagate confidence → formal support for candidate-cause/prerequisite-probe machinery; (3) **agreeable inaccuracy** — encouragement-optimized tutors affirm wrong statements and entrench misconceptions → audit tutor-lane prompts.

---

## 4. Datasets — what each is actually for

Per-source verdicts for [[Datasets]]. None can train a per-learner model (wrong population, wrong content). Four legitimate external-data consumers:
- **(a)** trace/misconception encoder training + validation
- **(b)** text-conditioned response prior for generated items
- **(c)** grader/diagnoser calibration against expert labels
- **(d)** tutor-policy and synthetic-learner evaluation

| Dataset | Verdict | Consumer |
|---|---|---|
| [Eedi Mining Misconceptions](https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics) (Kaggle) | **Use.** Math MCQs with distractor→misconception mappings (~2.5k labels + question text). Only public dataset with the misconception-sensitivity axis. Trains/validates trace→misconception retrieval; benchmarks misconception-specific distractor generation. MCQ-only, K-12 math. | (a) |
| [Eedi NeurIPS 2020](https://arxiv.org/html/2104.04034v1) | Secondary. 1.4M answers + rare **student confidence ratings** (useful for the confidence-performance-mismatch trigger). Question content is images. | (b) |
| [NeurIPS 2022 follow-up](https://arxiv.org/html/2208.12610v2) | Reclassify: it's causal discovery + CATE estimation, mostly synthetic; no misconception labels or question content. Methods benchmark for repair-effect estimation at most. Low priority. | — |
| [TutorMoments](https://huggingface.co/datasets/allenai/tutormoments-preview) (AI2, CC BY 4.0) | **Use.** 462 real sessions + frozen 520-moment benchmark with scored AI replays. Ready external benchmark for the tutor lane. | (d) |
| [ASSISTments 09/15](https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data) | Skip. Correctness + skill IDs, no usable question text. | — |
| [FoundationalASSIST](https://huggingface.co/datasets/ASSISTments/FoundationalASSIST) (CC-BY-NC, gated) | **Use — best open corpus for the response prior.** 1.7M interactions with full problem text *as the student saw it* + **student answer text**, 3,395 problems, 224 skills. NTKT-style training data; answer text supports error-signature modeling (weak misconception labels derivable via LLM). | (b), (a) |
| [EdNet](https://github.com/riiid/ednet) | Skip. 131M interactions, TOEIC domain, no public question text. | — |
| [Tutor Move Taxonomy](https://arxiv.org/pdf/2603.05778) (Cornell NTO) | Reference, not data (codebook still refining; four categories, eliciting↔explaining spectrum). Use as the **typed ontology for repair actions** (currently free-text operator names). | (d) |
| [Million Tutoring Moves](https://arxiv.org/html/2605.08092v1) | Use later. 4,654 real math tutoring transcripts (274k utterances), open, unannotated. Apply LLMKT-style auto-annotation → repair-move → outcome sequences; ground repair-effect priors in real tutoring. | (d) |
| [ConceptKT](https://arxiv.org/html/2603.24073v1) (CC BY 4.0, [GitHub](https://github.com/NYCU-NLP-Lab/ConceptKT)) | **Use first — most directly usable item in the list.** Tiny (4,048 records, 6 students) but uniquely shaped: full student *solution processes* + expert labels of associated concepts, **missing concepts per wrong answer**, careless-vs-conceptual distinction (κ 0.63–0.68). External benchmark for the grader→hypothesis pipeline: does candidate-cause output recover the expert's missing-concept label and separate slips (13.2%) from conceptual deficiencies (11.4%)? Never measured externally. Bonus: concept-aligned history selection beats all-history (+17.4 Macro-F1) — empirically validates facet-conditioned retrieval. | (c) |
| [EvalConvoLearn](https://github.com/RenaissancePhilanthropy/EvalConvoLearn) (MIT) | **Use with W3.** Evaluation harness for learner simulations; certifies a BEAGLE-style synthetic learner's realism before trusting router evals against it. | (d) |
| [QATD-2k](https://huggingface.co/datasets/Eedi/Question-Anchored-Tutoring-Dialogues-2k) (Eedi, CC-BY-NC) | Use later. 2k tutoring dialogues anchored to diagnostic questions with question text + talk-move labels. Dialogue evidence extraction training/eval; repair-move mining on misconception-linked questions. | (a), (d) |
| [BePKT](https://arxiv.org/html/2112.08273v1) | Park. Programming OJ logs with concept annotations; relevant only if vaults cover programming. | — |

---

## 5. The integrated pipeline

Five layers; strikingly little is greenfield.

### Layer 0 — Decision core
Route comparator `{repair now / ask existing probe / construct probe / defer}` over existing lanes; repair-equivalence stopping; **route receipts stamped with selection propensity** (TSDR). Hey-Chat validates keeping this a deterministic state machine with a fixed observation vector — the LLM stays proposer/grader, never transcript-reading route-picker.

### Layer 1 — Evidence compilation
Grader prose → canonicalized executable hypotheses (partially shipped: free-text hypothesis drafting, candidate-cause errors). LLMKT's turn-annotation scheme extends compilation to tutor-dialogue evidence at discounted weight. **ConceptKT is this layer's external benchmark** — first outside measurement of slip-vs-misconception discrimination. Weekend-scale harness, unusually high signal.

### Layer 2 — Memory & retrieval (the reshaped [[EduEmbed]] fork)
Off-the-shelf embeddings over canonicalized trace records, probe templates, misconception templates — **MERIT-shaped payloads**: retrieval returns structured (pattern, context, causal reasoning) paradigm records into the diagnoser prompt. Eedi Kaggle seeds a global misconception-template library for math-adjacent vaults and validates trace→misconception ranking. Retrieval confined to candidate generation; discrimination scoring stays with the hypothesis layer.

### Layer 3 — Response priors for generated items
NTKT's cold-start result is the license: text carries response-prediction signal onto unseen items. Ship the prompt-based version first (Thinking-KT-style frozen-LLM prediction); treat a small LoRA trained on FoundationalASSIST + Eedi as a later, math-vault-only upgrade. This is what turns the route comparator's likelihood estimates from per-call guesses into pooled empirical grounding — closing the calibration-pooling loop from §2.

### Layer 4 — Synthetic-learner harness
BEAGLE's enforcement recipe (flaw injection + strategist/executor decoupling + observation filtering) makes W3 real; EvalConvoLearn certifies realism. Evaluation substrate for everything above: router recovery-rate evals against known injected misconceptions, signature calibration against knowable ground truth, and eventually the labeled contrastive corpus that justifies an actual trace-encoder fine-tune — **the "real EduEmbed fork" moment**.

### Layer 5 — Repair-move layer
Tutor Move Taxonomy as typed vocabulary for repair actions; MTM/QATD/TutorMoments for grounding repair-effect priors and benchmarking the tutor lane; the APIET diagnosis-ablation A/B as the evaluation template for the system's central value claim.

### Order of operations
1. Route comparator + propensity-stamped route receipts — pure engineering on existing substrate.
2. Canonicalized trace records + embedding index with MERIT-shaped payloads.
3. ConceptKT grader benchmark — cheapest external validity available.
4. BEAGLE-style enforcement in W3 + EvalConvoLearn → router end-to-end evals.
5. Only then, trained artifacts: NTKT-style response prior (math vaults), trace-encoder fine-tune on synthetic + Eedi data.

**Explicitly not doing:** any population KT model in the loop (PLKT / MOSAIC / NSKT / TSDR as models); ASSISTments-classic / EdNet as data; a literal EduEmbed fork before a training corpus exists.

---

*Related: [[Capability Gated Planning, Cost to Goal Discovery]] · [[EduEmbed]] · [[Knowledge Tracing]] · [[Datasets]]*
