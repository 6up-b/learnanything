---
title: "learnloop.experiments.contextual_embeddings.budget"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/budget.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/budget.py"
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
  - "learnloop.experiments.contextual_embeddings.budget module"
  - "src/learnloop/experiments/contextual_embeddings/budget.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.budget`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.budget` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: The one E0 spend admission: $25 across every paid call (spec §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py) |
| Source lines | 772 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class E0Stop(Exception)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 81) — A step of the paid run cannot continue; nothing more is sent for it.
- `class E0BudgetExceeded(SpendLimitExceeded, E0Stop)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 89) — The next request cannot be admitted under the E0 cap; nothing was sent.
- `class E0DeadlineExceeded(E0BudgetExceeded)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 95) — The run's wall-time bound (``pins.MAX_WALL_S``) has passed; nothing was sent.
- `class E0PriceUnverified(E0BudgetExceeded)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 101) — A metered request priced by an unverified pin; nothing was sent.
- `class E0RunHalted(E0BudgetExceeded)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 107) — A settlement exceeded its reservation: the whole run stops at once.
- `class E0ProviderFailure(E0Stop)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 113) — A provider or contract failure, normalized at the E0 boundary (fix round 4, High 8 and Medium 12).
  - `__init__(self, classification: str, *, status_code: int | None=None, request_id: str | None=None, reason: str | None=None, details: dict[str, Any] | None=None) -> None` (line 121; internal)
- `class E0RequestBlocked(E0Stop)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 141) — A request whose earlier attempt may have been charged without its result recorded: blocked pending reconciliation, never re-sent automatically (fix round 4, Medium 11).
- `class Request` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 158) — What one physical request is admitted as.
- `class E0Ledger` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 175) — The persistent, lock-protected E0 ledger.
  - `__init__(self, directory: Path | str | None=None, *, file: Path | str | None=None, cap_usd: float=pins.E0_CAP_USD, allocation: Mapping[str, float] | None=None, max_requests: int=pins.MAX_PAID_REQUESTS, max_subscription_requests: int=pins.MAX_SUBSCRIPTION_REQUESTS) -> None` (line 181; internal)
  - `start_clock(self, max_wall_s: float=pins.MAX_WALL_S, *, clock: Any=None, wall: Callable[[], float]=time.time) -> float` (line 207; public) — Bound the run to ``max_wall_s`` of wall time from the FIRST start recorded in this ledger (a resumed process keeps the elapsed time: fix round 4, Medium 10): every later admission (each retry included) is refused once it has passed (Codex review F14).
  - `time_left(self) -> float | None` (line 223; public)
  - `_locked(self) -> Iterator[dict[str, Any]]` (line 230; internal)
  - `_read(self) -> dict[str, Any]` (line 241; internal)
  - `_write(self, state: Mapping[str, Any]) -> None` (line 256; internal)
  - `bind_authorization(self, plan_id: str, reason: str | None, carried: Mapping[str, Mapping[str, Any]] | None=None) -> dict[str, Any]` (line 270; public) — Record (once) which plan this ledger's budget belongs to; refuse another plan's id.
  - `_committed(entry: Mapping[str, Any]) -> Decimal` (line 301; internal) — A reconciled entry's actual charge, else its whole reservation.
  - `_totals(self, state: Mapping[str, Any]) -> tuple[Decimal, dict[str, Decimal], int]` (line 308; internal) — Committed money, per category, and the METERED requests.
  - `_carried(state: Mapping[str, Any]) -> tuple[Decimal, dict[str, Decimal]]` (line 323; internal) — What earlier authorizations committed, carried into this one.
  - `_subscription_count(state: Mapping[str, Any]) -> int` (line 331; internal)
  - `reserve(self, request: Request) -> str` (line 334; public) — Admit one physical request; returns its reservation id.
  - `settle(self, reservation: str, *, actual_usd: float | None, usage: Mapping[str, Any] | None=None, status: str='settled', request_id: str | None=None, latency_s: float | None=None) -> None` (line 384; public) — Reconcile a finished request.
  - `admit(self, request: Request) -> Iterator[Charge]` (line 429; public) — Reserve, run the body (the physical request), settle.
  - `halted(self) -> dict[str, Any] | None` (line 444; public)
  - `entries_for(self, request_key: str) -> list[dict[str, Any]]` (line 448; public) — Every entry admitted under one complete request identity, the carried (sealed) ledgers' included.
  - `_sealed_entries(self, name: str) -> dict[str, Any]` (line 461; internal) — A carried ledger's entries (sealed: read once, kept).
  - `remaining(self) -> float` (line 471; public)
  - `report(self) -> dict[str, Any]` (line 477; public)
- `canonical_ledger_dir(copies: Sequence[Path]) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 539) — ``<fixtures-local>/contextual-embeddings/ledger`` for the copies: every copy must lie under the SAME fixtures-local root (independent of any run directory or working directory).
- `authorized_ledger(copies: Sequence[Path], plan_id: str, *, new_authorization: str | None=None) -> E0Ledger` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 556) — The ONE ledger of a frozen plan's authorization.
- `ledger_spend(path: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 584) — One ledger file's OWN committed spend (reconciled charges plus outstanding reservations), per category, read-only.
- `prior_spend(copies: Sequence[Path], *, exclude: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 600) — Every authorization ledger's own committed spend under the copies' canonical ledger directory (read-only; ``exclude``: a plan id), with the total and per category: what a new authorization would carry.
- `seal_ledger(path: Path, *, superseded_by: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 619) — Seal an earlier authorization's ledger under its own lock: mark it ``superseded`` and ``halted`` (every later request on it is refused, by this code and by any older checkout's), and return its own committed spend for the new authorization to carry.
- `known_tokens(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 654) — A reported token count (a nonnegative int, never a bool), else None.
- `explicit_cost(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 662) — A provider's explicit, finite, nonnegative cost, else None.
- `reconciled_usd(usage: Mapping[str, Any], price: Callable[[int, int], float], *, output_bound: int=0) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 671) — What a finished METERED request may be reconciled to; None keeps the whole reservation (``unknown_billing``), counted against the cap.
- `class Charge` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 695) — One admitted request; settle it once with what the provider reported.
  - `__init__(self, ledger: E0Ledger, reservation: str) -> None` (line 698; internal)
  - `settle(self, *, actual_usd: float | None, usage: Mapping[str, Any] | None=None, request_id: str | None=None, latency_s: float | None=None, status: str='settled') -> None` (line 703; public)
- `class LedgerEnvelope(SpendEnvelope)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 713) — The E0 ledger as a ``SpendEnvelope`` for reused production paths.
  - `__init__(self, ledger: E0Ledger, *, category: str, provider: str, route: str, arm: str | None=None) -> None` (line 731; internal)
  - `reserve(self, usd: Decimal) -> object` (line 739; public)
  - `reservation_ref(self, handle: object) -> str | None` (line 743; public)
  - `unreserve(self, handle: object) -> None` (line 746; public)
  - `charge(self, usd: Decimal, handle: object=None) -> None` (line 750; public)
  - `settle(self, handle: object, actual: Decimal | None=None) -> None` (line 754; public) — Reconcile with the production path's own reconciled figure.
  - `remaining(self) -> float` (line 768; public)
  - `report(self) -> dict[str, object]` (line 771; public)

### Module constants

- `LEDGER_NAME` ([src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 74)
- `LOCK_NAME` ([src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 75)
- `LEDGER_DIR` ([src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 77)
- `_PROCESS_LOCK` ([src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 78)
- `_PLAN_ID` ([src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 536)

## Internal implementation anchors

- `_now() -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 149)
- `_d(value: Any) -> Decimal` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `Request`, `explicit_cost`, `known_tokens`, `reconciled_usd`; statically calls `E0PriceUnverified`, `Request`, `explicit_cost`, `known_tokens`, `reconciled_usd`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `E0BudgetExceeded`, `E0ProviderFailure`; statically calls `E0BudgetExceeded`, `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `E0ProviderFailure`, `E0Stop`; statically calls `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `E0ProviderFailure`, `E0RequestBlocked`, `E0Stop`, `Request`, `reconciled_usd`; statically calls `E0BudgetExceeded`, `E0PriceUnverified`, `E0ProviderFailure`, `E0RequestBlocked`, `Request`, `reconciled_usd`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/ledger|learnloop.experiments.contextual_embeddings.e1.ledger]] — imports `E0Ledger`, `ledger_spend`, `seal_ledger`; statically calls `E0Ledger`, `ledger_spend`, `seal_ledger`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `E0Ledger`, `E0ProviderFailure`, `E0Stop`; statically calls `E0Ledger`, `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `E0Stop`, `ledger_spend`; statically calls `ledger_spend`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `E0ProviderFailure`, `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `E0Ledger`, `authorized_ledger`; statically calls `authorized_ledger`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `E0Ledger`, `E0ProviderFailure`, `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `canonical_ledger_dir`, `prior_spend`; statically calls `canonical_ledger_dir`, `prior_spend`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `E0ProviderFailure`, `Request`, `reconciled_usd`; statically calls `E0BudgetExceeded`, `E0PriceUnverified`, `E0ProviderFailure`, `Request`, `reconciled_usd`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendEnvelope`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `decimal`, `fcntl`, `json`, `math`, `os`, `pathlib`, `re`, `threading`, `time`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_adapters.py](../../../../../../../tests/test_e0_adapters.py) — direct import
  - `test_a_refused_admission_sends_nothing`
- [tests/test_e0_bank.py](../../../../../../../tests/test_e0_bank.py) — direct import
  - `test_the_writer_pipeline_with_a_fake_and_its_admission`
- [tests/test_e0_budget.py](../../../../../../../tests/test_e0_budget.py) — direct import
  - `test_a_failed_request_keeps_its_whole_reservation`
  - `test_admission_counts_outstanding_reservations_and_unknown_billing_stays_reserved`
  - `test_concurrent_threads_never_overshoot`
  - `test_subscription_requests_are_admitted_at_zero_and_never_hit_the_request_cap`
  - `test_the_cap_and_allocations_are_the_specs`
  - `test_the_global_cap_binds_across_categories`
  - `test_the_ledger_is_a_spend_envelope_for_reused_production_paths`
  - `test_the_request_gate_admits_every_physical_request`
  - `test_the_wall_time_bound_refuses_every_later_admission_including_retries`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_a_budget_stop_reports_incomplete_with_no_substitution`
  - `test_a_fake_paid_run_completes_every_arm_and_computes_the_stop_rules`
  - `test_a_pinned_reader_budget_is_checked_against_measured_answer_latency`
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
  - `test_resume_pays_only_for_what_is_missing`
  - `test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_new_authorization_carries_the_earlier_spend_into_one_cumulative_cap`
  - `test_a_permitted_block_containing_a_withheld_blocks_text_is_embedded`
  - `test_a_reused_run_with_other_candidate_maps_is_refused_before_anything_is_sealed`
  - `test_an_unredacted_service_copy_is_refused_before_any_request`
  - `test_the_dry_run_budget_uses_the_reused_runs_ledger_and_fails_closed_without_it`
  - `test_the_earlier_ledger_is_sealed_for_any_code_that_reads_it`
  - `test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f11_an_interrupted_service_copy_is_set_aside_and_prepared_again`
  - `test_f12_an_incompletely_covered_service_copy_blocks_the_qwen_system_arms`
  - `test_f12_system_arms_use_find_sources_and_an_unverified_intent_is_no_ranking`
  - `test_f14_a_run_past_its_wall_time_stops_cleanly_and_reports_incomplete`
  - `test_f15_provider_limits_use_a_guaranteed_upper_bound`
  - `test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator`
  - `test_f17_an_answer_stop_keeps_the_planned_denominator`
  - `test_f18_query_vectors_are_cached_and_not_repaid`
  - `test_f1_service_copy_preparation_never_sends_protected_text`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
  - `test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request`
  - `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs`
  - `test_f9_finalist_latency_includes_a_fresh_online_query_and_the_search`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f19_a_qwen_arm_charges_embeddings_and_verification_once_each`
  - `test_f19_successful_production_verification_charges_once_per_physical_request`
  - `test_f19_the_ledger_envelope_ignores_a_subscription_sentinel`
  - `test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding`
  - `test_f20_a_failed_delegated_comparison_is_missing_not_ranked`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_a_hosted_embedding_without_positive_usage_keeps_its_reservation`
  - `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`
  - `test_f21_the_ledger_envelope_keeps_a_zero_dollar_reconciliation_reserved`
  - `test_f21_the_role_gate_never_settles_a_metered_request_from_output_tokens_alone`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_a_settlement_above_its_reservation_halts_the_whole_run`
  - `test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once`
  - `test_h2_an_unverified_price_refuses_every_metered_request_before_sending`
  - `test_h3_one_canonical_ledger_per_plan_whatever_the_run_directory`
  - `test_h4_a_qwen_client_that_is_not_its_pin_is_refused_before_its_first_request`
  - `test_h4_the_qwen_identity_is_in_cache_keys_and_receipts_and_the_service_gate`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m10_a_resumed_process_keeps_the_run_clock`
  - `test_m10_subscription_requests_are_bounded_by_a_persisted_allowance`
  - `test_m11_a_charged_but_unrecorded_request_is_blocked_never_resent`
  - `test_m11_a_settled_response_is_recovered_from_the_receipts`
  - `test_m11_concurrent_workers_send_one_request_and_a_known_failure_may_retry`
  - `test_m12_a_provider_failure_records_incomplete_work_instead_of_aborting`
  - `test_m13_an_arm_that_fails_every_logged_question_stops_verdicts`
  - `test_m9_the_qwen_route_is_canaried_before_its_service_backfill`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
  - `test_voyage_is_admitted_at_the_full_price_never_the_free_tier`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_a_role_call_goes_through_the_messages_api_transport`
  - `test_each_model_id_is_canaried_before_bulk_work_and_a_wrong_model_stops_the_run`
  - `test_the_key_is_in_one_header_only_and_errors_are_allowlisted`
  - `test_the_plan_has_zero_codex_requests_and_the_paid_ledger_refuses_any`
  - `test_the_service_copies_route_their_source_routes_to_openrouter_haiku`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
  - `test_l4_the_messages_client_refuses_to_send_without_a_request_gate`
- [tests/test_e0_review_round7.py](../../../../../../../tests/test_e0_review_round7.py) — direct import
  - `test_a_2xx_that_does_not_parse_records_a_safe_reason`
  - `test_a_canary_failure_reaches_the_contracts_result_with_its_reason`
  - `test_a_documented_contextual_response_decodes_by_index`
  - `test_a_rerun_reopens_the_ledger_and_keeps_an_interrupted_reservation`
  - `test_the_three_perplexity_canaries_pass_against_the_documented_contract`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_failed_repair_raises_with_both_safe_reasons_and_no_model_text`
  - `test_a_failed_role_call_leaves_a_safe_failure_record`
  - `test_a_max_tokens_or_refusal_stop_is_never_repaired_and_carries_its_details`
  - `test_a_non_item_failure_still_stops_the_labels`
  - `test_a_refused_backfill_batch_is_reported_safely_and_sent_once_more`
  - `test_a_request_known_truncated_at_the_same_bound_is_not_sent_again`
  - `test_label_bs_two_different_objects_with_prose_between_get_one_repair`
  - `test_one_questions_unusable_labels_skip_that_question_only`
  - `test_the_first_paid_runs_failure_marker_is_read_and_truncation_inferred_from_the_ledger`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_e1_ledger_is_cumulative_across_e1_plans_and_never_touches_e0`
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`

## Modification guidance

- Make changes here when the responsibility remains budget within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/budget.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/budget.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
