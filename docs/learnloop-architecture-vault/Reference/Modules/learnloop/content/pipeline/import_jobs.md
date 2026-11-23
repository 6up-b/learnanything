---
title: "learnloop.content.pipeline.import_jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/import_jobs.py"
source_paths:
  - "src/learnloop/content/pipeline/import_jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.import_jobs module"
  - "src/learnloop/content/pipeline/import_jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.import_jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.import_jobs` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: The import and extraction job types: ``import``, ``auto_study_map``, ``legacy_ingest`` and ``exam_ingest``, and ``extraction_repair``, with the acquisition and extraction defaults the runner's services fall back on.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py) |
| Source lines | 1662 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `default_fetch(source: str, category: str, ctx: JobContext) -> FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 56) — Read raw bytes for one acquisition.
- `glm_upload_estimate(ctx: JobContext, fetched: FetchedBytes) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 247) — Pages and the estimated cost of reading this file with hosted GLM-OCR (``glm_ocr.estimate``), for the card's z.ai OK line (re-read safety item 5): the pages the import asks for, else every page of the file.
- `default_extract(fetched: FetchedBytes, category: str, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 364) — Produce Document IR from fetched bytes using the M1 extractor providers.
- `default_extraction_identity(fetched: FetchedBytes, category: str, ctx: JobContext) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 461) — Describe the chosen extractor before running it, making cache hits cheap.
- `class NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 586) — A resolved native-multimodal route: which chat provider ingests media.
- `default_run_legacy_ingest(*, vault_root: Path, source: str, subject_id: str, mode: str, progress: Callable[[str, dict[str, Any]], None] | None, clock: Clock | None, ir_markdown: str | None=None, resume_extraction_id: str | None=None, **_ignored: Any) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1043) — Run the legacy one-shot pipeline in-process with a ready provider client.
- `handle_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1129) — import: fetch -> register artifact/revision -> extract to IR -> persist -> health.
- `handle_legacy_ingest(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1357) — legacy_ingest: wrap the existing one-shot pipeline as one durable job so the current single-source UX keeps working (Quick add compatibility, §6.1).
- `handle_extraction_repair(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1444) — extraction_repair: a consent-gated, page-range re-extraction (§2.5).
- `handle_auto_study_map(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1649) — auto_study_map: plan the automatic question build after an Add (UX Phase 1).

### Module constants

- `_LEGACY_PHASE_TO_LADDER` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 30)
- `_LEGACY_PHASE_MESSAGE` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 38)
- `_UPLOAD_FLOW_MESSAGES` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 291)
- `_PLAIN_IMPORT_UPLOAD_MESSAGES` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 301)
- `_PLAIN_IMPORT_SCAN_MESSAGE` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 307)
- `GLM_NEEDS_UPLOAD_OK` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 312)
- `_ROUTED_AUDIO_FORMAT_MESSAGE` ([src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 783)

## Internal implementation anchors

- `_optional_int(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 47)
- `_fetch_metadata(source: str, category: str) -> tuple[str | None, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 89) — Best-effort human-readable (title, authors) for the fetched source.
- `_pdf_payload_config(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 109) — The effective PDF extraction config for one import job.
- `_local_repair(ctx: JobContext) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 145) — Whether this reading must stay on this computer: an extraction repair whose consent is local (GLM-OCR third review F10, set by :func:`handle_extraction_repair`).
- `_repair_is_local(consent: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 155) — A repair consent that approved no external service: OutlineAndPlan's repair without "external VLM" and ``learnloop repair-extraction`` without ``--use-llm`` both send ``external: false`` and provider ``local``.
- `_glm_settings(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 164) — The vault's ``[ingest.pdf.glm_ocr]`` settings (not hashed); loading the config also loads the machine's settings.env, where the key lives.
- `_glm_backend(ctx: JobContext, pdf_config: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 176)
- `_hosted_marker_selected(pdf_config: Mapping[str, Any], *, glm_selected: bool=False) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 184) — The explicit Datalab debug runtime: Marker runs on Datalab's servers (only when GLM-OCR, which ``auto`` prefers, is not selected).
- `_is_document(fetched: FetchedBytes, category: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 196) — A PDF, PNG or JPG: read by the document extractors (GLM-OCR, Marker, pypdf), whatever page or link it came from.
- `_image_config(pdf_config: dict[str, Any], fetched: FetchedBytes) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 208)
- `_document_extractor(ctx: JobContext, pdf_config: Mapping[str, Any], fetched: FetchedBytes) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 214) — The extractor for a PDF/PNG/JPG import, its upload guarded.
- `_extraction_interrupt(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 267) — Checked before each request GLM-OCR sends (every window, every retry; second review F4): a cancelled import stops there (never a fallback; the runner records the job as cancelled).
- `_upload_allowed(ctx: JobContext, flow: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 284)
- `_guard_file_upload(ctx: JobContext, flow: str, *, plain_message: str | None=None, details: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 315) — Before a whole file leaves the computer (UX Phase 1 review F1): an Add (which asked the learner nothing per book) uploads only after the separate OK for whole files (spec §6.6: the connection's OK covers passages and answers only).
- `_extract_pdf_locally(fetched: FetchedBytes, extractor: Any, pdf_config: Mapping[str, Any], context: Any) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 340) — Run the extractor with the registry's fallback chain (§2.9): under ``auto``, GLM-OCR degrades to local Marker or pypdf and Marker to pypdf, each with a health flag; an explicitly chosen engine fails as itself.
- `_found_no_text(exc: BaseException) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 357) — A local reading that found no text layer at all (a scanned PDF).
- `_audio_ingest_config(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 573) — The vault's [ingest.audio] settings (defaults when the vault is gone).
- `_native_readiness(ctx: JobContext, modality: str, *, requested: bool | None=None) -> tuple[Any, bool] | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 595) — The shared readiness judgement (learnloop.ai.native_media) for this vault plus the ``fallback_when_unavailable`` opt-in, read from ONE config load so the two can never come from different versions of learnloop.toml.
- `_route_from_readiness(readiness: Any) -> NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 614)
- `class _NativeDecision` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 623) — What happens to media whose modality is routed natively.
- `_decide_native(ctx: JobContext, modality: str, *, requested: bool | None=None, unavailable_code: str) -> _NativeDecision | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 635) — PURE config decision shared by identity and extraction.
- `_add_health_flag(ir: Any, flag: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 669)
- `_native_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 675)
- `_transcription_media_route(ctx: JobContext) -> NativeMediaRoute | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 697) — Resolve an explicitly configured chat-transcription route without I/O.
- `_transcription_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 739) — Build the configured transcription client through the composition root.
- `_audio_filename(fetched: FetchedBytes) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 772)
- `_extract_audio(fetched: FetchedBytes, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 790) — Audio → timestamped transcript → the same time_range IR captions use.
- `_extract_audio_transcription(fetched: FetchedBytes, ctx: JobContext, chat_format: str | None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 823) — The non-native audio path: the dedicated transcription route, else the endpoint.
- `_extract_audio_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute, chat_format: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 867)
- `_extract_audio_routed(fetched: FetchedBytes, ctx: JobContext, config: Any, route: NativeMediaRoute, chat_format: str | None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 896) — Transcribe through the dedicated task route with no endpoint fallback.
- `_chat_transcript_to_ir(transcript: Any, ctx: JobContext, *, provider_label: str, empty_code: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 947) — Chat-model MediaTranscript segments → the same time_range IR the endpoint transcription path produces (shared native/routed-chat tail).
- `_extract_pdf_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 980) — PDF → chat file part → Markdown → IR ([ingest.pdf] engine "native").
- `_caption_cues(text: str) -> list[dict[str, Any]] | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1021) — Decode fetched YouTube caption bytes ({"cues": [...]} or a bare list).
- `_record_import_source(ctx: JobContext, source_id: str, revision_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1089) — Name the book on its import once the book exists (GLM-OCR third review F2): a link Add's or a plain import's job learns its book only here, and a failed one has no result, so without it the book's card never finds the import that waits for an OK.
- `_note_carry_owed(ctx: JobContext, revision_id: str, extraction_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1106) — Before a reading of a revision that already has one completes (or a cached one is carried again): the job's payload names the carry-over it owes (re-read safety, Codex review F7; ``reread.carry_owed``).
- `_carry_noted(ctx: JobContext, extraction_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1122)
- `_actual_model_versions(identity: Mapping[str, Any], ir: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1325) — The model versions of the extractor that really read the document.
- `_compose_display_title(title: str | None, authors: Sequence[str]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1345) — Assemble the artifact's stored label: "<title> — <author>" when both are known, the title alone when there is no author, and ``None`` (→ URL fallback) when the fetch captured no title at all.
- `_legacy_ir_extraction_id(ctx: JobContext) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1408)
- `_legacy_ir_markdown(ctx: JobContext, extraction_id: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1423) — Render the IR from this job's completed ``import`` dependency, if any (§2.3).
- `_repair_pdf_config(options: Mapping[str, Any], pages: list[int]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1570)
- `_validate_page_selection(raw_bytes: bytes, pages: list[int]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1585) — Refuse out-of-range page selections BEFORE any expensive extraction.
- `_normalize_pages(raw: Any) -> list[int]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1608)
- `_latest_completed_extraction(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1628)
- `_units_touching(ir: Any, pages: list[int]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/import_jobs.py), line 1637)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]] — imports `_optional_int`; statically calls `_optional_int`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `module`; calls `require`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`; calls `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`
- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `native_modality_readiness`; calls `native_modality_readiness`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`; calls `SpendCancelled`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `MEDIA_TRANSCRIPTION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AudioIngestConfig`; calls `AudioIngestConfig`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `file_upload_allowed`, `pdf_metadata_title`, `run_auto_study_map`; calls `file_upload_allowed`, `pdf_metadata_title`, `run_auto_study_map`
- [[Reference/Modules/learnloop/content/pipeline/job_contracts|learnloop.content.pipeline.job_contracts]] — imports `FetchedBytes`, `IngestRunnerError`; calls `FetchedBytes`, `IngestRunnerError`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `CARRY_DONE_KEY`, `CARRY_OWED_KEY`, `_pdf_page_count`, `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`; calls `_pdf_page_count`, `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobContext`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `ingest_canonical_source`, `module`; calls `fetch_source`, `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `register_source_revision`; calls `register_source_revision`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `exam_ingest_instructions`; calls `exam_ingest_instructions`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `ExtractionFallbackFailed`, `MarkerUnavailableError`, `captions_to_ir`, `document_pdf_config`, `extract_with_fallback`, `fallback_model_versions`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`; calls `captions_to_ir`, `document_pdf_config`, `extract_with_fallback`, `fallback_model_versions`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`; calls `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `estimate`, `is_image_document`, `selected_backend`; calls `estimate`, `is_image_document`, `selected_backend`
- [[Reference/Modules/learnloop/ingest/extractors/web_page|learnloop.ingest.extractors.web_page]] — imports `WEB_PAGE_EXTRACTOR_VERSION`, `page_markdown`; calls `page_markdown`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `extraction_request_hash`, `extraction_result_hash`; calls `extraction_request_hash`, `extraction_result_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `IR_SCHEMA_VERSION`, `compose_extraction_runs`, `render_ir_markdown`; calls `compose_extraction_runs`, `render_ir_markdown`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/ingest/source_kinds|learnloop.ingest.source_kinds]] — imports `source_kind`; calls `source_kind`
- [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] — imports `TranscriptionFailed`, `TranscriptionUnavailable`, `transcribe_audio`; calls `transcribe_audio`
- [[Reference/Modules/learnloop/ingest/transcripts|learnloop.ingest.transcripts]] — imports `TranscriptCue`, `detect_transcript_format`, `parse_transcript`; calls `TranscriptCue`, `detect_transcript_format`, `parse_transcript`
- [[Reference/Modules/learnloop/ingest/youtube|learnloop.ingest.youtube]] — imports `youtube_oembed_metadata`, `youtube_video_id`; calls `youtube_oembed_metadata`, `youtube_video_id`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `trace_scope`
- [[Reference/Modules/learnloop/source_retrieval/jobs|learnloop.source_retrieval.jobs]] — imports `queue_source_vectors`; calls `queue_source_vectors`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `logging`, `os`, `pathlib`, `re`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other`
  - `test_an_image_import_needs_glm_and_reads_with_it`
  - `test_identity_hashes_the_choice_not_endpoints_prices_or_timeouts`
  - `test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer`
  - `test_r2_f4_cancelling_stops_the_windows_not_yet_sent`
  - `test_remote_documents_download_raw_so_nothing_is_read_before_the_ok`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_audio_extract_routes_transcription_to_time_range_ir`
  - `test_audio_extraction_identity_tracks_model_and_endpoint`
  - `test_audio_oversize_rejected_before_any_upload`
  - `test_audio_transcription_mode_uses_endpoint_without_native_route`
  - `test_audio_transcription_unavailable_is_typed_retryable`
  - `test_compose_display_title_variants`
  - `test_explicit_transcription_route_uses_named_profile_without_legacy_switch`
  - `test_fetch_metadata_only_resolves_youtube`
  - `test_native_audio_failure_is_typed_and_never_switches_routes`
  - `test_native_audio_route_transcribes_via_chat_provider`
  - `test_native_audio_unready_fails_closed_by_default`
  - `test_native_audio_unready_falls_back_when_opted_in`
  - `test_native_audio_unready_route_is_irrelevant_for_non_chat_containers`
  - `test_native_audio_unsupported_container_falls_back_to_endpoint`
  - `test_native_pdf_engine_extracts_markdown_via_chat_provider`
  - `test_native_pdf_engine_rejects_a_repair_page_range`
  - `test_native_pdf_engine_rejects_page_selection`
  - `test_native_pdf_engine_without_capable_route_is_typed`
  - `test_native_pdf_fallback_when_unavailable_uses_local_with_health_flag`
  - `test_native_pdf_rejects_oversized_file`
  - `test_native_route_takes_precedence_over_openrouter_transcription_setting`
  - `test_openrouter_transcription_missing_key_is_typed`
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
  - `test_openrouter_transcription_unsupported_container_errors`
  - `test_routed_transcription_keeps_the_chat_upload_size_cap`
  - `test_transcription_route_never_falls_back_to_an_unconsented_provider`
  - `test_web_import_routes_html_normalizer_not_raw_text`
  - `test_youtube_import_routes_caption_cues_to_time_range_ir`
- [tests/test_ingest_transcripts.py](../../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_default_extract_routes_caption_text_to_transcript_ir`
- [tests/test_job_types.py](../../../../../../../tests/test_job_types.py) — direct import
  - `test_the_job_contracts_are_one_set_of_objects_through_every_path`
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_an_import_the_retired_choice_refused_offers_to_get_it_ready`
  - `test_whole_file_extraction_is_no_longer_narrowed_for_the_retired_choice`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_ux11_html_extraction.py](../../../../../../../tests/test_ux11_html_extraction.py) — direct import
  - `test_ux11_hidden_and_collapsed_parts_are_treated_as_the_old_extraction_treated_them`
  - `test_ux11_mathml_and_script_math_reach_the_text_as_tex`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f1_sending_a_whole_recording_out_waits_for_its_own_ok`

## Modification guidance

- Change import jobs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/import_jobs.py](../../../../../../../src/learnloop/content/pipeline/import_jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
