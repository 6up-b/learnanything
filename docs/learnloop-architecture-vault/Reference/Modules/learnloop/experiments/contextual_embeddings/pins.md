---
title: "learnloop.experiments.contextual_embeddings.pins"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/pins.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/pins.py"
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
  - "learnloop.experiments.contextual_embeddings.pins module"
  - "src/learnloop/experiments/contextual_embeddings/pins.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.pins`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.pins` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's frozen constants: models, routes, provider contracts, prices, caps, seeds.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py) |
| Source lines | 575 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PriceVerification` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 103) — Where and when a metered price was checked against the provider's published price page.
  - `verified(self) -> bool` (line 116; public)
  - `as_dict(self) -> dict[str, str]` (line 122; public)
- `token_estimate(text: str | None) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 192) — A token ESTIMATE (UTF-8 bytes / 3, rounded up): typical for English and LaTeX under common subword tokenizers, but not a bound (dense notation, punctuation or poorly compressible text tokenize above it; Codex review F15).
- `token_upper_bound(text: str | None) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 203) — A guaranteed token UPPER BOUND: UTF-8 bytes plus the special-token allowance.
- `class EmbeddingPin` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 216) — One embedding model's frozen contract (unverified until its canary).
  - `as_dict(self) -> dict[str, Any]` (line 245; public)
- `class RolePin` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 333) — One paid LLM role: its exact route, model, transport and price bound.
  - `prices_for(self, input_tokens: float) -> tuple[float, float]` (line 362; public) — ``(input, output)`` dollars per million tokens for a request of ``input_tokens`` (the long tier past its threshold).
  - `as_dict(self) -> dict[str, Any]` (line 371; public)
- `class ArmPin` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 474) — A named arm: what it encodes, with which model, how it searches.
- `pins_fingerprint() -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 521) — One hash of every pin above (part of the run id).
- `price_problem(pin: EmbeddingPin | RolePin) -> str | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 544) — Why a METERED pin's price cannot admit a request (None: it can).
- `unverified_prices() -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 561) — Every metered pin whose price is unverified (the dry run reports them).
- `verified_role_for_model(model: str | None) -> RolePin | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 568) — A metered role pin with a verified price for ``model`` (a production route on a service copy is priced only through one).

### Module constants

- `HARNESS_VERSION` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 34)
- `DELIVERY_FIXES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 38)
- `D1_EVIDENCE_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 50)
- `GENERATOR_CONTEXT_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 54)
- `GENERATOR_RESERVES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 56)
- `E0_CAP_USD` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 62)
- `ALLOCATION_USD` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 78)
- `TRANSIENT_RETRIES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 85)
- `REQUEST_TIMEOUT_S` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 86)
- `MAX_WALL_S` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 88)
- `MAX_PAID_REQUESTS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 90)
- `MAX_SUBSCRIPTION_REQUESTS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 95)
- `PAID_RUN_SUBSCRIPTION_ALLOWANCE` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 99)
- `UNVERIFIED` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 129)
- `SEED` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 132)
- `BOOTSTRAP_RESAMPLES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 133)
- `AUDIT_SAMPLE_SHARE` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 135)
- `WINDOW_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 139)
- `CHUNK_MARKER_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 141)
- `UNIT_MAX_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 143)
- `CAPTION_TARGET_TOKENS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 145)
- `TOP_K` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 146)
- `POOL_DEPTH` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 148)
- `LABEL_RUBRIC_SHA256` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 155)
- `KAPPA_MIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 156)
- `ARM_COMPLETION_MIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 158)
- `MIN_INDEPENDENT_FAMILIES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 160)
- `S2_NONINFERIORITY_MARGIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 161)
- `S3_CONTEXT_GAIN_MIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 162)
- `S3_QWEN_WITHIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 163)
- `S4_GAIN_MIN` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 164)
- `LATENCY_REGRESSION_TOLERANCE` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 168)
- `SMOKE_CASES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 171)
- `DEV_QUESTIONS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 172)
- `DEV_QUESTION_TARGET` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 173)
- `DEV_STRATA` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 175)
- `TOKEN_BOUND_SPECIAL` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 189)
- `PRICES_CHECKED_ON` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 250)
- `VOYAGE_FREE_TIER_NOTE` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 252)
- `EMBEDDING_PINS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 261)
- `ANTHROPIC_MESSAGES_URL` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 378)
- `ANTHROPIC_VERSION` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 380)
- `ANTHROPIC_KEY_ENV` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 381)
- `ANTHROPIC_TIMEOUT_S` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 383)
- `ANTHROPIC_MODELS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 388)
- `ANTHROPIC_PROFILES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 390)
- `ANTHROPIC_PRICE` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 395)
- `_HAIKU` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 396)
- `_SONNET` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 399)
- `_OPUS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 401)
- `_FAMILY_PRICES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 403)
- `ROLE_PINS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 418)
- `EXPERIMENT_PROFILES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 459)
- `SYSTEM_ARM_ROUTES` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 466)
- `DEFAULT_KEY_ENVS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 469)
- `DELIVERY_ARMS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 486)
- `RETRIEVAL_ARMS` ([src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 493)

## Internal implementation anchors

- `_verified(source_url: str, *, note: str='') -> PriceVerification` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 256)
- `_anthropic(role: str, family: str, category: str, expected_output: int, max_output: int, prompt_version: str) -> RolePin` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py), line 406)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `EmbeddingPin`, `module`, `token_upper_bound`; statically calls `price_problem`, `token_upper_bound`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `RolePin`, `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `RolePin`, `module`, `token_upper_bound`; statically calls `price_problem`, `token_upper_bound`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `module`, `token_estimate`, `token_upper_bound`; statically calls `token_estimate`, `token_upper_bound`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `module`; statically calls `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `EmbeddingPin`; statically calls `EmbeddingPin`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `module`; statically calls `pins_fingerprint`, `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `module`; statically calls `pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `module`; statically calls `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `module`; statically calls `pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `module`, `token_estimate`; statically calls `pins_fingerprint`, `price_problem`, `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `module`; statically calls `pins_fingerprint`, `price_problem`, `unverified_prices`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/stop_rules|learnloop.experiments.contextual_embeddings.stop_rules]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `module`; statically calls `price_problem`, `token_upper_bound`, `verified_role_for_model`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] and 20 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/e0_fakes.py](../../../../../../../tests/e0_fakes.py) — direct import
- [tests/test_e0_adapters.py](../../../../../../../tests/test_e0_adapters.py) — direct import
  - `test_a_refused_admission_sends_nothing`
  - `test_qwen_adapter_uses_production_prefixes_and_admits_each_batch`
  - `test_transient_failures_retry_twice_each_attempt_admitted_auth_never`
- [tests/test_e0_bank.py](../../../../../../../tests/test_e0_bank.py) — direct import
  - `test_the_smoke_bank_has_16_deterministic_cases_from_permitted_text`
- [tests/test_e0_budget.py](../../../../../../../tests/test_e0_budget.py) — direct import
  - `test_the_cap_and_allocations_are_the_specs`
  - `test_the_global_cap_binds_across_categories`
  - `test_the_request_gate_admits_every_physical_request`
- [tests/test_e0_corpus.py](../../../../../../../tests/test_e0_corpus.py) — direct import
  - `test_split_offsets_cover_text_exactly_and_respect_the_bound`
  - `test_transcript_captions_merge_toward_the_target_within_one_sequence`
  - `test_units_are_deterministic_and_keep_original_offsets`
  - `test_windows_partition_units_within_the_token_bound`
- [tests/test_e0_delivery.py](../../../../../../../tests/test_e0_delivery.py) — direct import
  - `test_a_source_that_does_not_fit_runs_the_named_fallback_never_a_truncation`
  - `test_d0_and_d1_reproduce_the_production_reader_delivery`
- [tests/test_e0_dry_run.py](../../../../../../../tests/test_e0_dry_run.py) — direct import
  - `test_split_strata_is_deterministic_and_complete`
  - `test_the_plan_has_every_arm_question_count_estimate_and_key_state`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_a_fake_paid_run_completes_every_arm_and_computes_the_stop_rules`
  - `test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_new_authorization_carries_the_earlier_spend_into_one_cumulative_cap`
  - `test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results`
  - `test_an_edited_rubric_refuses_to_load`
  - `test_both_label_passes_are_sonnet_and_the_rubric_is_frozen_by_hash`
  - `test_the_committed_relabel_plan_is_current_and_fits_what_is_left`
  - `test_the_reuse_estimate_reprices_every_label_request_at_todays_pins`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f15_provider_limits_use_a_guaranteed_upper_bound`
  - `test_f17_an_answer_stop_keeps_the_planned_denominator`
  - `test_f18_a_torn_vector_append_is_recovered_and_raw_output_is_kept`
  - `test_f18_query_vectors_are_cached_and_not_repaid`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
  - `test_f3_a_changed_identity_never_reuses_a_checkpoint`
  - `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_a_hosted_embedding_without_positive_usage_keeps_its_reservation`
  - `test_f21_a_metered_system_llm_request_without_input_usage_or_cost_keeps_its_reservation`
  - `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`
  - `test_f21_reported_input_tokens_or_an_explicit_cost_still_reconcile`
  - `test_f21_the_role_gate_never_settles_a_metered_request_from_output_tokens_alone`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_an_unverified_price_refuses_every_metered_request_before_sending`
  - `test_h2_the_dry_run_reports_unverified_prices_and_authorization_refuses_them`
  - `test_h4_a_qwen_client_that_is_not_its_pin_is_refused_before_its_first_request`
  - `test_h4_the_qwen_identity_is_in_cache_keys_and_receipts_and_the_service_gate`
  - `test_m10_the_dry_run_reports_the_planned_codex_requests`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_every_metered_pin_carries_exactly_the_orchestrator_verified_price`
  - `test_the_label_passes_never_reach_a_codex_turn`
  - `test_voyage_is_admitted_at_the_full_price_never_the_free_tier`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_a_prompt_that_could_pass_100k_tokens_is_admitted_at_haikus_long_rate`
  - `test_each_post_is_admitted_first_at_its_hard_maximum_and_settled_from_usage`
  - `test_preflight_only_reports_names_and_checks_with_zero_network_and_no_value`
  - `test_the_key_is_in_one_header_only_and_errors_are_allowlisted`
  - `test_the_paid_preflight_passes_with_every_pin_verified_zero_codex_and_the_lockdown`
  - `test_the_paid_run_refuses_any_codex_role`
  - `test_the_service_copies_route_their_source_routes_to_openrouter_haiku`
  - `test_two_independent_labellers_a_different_adjudicator_and_no_codex_role`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l1_a_redirect_is_a_contract_failure_that_is_never_retried`
  - `test_l4_the_messages_client_refuses_to_send_without_a_request_gate`
  - `test_m2_the_allocation_covers_each_expected_spend_with_headroom_above_an_opus_reservation`
- [tests/test_e0_review_round7.py](../../../../../../../tests/test_e0_review_round7.py) — direct import
  - `test_this_round_keeps_the_frozen_plans_pins_fingerprint`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_label_as_extra_misspelled_key_is_named_safely_and_repaired_once`
  - `test_this_round_keeps_the_plan_id`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`
  - `test_the_replay_restores_e0s_strata_order_from_the_sorted_json_plan`
- [tests/test_e1_supplement.py](../../../../../../../tests/test_e1_supplement.py) — direct import
  - `test_the_e1_roles_are_e0s_metered_messages_api_pins_with_e1_prompt_versions`

## Modification guidance

- Make changes here when the responsibility remains pins within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/pins.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/pins.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
