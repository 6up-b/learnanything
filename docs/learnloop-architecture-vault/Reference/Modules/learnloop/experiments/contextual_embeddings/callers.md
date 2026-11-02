---
title: "learnloop.experiments.contextual_embeddings.callers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/callers.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/callers.py"
source_commit: "7e6020e02ac2ef32285a38ee94800039dd54c9d3"
source_commit_timestamp: "2026-10-23T17:26:11-04:00"
source_worktree_state: "clean"
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
  - "learnloop.experiments.contextual_embeddings.callers module"
  - "src/learnloop/experiments/contextual_embeddings/callers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.callers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.callers` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: Paid LLM roles for E0 (writer, context, labels, adjudicator, tutor, judges).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/callers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py) |
| Source lines | 628 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7e6020e02ac2ef32285a38ee94800039dd54c9d3` |
| Commit timestamp | `2026-10-23T17:26:11-04:00` |

## Public API

- `class PinMismatch(E0Stop, RuntimeError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 84) — The client a role resolved to is not its frozen pin; nothing was sent (an E0 stop: its message is built from pins only, never provider text).
- `class RoleCaller(Protocol)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 91)
  - `call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None=None) -> Any` (line 92; public)
- `class CallRecord` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 96) — What one role call did: measured latency (the original one on a resume), whether it came from a checkpoint, its receipts and identity.
- `role_cost(pin: RolePin, input_tokens: int, output_tokens: int) -> float` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 109) — The pin's upper-bound price for a request (subscription: $0 billed).
- `estimate_input_tokens(prompt: Any) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 119) — The input UPPER bound admission reserves (bytes, not the bytes/3 estimate).
- `resolved_identity(client: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 126) — What a client will actually call: transport, model, endpoint, effort, billing.
- `check_pin(pin: RolePin, client: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 139) — The resolved identity, or ``PinMismatch`` before any request.
- `class E0RequestGate` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 170) — A ``learnloop.ai.execution`` request gate admitting through the E0 ledger.
  - `__init__(self, ledger: E0Ledger, pin: RolePin, *, arm: str | None=None, request_key: str | None=None) -> None` (line 176; internal)
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> _Admission` (line 186; public)
  - `settle(self, admission: _Admission | None, usage: Mapping[str, Any]) -> None` (line 210; public)
- `checkpoint_key(pin: RolePin, prompt: str, result_model: type[BaseModel], *, identity: Mapping[str, Any] | None=None, output_bound: int | None=None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 226)
- `class Checkpoints` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 234) — Validated results by content key (private run directory), each with the original measurement (latency, receipts) of the call that paid for it.
  - `__init__(self, directory: Path | None) -> None` (line 238; internal)
  - `get(self, key: str, *, refresh: bool=False) -> dict[str, Any] | None` (line 243; public)
  - `put(self, key: str, value: Mapping[str, Any]) -> None` (line 256; public) — Durable: the file and its directory are fsynced before returning (fix round 4, Medium 11), so a recorded result survives a crash.
  - `mark_failed(self, key: str, reservations: Sequence[str], *, failure: Mapping[str, Any] | None=None) -> None` (line 275; public) — Record, durably, that these admissions of ``key`` ended in a failure (nothing to recover: a later run may send the request again), with the failure's SAFE record (paid-run round 2): its classification, reason, status and details (stop_reason, token counts, max_tokens), never pro…
  - `_failed_record(self, key: str) -> dict[str, Any]` (line 288; internal)
  - `failed_reservations(self, key: str) -> list[str]` (line 298; public)
  - `failure(self, key: str) -> dict[str, Any] | None` (line 301; public) — The safe record of this key's last failure (None: none recorded).
  - `_durable_write(self, path: Path, text: str) -> None` (line 307; internal)
  - `claim(self, key: str) -> Iterator[None]` (line 322; public) — An exclusive cross-process claim on one request identity, held while it executes (an ``flock`` that the OS releases if the process dies).
  - `_local_lock(self, key: str) -> Iterator[None]` (line 343; internal)
- `class LiveRoleCaller(_Recording)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 381) — The real caller (paid run only; tests use fake clients).
  - `__init__(self, vault_root: Path, config: Any, ledger: E0Ledger, *, checkpoints: Checkpoints, role_pins: Mapping[str, RolePin] | None=None, client_factory: Callable[[str], Any] | None=None, records: Any=None, key_envs: Mapping[str, str | None] | None=None, environ: Mapping[str, str] | None=None, anthropic_transport: Any=None) -> None` (line 384; internal)
  - `_client(self, pin: RolePin) -> tuple[Any, dict[str, Any]]` (line 404; internal)
  - `output_bound(self, pin: RolePin) -> int` (line 423; public) — The pin's hard ``max_tokens`` (Anthropic roles), else the normal output-budget policy for the role's profile (never lowered).
  - `call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None=None) -> Any` (line 434; public)
  - `_from_checkpoint(self, role: str, pin: RolePin, key: str, identity: Mapping[str, Any], saved: Mapping[str, Any], result_model: type[BaseModel]) -> Any` (line 522; internal)
  - `_recover(self, prompt: Any, result_model: type[BaseModel]) -> Any | None` (line 529; internal) — A settled response of this exact prompt from the experiment's own receipts (a completed receipt whose input is the prompt and whose output validates), or None.
- `failure_record(role: str, exc: BaseException) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 548) — The SAFE record of a failed role call (paid-run round 2): the role, the allowlisted classification, the harness-built reason, the HTTP status and the response's safe details; an exception that is not an E0 provider failure is named by its type only.
- `with_experiment_profiles(config: Any) -> Any` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 561) — A copy of ``config`` with E0's metered profiles added (in memory only).
- `class FakeRoleCaller(_Recording)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 580) — Test double: answers from ``respond(role, prompt, result_model)`` and still admits every call through the ledger at the pin's estimate.
  - `__init__(self, respond: Callable[[str, str, type[BaseModel]], Any], ledger: E0Ledger | None=None, *, role_pins: Mapping[str, RolePin] | None=None, records: Any=None, latency: Callable[[str, str], float] | None=None) -> None` (line 585; internal)
  - `call(self, role: str, *, prompt: str, result_model: type[BaseModel], arm: str | None=None) -> Any` (line 596; public)
- `canary_models(caller: LiveRoleCaller) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 610) — Each pinned Anthropic model id checked before any bulk work (re-plan 2026-10-22): one tiny admitted request per distinct model, answered as a Messages API ``message`` by exactly that model.

### Module constants

- `SCHEMA_ALLOWANCE_TOKENS` ([src/learnloop/experiments/contextual_embeddings/callers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 78)
- `TRANSPORT_TYPES` ([src/learnloop/experiments/contextual_embeddings/callers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 80)

## Internal implementation anchors

- `class _Admission` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 162)
- `_collect_receipts(found: list[str]) -> Iterator[None]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 351)
- `class _Recording` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py), line 362) — Judgment recording shared by the live and fake callers.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `Checkpoints`, `LiveRoleCaller`, `checkpoint_key`; statically calls `Checkpoints`, `checkpoint_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `Checkpoints`, `LiveRoleCaller`, `canary_models`; statically calls `Checkpoints`, `LiveRoleCaller`, `canary_models`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `Checkpoints`, `LiveRoleCaller`, `canary_models`; statically calls `Checkpoints`, `LiveRoleCaller`, `canary_models`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `Checkpoints`; statically calls `Checkpoints`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `SCHEMA_ALLOWANCE_TOKENS`, `role_cost`; statically calls `role_cost`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `estimate_input_tokens`, `role_cost`; statically calls `estimate_input_tokens`, `role_cost`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `gate_model_requests`, `generation_limit`, `requested_reasoning_effort`, `tee_model_calls`, `truncation_retry_allowed`; calls `gate_model_requests`, `generation_limit`, `requested_reasoning_effort`, `tee_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `client_for_provider`; calls `client_for_provider`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `AnthropicMessagesClient`; calls `AnthropicMessagesClient`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `provider_failure`, `quiet_provider_logs`; calls `provider_failure`, `quiet_provider_logs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `E0ProviderFailure`, `E0RequestBlocked`, `E0Stop`, `Request`, `reconciled_usd`; calls `E0BudgetExceeded`, `E0PriceUnverified`, `E0ProviderFailure`, `E0RequestBlocked`, `Request`, `reconciled_usd`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `RolePin`, `module`, `token_upper_bound`; calls `price_problem`, `token_upper_bound`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_bank.py](../../../../../../../tests/test_e0_bank.py) — direct import
  - `test_the_writer_pipeline_with_a_fake_and_its_admission`
  - `test_two_blinded_passes_audit_plan_and_adjudication`
- [tests/test_e0_budget.py](../../../../../../../tests/test_e0_budget.py) — direct import
  - `test_the_request_gate_admits_every_physical_request`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_a_pinned_reader_budget_is_checked_against_measured_answer_latency`
  - `test_resume_pays_only_for_what_is_missing`
  - `test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f10_verdicts_enter_judgment_ledger_once`
  - `test_f12_an_incompletely_covered_service_copy_blocks_the_qwen_system_arms`
  - `test_f13_a_conjunction_split_across_batches_is_found_by_the_joint_review`
  - `test_f14_a_run_past_its_wall_time_stops_cleanly_and_reports_incomplete`
  - `test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator`
  - `test_f17_an_answer_stop_keeps_the_planned_denominator`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
  - `test_f3_a_changed_identity_never_reuses_a_checkpoint`
  - `test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request`
  - `test_f7_a_malformed_adjudication_leaves_sufficiency_unresolved`
  - `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs`
  - `test_f9_finalist_latency_includes_a_fresh_online_query_and_the_search`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f7_a_set_member_is_checked_against_the_merged_final_labels`
  - `test_f7_an_inherited_supporting_label_still_completes_a_set`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_reported_input_tokens_or_an_explicit_cost_still_reconcile`
  - `test_f21_the_role_gate_never_settles_a_metered_request_from_output_tokens_alone`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once`
  - `test_h2_an_unverified_price_refuses_every_metered_request_before_sending`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m12_a_provider_failure_records_incomplete_work_instead_of_aborting`
  - `test_m13_an_arm_that_fails_every_logged_question_stops_verdicts`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_a_prompt_that_could_pass_100k_tokens_is_admitted_at_haikus_long_rate`
  - `test_a_role_call_goes_through_the_messages_api_transport`
  - `test_each_model_id_is_canaried_before_bulk_work_and_a_wrong_model_stops_the_run`
  - `test_each_post_is_admitted_first_at_its_hard_maximum_and_settled_from_usage`
  - `test_the_key_is_in_one_header_only_and_errors_are_allowlisted`
  - `test_the_service_copies_route_their_source_routes_to_openrouter_haiku`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_the_first_paid_runs_failure_marker_is_read_and_truncation_inferred_from_the_ledger`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`
- [tests/test_e1_supplement.py](../../../../../../../tests/test_e1_supplement.py) — direct import
  - `test_a_set_without_a_new_candidate_or_with_a_background_member_is_malformed`
  - `test_an_unresolved_verdict_leaves_the_new_candidates_unknown`
  - `test_passes_are_blinded_new_sets_are_audited_and_merged`

## Modification guidance

- Make changes here when the responsibility remains callers within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/callers.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/callers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
