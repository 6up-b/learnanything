---
title: "learnloop.matching.union"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/matching/union.py"
source_paths:
  - "src/learnloop/matching/union.py"
source_commit: "c2e99eaf2276f6014c94376587e03ac8e6777ab8"
source_commit_timestamp: "2026-10-12T15:48:06-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.matching.union module"
  - "src/learnloop/matching/union.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-matching"
---

# `learnloop.matching.union`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.matching.union` exists within [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] to own the behavior summarized by its module contract: Deterministic union with the no-chaining refusal (Slice 2 §3.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/matching/union.py](../../../../../../src/learnloop/matching/union.py) |
| Source lines | 195 |
| Owning package | [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c2e99eaf2276f6014c94376587e03ac8e6777ab8` |
| Commit timestamp | `2026-10-12T15:48:06-04:00` |

## Public API

- `class UnionEdge` ([source](../../../../../../src/learnloop/matching/union.py), line 32)
  - `pair(self) -> frozenset[str]` (line 46; public)
  - `order(self) -> tuple[str, str]` (line 49; public)
- `class Refusal` ([source](../../../../../../src/learnloop/matching/union.py), line 54)
- `class UnionResult` ([source](../../../../../../src/learnloop/matching/union.py), line 64)
  - `components(self) -> dict[str, list[str]]` (line 75; public)
- `effective_verdicts(edges: Iterable[UnionEdge]) -> tuple[dict[frozenset[str], UnionEdge], list[UnionEdge]]` ([source](../../../../../../src/learnloop/matching/union.py), line 103) — Highest authority wins; within it ``different`` beats ``same``; ``unsure`` never counts.
- `tier_conflicts(edges: Iterable[UnionEdge]) -> list[Refusal]` ([source](../../../../../../src/learnloop/matching/union.py), line 119) — Pairs whose top tier holds both verdicts: the latest ``same`` refused by the latest ``different``.
- `union_with_refusals(nodes: Iterable[str], edges: Iterable[UnionEdge], *, order: Mapping[str, Hashable] | None=None) -> UnionResult` ([source](../../../../../../src/learnloop/matching/union.py), line 132)

### Explicit exports

`__all__` declares:

- `Refusal`
- `UnionEdge`
- `UnionResult`
- `effective_verdicts`
- `tier_conflicts`
- `union_with_refusals`

## Internal implementation anchors

- `_top_tiers(edges: Iterable[UnionEdge]) -> tuple[dict[frozenset[str], list[UnionEdge]], list[UnionEdge]]` ([source](../../../../../../src/learnloop/matching/union.py), line 82) — Per node pair, its highest-authority non-``unsure`` edges (oldest first); plus ``different`` edges between a node and itself.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `module`; statically calls `UnionEdge`, `union_with_refusals`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `UnionEdge`, `effective_verdicts`, `union_with_refusals`; statically calls `UnionEdge`, `effective_verdicts`, `union_with_refusals`
- [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] — imports `Refusal`, `UnionEdge`, `UnionResult`, `union_with_refusals`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `UnionEdge`, `union_with_refusals`; statically calls `UnionEdge`, `union_with_refusals`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]], [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_decider_partition_is_matchings_no_chaining_union`
- [tests/test_recurrence_groups.py](../../../../../../tests/test_recurrence_groups.py) — direct import
  - `test_a_higher_tier_same_still_replaces_a_lower_different`
  - `test_a_lower_authority_different_does_not_block_a_higher_same`
  - `test_an_equal_authority_conflict_on_one_pair_refuses_the_union_and_reports_it`
  - `test_highest_authority_wins_a_tie_in_the_tier_is_different_and_unsure_never_counts`
  - `test_no_chaining_a_b_b_c_with_a_not_c_never_makes_one_group`
  - `test_the_oldest_class_roots_its_group_and_each_member_records_its_join`

## Modification guidance

- Make changes here when the responsibility remains union within learnloop.matching; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/matching/union.py](../../../../../../src/learnloop/matching/union.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
