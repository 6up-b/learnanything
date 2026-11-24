---
title: "learnloop.source_retrieval.follow_along"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/follow_along.py"
source_paths:
  - "src/learnloop/source_retrieval/follow_along.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.follow_along module"
  - "src/learnloop/source_retrieval/follow_along.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.follow_along`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.follow_along` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader workbench v2 RD10 (spec §7.5): follow-along, book ↔ video.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/follow_along.py](../../../../../../src/learnloop/source_retrieval/follow_along.py) |
| Source lines | 63 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `follow(vault: Any, repository: Repository, video_extraction_id: str, t: float, book_extraction_id: str, *, cache: SC.LibraryCache | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/follow_along.py), line 17) — What a book window follows at a video's time: ``status`` (``following``, ``no_passage``, ``no_section``, ``withheld``), the video's section with its time bounds (the desk asks again only once the time leaves them), the chapter, and per LO the book's correspondent sections (each…

### Explicit exports

`__all__` declares:

- `follow`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/video|learnloop_sidecar.handlers.video]] — imports `module`; statically calls `follow`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `correspondents`
- [[Reference/Modules/learnloop/source_retrieval/video_chapters|learnloop.source_retrieval.video_chapters]] — imports `module`; calls `accepted_at`, `section_at`, `transcript_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/video|learnloop_sidecar.handlers.video]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd10_video.py](../../../../../../tests/test_reader_rd10_video.py) — direct import
  - `test_chapters_are_judged_once_stored_suggested_and_accepting_stores`
  - `test_follow_along_maps_the_playing_cue_to_the_books_correspondent_passage`

## Modification guidance

- Make changes here when the responsibility remains follow along within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/follow_along.py](../../../../../../src/learnloop/source_retrieval/follow_along.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
