---
title: "learnloop.reader.reader_quick_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_quick_check.py"
source_paths:
  - "src/learnloop/reader/reader_quick_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_quick_check module"
  - "src/learnloop/reader/reader_quick_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_quick_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_quick_check` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader quick-check producer: AI-authored section-boundary questions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py) |
| Source lines | 1269 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReaderQuickCheckError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 120) — Domain error for the reader quick-check producer.
- `class PassageCheckRefused(ReaderQuickCheckError)` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 124) — The spend framework refused the passage check before anything was sent.
  - `__init__(self, reason: str, message: str, *, refusal: str | None=None) -> None` (line 132; internal)
- `class InquiryCheckHeld(ReaderQuickCheckError)` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 138) — Another worker holds this inquiry's claim: no call was made.
- `class PassageCheckSpend` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 143) — Admission settings of one passage check (``[reader_inquiry]``, W10).
  - `caps(self) -> SpendCaps` (line 166; public)
- `passage_check_spend(config: Any, *, provider: str | None=None, cancelled: Callable[[], bool] | None=None) -> PassageCheckSpend` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 175) — The vault's passage-check admission settings (``[reader_inquiry]``, and the shared output-budget policy for the check's route: its budget and its reasoning effort).
- `inquiry_claim_key(inquiry_root_event_id: str, prompt_version: str | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 193)
- `request_reading_quick_check(client: StructuredTransport, context: ReadingQuickCheckContext) -> ReadingQuickCheck` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 201) — Author one section quick check through the shared transport.
- `request_passage_check(client: StructuredTransport, context: ReadingQuickCheckContext) -> ReadingQuickCheck` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 214) — Author one passage-scoped quick check (RW1a) through the shared transport.
- `section_view(repository: Repository, *, extraction_id: str, section_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 408) — The bounded, readable view of ONE guide section: {section_id, label, blocks:[{span_id, kind, text}]}.
- `author_quick_check(repository: Repository, client: Any, *, extraction_id: str, section_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 437) — Author + persist one quick check for a section (idempotent).
- `passage_view(repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 500) — The bounded view of one inquiry's root passage (RW1a): its anchor spans and up to ``PASSAGE_BLOCKS_BEFORE``/``AFTER`` neighbours, inside the anchor's guide section (the same section derivation as the guide plan).
- `author_inquiry_quick_check(repository: Repository, client: Any, *, extraction_id: str, inquiry_root_event_id: str, anchor_span_ids: list[str] | tuple[str, ...], clock: Clock | None=None, spend: PassageCheckSpend | None=None, owner: str | None=None, owner_ended: Callable[[str], bool] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 544) — Author + persist the reconnect line's quick check for one inquiry (RW1a).
- `record_inquiry_action(repository: Repository, *, question_id: str, action: str, response_md: str | None=None, self_check: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 700) — Record the learner's act on an inquiry-scoped quick check (RW1a).
- `record_action(repository: Repository, *, question_id: str, action: str, response_md: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 803) — Record the learner's self-check outcome on the row (salience-only): ``answered`` stamps their response; ``dismissed`` is the durable "don't bring this back".
- `escalate(root: Path, repository: Repository, *, question_id: str, learning_object_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 833) — Escalate an authored quick check into a real PracticeItem.
- `selection_item_id(question_id: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 950) — The practice item an active-reading question escalates into, named by the question (RW1b review F5): the item file is written before the question is linked to it, so a retry after a crash between the two rewrites the same item instead of leaving a second one outside the question…
- `selection_claim_key(extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 964)
- `selection_view(repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 969) — The bounded view of one selection (RW1b): the selected blocks in reading order inside the first one's guide section, one block of context before them and the book's next ``FOLD_BLOCKS`` blocks after them (the ones the Reader folds for the next step).
- `folded_span_ids(repository: Repository, *, extraction_id: str, anchor_span_ids: list[str]) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1030) — The book's next blocks after a selection, the ones that fold (G4's fold).
- `request_active_question(client: StructuredTransport, context: ReadingActiveContext) -> ReadingActiveCheck` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1041) — Author one selection-scoped question (RW1b) as an isolated turn (the passage is untrusted source text, as for RW1a's passage check).
- `selection_question(repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1093) — The selection's question in ``style`` under its reuse key, any status.
- `author_selection_question(repository: Repository, client: Any, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], style: str, clock: Clock | None=None, spend: PassageCheckSpend | None=None, owner: str | None=None, owner_ended: Callable[[str], bool] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1104) — Author + persist one active-reading question on a selection (RW1b).
- `is_missed(row: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1213) — A missed formative answer: partly or no on a next step, why step or assumption.
- `record_selection_action(repository: Repository, *, question_id: str, action: str, response_md: str | None=None, self_check: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1220) — The learner's act on an active-reading question (RW1b).

### Module constants

- `MAX_SECTION_BLOCKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 80)
- `MAX_SECTION_CHARS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 81)
- `QUESTION_ACTIONS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 83)
- `INQUIRY_PROMPT_VERSION` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 88)
- `PASSAGE_BLOCKS_BEFORE` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 89)
- `PASSAGE_BLOCKS_AFTER` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 90)
- `MAX_PASSAGE_CHARS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 91)
- `INQUIRY_ACTIONS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 92)
- `SELF_CHECKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 93)
- `PASSAGE_CHECK_RECEIPT_OWNER` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 99)
- `INQUIRY_CLAIM_TASK` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 100)
- `INQUIRY_CLAIM_PRODUCER` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 101)
- `INQUIRY_CLAIM_LEASE_SECONDS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 105)
- `PASSAGE_CHECK_PROMPT_TOKENS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 108)
- `PASSAGE_CHECK_ROUTE` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 111)
- `PASSAGE_CHECK_PRICE_SETTING` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 113)
- `PASSAGE_CHECK_PURPOSE` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 114)
- `SELF_CHECK_TASK` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 117)
- `SELECTION_PROMPT_VERSION` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 934)
- `SELECTION_STYLES` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 935)
- `FORMATIVE_STYLES` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 938)
- `MISSED_SELF_CHECKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 939)
- `SELECTION_ACTIONS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 940)
- `SELECTION_CLAIM_TASK` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 941)
- `FOLD_BLOCKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 945)
- `MAX_SELECTED_BLOCKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 946)
- `MAX_SELECTION_CHARS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 947)

## Internal implementation anchors

- `_estimate_tokens(text: str) -> int` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 197)
- `_admitted_passage_check(repository: Repository, client: Any, context: Any, *, spend: PassageCheckSpend, owner_id: str, clock: Clock | None, prompt: Callable[[Any], str]=reading_passage_check_prompt, request: Callable[[Any, Any], Any]=request_passage_check) -> Any` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 235) — Admit one passage check through the spend framework, then send it.
- `_send_passage_check(repository: Repository, client: Any, context: ReadingQuickCheckContext, *, budget: SpendBudget, estimate: SpendEstimate, planned: int, price: float | None, subscription: bool, limit: int | None, day: str, capped: Callable[[], PassageCheckRefused], owner_id: str, output_tokens: int, truncation: TruncationRetry, effort: str | None, request: Callable[[Any, Any], Any]=request_passage_check) -> Any` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 321) — One admitted attempt of the passage check: its receipts, its request.
- `_insert_inquiry_row(repository: Repository, client: Any, *, extraction_id: str, view: dict[str, Any], revision: dict[str, Any], question_md: str, expected_answer_md: str, span_ids: list[str], inquiry_root_event_id: str, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 665)
- `_append_self_check_verdict(repository: Repository, row: dict[str, Any], verdict: str, *, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 756) — Append the learner's self-check to ``judgment_ledger`` (inside the caller's transaction).
- `_clean(text: str | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 960)
- `_expected_answer(view: dict[str, Any], result: ReadingActiveCheck) -> tuple[str, str, list[str]]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 1054) — ``(expected answer, answer basis, cited spans)``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `author_inquiry_quick_check`, `author_quick_check`, `author_selection_question`, `extraction_sections`, `passage_check_spend`, `passage_view`, `selection_claim_key`, `selection_question`, `selection_view`
- [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] — imports `module`; statically calls `escalate`, `is_missed`, `record_selection_action`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `escalate`, `record_action`, `record_inquiry_action`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `is_missed`, `selection_question`, `selection_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; calls `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `CLAIMED`, `DONE`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `lease_holder`, `release_claim`, `take_over_claim`; calls `claim_work`, `complete_claim`, `holds_claim`, `lease_holder`, `release_claim`, `take_over_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `ACTIVE_QUESTION_STYLES`, `READING_ACTIVE_PROMPT_VERSION`, `READING_PASSAGE_CHECK_PROMPT_VERSION`, `READING_QUICK_CHECK_PROMPT_VERSION`, `ReadingActiveCheck`, `ReadingActiveContext`, `ReadingQuickCheck`, `ReadingQuickCheckContext`, `reading_active_prompt`, `reading_passage_check_prompt`, `reading_quick_check_prompt`; calls `ReadingActiveContext`, `ReadingQuickCheckContext`, `reading_active_prompt`, `reading_passage_check_prompt`, `reading_quick_check_prompt`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_reading_opportunities.py](../../../../../../tests/test_ad1_reading_opportunities.py) — direct import
  - `test_reading_opportunities_frozen_and_ordered_by_source_time`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_a_taken_extra_becomes_a_reading_opportunity_with_the_offer_id`
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_a_question_counts_once_and_no_verdict_reaches_evidence`
- [tests/test_reader_active_reading.py](../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_answering_and_self_checking_write_no_attempt_or_evidence`
  - `test_nothing_after_the_line_means_no_next_step_and_no_call`
  - `test_section_quick_checks_are_byte_identical`
  - `test_show_me_reveals_without_an_answer_and_self_check_needs_the_reveal`
  - `test_the_next_step_is_the_books_following_block_verbatim`
  - `test_the_selection_reuse_key_holds`
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_show_me_with_no_answer_queues_nothing`
  - `test_the_sidecars_self_check_queues_the_text_and_wakes_the_worker`
- [tests/test_reader_intentions.py](../../../../../../tests/test_reader_intentions.py) — direct import
  - `test_active_reading_works_on_a_transcript`
  - `test_grouping_changes_no_presets_effect`
- [tests/test_reader_passage_check.py](../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_check_held_by_a_live_job_waits_for_it_and_returns_its_question`
  - `test_a_check_held_past_the_wait_fails_retryably_and_never_completes_without_a_question`
  - `test_a_claim_left_by_a_crashed_job_is_taken_over_by_the_next_job_at_once`
  - `test_a_crashed_claim_from_another_job_is_taken_over_after_its_lease`
  - `test_a_crashed_claim_is_recovered_by_its_own_job_at_once_and_by_others_after_its_lease`
  - `test_a_failed_call_is_receipted_and_counts_toward_the_daily_cap`
  - `test_a_late_completion_never_replaces_the_check_the_learner_saw`
  - `test_a_metered_check_over_its_dollar_cap_makes_no_request`
  - `test_a_metered_route_without_an_owner_price_makes_no_request`
  - `test_a_spend_refusal_says_whether_the_price_is_missing_or_the_check_is_over_its_cap`
  - `test_an_exhausted_daily_budget_makes_no_request`
  - `test_concurrent_checks_on_different_inquiries_never_overrun_the_daily_count`
  - `test_overlapping_workers_make_one_model_call_and_one_row`
- [tests/test_reader_quick_check.py](../../../../../../tests/test_reader_quick_check.py) — direct import
  - `test_author_quick_check_is_idempotent_per_section`
  - `test_author_quick_check_persists_span_grounded_row`
  - `test_author_quick_check_rejects_invented_spans`
  - `test_dismissed_question_suppresses_reauthoring_and_display`
  - `test_escalate_mints_practice_item_with_span_provenance`
  - `test_guide_plan_falls_back_to_authored_question`
  - `test_owner_reviewed_placement_wins_over_authored`
  - `test_record_answer_stamps_response_on_the_row`
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_a_landed_inquiry_check_names_its_model_and_prompt_version`
  - `test_an_inquiry_row_never_shadows_its_sections_quick_check`
  - `test_answering_and_self_checking_an_inquiry_check_is_formative`
  - `test_each_self_check_verdict_is_a_learner_card_judgment_and_a_change_supersedes`
  - `test_every_question_style_is_accepted_now`
  - `test_inquiry_question_action_rpc_records_the_self_check`
  - `test_inquiry_reuse_key_is_root_and_prompt_version`
  - `test_migration_185_and_the_inquiry_check_under_production_sqlite`
  - `test_migration_adds_the_scope_columns_with_section_defaults`
  - `test_reconnect_and_its_check_on_every_source_kind`
  - `test_scope_columns_carry_their_checks`
  - `test_section_quick_checks_are_byte_identical`
  - `test_the_inquiry_check_is_scoped_to_the_root_passage`
  - `test_the_self_check_and_its_ledger_row_commit_together`
- [tests/test_reader_reconstruct.py](../../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_every_rw1b_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
  - `test_reconstruct_needs_a_reconstruct_question`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f13_answering_makes_no_item_and_add_to_practice_makes_exactly_one`
  - `test_f7_the_backlog_sweep_recovers_a_missed_answer_without_a_job`
- [tests/test_rw1a_composition.py](../../../../../../tests/test_rw1a_composition.py) — direct import
  - `test_a_truncation_retry_counts_toward_the_day_like_any_call`
  - `test_a_truncation_retry_over_the_per_check_cap_is_refused_before_it_is_sent`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change reader quick check policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
