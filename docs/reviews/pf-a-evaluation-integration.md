# PF-a offline evaluation and family memory

## Entry points

The CLI is registered without importing an adapter from a domain module:

```python
from learnloop.cli.evaluation import eval_app
app.add_typer(eval_app, name="eval")
```

Its default callback preserves the prior `learnloop eval --vault ...`
calibration report. The `families` subcommand runs the predictor harness.

```sh
uv run learnloop eval families --vault fixtures-local/my-vault
uv run learnloop eval families --vault fixtures-local/my-vault \
  --legacy-fallback current_content --output fixtures-local/reports --json
```

The command attaches to SQLite **read-only**, does not migrate, and creates only
the chosen JSON/Markdown report files. It invokes no model or generator.
Reports are aggregates only; attempts, item text and learner responses are not
exported. The report hash names the files, so different runs do not overwrite
one another.

## Reusable seam and Phase 2 integration

`offline_outcomes.PredictionRow` contains only immutable prediction features.
`OutcomeRow` adds the observed fraction, FSRS rating, coldness and exclusion.
`evaluation.harness.replay` sorts by `(observed_at, attempt_id)`, asks **all**
arms to predict before observing, and rejects duplicate attempt epochs.
Arms have no repository handle. The protocol is the research harness's
`name`, `version_hash`, `granularity`, `predict`, `observe` subset, **not** the
full live learner-field activation interface (`predict_item`,
`conditional_gain`, `rebuild`, etc.). Nothing here is activatable.

Phase 2 should supply these records from its canonical attempt outcome view,
replacing `substrate.family_memory_rows.load_rows`. Do not add another replay
script, duplicate the EKF, or make arms query the store. The current adapter:

- selects non-superseded criterion evidence;
- requires a content-addressed scheduler item snapshot **and** matching graded
  assessment contract for `exact`;
- defaults to `excluded` when that revision is unavailable; only the explicit
  `current_content` option uses `reconstructed_current`;
- excludes regraded attempts from evaluation rather than backdating a later
  corrected label (the retrospective projection can use the corrected label);
- reads persisted `EffectiveObservation` mass and quarantine state; legacy
  missing interpretations contribute no invented reliable ability mass;
- uses the causal activity policy plus the item-or-LO reveal ledger;
- never reads `practice_item_state`, `activity_card_state` or full-log
  `item_parameter_state` to predict a historical answer.

The conservative reveal window is all reveals at or before production. Phase 2
can replace it with its authoritative receipt window, preserving the coldness
gate. Unknown serving-origin joins stay unknown rather than inferred.

## Memory arms and projection

`scheduling.family_memory_model.FamilyMemory` is the single pure FSRS fold used
by both evaluation and `substrate.family_memory.rebuild_family_memory`.
The orchestrator registers `family_memory` as the sole DERIVED owner of
`family_memory_state`; the foundation owns its migration and table role.
No code reads this table for serving or scheduling.

Every key (item/family/LO) receives the **same** weights for a given report
configuration. Both the active current user fit (with provenance, or explicit
default fallback) and pinned FSRS defaults are reported. Current fit may have
been trained on the evaluated log: its result is explicitly descriptive, not a
past-only weight fit. The fixed-default arm has no such fitting leakage.

Memory trains only graded cold `same_target`/`isomorph` opportunities. Assisted,
primed, tutor/chat, diagnostic and post-reveal rows never train it. `near` and
`far` are prediction-only transfer probes. Unfamilied items use an item key.
Cold first-key probability is an explicit fixed 0.5, not a fabricated FSRS
history. Warm rows are not scored by memory arms.

The distance arm discounts positive stability credit by `exp(-distance)`;
failures are not discounted. **There are no PF-b skeleton distances yet.**
The adapter leaves them missing and reports coverage, so these arms currently
equal their undiscounted counterparts. An authored transfer-distance label
must never be substituted for a skeleton measurement. A future distance
provider must use only previously administered family variants.

The projection uses applied authored groupings retrospectively and explicitly
permits reconstructed-current legacy grades. Legacy grades without a calibration
interpretation can still be graded cold memory opportunities; they are not
promoted to reliable ability observations in evaluation. This distinction is
intentional. Undo removes item family fields and a rebuild clears stale rows;
orphan family files do not create memory.

## `idea_hier`

The predictor uses a float64 **joint** probability-space EKF with independent
Gaussian priors: subject general variance 0.75, LO variance 2.25, family variance
0.5. Posterior cross-covariances are retained. The observation derivative is
`a*p*(1-p)` and noise is `base_observation_variance*p*(1-p)/mass`, plus
nonnegative difficulty uncertainty. Joseph covariance updates avoid negative
variance from numerical subtraction. Drift grows diagonal variance without
mean decay; new family effects start at variance 0.5. `region_estimates` marks
regions without direct observations untested.

Current adapter limitations, not activation promises:

- no Phase 2 incumbent/extension-arm comparison, conditional gain, facet
  aggregation, fast-track simulation or promotion gate;
- no historical weak learner-claim prior, solver-panel prior or past-only
  empirical-Bayes difficulty evolution: authored/LO priors are reported instead;
- LLM-estimated difficulty is discarded as a point value and widens noise by
  variance 1.0;
- primed difficulty gets the existing configured offset, once;
- missing calibration can leave the real legacy evaluation empty; exclusion
  and revision counts explain this rather than manufacturing predictions;
- bootstrap intervals are deterministic percentile intervals clustered by
  attempt, not proof against correlated sessions or historical serving bias.

JSON includes log loss, Brier, reliability bins, binary AUC when applicable,
300-resample intervals, counts, first/later-LO, origin, revision, topic,
grader-model, resolved family-judge-model, relation and coldness splits, plus
arm/config/data/weight hashes. An explicit `dont_know` is an observed failure at
full predictor mass, rather than an uncertain LLM grade.
No automatic conclusion favors Phase 3b.
