---
title: "learnloop.router_objective.preference_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/preference_report.py"
source_paths:
  - "src/learnloop/router_objective/preference_report.py"
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
  - "learnloop.router_objective.preference_report module"
  - "src/learnloop/router_objective/preference_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.preference_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.preference_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: ``learnloop data-capture report``'s section on what the learner said would help (instruct hand-off IH4, spec_instruct_handoff_v1 §7 items 4-5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py) |
| Source lines | 229 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `section(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 128) — The section (module docstring), read-only.
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 209)

### Module constants

- `VERSION` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 31)
- `SELF_SELECTED` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 32)
- `COMPARISON_LABEL` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 33)
- `NOT_USING` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 35)
- `OFFER_PREFIX` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 36)
- `WHAT_MOVES_W_PREF` ([src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py), line 37)

### Explicit exports

`__all__` declares:

- `COMPARISON_LABEL`
- `NOT_USING`
- `SELF_SELECTED`
- `VERSION`
- `WHAT_MOVES_W_PREF`
- `lines`
- `section`

## Internal implementation anchors

- `_later_cold(connection: Any, lo: str | None, after: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 44)
- `_block(connection: Any, decision_id: str | None) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 54)
- `_topic_of(connection: Any, ref: Any, decision_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 62) — The topic a choice or a draw names: a lesson's from its ref, else the decision's, else its block's first.
- `_lesson_opened(connection: Any, lo: str | None, after: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 78)
- `_followed(connection: Any, row: Mapping[str, Any], lo: str | None) -> bool | None` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 86) — Whether what the choice asked for happened; None where nothing could say (no decision logged, no block placed).
- `_mean(values: list[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 106)
- `_standing(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/preference_report.py), line 110) — ``w_pref`` as the latest ``plan_block`` trace froze it, and how many decisions carry the sensor.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `lines`, `section`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; calls `learner_preference_rows`, `preferences_present`
- [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] — imports `DELAYED_LABEL`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `KINDS`, `STOP`, `kind_of`; calls `kind_of`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_kinds_are_the_plans_own_names`
  - `test_the_report_section_says_each_thing_and_labels_it_self_selected`

## Modification guidance

- Make changes here when the responsibility remains preference report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/preference_report.py](../../../../../../src/learnloop/router_objective/preference_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
