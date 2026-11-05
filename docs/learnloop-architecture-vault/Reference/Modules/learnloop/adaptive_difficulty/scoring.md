---
title: "learnloop.adaptive_difficulty.scoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/scoring.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/scoring.py"
source_commit: "workspace/uncommitted @ HEAD 5a4f18feff72f2759ad90fe426bc5021ea5948f1"
source_commit_timestamp: "2026-11-04T23:02:05-05:00"
source_worktree_state: "modified"
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
  - "learnloop.adaptive_difficulty.scoring module"
  - "src/learnloop/adaptive_difficulty/scoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.scoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.scoring` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The forecast-score replayer (spec_adaptive_difficulty_v1 §8.3; DERIVED ``item_forecast_scores``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py) |
| Source lines | 382 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 5a4f18feff72f2759ad90fe426bc5021ea5948f1` |
| Commit timestamp | `2026-11-04T23:02:05-05:00` |

## Public API

- `log_loss(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 33)
- `brier(p: float, y: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 38)
- `score_rows(connection: Any, vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 43) — The scores of every item forecast receipt (pure reads; zero model calls).
- `rebuild(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 114) — Clear and rebuild ``item_forecast_scores`` (zero model calls).
- `calibration_slopes(points: Mapping[str, list[tuple[float, float]]], *, scale: float=1.0, prior: Mapping[str, tuple[float, float]]=SLOPE_PRIOR) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 253) — Each model and prompt version's calibration slope under the hierarchical prior: the population (every version pooled) is fitted under the seeded prior, and each version under a prior centred at the population's posterior with the seeded spread, so a new version starts from the p…
- `history_report(connection: Any, vault: Any, repository: Any, *, now: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 277) — RO2's comparisons (spec §6.4): ``llm_history_v1:H3`` against ``mastery_ekf``, ``lo_general+composite`` and ``llm_v3:llm`` on the same presentations (log loss and calibration on field's first-attempt split first, then repeats), delayed cold between the rungs (intention to treat)…

### Module constants

- `SCORE_VERSION` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 29)
- `CLIP` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 30)
- `HISTORY_REPORT_VERSION` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 135)
- `HISTORY_SUBJECT` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 136)
- `HISTORY_COMPARATORS` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 138)
- `SLOPE_PRIOR` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 144)
- `FIT_TOLERANCE` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 184)
- `FIT_ITERATIONS` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 185)
- `FIT_ARMIJO` ([src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 187)

### Explicit exports

`__all__` declares:

- `CLIP`
- `HISTORY_COMPARATORS`
- `HISTORY_REPORT_VERSION`
- `SCORE_VERSION`
- `SLOPE_PRIOR`
- `brier`
- `calibration_slopes`
- `history_report`
- `log_loss`
- `rebuild`
- `score_rows`

## Internal implementation anchors

- `_paired(left: Mapping[str, tuple[float, float]], right: Mapping[str, tuple[float, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 145) — The mean paired log-loss difference ``left - right`` (below zero, ``left`` scores better) on the keys both hold (each ``(p, y)``, the same outcome), with AD's anytime-valid confidence sequence on it (``monitoring.confidence_sequence`` over each difference's predictable range, §8…
- `_calibration(points: list[tuple[float, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 164)
- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 173)
- `_log1pexp(z: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 178)
- `_map_fit(points: list[tuple[float, float]], prior: Mapping[str, tuple[float, float]], scale: float=1.0, iterations: int=FIT_ITERATIONS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/scoring.py), line 190) — The MAP intercept and slope of ``y ~ Bernoulli(sigmoid(a + b * logit(p)))`` under independent normal priors (each sd times ``scale``), with the Laplace sd of each at the optimum.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `rebuild`; statically calls `rebuild`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `calibration_slopes`, `score_rows`; statically calls `calibration_slopes`, `score_rows`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `log_loss`; statically calls `log_loss`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `history_report`; statically calls `history_report`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild`; statically calls `rebuild`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/monitoring|learnloop.adaptive_difficulty.monitoring]] — imports `module`; calls `confidence_sequence`, `log_loss_difference`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `unassisted_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `successor_active`; calls `successor_active`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `has_table`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `clear_derived`, `has_table`, `write_scores`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `valid_for_serve`; calls `valid_for_serve`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_ad_never_writes_evidence`
  - `test_pre_exposed_presentation_excluded_from_update_and_scoring`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_an_unconverged_calibration_fit_is_reported_not_presented`
  - `test_calibration_slopes_converge_on_a_reversed_forecaster`
  - `test_calibration_slopes_shrink_a_new_version_to_the_population`
  - `test_the_report_compares_on_the_same_presentations_and_reports_missing_pairs`

## Modification guidance

- Make changes here when the responsibility remains scoring within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/scoring.py](../../../../../../src/learnloop/adaptive_difficulty/scoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
