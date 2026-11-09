---
title: "learnloop.ingest.originals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/originals.py"
source_paths:
  - "src/learnloop/ingest/originals.py"
source_commit: "f570736fc6f820fb44181195ebd5da63f883905a"
source_commit_timestamp: "2026-09-23T12:40:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 110 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f570736fc6f820fb44181195ebd5da63f883905a` |
| Commit timestamp | `2026-09-23T12:40:16-04:00` |

## Public API

- `canonical_source_raw_path(root: Path, asset_hash_value: str) -> Path` ([source](../../../../../../src/learnloop/ingest/originals.py), line 23) — Return the config-free managed-original path for one content hash.
- `store_original_bytes(vault_root: Path, digest: str, raw_bytes: bytes) -> Path` ([source](../../../../../../src/learnloop/ingest/originals.py), line 29) — Write bytes into the content-addressed store (idempotent, atomic).
- `stored_original_path(vault_root: Path, digest: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 56)
- `resolve_original_file(vault_root: Path, *, digest: str | None, original_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 71) — Best available copy of a revision's original bytes: the managed store first, else ``original_uri`` when it still points at a local file.
- `is_pdf_file(path: Path) -> bool` ([source](../../../../../../src/learnloop/ingest/originals.py), line 80) — Header sniff — store files are extensionless (named by hash).
- `backfill_original(vault_root: Path, *, digest: str, original_uri: str | None) -> tuple[str, Path | None]` ([source](../../../../../../src/learnloop/ingest/originals.py), line 90) — Copy a pre-store revision's bytes into the store from ``original_uri``.

### Module constants

- `PDF_MAGIC` ([src/learnloop/ingest/originals.py](../../../../../../src/learnloop/ingest/originals.py), line 20)

## Internal implementation anchors

- `_local_uri_path(original_uri: str | None) -> Path | None` ([source](../../../../../../src/learnloop/ingest/originals.py), line 63)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `canonical_source_raw_path`, `store_original_bytes`; statically calls `canonical_source_raw_path`, `store_original_bytes`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `backfill_original`; statically calls `backfill_original`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `stored_original_path`; statically calls `stored_original_path`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `stored_original_path`; statically calls `stored_original_path`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `store_original_bytes`; statically calls `store_original_bytes`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `canonical_source_raw_path`, `store_original_bytes`; statically calls `canonical_source_raw_path`, `store_original_bytes`
- [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]] — imports `is_pdf_file`, `stored_original_path`; statically calls `is_pdf_file`, `stored_original_path`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `is_pdf_file`, `resolve_original_file`; statically calls `is_pdf_file`, `resolve_original_file`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `is_pdf_file`, `resolve_original_file`; statically calls `is_pdf_file`, `resolve_original_file`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `canonical_source_raw_path`; statically calls `canonical_source_raw_path`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `backfill_original`, `is_pdf_file`, `stored_original_path`; statically calls `backfill_original`, `is_pdf_file`, `stored_original_path`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_capture_domain.py](../../../../../../tests/test_capture_domain.py) — direct import
  - `test_image_sanitization_and_raw_fingerprint`
  - `test_photo_preview_refuses_tampered_hashes_missing_files_and_purge`
  - `test_purge_retains_canonical_source_original`
  - `test_purge_shared_original_and_retry_never_resurrects`
- [tests/test_capture_originals_race.py](../../../../../../tests/test_capture_originals_race.py) — direct import
  - `test_source_publication_and_capture_purge_share_writer_reservation`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_concurrent_original_writers_use_independent_temporary_files`
- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
- [tests/test_mobile_v4_eligibility.py](../../../../../../tests/test_mobile_v4_eligibility.py) — direct import
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_a_stored_image_is_served_by_its_content_address_and_never_a_pdf`
- [tests/test_originals_store.py](../../../../../../tests/test_originals_store.py) — direct import
  - `test_backfill_statuses`
  - `test_failed_original_write_leaves_no_temporary_file`
  - `test_original_bytes_are_synced_before_they_become_visible`
  - `test_register_reuse_backfills_missing_store_copy`
  - `test_register_with_vault_root_retains_bytes`
  - `test_resolve_prefers_store_then_original_uri`
  - `test_stored_original_is_world_readable_under_the_default_umask`
- [tests/test_project_redaction.py](../../../../../../tests/test_project_redaction.py) — direct import
  - `test_capture_never_stores_secret_files_or_lines`
  - `test_hunk_header_secrets_never_reach_the_store`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_e1_the_reread_hands_the_import_the_stored_bytes_never_a_store_path`
  - `test_e1_the_reread_reads_the_stored_original_and_reuses_the_revision`
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — direct import
  - `test_pdf_view_manifest_from_originals_store`
  - `test_pdf_view_resolves_source_ref_like_render_view`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u2_pdf_view_lists_each_passages_page_for_a_text_only_extraction`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/originals.py](../../../../../../src/learnloop/ingest/originals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
