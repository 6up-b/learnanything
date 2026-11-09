---
title: "learnloop.experiments.contextual_embeddings.anthropic_api"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/anthropic_api.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/anthropic_api.py"
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
  - "learnloop.experiments.contextual_embeddings.anthropic_api module"
  - "src/learnloop/experiments/contextual_embeddings/anthropic_api.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.anthropic_api`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.anthropic_api` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's experiment-only Anthropic Messages API transport (re-plan 2026-10-22).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py) |
| Source lines | 386 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class BodyGrammarError(ValueError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 59) — A request body outside the grammar; nothing was sent.
- `check_body(body: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 63) — Refuse any body outside the grammar: an unknown key (``tools`` above all), a wrong type, more than one user turn, or non-text content.
- `json_instructions(result_model: type[BaseModel]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 109) — The system prompt: answer with one JSON object of the result schema (no ``output_config``: the body grammar has no structured-output key).
- `extract_json(text: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 118) — The JSON object in a text answer (a stray code fence tolerated).
- `schema_fields(result_model: type[BaseModel]) -> frozenset[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 135) — Every field name of the result schema, nested models included: the names a safe validation reason may print (anything else is ``?``).
- `validation_reason(error: Any, fields: frozenset[str]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 158) — A pydantic ``ValidationError`` as ``loc:type`` codes (no input, no message).
- `parse_answer(text: str, result_model: type[BaseModel]) -> BaseModel` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 172) — The ONE result object in a text answer (paid-run round 2).
- `repair_prompt(text: str, reason: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 216) — The one repair request (paid-run round 2): the model's own answer back with the SAFE reason it failed, asking for exactly one valid object.
- `class AnthropicMessagesClient` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 226) — One role's client: its pin's model, the Messages API, one POST per admitted request.
  - `__init__(self, pin: RolePin, *, key_env: str | None=None, environ: Mapping[str, str] | None=None, transport: Any=None, url: str=pins.ANTHROPIC_MESSAGES_URL, sleep: Callable[[float], None]=time.sleep) -> None` (line 233; internal)
  - `supports(self, capability: str) -> bool` (line 251; public)
  - `body(self, system: str, prompt: str, max_tokens: int) -> dict[str, Any]` (line 255; public)
  - `wire_prompt(self, prompt: str, result_model: type[BaseModel]) -> list[str]` (line 261; public) — What a request sends as text, in order: the admission's input bound and the receipt's prompt identity.
  - `_headers(self) -> dict[str, str]` (line 267; internal)
  - `send(self, body: Mapping[str, Any], *, purpose: str, prompt_identity: Any) -> Mapping[str, Any]` (line 273; public) — ONE admitted POST: the active request gate admits it inside ``model_call`` before it is sent and settles it from ``usage``.
  - `structured(self, *, purpose: str, prompt: str, result_model: type[BaseModel], max_tokens: int) -> BaseModel` (line 310; public) — The role's answer: one admitted POST (plus admitted retries of a transient failure), parsed and validated against ``result_model``.
  - `_post_with_retries(self, body: Mapping[str, Any], *, purpose: str, prompt_identity: Any) -> Mapping[str, Any]` (line 336; internal)
  - `_details(payload: Mapping[str, Any], max_tokens: int) -> dict[str, Any]` (line 348; internal) — Safe numbers of a response: its stop_reason (allowlisted), token counts, the max_tokens sent and the content block types.
  - `_answer_text(self, payload: Mapping[str, Any], max_tokens: int, *, repaired: bool=False) -> str` (line 361; internal) — The text blocks of a finished answer; a refusal or a ``max_tokens`` stop is raised with its safe details (thinking counts against ``max_tokens`` on these models: the documented adaptive default).
  - `canary(self) -> dict[str, Any]` (line 375; public) — The model id's check before any bulk work: one tiny admitted request must be answered as a Messages API ``message`` by exactly the pinned model, with usage.

### Module constants

- `ALLOWED_BODY_KEYS` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 53)
- `SENT_BODY_KEYS` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 55)
- `_SAFE_ID` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 56)
- `TRANSIENT` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 102)
- `STOP_REASONS` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 105)
- `BLOCK_TYPES` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 106)
- `MAX_CANDIDATES` ([src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 132)

## Internal implementation anchors

- `_classify(status: int | None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `AnthropicMessagesClient`; statically calls `AnthropicMessagesClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `model_call`, `report_call_usage`; calls `active_request_gate`, `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `UrllibTransport`; calls `UrllibTransport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0BudgetExceeded`, `E0ProviderFailure`; calls `E0BudgetExceeded`, `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/credentials|learnloop.experiments.contextual_embeddings.credentials]] — imports `module`; calls `read_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `RolePin`, `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `re`, `time`, `types`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_every_body_is_within_the_grammar_and_never_carries_tools`
  - `test_the_key_is_in_one_header_only_and_errors_are_allowlisted`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
  - `test_l4_the_messages_client_refuses_to_send_without_a_request_gate`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_label_bs_two_different_objects_with_prose_between_get_one_repair`
  - `test_one_valid_object_inside_prose_or_a_fence_parses_without_a_repair`

## Modification guidance

- Make changes here when the responsibility remains anthropic api within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/anthropic_api.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/anthropic_api.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
