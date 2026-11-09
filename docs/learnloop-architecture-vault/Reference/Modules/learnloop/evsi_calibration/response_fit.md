---
title: "learnloop.evsi_calibration.response_fit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/response_fit.py"
source_paths:
  - "src/learnloop/evsi_calibration/response_fit.py"
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
  - "learnloop.evsi_calibration.response_fit module"
  - "src/learnloop/evsi_calibration/response_fit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.response_fit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.response_fit` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Fit a misconception response model to Eedi's real answer patterns.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/response_fit.py](../../../../../../src/learnloop/evsi_calibration/response_fit.py) |
| Source lines | 579 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FitSettings` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 59)
  - `as_dict(self) -> dict[str, Any]` (line 71; public)
- `class Estimate` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 76) — A pooled estimate across triples: median, mean and a bootstrap CI of the median.
  - `as_dict(self) -> dict[str, Any]` (line 85; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'Estimate'` (line 94; public)
- `class TripleFit` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 100)
  - `params(self) -> dict[str, float]` (line 111; public)
  - `as_dict(self) -> dict[str, Any]` (line 127; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'TripleFit'` (line 140; public)
- `class ResponseFit` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 167) — The fitted response model: pooled estimates, per-subject medians, dispersion.
  - `param(self, name: str, subject_id: int | None=None) -> float` (line 181; public)
  - `as_dict(self) -> dict[str, Any]` (line 188; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'ResponseFit'` (line 205; public)
- `fit_response_model(responses: NeuripsResponses, *, settings: FitSettings | None=None, subjects: Sequence[int] | None=None) -> ResponseFit` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 415) — Find misconception triples per subject and fit the latent class model.
- `assemble_response_fit(triples: Sequence[TripleFit], *, settings: FitSettings, source: Mapping[str, Any]) -> ResponseFit` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 454) — Pool fitted triples into a :class:`ResponseFit` (medians, subject medians, dispersion, persistence).

### Module constants

- `RESPONSE_FIT_VERSION` ([src/learnloop/evsi_calibration/response_fit.py](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 51)
- `CLASSES` ([src/learnloop/evsi_calibration/response_fit.py](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 55)
- `PARAMETERS` ([src/learnloop/evsi_calibration/response_fit.py](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 153)

## Internal implementation anchors

- `_pair_lifts(answers: np.ndarray, users: np.ndarray, q_index: np.ndarray, correct_by_q: np.ndarray, n_questions: int, settings: FitSettings) -> dict[tuple[int, int], tuple[float, int, int]]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 220) — Best co-selection lift per question pair: (i, j) -> (lift, di, dj), i < j.
- `_triples_from_pairs(best: Mapping[tuple[int, int], tuple[float, int, int]], settings: FitSettings) -> list[tuple[float, tuple[int, int, int], tuple[int, int, int]]]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 271) — Triples whose three pairwise best distractor choices agree, best first.
- `_em_three_class(table: Mapping[tuple[int, int, int], int], iterations: int) -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 309) — Three-class latent class model on three 3-category items (deterministic init).
- `_label_classes(theta: np.ndarray) -> dict[str, int]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 345)
- `_persistence(categories: np.ndarray, minutes: np.ndarray) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 353) — Repeat-error rates after a designated vs a correct first encounter.
- `_bootstrap_median(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 379)
- `_estimate(values: Sequence[float], rng: np.random.Generator, draws: int) -> Estimate` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 387)
- `_consistency_concentration(triples: Sequence[TripleFit]) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 395) — Beta concentration of item-level consistency (between-item spread only).
- `_fit_subject(responses: NeuripsResponses, subject: int, rows: np.ndarray, settings: FitSettings) -> list[TripleFit]` ([source](../../../../../../src/learnloop/evsi_calibration/response_fit.py), line 493)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `FitSettings`, `ResponseFit`, `fit_response_model`; statically calls `FitSettings`, `fit_response_model`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `ResponseFit`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `FitSettings`, `ResponseFit`, `assemble_response_fit`; statically calls `FitSettings`, `assemble_response_fit`
- [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]] — imports `CORRECT`, `DESIGNATED`, `OTHER`, `TripleFit`
- [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] — imports `CORRECT`, `DESIGNATED`, `FitSettings`, `OTHER`, `ResponseFit`, `TripleFit`, `_em_three_class`, `_label_classes`, `_persistence`, `assemble_response_fit`; statically calls `FitSettings`, `TripleFit`, `_em_three_class`, `_label_classes`, `_persistence`, `assemble_response_fit`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `ResponseFit`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `NeuripsResponses`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]], [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]], [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_the_fit_recovers_the_planted_consistency`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains response fit within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/response_fit.py](../../../../../../src/learnloop/evsi_calibration/response_fit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
