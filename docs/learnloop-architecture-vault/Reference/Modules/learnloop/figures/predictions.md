---
title: "learnloop.figures.predictions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/predictions.py"
source_paths:
  - "src/learnloop/figures/predictions.py"
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
  - "learnloop.figures.predictions module"
  - "src/learnloop/figures/predictions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.predictions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.predictions` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: A figure's predictions: the learner's answer, what the figure shows before and after, and whether it matched.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/predictions.py](../../../../../../src/learnloop/figures/predictions.py) |
| Source lines | 154 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_prediction(vault: Any, repository: Repository, figure_id: str, index: int, answer: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None, assist_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/predictions.py), line 34) — The learner's prediction, its observed before/after readout and whether it matched (code decides).
- `record_explanation(vault: Any, repository: Repository, prediction_id: str, text: str, *, clock: Clock | None=None, on_queued: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/predictions.py), line 106) — "What changed, and why?" (optional, once).

### Module constants

- `EXPLANATION_CHARS` ([src/learnloop/figures/predictions.py](../../../../../../src/learnloop/figures/predictions.py), line 29)
- `ANSWER_CHARS` ([src/learnloop/figures/predictions.py](../../../../../../src/learnloop/figures/predictions.py), line 30)
- `PREDICTION_PREFIX` ([src/learnloop/figures/predictions.py](../../../../../../src/learnloop/figures/predictions.py), line 31)

### Explicit exports

`__all__` declares:

- `ANSWER_CHARS`
- `EXPLANATION_CHARS`
- `PREDICTION_PREFIX`
- `record_explanation`
- `record_prediction`

## Internal implementation anchors

- `_sketch_outcome(compiled: K.CompiledSketch, index: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/predictions.py), line 92) — A sketch's prediction, decided by code in the sealed engine (spec §9.3).
- `_queue_formative(vault: Any, repository: Repository, prediction_id: str, *, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/figures/predictions.py), line 137)
- `_queued(job_id: str | None, on_queued: Callable[[str], None] | None) -> None` ([source](../../../../../../src/learnloop/figures/predictions.py), line 143)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `record_explanation`, `record_prediction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `has_tables`, `insert_prediction`, `prediction`, `prediction_for`, `set_explanation`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_figure_explanation`, `enqueue_figure_prediction`; calls `enqueue_figure_explanation`, `enqueue_figure_prediction`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `figures_enabled`; calls `figures_enabled`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `shown_figure`; calls `shown_figure`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `FigureRefused`, `prediction_home`; calls `FigureRefused`, `prediction_home`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `SketchEngine`, `SketchRunError`; calls `SketchEngine`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `module`; calls `prediction_outcome`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `prediction_outcome`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `_code_owned_labels`, `_coded_answer`, `_prediction_view`; calls `_code_owned_labels`, `_coded_answer`, `_prediction_view`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit`

## Modification guidance

- Make changes here when the responsibility remains predictions within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/predictions.py](../../../../../../src/learnloop/figures/predictions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
