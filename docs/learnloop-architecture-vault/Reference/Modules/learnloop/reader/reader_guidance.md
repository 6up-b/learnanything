---
title: "learnloop.reader.reader_guidance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_guidance.py"
source_paths:
  - "src/learnloop/reader/reader_guidance.py"
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
  - "learnloop.reader.reader_guidance module"
  - "src/learnloop/reader/reader_guidance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_guidance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_guidance` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Personalized, source-grounded guidance for the Reader.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py) |
| Source lines | 553 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `normalize_text(value: str | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 42)
- `goal_for_item(vault: LoadedVault, learning_object: Any, item: Any) -> Any | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 116)
- `extraction_sections(ir: Any) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 252) — Derive the Reader's guide sections from one extraction's IR.
- `build_guide_plan(vault: LoadedVault, repository: Repository, *, extraction_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 292) — Build section checks and suggested passages for one extraction.

### Module constants

- `_SPAN_LOCATOR_RE` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 25)
- `_TIME_LOCATOR_RE` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 26)
- `_FURNITURE_TYPES` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 27)
- `_PATTERN_PHASES` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 28)
- `_READING_PHASES` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 34)

## Internal implementation anchors

- `_extras(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 37)
- `_section_key(value: str | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 46)
- `_canonical_note_ids(vault: LoadedVault, artifact: dict[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 50) — Resolve legacy note-id provenance to the source-library artifact.
- `_ref_matches_source(ref: SourceRef, source_id: str, note_ids: set[str]) -> bool` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 64)
- `_span_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str, note_ids: set[str], blocks: list[Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 73)
- `_learner_signal(repository: Repository, learning_object_id: str, *, goal_match: bool) -> tuple[float, str, str]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 130) — Return a local ranking boost and a learner-facing, non-numeric reason.
- `_refs_for(vault: LoadedVault, item: Any, learning_object: Any) -> Iterable[SourceRef]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 157)
- `_placement_item_id(placement: dict[str, Any], blueprint_spec: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 166) — Resolve the explicitly placed surface, with a legacy blueprint fallback.
- `_placement_phase(placement: dict[str, Any]) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 191)
- `_placement_section(placement: dict[str, Any], *, blueprint_unit_id: str, sections: list[dict[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 200)
- `_placement_suppressed(repository: Repository, placement_event_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 237) — Honor the learner's durable "don't bring this back" control.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`; statically calls `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `build_guide_plan`, `goal_for_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]], [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
  - `test_dont_bring_this_back_suppresses_the_exact_reviewed_placement`
  - `test_legacy_placement_uses_only_its_reviewed_familiar_exemplar`
  - `test_reviewed_boundary_placement_connects_question_to_active_goal`
  - `test_timestamp_provenance_anchors_video_transcript_guidance`
  - `test_unplaced_source_item_never_becomes_a_boundary_question`
  - `test_unresolved_misunderstanding_drives_plain_language_passage_reason`
- [tests/test_reader_quick_check.py](../../../../../../tests/test_reader_quick_check.py) — direct import
  - `test_dismissed_question_suppresses_reauthoring_and_display`
  - `test_escalate_mints_practice_item_with_span_provenance`
  - `test_guide_plan_falls_back_to_authored_question`
  - `test_owner_reviewed_placement_wins_over_authored`

## Modification guidance

- Change reader guidance policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
