---
title: "learnloop.reader.section_generation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/section_generation.py"
source_paths:
  - "src/learnloop/reader/section_generation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.section_generation module"
  - "src/learnloop/reader/section_generation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.section_generation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.section_generation` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Section practice candidates, separate from reader grounding, and when a finished section's questions are written.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/section_generation.py](../../../../../../src/learnloop/reader/section_generation.py) |
| Source lines | 163 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `section_generation_candidates(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, target_items_per_lo: int=3, max_new_per_lo: int=3) -> list[str]` ([source](../../../../../../src/learnloop/reader/section_generation.py), line 42) — LOs in the section that actually need items (dry-run of the expansion plan with the probe gate waived).
- `section_reason(section_id: str) -> str` ([source](../../../../../../src/learnloop/reader/section_generation.py), line 84) — The reason a finished section's writing is queued under.
- `start_section_questions(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, enqueue: Enqueue, fresh_vault: Callable[[], LoadedVault], topics_settled: Callable[[], tuple[bool, str | None]], from_stamp: str | None=None, completed_at: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/reader/section_generation.py), line 90) — Start a finished section's question writing, once, or record why not yet.

### Module constants

- `OWED` ([src/learnloop/reader/section_generation.py](../../../../../../src/learnloop/reader/section_generation.py), line 36)

### Explicit exports

`__all__` declares:

- `DEFERRED_TO_PRIMARY`
- `ENQUEUING`
- `NONE_NEEDED`
- `NONE_NEEDED_BEFORE`
- `OWED`
- `WAITING_FOR_BUILD`
- `section_generation_candidates`
- `section_reason`
- `start_section_questions`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `section_generation_candidates`, `section_reason`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `DEFERRED_TO_PRIMARY`, `WAITING_FOR_BUILD`
- [[Reference/Modules/learnloop_sidecar/section_questions|learnloop_sidecar.section_questions]] — imports `OWED`, `module`; statically calls `start_section_questions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_practice_expansion_plan`; calls `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/reader|learnloop.db.stores.reader]] — imports `SECTION_DEFERRED_TO_PRIMARY`, `SECTION_ENQUEUING`, `SECTION_NONE_NEEDED`, `SECTION_NONE_NEEDED_BEFORE`, `SECTION_WAITING_FOR_BUILD`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_section`, `source_refs_for_section`; calls `learning_objects_for_section`, `source_refs_for_section`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/section_questions|learnloop_sidecar.section_questions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once`

## Modification guidance

- Change section generation policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/section_generation.py](../../../../../../src/learnloop/reader/section_generation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
