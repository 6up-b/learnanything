---
title: "learnloop.practice_index.contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/contracts.py"
source_paths:
  - "src/learnloop/practice_index/contracts.py"
source_commit: "9cbc0eacaa318a539f26621ed675698b7cafb1de"
source_commit_timestamp: "2026-10-13T01:42:51-04:00"
source_worktree_state: "clean"
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
  - "learnloop.practice_index.contracts module"
  - "src/learnloop/practice_index/contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.contracts` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Strict wire contracts for the practice index's paid LLM roles.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/contracts.py](../../../../../../src/learnloop/practice_index/contracts.py) |
| Source lines | 97 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9cbc0eacaa318a539f26621ed675698b7cafb1de` |
| Commit timestamp | `2026-10-13T01:42:51-04:00` |

## Public API

- `class DossierContrast(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 18)
- `class FacetDossierDraft(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 23) — scope (covers/excludes), moves, errors and contrast (Slice 2 §5.9).
- `class CandidateJudgment(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 33)
- `class PracticeRerank(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 39) — Judge every candidate, then pick and order the best few.
- `class FacetQuote(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 46) — A facet the exercise exercises, with a verbatim quote from its statement that shows it (checked in code; a facet whose quote fails is dropped).
- `class ExerciseMetadata(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 54) — Provisional metadata for one unimported textbook exercise (§8.1).
- `class MixedPracticeRerank(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 62) — Judge every candidate (practice items and textbook exercises), pick the best few, and give each textbook exercise its provisional metadata.
- `class RelevanceLabels(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 71)
- `class WrittenQuery(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 75)
- `class WrittenQueries(WireModel)` ([source](../../../../../../src/learnloop/practice_index/contracts.py), line 80)

### Module constants

- `RELEVANCE_SCORE` ([src/learnloop/practice_index/contracts.py](../../../../../../src/learnloop/practice_index/contracts.py), line 15)

### Explicit exports

`__all__` declares:

- `RELEVANCE_SCORE`
- `CandidateJudgment`
- `DossierContrast`
- `ExerciseMetadata`
- `FacetDossierDraft`
- `FacetQuote`
- `MixedPracticeRerank`
- `PracticeRerank`
- `Relevance`
- `RelevanceLabels`
- `WrittenQueries`
- `WrittenQuery`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `FacetDossierDraft`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `RELEVANCE_SCORE`, `RelevanceLabels`, `WrittenQueries`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `MixedPracticeRerank`, `PracticeRerank`, `RELEVANCE_SCORE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]], [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_find_dry_run_bounds_the_rerank_pool_the_query_vector_will_fill`
- [tests/test_practice_index_text.py](../../../../../../tests/test_practice_index_text.py) — direct import
  - `test_wire_contracts_are_strict`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_a_harvest_says_why_picked_exercises_were_not_imported`

## Modification guidance

- Make changes here when the responsibility remains contracts within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/contracts.py](../../../../../../src/learnloop/practice_index/contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
