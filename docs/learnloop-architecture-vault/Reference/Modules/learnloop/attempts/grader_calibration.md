---
title: "learnloop.attempts.grader_calibration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grader_calibration.py"
source_paths:
  - "src/learnloop/attempts/grader_calibration.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.grader_calibration module"
  - "src/learnloop/attempts/grader_calibration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grader_calibration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grader_calibration` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Grader identity + calibration model layer (spec_p0_measurement_correctness §3.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py) |
| Source lines | 697 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `grader_identity_hash(*, provider: str | None, model_revision: str | None, prompt_version: str | None, output_schema_version: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 72) — 32-char canonical hash of the grader identity tuple (§3.2).
- `symmetric_mean_confusion(true_classes: Sequence[str], observed_classes: Sequence[str], reliability: float) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 98) — Diagonal ``reliability``, off-diagonal ``(1-r)/(n-1)`` -- exactly the ``probe_families.grader_channel_matrix`` mean the Dirichlet centers on.
- `heuristic_alphas(*, true_classes: Sequence[str], observed_classes: Sequence[str], reliability: float, concentration: float=PRIOR_CONCENTRATION) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 113) — Spread the symmetric mean over the joint ``(G, conf_bucket)`` cells with a low concentration (wide intervals).
- `seed_heuristic_priors(repository: Repository, *, clock: Clock | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 148) — Idempotently seed the heuristic global + grader-identity priors (§5).
- `import_calibration_bundle(repository: Repository, bundle: Mapping[str, Any], *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 292) — Import a shipped grader-calibration bundle (warm priors, §grader cold start).
- `class ResolvedModel` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 377)
  - `emission_likelihoods(self, true_class: str) -> dict[str, float]` (line 388; public)
  - `marginal_confusion(self) -> dict[str, dict[str, float]]` (line 393; public) — P(G | Z): marginalize the joint emission over confidence buckets.
- `resolve_calibration_model(repository: Repository, *, grader_identity_hash: str | None, outcome_schema_id: str, outcome_schema_version: int, domain: str | None=None, length_bucket: str | None=None, clock: Clock | None=None) -> ResolvedModel` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 417) — Resolve the partial-pooling mixture for a context (§3.2).
- `posterior_over_true_class(resolved: ResolvedModel, *, observed_class: str, confidence_bucket: str, prior: Mapping[str, float] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 547) — P(Z | E, context) conditioning on the observed emission E=(G, conf_bucket).
- `certainty(posterior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 573) — 1 - H(p)/log(k): 0 for uniform, 1 for a point mass (§4.3).
- `credible_interval(resolved: ResolvedModel, *, observed_class: str, confidence_bucket: str, prior: Mapping[str, float] | None=None, draws: int=ENSEMBLE_DRAWS) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 592) — Deterministic Dirichlet ensemble interval on the leading-class posterior (§4.2).
- `class ModelPromotionError(ValueError)` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 642) — A model cannot be promoted to the requested status.
- `validate_promotion(model: Mapping[str, Any], *, to_status: str) -> None` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 646) — Enforce §3.2 promotion rules.
- `denominator_counts_from_samples(samples: Sequence[Mapping[str, Any]]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 680) — IPW-reweighted denominator contribution per sample stream (§4.7).

### Module constants

- `PRIOR_CONCENTRATION` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 37)
- `CONFIDENCE_MASS_SPLIT` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 44)
- `CONFIDENCE_BUCKETS` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 50)
- `ENSEMBLE_DRAWS` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 54)
- `ROBUST_QUANTILE` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 55)
- `GRADING_PROMPT_VERSION` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 58)
- `GRADER_OUTPUT_SCHEMA_VERSION` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 59)
- `CALIBRATION_ALGORITHM_VERSION` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 61)
- `_HEURISTIC_POLICY_PROVIDERS` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 66)
- `DENOMINATOR_BEARING_STREAMS` ([src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py), line 677)

## Internal implementation anchors

- `_model_content_hash(*, identity: Mapping[str, Any], scope: Mapping[str, Any], alphas: Mapping[str, Mapping[str, float]], status: str) -> str` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 134)
- `_sum_alphas(rows: Sequence[Mapping[str, Mapping[str, float]]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 407)
- `_uniform_fallback(repository: Repository, outcome_schema_id: str, outcome_schema_version: int) -> ResolvedModel` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 514)
- `_dirichlet_sample(rng: random.Random, alpha: Sequence[float]) -> list[float]` ([source](../../../../../../src/learnloop/attempts/grader_calibration.py), line 586)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `module`; statically calls `_sum_alphas`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `module`; statically calls `certainty`, `credible_interval`, `grader_identity_hash`, `posterior_over_true_class`, `resolve_calibration_model`
- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `import_calibration_bundle`; statically calls `import_calibration_bundle`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `module`; statically calls `resolve_calibration_model`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `BUILTIN_SCHEMAS`, `ensure_builtin_schemas`; calls `ensure_builtin_schemas`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `GRADER_CHANNEL_RELIABILITY`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_grader_channel_prior`; calls `resolve_grader_channel_prior`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_asymmetric_planted_channel_produces_nonsymmetric_matrix_and_direction`
  - `test_builtin_schemas_and_heuristic_priors_are_idempotent`
  - `test_confusion_updates_only_from_denominator_bearing_sources`
  - `test_exploratory_em_cannot_promote_to_live_calibrated`
  - `test_raw_confidence_only_affects_interpretation_through_bucket`
  - `test_resolution_global_fallback_never_crashes`
  - `test_resolution_seeds_and_missing_child_inherits_parent`
- [tests/test_grader_channel_prior_knobs.py](../../../../../../tests/test_grader_channel_prior_knobs.py) — direct import
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`

## Modification guidance

- Change grader calibration policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grader_calibration.py](../../../../../../src/learnloop/attempts/grader_calibration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
