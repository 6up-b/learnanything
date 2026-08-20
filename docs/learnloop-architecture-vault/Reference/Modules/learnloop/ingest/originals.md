---
title: "learnloop.ingest.originals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/originals.py"
source_paths:
  - "src/learnloop/ingest/originals.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.originals module"
  - "src/learnloop/ingest/originals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.originals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.originals` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Managed store for original source bytes (``canonical-sources/raw/``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/originals.py](../../../../../../src/learnloop/ingest/originals.py) |
| Source lines | 95 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `canonical_source_raw_path(root: Path, asset_hash_value: str) -> Path` ([source](../../../../../../src/learnloop/ingest/originals.py), line 23) — Return the config-free managed-original path for one content hash.
- `store_original_bytes(vault_root: Path, digest: str, raw_bytes: bytes) -> Path` ([source](../../../../../../src/learnloop/ingest/originals.py), line 29) — Write bytes into the content-addressed store (idempotent, atomic).
- `stored_original_path(vault_root: Path, digest: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 41)
- `resolve_original_file(vault_root: Path, *, digest: str | None, original_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 56) — Best available copy of a revision's original bytes: the managed store first, else ``original_uri`` when it still points at a local file.
- `is_pdf_file(path: Path) -> bool` ([source](../../../../../../src/learnloop/ingest/originals.py), line 65) — Header sniff — store files are extensionless (named by hash).
- `backfill_original(vault_root: Path, *, digest: str, original_uri: str | None) -> tuple[str, Path | None]` ([source](../../../../../../src/learnloop/ingest/originals.py), line 75) — Copy a pre-store revision's bytes into the store from ``original_uri``.

### Module constants

- `PDF_MAGIC` ([src/learnloop/ingest/originals.py](../../../../../../src/learnloop/ingest/originals.py), line 20)

## Internal implementation anchors

- `_local_uri_path(original_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `backfill_original`; statically calls `backfill_original`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `store_original_bytes`; statically calls `store_original_bytes`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `is_pdf_file`, `resolve_original_file`; statically calls `is_pdf_file`, `resolve_original_file`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `canonical_source_raw_path`; statically calls `canonical_source_raw_path`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `backfill_original`, `is_pdf_file`, `stored_original_path`; statically calls `backfill_original`, `is_pdf_file`, `stored_original_path`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]], [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]], [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_originals_store.py](../../../../../../tests/test_originals_store.py) — direct import
  - `test_backfill_statuses`
  - `test_register_reuse_backfills_missing_store_copy`
  - `test_register_with_vault_root_retains_bytes`
  - `test_resolve_prefers_store_then_original_uri`
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — direct import
  - `test_pdf_view_manifest_from_originals_store`
  - `test_pdf_view_resolves_source_ref_like_render_view`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/originals.py](../../../../../../src/learnloop/ingest/originals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
