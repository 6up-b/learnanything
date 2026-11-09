---
title: "learnloop.evsi_calibration.metrics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/metrics.py"
source_paths:
  - "src/learnloop/evsi_calibration/metrics.py"
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
  - "learnloop.evsi_calibration.metrics module"
  - "src/learnloop/evsi_calibration/metrics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.metrics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.metrics` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Score a simulation run: calibration, information, action change, minutes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/metrics.py](../../../../../../src/learnloop/evsi_calibration/metrics.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `reliability(pairs: Iterable[tuple[float, float]], bins: int=BINS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 40) — Reliability table + expected calibration error for (predicted, outcome) pairs.
- `outcome_calibration(checks: Sequence[CheckRecord]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 69) — (1) Predicted answer distributions vs the realized answers.
- `information(checks: Sequence[CheckRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 84) — (2) Predicted EIG vs realized entropy drop and vs information about the truth.
- `action_change(checks: Sequence[CheckRecord]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 118) — (3) Predicted vs realized probability that a check changes the chosen action.
- `value_of_checks(checks: Sequence[CheckRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 129) — Predicted EVSI (and its member quantiles) vs the realized value of each check.
- `episode_summary(episodes: Sequence[EpisodeRecord], rng: np.random.Generator, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 181) — (4) Checks and minutes to identify the misconception, and wasted minutes.
- `summarize(checks: Sequence[CheckRecord], episodes: Sequence[EpisodeRecord], *, seed: int, draws: int=400) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 217) — Per-policy metric blocks (1)-(4).
- `paired_difference(left: Sequence[EpisodeRecord], right: Sequence[EpisodeRecord], *, field_name: str='total_minutes', seed: int, draws: int=400) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 236) — Mean of ``right - left`` per learner (common random numbers), bootstrap CI.
- `kendall_tau(left: Sequence[str], right: Sequence[str]) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 259) — Kendall's tau-a between two rankings over their common items.
- `quantile_names() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 277)

### Module constants

- `BINS` ([src/learnloop/evsi_calibration/metrics.py](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 16)

## Internal implementation anchors

- `_ci(values: np.ndarray, groups: np.ndarray, rng: np.random.Generator, draws: int, stat=np.mean) -> list[float]` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 19) — Cluster bootstrap over ``groups`` (learner ids) of ``stat(values)``.
- `_round(value: float | None, digits: int=4) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/metrics.py), line 34)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `module`; statically calls `episode_summary`, `kendall_tau`, `paired_difference`, `summarize`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `reliability`; statically calls `reliability`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `reliability`; statically calls `reliability`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `module`; statically calls `episode_summary`, `paired_difference`, `summarize`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `CheckRecord`, `EpisodeRecord`, `MEMBER_QUANTILES`

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_metrics_reliability_tau_and_paired_differences`

## Modification guidance

- Make changes here when the responsibility remains metrics within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/metrics.py](../../../../../../src/learnloop/evsi_calibration/metrics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
