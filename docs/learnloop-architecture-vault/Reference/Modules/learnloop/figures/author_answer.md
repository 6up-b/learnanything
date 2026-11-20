---
title: "learnloop.figures.author_answer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/author_answer.py"
source_paths:
  - "src/learnloop/figures/author_answer.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.author_answer module"
  - "src/learnloop/figures/author_answer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.author_answer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.author_answer` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: What one figure-author answer is, and what the author loop does with it next.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/author_answer.py](../../../../../../src/learnloop/figures/author_answer.py) |
| Source lines | 274 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Retry` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 30) — The attempt ends with record code ``rule``; the next prompt is told ``problems``.
- `class Unsupported` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 43) — The author says no medium offered can show it: what it would take, and why.
- `class Spec` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 51) — A spec that parsed; ``dropped`` names the malformed predictions left out of it.
- `class Sketch` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 59) — A sketch program that parsed, for the sealed engine; ``dropped`` as for :class:`Spec`.
- `class Rich` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 67) — A rich tier's brief, with its optional quick figure, or why that figure was dropped (the brief stands).
- `class Reading` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 76) — One answer, read: ``then`` is what the loop does next.
- `status_of(output: Any) -> str` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 89)
- `read_answer(output: Any, *, last: bool, tiers: Sequence[str] | None, sketch: bool, grounded: bool, advanced: bool) -> Reading` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 97) — ``output`` is the author's parsed answer (its output contract's fields); ``tiers`` the menu when it held a rich tier, else None; ``grounded`` False when no passage came from the learner's books.

### Explicit exports

`__all__` declares:

- `Reading`
- `Retry`
- `Rich`
- `Sketch`
- `Spec`
- `Unsupported`
- `read_answer`
- `status_of`

## Internal implementation anchors

- `_sentence(value: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 93)
- `_with_quick(brief: RICH.RichBrief, output: Any, *, sketch: bool, grounded: bool, advanced: bool) -> Rich` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 159) — The rich answer's optional quick figure, parsed: a spec first, else a sketch with the sketch tier on.
- `_free_text(output: Any, status: str) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 180) — The author's model-written free text the label rule reads (spec §9b.4): the tier reason, and what each figure it carries shows and assumes (a rich status's quick figure and brief included).
- `_without_label_text(output: Any) -> Any` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 198) — The author's answer with its label-like free text left out (spec §9b.4): a tier reason in code's words, a figure's or brief's label-like ``demonstrates`` emptied and label-like assumptions dropped.
- `_ungrounded(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 221) — RW5d (spec §8.3 step 3): with nothing from the learner's books, the figure is an illustration that quotes nothing, whatever the author wrote: code forces ``kind`` illustrative and drops every source claim and quote (there is no passage to verify them against).
- `_ungrounded_sketch(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/author_answer.py), line 247) — RW5d P2 + §8.3 step 3: a sketch built with nothing from the learner's books quotes nothing, whatever the author wrote.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `module`; statically calls `read_answer`, `status_of`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/labels|learnloop.figures.labels]] — imports `module`; calls `json_fields`, `label_like`, `label_problems`, `strip_json`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`; calls `sketch_problem`, `spec_problem`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `parse_brief`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; calls `parse_author_sketch`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `parse_author_spec`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_author_answer.py](../../../../../../tests/test_figure_author_answer.py) — direct import
  - `test_a_bad_prediction_is_dropped_and_the_spec_kept`
  - `test_a_brief_that_does_not_parse_is_retried_with_its_problems`
  - `test_a_label_like_tier_reason_is_retried_then_kept_out_of_the_verdict`
  - `test_a_quick_figure_that_does_not_parse_is_dropped_and_the_brief_stands`
  - `test_a_rich_answer_carries_its_brief_and_its_quick_figure`
  - `test_a_rich_answer_still_label_like_on_the_last_attempt_keeps_its_brief_without_that_text`
  - `test_a_sketch_that_does_not_parse_is_retried_and_ends_an_earlier_figure`
  - `test_a_sketch_that_parses_goes_to_the_engine_with_its_tier_verdict`
  - `test_a_spec_that_does_not_parse_is_retried_with_the_parsers_problems`
  - `test_a_spec_that_parses_goes_on_to_its_checks_with_no_tier_verdict`
  - `test_a_status_no_menu_offers_has_its_rich_text_left_unread`
  - `test_a_status_off_the_menu_is_retried_uncounted_with_the_media_offered`
  - `test_a_v2_spec_is_judged_spec_and_a_status_outside_the_three_is_noted_and_read_as_a_spec`
  - `test_a_v2_unsupported_is_judged_with_its_reason`
  - `test_a_v3_unsupported_and_a_v3_spec_are_judged_on_the_menu`
  - `test_an_empty_tier_reason_is_retried_uncounted`
  - `test_label_like_text_is_retried_in_codes_words_then_stripped_on_the_last_attempt`
  - `test_unsupported_names_what_it_would_take_and_why`
  - `test_with_the_panels_off_an_advanced_panel_is_a_parse_problem`
  - `test_with_the_sketch_tier_off_a_sketch_status_is_read_as_a_spec`
- [tests/test_figure_author_predictions.py](../../../../../../tests/test_figure_author_predictions.py) — direct import
  - `test_a_real_problem_still_gets_the_second_attempt_without_the_predictions_noise`
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f1_a_spec_saying_it_matches_the_book_gets_the_repair_call`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_sketch_built_with_nothing_from_the_books_quotes_nothing`

## Modification guidance

- Make changes here when the responsibility remains author answer within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/author_answer.py](../../../../../../src/learnloop/figures/author_answer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
