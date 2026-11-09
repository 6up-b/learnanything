---
title: "learnloop.evsi_calibration.family_fit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/family_fit.py"
source_paths:
  - "src/learnloop/evsi_calibration/family_fit.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.family_fit module"
  - "src/learnloop/evsi_calibration/family_fit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.family_fit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.family_fit` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Fit structurally different simulator families to the same Eedi answers.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py) |
| Source lines | 961 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FamilyFitSettings` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 96)
  - `as_dict(self) -> dict[str, Any]` (line 109; public)
- `fit_lca(triples: Sequence[TripleData], settings: FamilyFitSettings) -> list[TripleFit]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 116)
- `lca_response_fit(fits: Sequence[TripleFit], *, seed: int, source: Mapping[str, Any]) -> ResponseFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 139)
- `predict_lca(fit: TripleFit, roles: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 161) — (n, 3 items, 4 roles) leave-one-out predictions on a triple.
- `fit_marginal(triples: Sequence[TripleData]) -> dict[int, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 181)
- `cdm_profiles(attributes: int, max_held: int=CDM_MAX_HELD) -> list[tuple[int, tuple[int, ...]]]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 195)
- `class CdmSubjectFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 223)
  - `as_dict(self) -> dict[str, Any]` (line 236; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'CdmSubjectFit'` (line 251; public)
  - `summary(self) -> dict[str, float]` (line 265; public) — The common quantities (as the latent class model names them) plus the profile structure the simulator transfers.
- `fit_cdm_subject(subject: SubjectData, settings: FamilyFitSettings) -> CdmSubjectFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 306)
- `predict_cdm(fit: CdmSubjectFit, position: int, roles: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 363) — Leave-one-out predictions on one of the subject's triples (``position``), conditioning only on that triple's other two answers.
- `gauss_hermite_grid(nodes: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 383) — 2-D standard-normal product grid: theta, eta, weights (sum 1).
- `nrm_logits(params: np.ndarray, theta: np.ndarray, eta: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 399) — (..., 4) role logits for item parameters ``params`` (..., 7).
- `class NrmTripleFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 436)
  - `as_dict(self) -> dict[str, Any]` (line 444; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'NrmTripleFit'` (line 455; public)
- `fit_nrm_triple(payload: tuple[TripleData, FamilyFitSettings]) -> NrmTripleFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 466)
- `predict_nrm(fit: NrmTripleFit, roles: np.ndarray, nodes: int) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 501)
- `class LtaFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 519) — Latent transition model: per-triple start mix and emissions, shared transitions.
  - `as_dict(self) -> dict[str, Any]` (line 534; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'LtaFit'` (line 547; public)
  - `triple_fit(self, index: int) -> TripleFit` (line 559; public) — This triple's emissions and start mix as a latent class triple (the simulator's row machinery reads these).
- `fit_lta(triples: Sequence[TripleData], lca: Mapping[int, TripleFit], settings: FamilyFitSettings) -> LtaFit` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 612) — Baum-Welch over every fit-split triple sequence in time order.
- `predict_lta(fit: LtaFit, triple: TripleData) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 663) — Leave-one-out predictions in time order (forward over each completion).
- `class Predictions` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 725) — Stacked held-out predictions of one family: (N, 4) role forecasts, realized roles, users.
  - `add(self, forecast: np.ndarray, roles: np.ndarray, users: np.ndarray) -> None` (line 732; public)
  - `stacked(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]` (line 737; public)
- `score_predictions(forecast: np.ndarray, realized: np.ndarray, users: np.ndarray, *, baseline_three: np.ndarray | None, rng: np.random.Generator, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 743)
- `class FamilyFits` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 811) — Every family fitted to the fit split, with the held-out validation.
  - `as_dict(self) -> dict[str, Any]` (line 823; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'FamilyFits'` (line 836; public)
- `fit_families(triples: Sequence[TripleData], subjects: Sequence[SubjectData], settings: FamilyFitSettings, *, source: Mapping[str, Any], progress: Any=None) -> FamilyFits` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 851) — Fit every family on the fit split and score all of them on the held-out split.
- `validate_families(held_out: Sequence[TripleData], fit_split: Sequence[TripleData], lca: Mapping[int, TripleFit], cdm: Mapping[int, CdmSubjectFit], subjects: Sequence[SubjectData], nrm: Mapping[int, NrmTripleFit], lta: LtaFit, settings: FamilyFitSettings) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 892) — Score every family on the same held-out predictions (triples every family fitted).

### Module constants

- `FAMILY_FIT_VERSION` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 84)
- `FAMILIES` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 85)
- `STATES` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 86)
- `ADEQUACY_MIN_AUC` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 88)
- `ADEQUACY_MIN_NLL_GAIN` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 89)
- `ADEQUACY_MAX_ECE` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 90)
- `CDM_MAX_HELD` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 92)
- `_CDM_INIT` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 214)
- `NRM_PARAMS` ([src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 396)

### Explicit exports

`__all__` declares:

- `FAMILIES`
- `CdmSubjectFit`
- `FamilyFitSettings`
- `FamilyFits`
- `LtaFit`
- `NrmTripleFit`
- `cdm_profiles`
- `fit_cdm_subject`
- `fit_families`
- `fit_lca`
- `fit_lta`
- `fit_nrm_triple`
- `gauss_hermite_grid`
- `nrm_logits`
- `predict_cdm`
- `predict_lca`
- `predict_lta`
- `predict_nrm`
- `validate_families`

## Internal implementation anchors

- `_lca_tables(fit: TripleFit) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 143)
- `_three_to_four(probabilities: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 149) — (..., 3) categories -> (..., 4) roles: 'other' split evenly (as the simulator's latent class rows split it).
- `_cdm_groups(profiles: Sequence[tuple[int, tuple[int, ...]]], attribute: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 202) — (P, J) response group: 2*triggered + skill.
- `_softmax(z: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 410)
- `_nrm_item_objective(params: np.ndarray, counts: np.ndarray, theta: np.ndarray, eta: np.ndarray, prior_sd: float) -> tuple[float, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 416)
- `_lta_sequences(triples: Sequence[TripleData]) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 575)
- `_lta_forward_backward(start: np.ndarray, emission: np.ndarray, transitions: np.ndarray, seq: Mapping[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 587) — Posterior state marginals (n, 3 steps, 3), pair posteriors (n, 2, 3, 3), log likelihoods (n,).
- `_auc(scores: np.ndarray, labels: np.ndarray) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 690)
- `_ece(predicted: np.ndarray, outcome: np.ndarray, bins: int=10) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/family_fit.py), line 711)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `FamilyFitSettings`, `FamilyFits`, `fit_families`; statically calls `FamilyFitSettings`, `fit_families`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `FamilyFits`, `nrm_logits`; statically calls `nrm_logits`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `FamilyFits`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]] — imports `GAP_LATER`, `GAP_SAME_SESSION`, `SubjectData`, `TripleData`, `category_counts`, `item_roles`; calls `category_counts`, `item_roles`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `CORRECT`, `DESIGNATED`, `FitSettings`, `OTHER`, `ResponseFit`, `TripleFit`, `_em_three_class`, `_label_classes`, `_persistence`, `assemble_response_fit`; calls `FitSettings`, `TripleFit`, `_em_three_class`, `_label_classes`, `_persistence`, `assemble_response_fit`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `dataclasses`, `itertools`, `math`, `typing`
- Third party: `numpy`, `scipy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_every_family_beats_the_marginal_on_held_out_students`
  - `test_the_learning_family_recovers_a_planted_within_session_transition`

## Modification guidance

- Make changes here when the responsibility remains family fit within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/family_fit.py](../../../../../../src/learnloop/evsi_calibration/family_fit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
