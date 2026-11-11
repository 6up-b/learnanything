---
title: "learnloop.practice_index.coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/coverage.py"
source_paths:
  - "src/learnloop/practice_index/coverage.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.coverage module"
  - "src/learnloop/practice_index/coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.coverage` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Coverage: facets with few admissible items become Phase 5a generation targets.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/coverage.py](../../../../../../src/learnloop/practice_index/coverage.py) |
| Source lines | 92 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CoverageTarget` ([source](../../../../../../src/learnloop/practice_index/coverage.py), line 21)
  - `as_dict(self) -> dict[str, Any]` (line 29; public)
- `coverage_targets(vault: LoadedVault, repository: Repository, *, min_eligible: int | None=None, clock: Clock | None=None) -> list[CoverageTarget]` ([source](../../../../../../src/learnloop/practice_index/coverage.py), line 35) — Facets with fewer admissible items than the threshold, fewest first.
- `coverage_report(vault: LoadedVault, repository: Repository, *, min_eligible: int | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/coverage.py), line 42) — Aggregate coverage: targets, counts and per-facet eligibility.

### Explicit exports

`__all__` declares:

- `CoverageTarget`
- `coverage_report`
- `coverage_targets`

## Internal implementation anchors

- `_coverage(vault: LoadedVault, repository: Repository, *, min_eligible: int | None, clock: Clock | None) -> tuple[list[CoverageTarget], dict[str, Any]]` ([source](../../../../../../src/learnloop/practice_index/coverage.py), line 49)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `coverage_report`; statically calls `coverage_report`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `coverage_targets`; statically calls `coverage_targets`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `PracticeAdmission`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `facet_items`, `facet_label`, `registered_facets`; calls `facet_items`, `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]

## Modification guidance

- Make changes here when the responsibility remains coverage within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/coverage.py](../../../../../../src/learnloop/practice_index/coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
