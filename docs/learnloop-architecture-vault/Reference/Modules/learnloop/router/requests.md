---
title: "learnloop.router.requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/requests.py"
source_paths:
  - "src/learnloop/router/requests.py"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.requests module"
  - "src/learnloop/router/requests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.requests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.requests` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R2b/R2c: the two models' requests and the strict parsing of their answers.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py) |
| Source lines | 687 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

- `class RouterResponseInvalid(ValueError)` ([source](../../../../../../src/learnloop/router/requests.py), line 76) — A model's answer broke the request's contract; that model's answer is not used.
- `class BlockOption` ([source](../../../../../../src/learnloop/router/requests.py), line 84) — One option the models choose among: a reversible candidate, or stop for today.
- `class SensorTopic` ([source](../../../../../../src/learnloop/router/requests.py), line 92)
- `option_description(*, why: str, kind: str, item_count: int, est_minutes: float, topics: Sequence[str], section: str | None=None) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 97) — "Eigenvalues again, before it slips.
- `class EvidenceRef` ([source](../../../../../../src/learnloop/router/requests.py), line 120) — An attempt on the card the LLM may cite (``evidence_ids``).
- `evidence_from_card(card_json: Mapping[str, Any] | None) -> tuple[EvidenceRef, ...]` ([source](../../../../../../src/learnloop/router/requests.py), line 127) — The card's citable evidence: each shown recent attempt, labelled plainly.
- `state_text(card_text: str, options: Sequence[BlockOption], *, similar: Sequence[str]=(), evidence: Sequence[EvidenceRef]=(), extra: Sequence[str]=()) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 148) — The state both models read (the Decider's ``state``, the LLM prompt's body).
- `sensor_question_name(kind: str, learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 195)
- `class BoundaryRequest` ([source](../../../../../../src/learnloop/router/requests.py), line 200) — One block decision's request to both models (built once, at prefetch).
  - `question_set_version(self) -> str` (line 209; public)
  - `llm_schema_version(self) -> str` (line 213; public)
  - `refs(self) -> tuple[str, ...]` (line 217; public)
  - `decider_questions(self) -> dict[str, Question]` (line 220; public)
  - `llm_prompt(self) -> str` (line 236; public)
- `class RestraintRequest` ([source](../../../../../../src/learnloop/router/requests.py), line 263) — A follow-up's restraint decision (``plan_interrupt``): one ``intervene_now`` noul.
  - `decider_questions(self) -> dict[str, Question]` (line 272; public)
  - `llm_prompt(self) -> str` (line 275; public)
- `class OptionProbability(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 303)
- `class TopicProbability(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 308)
- `class RouterLLMAnswerV1(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 313) — ``router_llm_v1``: the block distribution, a rationale and its evidence ids.
- `class RouterLLMAnswerV2(RouterLLMAnswerV1)` ([source](../../../../../../src/learnloop/router/requests.py), line 321) — ``router_llm_v2`` (R2c): v1 plus the logged-only sensors.
- `class RouterLLMRestraintAnswer(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 328) — ``router_llm_restraint_v1``: P(interrupt now does more good) and a rationale.
- `class OptionForecastV3(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 345)
- `class ReferenceForecastV3(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 353)
- `class RouterLLMChoiceV3(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 360) — ``router_llm_choice_v3``: a probability per option (every one positive), per-option forecasts, the reference row's forecasts, at most three sentences of rationale and the evidence ids they rely on.
- `class RouterLLMRestraintV3(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 370) — The LLM policy on a mid-block follow-up (``plan_interrupt``): P(interrupting now is the better choice).
- `class PolicyRequest` ([source](../../../../../../src/learnloop/router/requests.py), line 388) — The LLM policy's request for one decision (built once, in the prefetch, frozen with the boundary key).
  - `llm_schema_version(self) -> str` (line 400; public)
  - `refs(self) -> tuple[str, ...]` (line 404; public)
  - `llm_prompt(self) -> str` (line 407; public)
- `class ParsedPolicy` ([source](../../../../../../src/learnloop/router/requests.py), line 440) — The LLM policy's validated answer.
- `parse_llm_policy(answer: Any, request: PolicyRequest) -> ParsedPolicy` ([source](../../../../../../src/learnloop/router/requests.py), line 461) — Validate the LLM policy's answer (fails closed): every option exactly once with a positive probability, every forecast strictly in (0, 1), the reference row's forecasts present.
- `parse_llm_policy_restraint(answer: Any) -> tuple[float, str | None, tuple[str, ...]]` ([source](../../../../../../src/learnloop/router/requests.py), line 501)
- `llm_result_model(schema_version: str) -> type[_Wire]` ([source](../../../../../../src/learnloop/router/requests.py), line 512)
- `class ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 539) — A model's answer to a block decision, validated.
- `parse_llm_choice(answer: Any, request: BoundaryRequest) -> ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 584) — Validate the LLM's block answer against the request (fails closed).
- `parse_decider_choice(result: DecisionResult, request: BoundaryRequest) -> ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 608) — The Decider's typed answers (already parsed strictly by the client) for one block decision.
- `parse_llm_restraint(answer: Any) -> tuple[float, str | None]` ([source](../../../../../../src/learnloop/router/requests.py), line 627)
- `parse_decider_restraint(result: DecisionResult) -> float` ([source](../../../../../../src/learnloop/router/requests.py), line 633)

### Module constants

- `PURPOSE` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 57)
- `QUESTION_SET_V1` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 58)
- `QUESTION_SET_V2` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 59)
- `RESTRAINT_QUESTION_SET` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 60)
- `LLM_SCHEMA_V1` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 61)
- `LLM_SCHEMA_V2` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 62)
- `LLM_RESTRAINT_SCHEMA` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 63)
- `MAX_SENSOR_LOS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 65)
- `MAX_RATIONALE_SENTENCES` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 66)
- `CHOOSE_BLOCK` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 67)
- `INTERVENE_NOW` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 68)
- `TEACH_FIRST` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 69)
- `WILL_PASS_NEXT` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 70)
- `SENSORS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 71)
- `OPTION_LIMIT` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 73)
- `STOP_DESCRIPTION` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 113)
- `STOP_OFFER_DESCRIPTION` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 115)
- `CHOOSE_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 176)
- `TEACH_FIRST_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 181)
- `WILL_PASS_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 185)
- `INTERVENE_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 188)
- `NO_INTERVENTION_DESCRIPTION` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 290)
- `LLM_POLICY_SCHEMA` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 338)
- `LLM_POLICY_RESTRAINT_SCHEMA` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 339)
- `POLICY_LAGS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 342)
- `POLICY_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 378)

### Explicit exports

`__all__` declares:

- `LLM_POLICY_RESTRAINT_SCHEMA`
- `LLM_POLICY_SCHEMA`
- `POLICY_LAGS`
- `ParsedPolicy`
- `PolicyRequest`
- `RouterLLMChoiceV3`
- `RouterLLMRestraintV3`
- `parse_llm_policy`
- `parse_llm_policy_restraint`
- `BlockOption`
- `BoundaryRequest`
- `CHOOSE_BLOCK`
- `EvidenceRef`
- `INTERVENE_NOW`
- `LLM_RESTRAINT_SCHEMA`
- `LLM_SCHEMA_V1`
- `LLM_SCHEMA_V2`
- `MAX_RATIONALE_SENTENCES`
- `MAX_SENSOR_LOS`
- `OptionProbability`
- `PURPOSE`
- `ParsedChoice`
- `QUESTION_SET_V1`
- `QUESTION_SET_V2`
- `RESTRAINT_QUESTION_SET`
- `RestraintRequest`
- `RouterLLMAnswerV1`
- `RouterLLMAnswerV2`
- `RouterLLMRestraintAnswer`
- `RouterResponseInvalid`
- `SENSORS`
- `STOP_DESCRIPTION`
- `STOP_OFFER_DESCRIPTION`
- `SensorTopic`
- `TEACH_FIRST`
- `TopicProbability`
- `WILL_PASS_NEXT`
- `evidence_from_card`
- `llm_result_model`
- `option_description`
- `parse_decider_choice`
- `parse_decider_restraint`
- `parse_llm_choice`
- `parse_llm_restraint`
- `sensor_question_name`
- `state_text`

## Internal implementation anchors

- `class _Wire(WireModel)` ([source](../../../../../../src/learnloop/router/requests.py), line 298) — The LLM's answers cross the provider boundary: the strict output schema every structured transport sends requires a ``WireModel``.
- `_open_probability(value: Any, what: str) -> float` ([source](../../../../../../src/learnloop/router/requests.py), line 450)
- `_lags(entry: Mapping[str, Any], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/requests.py), line 457)
- `_probability(value: Any, what: str) -> float` ([source](../../../../../../src/learnloop/router/requests.py), line 522)
- `_as_mapping(answer: Any) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/router/requests.py), line 530)
- `_distribution(entries: Any, refs: Sequence[str], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/requests.py), line 549)
- `_sensor_answers(entries: Any, topics: Sequence[str], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/requests.py), line 568)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `BlockOption`, `BoundaryRequest`, `PolicyRequest`, `RestraintRequest`, `evidence_from_card`, `parse_decider_restraint`, `parse_llm_policy`, `parse_llm_policy_restraint`, `state_text`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`; statically calls `BlockOption`, `BoundaryRequest`, `RestraintRequest`, `SensorTopic`, `evidence_from_card`, `option_description`, `parse_decider_restraint`, `parse_llm_restraint`, `state_text`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `module`; statically calls `llm_result_model`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceAnswer`, `ChoiceQuestion`, `DecisionResult`, `NoulAnswer`, `NoulQuestion`, `Question`; calls `ChoiceQuestion`, `NoulQuestion`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_1_at_the_tag_fg1s_gate_is_the_two_policy_mix_with_its_trace`
  - `test_r5_1_below_the_tag_and_with_the_objective_off_fg1s_gate_is_unchanged`
- [tests/test_router_r2b_requests.py](../../../../../../tests/test_router_r2b_requests.py) — direct import
  - `test_a_fake_llm_naming_an_unknown_block_is_rejected_at_parse`
  - `test_every_router_answer_model_has_the_strict_schema_the_transports_send`
  - `test_malformed_distributions_fail_closed`
  - `test_sensors_name_only_the_asked_topics`
  - `test_the_decider_gets_typed_questions_and_a_body_with_no_unknown_field`
  - `test_the_llm_distribution_is_renormalized_and_missing_ids_are_zero`
  - `test_the_llm_prompt_lists_the_options_and_the_plain_word_rules`
- [tests/test_router_r2c_teach_back.py](../../../../../../tests/test_router_r2c_teach_back.py) — direct import
  - `test_a_graded_teach_back_is_summarized_into_the_next_card`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_the_section_is_in_the_typed_card_its_text_and_its_hash`

## Modification guidance

- Make changes here when the responsibility remains requests within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
