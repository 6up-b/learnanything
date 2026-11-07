---
title: "learnloop.adaptive_difficulty.history_resolve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/history_resolve.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/history_resolve.py"
source_commit: "246bdfc0b7d92c7c8514539af343fab875001cf8"
source_commit_timestamp: "2026-11-06T20:35:00-05:00"
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
  - "learnloop.adaptive_difficulty.history_resolve module"
  - "src/learnloop/adaptive_difficulty/history_resolve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.history_resolve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.history_resolve` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router objective RO2's versioned resolver for ``lo_cold_success`` (spec_router_objective_v1 §6.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py) |
| Source lines | 308 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `246bdfc0b7d92c7c8514539af343fab875001cf8` |
| Commit timestamp | `2026-11-06T20:35:00-05:00` |

## Public API

- `interpolate(curve: Mapping[str, Any], lag_days: float) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 74) — The curve's probability at ``lag_days``: linear in log time between the stated lags; the first lag's value below it; None past the last (censored ``beyond_measured_lag``).
- `resolve(connection: Any, vault: Any, repository: Any, *, now: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 164) — Every ``lo_cold_success`` curve resolved under both bindings (pure reads; zero model calls).
- `resolve_curves(connection: Any, vault: Any, repository: Any, groups: Sequence[Mapping[str, Any]], *, now: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 175) — The same event's curves stated outside ``forecast_receipts`` (router objective RO4's per-option policy forecasts on its traces, Codex review F9), resolved by exactly these bindings: each group names its ``plan_presentation_id`` (the block's), ``learning_object_id``, ``forecaster…

### Module constants

- `RESOLVER_VERSION` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 58)
- `PER_PROTOCOL` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 59)
- `INTENTION_TO_TREAT` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 60)
- `BINDINGS` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 61)
- `MAX_LAG_DAYS` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 64)

### Explicit exports

`__all__` declares:

- `BINDINGS`
- `INTENTION_TO_TREAT`
- `MAX_LAG_DAYS`
- `PER_PROTOCOL`
- `RESOLVER_VERSION`
- `interpolate`
- `resolve_curves`
- `resolve`

## Internal implementation anchors

- `_days(later: Any, earlier: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 67)
- `_groups(receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 90) — One forecast curve per presentation and forecaster (the receipts of one call).
- `class _Uncapped` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 112) — The material view as the reading collectors see it, with nothing on record: each source event is listed whether or not a sweep recorded (or a cap refused) its receipt.
- `_opportunities(connection: Any, vault: Any, repository: Any, view: Any, *, now: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 132) — Every learning opportunity on any LO up to ``now`` (``id``, ``learning_object_id``, ``at``): the uncapped source events and AD's receipts, one per source row and LO.
- `_outcome_state(row: Mapping[str, Any], category: int) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 155) — The outcome's help state beside its binary label (spec §6.2: A4's states stay distinct).
- `_resolve_groups(connection: Any, vault: Any, repository: Any, view: Any, groups: Sequence[Mapping[str, Any]], *, now: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 194)
- `_log_loss(p: float | None, y: float | None) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 301)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `resolve_curves`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `resolve_curves`; statically calls `resolve_curves`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `CENSORED`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `unassisted_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `VaultReadingMap`; calls `VaultReadingMap`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `log_loss`; calls `log_loss`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `listed_events`, `source_stamp`; calls `listed_events`, `source_stamp`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `LO_COLD_SUCCESS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]], [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_log_time_interpolation`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_rofu_learning.py](../../../../../../tests/test_rofu_learning.py) — direct import
  - `test_below_the_tag_the_combiner_reads_no_trace`
  - `test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_one_decisions_builds_read_the_fit_once_and_the_next_decision_afresh`
  - `test_the_indexed_resolver_gives_the_landing_codes_rows`

## Modification guidance

- Make changes here when the responsibility remains history resolve within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
