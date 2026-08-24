# Architecture Pivot: Toward a Learned, Compute-Leveraging LearnLoop

Status: strategy / direction. Written 2026-05-28. Stages 0 and 1 are partially
implemented; later stages remain direction rather than shipped behavior.

This document proposes how to evolve the LearnLoop algorithm (see `documentation.md`)
from a deterministic, hand-engineered pipeline toward an architecture where
**search and learning** carry the load and human-authored knowledge is demoted to
priors, cold-start, and interpretable views — per Sutton's *Bitter Lesson*
(http://www.incompleteideas.net/IncIdeas/BitterLesson.html).

It is a sequencing plan, not a rewrite. Most of the enabling substrate already
exists in the codebase; the pivot is mostly about flipping which components are
load-bearing.

---

## 1. What the Bitter Lesson argues (and doesn't)

The claim is narrow: **general methods that scale with computation — search and
learning — eventually beat methods that encode how humans believe the domain
works.** Hand-built knowledge gives a fast start and a low ceiling; it stops
improving when you add compute/data, and later actively obstructs the scalable
method.

Two qualifications matter here:

- It is about **means, not ends.** We still choose the objective. "Durable
  retention + transfer" is a value choice — and, importantly, it is *measurable*,
  which is what makes everything downstream learnable.
- It assumes compute/data abundance. A single-user, local, offline,
  latency-sensitive, replay-deterministic vault is the adversarial case. So the
  pivot is **not** "delete the math, train a net." It is "restructure so
  computation can take over each module as data arrives, with the hand-built
  version as cold-start prior and fallback."

The architecture is already philosophically aligned. `spec.md` ("The scheduler is
five layers stacked … **Always store raw attempts forever so the mastery and
uncertainty models are replaceable without re-collecting data**") plus the
migration-010/011 logging (`learning_outcome_labels`, `decision_features`,
`scheduler_slate_candidates.selection_propensity`) is exactly the substrate a
learned approach needs. What *ships* today is hand-engineered; the pivot flips
which one is load-bearing.

## 2. Where human knowledge is currently load-bearing

Ranked by how much each caps the ceiling:

| Component | Human knowledge baked in | Doc ref |
|---|---|---|
| **Item/content semantics** | `evidence_facets`, `evidence_weights`, `criterion_facet_weights`, `retrieval_demand`, `transfer_distance`, `scaffold_level`, `surface_family`, `difficulty` — all authored/LLM-annotated per item | §9, §14.2 |
| **Mastery dynamics** | 2PL EKF with fixed `a_i=1.0`, static authored `b_i`, hand-set drift/clamps, one-step linearization | §4.2–4.4, §17 |
| **Item memory** | FSRS-6 falls back to pinned global weights; an explicitly fitted, versioned per-vault set can replace them once it beats the configured improvement gate | §5 |
| **Scheduler policy** | Weighted sum of hand-chosen terms + hand-set reward decompositions and target bands (probe 0.40–0.60, repair 0.75–0.90, …) | §11 |
| **Probe diagnosis** | Hand-set conditional outcome model: `θ_mastered=2`, cut points, `err_low_frac=0.80`, leak=0.20 | §8.3 |
| **The coefficient zoo** | §15.7 — dozens of magic constants (severity 0.12/0.10/0.08…, predicted-correctness 0.12/0.15…, ability-gain 0.04…) | §15.7 |
| **The curriculum theory itself** | `research_on_learning.md` (10–20% rule, ~70–85% success band, desirable-difficulty heuristics) encoded as thresholds | research doc → config |

Every row tells the system *how learning works* instead of letting it *measure how
this learner learns*. The two deepest are the top and the bottom: per-item human
annotation, and the encoded learning theory.

## 3. The reframe that makes it all learnable

State the POMDP spine explicitly (the spec already gestures at this via
POMDP/knowledge-tracing and Wang et al. 2025):

> LearnLoop is a POMDP. Hidden state = the learner's true knowledge.
> Observations = graded attempts (score, error, latency, hints, confidence).
> Actions = which item, when. **Reward = future graded success at a delay, and
> success on items not previously seen (transfer).**

That reward is not hypothetical. `learning_outcome_labels` already records
`same_item_retention` and `same_learning_object_transfer` against up to 20 prior
attempts (§2, migration 010). Today they are labeled "for training/evaluation, not
an online update." **That table is the objective function.** Everything in §4–§11
is a hand-built *proxy* for predicting it. The pivot is to predict and optimize the
real labels directly.

## 4. The staged pivot

Lock the invariants first, then replace modules in increasing order of risk. Each
stage keeps the current pipeline as the behavior/teacher policy and fallback
(gated by the existing `eig_reliability` evidence ramp), so nothing regresses on
cold start.

### Stage 0 — Make it trainable (mostly done; finish it)
Guarantee every decision logs frozen inputs + propensity + realized outcome.
`decision_features` / `selection_propensity` exist, and seeded near-tie exploration
now defaults to `selection_exploration_rate = 0.1` with deterministic replay seeds.
The remaining gap is closing the loop so `learnloop eval policy` (spec.md) can do
honest off-policy (IPS / doubly-robust) estimation over the logged propensities and
realized delayed outcomes.

### Stage 1 — Fit the constants currently hand-set
No new model classes; just stop hardcoding:

- The **FSRS optimizer** now fits the learner's own review log via
  `learnloop fit fsrs`. A fit is stored as a versioned parameter set only when it
  clears the configured improvement gate; all consumers resolve that active set
  and safely fall back to the pinned 21 defaults. Automatic fit cadence and
  held-out promotion policy remain Stage-1 work.
- **Calibrate `a_i`, `b_i` online** from response data. `services/calibration.py`
  already flags miscalibration — promote it from "flag for author" to "fit."
  Discrimination fixed at 1.0 discards the main thing IRT can learn.
- Fit the §15.7 coefficients and surprise thresholds by **regression onto
  `learning_outcome_labels`** rather than tuning by hand. Replace "we believe
  incorrectness contributes 0.12" with "the coefficient that best predicts delayed
  recall is X."

In-distribution, interpretable, replay-compatible (fitted params are versioned
numbers under `algorithm_version`), and works at single-user scale.

### Stage 2 — Replace the mastery estimator with a learned sequence model
Swap the per-LO EKF (§4) for a knowledge-tracing model (DKT/SAKT/AKT lineage) that
consumes the full interaction history and predicts P(correct | history, item) and
the outcome labels. Ship it **pretrained on a population corpus, fine-tuned
locally**; fall back to the EKF below an evidence threshold (the ramp already does
this conceptually). This is where compute begins to genuinely beat the hand-built
latent.

### Stage 3 — Learn the policy / add search
The scheduler (§11) is a one-step greedy ranker; EIG (§8.4) is one-step myopic
information gain. With a learned, rollable dynamics model you can **plan**:
Monte-Carlo / tree-search over simulated futures to pick the action sequence
maximizing long-horizon retention+transfer. The spec already reserves MCTS "after
enough local attempts" — that is the bitter-lesson endpoint: *search over a learned
model*, not a heuristic priority sum. Train the policy off-policy on logged
slates + propensities + outcomes; the planner is the compute knob you turn up.

### Stage 4 (deepest cut) — Content as features, not annotations
Retire the top row of §2's table. Instead of humans/LLMs labeling
`retrieval_demand`, `transfer_distance`, `evidence_facets`, `difficulty` per item,
feed the **raw prompt/answer text as embeddings** into the model and let it infer
those properties from content + response history. This is the largest pool of
encoded human judgment in the system and exactly what a model with enough data
should subsume. The authored fields survive as **interpretable views and cold-start
priors**, mirroring how axis labels were already demoted to "derived views, not
primitive belief state."

## 5. Tensions the pivot must preserve (not hand-wave)

These are real and are *why* the current design is reasonable. The pivot must keep
them, not ignore them:

- **Determinism / replay.** A learned model is replayable *iff* its weights are
  pinned and versioned exactly like `algorithm_version`. Treat model checkpoints as
  versioned algorithm artifacts; replay loads the pinned checkpoint. Embeddings
  stay out of replay invariants (already decided in open-questions D2).
- **Interpretability / "Why now?".** A black-box policy fights
  `scheduler_explanations` + debug payloads. Keep the planner's rollout and the
  predictor's feature attributions as the explanation surface, and keep a distilled
  interpretable surrogate alongside for the UI. Don't let "Why now?" die.
- **Cold start with N=1.** The reason for staging. Population-pretrain +
  local-finetune + heuristic fallback under the reliability ramp is the bridge.
  Never let a thinly-trained local model take the wheel before the ramp says it has
  earned it.
- **Offline / latency.** Stage-3 search has a per-queue compute budget; the spec's
  TUI-latency objection is valid. Plan asynchronously / between sessions, cache the
  slate, keep the heuristic for the synchronous path.

## 6. The one-line recommendation

The pivot is a sequencing decision, not a rewrite. **Turn `learning_outcome_labels`
from a passive log into the optimization target, turn on exploration so off-policy
estimation is honest, then replace hand-set constants → learned estimator → planned
policy in that order, each gated behind the evidence ramp that already exists.**
Start with Stage 1 (FSRS-fitting + coefficient regression): lowest risk,
immediately measurable against held-out outcome labels, and it proves the loop
end-to-end before touching model classes.
