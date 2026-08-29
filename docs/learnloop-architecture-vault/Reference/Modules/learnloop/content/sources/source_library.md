---
title: "learnloop.content.sources.source_library"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_library.py"
source_paths:
  - "src/learnloop/content/sources/source_library.py"
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
  - "learnloop.content.sources.source_library module"
  - "src/learnloop/content/sources/source_library.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.source_library`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_library` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Vault-level source library registration (spec_source_ingestion_v2 §4.1/§13).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_library.py](../../../../../../../src/learnloop/content/sources/source_library.py) |
| Source lines | 154 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RegisteredRevision` ([source](../../../../../../../src/learnloop/content/sources/source_library.py), line 25)
- `register_source_revision(repo: Repository, *, acquisition_kind: str, canonical_uri: str | None, raw_bytes: bytes, note_id: str | None=None, original_uri: str | None=None, retrieved_at: str | None=None, work_id: str | None=None, display_title: str | None=None, reader_enabled: bool | None=None, vault_root: Path | None=None, clock: Clock | None=None) -> RegisteredRevision` ([source](../../../../../../../src/learnloop/content/sources/source_library.py), line 33) — Register (or reuse) the artifact/revision rows for one acquisition.
- `index_legacy_note(repo: Repository, *, note_id: str, acquisition_kind: str, canonical_uri: str | None, raw_bytes: bytes, note_path: str | None=None, retrieved_at: str | None=None, clock: Clock | None=None) -> RegisteredRevision` ([source](../../../../../../../src/learnloop/content/sources/source_library.py), line 127) — Index one legacy subject-scoped source note into artifact/revision rows.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `register_source_revision`; statically calls `register_source_revision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `store_original_bytes`; calls `store_original_bytes`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_acquisition_preview_reports_recognition_dupes_and_existing`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_import_retry_replaces_ir_left_by_interrupted_run`
- [tests/test_originals_store.py](../../../../../../../tests/test_originals_store.py) — direct import
  - `test_register_reuse_backfills_missing_store_copy`
  - `test_register_with_vault_root_retains_bytes`
- [tests/test_primed_attempts.py](../../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_feedback_resolves_current_ingest_span_and_filename`
  - `test_missing_note_resolves_youtube_ingest_identity`
- [tests/test_self_grade.py](../../../../../../../tests/test_self_grade.py) — direct import
  - `test_practice_item_detail_displays_source_name_instead_of_id`
- [tests/test_show.py](../../../../../../../tests/test_show.py) — direct import
  - `test_show_adds_imported_source_name_without_replacing_ref_id`
- [tests/test_sidecar_ingest_m3.py](../../../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — direct import
  - `test_different_artifacts_same_bytes_distinct_revisions`
  - `test_extraction_request_hash_unique_constraint`
  - `test_persist_and_load_document_ir_round_trips`
  - `test_retry_keys_on_request_hash_before_result_exists`
  - `test_same_artifact_changed_bytes_links_new_revision`
  - `test_same_artifact_same_bytes_reuses_revision`
- [tests/test_source_refs.py](../../../../../../../tests/test_source_refs.py) — direct import
  - `test_file_source_ref_uses_original_imported_filename`
  - `test_youtube_source_ref_uses_title_captured_during_ingest`
- [tests/test_span_reanchor.py](../../../../../../../tests/test_span_reanchor.py) — direct import
  - `test_reanchor_aliases_persist`

## Modification guidance

- Change source library policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_library.py](../../../../../../../src/learnloop/content/sources/source_library.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
