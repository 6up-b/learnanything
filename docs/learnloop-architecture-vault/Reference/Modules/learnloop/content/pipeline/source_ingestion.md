---
title: "learnloop.content.pipeline.source_ingestion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/source_ingestion.py"
source_paths:
  - "src/learnloop/content/pipeline/source_ingestion.py"
source_commit: "4c00dc55d956abf57d4202863b629b9567104c34"
source_commit_timestamp: "2026-09-23T12:46:21-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.source_ingestion module"
  - "src/learnloop/content/pipeline/source_ingestion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.source_ingestion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps source ingestion behavior inside its owning package, [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]]. Its public surface centers on `request_canonical_ingest`, `SourceIngestionError`, `FetchResult`, `CaptionCue`, `NormalizedSource`, `RegisteredSource`, `IngestWindow`, `IngestResult` and 19 more public symbols.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/source_ingestion.py](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py) |
| Source lines | 2176 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4c00dc55d956abf57d4202863b629b9567104c34` |
| Commit timestamp | `2026-09-23T12:46:21-04:00` |

## Public API

- `request_canonical_ingest(client: AIProviderClient, context: CanonicalIngestContext) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 46) — Run the feature-owned canonical-ingest operation.
- `class SourceIngestionError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 62)
- `class FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 67)
- `class CaptionCue` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 80)
- `class NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 87)
- `class RegisteredSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 101)
- `class IngestWindow` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 109)
- `class IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 115)
  - `as_dict(self) -> dict[str, Any]` (line 138; public)
- `class SourceChangeAnalysis` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 160)
- `ingest_canonical_source(root: Path, source: str, codex_client: AIProviderClient, *, kind: KindOption='auto', subject_id: str | None=None, learning_object_ids: list[str] | None=None, goal_id: str | None=None, allow_auto_captions: bool | None=None, instructions: str | None=None, model: str | None=None, codex_revision: str | None=None, retry_client: AIProviderClient | None=None, retry_model: str | None=None, retry_provider_revision: str | None=None, purpose: str='canonical_ingest', pdf_engine: str | None=None, pdf_use_llm: bool | None=None, ir_markdown: str | None=None, resume_extraction_id: str | None=None, clock: Clock | None=None, progress: IngestProgress | None=None) -> IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 165)
- `detect_source_kind(source: str, *, kind: KindOption='auto', learning_object_ids: list[str] | None=None) -> SourceKind` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 668)
- `resolve_canonical_source(source: str, *, kind: KindOption='auto', learning_object_ids: list[str] | None=None) -> tuple[ResolvedSource, SourceKind]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 677)
- `fetch_source(root: Path, source: str, *, kind: SourceKind, allow_auto_captions: bool, pdf_config: PdfIngestConfig | None=None, clock: Clock | None=None, progress: IngestProgress | None=None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 707)
- `normalize_source(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 755)
- `source_content_hash(markdown: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 763)
- `analyze_source_change(vault, source: NormalizedSource, new_chunks: list[SourceChunk], content_hash: str, *, clock: Clock | None=None) -> SourceChangeAnalysis` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 768)
- `chunk_normalized_source(source: NormalizedSource) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 848)
- `chunk_markdown(markdown: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 869)
- `build_ingest_windows(chunks: list[SourceChunk], *, window_char_cap: int) -> list[IngestWindow]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 937)
- `canonical_ingest_context_hash(canonical_uri: str, content_hash: str, source_kind: SourceKind, target_learning_object_ids: list[str], *, instructions: str | None=None, subject_id: str | None=None, provider_identity: dict[str, Any] | None=None, purpose: str='canonical_ingest') -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 973)
- `register_canonical_source(root: Path, subject_id: str, source: NormalizedSource, raw_bytes: bytes, content_hash: str, *, clock: Clock | None=None) -> RegisteredSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 993)
- `merge_window_proposals(proposals: list[AuthoringProposal]) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1078)
- `chunks_for_note_body(kind: SourceKind, body: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1734)
- `locator_hash_for_ref(chunks: list[SourceChunk], locator: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1770)
- `child_chunks_for_locator(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1787)
- `caption_chunks_for_time_range(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1795)
- `source_youtube_video_id(source: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2062)

## Internal implementation anchors

- `_run_ingest_windows(client: AIProviderClient, vault, registered: RegisteredSource, normalized: NormalizedSource, windows: list[IngestWindow], *, target_learning_object_ids: list[str], instructions: str | None, progress: IngestProgress | None=None, usage: dict[str, int] | None=None) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 472)
- `_report_progress(progress: IngestProgress | None, phase: str, **details: Any) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 513)
- `_proposal_with_change_summary(proposal: AuthoringProposal, summary: str) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 518)
- `_agent_provider_fields(client: AIProviderClient, *, model: str | None, provider_revision: str | None) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 528)
- `_reachability_summary(vault, repository, learning_object_ids: list[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 548) — Verdict counts for the just-applied LOs' contract cells (Meas §5.8.2).
- `_apply_instrument_gates(rows: list[dict[str, Any]], vault, repository, grading_client) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 578) — Stage-5.3/6 instrument gates on the canonical-ingest lane.
- `_downgrade_unready_auto_apply(rows: list[dict[str, Any]], vault) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 595) — Keep auto-apply from accepting dependents before their prerequisites exist.
- `_legacy_pdf_config(base: PdfIngestConfig, *, engine: str | None, use_llm: bool | None) -> PdfIngestConfig` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 630) — The PDF settings for this one-shot pipeline, which only runs local extractors.
- `_resolved_pdf_config(base: PdfIngestConfig, *, engine: str | None, use_llm: bool | None) -> PdfIngestConfig` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 649)
- `_register_canonical_source_locked(root: Path, subject_id: str, source: NormalizedSource, raw_bytes: bytes, content_hash: str, *, clock: Clock | None) -> RegisteredSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1010)
- `_checkpointed_window_proposal(repository: Repository, key: str) -> AuthoringProposal | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1065) — Return a window's saved proposal, discarding one that no longer validates.
- `_validate_explicit_kind(kind: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1109)
- `_validate_textbook_targets(vault, subject_id: str | None, learning_object_ids: list[str]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1114)
- `_validate_active_goal(vault, goal_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1135)
- `_validate_usable_source(chunks: list[SourceChunk], min_content_chars: int) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1144)
- `_canonical_fetch_uri(source: str, kind: SourceKind) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1150)
- `_fetch_url(root: Path, fetch_uri: str, *, original_uri: str, clock: Clock | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1162)
- `_fetch_youtube_transcript(source: str, *, allow_auto_captions: bool, clock: Clock | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1202)
- `_transcript_cues_to_raw_data(fetched: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1233)
- `_normalize_website_like(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1259)
- `_normalize_arxiv_html(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1286)
- `_normalize_youtube(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1315)
- `_extract_html_markdown(raw_html: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1345)
- `_arxiv_native_locator_overrides(raw_html: str) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1366)
- `_native_arxiv_label(element_id: str, text: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1394)
- `_dedupe_native_overrides(overrides: list[dict[str, str]]) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1409)
- `_apply_arxiv_native_locator_overrides(chunks: list[SourceChunk], labels: dict[str, Any]) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1421)
- `class _HTMLMarkdownParser(HTMLParser)` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1454)
- `_canonical_context(vault, registered: RegisteredSource, source: NormalizedSource, window: IngestWindow, *, target_learning_object_ids: list[str], instructions: str | None) -> CanonicalIngestContext` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1546)
- `_proposal_with_locator_validation(proposal: AuthoringProposal, registered: RegisteredSource, window: IngestWindow) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1588)
- `_missing_source_ref_ids(proposal: AuthoringProposal, known_ref_ids: set[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1618)
- `_canonical_source_ref_from_id(ref_id: str, registered: RegisteredSource, window: IngestWindow) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1630)
- `_chunk_locator_from_ref_id(ref_id: str, registered: RegisteredSource, window: IngestWindow) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1649) — Recover a chunk locator from a source-ref id that embeds one.
- `_time_locator_from_ref_id(ref_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1675)
- `_existing_registered_source(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> RegisteredSource | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1693)
- `_previous_registered_sources(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1716)
- `_locator_hashes(chunks: list[SourceChunk]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1755)
- `_locator_resolves(chunks: list[SourceChunk], locator: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1762)
- `_parse_time_locator(locator: str) -> tuple[float, float] | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1825)
- `_grounded_entity_refs(vault) -> list[tuple[str, str, str | None, list[Any]]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1836)
- `_resolve_subject(root: Path, source: NormalizedSource, subject_id: str | None, kind: SourceKind, learning_object_ids: list[str], content_hash: str, *, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1860)
- `_establish_goal_linkage(root: Path, subject_id: str, title: str, proposal: AuthoringProposal, *, goal_id: str | None, default_priority: float, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1890)
- `_establish_goal_linkage_locked(root: Path, subject_id: str, title: str, proposal: AuthoringProposal, *, goal_id: str | None, default_priority: float, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1914)
- `_proposal_learning_object_concepts(proposal: AuthoringProposal) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1985)
- `_goal_scope_concepts(goal: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1997) — Concept scope of a raw goals.yaml entry, tolerating legacy v1 form.
- `_result_from_existing_batch(agent_run: dict[str, Any], batch: dict[str, Any] | None, registered: RegisteredSource, source_kind: SourceKind, content_hash: str) -> IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2006)
- `_retain_raw_bytes(root: Path, note_id: str, content_hash: str, raw_bytes: bytes) -> Path` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2028)
- `_unique_note_id(vault, title: str, content_hash: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2038)
- `_unique_goal_id(goals: list[Any], subject_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2051)
- `_is_pdf_fetch(fetched: FetchResult) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2073)
- `_pdf_fetch_result(root: Path, pdf_bytes: bytes, fetched: FetchResult, pdf_config: PdfIngestConfig | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2082)
- `_pdf_markdown(root: Path, pdf_bytes: bytes, pdf_config: PdfIngestConfig | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2099)
- `_content_type_for_path(path: Path) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2108)
- `_looks_like_markdown(fetch_result: FetchResult) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2117)
- `_decode_bytes(raw: bytes) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2123)
- `_normalize_markdown(markdown: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2132)
- `_first_markdown_heading(markdown: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2148)
- `_strip_markdown(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2156)
- `_title_from_uri(uri: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2160)
- `_title_from_slug(slug: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2166)
- `_collapse_ws(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2170)
- `_collapse_block(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2174)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `SourceIngestionError`, `ingest_canonical_source`; statically calls `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ingest_canonical_source`, `module`; statically calls `fetch_source`, `ingest_canonical_source`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `SourceChunk`, `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`; statically calls `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `PdfIngestConfig`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/pipeline/ai_contracts|learnloop.content.pipeline.ai_contracts]] — imports `CANONICAL_INGEST_PROMPT_VERSION`, `CanonicalIngestContext`, `ExtractionPlan`, `SourceChunk`, `SourceKind`, `canonical_ingest_prompt`; calls `CanonicalIngestContext`, `ExtractionPlan`, `SourceChunk`, `canonical_ingest_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AuthoringProposal`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `auto_apply_rows`, `proposal_item_row`; calls `auto_apply_rows`, `proposal_item_row`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `PdfExtractionError`, `extract_pdf_markdown`; calls `extract_pdf_markdown`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `kebab_case`, `new_ulid`, `snake_case`; calls `kebab_case`, `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `stored_original_path`; calls `stored_original_path`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `ResolvedSource`, `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `load_vault`; calls `add_subject`, `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; calls `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `html`, `json`, `pathlib`, `re`, `typing`, `urllib`
- Third party: `bs4`, `pydantic`, `trafilatura`, `youtube_transcript_api`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_seeding.py](../../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_ingest_exam_instructions_reach_context_and_tags_apply`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_canonical_lane_does_not_auto_apply_gated_items`
  - `test_reachability_summary_reports_minted_cells`
- [tests/test_ingest_ownership.py](../../../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_replaced_ingest_cannot_publish_its_source_note_or_goal_linkage`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_legacy_one_shot_pipeline_never_uses_the_native_engine`
- [tests/test_pdf_extraction.py](../../../../../../../tests/test_pdf_extraction.py) — direct import
  - `test_resolved_pdf_config_overrides_and_validates`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_source_ingestion.py](../../../../../../../tests/test_source_ingestion.py) — direct import
  - `test_composite_note_id_locator_source_ref_resolves`
  - `test_ingest_does_not_link_goal_to_pending_proposed_concept`
  - `test_ingest_invalid_returned_locator_blocks_auto_apply`
  - `test_ingest_local_html_registers_source_and_auto_applies`
  - `test_ingest_local_markdown_runs_the_canonical_proposal_pipeline`
  - `test_ingest_reports_user_visible_pipeline_phases`
  - `test_ingest_retries_with_stronger_ai_provider_on_validation_failure`
  - `test_ingest_same_canonical_source_is_noop_after_completed_run`
  - `test_regrounded_update_clears_active_source_span_events`
  - `test_reingest_changed_source_records_stale_source_events`
  - `test_reject_auto_applied_ingest_items_deactivates_created_entities`
  - `test_section_level_source_ref_resolves_to_child_chunks`
  - `test_youtube_missing_source_ref_accepts_registered_note_timecoded_id`
  - `test_youtube_missing_source_ref_is_reconstructed_from_timecoded_id`
  - `test_youtube_missing_source_ref_without_timecoded_id_stays_invalid`
  - `test_youtube_time_range_hash_covers_spanned_caption_text`
  - `test_youtube_time_range_source_refs_can_span_caption_cues`
- [tests/test_source_ingestion_adapters.py](../../../../../../../tests/test_source_ingestion_adapters.py) — direct import
  - `test_arxiv_html_normalizer_captures_descriptor_fields`
  - `test_pdf_source_is_normalized_to_markdown`
  - `test_pdf_without_text_layer_raises`
  - `test_source_kind_detection_handles_special_cases`
  - `test_textbook_ingest_requires_existing_anchor_and_passes_constraints`
  - `test_youtube_fetcher_supports_current_transcript_api`
  - `test_youtube_normalizer_uses_timestamp_locators`
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_legacy_path_without_ir_unchanged`
  - `test_legacy_window_checkpoint_that_no_longer_validates_is_discarded`
  - `test_v2lite_retry_resumes_from_retained_bytes_without_fetching`
- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — direct import
  - `test_legacy_locators_still_resolve_after_backfill`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change source ingestion policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/source_ingestion.py](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
