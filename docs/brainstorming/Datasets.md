- [Eedi Mining Misconceptions ](https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics/leaderboard)
	- [Neurips 2020 Education Challenge](https://www.eedischool.com/projects/neurips-education-challenge) [Codalab](https://competitions.codalab.org/competitions/25449)
		- [arXiv](https://arxiv.org/html/2104.04034v1)
	- [Neurips 2022 Follow up challenge](https://www.eedischool.com/projects/neurips-2022) [Codalab](https://codalab.lisn.upsaclay.fr/competitions/5626)
		- [arXiv](https://arxiv.org/html/2208.12610v2)
- [TutorMoments-Preview](https://huggingface.co/datasets/allenai/tutormoments-preview)
- [ASSISTments 2009/2015](https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data)
- [FoundationalASSIST](https://huggingface.co/datasets/ASSISTments/FoundationalASSIST)
- [EdNet](https://github.com/riiid/ednet)
- [Tutor Move Taxonomy](https://arxiv.org/pdf/2603.05778)
- [Million Tutoring Moves](https://arxiv.org/html/2605.08092v1)
- [ConceptKT](https://arxiv.org/html/2603.24073v1)
- [EvalConvoLearn](https://github.com/RenaissancePhilanthropy/EvalConvoLearn)
- [Question-Anchored-Tutoring-Dialogues-2k](https://huggingface.co/datasets/Eedi/Question-Anchored-Tutoring-Dialogues-2k)
- [BePKT](https://arxiv.org/html/2112.08273v1)
- [GenAICanHarmLearning](https://github.com/obastani/GenAICanHarmLearning)

Per-dataset verdicts for LearnLoop: [[Diagnostic Pipeline Synthesis]]

---

## Aug 24 update — verdict changes from the [[Pipeline Augmentation Plan]]

*The plan's workstreams (A trace memory · B learner field · C arm A likelihoods · D benchmarks · E synthetic learners + belief · F route comparator · G equipoise bandit · H trained artifacts · I hypergraph edge authority) created new consumers for this list and rehabilitated three entries. Workstream letters below refer to that doc.*

### Verdict upgrades

| Dataset | Old verdict | New verdict | Why |
|---|---|---|---|
| [Eedi NeurIPS 2020](https://arxiv.org/html/2104.04034v1) | Secondary | **Primary calibration source** | Only large public corpus with per-response student **confidence** — fits priors for A's confidence-before-feedback field, the "believed vs. doubted recurring error" repair distinction, and the confidence–performance-mismatch trigger. Image-content blocker resolved by the vision ingest path. |
| [NeurIPS 2022 follow-up](https://arxiv.org/html/2208.12610v2) | Reclassified, low priority | **Methods benchmark for I + G** | Its causal-discovery track tests the synergy/hyperedge confirmer and soft-prior demotion (I); its CATE track validates the drifting repair-effect state-space and PERRY-style OPE intervals (G). |
| [EdNet](https://github.com/riiid/ednet) | Skip | **Partially unparked** | Decay-form fitting needs only (skill, time-gap, correctness): 131M timestamped interactions make it the robustness check for B's trained-once forgetting kernels (FoundationalASSIST stays primary). Skip verdict stands for everything semantic. |
| [QATD-2k](https://huggingface.co/datasets/Eedi/Question-Anchored-Tutoring-Dialogues-2k) | Use later | **Pulled earlier** | Public train/eval set for the generate-retrieve-rerank misconception matcher ([arXiv:2602.02414](https://arxiv.org/abs/2602.02414) is Eedi on this data shape), and the corpus for building the three-axis simulator evaluation ([arXiv:2601.04025](https://arxiv.org/abs/2601.04025)) feeding E's acceptance gate. |

### New consumers for existing "use" verdicts

- **[Eedi Mining Misconceptions](https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics)** → three new jobs: hard-negative source for A's recurrence-detector **false-merge audit** (same wrong answer, different misconception); the **planting library** for E's Selective Flip Score gate ([arXiv:2605.12748](https://arxiv.org/abs/2605.12748)); ground truth for A's **predicted-signature embeddings** (does the hypothesis-predicted trace rank the observed distractor first?).
- **[FoundationalASSIST](https://huggingface.co/datasets/ASSISTments/FoundationalASSIST)** → now the single most load-bearing external dataset: three trained-once artifacts draw on it — H's **response prior** (exact-response format published, [arXiv:2602.00070](https://arxiv.org/abs/2602.00070)), the **V2 GRU/SSM behavioral residual** (trained once, frozen, shadow-scored on cold Brier), and B's **forgetting-kernel fit** (primary corpus).
- **[ConceptKT](https://arxiv.org/html/2603.24073v1)** → additionally validates two A-schema fields: the **first-divergence-step embedding** (localized first error vs. expert missing-concept label) and the **delta-vs-canonical contrast embedding** (do expert-labeled same-deficiency solutions cluster?); careless-vs-conceptual κ labels check the slip-vs-misconception logic; the concept-aligned-history result is the specific license for A's factorized fields.
- **[TutorMoments](https://huggingface.co/datasets/allenai/tutormoments-preview)** → frozen 520 scored moments double as the **paired-anchor set for judge calibration** ([arXiv:2605.09227](https://arxiv.org/abs/2605.09227)) and a substrate for D's **flip-rate invariance audits** (perturb register/notation, measure RepairFlipRate).
- **[Tutor Move Taxonomy](https://arxiv.org/pdf/2603.05778) + [Million Tutoring Moves](https://arxiv.org/html/2605.08092v1)** → the taxonomy is the **schema for G's action capability embeddings** `c_a`; MTM's utterances, LLMKT-annotated into move→outcome sequences, initialize the **drifting repair-effect state-space** — the population prior the per-learner estimate starts from.
- **[EvalConvoLearn](https://github.com/RenaissancePhilanthropy/EvalConvoLearn)** → unchanged role, but now one member of E's acceptance battery: realism certification + Selective Flip Score + three-axis rubric.

### Unchanged

ASSISTments 09/15 stays skipped (FoundationalASSIST dominates it for every purpose). BePKT stays parked pending programming vaults.

### New entries (from the Aug 24 research sweep)

- [MediQ](https://arxiv.org/abs/2607.03426) — adaptive information-seeking-before-diagnosis benchmark (via ASIG); closest public analogue to the diagnose-then-repair loop. Consumer: F's route comparator evaluation.
- [LongMemEval / LoCoMo](https://arxiv.org/abs/2601.02845) and [PrecisionMemBench](https://arxiv.org/abs/2605.11325) — agent-memory retrieval benchmarks; harness shapes for A's retrieval-isolated evaluation (precision / noise-isolation / mutability, fixed embedder+backbone, recency baseline).
