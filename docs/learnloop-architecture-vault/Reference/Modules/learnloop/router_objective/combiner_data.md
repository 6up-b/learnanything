---
title: "learnloop.router_objective.combiner_data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/combiner_data.py"
source_paths:
  - "src/learnloop/router_objective/combiner_data.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.combiner_data module"
  - "src/learnloop/router_objective/combiner_data.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.combiner_data`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.combiner_data` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The follow-up batch, item 2 (RO4's item 6): the memory combiner's outcomes from the traces.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py) |
| Source lines | 186 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `groups(connection: Any, *, now: str) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../../src/learnloop/router_objective/combiner_data.py), line 96) — One resolvable group per (decision, untouched topic) as of ``now``, and the decisions joined nothing, by reason.
- `rows(connection: Any, resolved: Sequence[Mapping[str, Any]], *, now: str, known_at: Callable[[Mapping[str, Any]], Any], retrievability: Callable[[float, float], float], exclude: Collection[str]=()) -> tuple[list[tuple[float, float | None, int]], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/combiner_data.py), line 131) — The combiner's ``(η, R or None, y)`` rows from the resolver's rows (``resolved``), as of ``now``; ``exclude``: attempt ids already counted (a randomized check's).

### Module constants

- `JOIN_VERSION` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 42)
- `FORECASTER` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 43)
- `_PER_PROTOCOL` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 44)
- `_FLAT_CURVE` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 46)
- `_PARSED` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 57)
- `_PARSED_LOCK` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 58)
- `_PARSED_LIMIT` ([src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py), line 59)

### Explicit exports

`__all__` declares:

- `FORECASTER`
- `JOIN_VERSION`
- `groups`
- `rows`

## Internal implementation anchors

- `_days(later: datetime, earlier: datetime) -> float` ([source](../../../../../../src/learnloop/router_objective/combiner_data.py), line 49)
- `_untouched(chosen: str, trace_json: str) -> tuple[tuple[str, dict[str, Any]], ...]` ([source](../../../../../../src/learnloop/router_objective/combiner_data.py), line 62) — The trace's topics with sensors frozen, except the drawn option's own, in id order with their sensor values (``eta``, ``stability``, ``elapsed``, ``practiced``): a pure function of the drawn option and the trace's text, held per content digest (router speed, item 2: the join par…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `groups`, `rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rofu_learning.py](../../../../../../tests/test_rofu_learning.py) — direct import
  - `test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it`
  - `test_the_join_rows_count_one_outcome_once_per_protocol_and_only_when_known`
  - `test_the_join_takes_the_drawn_blocks_untouched_topics_as_of_the_moment`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_a_rewritten_trace_is_parsed_again`
  - `test_the_groups_are_the_landing_codes`
  - `test_the_parsed_traces_are_bounded`

## Modification guidance

- Make changes here when the responsibility remains combiner data within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/combiner_data.py](../../../../../../src/learnloop/router_objective/combiner_data.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
