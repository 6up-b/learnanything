---
title: "learnloop.daily_plan.split"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/split.py"
source_paths:
  - "src/learnloop/daily_plan/split.py"
source_commit: "a74c1b555272fd8c63961b291624b981315c0b02"
source_commit_timestamp: "2026-10-12T16:23:01-04:00"
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
  - "learnloop.daily_plan.split module"
  - "src/learnloop/daily_plan/split.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.split`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.split` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The split (``spec_daily_loop_v1.md`` §6.2, P3): rule ``split_v1``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/split.py](../../../../../../src/learnloop/daily_plan/split.py) |
| Source lines | 315 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a74c1b555272fd8c63961b291624b981315c0b02` |
| Commit timestamp | `2026-10-12T16:23:01-04:00` |

## Public API

- `class LaneSplit` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 32)
  - `as_dict(self) -> dict[str, Any]` (line 39; public)
- `class Split` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 50)
  - `minutes(self, lane: str) -> float` (line 59; public)
  - `display_minutes(self) -> dict[str, int]` (line 63; public)
  - `line(self) -> str` (line 66; public)
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `display_lane_minutes(minutes: Mapping[str, float]) -> dict[str, int]` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 83) — Whole minutes per lane whose sum is the rounded total (largest remainder).
- `split_line(budget: float, display: Mapping[str, int]) -> str` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 106) — "25 min · maintain 13 · repair 4 · new 4 · push 4" (§6.2; zero lanes omitted).
- `split_v1(*, budget: float, requested_minutes: float, loads: Mapping[str, float], admitted_new_minutes: float, push_candidates: bool, repair_max_share: float, maintain_max_share: float, lanes_allowed: Sequence[str]=LANES, new_first: bool=False) -> Split` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 121) — Compute the split.
- `class LaneLedger` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 232) — The container's lane accounting at one block boundary (§6.8 rule 1).
  - `left(self, lane: str) -> float` (line 238; public)
  - `lefts(self, lanes: Sequence[str]=LANES) -> dict[str, float]` (line 241; public)
- `redistribute(lane_left: Mapping[str, float], *, has_candidate: Callable[[str, float], bool], new_room: float, lanes_allowed: Sequence[str]=LANES) -> tuple[dict[str, float], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 245) — §6.8 rule 1: released lane minutes flow on before every choice.

### Module constants

- `SPLIT_RULE` ([src/learnloop/daily_plan/split.py](../../../../../../src/learnloop/daily_plan/split.py), line 27)
- `_EPS` ([src/learnloop/daily_plan/split.py](../../../../../../src/learnloop/daily_plan/split.py), line 28)

### Explicit exports

`__all__` declares:

- `LaneLedger`
- `LaneSplit`
- `SPLIT_RULE`
- `Split`
- `display_lane_minutes`
- `redistribute`
- `split_line`
- `split_v1`

## Internal implementation anchors

- `_minutes_text(value: float) -> str` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 117)
- `_reason(lane: str, minutes: float, load: float, cap: float | None, m: float, repair_share: float, maintain_share: float) -> str` ([source](../../../../../../src/learnloop/daily_plan/split.py), line 201)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `redistribute`, `split_v1`; statically calls `redistribute`, `split_v1`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `display_lane_minutes`, `split_line`; statically calls `display_lane_minutes`, `split_line`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `FLOW_ORDER`, `LANES`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_plan_rpc.py](../../../../../../tests/test_daily_plan_rpc.py) — direct import
  - `test_the_plan_dto_is_the_one_source_of_every_number`
- [tests/test_daily_plan_split.py](../../../../../../tests/test_daily_plan_split.py) — direct import
  - `test_new_never_receives_more_than_its_admitted_room`
  - `test_redistribution_releases_to_the_first_lane_that_can_use_it`
  - `test_the_line_shows_whole_minutes_that_add_up`

## Modification guidance

- Make changes here when the responsibility remains split within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/split.py](../../../../../../src/learnloop/daily_plan/split.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
