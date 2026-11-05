---
title: "learnloop.adaptive_difficulty.monitoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/monitoring.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/monitoring.py"
source_commit: "2778e23fe57cb9e86780e5e1e0b93ad814872e6e"
source_commit_timestamp: "2026-10-19T00:49:53-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.monitoring module"
  - "src/learnloop/adaptive_difficulty/monitoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.monitoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.monitoring` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Monitoring, never gating (spec_adaptive_difficulty_v1 §10.4, D3): scores, sequences, honest lines, auto-flags.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py) |
| Source lines | 285 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2778e23fe57cb9e86780e5e1e0b93ad814872e6e` |
| Commit timestamp | `2026-10-19T00:49:53-04:00` |

## Public API

- `log_loss(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 39)
- `brier(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 44)
- `bootstrap_interval(values: Sequence[float], *, samples: int=BOOTSTRAP_SAMPLES, seed: str=BOOTSTRAP_SEED, level: float=0.95) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 54) — The percentile bootstrap of a mean (field §7.4's rule as a monitor; D9's margin 0).
- `confidence_sequence(differences: Sequence[float], *, ranges: Sequence[tuple[float, float]] | None=None, bound: float=LOG_LOSS_BOUND, alpha: float=ALPHA, n0: int=CS_N0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 68) — An anytime-valid confidence sequence for the running mean of differences ``[choe2023]``.
- `verdict(sequence: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 99) — "helping" when the challenger's loss is below the comparator's throughout the sequence, "hurting" when above, else "can't tell yet" (the difference is challenger - comparator).
- `honest_line(subject: str, verdict_value: str, n: int) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 112)
- `reliability(predictions: Sequence[float], outcomes: Sequence[float], bins: int=10) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 116)
- `band_region_error(predictions: Sequence[float], outcomes: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 129) — The count-weighted mean |mean prediction - realized| over [0.6,0.7), [0.7,0.8), [0.8,0.9].
- `wilson(failures: int, n: int, z: float=1.96) -> list[float] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 144)
- `class Flag` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 155)
  - `as_dict(self) -> dict[str, Any]` (line 161; public)
- `comparison_flag(name: str, differences: Sequence[float], ranges: Sequence[tuple[float, float]] | None=None) -> Flag` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 176) — Fires when the live model is worse (its loss minus the comparator's), the sequence excluding 0.
- `readiness_flag(errors: Sequence[float | None]) -> Flag` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 184) — Band-region reliability error of ``@subject`` above 0.05 in two consecutive reports.
- `band_missed_flag(outcomes: Sequence[float]) -> Flag` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 193) — Realized success on AD-selected practice outside 0.60-0.88 over (at least) 200 selections.
- `dose_burden_flag(delivered: Sequence[Mapping[str, Any]], density_lowerings: Sequence[str], *, now: str) -> Flag` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 203) — Of the last 30 delivered extra offers at least 80% dismissed; or the cue density lowered within a visit after an offer three times in 14 days.
- `log_loss_difference(p_challenger: float, p_comparator: float, y: float) -> tuple[float, tuple[float, float]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 223) — The challenger's log loss minus the comparator's, and the two values it could take (its predictable range: both forecasts are fixed before the outcome).
- `difference_terms(records: Iterable[Mapping[str, Any]], challenger: str, comparator: str, *, split: str | None=None) -> tuple[list[float], list[tuple[float, float]]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 234) — Per scored record, the log-loss difference and its predictable range (the split's records).
- `differences(records: Iterable[Mapping[str, Any]], challenger: str, comparator: str, *, split: str | None=None) -> list[float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 252) — Per scored record, the challenger's log loss minus the comparator's (the split's records only).

### Module constants

- `CLIP` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 19)
- `LOG_LOSS_BOUND` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 20)
- `ALPHA` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 21)
- `CS_N0` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 22)
- `BOOTSTRAP_SAMPLES` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 23)
- `BOOTSTRAP_SEED` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 24)
- `BAND_REGION_BINS` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 25)
- `READINESS_ERROR_LIMIT` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 26)
- `BAND_MISSED` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 27)
- `BAND_MISSED_AFTER` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 28)
- `DOSE_DISMISS_WINDOW` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 29)
- `DOSE_DISMISS_SHARE` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 30)
- `DOSE_DENSITY_LOWERINGS` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 31)
- `DOSE_DENSITY_DAYS` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 32)
- `HELPING` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 34)
- `HURTING` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 35)
- `CANT_TELL` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 36)
- `FLAG_SWITCHES` ([src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 165)

### Explicit exports

`__all__` declares:

- `ALPHA`
- `BAND_MISSED`
- `CANT_TELL`
- `CLIP`
- `FLAG_SWITCHES`
- `Flag`
- `HELPING`
- `HURTING`
- `LOG_LOSS_BOUND`
- `band_missed_flag`
- `band_region_error`
- `bootstrap_interval`
- `brier`
- `comparison_flag`
- `confidence_sequence`
- `difference_terms`
- `differences`
- `dose_burden_flag`
- `honest_line`
- `log_loss`
- `log_loss_difference`
- `readiness_flag`
- `reliability`
- `verdict`
- `wilson`

## Internal implementation anchors

- `_seed(text: str) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]] — imports `module`; statically calls `confidence_sequence`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `band_missed_flag`, `band_region_error`, `bootstrap_interval`, `comparison_flag`, `confidence_sequence`, `difference_terms`, `dose_burden_flag`, `honest_line`, `log_loss`, `readiness_flag`, `reliability`, `verdict`, `wilson`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `confidence_sequence`, `log_loss_difference`
- [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]] — imports `module`; statically calls `band_missed_flag`, `band_region_error`, `comparison_flag`, `dose_burden_flag`, `log_loss_difference`, `readiness_flag`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `module`; statically calls `comparison_flag`, `log_loss_difference`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose_report|learnloop.adaptive_difficulty.dose_report]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]], [[Reference/Modules/learnloop/sim/ad_gates|learnloop.sim.ad_gates]], [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_sim.py](../../../../../../tests/test_ad23_sim.py) — direct import
  - `test_auto_flags_fire_on_synthetic_logs`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
  - `test_confidence_sequence_is_anytime_valid_under_the_null`
  - `test_honest_verdicts_follow_the_sequence`
  - `test_monitoring_applies_field_rule_as_monitor_never_gate`

## Modification guidance

- Make changes here when the responsibility remains monitoring within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/monitoring.py](../../../../../../src/learnloop/adaptive_difficulty/monitoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
