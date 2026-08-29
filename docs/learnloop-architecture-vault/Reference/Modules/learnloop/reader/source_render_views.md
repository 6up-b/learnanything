---
title: "learnloop.reader.source_render_views"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_render_views.py"
source_paths:
  - "src/learnloop/reader/source_render_views.py"
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
  - "learnloop.reader.source_render_views module"
  - "src/learnloop/reader/source_render_views.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_render_views`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_render_views` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Source render views + display<->source-block crosswalk (spec §3.1-3.3, design B step 1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py) |
| Source lines | 215 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `sanitize_source_text(text: str) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 44) — Neutralize script execution / external embeds / local-file refs in untrusted source text (§3.3).
- `build_crosswalk(ir: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 69) — One display node per source block (1:1), with disposable display offsets.
- `resolve_or_create_render_view(repository: Repository, *, revision_id: str | None=None, extraction_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 93) — Lazy + idempotent render-view resolution keyed on ``request_hash``.
- `render_payload(repository: Repository, render_view_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 153) — The reader render payload: sanitized display nodes + per-block health + the six authority layers (§3.1).

### Module constants

- `RENDER_SCHEMA_VERSION` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 25)
- `RENDERER` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 26)
- `AUTHORITY_LAYERS` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 29)
- `_SCRIPT_RE` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 38)
- `_EMBED_RE` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 39)
- `_JS_URI_RE` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 40)
- `_FILE_URI_RE` ([src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py), line 41)

## Internal implementation anchors

- `_request_hash(*, revision_id: str, extraction_id: str, renderer_version: str) -> str` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 64)
- `_loads_list(value: str | None) -> list[Any]` ([source](../../../../../../src/learnloop/reader/source_render_views.py), line 206)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `render_payload`, `resolve_or_create_render_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_journey1_reading_first_session`
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_reextraction_changes_render_version_not_content_hash_bytes`
  - `test_render_payload_states_six_authority_layers`
  - `test_render_view_is_idempotent_on_request_hash`
  - `test_unsafe_source_html_is_sanitized_inert`

## Modification guidance

- Change source render views policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_render_views.py](../../../../../../src/learnloop/reader/source_render_views.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
