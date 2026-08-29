---
title: "learnloop.reader.reader_progression"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_progression.py"
source_paths:
  - "src/learnloop/reader/reader_progression.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_progression module"
  - "src/learnloop/reader/reader_progression.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_progression`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_progression` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader-driven progressive practice seeding (reader-first bootstrap).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py) |
| Source lines | 321 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `section_id_for_span(repository: Repository, *, extraction_id: str, span_id: str) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 30) — Resolve one reader span to its containing normalized section.
- `learning_objects_for_span(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 43) — Provenance-linked Learning Objects available as promotion targets.
- `learning_objects_for_section(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 65) — Active Learning Objects whose provenance cites spans inside the section.
- `source_refs_for_span(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str, learning_object_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 123) — Canonical, path-backed grounding bundles for a selected reader target.
- `section_generation_candidates(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, target_items_per_lo: int=3, max_new_per_lo: int=3) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 147) — LOs in the section that actually need items (dry-run of the expansion plan with the probe gate waived).
- `source_refs_for_section(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, learning_object_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 189) — Build bounded, proposal-local citation bundles for reader seeding.

### Module constants

- `_SOURCE_BUNDLE_RADIUS` ([src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py), line 26)
- `_MAX_SOURCE_BUNDLES_PER_LO` ([src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py), line 27)

## Internal implementation anchors

- `_merged_context_intervals(anchor_indices: list[int], span_count: int) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 307)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `learning_objects_for_span`, `source_refs_for_span`; statically calls `learning_objects_for_span`, `source_refs_for_span`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `section_generation_candidates`, `source_refs_for_section`; statically calls `section_generation_candidates`, `source_refs_for_section`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_practice_expansion_plan`; calls `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`; calls `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`

## Modification guidance

- Change reader progression policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
