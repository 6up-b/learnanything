---
title: "learnloop.router.requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/requests.py"
source_paths:
  - "src/learnloop/router/requests.py"
source_commit: "c11b6179c76d77eb4ef639d03f4fb112e12a75a7"
source_commit_timestamp: "2026-11-03T22:03:31-05:00"
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
| Source lines | 495 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c11b6179c76d77eb4ef639d03f4fb112e12a75a7` |
| Commit timestamp | `2026-11-03T22:03:31-05:00` |

## Public API

- `class RouterResponseInvalid(ValueError)` ([source](../../../../../../src/learnloop/router/requests.py), line 76) — A model's answer broke the request's contract; that model's answer is not used.
- `class BlockOption` ([source](../../../../../../src/learnloop/router/requests.py), line 84) — One option the models choose among: a reversible candidate, or stop for today.
- `class SensorTopic` ([source](../../../../../../src/learnloop/router/requests.py), line 92)
- `option_description(*, why: str, kind: str, item_count: int, est_minutes: float, topics: Sequence[str], section: str | None=None) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 97) — "Eigenvalues again, before it slips.
- `class EvidenceRef` ([source](../../../../../../src/learnloop/router/requests.py), line 117) — An attempt on the card the LLM may cite (``evidence_ids``).
- `evidence_from_card(card_json: Mapping[str, Any] | None) -> tuple[EvidenceRef, ...]` ([source](../../../../../../src/learnloop/router/requests.py), line 124) — The card's citable evidence: each shown recent attempt, labelled plainly.
- `state_text(card_text: str, options: Sequence[BlockOption], *, similar: Sequence[str]=(), evidence: Sequence[EvidenceRef]=(), extra: Sequence[str]=()) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 145) — The state both models read (the Decider's ``state``, the LLM prompt's body).
- `sensor_question_name(kind: str, learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/router/requests.py), line 192)
- `class BoundaryRequest` ([source](../../../../../../src/learnloop/router/requests.py), line 197) — One block decision's request to both models (built once, at prefetch).
  - `question_set_version(self) -> str` (line 206; public)
  - `llm_schema_version(self) -> str` (line 210; public)
  - `refs(self) -> tuple[str, ...]` (line 214; public)
  - `decider_questions(self) -> dict[str, Question]` (line 217; public)
  - `llm_prompt(self) -> str` (line 233; public)
- `class RestraintRequest` ([source](../../../../../../src/learnloop/router/requests.py), line 260) — A follow-up's restraint decision (``plan_interrupt``): one ``intervene_now`` noul.
  - `decider_questions(self) -> dict[str, Question]` (line 269; public)
  - `llm_prompt(self) -> str` (line 272; public)
- `class OptionProbability(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 300)
- `class TopicProbability(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 305)
- `class RouterLLMAnswerV1(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 310) — ``router_llm_v1``: the block distribution, a rationale and its evidence ids.
- `class RouterLLMAnswerV2(RouterLLMAnswerV1)` ([source](../../../../../../src/learnloop/router/requests.py), line 318) — ``router_llm_v2`` (R2c): v1 plus the logged-only sensors.
- `class RouterLLMRestraintAnswer(_Wire)` ([source](../../../../../../src/learnloop/router/requests.py), line 325) — ``router_llm_restraint_v1``: P(interrupt now does more good) and a rationale.
- `llm_result_model(schema_version: str) -> type[_Wire]` ([source](../../../../../../src/learnloop/router/requests.py), line 332)
- `class ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 357) — A model's answer to a block decision, validated.
- `parse_llm_choice(answer: Any, request: BoundaryRequest) -> ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 402) — Validate the LLM's block answer against the request (fails closed).
- `parse_decider_choice(result: DecisionResult, request: BoundaryRequest) -> ParsedChoice` ([source](../../../../../../src/learnloop/router/requests.py), line 426) — The Decider's typed answers (already parsed strictly by the client) for one block decision.
- `parse_llm_restraint(answer: Any) -> tuple[float, str | None]` ([source](../../../../../../src/learnloop/router/requests.py), line 445)
- `parse_decider_restraint(result: DecisionResult) -> float` ([source](../../../../../../src/learnloop/router/requests.py), line 451)

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
- `CHOOSE_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 173)
- `TEACH_FIRST_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 178)
- `WILL_PASS_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 182)
- `INTERVENE_INSTRUCTIONS` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 185)
- `NO_INTERVENTION_DESCRIPTION` ([src/learnloop/router/requests.py](../../../../../../src/learnloop/router/requests.py), line 287)

### Explicit exports

`__all__` declares:

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

- `class _Wire(WireModel)` ([source](../../../../../../src/learnloop/router/requests.py), line 295) — The LLM's answers cross the provider boundary: the strict output schema every structured transport sends requires a ``WireModel``.
- `_probability(value: Any, what: str) -> float` ([source](../../../../../../src/learnloop/router/requests.py), line 340)
- `_as_mapping(answer: Any) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/router/requests.py), line 348)
- `_distribution(entries: Any, refs: Sequence[str], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/requests.py), line 367)
- `_sensor_answers(entries: Any, topics: Sequence[str], what: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/requests.py), line 386)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

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
