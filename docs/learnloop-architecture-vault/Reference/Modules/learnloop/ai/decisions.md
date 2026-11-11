---
title: "learnloop.ai.decisions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/decisions.py"
source_paths:
  - "src/learnloop/ai/decisions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.decisions module"
  - "src/learnloop/ai/decisions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.decisions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.decisions` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: The decision-model contract: typed questions in, typed probabilities out.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py) |
| Source lines | 336 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class DecisionResponseInvalid(AIInvalidOutput)` ([source](../../../../../../src/learnloop/ai/decisions.py), line 39) — A paid decision response did not match the documented contract.
- `class NoulQuestion` ([source](../../../../../../src/learnloop/ai/decisions.py), line 50) — A yes/no question; ``when_true``/``when_false`` describe each answer.
  - `__post_init__(self) -> None` (line 57; internal)
  - `wire(self) -> dict[str, Any]` (line 66; public)
- `class ChoiceQuestion` ([source](../../../../../../src/learnloop/ai/decisions.py), line 74) — Pick one of 1-255 named options; a description may be None.
  - `__post_init__(self) -> None` (line 80; internal)
  - `wire(self) -> dict[str, Any]` (line 90; public)
- `class ScoreQuestion` ([source](../../../../../../src/learnloop/ai/decisions.py), line 95) — Rate on an ordered rubric of 1-10 levels; index i is score i.
  - `__post_init__(self) -> None` (line 101; internal)
  - `wire(self) -> dict[str, Any]` (line 109; public)
- `class NoulAnswer` ([source](../../../../../../src/learnloop/ai/decisions.py), line 117)
- `class ChoiceAnswer` ([source](../../../../../../src/learnloop/ai/decisions.py), line 122)
- `class ScoreAnswer` ([source](../../../../../../src/learnloop/ai/decisions.py), line 129)
- `class DecisionResult` ([source](../../../../../../src/learnloop/ai/decisions.py), line 139) — Typed answers plus the provider's own accounting for the receipt.
- `class DecisionClient(Protocol)` ([source](../../../../../../src/learnloop/ai/decisions.py), line 153) — One request per call: the same ``state`` answers every named question.
  - `decide(self, state: DecisionState, questions: Mapping[str, Question], *, purpose: str) -> DecisionResult` (line 160; public)
- `validate_questions(questions: Mapping[str, Question]) -> dict[str, Question]` ([source](../../../../../../src/learnloop/ai/decisions.py), line 166)
- `validate_state(state: DecisionState) -> DecisionState` ([source](../../../../../../src/learnloop/ai/decisions.py), line 179)
- `request_body(model: str, state: DecisionState, questions: Mapping[str, Question]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/decisions.py), line 187) — The complete wire body: ``model``, ``state`` and ``questions``, nothing else.
- `choice_probabilities(answer: ChoiceAnswer, question: ChoiceQuestion) -> dict[str, float]` ([source](../../../../../../src/learnloop/ai/decisions.py), line 235) — Validate a typed choice distribution before a policy takes its argmax.
- `parse_response(payload: Any, questions: Mapping[str, Question]) -> DecisionResult` ([source](../../../../../../src/learnloop/ai/decisions.py), line 278) — Parse a 200 body against the questions that were asked; fail closed.

### Module constants

- `MAX_QUESTIONS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 30)
- `MAX_CHOICE_OPTIONS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 31)
- `MAX_SCORE_LEVELS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 32)
- `PROBABILITY_SUM_TOLERANCE` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 34)
- `_RESPONSE_FIELDS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 203)
- `_USAGE_FIELDS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 204)
- `_ANSWER_FIELDS` ([src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py), line 205)

### Explicit exports

`__all__` declares:

- `Answer`
- `ChoiceAnswer`
- `ChoiceQuestion`
- `DecisionClient`
- `DecisionResponseInvalid`
- `DecisionResult`
- `DecisionState`
- `MAX_CHOICE_OPTIONS`
- `MAX_QUESTIONS`
- `MAX_SCORE_LEVELS`
- `NoulAnswer`
- `NoulQuestion`
- `Question`
- `ScoreAnswer`
- `ScoreQuestion`
- `choice_probabilities`
- `parse_response`
- `request_body`
- `validate_questions`
- `validate_state`

## Internal implementation anchors

- `_text(value: str, what: str) -> str` ([source](../../../../../../src/learnloop/ai/decisions.py), line 43)
- `_probability(value: Any, what: str) -> float` ([source](../../../../../../src/learnloop/ai/decisions.py), line 212)
- `_count(value: Any, what: str) -> int` ([source](../../../../../../src/learnloop/ai/decisions.py), line 220)
- `_distribution(values: Any, expected: Sequence[str], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/ai/decisions.py), line 226)
- `_answer(name: str, question: Question, raw: Any) -> Answer` ([source](../../../../../../src/learnloop/ai/decisions.py), line 240)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `ChoiceQuestion`, `choice_probabilities`; statically calls `ChoiceQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `NoulQuestion`; statically calls `NoulQuestion`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `DecisionResult`, `DecisionState`, `Question`, `parse_response`, `request_body`, `validate_questions`; statically calls `parse_response`, `request_body`, `validate_questions`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `ChoiceQuestion`, `NoulQuestion`, `ScoreQuestion`, `request_body`; statically calls `ChoiceQuestion`, `NoulQuestion`, `ScoreQuestion`, `request_body`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `request_body`; statically calls `request_body`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ChoiceQuestion`, `MAX_QUESTIONS`, `choice_probabilities`; statically calls `choice_probabilities`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `ChoiceQuestion`, `MAX_CHOICE_OPTIONS`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `choice_probabilities`; statically calls `choice_probabilities`
- [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]] — imports `ChoiceQuestion`, `MAX_QUESTIONS`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `DecisionResponseInvalid`, `NoulQuestion`, `request_body`; statically calls `NoulQuestion`, `request_body`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `ChoiceQuestion`, `ScoreQuestion`, `choice_probabilities`; statically calls `ChoiceQuestion`, `ScoreQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `ChoiceQuestion`; statically calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `ChoiceQuestion`, `choice_probabilities`; statically calls `ChoiceQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `ChoiceAnswer`, `ChoiceQuestion`, `DecisionResult`, `NoulAnswer`, `NoulQuestion`, `Question`; statically calls `ChoiceQuestion`, `NoulQuestion`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `ChoiceQuestion`, `MAX_CHOICE_OPTIONS`, `MAX_QUESTIONS`, `NoulQuestion`, `choice_probabilities`; statically calls `ChoiceQuestion`, `NoulQuestion`, `choice_probabilities`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] and 17 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad_fakes.py](../../../../../../tests/ad_fakes.py) — direct import
- [tests/decider_fakes.py](../../../../../../tests/decider_fakes.py) — direct import
- [tests/facet_identity_fakes.py](../../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/facet_span_support_helpers.py](../../../../../../tests/facet_span_support_helpers.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/reader_ca3_compare_anywhere_helpers.py](../../../../../../tests/reader_ca3_compare_anywhere_helpers.py) — direct import
- [tests/required_method_authority_helpers.py](../../../../../../tests/required_method_authority_helpers.py) — direct import
- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/test_decider_client.py](../../../../../../tests/test_decider_client.py) — direct import
  - `test_a_malformed_paid_answer_keeps_its_usage_on_the_receipt`
  - `test_a_rejected_request_keeps_its_status_and_redacted_error_on_the_receipt`
  - `test_a_transport_error_echoing_a_key_reaches_neither_receipt_nor_caller`
  - `test_an_unreachable_endpoint_is_recorded_as_network_without_a_status`
  - `test_choice_answers_must_cover_the_asked_options`
  - `test_error_statuses_surface_without_parsing`
  - `test_fake_endpoint_answers_400_to_an_unknown_field_and_the_client_never_sends_one`
  - `test_missing_key_and_oversized_state_refuse_before_any_request`
  - `test_openrouter_dialect_posts_the_typed_request_and_parses_typed_answers`
  - `test_parsing_fails_closed_on_any_contract_change`
  - `test_perplexity_dialect_uses_its_path_key_and_model`
  - `test_question_classes_refuse_invalid_shapes`
  - `test_receipt_carries_body_usage_cost_model_and_labels`
  - `test_request_body_holds_exactly_model_state_and_typed_questions`
  - `test_requests_refuse_untyped_questions_and_bad_counts`
  - `test_score_answers_must_match_the_rubric`
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_refusal_records.py](../../../../../../tests/test_refusal_records.py) — direct import
- [tests/test_router_g7_fallback.py](../../../../../../tests/test_router_g7_fallback.py) — direct import
  - `test_an_error_or_an_invalid_answer_falls_back`
- [tests/test_router_r2b_requests.py](../../../../../../tests/test_router_r2b_requests.py) — direct import
  - `test_the_decider_gets_typed_questions_and_a_body_with_no_unknown_field`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_decider_naming_an_option_it_was_not_asked_is_rejected`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_cancellation_is_never_a_fallback`
  - `test_a_tied_batch_question_has_no_choice`
  - `test_a_tied_top_option_is_no_answer_and_hands_over`
  - `test_decider_receipt_and_spend_ignore_llm_output_budget`
  - `test_route_decision_fallback_and_switch`
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import
- [tests/tier1_decider_helpers.py](../../../../../../tests/tier1_decider_helpers.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/decisions.py](../../../../../../src/learnloop/ai/decisions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
