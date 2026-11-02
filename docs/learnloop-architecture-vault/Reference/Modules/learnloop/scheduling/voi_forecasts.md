---
title: "learnloop.scheduling.voi_forecasts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/voi_forecasts.py"
source_paths:
  - "src/learnloop/scheduling/voi_forecasts.py"
source_commit: "cbd26b3e715642d45c0df27013a6ab9c1f29e5d5"
source_commit_timestamp: "2026-10-13T17:56:23-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.scheduling.voi_forecasts module"
  - "src/learnloop/scheduling/voi_forecasts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.voi_forecasts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.voi_forecasts` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: EVSI calibration Part B: record the forecast every live VOI decision runs on.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py) |
| Source lines | 474 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cbd26b3e715642d45c0df27013a6ab9c1f29e5d5` |
| Commit timestamp | `2026-10-13T17:56:23-04:00` |

## Public API

- `provenance_of(source: str | None) -> str` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 97)
- `parameter(name: str, value: Any, provenance: str, *, source: str | None=None, sample_count: int | None=None, note: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 101)
- `entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 133)
- `predictive(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 137)
- `posterior(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float], emission: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 147)
- `expected_information_gain(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 159) — Hypothesis EIG in nats: prior entropy minus expected posterior entropy.
- `forecast_block(likelihood: Mapping[str, Mapping[str, float]], belief: Mapping[str, float], *, action_of: Callable[[Mapping[str, float]], str | None], action_proxy: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 173) — Predicted answers, EIG, action after each answer and P(action change).
- `loss_summary(loss_table: AL.LossTable) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 206)
- `loss_table_parameters(loss_table: AL.LossTable, *, duration_estimates: Mapping[str, Mapping[str, Any]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 219) — Provenance of every number in a minutes loss table.
- `evsi_parameters(*, quantile: float=EV.ROBUST_QUANTILE, perturbation_delta: float=EV.PERTURBATION_DELTA, lambda_time: float=EV.LAMBDA_TIME, burden_cost: float=EV.BURDEN_COST) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 265)
- `rank_forecast(result: EV.RankResult, candidates: Sequence[EV.DiagnosticCandidate], loss_table: AL.LossTable, *, chosen_ref: str | None=None, committed: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 293) — The forecast body of one ``rank_feasible`` decision.
- `forecast_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 342) — The ``evsi.forecast_logging`` kill switch (on without a vault config).
- `record_forecast(repository: Repository | None, *, vault: Any=None, site: str, receipt_key: str, verdict: str, forecast: Mapping[str, Any], parameters: Sequence[Mapping[str, Any]], versions: Mapping[str, Any] | None=None, candidate_count: int=0, clock: Clock | None=None, **columns: Any) -> str | None` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 349) — Append one ``voi_forecasts`` receipt.
- `record_rank_feasible_forecast(repository: Repository | None, *, vault: Any=None, site: str, receipt_key: str, result: EV.RankResult, candidates: Sequence[EV.DiagnosticCandidate], loss_table: AL.LossTable, extra_parameters: Sequence[Mapping[str, Any]]=(), duration_estimates: Mapping[str, Mapping[str, Any]] | None=None, extra: Mapping[str, Any] | None=None, chosen_ref: str | None=None, committed: bool=False, clock: Clock | None=None, **columns: Any) -> str | None` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 420) — Record one ``rank_feasible`` decision (EVSI point/robust, P(change), loss).

### Module constants

- `FORECAST_VERSION` ([src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 46)
- `VOI_SITES` ([src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 51)
- `PROVENANCES` ([src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 74)
- `SOURCE_PROVENANCE` ([src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 77)
- `MAX_RECORDED_CANDIDATES` ([src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 94)

## Internal implementation anchors

- `_normalized(belief: Mapping[str, float], labels: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 125)
- `_candidate_forecast(candidate: EV.DiagnosticCandidate, loss_table: AL.LossTable) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 280)
- `_maybe_float(value: Any) -> float | None` ([source](../../../../../../src/learnloop/scheduling/voi_forecasts.py), line 411)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `parameter`; statically calls `parameter`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `parameter`; statically calls `parameter`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `module`; statically calls `parameter`, `record_rank_feasible_forecast`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `module`; statically calls `parameter`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `module`; statically calls `forecast_block`, `parameter`, `provenance_of`, `record_forecast`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `FORECAST_VERSION`, `entropy`, `posterior`; statically calls `entropy`, `posterior`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `module`; statically calls `record_rank_feasible_forecast`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `forecast_enabled`, `record_rank_feasible_forecast`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] — imports `module`; calls `has_table`, `insert_forecast`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]], [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]], [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_decision_mode_valuation_records_its_forecast_when_logging_is_on`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_forecast_block_predicts_answers_information_and_action_change`
  - `test_logging_never_raises_and_respects_the_kill_switch`
  - `test_the_ledger_is_append_only_and_idempotent`

## Modification guidance

- Change voi forecasts policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/voi_forecasts.py](../../../../../../src/learnloop/scheduling/voi_forecasts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
