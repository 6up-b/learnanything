---
title: "learnloop.content.sources.source_refs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_refs.py"
source_paths:
  - "src/learnloop/content/sources/source_refs.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.source_refs module"
  - "src/learnloop/content/sources/source_refs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.source_refs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_refs` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Human-facing labels and metadata for durable source references.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_refs.py](../../../../../../../src/learnloop/content/sources/source_refs.py) |
| Source lines | 239 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SourceRefPresentation` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 28) — Resolved source identity suitable for UI and CLI presentation.
- `source_ref_presentation(vault, repository, ref) -> SourceRefPresentation` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 38) — Resolve one ref without changing its persisted provenance identity.
- `source_ref_display_dto(vault, repository, ref) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 118) — Return a source-ref payload augmented with its human-facing name.

### Module constants

- `_SPAN_LOCATOR` ([src/learnloop/content/sources/source_refs.py](../../../../../../../src/learnloop/content/sources/source_refs.py), line 18)
- `_FILE_KINDS` ([src/learnloop/content/sources/source_refs.py](../../../../../../../src/learnloop/content/sources/source_refs.py), line 19)
- `_KIND_ALIASES` ([src/learnloop/content/sources/source_refs.py](../../../../../../../src/learnloop/content/sources/source_refs.py), line 20)

## Internal implementation anchors

- `_revision_for_ref(repository, ref) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 136)
- `_note_for_ref(vault, ref, revision: Mapping[str, Any] | None)` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 157)
- `_canonical_metadata(note) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 173)
- `_is_file_source(kind: str | None, uri: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 181)
- `_file_name(uri: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 192)
- `_uri_label(uri: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 200)
- `_first_heading(body: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 212)
- `_text_field(value: Any, field: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 220)
- `_clean_text(value: Any) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 226)
- `_repo_call(repository, method: str, *args)` ([source](../../../../../../../src/learnloop/content/sources/source_refs.py), line 233)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `source_ref_display_dto`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `source_ref_presentation`; statically calls `source_ref_presentation`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `source_ref_display_dto`; statically calls `source_ref_display_dto`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `re`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]], [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_refs.py](../../../../../../../tests/test_source_refs.py) — direct import
  - `test_file_source_ref_uses_original_imported_filename`
  - `test_youtube_source_ref_uses_title_captured_during_ingest`

## Modification guidance

- Change source refs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_refs.py](../../../../../../../src/learnloop/content/sources/source_refs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
