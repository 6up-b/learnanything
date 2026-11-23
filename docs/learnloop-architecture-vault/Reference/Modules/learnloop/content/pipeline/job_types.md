---
title: "learnloop.content.pipeline.job_types"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/job_types.py"
source_paths:
  - "src/learnloop/content/pipeline/job_types.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.job_types module"
  - "src/learnloop/content/pipeline/job_types.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.job_types`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.job_types` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: What each ingest job type is: one row per type.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py) |
| Source lines | 121 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class JobType` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 40)
- `job_type(name: str) -> JobType | None` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 99) — The row for ``name``, or None for a type the table does not hold (a handler a test injects).
- `resolve_handler(reference: str) -> Handler` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 105) — The handler a row's ``module:function`` names, importing its module.
- `default_handlers() -> dict[str, Handler]` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 112)
- `applying_job_types() -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 116)
- `parallel_job_types() -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 120)

### Module constants

- `_IMPORT` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 32)
- `_SYNTHESIS` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 33)
- `_AUTHORING` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 34)
- `_FIGURES` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 35)
- `_RETRIEVAL` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 36)
- `JOB_TYPES` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 53)
- `_BY_NAME` ([src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py), line 96)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `applying_job_types`, `parallel_job_types`; statically calls `applying_job_types`, `parallel_job_types`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `applying_job_types`; statically calls `applying_job_types`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `applying_job_types`; statically calls `applying_job_types`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `Handler`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `importlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_coverage_on_extract.py](../../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_the_handler_is_registered_and_known`
- [tests/test_job_types.py](../../../../../../../tests/test_job_types.py) — direct import
  - `test_a_rows_routes_are_the_routes_its_default_clients_resolve`
  - `test_every_client_route_is_a_routing_task`
  - `test_every_type_has_exactly_one_row_and_every_row_a_handler`
  - `test_the_derived_lists_follow_the_flags`
  - `test_the_legacy_lane_resolves_its_rows_route`
  - `test_the_runner_runs_exactly_the_table`

## Modification guidance

- Change job types policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/job_types.py](../../../../../../../src/learnloop/content/pipeline/job_types.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
