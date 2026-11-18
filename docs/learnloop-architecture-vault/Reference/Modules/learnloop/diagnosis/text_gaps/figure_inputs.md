---
title: "learnloop.diagnosis.text_gaps.figure_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/figure_inputs.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/figure_inputs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.figure_inputs module"
  - "src/learnloop/diagnosis/text_gaps/figure_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.figure_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.figure_inputs` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: Figure source identifiers and input manifests.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/figure_inputs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py) |
| Source lines | 72 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `figure_prediction_id(source_id: str) -> tuple[str, bool]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py), line 24) — ``(prediction id, whether the source is its later explanation)``.
- `figure_input_manifest(row: Mapping[str, Any]) -> list[str] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py), line 33) — Every span a figure was built from and its author was sent, or None when the stored lists are unreadable (a caller fails closed): the selection, the region's block, the crop's block and ``input_span_ids`` (the paragraphs around it).
- `figure_input_keys(row: Mapping[str, Any]) -> dict[str, list[str]] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py), line 56) — Reader RW5d: the retrieved passages a figure was built from, in any source (``input_span_keys_json``), by extraction; None when unreadable (a caller fails closed).

### Module constants

- `FIGURE_PREDICTION_PREFIX` ([src/learnloop/diagnosis/text_gaps/figure_inputs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py), line 15)
- `FIGURE_EXPLANATION_SUFFIX` ([src/learnloop/diagnosis/text_gaps/figure_inputs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py), line 21)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `FIGURE_EXPLANATION_SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`; statically calls `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `FIGURE_PREDICTION_PREFIX`, `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`; statically calls `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]], [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f5_an_explained_source_with_no_explanation_reads_nothing`
  - `test_f5_an_explanation_after_the_reading_is_read_as_its_own_text`
- [tests/test_figures_fix_round2.py](../../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f1_a_later_explanation_of_a_held_out_figure_is_skipped_too`
  - `test_f5_off_save_on_sweep_reads_the_explanation_once`
- [tests/test_figures_fix_round3.py](../../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_f5_an_explanation_repeating_the_answer_is_still_read`
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text`
- [tests/test_ro2_history_protection.py](../../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_the_registry_restates_the_figure_source_grammar`

## Modification guidance

- Change figure inputs policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/figure_inputs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/figure_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
