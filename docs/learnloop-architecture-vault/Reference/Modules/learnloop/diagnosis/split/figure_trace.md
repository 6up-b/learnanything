---
title: "learnloop.diagnosis.split.figure_trace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/figure_trace.py"
source_paths:
  - "src/learnloop/diagnosis/split/figure_trace.py"
source_commit: "b49f7df5c8791997a7a2b59e46c9ba5edc95b147"
source_commit_timestamp: "2026-11-01T21:09:47-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.figure_trace module"
  - "src/learnloop/diagnosis/split/figure_trace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.figure_trace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.figure_trace` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Reader RW5d P3: the figure trace the diagnoser reads at Submit (spec_reader_show_me_figures_v1 §11.2, §11.4b).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py) |
| Source lines | 145 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b49f7df5c8791997a7a2b59e46c9ba5edc95b147` |
| Commit timestamp | `2026-11-01T21:09:47-05:00` |

## Public API

- `figure_trace_for_attempt(vault: Any, repository: Any, attempt: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 60) — The figures an attempt used, or None (no figure row, the switch off, or every figure held out now).

### Module constants

- `SUFFIX` ([src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 30)
- `NOTE` ([src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 31)
- `MAX_FIGURES` ([src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 37)
- `TEXT_CHARS` ([src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 38)

### Explicit exports

`__all__` declares:

- `MAX_FIGURES`
- `NOTE`
- `SUFFIX`
- `TEXT_CHARS`
- `figure_trace_for_attempt`

## Internal implementation anchors

- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 41)
- `_demonstrates(spec_json: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 48)
- `_by(stamp: Any, cutoff: str | None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py), line 53) — Whether a row written at ``stamp`` is at or before the attempt's Submit (no cutoff on record: every linked row).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `figure_trace_for_attempt`; statically calls `figure_trace_for_attempt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `figure_prediction_withheld`; calls `figure_prediction_withheld`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `help_kind_enabled`; calls `help_kind_enabled`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help.py](../../../../../../../tests/test_figures_help.py) — direct import
  - `test_the_diagnoser_reads_the_figure_trace_under_its_suffix_and_never_the_program`
- [tests/test_figures_help_codex_review.py](../../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f7_predictions_made_before_the_attempt_are_not_its_trace`
  - `test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit`

## Modification guidance

- Change figure trace policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/figure_trace.py](../../../../../../../src/learnloop/diagnosis/split/figure_trace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
