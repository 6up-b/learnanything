---
title: "learnloop.learner.mastery_step_attribution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/mastery_step_attribution.py"
source_paths:
  - "src/learnloop/learner/mastery_step_attribution.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.mastery_step_attribution module"
  - "src/learnloop/learner/mastery_step_attribution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.mastery_step_attribution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.mastery_step_attribution` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Why the mastery posterior moved as far as it did (read-time attribution).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/mastery_step_attribution.py](../../../../../../src/learnloop/learner/mastery_step_attribution.py) |
| Source lines | 216 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MasteryStepFactor` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 39) — One multiplicative term in the observation weight.
- `class MasteryStepExplanation` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 49)
- `explain_mastery_step(debug_payload: Mapping[str, Any] | None, *, observed_correctness: float | None=None) -> MasteryStepExplanation | None` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 107) — Attribute the observation weight to its factors, or ``None`` if untraceable.

### Module constants

- `WEIGHT_FLOOR` ([src/learnloop/learner/mastery_step_attribution.py](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 27)
- `_PRODUCT_TOLERANCE` ([src/learnloop/learner/mastery_step_attribution.py](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 31)
- `_NEUTRAL_EPSILON` ([src/learnloop/learner/mastery_step_attribution.py](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 35)

## Internal implementation anchors

- `_number(source: Mapping[str, Any] | None, key: str) -> float | None` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 63)
- `_mapping(source: Mapping[str, Any] | None, key: str) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 72)
- `_coverage_detail(trace: Mapping[str, Any] | None, effective_coverage: float | None) -> str` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 79) — ``3 of 6 facets`` -- the LO surface this item can actually reach.
- `_familiarity_detail(trace: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/learner/mastery_step_attribution.py), line 92) — Name the surface that made this attempt less novel.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `explain_mastery_step`; statically calls `explain_mastery_step`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mastery_step_attribution.py](../../../../../../tests/test_mastery_step_attribution.py) — direct import
  - `test_a_payload_missing_traces_reports_a_non_reconciling_chain`
  - `test_amplifying_factor_never_becomes_the_dominant_one`
  - `test_coverage_detail_counts_touched_against_required_facets`
  - `test_dominant_factor_is_the_largest_penalty`
  - `test_factor_product_reproduces_the_stored_observation_weight`
  - `test_neutral_factors_are_dropped_but_penalties_are_kept`
  - `test_observed_correctness_comes_from_the_caller_not_the_payload`
  - `test_untraceable_attempts_return_none_rather_than_a_fabricated_chain`
  - `test_weight_floor_is_flagged_so_the_ui_can_say_the_step_stopped_tracking`

## Modification guidance

- Change mastery step attribution policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/mastery_step_attribution.py](../../../../../../src/learnloop/learner/mastery_step_attribution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
