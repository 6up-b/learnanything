---
title: "learnloop.attempts.lifecycle_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/lifecycle_inputs.py"
source_paths:
  - "src/learnloop/attempts/lifecycle_inputs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.lifecycle_inputs module"
  - "src/learnloop/attempts/lifecycle_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.lifecycle_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.lifecycle_inputs` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Which required facet set a grade application reads (mvp-0.66, retired items replay at the right point in history).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/lifecycle_inputs.py](../../../../../../src/learnloop/attempts/lifecycle_inputs.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LifecycleInputsMissing(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 33) — An attempt applied at the tag has no recorded lifecycle inputs: its replay cannot be told what it read.
  - `__init__(self, attempt_id: str)` (line 36; internal)
- `reconstructing_legacy_lifecycle_inputs() -> Iterator[dict[str, LifecycleInputs]]` ([source](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 45) — Collect, while the block runs, the predecessor's reading for every replayed attempt that has no row (the first reading of each attempt; a later pass of the same rebuild reuses it).
- `recorded_for_replay(vault: LoadedVault, repository: Repository, attempt_id: str) -> LifecycleInputs | None` ([source](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 57) — The set recorded for a replayed or regraded attempt (None below the tag, or where none was recorded).
- `application_required_facets(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, replay: bool, recorded: LifecycleInputs | None) -> tuple[Collection[str], bool, LifecycleInputs | None]` ([source](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 68) — The required facets a grade application counts, whether its coverage sums them in canonical (sorted) order, and the new capture its attempt records (None on replay, on a regrade and below the tag).
- `application_lifecycle_inputs(vault: LoadedVault, repository: Repository, *, attempt_id: str, learning_object_id: str, replay: bool, recorded: LifecycleInputs | None) -> tuple[LifecycleInputs, bool]` ([source](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 89) — At the tag: the set this application reads, and whether it is a new capture its attempt must record.

### Module constants

- `_RECONSTRUCTING` ([src/learnloop/attempts/lifecycle_inputs.py](../../../../../../src/learnloop/attempts/lifecycle_inputs.py), line 30)

### Explicit exports

`__all__` declares:

- `LifecycleInputsMissing`
- `application_lifecycle_inputs`
- `application_required_facets`
- `reconstructing_legacy_lifecycle_inputs`
- `recorded_for_replay`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `application_required_facets`, `recorded_for_replay`; statically calls `application_required_facets`, `recorded_for_replay`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `reconstructing_legacy_lifecycle_inputs`; statically calls `reconstructing_legacy_lifecycle_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LIFECYCLE_INPUTS_VERSIONS`, `lifecycle_inputs_on`; calls `lifecycle_inputs_on`
- [[Reference/Modules/learnloop/db/attempt_lifecycle_inputs|learnloop.db.attempt_lifecycle_inputs]] — imports `BASIS_CAPTURED`, `BASIS_LEGACY_RECONSTRUCTED`, `LifecycleInputs`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rebuild_closed_row_answer.py](../../../../../../tests/test_rebuild_closed_row_answer.py) — direct import
  - `test_an_attempt_applied_at_the_tag_without_its_capture_refuses_to_replay`

## Modification guidance

- Change lifecycle inputs policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/lifecycle_inputs.py](../../../../../../src/learnloop/attempts/lifecycle_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
