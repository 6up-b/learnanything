---
title: "learnloop_sidecar.handlers.tutor_qa"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/tutor_qa.py"
source_paths:
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop_sidecar.handlers.tutor_qa module"
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.tutor_qa`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.tutor_qa` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Tutor Q&A RPCs: ask, rate, save-as-note, transcript.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/tutor_qa.py](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py) |
| Source lines | 968 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class AskTutorQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 41)
- `class RateTutorAnswerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 80)
- `class SaveTutorAnswerNoteInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 85)
- `class GetTutorTranscriptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 90)
- `class PromoteTutorQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 103)
- `class ListQuestionQueueInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 110)
- `class ResolveQuestionEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 116)
- `list_question_queue(ctx: SidecarContext, params: ListQuestionQueueInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 122) — The outstanding-question queue (newest first) + the open count.
- `resolve_question_event(ctx: SidecarContext, params: ResolveQuestionEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 141) — Flip one question to open/resolved/dismissed (learner-owned queue state).
- `ask_tutor_question(ctx: SidecarContext, params: AskTutorQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 161)
- `class PanelAsk` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 361) — What the server derives for one practice or feedback question while ``ask.panel_enabled`` (Reader CA2 §7.4, K5, K7; Codex review F3, F6, F10), never from the client's word: the answer mode, the validated workbench, the attempt's key and practice session, whether the item is unde…
  - `bound(self) -> bool` (line 379; public)
- `attempt_aliases(repository: Any, practice_item_id: str | None, submission_id: str | None, workbench_session_id: str | None) -> AttemptAliases | None` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 451) — Astra batch review (Medium): the other identities of the attempt a practice question names (``reader.workbench.attempt_identities``: the answer box's draft handed into Work in Steps, resumed in the Reader), so its thread and its per-attempt budget are one in every host.
- `tutor_practice_request(vault: Any, repository: Any, event_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 560) — The answer's practice request, or None when the offer is switched off.
- `class PreviewTutorOpeningInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 574)
- `preview_tutor_opening(ctx: SidecarContext, params: PreviewTutorOpeningInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 580) — A proactive tutor opening for a just-closed diagnostic block (§12.1).
- `rate_tutor_answer(ctx: SidecarContext, params: RateTutorAnswerInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 604)
- `save_tutor_answer_note(ctx: SidecarContext, params: SaveTutorAnswerNoteInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 612)
- `promote_tutor_question(ctx: SidecarContext, params: PromoteTutorQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 633) — Persist and enqueue an answered tutor turn for durable promotion.
- `get_tutor_transcript(ctx: SidecarContext, params: GetTutorTranscriptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 738)

## Internal implementation anchors

- `_ask_panel_inputs(ctx: SidecarContext, vault: Any, repository: Any, params: Any, *, transcript: bool=False) -> PanelAsk` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 383) — Reader CA2 (§7.4, K7): the :class:`PanelAsk` of a practice or feedback question (or transcript) while ``ask.panel_enabled``.
- `_worked_help_check(answer_md: str, item: Any) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 469) — Codex review F2 (K9): the hint service's leak control at levels 1-3 (``hints.contracts.leak_flags``) for an Ask answer before it is shown.
- `_item_cold(vault: Any, repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 478) — Is the item under a cold administration now (an open cold follow-up or a held-out exam, ``instructional.policy.cold_administration_open``, or a "Check once" served cold)?
- `_with_offers(vault: Any, repository: Any, response: dict[str, Any], event_id: str, tool_requests: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 493) — Canonical sources S0 (§6.2): a deterministic "Practice this" request the frontend runs once the answer is on screen.
- `_stored_tool_requests(repository: Any, event_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 506)
- `_record_citations(vault: Any, repository: Any, event_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 517) — S5: a tutor answer citing retrieved spans is an intervention (best effort).
- `_span_provider(vault: Any, repository: Any, params: AskTutorQuestionInput, *, cold: bool=False) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 530)
- `_tool_request_handler(vault: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 544)
- `_tutor_intent_for(vault: Any, repository: Any, *, context: str, item: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 552) — Canonical sources S3: remediate when the item's LO has an active misconception.
- `_tutor_route_subscription(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 808) — Is the tutor's route a subscription transport (Codex, the ChatGPT plan)?
- `_help_record(repository: Any, params: GetTutorTranscriptInput, panel_ask: PanelAsk, thread: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 824) — Reader CA2 (§7.5, K8; Codex review F7): the attempt's help record as Submit will fold it, in order, read from what is stored (never the panel's memory): every question Submit counts (the item's window, which may hold a question asked on an earlier serving of the item), this atte…
- `_draft_opened(repository: Any, session_id: str | None, item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 880)
- `_shown_assists(repository: Any, item_id: str, session_id: str | None, submission_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 891) — The attempt's shown hints still unattached, under its key (``help_assists``).
- `_earlier(vault: Any, repository: Any, params: GetTutorTranscriptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 925) — Reader CA2 (§7.3, K6, Q2): *earlier on this question*.
- `_served_cold(vault: Any, repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py), line 953) — Is the item served as a check on your own now (a due "Check once" served cold, or a due cold follow-up)?

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `_item_cold`; statically calls `_item_cold`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `tutor_practice_request`; statically calls `tutor_practice_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `get_capture`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/hint_window|learnloop.hint_window]] — imports `counts_in_session`, `workbench_bound`; calls `counts_in_session`, `workbench_bound`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `leak_flags`; calls `leak_flags`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_tutor_citations`; calls `record_tutor_citations`
- [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]] — imports `practice_request_for_answer`; calls `practice_request_for_answer`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `cold_administration_open`; calls `cold_administration_open`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `tutor_intent_for`; calls `tutor_intent_for`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `offered_tool_requests`, `tutor_request_handler`; calls `offered_tool_requests`, `tutor_request_handler`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `cold_followup_duty`, `served_check`; calls `cold_followup_duty`, `served_check`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `attempt_identities`, `session_row`, `submission_id_for`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `help_converts_active`; calls `help_converts_active`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `PinnedSpanProvider`, `TutorSpanProvider`, `linked_reference_filter`; calls `PinnedSpanProvider`, `TutorSpanProvider`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `QuestionQueueError`, `module`; calls `count_open_questions`, `list_question_queue`, `set_question_resolution`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `AttemptAliases`, `QuestionLimitReached`, `READER_ANSWER_MODES`, `TutorQAError`, `WITHHELD_NOT_SAVED`, `answer_withheld`, `ask_panel_enabled`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `delivered_answer_md`, `earlier_threads`, `help_style_answer_mode`, `hint_equivalents_for_submission`, `practice_thread_events`, `question_usage`; calls `AttemptAliases`, `answer_withheld`, `ask_panel_enabled`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `delivered_answer_md`, `earlier_threads`, `help_style_answer_mode`, `hint_equivalents_for_submission`, `practice_thread_events`, `question_usage`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_note`, `move_note`; calls `add_note`, `move_note`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `provider_label`, `ready_tutor_qa_provider`; calls `provider_label`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `capture_call`, `finish_route`, `route_intent`; calls `capture_call`, `finish_route`, `route_intent`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `queue_tutor_question_gap`; calls `queue_tutor_question_gap`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `_earlier_opened_hint`; calls `_earlier_opened_hint`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `draft_earlier_opened`, `refuse_moved_session`; calls `draft_earlier_opened`, `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `_practice_session`; calls `_practice_session`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_ca2_astra_handoff_helpers.py](../../../../../../tests/reader_ca2_astra_handoff_helpers.py) — direct import
- [tests/reader_ca2_codex_review_helpers.py](../../../../../../tests/reader_ca2_codex_review_helpers.py) — direct import
- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — direct import
  - `test_tutor_route_after_answer_only_and_reference_anchor`
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — direct import
  - `test_incomplete_tutor_event_is_not_duplicated`
  - `test_purge_during_tutor_answer_does_not_restore_capture`
  - `test_replacement_tutor_request_moves_the_partial_note_to_its_subject`
  - `test_tutor_ai_does_not_hold_a_sqlite_writer`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_sidecar_queues_the_reading_and_the_overlay_shows_it_with_undo`
- [tests/test_reader_ca2_codex_rereview.py](../../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
  - `test_f13_a_sessionless_reader_question_counts_after_its_session_ends_and_the_problem_resumes`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_transcript_offers_earlier_threads_but_never_on_a_cold_check`
- [tests/test_sidecar_source_retrieval.py](../../../../../../tests/test_sidecar_source_retrieval.py) — direct import
  - `test_ask_tutor_question_injects_the_source_span_provider`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_sidecar_injects_the_linked_reference_rules`
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_ask_tutor_question_returns_the_request`
  - `test_the_offer_switch_removes_the_request`
- [tests/test_tutor_tool_requests.py](../../../../../../tests/test_tutor_tool_requests.py) — direct import
  - `test_the_sidecar_offers_requests_and_drops_the_s0_request`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/tutor_qa.py](../../../../../../src/learnloop_sidecar/handlers/tutor_qa.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
