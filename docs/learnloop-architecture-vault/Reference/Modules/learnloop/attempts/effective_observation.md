---
title: "learnloop.attempts.effective_observation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/effective_observation.py"
source_paths:
  - "src/learnloop/attempts/effective_observation.py"
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
  - "learnloop.attempts.effective_observation module"
  - "src/learnloop/attempts/effective_observation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.effective_observation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.effective_observation` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Reliability-aware EffectiveObservation (spec_p0_measurement_correctness §4.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/effective_observation.py](../../../../../../src/learnloop/attempts/effective_observation.py) |
| Source lines | 466 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `shared_certainty_lcb(*, joint_alpha: Mapping[str, Mapping[str, float]], observed_emission: str, calibration_model_hash: str, posterior: Mapping[str, float], projection_algorithm_version: str=SHARED_CERTAINTY_PROJECTION_VERSION, quantile: float | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 51) — THE one canonical certainty LCB (spec §4.3 final ¶).
- `expected_true_score_fraction(posterior: Mapping[str, float], score_fraction: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 107) — ``E[true_score_fraction] = sum_z P(Z|E) * score_fraction[z]``.
- `class EffectiveObservation` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 118) — The reliability-discounted evidence one graded observation contributes.
  - `epistemic_factor(self) -> float` (line 143; public) — ``certainty_lcb / certainty`` — model-level doubt only (module docstring).
  - `effective_mass(self) -> float` (line 160; public)
  - `positive_mass(self) -> float` (line 172; public)
  - `negative_mass(self) -> float` (line 176; public)
- `effective_observation_from_posterior(*, observation_id: str | None, posterior: Mapping[str, float], score_fraction: Mapping[str, float], certainty_lcb: float, attempt_type_mass: float, assistance_discount: float=1.0, familiarity_discount: float=1.0, quarantined: bool=False, unassessable: bool=False, calibration_model_id: str | None=None, calibration_model_hash: str | None=None, calibration_status: str='heuristic', projection_algorithm_version: str | None=None, lineage_model_ids: tuple[str, ...]=()) -> EffectiveObservation` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 180) — Build an EffectiveObservation from an already-computed posterior + LCB.
- `class EffectiveObservationReferences` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 223) — Bulk-loaded immutable references for one evidence-ledger replay.
- `load_effective_observation_references(repository: Repository, interpretations: Iterable[Mapping[str, Any] | None]) -> EffectiveObservationReferences` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 234) — Load every DB input needed by ``build_effective_observation`` once.
- `build_effective_observation(repository: Repository, *, interpretation: Mapping[str, Any] | None, score_fraction: Mapping[str, float], attempt_type_mass: float, assistance_discount: float=1.0, familiarity_discount: float=1.0, observation_id: str | None=None, unassessable: bool=False, references: EffectiveObservationReferences | None=None) -> EffectiveObservation` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 290) — Assemble the EffectiveObservation for a P0.2 calibrated interpretation.

### Module constants

- `SHARED_CERTAINTY_PROJECTION_VERSION` ([src/learnloop/attempts/effective_observation.py](../../../../../../src/learnloop/attempts/effective_observation.py), line 48)

## Internal implementation anchors

- `_certainty(posterior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 94) — 1 - H(p)/log(K): 0 for uniform, 1 for a point mass (§4.3).
- `_certainty_lcb_for_interpretation(repository: Repository, interpretation: Mapping[str, Any], posterior: Mapping[str, float], *, references: EffectiveObservationReferences | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 381) — Fallback recompute of the shared certainty LCB for a row that predates the persisted ``shared_certainty_lcb`` column (H1, spec §4.3 final ¶).
- `_resolved_lcb_quantile(repository: Repository) -> float` ([source](../../../../../../src/learnloop/attempts/effective_observation.py), line 463)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `module`; statically calls `shared_certainty_lcb`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `load_effective_observation_references`; statically calls `load_effective_observation_references`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `EffectiveObservationReferences`, `build_effective_observation`, `load_effective_observation_references`; statically calls `build_effective_observation`, `load_effective_observation_references`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `module`; calls `_sum_alphas`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `certainty_lcb`, `decision_context_hash`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `CERTAINTY_LCB_QUANTILE_DEFAULT`, `resolve_grader_channel_prior`; calls `resolve_grader_channel_prior`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]], [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_effective_observation.py](../../../../../../tests/test_effective_observation.py) — direct import
  - `test_adjudicated_grade_has_higher_certainty_than_heuristic`
  - `test_epistemic_factor_strips_aleatoric_double_count`
  - `test_missing_interpretation_is_zero_mass_never_full_credit`
  - `test_point_posterior_has_certainty_one_and_full_split`
  - `test_quarantined_and_unassessable_contribute_zero`
  - `test_quarantined_interpretation_contributes_zero`
  - `test_reliability_never_creates_mass_and_discounts_multiply`
  - `test_shared_certainty_lcb_agrees_across_mastery_and_certification`
  - `test_uniform_posterior_yields_zero_certification_mass`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_p0_replays_bulk_load_calibration_references_once`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_narrowing_model_monotonically_increases_effective_mass`

## Modification guidance

- Change effective observation policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/effective_observation.py](../../../../../../src/learnloop/attempts/effective_observation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
