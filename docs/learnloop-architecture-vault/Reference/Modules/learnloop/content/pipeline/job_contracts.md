---
title: "learnloop.content.pipeline.job_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/job_contracts.py"
source_paths:
  - "src/learnloop/content/pipeline/job_contracts.py"
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
  - "learnloop.content.pipeline.job_contracts module"
  - "src/learnloop/content/pipeline/job_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.job_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.job_contracts` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: The contracts a job handler and the code it calls share with the ingest runner.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/job_contracts.py](../../../../../../../src/learnloop/content/pipeline/job_contracts.py) |
| Source lines | 71 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class IngestRunnerError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/job_contracts.py), line 17) — A typed, user-actionable job failure persisted for the Activity UI.
  - `__init__(self, message: str, *, code: str='invalid_job', details: Mapping[str, Any] | None=None, retryable: bool=False) -> None` (line 20; internal)
- `class JobCancelled(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/job_contracts.py), line 34) — Raised from ``report()`` when a cancellation was requested mid-stage.
- `class WaitingForInput(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/job_contracts.py), line 38) — A handler pauses the job pending user input (unit choice, consent, budget).
  - `__init__(self, payload: Mapping[str, Any], *, message: str='Waiting for input') -> None` (line 44; internal)
- `class FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/job_contracts.py), line 51)
- `class JobSpec` ([source](../../../../../../../src/learnloop/content/pipeline/job_contracts.py), line 65) — One job in an enqueued batch.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/jobs|learnloop.content.authoring.jobs]] — imports `IngestRunnerError`, `JobCancelled`; statically calls `IngestRunnerError`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `JobCancelled`, `JobSpec`
- [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]] — imports `FetchedBytes`, `IngestRunnerError`; statically calls `FetchedBytes`, `IngestRunnerError`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `FetchedBytes`, `IngestRunnerError`, `JobCancelled`, `JobSpec`, `WaitingForInput`; statically calls `IngestRunnerError`, `JobCancelled`
- [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]] — imports `IngestRunnerError`, `JobCancelled`; statically calls `IngestRunnerError`, `JobCancelled`
- [[Reference/Modules/learnloop/figures/jobs|learnloop.figures.jobs]] — imports `IngestRunnerError`, `JobCancelled`; statically calls `IngestRunnerError`
- [[Reference/Modules/learnloop/source_retrieval/jobs|learnloop.source_retrieval.jobs]] — imports `IngestRunnerError`, `JobCancelled`, `JobSpec`; statically calls `IngestRunnerError`, `JobCancelled`, `JobSpec`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/jobs|learnloop.content.authoring.jobs]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/import_jobs|learnloop.content.pipeline.import_jobs]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_job_types.py](../../../../../../../tests/test_job_types.py) — direct import
  - `test_the_job_contracts_are_one_set_of_objects_through_every_path`

## Modification guidance

- Change job contracts policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/job_contracts.py](../../../../../../../src/learnloop/content/pipeline/job_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
