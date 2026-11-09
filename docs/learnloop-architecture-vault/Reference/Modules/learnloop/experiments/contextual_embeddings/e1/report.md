---
title: "learnloop.experiments.contextual_embeddings.e1.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/report.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.report module"
  - "src/learnloop/experiments/contextual_embeddings/e1/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.report` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: The E1 report (aggregates only; refuses private fields like E0's).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/report.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/report.py) |
| Source lines | 51 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `render(results: Mapping[str, Any]) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/report.py), line 24)

## Internal implementation anchors

- `_f(value: Any) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/report.py), line 10)
- `_pair(result: Mapping[str, Any] | None) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/report.py), line 16)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `render`; statically calls `render`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `assert_aggregate`; calls `assert_aggregate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_whole_pilot_with_fakes`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/report.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
