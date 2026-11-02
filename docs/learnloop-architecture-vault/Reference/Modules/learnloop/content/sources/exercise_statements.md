---
title: "learnloop.content.sources.exercise_statements"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/exercise_statements.py"
source_paths:
  - "src/learnloop/content/sources/exercise_statements.py"
source_commit: "ae8339e6a36086fbd02e406b50925dd747ad3d6e"
source_commit_timestamp: "2026-10-20T12:30:38-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.exercise_statements module"
  - "src/learnloop/content/sources/exercise_statements.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.exercise_statements`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.exercise_statements` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: A textbook exercise's region and its statement, read one way (Reader RW4b fix round 5, R2; canonical sources S1).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/exercise_statements.py](../../../../../../../src/learnloop/content/sources/exercise_statements.py) |
| Source lines | 204 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ae8339e6a36086fbd02e406b50925dd747ad3d6e` |
| Commit timestamp | `2026-10-20T12:30:38-04:00` |

## Public API

- `class ExerciseRegion` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 51)
  - `key(self) -> tuple[str, ...]` (line 57; public)
- `starts_exercise(text: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 61) — Whether a block's own text opens an exercise: "20 Suppose ...", "3.
- `exercise_regions(connection, extraction_id: str) -> list[ExerciseRegion]` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 76) — One extraction's exercise regions in document order.
- `class ExerciseStatement` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 125) — A textbook exercise's statement, read now and cleared for showing.
- `exercise_region_spans(connection: Any, extraction_id: str, span_id: str, cache: dict[str, list[ExerciseRegion]] | None=None) -> tuple[str, ...] | None` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 141) — The span ids of the exercise region a span sits in (boundaries only, never its text), or None.
- `read_exercise_statement(vault: Any, repository: Any, extraction_id: str, span_ids: Sequence[str]) -> ExerciseStatement | None` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 155) — THE one reader of a textbook exercise's statement (see the module).
- `selection_nodes(statement: ExerciseStatement) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 186) — A Reader-style selection over the statement's whole blocks (``start = 0``, ``end = len(text)``): what S1's ``selection_for_region`` returns.

### Module constants

- `LABEL_RE` ([src/learnloop/content/sources/exercise_statements.py](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 46)
- `NUMBER_RE` ([src/learnloop/content/sources/exercise_statements.py](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 47)
- `PAGE_FURNITURE` ([src/learnloop/content/sources/exercise_statements.py](../../../../../../../src/learnloop/content/sources/exercise_statements.py), line 73)

### Explicit exports

`__all__` declares:

- `LABEL_RE`
- `NUMBER_RE`
- `PAGE_FURNITURE`
- `ExerciseRegion`
- `ExerciseStatement`
- `exercise_region_spans`
- `exercise_regions`
- `read_exercise_statement`
- `selection_nodes`
- `starts_exercise`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `read_exercise_statement`, `selection_nodes`; statically calls `read_exercise_statement`, `selection_nodes`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `ExerciseRegion`, `LABEL_RE`, `NUMBER_RE`, `PAGE_FURNITURE`, `exercise_regions`, `starts_exercise`; statically calls `exercise_regions`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `read_exercise_statement`; statically calls `read_exercise_statement`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`; statically calls `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `LABEL_RE`, `NUMBER_RE`, `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`, `selection_nodes`; statically calls `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`, `selection_nodes`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `ExerciseStatement`, `exercise_region_spans`, `read_exercise_statement`; statically calls `exercise_region_spans`, `read_exercise_statement`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_withheld`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `MAX_REGION_BLOCKS`, `REGION_BODY_HINTS`, `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`; calls `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `effective_hint`; calls `effective_hint`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]], [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]], [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it`
  - `test_r4_the_statement_reader_fails_closed`

## Modification guidance

- Change exercise statements policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/exercise_statements.py](../../../../../../../src/learnloop/content/sources/exercise_statements.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
