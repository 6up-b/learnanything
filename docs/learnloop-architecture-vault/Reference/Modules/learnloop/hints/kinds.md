---
title: "learnloop.hints.kinds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/kinds.py"
source_paths:
  - "src/learnloop/hints/kinds.py"
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
  - "learnloop.hints.kinds module"
  - "src/learnloop/hints/kinds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.kinds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.kinds` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the kinds, levels, labels and replies (spec §4.2, §4.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py) |
| Source lines | 191 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Kind` ([source](../../../../../../src/learnloop/hints/kinds.py), line 30)
  - `label_at(self, level: int) -> str` (line 42; public)
- `option_id(kind: str, level: int) -> str` ([source](../../../../../../src/learnloop/hints/kinds.py), line 121) — A chooser option's name: ``<kind>@L<level>``.
- `parse_option(option: str) -> tuple[str, int]` ([source](../../../../../../src/learnloop/hints/kinds.py), line 127)
- `labels_for(kind: str, level: int, *, origin: str, has_work: bool=True, horizon_index: int | None=None, source_origin: str | None=None) -> dict[str, object]` ([source](../../../../../../src/learnloop/hints/kinds.py), line 134) — The labels a hint carries (§4.8, H5, G-H12): where it came from, its kind in plain words, a waypoint's horizon, and *worked help ◌* for levels 4-5 (which the panel shows before the help is taken, too).
- `worked_help_picks() -> list[dict[str, object]]` ([source](../../../../../../src/learnloop/hints/kinds.py), line 155) — The hint panel's two worked-help picks, each labelled before it is taken (§4.8, D17): a Hint press alone never serves them.

### Module constants

- `WORKED_LEVELS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 18)
- `PRESS_LEVELS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 20)
- `WORKED_HELP_MARK` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 22)
- `AI_WRITTEN` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 24)
- `FROM_THE_ITEM` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 25)
- `FROM_THE_BOOK` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 26)
- `KINDS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 46)
- `KIND_NAMES` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 70)
- `HORIZON_LEVELS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 74)
- `HORIZON_LABELS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 81)
- `REQUESTS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 86)
- `SHORTCUTS` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 88)
- `FALLBACK_ORDER` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 92)
- `GRAIN` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 101)
- `WITHHELD_MESSAGE` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 108)
- `NO_SEPARATING_QUESTION` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 110)
- `FIRST_MOVE_LABEL` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 115)
- `FORBIDDEN_WORDING` ([src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py), line 118)

### Explicit exports

`__all__` declares:

- `AI_WRITTEN`
- `FALLBACK_ORDER`
- `FIRST_MOVE_LABEL`
- `FORBIDDEN_WORDING`
- `FROM_THE_BOOK`
- `FROM_THE_ITEM`
- `GRAIN`
- `HORIZON_LABELS`
- `HORIZON_LEVELS`
- `KINDS`
- `KIND_NAMES`
- `Kind`
- `NO_SEPARATING_QUESTION`
- `PRESS_LEVELS`
- `REQUESTS`
- `SHORTCUTS`
- `WITHHELD_MESSAGE`
- `WORKED_HELP_MARK`
- `WORKED_LEVELS`
- `labels_for`
- `option_id`
- `parse_option`
- `worked_help_picks`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `FALLBACK_ORDER`, `HORIZON_LEVELS`, `parse_option`; statically calls `parse_option`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `KINDS`, `WORKED_LEVELS`
- [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]] — imports `GRAIN`, `KINDS`, `PRESS_LEVELS`, `WORKED_LEVELS`, `option_id`; statically calls `option_id`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `AI_WRITTEN`, `FROM_THE_ITEM`, `GRAIN`, `KINDS`, `NO_SEPARATING_QUESTION`, `REQUESTS`, `SHORTCUTS`, `WITHHELD_MESSAGE`, `WORKED_LEVELS`, `labels_for`, `worked_help_picks`; statically calls `labels_for`, `worked_help_picks`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `HORIZON_LABELS`, `KINDS`, `WORKED_HELP_MARK`, `WORKED_LEVELS`, `option_id`, `parse_option`; statically calls `option_id`, `parse_option`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `HORIZON_LEVELS`, `KINDS`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; statically calls `labels_for`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]], [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]], [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_help_assist_figures_migration.py](../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_the_check_values_are_the_kinds_the_code_writes`
- [tests/test_hint_blind.py](../../../../../../tests/test_hint_blind.py) — direct import
  - `test_the_blind_prompt_of_a_hinted_attempt_carries_no_hint_map_placement_or_state`
- [tests/test_hint_contracts.py](../../../../../../tests/test_hint_contracts.py) — direct import
  - `test_a_leaking_hint_is_reasked_once_then_withheld`
  - `test_an_authored_hint_that_gives_the_answer_away_is_withheld_and_not_served_again`
- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_no_positive_eig_downgrades_and_says_why`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_a_metered_writer_inside_the_cap_writes_and_its_receipt_is_counted`
  - `test_a_taken_level_is_drawn_conditional_on_that_level`
  - `test_authored_hints_the_client_revealed_are_not_served_again`
  - `test_every_kind_has_the_readers_plain_words_and_worked_help_is_marked`
  - `test_the_fallback_serves_authored_hints_in_order_then_the_next_step`
  - `test_the_wording_lint_rejects_judging_words_in_every_learner_facing_string`
- [tests/test_workbench_chooser.py](../../../../../../tests/test_workbench_chooser.py) — direct import
  - `test_every_served_hint_is_a_kind_of_its_rung`

## Modification guidance

- Make changes here when the responsibility remains kinds within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/kinds.py](../../../../../../src/learnloop/hints/kinds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
