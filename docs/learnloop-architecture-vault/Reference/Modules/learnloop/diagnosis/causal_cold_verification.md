---
title: "learnloop.diagnosis.causal_cold_verification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_cold_verification.py"
source_paths:
  - "src/learnloop/diagnosis/causal_cold_verification.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_cold_verification module"
  - "src/learnloop/diagnosis/causal_cold_verification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_cold_verification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_cold_verification` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Carry repair context into delayed cold retries and record their outcomes.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_cold_verification.py](../../../../../../src/learnloop/diagnosis/causal_cold_verification.py) |
| Source lines | 434 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `cold_verification_context(vault: LoadedVault | None, repository: Repository, *, episode: Mapping[str, Any], source_attempt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_cold_verification.py), line 29) — Everything ``record_delayed_cold_verification`` will need, resolved NOW.
- `record_cold_verification_from_task(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], cold_attempt_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_cold_verification.py), line 139) — Fire the delayed cold verification when a scheduled retry completes.
- `sweep_expired_cold_retries(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_cold_verification.py), line 318) — Turn silent cold-retry expiries into typed §4.3 dispositions.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `record_cold_verification_from_task`; statically calls `record_cold_verification_from_task`
- [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]] — imports `sweep_expired_cold_retries`; statically calls `sweep_expired_cold_retries`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `cold_verification_context`; statically calls `cold_verification_context`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `evaluate_final_coldness`, `record_final_receipt`; calls `evaluate_final_coldness`, `record_final_receipt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `ColdVerificationPrecondition`, `candidate_has_current_blind_input_contract`, `record_causal_cold_outcome`, `record_delayed_cold_verification`; calls `candidate_has_current_blind_input_contract`, `record_causal_cold_outcome`, `record_delayed_cold_verification`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `_case_repair_class_id`, `_receipt_repair_class_id`, `diagnosis_receipt`, `open_factors_for_hypothesis`; calls `_case_repair_class_id`, `_receipt_repair_class_id`, `diagnosis_receipt`, `open_factors_for_hypothesis`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
  - `test_clean_consume_records_cold_success_row_idempotently`
  - `test_contaminated_consume_records_typed_row`
  - `test_expired_inactive_surface_is_unmeasurable_not_censored`
  - `test_expired_servable_task_right_censors`
  - `test_missing_chain_records_typed_row`
  - `test_same_surface_consume_records_typed_row`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_cold_verification_context_names_the_avoided_affordances`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_the_fresh_retry_records_its_own_repair_forecast_which_resolves_when_it_is_measured`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_delivered_passage_on_the_cold_items_own_source_span_is_hard`
  - `test_delivered_passages_in_interval_are_typed_exposure_not_indeterminate`
  - `test_delivery_outside_the_interval_is_observed_silence_not_indeterminate`
  - `test_expired_task_gets_a_partial_final_receipt`
  - `test_feedback_reopen_on_the_cold_item_is_a_hard_answer_reveal`
  - `test_feedback_reopen_on_the_source_attempt_is_a_soft_exposure`
  - `test_happy_path_snapshot_verification_and_final_receipt`
  - `test_hard_same_surface_exposure_yields_disposition_not_verification`
  - `test_no_reveal_rows_is_a_scoped_absence_claim_not_a_bare_pass`
  - `test_over_budget_episode_downgrades_the_repair_effect_claim`
  - `test_prescription_without_a_delivery_record_is_unknown_not_pass`
  - `test_recent_retrieval_resets_the_cold_delay_anchor`
  - `test_retrieval_cointervention_demotes_attribution_not_the_verification`
  - `test_reveal_elsewhere_in_the_learning_object_is_soft_not_a_failure`
  - `test_reveal_on_the_cold_item_fails_leakage_and_unassisted`
  - `test_unrelated_remediation_is_counted_but_does_not_change_coldness`
  - `test_within_budget_episode_records_the_spend_without_downgrading`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task`
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_a_deferred_cold_retry_still_expires_on_its_original_window`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice_and_ends_it_honestly`

## Modification guidance

- Change causal cold verification policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_cold_verification.py](../../../../../../src/learnloop/diagnosis/causal_cold_verification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
