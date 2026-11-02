---
title: "learnloop.hints.contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/contracts.py"
source_paths:
  - "src/learnloop/hints/contracts.py"
source_commit: "62897a63d196c1aeb828fb9c30b3e2306943789a"
source_commit_timestamp: "2026-10-18T08:20:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.contracts module"
  - "src/learnloop/hints/contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.contracts` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the writer's contracts and leak control, checked in code (spec §4.2, §4.6, G-H5, G-H6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/contracts.py](../../../../../../src/learnloop/hints/contracts.py) |
| Source lines | 545 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `62897a63d196c1aeb828fb9c30b3e2306943789a` |
| Commit timestamp | `2026-10-18T08:20:05-04:00` |

## Public API

- `class Check` ([source](../../../../../../src/learnloop/hints/contracts.py), line 50) — The checks' result: rule failures (re-asked, then downgraded) and leak flags (re-asked, then withheld).
  - `ok(self) -> bool` (line 58; public)
  - `fail(self, code: str) -> None` (line 61; public)
- `class Target` ([source](../../../../../../src/learnloop/hints/contracts.py), line 67) — What the chosen option asks the writer for (and the checks hold it to).
- `in_work(quote: str, work: str) -> bool` ([source](../../../../../../src/learnloop/hints/contracts.py), line 98) — A quote is the learner's when it appears in the draft (spacing ignored).
- `stands_before(stands: str, questionable: str, work: str) -> bool` ([source](../../../../../../src/learnloop/hints/contracts.py), line 105) — Whether the standing quote ends before the first questionable point in the draft (spacing ignored).
- `nodes_by_id(current: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 120)
- `routes_by_id(current: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 124)
- `reference_route_id(current: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 128)
- `goal_node_id(current: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 135)
- `route_distance(current: Mapping[str, Any] | None, route_id: str, start: str, end: str) -> int | None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 140) — Edges from ``start`` to ``end`` along the route, or None when either is not on it or ``end`` comes first.
- `horizon_distance(current: Mapping[str, Any] | None, route_id: str, start: str, horizon_index: int) -> int | None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 152) — The edges the chosen horizon asks for from ``start`` on the route: index 0 one, index 1 two, index 2 the end of the current subgoal (the next node with a checkpoint, else two), index 3 the goal.
- `later_expressions(current: Mapping[str, Any] | None, route_id: str | None, start: str | None, work: str, public_text: str='') -> set[str]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 178) — Expressions of the states after the placement on the route (and every leak node's), minus those the learner has written: what a hint that names no step content must not carry.
- `leak_node_expressions(current: Mapping[str, Any] | None, public_text: str='') -> set[str]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 199) — The expressions of every leak node's state (the goal's always), less what the question itself states: a given is never a leak (H1's rule for labels, deviation 5 there).
- `leak_flags(texts: Sequence[str], *, item: Any, current: Mapping[str, Any] | None, level: int) -> list[str]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 222) — Why any of ``texts`` would give the answer away (empty: it does not).
- `check_output(output: Any, *, target: Target, state: Any, item: Any) -> Check` ([source](../../../../../../src/learnloop/hints/contracts.py), line 256) — Every shared rule and the kind's contract for one writer answer (the discriminating kind's question is checked by the service after its EIG ranking; its fallback hint is checked as its own kind).
- `at_givens(current: Mapping[str, Any] | None, reached: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/contracts.py), line 386) — Whether a placement is at the givens: no node reached, or the reference route's first node.
- `toward_waypoint(current: Mapping[str, Any] | None, route_id: str, start: str | None, aimed: str, waypoint: str) -> bool` ([source](../../../../../../src/learnloop/hints/contracts.py), line 396) — Whether a hint aiming at ``aimed`` from ``start`` aims at the retained waypoint: ``aimed`` is the waypoint, or lies on the route after ``start`` and no later than the waypoint; once the work has reached (or passed) the waypoint, any target does.

### Module constants

- `_TRIVIAL_NUMBERS` ([src/learnloop/hints/contracts.py](../../../../../../src/learnloop/hints/contracts.py), line 426)

### Explicit exports

`__all__` declares:

- `Check`
- `Target`
- `at_givens`
- `check_output`
- `goal_node_id`
- `horizon_distance`
- `in_work`
- `leak_flags`
- `reference_route_id`
- `route_distance`
- `stands_before`
- `toward_waypoint`

## Internal implementation anchors

- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/hints/contracts.py), line 94)
- `_squash_math(text: str) -> str` ([source](../../../../../../src/learnloop/hints/contracts.py), line 214)
- `_earlier_at_placement(state: Any) -> list[Any]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 249) — Shown hints of this attempt on the same work (the same placement on the practice screen).
- `_first_node(current: Mapping[str, Any], route_id: str) -> str | None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 416)
- `_route_done(current: Mapping[str, Any], route_id: str, start: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/contracts.py), line 421)
- `_kind_contract(check: Check, output: Any, *, target: Target, state: Any, item: Any, quotes: Sequence[str]) -> None` ([source](../../../../../../src/learnloop/hints/contracts.py), line 429)
- `_techniques_between(current: Mapping[str, Any], route_id: str, start: str, end: str) -> list[str]` ([source](../../../../../../src/learnloop/hints/contracts.py), line 521)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `Check`, `Target`, `at_givens`, `check_output`, `leak_flags`, `reference_route_id`, `route_distance`; statically calls `Check`, `Target`, `at_givens`, `check_output`, `leak_flags`, `reference_route_id`, `route_distance`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `Check`, `Target`, `in_work`, `leak_flags`, `nodes_by_id`, `routes_by_id`; statically calls `in_work`, `leak_flags`, `nodes_by_id`, `routes_by_id`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `Target`, `reference_route_id`; statically calls `reference_route_id`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `leak_flags`; statically calls `leak_flags`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `KINDS`, `WORKED_LEVELS`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `exact_key`, `gives_away`, `label_leaks`, `leak_expressions`, `number_tokens`; calls `exact_key`, `gives_away`, `label_leaks`, `leak_expressions`, `number_tokens`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `answer_leaks_expected`; calls `answer_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]], [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_contracts.py](../../../../../../tests/test_hint_contracts.py) — direct import
  - `test_a_waypoint_that_misses_the_chosen_horizon_is_caught`
  - `test_no_waypoint_or_label_carries_a_leak_nodes_state`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f2_a_smaller_step_toward_a_far_waypoint_targets_the_adjacent_node_on_the_way`
  - `test_f4_an_alternative_learner_route_is_not_swapped_for_another_alternative`
  - `test_f8_a_book_origin_on_an_unverified_passage_is_refused`
  - `test_f8_the_writer_is_told_its_passages_are_unverified`
- [tests/test_hint_h2a_review_round4.py](../../../../../../tests/test_hint_h2a_review_round4.py) — direct import
  - `test_r4_the_reference_route_rule_for_every_kind_and_no_map_unchanged`
- [tests/test_hint_replies.py](../../../../../../tests/test_hint_replies.py) — direct import
  - `test_learner_route_keeps_the_learners_route_and_never_targets_the_reference`

## Modification guidance

- Make changes here when the responsibility remains contracts within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/contracts.py](../../../../../../src/learnloop/hints/contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
