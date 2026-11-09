---
title: "learnloop.experiments.contextual_embeddings.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/report.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.report module"
  - "src/learnloop/experiments/contextual_embeddings/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.report` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: The E0 report template (spec §11 "E0 report"): aggregates only.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/report.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py) |
| Source lines | 181 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `assert_aggregate(value: Any, path: str='') -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 29) — Refuse a report payload that carries a private field (fail closed).
- `render(results: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 59) — The Markdown report for ``results`` (see the module docstring).
- `failure_rows(blocked: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 179)

### Module constants

- `_PRIVATE_KEYS` ([src/learnloop/experiments/contextual_embeddings/report.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 25)

## Internal implementation anchors

- `_fmt(value: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 42)
- `_interval(result: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py), line 50)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `render`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/report|learnloop.experiments.contextual_embeddings.e1.report]] — imports `assert_aggregate`; statically calls `assert_aggregate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `assert_aggregate`; statically calls `assert_aggregate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `assert_aggregate`, `render`; statically calls `assert_aggregate`, `render`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/stop_rules|learnloop.experiments.contextual_embeddings.stop_rules]] — imports `incomplete_rules`, `summarize_decisions`; calls `incomplete_rules`, `summarize_decisions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/report|learnloop.experiments.contextual_embeddings.e1.report]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_metrics_stop_rules.py](../../../../../../../tests/test_e0_metrics_stop_rules.py) — direct import
  - `test_the_report_template_renders_incomplete_runs_and_refuses_private_fields`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_a_budget_stop_reports_incomplete_with_no_substitution`
  - `test_a_fake_paid_run_completes_every_arm_and_computes_the_stop_rules`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator`
  - `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/report.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
