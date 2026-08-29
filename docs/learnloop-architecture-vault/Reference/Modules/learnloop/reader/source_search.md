---
title: "learnloop.reader.source_search"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_search.py"
source_paths:
  - "src/learnloop/reader/source_search.py"
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
  - "learnloop.reader.source_search module"
  - "src/learnloop/reader/source_search.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_search`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_search` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Across-source text search for the Reader library.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_search.py](../../../../../../src/learnloop/reader/source_search.py) |
| Source lines | 87 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `search_sources(repository: Repository, *, query: str, limit: int=MAX_HITS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_search.py), line 42) — Search every reader-enabled source's current extraction for ``query``.

### Module constants

- `MAX_HITS` ([src/learnloop/reader/source_search.py](../../../../../../src/learnloop/reader/source_search.py), line 17)
- `_SNIPPET_RADIUS` ([src/learnloop/reader/source_search.py](../../../../../../src/learnloop/reader/source_search.py), line 18)

## Internal implementation anchors

- `_artifact_title(artifact: dict[str, Any], revision: dict[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/reader/source_search.py), line 21)
- `_snippet(text: str, needle: str) -> str` ([source](../../../../../../src/learnloop/reader/source_search.py), line 30)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `search_sources`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_search.py](../../../../../../tests/test_source_search.py) — direct import
  - `test_search_finds_hits_across_sources_with_span_addresses`
  - `test_search_skips_reader_disabled_sources_and_short_queries`

## Modification guidance

- Change source search policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_search.py](../../../../../../src/learnloop/reader/source_search.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
