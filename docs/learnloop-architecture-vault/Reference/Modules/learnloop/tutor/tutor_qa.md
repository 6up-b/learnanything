---
title: "learnloop.tutor.tutor_qa"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/tutor_qa.py"
source_paths:
  - "src/learnloop/tutor/tutor_qa.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.tutor_qa module"
  - "src/learnloop/tutor/tutor_qa.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.tutor_qa`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.tutor_qa` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Tutor Q&A ("ask"): classified learner questions in three contexts.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py) |
| Source lines | 1118 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_tutor_answer(client: OperationClient, context: TutorQAContext) -> TutorAnswer` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 75) — Run the feature-owned tutor-Q&A operation.
- `reader_span_key(extraction_id: str, span_id: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 91) — The persistence/budget key for a reader exchange: one source block span.
- `class TutorQAError(ValueError)` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 119)
- `class QuestionLimitReached(Exception)` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 124)
  - `__str__(self) -> str` (line 129; internal)
- `question_usage(vault: LoadedVault, repository: Repository, *, context: str, practice_item_id: str | None=None, attempt_id: str | None=None, note_id: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> tuple[int, int]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 136) — (used, limit) for one Q&A budget window.
- `ask_question(vault: LoadedVault, repository: Repository, client: Any, *, context: str, question_md: str, practice_item_id: str | None=None, attempt_id: str | None=None, note_id: str | None=None, session_id: str | None=None, seconds_into_attempt: float | None=None, question_context: Mapping[str, Any] | None=None, extraction_id: str | None=None, span_id: str | None=None, answer_mode: str | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 282) — ``question_context`` carries the §13.4 generating-process fields (preceding_tutor_move, scaffold_level, warning_state, learner_mode, question_opportunity, hints_used_before, direct_explanation_request, attempt_progress).
- `build_tutor_opening(vault: LoadedVault, repository: Repository, client: Any, *, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 601) — A proactive tutor opening for a just-closed diagnostic block (§12.1).
- `hint_equivalents_for_submission(repository: Repository, practice_item_id: str, session_id: str | None, *, until: str | None=None) -> int` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 640) — Hint-equivalent questions since the item was last attempted.
- `hint_equivalents_for_attempt(repository: Repository, attempt: dict[str, Any]) -> int` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 662) — Reconstruct a graded attempt's question-hint count from persisted rows.
- `answer_leak_overlap(answer_md: str, expected_answer: str | dict[str, Any]) -> float` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 685) — How much of the expected answer the tutor's answer exposed (0..1).
- `answer_leaks_expected(answer_md: str, expected_answer: str | dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 715) — Heuristic answer-leak telemetry: did the tutor give the answer away?
- `tutor_qa_note_title(question_md: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 724)
- `build_tutor_qa_note(vault: LoadedVault, repository: Repository, event: Mapping[str, Any], *, subject_id: str | None=None, related_lo_ids: list[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 731) — Materialize a tutor Q&A turn as a vault note and persist the back-link.

### Module constants

- `QUESTION_CONTEXTS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 68)
- `READER_ANSWER_MODES` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 71)
- `READER_ANSWER_MODE_DEFAULT` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 72)
- `HINT_EQUIVALENT_TYPES` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 105)
- `_LEAK_MIN_TOKENS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 107)
- `_LEAK_OVERLAP_THRESHOLD` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 108)
- `_MAX_CITATION_SPANS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 112)
- `_MAX_SELECTION_SPANS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 116)

## Internal implementation anchors

- `_record_dialogue_causal_signals(vault: LoadedVault, repository: Repository, *, answer: Any, attempt_id: str | None, practice_item_id: str | None, question_event_id: str, remediation_episode_id: str | None, leak_overlap: float, model: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 186) — Fold what the learner's question revealed back into the causal record.
- `_validated_citations(answer: Any, source_spans: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 572) — Keep only citations naming a span actually provided in context (§9.2).
- `_normalize(text: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 801)
- `_candidate_facets(vault: LoadedVault, repository: Repository, context: str, *, item: PracticeItem | None, note) -> list[str]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 805)
- `_thread(repository: Repository, *, context: str, practice_item_id: str | None, attempt_id: str | None, note_id: str | None, session_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 823)
- `_tutor_context_hash(context: TutorQAContext) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 863)
- `_build_context(vault: LoadedVault, repository: Repository, *, context: str, question_md: str, candidates: list[str], thread: list[dict[str, Any]], item: PracticeItem | None, attempt: dict[str, Any] | None, note, note_id: str | None, extraction_id: str | None=None, span_id: str | None=None, answer_mode: str | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None) -> TutorQAContext` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 868)
- `_source_spans(vault: LoadedVault, repository: Repository, lo_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 968) — Bounded semantic-authority source spans for the LO(s) in tutor context (§9.2).
- `_reader_source_spans(repository: Repository, extraction_id: str | None, span_id: str | None, *, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 995) — Block-level span views for the reader manifest (§7.6): the learner's selection (exact quote first, then every covered block), plus the primary block's immediate neighbours, as citable {extraction_id, span_id, label, text} spans.
- `_diagnostic_decision_for(repository: Repository, item: PracticeItem | None, context: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1082) — The §12.1 typed transition decision steering post-diagnosis tutoring.
- `_grading_evidence_rows(repository: Repository, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1104)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `_reader_source_spans`, `ask_question`, `reader_span_key`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `_thread`, `build_tutor_qa_note`; statically calls `_thread`, `build_tutor_qa_note`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `_source_spans`; statically calls `_source_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `hint_equivalents_for_submission`; statically calls `hint_equivalents_for_submission`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `QuestionLimitReached`, `TutorQAError`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `hint_equivalents_for_attempt`; statically calls `hint_equivalents_for_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `QuestionLimitReached`, `TutorQAError`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `question_usage`; statically calls `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `question_usage`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal`, `reveal_episode_id`; calls `record_reveal`, `reveal_episode_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `append_dialogue_candidate`; calls `append_dialogue_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `record_learner_embedded_prediction`; calls `record_learner_embedded_prediction`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `build_span_view`; calls `build_span_view`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TUTOR_QA_PROMPT_VERSION`, `TutorAnswer`, `TutorQAContext`, `tutor_qa_prompt`; calls `TutorQAContext`, `tutor_qa_prompt`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_note`; calls `add_note`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]], [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_question_context.py](../../../../../../tests/test_question_context.py) — direct import
  - `test_classifier_channel_is_persisted`
  - `test_direct_explanation_request_forces_preference_channel`
  - `test_question_context_fields_persist`
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_build_tutor_qa_note_raises_without_subject`
  - `test_build_tutor_qa_note_writes_back_link_and_is_idempotent`
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
  - `test_failed_provider_keeps_question_row_without_charging_budget`
  - `test_successful_ask_records_answered_event_and_agent_run`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_ask_is_never_ability_evidence`
  - `test_each_disposition_produces_its_mechanism_and_nothing_else`
  - `test_reader_is_the_fourth_tutor_context`
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_a_reveal_inside_a_live_repair_is_attributed_to_its_episode`
  - `test_a_tutor_answer_that_gives_the_solution_primes_the_next_attempt`
  - `test_answer_leak_overlap_accepts_a_structured_expected_answer`
  - `test_answer_leak_overlap_is_a_fraction_not_a_flag`
  - `test_answer_leak_overlap_is_zero_when_it_cannot_be_computed`
  - `test_answer_leak_overlap_scores_a_verbatim_restatement_as_a_full_reveal`
  - `test_feedback_question_is_hint_equivalent_and_writes_a_reveal_event`
  - `test_feedback_questions_count_as_hints_for_the_next_attempt`
  - `test_hint_window_still_starts_at_the_previous_attempt`
  - `test_reader_questions_bind_no_item_so_they_debit_nothing`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_tutor_citations.py](../../../../../../tests/test_tutor_citations.py) — direct import
  - `test_citations_validated_against_provided_spans`
  - `test_no_links_degrades_to_no_citations`
  - `test_tutor_context_carries_semantic_authority_spans`
- [tests/test_tutor_qa.py](../../../../../../tests/test_tutor_qa.py) — direct import
  - `test_answer_leaks_expected_heuristics`
  - `test_ask_question_classifies_and_marks_hint_equivalents`
  - `test_ask_question_drops_facets_outside_candidates`
  - `test_ask_question_enforces_practice_limit`
  - `test_ask_question_feedback_limit_and_intervention_wiring`
  - `test_ask_question_leak_check_flags_expected_answer`
  - `test_ask_question_library_context_and_daily_limit`
  - `test_ask_question_validation_errors`
  - `test_diagnostic_decision_attaches_after_probe_transition`
  - `test_hint_equivalents_for_submission_window_starts_at_last_attempt`
  - `test_practice_prompt_context_carries_guardrail_grounding`
  - `test_question_raises_diagnostic_uncertainty_read_side`

## Modification guidance

- Change tutor qa policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
