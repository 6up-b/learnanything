---
title: "learnloop.daily_plan.intent_cost"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/intent_cost.py"
source_paths:
  - "src/learnloop/daily_plan/intent_cost.py"
source_commit: "1d5ba0272bb7d749483eea0f91c9eda2030bc4e9"
source_commit_timestamp: "2026-10-20T00:37:51-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.intent_cost module"
  - "src/learnloop/daily_plan/intent_cost.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.intent_cost`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.intent_cost` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The intent control's projected cost (spec §5.2): "about N min/day of reviews".

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/intent_cost.py](../../../../../../src/learnloop/daily_plan/intent_cost.py) |
| Source lines | 111 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1d5ba0272bb7d749483eea0f91c9eda2030bc4e9` |
| Commit timestamp | `2026-10-20T00:37:51-04:00` |

## Public API

- `class CostContext` ([source](../../../../../../src/learnloop/daily_plan/intent_cost.py), line 29) — What the cost reads, loaded once for every choice of one scope.
- `load_cost_context(vault: Any, repository: Any, *, clock: Clock | None=None) -> CostContext` ([source](../../../../../../src/learnloop/daily_plan/intent_cost.py), line 40)
- `projected_cost(vault: Any, context: CostContext, choice: str, after: Mapping[str, ItemIntent]) -> tuple[float | None, str]` ([source](../../../../../../src/learnloop/daily_plan/intent_cost.py), line 59)
- `cost_function(vault: Any, repository: Any, *, clock: Clock | None=None) -> CostFunction` ([source](../../../../../../src/learnloop/daily_plan/intent_cost.py), line 104) — The control's cost function for one read (its context loaded once).

### Explicit exports

`__all__` declares:

- `CostContext`
- `cost_function`
- `load_cost_context`
- `projected_cost`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `cost_function`; statically calls `cost_function`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/daily_plan/admission|learnloop.daily_plan.admission]] — imports `ReviewItem`, `projected_review_load`; calls `ReviewItem`, `projected_review_load`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `CostFunction`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CHOICE_DISPOSITION`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `effective_due`, `load_anchors`; calls `effective_due`, `load_anchors`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `ItemIntent`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f5_a_primed_retry_changes_neither_the_cost_preview_nor_the_review_load`
- [tests/test_intent_resolution.py](../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_the_consequence_line_names_what_it_replaces`
  - `test_the_projected_cost_follows_the_recall_target`

## Modification guidance

- Make changes here when the responsibility remains intent cost within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/intent_cost.py](../../../../../../src/learnloop/daily_plan/intent_cost.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
