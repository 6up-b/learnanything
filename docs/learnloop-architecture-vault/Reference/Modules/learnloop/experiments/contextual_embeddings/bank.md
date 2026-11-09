---
title: "learnloop.experiments.contextual_embeddings.bank"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/bank.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/bank.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.bank module"
  - "src/learnloop/experiments/contextual_embeddings/bank.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.bank`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.bank` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's question bank, labels and adjudication (spec §5.1, §5.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py) |
| Source lines | 1085 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `stable_order(values: Sequence[Any], *salt: Any, key=lambda value: value) -> list[Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 67)
- `class EvidenceSet` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 72)
  - `as_dict(self) -> dict[str, Any]` (line 76; public)
- `class BankQuestion` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 81)
  - `effective_query(self) -> str` (line 104; public) — The learner's question text alone (whitespace-normalized).
  - `retrieval_query(self) -> str` (line 110; public) — The complete query every arm encodes (no rewrite in the screen): the question and, for a known selection, the frozen selected passage.
  - `context(self) -> dict[str, Any]` (line 120; public) — The ONE question context every role reads (Codex review F6): the question, the frozen selected passage (a deictic question's referent) and the permitted history.
  - `known_location(self) -> bool` (line 132; public)
  - `public(self) -> dict[str, Any]` (line 135; public) — Aggregate-safe: no question text, no selection text, aliased ids.
  - `private(self) -> dict[str, Any]` (line 143; public)
- `unit_refs(unit: CandidateUnit) -> tuple[SpanRef, ...]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 149)
- `class SelectionWithheld(RuntimeError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 161) — A question's selection is material the policy withholds.
- `freeze_context(question: BankQuestion, snapshot: CorpusSnapshot) -> BankQuestion` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 165) — Freeze the question's one policy-checked context (idempotent).
- `smoke_bank(snapshot: CorpusSnapshot, *, count: int=pins.SMOKE_CASES) -> tuple[list[BankQuestion], dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 212) — 16 pipeline cases from the corpus itself: lookups of numbered blocks, deictic selections with a resolved dependency, distant dependencies, exact-term lookups and off-topic no-support controls.
- `event_protection(handle: Any) -> tuple[Callable[[Mapping[str, Any]], str | None], Callable[[], None]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 319) — The production authority on what of a learner's question may reach a model (``learnloop.learner_protection.PastWork.question_reason``): the question on record, its item's protection (exam and held-out material, reservations, cold checks, probes, an unreadable or unknown item), t…
- `logged_questions(handle: Any, snapshot: CorpusSnapshot) -> tuple[list[BankQuestion], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 345) — The copy's answered learner questions through :func:`logged_bank`, each event's provenance resolved by :func:`event_protection`.
- `logged_bank(snapshot: CorpusSnapshot, events: Sequence[Mapping[str, Any]], *, protection: Callable[[Mapping[str, Any]], str | None] | None=None) -> tuple[list[BankQuestion], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 356) — Every eligible answered learner question, with its actual selection (Reader) and no fabricated selection or reference otherwise.
- `class WrittenQuestion(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 431)
- `class WrittenQuestions(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 439)
- `class Seed` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 444)
- `distance_rule(unit_order: Sequence[str], window_of: Mapping[str, str])` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 466) — ``distant(a, b)``: in different grouped windows, or at least ``MIN_UNIT_GAP`` units apart (a short source fits one window).
- `lexical_links(units: Sequence[CandidateUnit], distant_pair: Any, *, min_shared: int=2, max_df: int=3) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 479) — ``{unit: earlier unit}`` of the same extraction in another window that shares the most rare terms (document frequency <= ``max_df``, at least ``min_shared``): the distant-dependency fallback where no numbered reference links them.
- `plan_seeds(snapshot: CorpusSnapshot, *, strata: Mapping[str, int] | None=None) -> tuple[list[Seed], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 514) — Development seeds per stratum, from development families only, deterministic; each seed carries same-source distractors.
- `writer_prompt(snapshot: CorpusSnapshot, seeds: Sequence[Seed]) -> tuple[str, dict[str, Seed], dict[str, str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 612) — One writer prompt for a batch of seeds; returns the ref maps.
- `write_questions(snapshot: CorpusSnapshot, seeds: Sequence[Seed], caller: Any, *, batch: int=6) -> tuple[list[BankQuestion], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 633) — Development questions from the writer (one call per batch of seeds).
- `check_rubric_frozen(rubric: str=RELEVANCE_RUBRIC) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 726) — The rubric's SHA-256, or ``RuntimeError`` when it is not the frozen one (``pins.LABEL_RUBRIC_SHA256``).
- `class CandidateLabel(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 748)
- `class LabelPass(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 753)
- `class AdjudicatedLabels(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 759)
- `class SufficiencyPass(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 781)
- `label_context(snapshot: CorpusSnapshot, unit: CandidateUnit) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 786) — What a labeller reads of a candidate: its complete text, section and the preceding numbered label (no arm, no rank, no score).
- `pool_for(question: BankQuestion, rankings: Mapping[str, Sequence[str]], snapshot: CorpusSnapshot, *, depth: int=pins.POOL_DEPTH, non_hits: int=4) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 796) — The labelled pool: each arm's top ``depth``, the writer's proposals, the units of any reference evidence, and a seeded sample of non-hits.
- `label_prompt(question: BankQuestion, candidates: Mapping[str, Mapping[str, Any]], pass_index: int, *, relevance_only: bool=False) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 814)
- `sufficiency_prompt(question: BankQuestion, candidates: Mapping[str, Mapping[str, Any]], pass_index: int) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 823)
- `class QuestionLabels` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 832)
- `label_question(question: BankQuestion, pool: Sequence[str], snapshot: CorpusSnapshot, caller: Any, *, batch: int=40) -> QuestionLabels` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 869) — Two blinded passes in different orders (refs are reassigned per pass).
- `needs_audit(labels: QuestionLabels) -> str | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 931) — Why the adjudicator must see this question, else None (it may still be sampled).
- `adjudication_problems(result: AdjudicatedLabels, refs: Mapping[str, str], labels: QuestionLabels) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 945) — Why an adjudicator verdict cannot be accepted (empty: well formed).
- `adjudicate(question: BankQuestion, labels: QuestionLabels, snapshot: CorpusSnapshot, caller: Any) -> QuestionLabels` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 992) — The named adjudicator decides labels and sets, seeing both passes blinded to model; an unresolved or malformed verdict leaves sufficiency unresolved and blocks the question (S1).
- `accept_agreed(labels: QuestionLabels) -> QuestionLabels` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 1041) — An unaudited agreement: model-only labels (reported as such).
- `audit_plan(all_labels: Sequence[QuestionLabels], *, share: float=pins.AUDIT_SAMPLE_SHARE) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 1050) — ``{query_id: reason}`` the adjudicator audits: every mandatory case and a seeded ``share`` of the rest (agreements, negatives, unanswerable).
- `evidence_sets_from_labels(labels: QuestionLabels, snapshot: CorpusSnapshot) -> list[EvidenceSet]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 1067)
- `reference_dependencies(snapshot: CorpusSnapshot, question: BankQuestion) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 1075) — Deterministic reference following for a known selection (identical for every arm): the units its numbered references resolve to.

### Module constants

- `RELEVANCE_ORDER` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 49)
- `GAIN` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 50)
- `WRITER_VERSION` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 53)
- `LABEL_VERSION` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 54)
- `ADJUDICATE_VERSION` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 55)
- `NO_SUPPORT_SMOKE` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 57)
- `SELECTION_CONTEXT_CHARS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 158)
- `LOGGED_CONTEXTS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 309)
- `WRITER_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 419)
- `_TERM` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 456)
- `_STOP` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 457)
- `MIN_UNIT_GAP` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 463)
- `RELEVANCE_RUBRIC` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 705)
- `LABEL_RUBRIC_VERSION` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 723)
- `SETS_RULE` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 739)
- `LABEL_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 745)
- `RELEVANCE_ONLY_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 766)
- `SUFFICIENCY_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 771)

## Internal implementation anchors

- `_sha(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 63)
- `_query_id(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 153)
- `_unresolved_reasons() -> frozenset[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 312)
- `_intent(stratum: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 510)
- `_sets_from(chosen_sets: Sequence[Sequence[str]], refs: Mapping[str, str]) -> tuple[list[frozenset[str]], int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 850) — Well-formed sets (every ref known, none repeated) and the malformed count.
- `_judge(caller: Any, **kwargs: Any) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py), line 863)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `BankQuestion`, `stable_order`; statically calls `stable_order`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `unit_refs`; statically calls `unit_refs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `BankQuestion`, `LABEL_VERSION`, `QuestionLabels`, `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `logged_questions`, `plan_seeds`, `smoke_bank`, `write_questions`; statically calls `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `logged_questions`, `plan_seeds`, `smoke_bank`, `write_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `BankQuestion`, `CandidateLabel`, `QuestionLabels`, `RELEVANCE_ORDER`, `RELEVANCE_RUBRIC`, `evidence_sets_from_labels`, `label_context`, `stable_order`; statically calls `evidence_sets_from_labels`, `label_context`, `stable_order`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `BankQuestion`, `QuestionLabels`, `RELEVANCE_ORDER`, `unit_refs`; statically calls `unit_refs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `logged_questions`; statically calls `logged_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `BankQuestion`, `QuestionLabels`, `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `plan_seeds`, `pool_for`, `smoke_bank`, `stable_order`, `write_questions`; statically calls `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `plan_seeds`, `pool_for`, `smoke_bank`, `stable_order`, `write_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `BankQuestion`, `RELEVANCE_RUBRIC`, `Seed`, `writer_prompt`; statically calls `writer_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `logged_questions`, `plan_seeds`, `smoke_bank`, `writer_prompt`; statically calls `logged_questions`, `plan_seeds`, `smoke_bank`, `writer_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `BankQuestion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CandidateUnit`, `CorpusSnapshot`, `alias`; calls `alias`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `Selection`, `quote_covered`; calls `Selection`, `quote_covered`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `preceding_text`; calls `preceding_text`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PastWork`, `module`; calls `PastWork`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_bank.py](../../../../../../../tests/test_e0_bank.py) — direct import
  - `test_distant_seeds_use_references_then_shared_terms`
  - `test_logged_questions_keep_their_real_selection_and_never_get_one_invented`
  - `test_seeds_come_only_from_development_families`
  - `test_the_audit_samples_twenty_percent_of_agreements`
  - `test_the_pool_includes_every_arm_proposals_and_seeded_non_hits`
  - `test_the_smoke_bank_has_16_deterministic_cases_from_permitted_text`
  - `test_the_writer_pipeline_with_a_fake_and_its_admission`
  - `test_two_blinded_passes_audit_plan_and_adjudication`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_an_edited_rubric_refuses_to_load`
  - `test_both_label_passes_are_sonnet_and_the_rubric_is_frozen_by_hash`
  - `test_the_reuse_estimate_reprices_every_label_request_at_todays_pins`
  - `test_the_two_passes_stay_independent_requests_in_different_orders`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f10_verdicts_enter_judgment_ledger_once`
  - `test_f12_system_arms_use_find_sources_and_an_unverified_intent_is_no_ranking`
  - `test_f13_a_conjunction_split_across_batches_is_found_by_the_joint_review`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
  - `test_f3_a_changed_identity_never_reuses_a_checkpoint`
  - `test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request`
  - `test_f6_a_quote_over_withheld_spans_falls_back_to_the_selected_block`
  - `test_f6_deictic_questions_carry_their_own_selection_to_every_role`
  - `test_f7_a_malformed_adjudication_leaves_sufficiency_unresolved`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding`
  - `test_f20_a_failed_delegated_comparison_is_missing_not_ranked`
  - `test_f6_a_permitted_quote_is_still_delivered`
  - `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges`
  - `test_f7_a_set_member_is_checked_against_the_merged_final_labels`
  - `test_f7_an_inherited_supporting_label_still_completes_a_set`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h6_a_practice_question_is_rejected_unless_its_provenance_is_cleared`
  - `test_h6_the_production_protection_rejects_an_unknown_item_question`
  - `test_h7_a_quote_without_complete_canonical_coverage_is_dropped`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m11_a_charged_but_unrecorded_request_is_blocked_never_resent`
  - `test_m11_a_settled_response_is_recovered_from_the_receipts`
  - `test_m11_concurrent_workers_send_one_request_and_a_known_failure_may_retry`
  - `test_m13_an_arm_that_fails_every_logged_question_stops_verdicts`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_a_response_without_usage_keeps_the_whole_reservation`
  - `test_a_role_call_goes_through_the_messages_api_transport`
  - `test_each_post_is_admitted_first_at_its_hard_maximum_and_settled_from_usage`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_failed_role_call_leaves_a_safe_failure_record`
  - `test_a_non_item_failure_still_stops_the_labels`
  - `test_label_as_extra_misspelled_key_is_named_safely_and_repaired_once`
  - `test_label_bs_two_different_objects_with_prose_between_get_one_repair`
  - `test_one_questions_unusable_labels_skip_that_question_only`
  - `test_one_valid_object_inside_prose_or_a_fence_parses_without_a_repair`
- [tests/test_e1_supplement.py](../../../../../../../tests/test_e1_supplement.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains bank within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/bank.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/bank.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
