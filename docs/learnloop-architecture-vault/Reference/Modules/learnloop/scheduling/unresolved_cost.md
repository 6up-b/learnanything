---
title: "learnloop.scheduling.unresolved_cost"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/unresolved_cost.py"
source_paths:
  - "src/learnloop/scheduling/unresolved_cost.py"
source_commit: "8c3cfe68ac65cac8120739b37fbde26d8d4b4508"
source_commit_timestamp: "2026-10-13T18:15:25-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.unresolved_cost module"
  - "src/learnloop/scheduling/unresolved_cost.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.unresolved_cost`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.unresolved_cost` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: EVSI calibration Part C: what leaving a misconception unresolved costs, measured.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py) |
| Source lines | 282 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8c3cfe68ac65cac8120739b37fbde26d8d4b4508` |
| Commit timestamp | `2026-10-13T18:15:25-04:00` |

## Public API

- `class UnresolvedCost` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 67) — The shrunk estimate and every input it came from.
  - `as_dict(self) -> dict[str, Any]` (line 82; public)
- `estimate_unresolved_cost(repository: Repository, *, pseudo_count: float) -> UnresolvedCost` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 185) — The shrunk minutes an unresolved persistent misconception costs.
- `unresolved_minutes_for_scopes(estimate: UnresolvedCost, scopes: Mapping[str, str], *, reasons: Mapping[str, str] | None=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 221) — Per-hypothesis cell entries for hypotheses whose cause scope the caller names: a persistent scope (:data:`PERSISTENT_SCOPES`) is charged ``estimate``; any other scope costs nothing later once the moment passes (0 minutes, ``structural``), with ``reasons[hypothesis]`` as its sour…
- `unresolved_minutes_for_hypotheses(repository: Repository, hypothesis_ids: Sequence[str], *, pseudo_count: float) -> tuple[dict[str, dict[str, Any]], UnresolvedCost]` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 263) — ``({hypothesis: {"minutes": U, provenance...}}, estimate)`` for a causal loss table.

### Module constants

- `UNRESOLVED_COST_VERSION` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 45)
- `EEDI_EXCESS_REPEAT_RATE` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 50)
- `ENCOUNTERS_UNTIL_CAUGHT` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 53)
- `CENSOR_DAYS` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 55)
- `MIN_TIMED_ATTEMPTS` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 60)
- `LATENCY_CAP_MINUTES` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 61)
- `PERSISTENT_SCOPES` ([src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 63)

## Internal implementation anchors

- `_parse_time(value: Any) -> float | None` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 113)
- `_personal_history(repository: Repository) -> tuple[list[float], int, dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/unresolved_cost.py), line 118) — Repeated-error minutes per recurrence class (+ censored count, detail).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `module`; statically calls `unresolved_minutes_for_hypotheses`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `module`; statically calls `estimate_unresolved_cost`, `unresolved_minutes_for_scopes`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `estimate_unresolved_cost`; statically calls `estimate_unresolved_cost`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]], [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_measured_loss_switch_charges_unresolved_minutes_in_the_shadow`
  - `test_unresolved_cost_shrinks_the_eedi_prior_toward_personal_history`
  - `test_untimed_recurrence_is_not_a_measured_zero`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_misconception_labels_are_charged_the_learners_recurrence_measured_cost`
  - `test_rank_four_off_keeps_todays_table_for_every_label_class`
  - `test_rank_four_off_prices_the_minutes_only_table_exactly`
  - `test_rank_four_on_charges_only_misconceptions_confusions_and_unknown_causes`

## Modification guidance

- Change unresolved cost policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/unresolved_cost.py](../../../../../../src/learnloop/scheduling/unresolved_cost.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
