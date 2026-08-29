---
title: "learnloop.scheduling.prequential"
type: "module-reference"
status: "current"
refactor_status: "DORMANT"
version: "1.0.0"
source_path: "src/learnloop/scheduling/prequential.py"
source_paths:
  - "src/learnloop/scheduling/prequential.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.scheduling.prequential module"
  - "src/learnloop/scheduling/prequential.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/dormant"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.prequential`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.prequential` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 6 (DESCOPED, U-025) -- prequential held-out scoring of shadow predictive components (spec_p4_controller_and_scale §7.1/§7.3; design §B step 6, §F).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/prequential.py](../../../../../../src/learnloop/scheduling/prequential.py) |
| Source lines | 276 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `DORMANT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Dormant or disabled boundary
> The source explicitly withholds live workflow authority. Its code/tests remain inspectable, but activation is a separate product and evidence decision.

## Public API

- `brier(pairs: Sequence[tuple[float, float]]) -> float | None` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 47) — Mean squared error of probabilistic predictions vs {0,1} outcomes.
- `log_loss(pairs: Sequence[tuple[float, float]]) -> float | None` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 55) — Mean negative log-likelihood of {0,1} outcomes under the predicted probability.
- `class PrequentialReport` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 68)
  - `as_dict(self) -> dict[str, Any]` (line 78; public)
- `component_report(repository: Repository, *, component: str, outcome_key: str='cold_success', persist: bool=True, clock: Clock | None=None) -> PrequentialReport` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 185) — The PRIMARY product (§7.3): a prequential calibration/error report for one predictive component at the next-spaced-cold-review horizon, split by target family/ surface group.
- `composed_selector_report(repository: Repository, *, outcome_key: str='cold_success', persist: bool=True, clock: Clock | None=None) -> PrequentialReport` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 212) — The SECONDARY product (§7.3): the composed-selector comparison.
- `reports_for(repository: Repository, *, target_kind: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 269)

### Module constants

- `REPORT_SCHEMA_VERSION` ([src/learnloop/scheduling/prequential.py](../../../../../../src/learnloop/scheduling/prequential.py), line 36)
- `HORIZON_KIND` ([src/learnloop/scheduling/prequential.py](../../../../../../src/learnloop/scheduling/prequential.py), line 38)

## Internal implementation anchors

- `_clip(p: float) -> float` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 43)
- `_effective_sample(pairs: Sequence[tuple[float, float]]) -> int` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 90) — Effective sample size = number of resolved, non-censored pairs.
- `_metrics_body(pairs: Sequence[tuple[float, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 97)
- `_resolved_outcomes_by_decision(repository: Repository) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 113)
- `_component_predictions(repository: Repository, scorer_kind: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 125)
- `_time_bucket(window: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 135) — The calendar-date time bucket a resolved outcome falls in (audit L3/D7).
- `_pairs_for(repository: Repository, scorer_kind: str, *, outcome_key: str) -> tuple[list[tuple[float, float]], dict[str, dict[str, list[tuple[float, float]]]]]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 144) — Return (all_pairs, split_groups).
- `_splits_body(split_groups: dict[str, dict[str, list[tuple[float, float]]]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 174) — Metrics per group within each split dimension, deterministically ordered.
- `_persist_report(repository: Repository, report: PrequentialReport, *, clock: Clock | None) -> PrequentialReport` ([source](../../../../../../src/learnloop/scheduling/prequential.py), line 237)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_prequential.py](../../../../../../tests/test_prequential.py) — direct import
  - `test_brier_and_log_loss`
  - `test_component_report_joins_predictions_to_cold_outcomes`
  - `test_composed_selector_report_is_secondary`
  - `test_report_ignores_unresolved_and_immediate_outcomes`
  - `test_report_repersist_is_idempotent_on_hash`
- [tests/test_shadow_components.py](../../../../../../tests/test_shadow_components.py) — direct import
  - `test_component_promotion_emits_u022_evidence_and_feeds_inputs_only`
  - `test_component_promotion_refuses_when_not_beating_incumbent`
  - `test_component_promotion_refuses_without_enough_evidence`
  - `test_monolithic_action_chooser_refuses_even_a_wide_margin_report`

## Modification guidance

- Change prequential policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This module is explicitly dormant/disabled. Do not grant it live workflow authority without a product decision, activation evidence, and tests for the newly reachable path.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/prequential.py](../../../../../../src/learnloop/scheduling/prequential.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
