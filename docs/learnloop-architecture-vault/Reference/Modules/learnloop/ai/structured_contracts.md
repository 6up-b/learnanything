---
title: "learnloop.ai.structured_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/structured_contracts.py"
source_paths:
  - "src/learnloop/ai/structured_contracts.py"
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
  - "learnloop.ai.structured_contracts module"
  - "src/learnloop/ai/structured_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.structured_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.structured_contracts` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: One shared step for structured answers that parse but break their contract.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py) |
| Source lines | 529 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class Predicate(Generic[T])` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 59) — One named obligation of a parsed answer.
  - `__post_init__(self) -> None` (line 73; internal)
- `contract_of(*predicates: Predicate[Any]) -> tuple[Predicate[Any], ...]` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 86) — ``predicates`` as a contract, refused when one is not a :class:`Predicate` or two share a name (a correction names its predicate; two would be ambiguous).
- `first_failure(contract: Iterable[Predicate[T]], answer: T) -> Predicate[T] | None` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 100) — The first predicate ``answer`` fails, in declared order, or None.
- `correction_prompt(first_prompt: str, predicate: Predicate[Any]) -> str` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 113) — The correction: the original prompt, then the failed predicate and its requirement.
- `class ContractRejected(Exception)` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 121) — A parsed answer failed a contract predicate.
  - `__init__(self, predicate: Predicate[Any]) -> None` (line 128; internal)
- `class RecoveryState` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 134) — What one logical call has spent, in the form a durable job stores and restores.
  - `__post_init__(self) -> None` (line 146; internal)
  - `as_dict(self) -> dict[str, Any]` (line 150; public)
  - `from_dict(cls, data: Mapping[str, Any] | None) -> RecoveryState` (line 154; public)
- `class RecoveryAllowance` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 161) — The caller's own room for the one recovery; it holds no money of its own.
- `class ContractFailure` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 187) — Why a checked call ended without an accepted answer, for the caller's ``failure``.
- `class Attempt` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 205) — One request the caller's ``send`` makes: the first (ordinal 0) or a correction.
- `class CheckedAnswer(Generic[T])` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 217)
- `claim_schema_repair() -> bool` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 278) — Whether a provider may send its schema repair now.
- `recovery_remaining_seconds() -> float | None` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 296) — What remains of the checked call's one deadline, or None (no checked call, or no deadline).
- `correction_in_flight() -> bool` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 307) — Whether the request being made is a checked call's correction.
- `checked_structured_call(*, first_prompt: str, contract: Iterable[Predicate[T]], send: Callable[[Attempt, Callable[[T], T]], T], recovery: RecoveryAllowance, checkpoint: ModelCheckpoint[T] | None, failure: Callable[[ContractFailure], BaseException], request_key: str | None=None, usage: Callable[[T], dict[str, Any]] | None=None) -> T` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 328) — The accepted answer of one structured call with a contract (:func:`checked_structured_answer`).
- `checked_structured_answer(*, first_prompt: str, contract: Iterable[Predicate[T]], send: Callable[[Attempt, Callable[[T], T]], T], recovery: RecoveryAllowance, checkpoint: ModelCheckpoint[T] | None, failure: Callable[[ContractFailure], BaseException], request_key: str | None=None, usage: Callable[[T], dict[str, Any]] | None=None) -> CheckedAnswer[T]` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 347) — Check, and at most once correct, one structured call's answer.
- `recovery_note(budget_json: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 454) — A root receipt's :data:`RECOVERY_NOTE` (its ``budget_json``), or None.
- `recover_from_receipts(receipts: Iterable[Mapping[str, Any]], *, first_prompt: str, request_key: str | None, contract: Iterable[Predicate[T]], read: Callable[[str], T]) -> tuple[T, Mapping[str, Any]] | None` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 464) — The newest receipt answer a checked call may reuse, and its receipt, or None.

### Module constants

- `T` ([src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py), line 44)
- `MAX_STRUCTURED_RECOVERIES` ([src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py), line 48)
- `RECOVERY_NOTE` ([src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py), line 51)
- `_PREDICATE_NAME` ([src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py), line 53)
- `_REFUSALS` ([src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py), line 55)

### Explicit exports

`__all__` declares:

- `Attempt`
- `CheckedAnswer`
- `Contract`
- `ContractFailure`
- `ContractRejected`
- `MAX_STRUCTURED_RECOVERIES`
- `Predicate`
- `RECOVERY_NOTE`
- `RecoveryAllowance`
- `RecoveryState`
- `checked_structured_answer`
- `checked_structured_call`
- `claim_schema_repair`
- `contract_of`
- `correction_in_flight`
- `correction_prompt`
- `first_failure`
- `recover_from_receipts`
- `recovery_note`
- `recovery_remaining_seconds`

## Internal implementation anchors

- `class _Ledger` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 227) — The one recovery of the checked call in flight, as the hooks below see it.
- `_checker(contract: tuple[Predicate[T], ...]) -> Callable[[T], T]` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 314)
- `_named(contract: tuple[Predicate[T], ...], name: Any) -> Predicate[T] | None` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 324)
- `_run(ledger: _Ledger, send: Callable[[Attempt, Callable[[T], T]], T], contract: tuple[Predicate[T], ...], attempt: Attempt, key: str | None, failure: Callable[[ContractFailure], BaseException], sends: int) -> tuple[Any, Predicate[T] | None, BaseException | None]` ([source](../../../../../../src/learnloop/ai/structured_contracts.py), line 423) — One send under the ledger: (answer, None, None) accepted, or (None, failed predicate, cause).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `claim_schema_repair`, `recovery_remaining_seconds`; statically calls `claim_schema_repair`, `recovery_remaining_seconds`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `claim_schema_repair`; statically calls `claim_schema_repair`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `correction_in_flight`; statically calls `correction_in_flight`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `Predicate`; statically calls `Predicate`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `Predicate`, `contract_of`, `correction_prompt`; statically calls `Predicate`, `contract_of`, `correction_prompt`
- [[Reference/Modules/learnloop/followup_run/contract_job|learnloop.followup_run.contract_job]] — imports `ContractFailure`, `RecoveryAllowance`, `RecoveryState`, `checked_structured_call`, `recover_from_receipts`, `recovery_note`; statically calls `RecoveryAllowance`, `RecoveryState`, `checked_structured_call`, `recover_from_receipts`, `recovery_note`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `annotate_calls`, `content_key`; calls `annotate_calls`, `content_key`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_contracts_helpers.py](../../../../../../tests/structured_contracts_helpers.py) — direct import
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_a_background_request_gets_no_fresh_ceiling_past_the_checked_calls_deadline`
  - `test_a_checked_call_sends_the_first_request_unchanged_and_one_correction`
  - `test_a_checked_call_with_no_admitted_recovery_sends_no_plan_repair`
  - `test_contract_failing_then_a_malformed_correction_gets_one_repair`
  - `test_malformed_then_repaired_then_contract_failing_gets_one_correction`
- [tests/test_chatgpt_plan_runaway.py](../../../../../../tests/test_chatgpt_plan_runaway.py) — direct import
  - `test_a_cut_stream_never_reaches_the_semantic_predicate`
- [tests/test_followup_contract_baseline.py](../../../../../../tests/test_followup_contract_baseline.py) — direct import
  - `test_every_schema_or_contract_recovery_needs_admission_time_and_no_cancellation`
  - `test_separate_credits_preserve_the_unadopted_success`
  - `test_two_attempts_each_allow_only_one_schema_repair`
- [tests/test_followup_contract_recovery.py](../../../../../../tests/test_followup_contract_recovery.py) — direct import
  - `test_named_predicates_preserve_the_interleaved_pipeline`
- [tests/test_model_work_checkpoints.py](../../../../../../tests/test_model_work_checkpoints.py) — direct import
- [tests/test_practice_index_paid.py](../../../../../../tests/test_practice_index_paid.py) — direct import
  - `test_a_metered_contract_correction_is_admitted_and_charged_as_a_retry`
  - `test_a_rejected_answer_stays_on_a_failed_receipt_and_only_the_correction_is_recoverable`
- [tests/test_structured_contracts.py](../../../../../../tests/test_structured_contracts.py) — direct import
  - `test_a_contract_holds_distinctly_named_predicates_and_may_be_empty`
  - `test_a_crash_after_the_rejection_resumes_with_the_correction_not_the_first_request`
  - `test_a_crash_after_the_reservation_never_sends_the_recovery_twice`
  - `test_a_crash_before_the_checkpoint_save_recovers_the_correction_from_its_receipt_under_the_original_key`
  - `test_a_deferred_correction_is_recorded_and_sent_on_the_next_run`
  - `test_a_predicate_must_answer_with_a_bool`
  - `test_a_predicate_needs_a_snake_case_name_and_one_fixed_requirement_line`
  - `test_a_rejected_answer_finishes_its_operation_receipt_as_failed_and_the_correction_names_its_original`
  - `test_a_restored_owed_correction_is_sent_instead_of_the_first_request`
  - `test_a_resumed_spent_recovery_stays_spent`
  - `test_a_valid_first_answer_is_one_unchanged_request_and_asks_for_no_recovery`
  - `test_an_exhausted_budget_deadline_or_cancellation_sends_nothing_more`
  - `test_an_owed_correction_the_contract_no_longer_declares_sends_nothing`
  - `test_bad_then_bad_sends_no_third_request`
  - `test_bad_then_good_spends_the_one_recovery_on_a_correction`
  - `test_checked_structured_call_returns_the_accepted_answer`
  - `test_no_ambient_authorization_sends_no_recovery`
  - `test_other_failures_of_the_send_are_the_callers_own`
  - `test_predicates_run_in_declared_order_and_the_first_failure_wins`
  - `test_receipt_recovery_reruns_the_contract_and_checks_the_correction_linkage`
  - `test_the_chat_providers_repair_is_separate_from_the_contract_recovery`
  - `test_the_correction_is_the_original_prompt_and_the_exact_suffix`
  - `test_the_correction_reproduces_the_followup_authors_reask_byte_for_byte`
  - `test_the_correction_runs_on_what_remains_of_the_one_deadline`
  - `test_without_a_contract_an_operation_and_its_receipt_are_as_before`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/structured_contracts.py](../../../../../../src/learnloop/ai/structured_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
