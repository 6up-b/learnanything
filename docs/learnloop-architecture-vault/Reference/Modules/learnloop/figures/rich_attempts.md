---
title: "learnloop.figures.rich_attempts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/rich_attempts.py"
source_paths:
  - "src/learnloop/figures/rich_attempts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.figures.rich_attempts module"
  - "src/learnloop/figures/rich_attempts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.rich_attempts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.rich_attempts` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Durable rich author verdicts for one execution of a figure job.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/rich_attempts.py](../../../../../../src/learnloop/figures/rich_attempts.py) |
| Source lines | 72 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RichAttempts(FR.AuthorAttempts)` ([source](../../../../../../src/learnloop/figures/rich_attempts.py), line 12)
  - `__init__(self, repository, job_id, request, request_id, prompt_version)` (line 13; internal)
  - `start(self, number, *, route=None)` (line 25; public)
  - `ask(self, route, *args, **kwargs)` (line 37; public)
  - `end(self, rule, **kwargs)` (line 44; public)
  - `record(self, *, result=None, error=None, interrupted=False, retrying=False)` (line 48; public)
  - `stage(self)` (line 64; public)
  - `finish(self, **kwargs)` (line 68; public)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `RichAttempts`; statically calls `RichAttempts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `job_attempt_decisions`; calls `job_attempt_decisions`
- [[Reference/Modules/learnloop/figures/records|learnloop.figures.records]] — imports `module`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `new_record_id`

### Platform and third-party dependencies

- Standard library: `copy`, `dataclasses`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_rich_attempt_records.py](../../../../../../tests/test_figure_rich_attempt_records.py) — direct import
  - `test_lease_recovery_preserves_the_interrupted_author_attempt`

## Modification guidance

- Make changes here when the responsibility remains rich attempts within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/rich_attempts.py](../../../../../../src/learnloop/figures/rich_attempts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
