---
title: "learnloop.content.pipeline.source_ingestion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/source_ingestion.py"
source_paths:
  - "src/learnloop/content/pipeline/source_ingestion.py"
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
| Source lines | 2055 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_canonical_ingest(client: AIProviderClient, context: CanonicalIngestContext) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 42) — Run the feature-owned canonical-ingest operation.
- `class SourceIngestionError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 58)
- `class FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 63)
- `class CaptionCue` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 76)
- `class NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 83)
- `class RegisteredSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 97)
- `class IngestWindow` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 105)
- `class IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 111)
  - `as_dict(self) -> dict[str, Any]` (line 134; public)
- `class SourceChangeAnalysis` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 156)
- `ingest_canonical_source(root: Path, source: str, codex_client: AIProviderClient, *, kind: KindOption='auto', subject_id: str | None=None, learning_object_ids: list[str] | None=None, goal_id: str | None=None, allow_auto_captions: bool | None=None, instructions: str | None=None, model: str | None=None, codex_revision: str | None=None, retry_client: AIProviderClient | None=None, retry_model: str | None=None, retry_provider_revision: str | None=None, purpose: str='canonical_ingest', pdf_engine: str | None=None, pdf_use_llm: bool | None=None, ir_markdown: str | None=None, clock: Clock | None=None, progress: IngestProgress | None=None) -> IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 161)
- `detect_source_kind(source: str, *, kind: KindOption='auto', learning_object_ids: list[str] | None=None) -> SourceKind` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 606)
- `resolve_canonical_source(source: str, *, kind: KindOption='auto', learning_object_ids: list[str] | None=None) -> tuple[ResolvedSource, SourceKind]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 615)
- `fetch_source(root: Path, source: str, *, kind: SourceKind, allow_auto_captions: bool, pdf_config: PdfIngestConfig | None=None, clock: Clock | None=None, progress: IngestProgress | None=None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 645)
- `normalize_source(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 693)
- `source_content_hash(markdown: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 701)
- `analyze_source_change(vault, source: NormalizedSource, new_chunks: list[SourceChunk], content_hash: str, *, clock: Clock | None=None) -> SourceChangeAnalysis` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 706)
- `chunk_normalized_source(source: NormalizedSource) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 786)
- `chunk_markdown(markdown: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 807)
- `build_ingest_windows(chunks: list[SourceChunk], *, window_char_cap: int) -> list[IngestWindow]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 875)
- `canonical_ingest_context_hash(canonical_uri: str, content_hash: str, source_kind: SourceKind, target_learning_object_ids: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 911)
- `register_canonical_source(root: Path, subject_id: str, source: NormalizedSource, raw_bytes: bytes, content_hash: str, *, clock: Clock | None=None) -> RegisteredSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 926)
- `merge_window_proposals(proposals: list[AuthoringProposal]) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 981)
- `chunks_for_note_body(kind: SourceKind, body: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1637)
- `locator_hash_for_ref(chunks: list[SourceChunk], locator: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1673)
- `child_chunks_for_locator(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1690)
- `caption_chunks_for_time_range(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1698)
- `source_youtube_video_id(source: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1941)

## Internal implementation anchors

- `_run_ingest_windows(client: AIProviderClient, vault, registered: RegisteredSource, normalized: NormalizedSource, windows: list[IngestWindow], *, target_learning_object_ids: list[str], instructions: str | None, progress: IngestProgress | None=None) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 438)
- `_report_progress(progress: IngestProgress | None, phase: str, **details: Any) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 470)
- `_proposal_with_change_summary(proposal: AuthoringProposal, summary: str) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 475)
- `_agent_provider_fields(client: AIProviderClient, *, model: str | None, provider_revision: str | None) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 485)
- `_reachability_summary(vault, repository, learning_object_ids: list[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 505) — Verdict counts for the just-applied LOs' contract cells (Meas §5.8.2).
- `_apply_instrument_gates(rows: list[dict[str, Any]], vault, repository, grading_client) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 535) — Stage-5.3/6 instrument gates on the canonical-ingest lane.
- `_downgrade_unready_auto_apply(rows: list[dict[str, Any]], vault) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 552) — Keep auto-apply from accepting dependents before their prerequisites exist.
- `_resolved_pdf_config(base: PdfIngestConfig, *, engine: str | None, use_llm: bool | None) -> PdfIngestConfig` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 587)
- `_validate_explicit_kind(kind: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1012)
- `_validate_textbook_targets(vault, subject_id: str | None, learning_object_ids: list[str]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1017)
- `_validate_active_goal(vault, goal_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1038)
- `_validate_usable_source(chunks: list[SourceChunk], min_content_chars: int) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1047)
- `_canonical_fetch_uri(source: str, kind: SourceKind) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1053)
- `_fetch_url(root: Path, fetch_uri: str, *, original_uri: str, clock: Clock | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1065)
- `_fetch_youtube_transcript(source: str, *, allow_auto_captions: bool, clock: Clock | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1105)
- `_transcript_cues_to_raw_data(fetched: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1136)
- `_normalize_website_like(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1162)
- `_normalize_arxiv_html(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1189)
- `_normalize_youtube(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1218)
- `_extract_html_markdown(raw_html: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1248)
- `_arxiv_native_locator_overrides(raw_html: str) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1269)
- `_native_arxiv_label(element_id: str, text: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1297)
- `_dedupe_native_overrides(overrides: list[dict[str, str]]) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1312)
- `_apply_arxiv_native_locator_overrides(chunks: list[SourceChunk], labels: dict[str, Any]) -> list[SourceChunk]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1324)
- `class _HTMLMarkdownParser(HTMLParser)` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1357)
- `_canonical_context(vault, registered: RegisteredSource, source: NormalizedSource, window: IngestWindow, *, target_learning_object_ids: list[str], instructions: str | None) -> CanonicalIngestContext` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1449)
- `_proposal_with_locator_validation(proposal: AuthoringProposal, registered: RegisteredSource, window: IngestWindow) -> AuthoringProposal` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1491)
- `_missing_source_ref_ids(proposal: AuthoringProposal, known_ref_ids: set[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1521)
- `_canonical_source_ref_from_id(ref_id: str, registered: RegisteredSource, window: IngestWindow) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1533)
- `_chunk_locator_from_ref_id(ref_id: str, registered: RegisteredSource, window: IngestWindow) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1552) — Recover a chunk locator from a source-ref id that embeds one.
- `_time_locator_from_ref_id(ref_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1578)
- `_existing_registered_source(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> RegisteredSource | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1596)
- `_previous_registered_sources(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1619)
- `_locator_hashes(chunks: list[SourceChunk]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1658)
- `_locator_resolves(chunks: list[SourceChunk], locator: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1665)
- `_parse_time_locator(locator: str) -> tuple[float, float] | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1728)
- `_grounded_entity_refs(vault) -> list[tuple[str, str, str | None, list[Any]]]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1739)
- `_resolve_subject(root: Path, source: NormalizedSource, subject_id: str | None, kind: SourceKind, learning_object_ids: list[str], content_hash: str, *, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1763)
- `_establish_goal_linkage(root: Path, subject_id: str, title: str, proposal: AuthoringProposal, *, goal_id: str | None, default_priority: float, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1793)
- `_proposal_learning_object_concepts(proposal: AuthoringProposal) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1864)
- `_goal_scope_concepts(goal: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1876) — Concept scope of a raw goals.yaml entry, tolerating legacy v1 form.
- `_result_from_existing_batch(agent_run: dict[str, Any], batch: dict[str, Any] | None, registered: RegisteredSource, source_kind: SourceKind, content_hash: str) -> IngestResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1885)
- `_retain_raw_bytes(root: Path, note_id: str, content_hash: str, raw_bytes: bytes) -> Path` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1907)
- `_unique_note_id(vault, title: str, content_hash: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1917)
- `_unique_goal_id(goals: list[Any], subject_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1930)
- `_is_pdf_fetch(fetched: FetchResult) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1952)
- `_pdf_fetch_result(root: Path, pdf_bytes: bytes, fetched: FetchResult, pdf_config: PdfIngestConfig | None) -> FetchResult` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1961)
- `_pdf_markdown(root: Path, pdf_bytes: bytes, pdf_config: PdfIngestConfig | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1978)
- `_content_type_for_path(path: Path) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1987)
- `_looks_like_markdown(fetch_result: FetchResult) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 1996)
- `_decode_bytes(raw: bytes) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2002)
- `_normalize_markdown(markdown: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2011)
- `_first_markdown_heading(markdown: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2027)
- `_strip_markdown(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2035)
- `_title_from_uri(uri: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2039)
- `_title_from_slug(slug: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2045)
- `_collapse_ws(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2049)
- `_collapse_block(text: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/source_ingestion.py), line 2053)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `SourceIngestionError`, `ingest_canonical_source`; statically calls `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ingest_canonical_source`, `module`; statically calls `fetch_source`, `ingest_canonical_source`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `SourceChunk`, `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`; statically calls `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
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
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `ResolvedSource`, `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `load_vault`; calls `add_subject`, `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; calls `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `html`, `json`, `pathlib`, `re`, `typing`, `urllib`
- Third party: `bs4`, `trafilatura`, `youtube_transcript_api`

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
