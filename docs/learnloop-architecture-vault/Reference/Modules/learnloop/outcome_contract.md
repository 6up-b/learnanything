---
title: "learnloop.outcome_contract"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/outcome_contract.py"
source_paths:
  - "src/learnloop/outcome_contract.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.outcome_contract module"
  - "src/learnloop/outcome_contract.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.outcome_contract`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.outcome_contract` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Versioned observational label eligibility, independent of persistence.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `unverified_evidence_row(attribution: Any) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 55) — Whether a grading-evidence row is a PF-c unverified criterion, under either interpretation.
- `unassessed_evidence_row(attribution: Any) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 64) — Whether a grading-evidence row is a PF-c criterion written under the unassessed rule (owner decision 2026-10-12).
- `grade_held_for_review(grading_support: Mapping[str, Any] | None) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 118) — Did the route rule (or mvp-0.17's route check) hold this grade?
- `grade_is_held(*, record_held: bool, anything_assessed: bool) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 138) — THE held-grade predicate (held-grade-evidence): is this attempt's grade held for review, and so unusable as evidence anywhere?
- `retention_exclusions(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../src/learnloop/outcome_contract.py), line 163)

### Module constants

- `COLLECTION_VERSION` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 13)
- `LABEL_VERSION` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 14)
- `RETENTION_MIN_DELAY_SECONDS` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 15)
- `PFC_REVIEW_REASON` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 29)
- `PFC_PARTIALLY_ASSESSED` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 31)
- `PFC_NOTHING_ASSESSED` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 33)
- `UNVERIFIED_CRITERION_BLOCK` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 41)
- `UNVERIFIED_INTERPRETATION_KEY` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 42)
- `UNASSESSED_INTERPRETATION` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 43)
- `GRADE_HELD_FOR_REVIEW` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 92)
- `PRE_HOLD_ROUTE_CHECK_VERSIONS` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 95)
- `HOLD_KEPT_FROM_KEY` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 101)
- `HELD_ROW_KEY` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 106)
- `GRADE_CONTRACT_UNRECORDED` ([src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py), line 115)

## Internal implementation anchors

- `_attribution_mapping(attribution: Any) -> Mapping[str, Any] | None` ([source](../../../../../src/learnloop/outcome_contract.py), line 46)
- `_observed_delay_at_least(elapsed_seconds: Any, minimum: float) -> bool` ([source](../../../../../src/learnloop/outcome_contract.py), line 204) — A missing or non-finite delay is unobserved, so it never qualifies.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GRADE_CONTRACT_UNRECORDED`, `HELD_ROW_KEY`, `grade_held_for_review`, `grade_is_held`; statically calls `grade_held_for_review`, `grade_is_held`
- [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]] — imports `GRADE_CONTRACT_UNRECORDED`, `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `GRADE_CONTRACT_UNRECORDED`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `grade_held_for_review`; statically calls `grade_held_for_review`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `RETENTION_MIN_DELAY_SECONDS`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`
- [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `RETENTION_MIN_DELAY_SECONDS`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `GRADE_HELD_FOR_REVIEW`, `unassessed_evidence_row`; statically calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `grade_held_for_review`; statically calls `grade_held_for_review`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `grade_held_for_review`; statically calls `grade_held_for_review`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `GRADE_HELD_FOR_REVIEW`, `unassessed_evidence_row`; statically calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `GRADE_CONTRACT_UNRECORDED`, `HELD_ROW_KEY`, `PFC_NOTHING_ASSESSED`, `PFC_PARTIALLY_ASSESSED`, `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`; statically calls `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]] — imports `RETENTION_MIN_DELAY_SECONDS`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `RETENTION_MIN_DELAY_SECONDS`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `GRADE_HELD_FOR_REVIEW`, `unverified_evidence_row`; statically calls `unverified_evidence_row`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `unassessed_evidence_row`, `unverified_evidence_row`; statically calls `unassessed_evidence_row`, `unverified_evidence_row`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `COLLECTION_VERSION`, `GRADE_HELD_FOR_REVIEW`, `LABEL_VERSION`, `retention_exclusions`; statically calls `retention_exclusions`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `GRADE_HELD_FOR_REVIEW`, `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`; statically calls `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `grade_held_for_review`, `unassessed_evidence_row`; statically calls `grade_held_for_review`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `math`, `numbers`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] and 28 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_chain_records.py](../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_held_grade_gets_a_record_when_the_hold_first_applies`
- [tests/test_collection_dataset.py](../../../../../tests/test_collection_dataset.py) — direct import
  - `test_adjudication_accepts_evidence_keyed_by_a_non_id_primary_key`
  - `test_retention_contract_rejects_contaminated_or_unobserved_labels`
- [tests/test_daily_plan_owner_decisions.py](../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_plan_served_attempts_have_the_daily_plan_serving_kind`
- [tests/test_data_capture_a4_delayed_completion.py](../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
  - `test_a_delay_counts_to_the_presentation_not_the_answer`
  - `test_the_definition_reuses_the_contracts_delay_and_no_new_number`
- [tests/test_held_grade_evidence.py](../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f5_an_adjudication_releases_the_follow_up_suppression`
  - `test_f6_the_dataset_exports_no_held_score_as_observed`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
  - `test_review_f2_a_scored_cold_probe_regraded_into_a_hold_abstains`
  - `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing`
  - `test_the_predicate_is_the_record_and_the_current_evidence`
- [tests/test_help_outcomes.py](../../../../../tests/test_help_outcomes.py) — direct import
  - `test_f6_a_hold_released_after_as_of_still_held_then`
- [tests/test_pfc_unassessed_readers.py](../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_separate_review_concern_survives_the_pfc_flag`
  - `test_retention_exclusions_distinguish_the_review_reasons`
  - `test_retention_exclusions_keep_the_pfc_state_and_the_review_independent`
- [tests/test_pfc_unverified_unassessed.py](../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_the_stamped_block_is_read_from_text_or_mapping`
- [tests/test_re0_capture.py](../../../../../tests/test_re0_capture.py) — direct import
  - `test_the_warmth_window_is_the_outcome_contracts_retention_minimum_not_a_new_constant`
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_a_first_grade_made_before_contracts_keeps_its_compatibility_reading`
  - `test_a_regrade_in_its_pre_contract_grades_second_is_held_not_read_as_its_only_grade`
  - `test_a_successor_regrade_releases_an_unrecorded_hold`
  - `test_an_uncited_regrade_epoch_is_held_with_the_maximum_recorded_with_it`
- [tests/test_ro5_codex_review.py](../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f1_a_current_epoch_that_assesses_nothing_is_no_observation`
- [tests/test_ro6_landing.py](../../../../../tests/test_ro6_landing.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_live_nothing_located_and_nothing_validated_is_held`
- [tests/test_sources_merge_composition.py](../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_held_grade_is_no_intervention_outcome`
- [tests/test_teacher_te0_fix_round2.py](../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_the_live_history_keeps_the_ledgers_hold`

## Modification guidance

- Make changes here when the responsibility remains outcome contract within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/outcome_contract.py](../../../../../src/learnloop/outcome_contract.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
