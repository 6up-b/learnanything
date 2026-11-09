---
title: "learnloop.diagnosis.split.workbench_trace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/workbench_trace.py"
source_paths:
  - "src/learnloop/diagnosis/split/workbench_trace.py"
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
  - "learnloop.diagnosis.split.workbench_trace module"
  - "src/learnloop/diagnosis/split/workbench_trace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.workbench_trace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.workbench_trace` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Reader workbench RW2b: the step trace the diagnoser reads at Submit (spec_reader_workbench_v1 §5.4, G37, G38).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py) |
| Source lines | 120 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `trace_for_attempt(repository: Any, attempt: Mapping[str, Any], *, symbolic_enabled: bool=False) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 50) — The trace of a workbench attempt, or None (any other attempt, or a workbench attempt with no shown assist).

### Module constants

- `SUFFIX` ([src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 29)
- `WORKBENCH_SURFACES` ([src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 31)
- `NOTE` ([src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 32)
- `MAX_ASSISTS` ([src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 39)
- `STEP_CHARS` ([src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 40)

### Explicit exports

`__all__` declares:

- `NOTE`
- `SUFFIX`
- `WORKBENCH_SURFACES`
- `trace_for_attempt`

## Internal implementation anchors

- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `trace_for_attempt`; statically calls `trace_for_attempt`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `WORKBENCH_SURFACES`, `trace_for_attempt`; statically calls `trace_for_attempt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `verdict_records`; calls `verdict_records`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]], [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_workbench_trace.py](../../../../../../../tests/test_workbench_trace.py) — direct import
  - `test_a_workbench_attempt_carries_its_trace_under_the_suffix_and_never_a_map`
  - `test_every_other_attempt_renders_exactly_as_before`

## Modification guidance

- Change workbench trace policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/workbench_trace.py](../../../../../../../src/learnloop/diagnosis/split/workbench_trace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
