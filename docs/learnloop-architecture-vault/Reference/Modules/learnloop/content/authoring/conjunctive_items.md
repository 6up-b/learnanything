---
title: "learnloop.content.authoring.conjunctive_items"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/conjunctive_items.py"
source_paths:
  - "src/learnloop/content/authoring/conjunctive_items.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.conjunctive_items module"
  - "src/learnloop/content/authoring/conjunctive_items.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.conjunctive_items`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.conjunctive_items` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Conjunctive instruments — item shape, the two A1 guards, and the posterior rule that decides which shape to serve.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/conjunctive_items.py](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py) |
| Source lines | 321 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ItemShape` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 86) — How many independent cells one item's rubric actually observes.
  - `is_conjunctive(self) -> bool` (line 111; public) — Whether this item was AUTHORED as a conjunction.
  - `conjunctive_strength(self) -> float` (line 127; public) — 0.0 for a single-cell or unauthored item, rising to 1.0 at the ceiling.
  - `as_dict(self) -> dict[str, Any]` (line 138; public)
- `classify_item_shape(item, rubric, *, canonical_facet_id=None) -> ItemShape` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 150) — Compile ``item``'s rubric into an :class:`ItemShape`.
- `class SupportingPartition` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 188) — Which of a criterion's supporting targets earned credit, and which did not.
  - `unexercised_cells(self) -> tuple[tuple[str, str], ...]` (line 195; public)
- `supporting_unexercised(target, exercised_facets, *, resolve=None) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 199) — Whether ``target`` is a supporting claim the trace did not support.
- `partition_supporting_targets(targets, exercised_facets, *, canonical_facet_id=None) -> SupportingPartition` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 214) — Split supporting targets by whether the trace showed the facet exercised.
- `cap_embedded_credit(direct_credit: float, embedded_credit: float, *, max_embedded_share: float) -> float` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 255) — Total certification credit for a cell, with embedded credit capped.
- `conjunctive_fit(shape: ItemShape, predicted_correctness: float, *, localizing: bool) -> float` ([source](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 294) — Selection preference for ``shape`` given the current posterior.

### Module constants

- `UNEXERCISED_SUPPORTING_TARGET` ([src/learnloop/content/authoring/conjunctive_items.py](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 71)
- `MIN_CONJUNCTIVE_CELLS` ([src/learnloop/content/authoring/conjunctive_items.py](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 76)
- `CONJUNCTIVE_STRENGTH_CEILING` ([src/learnloop/content/authoring/conjunctive_items.py](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py), line 82)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `UNEXERCISED_SUPPORTING_TARGET`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `cap_embedded_credit`, `supporting_unexercised`; statically calls `cap_embedded_credit`, `supporting_unexercised`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `ItemShape`, `classify_item_shape`, `conjunctive_fit`; statically calls `classify_item_shape`, `conjunctive_fit`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `cap_embedded_credit`, `supporting_unexercised`; statically calls `cap_embedded_credit`, `supporting_unexercised`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`; calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CriterionTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]], [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]], [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]], [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_conjunctive_instruments.py](../../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_cap_embedded_credit_boundaries`
  - `test_classify_item_shape_reads_the_authored_dependency_chain`
  - `test_conjunctive_fit_prefers_the_capstone_only_when_a_pass_is_likely`
  - `test_conjunctive_strength_saturates_at_the_ceiling`
  - `test_partition_supporting_targets_splits_on_trace_evidence`
  - `test_single_cell_item_is_not_conjunctive_and_scores_exactly_zero`

## Modification guidance

- Change conjunctive items policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/conjunctive_items.py](../../../../../../../src/learnloop/content/authoring/conjunctive_items.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
