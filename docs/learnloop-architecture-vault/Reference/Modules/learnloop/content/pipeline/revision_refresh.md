---
title: "learnloop.content.pipeline.revision_refresh"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/revision_refresh.py"
source_paths:
  - "src/learnloop/content/pipeline/revision_refresh.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.revision_refresh module"
  - "src/learnloop/content/pipeline/revision_refresh.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.revision_refresh`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.revision_refresh` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Revision refresh (source-ingestion §10.4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/revision_refresh.py](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RefreshResult` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 34)
  - `as_dict(self) -> dict[str, Any]` (line 46; public)
- `refresh_revision(root: Path, source_set_id: str, *, source_id: str, old_revision_id: str, new_revision_id: str, client: Any=None, new_extraction_id: str | None=None, confirm: bool=False, run_append: bool=True, repository: Repository | None=None, clock: Clock | None=None) -> RefreshResult` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 73) — Adopt ``new_revision_id`` for ``source_id`` in ``source_set_id`` (§10.4).

### Module constants

- `_EVENTABLE` ([src/learnloop/content/pipeline/revision_refresh.py](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 187)

## Internal implementation anchors

- `_span_id_from_locator(link: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 61)
- `_refresh(root, vault, repository, source_set_id, source_id, old_revision_id, new_revision_id, *, client, new_extraction_id, confirm, run_append, clock)` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 100)
- `_record_span_change_event(repository, link, status, now) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 168)
- `_advance_membership(root, vault, source_set_id, source_id, old_revision_id, new_revision_id, clock) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py), line 193)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `refresh_revision`; statically calls `refresh_revision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `append_source`; calls `append_source`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `EXACT_HASH`, `reanchor_spans`; calls `reanchor_spans`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_revision_refresh.py](../../../../../../../tests/test_revision_refresh.py) — direct import
  - `test_new_revision_pinned_membership_requires_confirmation`
  - `test_unchanged_spans_keep_links_changed_spans_go_stale`

## Modification guidance

- Change revision refresh policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/revision_refresh.py](../../../../../../../src/learnloop/content/pipeline/revision_refresh.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
