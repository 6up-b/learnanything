---
title: "learnloop_sidecar.handlers.reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader.py"
source_commit: "2079aa1eb02ced81c4ed4449672db9e2e437e45b"
source_commit_timestamp: "2026-11-04T16:51:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 2629 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2079aa1eb02ced81c4ed4449672db9e2e437e45b` |
| Commit timestamp | `2026-11-04T16:51:26-05:00` |

## Public API

- `class ReaderAskInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 92)
- `reader_ask(ctx: SidecarContext, params: ReaderAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 140)
- `class ReaderAskHistoryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 286)
- `reader_ask_history(ctx: SidecarContext, params: ReaderAskHistoryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 291) — List the durable, completed Ask exchanges for the open source.
- `class ReaderSetAnswerModeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 308)
- `reader_set_answer_mode(ctx: SidecarContext, params: ReaderSetAnswerModeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 318)
- `class ReaderPresentQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 339)
- `reader_present_question(ctx: SidecarContext, params: ReaderPresentQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 347)
- `class ReaderSubmitQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 366)
- `reader_submit_question(ctx: SidecarContext, params: ReaderSubmitQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 374)
- `class ReaderSkipQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 386)
- `reader_skip_question(ctx: SidecarContext, params: ReaderSkipQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 391)
- `class ReaderChooseDispositionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 401)
- `reader_choose_disposition(ctx: SidecarContext, params: ReaderChooseDispositionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 411)
- `class ReaderRestoreSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 433)
- `reader_restore_source(ctx: SidecarContext, params: ReaderRestoreSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 441)
- `class ReaderRoutingPriorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 461)
- `reader_routing_prior(ctx: SidecarContext, params: ReaderRoutingPriorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 467)
- `reader_prompt_contract(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 478)
- `class ReaderRenderViewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 553)
- `reader_render_view(ctx: SidecarContext, params: ReaderRenderViewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 561)
- `class ReaderSavedPlaceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 601)
- `reader_saved_place(ctx: SidecarContext, params: ReaderSavedPlaceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 614) — Where a saved reading place lands on the reading the Reader has open (``to_extraction_id``; the book's current reading when not given).
- `class ReaderGuidePlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 658)
- `reader_guide_plan(ctx: SidecarContext, params: ReaderGuidePlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 664) — Return optional section-break checks and a personalized second pass.
- `class ReaderBlockHealthInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 704)
- `reader_block_health(ctx: SidecarContext, params: ReaderBlockHealthInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 710)
- `class ReaderBlockRegionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 727)
  - `_one_form(self) -> 'ReaderBlockRegionInput'` (line 742; internal)
- `reader_block_original_region(ctx: SidecarContext, params: ReaderBlockRegionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 751)
- `class ReaderPdfViewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 768)
- `reader_pdf_view(ctx: SidecarContext, params: ReaderPdfViewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 775) — Tier-2 embedded PDF reader manifest: whether the revision's original PDF is available in the vault's content-addressed store (backfilling it from a still-present local original on demand), the store file name the llpdf:// protocol serves, and per-block page/bbox geometry (PDF po…
- `class ReaderTranslateSelectionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 878)
- `reader_translate_selection(ctx: SidecarContext, params: ReaderTranslateSelectionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 885)
- `class ReaderCaptureInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 895)
- `reader_capture(ctx: SidecarContext, params: ReaderCaptureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 909)
- `class ReaderCreateAnnotationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 933)
- `reader_create_annotation(ctx: SidecarContext, params: ReaderCreateAnnotationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 946)
- `class ReaderEditAnnotationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 968)
- `reader_edit_annotation(ctx: SidecarContext, params: ReaderEditAnnotationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 976)
- `class ReaderDeleteIntentInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 988)
- `reader_delete_intent_annotation(ctx: SidecarContext, params: ReaderDeleteIntentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 994)
- `class ReaderRestoreAnnotationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1000)
- `reader_restore_annotation(ctx: SidecarContext, params: ReaderRestoreAnnotationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1008) — Undo a delete (reader-pdf-selection): the annotation is listed again unless another delete of it stands (``listed``).
- `class ReaderReanchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1021)
- `reader_reanchor(ctx: SidecarContext, params: ReaderReanchorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1027)
- `class ReaderAnnotationHistoryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1040)
- `reader_annotation_history(ctx: SidecarContext, params: ReaderAnnotationHistoryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1045)
- `class ReaderSourceAnnotationsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1052)
- `reader_source_annotations(ctx: SidecarContext, params: ReaderSourceAnnotationsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1061)
- `class ReaderOutboxStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1070)
- `reader_outbox_status(ctx: SidecarContext, params: ReaderOutboxStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1075)
- `reader_drain_outbox(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1082)
- `class ReaderInvokePresetInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1103)
- `reader_invoke_preset(ctx: SidecarContext, params: ReaderInvokePresetInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1118)
- `class ReaderSetModeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1144)
- `reader_set_mode(ctx: SidecarContext, params: ReaderSetModeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1151)
- `class ReaderQuestionControlInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1162)
- `reader_question_control(ctx: SidecarContext, params: ReaderQuestionControlInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1170)
- `class ReaderEnqueueRequestInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1182)
- `reader_enqueue_request(ctx: SidecarContext, params: ReaderEnqueueRequestInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1199)
- `class ReaderRequestStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1217)
- `reader_request_status(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1222)
- `reader_cancel_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1228)
- `reader_retry_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1234)
- `class ReaderSourceRequestsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1241)
- `reader_source_requests(ctx: SidecarContext, params: ReaderSourceRequestsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1246)
- `reader_drain_requests(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1252)
- `class ReaderSourceObjectsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1257)
- `reader_source_objects(ctx: SidecarContext, params: ReaderSourceObjectsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1270)
- `class ReaderReviewSourceObjectInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1277)
- `reader_review_source_object(ctx: SidecarContext, params: ReaderReviewSourceObjectInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1283)
- `class ReaderLinkRelationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1294)
- `reader_link_relation(ctx: SidecarContext, params: ReaderLinkRelationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1302)
- `class ReaderProposalInboxInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1315)
- `reader_proposal_inbox(ctx: SidecarContext, params: ReaderProposalInboxInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1321)
- `class ReaderDecideProposalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1327)
- `reader_accept_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1332)
- `reader_reject_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1342)
- `class ReaderAuthorQAInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1368)
- `reader_author_qa(ctx: SidecarContext, params: ReaderAuthorQAInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1381) — Save the learner's Q+A verbatim and adopt it into practice (§9.1).
- `class ReaderCoachLintInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1405)
- `reader_coach_lint(ctx: SidecarContext, params: ReaderCoachLintInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1412)
- `class ReaderMaintainInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1421)
- `reader_maintain(ctx: SidecarContext, params: ReaderMaintainInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1438)
- `class ReaderArcInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1460)
- `reader_arc(ctx: SidecarContext, params: ReaderArcInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1467) — Create an arc (with ``commitment_id``) or project an existing one (``arc_id``).
- `class ReaderSetDepthPolicyInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1482)
- `reader_set_depth_policy(ctx: SidecarContext, params: ReaderSetDepthPolicyInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1488)
- `class ReaderArcIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1496)
- `reader_pause_arc(ctx: SidecarContext, params: ReaderArcIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1502)
- `class ReaderShrinkEnvelopeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1510)
- `reader_shrink_envelope(ctx: SidecarContext, params: ReaderShrinkEnvelopeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1517)
- `class ReaderPrimeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1530)
- `reader_prime(ctx: SidecarContext, params: ReaderPrimeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1539) — Offer (default) or answer (``answer=True``) an opt-in pretest prime (§10.3).
- `class ReaderRestoreInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1556)
- `reader_restore(ctx: SidecarContext, params: ReaderRestoreInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1564)
- `class ReaderWatchPlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1600)
- `reader_watch_plan(ctx: SidecarContext, params: ReaderWatchPlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1605)
- `class ReaderAuthorSectionQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1736)
- `reader_author_section_question(ctx: SidecarContext, params: ReaderAuthorSectionQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1742)
- `class ReaderGetProgressInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1803)
- `reader_get_progress(ctx: SidecarContext, params: ReaderGetProgressInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1808) — Durable per-section reading progress for one extraction (migration 106).
- `class ReaderMarkSectionProgressInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1819)
- `reader_mark_section_progress(ctx: SidecarContext, params: ReaderMarkSectionProgressInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1829) — Persist section progress; on first completion, trigger progressive practice generation for the section's provenance-linked Learning Objects.
- `class ReaderAuthoredQuestionActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1969)
- `reader_authored_question_action(ctx: SidecarContext, params: ReaderAuthoredQuestionActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1976)
- `class ReaderEscalateAuthoredQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1992)
- `class ReaderImportExerciseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1997)
- `reader_import_exercise(ctx: SidecarContext, params: ReaderImportExerciseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2008) — Queue the exact-exercise slice: the learner's selection (ordered per-block nodes) becomes one background authoring job that writes complete, schedulable PracticeItems around the verbatim exercise text.
- `enqueue_exercise_import(ctx: SidecarContext, vault, repository, params: ReaderImportExerciseInput) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2018) — Queue one exercise-import job and return its batch id (raises ``SidecarError`` when it cannot start).
- `class ReaderExerciseImportStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2067)
- `reader_exercise_import_status(ctx: SidecarContext, params: ReaderExerciseImportStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2072) — Poll one exercise-import batch.
- `reader_escalate_authored_question(ctx: SidecarContext, params: ReaderEscalateAuthoredQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2103)
- `class ReaderSearchSourcesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2134)
- `reader_search_sources(ctx: SidecarContext, params: ReaderSearchSourcesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2144)
- `class ReaderRetrievalOpenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2152)
- `reader_retrieval_open(ctx: SidecarContext, params: ReaderRetrievalOpenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2159) — The learner opened a passage from a library search result (local contextual retrieval P1, spec §9.2, Codex review F11): an ``opened`` signal on the span that result's receipt delivered.
- `class ReaderSpanLearningObjectsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2176)
- `reader_span_learning_objects(ctx: SidecarContext, params: ReaderSpanLearningObjectsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2182) — Provenance-linked LOs for a span, else labelled nearest-LO suggestions (T6).
- `class ReaderManualAnchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2192)
- `reader_manual_anchor(ctx: SidecarContext, params: ReaderManualAnchorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2200) — Repair a needs_reanchor annotation with a learner-chosen passage (§4.4).
- `class ReaderSetInquiryStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2286)
- `reader_set_inquiry_status(ctx: SidecarContext, params: ReaderSetInquiryStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2295) — Open, resolve, dismiss or reopen an inquiry (its root question's resolution).
- `class ReaderReconnectAnswerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2314)
- `reader_reconnect_answer(ctx: SidecarContext, params: ReaderReconnectAnswerInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2322) — The reconnect line's answer: yes resolves the root; quick check queues the passage-scoped question (never on the request path: a durable job writes it).
- `class ReaderInquiryQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2379)
- `reader_inquiry_question(ctx: SidecarContext, params: ReaderInquiryQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2413) — The inquiry's passage-scoped quick check, once authored (a cheap local read), and the state of the job writing it when ``batchId`` names one.
- `class ReaderInquiryQuestionActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2435)
- `reader_inquiry_question_action(ctx: SidecarContext, params: ReaderInquiryQuestionActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2443) — Answer, self-check (matches · partly · no) or dismiss an inquiry check.
- `class ReaderLogActivityInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2463)
- `reader_log_activity(ctx: SidecarContext, params: ReaderLogActivityInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2468) — Record the Reader's funnel events (salience only; ids, kinds and timings, never learner text).
- `check_me_proposal(vault: Any, repository: Any, extraction_id: str, cue: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2499) — "Check me" on a cue (spec §6.1): one short item on the cue's Learning Object, through ``find_practice`` under the Reader's caller (the question the learner answered left out).
- `class ReaderCueActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2546)
- `reader_cue_action(ctx: SidecarContext, params: ReaderCueActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2555) — A tap on a margin cue: open, check me, not relevant (and its undo).
- `class ReaderCuePreferencesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2584)
- `reader_cue_preferences(ctx: SidecarContext, params: ReaderCuePreferencesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2589) — The learner's cue preferences (Settings, the Guide's footer).
- `class ReaderSetCuePreferencesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2597)
- `reader_set_cue_preferences(ctx: SidecarContext, params: ReaderSetCuePreferencesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2606) — Change the margin-mark density, or switch cues off (or back on) for a book.

### Module constants

- `SOURCE_OBJECT_READ_PATHS` ([src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1266)
- `C_ERR` ([src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1365)
- `_TIME_LOCATOR_RE` ([src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1586)

## Internal implementation anchors

- `_require_reader(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 51) — Require an open vault AND the reader enabled (L8).
- `_require_source_reader(repository, source_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 65) — Per-source reader gate (owner ingest-time choice, migration 104): a source opted out of the reader loop (e.g.
- `_source_id_for_extraction(repository, extraction_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 80)
- `_reader_answer_mode(vault: Any, requested: str | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 125) — The Reader Ask's mode: the learner's one-question change, else (Reader CA2, Q5: the per-source select retires into the help style) the help style's while ``ask.panel_enabled``, else the launch default.
- `_reader_tool_handler(vault: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 280)
- `_revision_for_ref(repository, ref: str, run: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 859) — The revision behind an extraction / revision / source reference, for a source that has no finished extraction yet.
- `_parse_time_locator(locator: str | None) -> tuple[float, float | None] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1589)
- `_authored_question_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1698)
- `_progress_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 1791)
- `_require_inquiry(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2256)
- `_inquiry_question_payload(vault, repository, row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2266) — An inquiry check's wire shape, with the Learning Object "add to practice" would file it under (the anchor's provenance-linked LO, if any).
- `_inquiry_check_job(repository, batch_id: str, root_event_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2387) — The state of the quick-check job ``batch_id`` -- only when it is this inquiry's (any other batch reads as None).
- `_require_cues(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2487)
- `_check_me_clip(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/reader.py), line 2494)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `_require_source_reader`, `_source_id_for_extraction`; statically calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `_require_source_reader`, `_source_id_for_extraction`; statically calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `check_me_proposal`; statically calls `check_me_proposal`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `_authored_question_payload`; statically calls `_authored_question_payload`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `_require_source_reader`, `_source_id_for_extraction`; statically calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `_require_source_reader`, `_source_id_for_extraction`; statically calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `ReaderImportExerciseInput`, `_source_id_for_extraction`, `enqueue_exercise_import`; statically calls `_source_id_for_extraction`, `enqueue_exercise_import`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `priced_by`, `quiet`, `relay_batch_offer`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `PRICE_SETTING`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; calls `keep_ahead_for_reader`
- [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]] — imports `module`; calls `analyze_block_health`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_BACK_REFUSAL`, `HELD_OUT_REFUSAL`, `reading_held_back`; calls `reading_held_back`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `STATUS_STALE`, `legacy_place_origin`, `other_readings`, `resolve_span`; calls `legacy_place_origin`, `other_readings`, `resolve_span`
- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; calls `ArcError`, `answer_prime`, `create_arc`, `offer_prime`, `pause_arc`, `project_arc`, `set_depth_policy`, `shrink_envelope`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `note_reading_progress`; calls `PlanEnv`, `note_reading_progress`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `youtube_video_id`; calls `youtube_video_id`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `backfill_original`, `is_pdf_file`, `stored_original_path`; calls `backfill_original`, `is_pdf_file`, `stored_original_path`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `propose_practice`, `service_enabled`; calls `propose_practice`, `service_enabled`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `tutor_request_handler`; calls `tutor_request_handler`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `find_practice_injections`; calls `find_practice_injections`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `apply_config_updates`; calls `apply_config_updates`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `IntentUnavailable`, `PracticeConstraints`, `find_practice`; calls `find_practice`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `module`; calls `annotation_placements`, `append_annotation`, `delete_intent_annotation`, `edit_annotation`, `manual_anchor`, `reanchor_annotation`, `restore_annotation`, `translate_selection`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `printed_crops`, `region_for`; calls `printed_crops`, `region_for`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `module`; calls `author_qa`, `coach_lint`, `maintain`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; calls `capture`, `drain_outbox`, `invoke_preset`, `outbox_status`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `module`; calls `check_me_request`, `cues_enabled`, `find_cue`, `guide_cues`, `log_preference_events`, `preference_changes`, `preferences`, `record_cue_tap`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `administer_reading_question`, `ask`, `ask_history`, `choose_disposition`, `inquiry_enabled`, `question_control`, `reader_enabled`, `reader_prompt_contract`, `restore_source`, `routing_prior_projection_v1`, `set_answer_mode`, `set_mode`, `skip_reading_question`, `submit_reading_question`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `module`; calls `build_guide_plan`, `extraction_sections`, `goal_for_item`, `held_out_sections`, `reading_protection`
- [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] — imports `module`; calls `answer_reconnect`, `record_activity`, `resolve_inquiry_root`, `set_inquiry_status`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`, `section_generation_candidates`, `source_refs_for_section`; calls `learning_objects_for_span`, `section_generation_candidates`, `source_refs_for_section`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `escalate`, `record_action`, `record_inquiry_action`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `cancel_request`, `drain_requests`, `enqueue_request`, `request_status`, `retry_request`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `module`; calls `restore`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `accept_mapping`, `link_relation`, `proposal_inbox`, `reject_mapping`, `review_source_object`, `source_objects_for_source`
- [[Reference/Modules/learnloop/reader/source_render_views|learnloop.reader.source_render_views]] — imports `module`; calls `render_payload`, `resolve_or_create_render_view`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `module`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `module`; calls `build_block_region`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; calls `fields`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `record_open`; calls `record_open`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `search_library`; calls `search_library`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `module`; calls `discovery_enabled`, `merged_cues`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `resolver_active`; calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `suggest_learning_objects`, `suggested_learning_objects`; calls `suggest_learning_objects`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `module`; calls `count_open_questions`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `QuestionLimitReached`, `TutorQAError`, `ask_panel_enabled`, `help_style_answer_mode`; calls `ask_panel_enabled`, `help_style_answer_mode`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`; calls `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `queue_tutor_question_gap`; calls `queue_tutor_question_gap`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `plan_minutes_estimator`; calls `plan_minutes_estimator`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `remember`; calls `remember`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `learner_state_enabled`, `module`, `prompt_contract_fields`; calls `bound_ask`, `build_request`, `fallback_practice_request`, `learner_state`, `learner_state_enabled`, `offers`, `offers_enabled`, `prompt_contract_fields`, `record_excerpt_exposure`, `restriction`, `retrieval_enabled`, `tools_refused`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `prompt_contract_fields`; calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `tutor_practice_request`; calls `tutor_practice_request`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `notify`, `notify_offer`; calls `notify`, `notify_offer`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `require_identity`; calls `require_identity`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]], [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]], [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]], [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — direct import
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_every_registered_handler_reading_source_objects_is_pinned`
  - `test_the_pin_catches_a_second_raw_reader`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_check_me_keeps_the_sentence_whole_when_it_clips`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
- [tests/test_reader_active_reading.py](../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_section_quick_checks_are_byte_identical`
- [tests/test_reader_branches.py](../../../../../../tests/test_reader_branches.py) — direct import
  - `test_branch_rpc_roundtrip_uses_parent_id_and_persists_on_reinitialize`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_check_me_never_offers_the_question_the_learner_answered`
- [tests/test_reader_inquiry_kill_switch.py](../../../../../../tests/test_reader_inquiry_kill_switch.py) — direct import
  - `test_rpcs_off_answer_exactly_as_before`
  - `test_rpcs_on_add_only_the_branch_fields`
- [tests/test_reader_inquiry_status.py](../../../../../../tests/test_reader_inquiry_status.py) — direct import
  - `test_status_rpc_and_its_kill_switch`
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_a_landed_inquiry_check_names_its_model_and_prompt_version`
  - `test_inquiry_question_action_rpc_records_the_self_check`
  - `test_reconnect_rpcs_round_trip`
  - `test_section_quick_checks_are_byte_identical`
  - `test_the_quick_check_read_reports_its_durable_jobs_state`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`
- [tests/test_reader_tutor_switch_off.py](../../../../../../tests/test_reader_tutor_switch_off.py) — direct import
- [tests/test_reading_hardening_landing.py](../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_asking_for_a_held_out_sections_check_is_refused_before_anything_is_queued`
- [tests/test_rw4_kill_switches.py](../../../../../../tests/test_rw4_kill_switches.py) — direct import
  - `test_the_readers_tutor_spans_are_unchanged`
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_with_the_retired_keep_local_gets_its_passage_check_when_asked`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader.py](../../../../../../src/learnloop_sidecar/handlers/reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
