---
title: "learnloop_sidecar.handlers.reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop_sidecar.handlers.reader module"
  - "src/learnloop_sidecar/handlers/reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reader` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: P2 reader-dialogue sidecar RPC (spec §7.6, U-033; design B.11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py) |
| Source lines | 1633 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderAskInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 80)
- `reader_ask(ctx: SidecarContext, params: ReaderAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 96)
- `class ReaderAskHistoryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 154)
- `reader_ask_history(ctx: SidecarContext, params: ReaderAskHistoryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 159) — List the durable, completed Ask exchanges for the open source.
- `class ReaderSetAnswerModeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 169)
- `reader_set_answer_mode(ctx: SidecarContext, params: ReaderSetAnswerModeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 176)
- `class ReaderPresentQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 194)
- `reader_present_question(ctx: SidecarContext, params: ReaderPresentQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 202)
- `class ReaderSubmitQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 221)
- `reader_submit_question(ctx: SidecarContext, params: ReaderSubmitQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 229)
- `class ReaderSkipQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 241)
- `reader_skip_question(ctx: SidecarContext, params: ReaderSkipQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 246)
- `class ReaderChooseDispositionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 256)
- `reader_choose_disposition(ctx: SidecarContext, params: ReaderChooseDispositionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 266)
- `class ReaderRestoreSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 288)
- `reader_restore_source(ctx: SidecarContext, params: ReaderRestoreSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 296)
- `class ReaderRoutingPriorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 315)
- `reader_routing_prior(ctx: SidecarContext, params: ReaderRoutingPriorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 321)
- `reader_prompt_contract(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 332)
- `class ReaderRenderViewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 355)
- `reader_render_view(ctx: SidecarContext, params: ReaderRenderViewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 363)
- `class ReaderGuidePlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 387)
- `reader_guide_plan(ctx: SidecarContext, params: ReaderGuidePlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 393) — Return optional section-break checks and a personalized second pass.
- `class ReaderBlockHealthInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 417)
- `reader_block_health(ctx: SidecarContext, params: ReaderBlockHealthInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 423)
- `class ReaderBlockRegionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 440)
- `reader_block_original_region(ctx: SidecarContext, params: ReaderBlockRegionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 446)
- `class ReaderPdfViewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 451)
- `reader_pdf_view(ctx: SidecarContext, params: ReaderPdfViewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 458) — Tier-2 embedded PDF reader manifest: whether the revision's original PDF is available in the vault's content-addressed store (backfilling it from a still-present local original on demand), the store file name the llpdf:// protocol serves, and per-block page/bbox geometry (PDF po…
- `class ReaderTranslateSelectionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 516)
- `reader_translate_selection(ctx: SidecarContext, params: ReaderTranslateSelectionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 523)
- `class ReaderCaptureInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 533)
- `reader_capture(ctx: SidecarContext, params: ReaderCaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 547)
- `class ReaderCreateAnnotationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 568)
- `reader_create_annotation(ctx: SidecarContext, params: ReaderCreateAnnotationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 581)
- `class ReaderEditAnnotationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 600)
- `reader_edit_annotation(ctx: SidecarContext, params: ReaderEditAnnotationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 608)
- `class ReaderDeleteIntentInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 620)
- `reader_delete_intent_annotation(ctx: SidecarContext, params: ReaderDeleteIntentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 626)
- `class ReaderReanchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 632)
- `reader_reanchor(ctx: SidecarContext, params: ReaderReanchorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 638)
- `class ReaderAnnotationHistoryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 649)
- `reader_annotation_history(ctx: SidecarContext, params: ReaderAnnotationHistoryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 654)
- `class ReaderSourceAnnotationsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 661)
- `reader_source_annotations(ctx: SidecarContext, params: ReaderSourceAnnotationsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 666)
- `class ReaderOutboxStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 671)
- `reader_outbox_status(ctx: SidecarContext, params: ReaderOutboxStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 676)
- `reader_drain_outbox(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 683)
- `class ReaderInvokePresetInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 704)
- `reader_invoke_preset(ctx: SidecarContext, params: ReaderInvokePresetInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 719)
- `class ReaderSetModeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 741)
- `reader_set_mode(ctx: SidecarContext, params: ReaderSetModeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 748)
- `class ReaderQuestionControlInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 759)
- `reader_question_control(ctx: SidecarContext, params: ReaderQuestionControlInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 767)
- `class ReaderEnqueueRequestInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 779)
- `reader_enqueue_request(ctx: SidecarContext, params: ReaderEnqueueRequestInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 793)
- `class ReaderRequestStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 808)
- `reader_request_status(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 813)
- `reader_cancel_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 819)
- `reader_retry_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 825)
- `class ReaderSourceRequestsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 832)
- `reader_source_requests(ctx: SidecarContext, params: ReaderSourceRequestsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 837)
- `reader_drain_requests(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 843)
- `class ReaderSourceObjectsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 848)
- `reader_source_objects(ctx: SidecarContext, params: ReaderSourceObjectsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 853)
- `class ReaderReviewSourceObjectInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 858)
- `reader_review_source_object(ctx: SidecarContext, params: ReaderReviewSourceObjectInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 864)
- `class ReaderLinkRelationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 875)
- `reader_link_relation(ctx: SidecarContext, params: ReaderLinkRelationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 883)
- `class ReaderProposalInboxInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 896)
- `reader_proposal_inbox(ctx: SidecarContext, params: ReaderProposalInboxInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 902)
- `class ReaderDecideProposalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 907)
- `reader_accept_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 912)
- `reader_reject_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 922)
- `class ReaderAuthorQAInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 948)
- `reader_author_qa(ctx: SidecarContext, params: ReaderAuthorQAInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 960)
- `class ReaderCoachLintInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 974)
- `reader_coach_lint(ctx: SidecarContext, params: ReaderCoachLintInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 981)
- `class ReaderMaintainInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 990)
- `reader_maintain(ctx: SidecarContext, params: ReaderMaintainInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1007)
- `class ReaderArcInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1025)
- `reader_arc(ctx: SidecarContext, params: ReaderArcInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1032) — Create an arc (with ``commitment_id``) or project an existing one (``arc_id``).
- `class ReaderSetDepthPolicyInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1047)
- `reader_set_depth_policy(ctx: SidecarContext, params: ReaderSetDepthPolicyInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1053)
- `class ReaderArcIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1061)
- `reader_pause_arc(ctx: SidecarContext, params: ReaderArcIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1067)
- `class ReaderShrinkEnvelopeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1075)
- `reader_shrink_envelope(ctx: SidecarContext, params: ReaderShrinkEnvelopeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1082)
- `class ReaderPrimeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1095)
- `reader_prime(ctx: SidecarContext, params: ReaderPrimeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1104) — Offer (default) or answer (``answer=True``) an opt-in pretest prime (§10.3).
- `class ReaderRestoreInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1121)
- `reader_restore(ctx: SidecarContext, params: ReaderRestoreInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1129)
- `class ReaderWatchPlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1164)
- `reader_watch_plan(ctx: SidecarContext, params: ReaderWatchPlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1169)
- `class ReaderAuthorSectionQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1279)
- `reader_author_section_question(ctx: SidecarContext, params: ReaderAuthorSectionQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1285)
- `class ReaderGetProgressInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1335)
- `reader_get_progress(ctx: SidecarContext, params: ReaderGetProgressInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1340) — Durable per-section reading progress for one extraction (migration 106).
- `class ReaderMarkSectionProgressInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1351)
- `reader_mark_section_progress(ctx: SidecarContext, params: ReaderMarkSectionProgressInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1361) — Persist section progress; on first completion, trigger progressive practice generation for the section's provenance-linked Learning Objects.
- `class ReaderAuthoredQuestionActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1433)
- `reader_authored_question_action(ctx: SidecarContext, params: ReaderAuthoredQuestionActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1440)
- `class ReaderEscalateAuthoredQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1456)
- `class ReaderImportExerciseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1461)
- `reader_import_exercise(ctx: SidecarContext, params: ReaderImportExerciseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1472) — Queue the exact-exercise slice: the learner's selection (ordered per-block nodes) becomes one background authoring job that writes complete, schedulable PracticeItems around the verbatim exercise text.
- `class ReaderExerciseImportStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1514)
- `reader_exercise_import_status(ctx: SidecarContext, params: ReaderExerciseImportStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1519) — Poll one exercise-import batch.
- `reader_escalate_authored_question(ctx: SidecarContext, params: ReaderEscalateAuthoredQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1546)
- `class ReaderSearchSourcesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1577)
- `reader_search_sources(ctx: SidecarContext, params: ReaderSearchSourcesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1583)
- `class ReaderManualAnchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1588)
- `reader_manual_anchor(ctx: SidecarContext, params: ReaderManualAnchorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1596) — Repair a needs_reanchor annotation with a learner-chosen passage (§4.4).

### Module constants

- `C_ERR` ([src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 945)
- `_TIME_LOCATOR_RE` ([src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1150)

## Internal implementation anchors

- `_require_reader(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 39) — Require an open vault AND the reader enabled (L8).
- `_require_source_reader(repository, source_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 53) — Per-source reader gate (owner ingest-time choice, migration 104): a source opted out of the reader loop (e.g.
- `_source_id_for_extraction(repository, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 68)
- `_parse_time_locator(locator: str | None) -> tuple[float, float | None] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1153)
- `_authored_question_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1259)
- `_progress_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1323)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]] — imports `module`; calls `analyze_block_health`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; calls `ArcError`, `answer_prime`, `create_arc`, `offer_prime`, `pause_arc`, `project_arc`, `set_depth_policy`, `shrink_envelope`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `youtube_video_id`; calls `youtube_video_id`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `backfill_original`, `is_pdf_file`, `stored_original_path`; calls `backfill_original`, `is_pdf_file`, `stored_original_path`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `module`; calls `append_annotation`, `delete_intent_annotation`, `edit_annotation`, `manual_anchor`, `reanchor_annotation`, `translate_selection`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `module`; calls `author_qa`, `coach_lint`, `maintain`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; calls `capture`, `drain_outbox`, `invoke_preset`, `outbox_status`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `administer_reading_question`, `ask`, `ask_history`, `choose_disposition`, `question_control`, `reader_enabled`, `reader_prompt_contract`, `restore_source`, `routing_prior_projection_v1`, `set_answer_mode`, `set_mode`, `skip_reading_question`, `submit_reading_question`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `module`; calls `build_guide_plan`, `goal_for_item`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `section_generation_candidates`, `source_refs_for_section`; calls `section_generation_candidates`, `source_refs_for_section`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `escalate`, `record_action`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `cancel_request`, `drain_requests`, `enqueue_request`, `request_status`, `retry_request`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `module`; calls `restore`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `accept_mapping`, `link_relation`, `proposal_inbox`, `reject_mapping`, `review_source_object`, `source_objects_for_source`
- [[Reference/Modules/learnloop/reader/source_render_views|learnloop.reader.source_render_views]] — imports `module`; calls `render_payload`, `resolve_or_create_render_view`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `module`; calls `search_sources`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `module`; calls `build_block_region`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `QuestionLimitReached`, `TutorQAError`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`; calls `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
