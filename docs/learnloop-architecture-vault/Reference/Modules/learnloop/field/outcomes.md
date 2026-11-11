---
title: "learnloop.field.outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/outcomes.py"
source_paths:
  - "src/learnloop/field/outcomes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.outcomes module"
  - "src/learnloop/field/outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.outcomes` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Read-only outcome projection over grading ledgers, never the debug trace.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/outcomes.py](../../../../../../src/learnloop/field/outcomes.py) |
| Source lines | 915 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `borrowed_repository(connection: sqlite3.Connection) -> Repository` ([source](../../../../../../src/learnloop/field/outcomes.py), line 64) — A repository view that reads inside the caller's open snapshot.
- `resolve_legacy_fallback(vault, legacy_fallback=None) -> str` ([source](../../../../../../src/learnloop/field/outcomes.py), line 239) — The single revision policy: an explicit option, else ``field.legacy_fallback``.
- `current_criterion_evidence(evidence) -> list` ([source](../../../../../../src/learnloop/field/outcomes.py), line 255) — The latest surviving record for each criterion of an attempt's live rows.
- `unverified_criterion_ids(evidence) -> set[str]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 265) — PF-c: the criteria of the current grade the valid-alternative gate recorded unverified.
- `wholly_unassessed(evidence) -> bool` ([source](../../../../../../src/learnloop/field/outcomes.py), line 270) — PF-c: every criterion of the current grade is unverified, so the attempt measures nothing (owner decision 2026-10-12), whatever its scheduling grade.
- `measurement_masses(connection, vault: LoadedVault, ledger) -> dict[str, float]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 277) — Per attempt, its effective mass before the item-dependent (familiarity) and assistance discounts: the attempt type's mass (an independent attempt's for a hinted one, as ``mass_without_assistance``), quarantine, an unassessable type and the grade's reliability.
- `load_attempt_rows(connection, vault: LoadedVault, *, legacy_fallback=None, as_of=None, retrieval=False, attempt_rows=None) -> tuple[AttemptRow, ...]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 719) — Immutable attempt rows, including zero-mass exclusions for accounting.
- `load_replay_rows(connection, vault: LoadedVault, *, legacy_fallback=None)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 735) — Attempt and facet rows for one prequential replay, read in one pass.
- `fsrs_predicted_retrievability(connection, vault: LoadedVault, repository: Repository, *, held_attempt_ids=frozenset()) -> dict[str, float]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 740) — FSRS-predicted retrievability at each graded attempt, from the ledger.
- `load_effective_replay_rows(connection, vault: LoadedVault, *, legacy_fallback=None, include_workbench=True)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 776) — ``(attempts, facets, signals)`` with the complete coldness derivation.
- `load_facet_rows(connection, vault: LoadedVault, *, legacy_fallback=None, as_of=None) -> tuple[FacetRow, ...]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 791)
- `rebuild_outcome_view(connection, vault: LoadedVault, *, legacy_fallback=None) -> int` ([source](../../../../../../src/learnloop/field/outcomes.py), line 795) — Replace only the outcome cache; transaction ownership stays with caller.
- `data_check(connection, vault: LoadedVault, *, legacy_fallback=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 808) — Aggregate-only diagnostic; no learner answers, prompts or debug text.

### Module constants

- `OUTCOME_VIEW_VERSION` ([src/learnloop/field/outcomes.py](../../../../../../src/learnloop/field/outcomes.py), line 51)
- `GRADED_RETRIEVAL_TYPES` ([src/learnloop/field/outcomes.py](../../../../../../src/learnloop/field/outcomes.py), line 236)

## Internal implementation anchors

- `class _ReadRepository(Repository)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 54) — Borrow the caller's transaction; repository reads must not commit it.
- `_json(value: str | None, default: Any=None) -> Any` ([source](../../../../../../src/learnloop/field/outcomes.py), line 69)
- `_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/field/outcomes.py), line 73)
- `_plan_served(plan_served, attempt, candidate_id)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 78) — The plan's ``item_served`` receipt for this attempt, or None.
- `_serving(connection, attempt, plan_served=None)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 102)
- `_revision(connection, vault, attempt, evidence, candidate_id, fallback)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 154)
- `_unverified(record) -> bool` ([source](../../../../../../src/learnloop/field/outcomes.py), line 247) — A criterion the PF-c valid-alternative gate recorded as unverified.
- `_hedging_readings(connection) -> dict[str, tuple[int, int]]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 314) — Per attempt, (hedged, read): the grader's reading of the learner's tone.
- `_answer_signal_counts(attempts) -> dict[str, Any]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 337)
- `_answer_signals(attempt: dict, hedging: dict[str, tuple[int, int]]) -> AnswerSignals` ([source](../../../../../../src/learnloop/field/outcomes.py), line 366) — The attempt's own pre-outcome signals (offline answer-signal arms only).
- `_grader_models(connection) -> dict[str, str]` ([source](../../../../../../src/learnloop/field/outcomes.py), line 383) — Latest raw grade event of each attempt's latest observation (no text).
- `_retrieval_cold(connection, repository, attempt, policy, since)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 399) — Strict research coldness for memory arms; returns (cold, window start).
- `_load(connection, vault, *, legacy_fallback=None, as_of=None, retrieval=False, diagnostics=None, attempt_rows=None)` ([source](../../../../../../src/learnloop/field/outcomes.py), line 440) — Derive attempt and facet rows; ``retrieval`` adds the memory-arm fields.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]] — imports `load_attempt_rows`; statically calls `load_attempt_rows`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `load_attempt_rows`, `measurement_masses`; statically calls `load_attempt_rows`, `measurement_masses`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `wholly_unassessed`; statically calls `wholly_unassessed`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `borrowed_repository`, `data_check`, `load_effective_replay_rows`; statically calls `borrowed_repository`, `data_check`, `load_effective_replay_rows`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `borrowed_repository`; statically calls `borrowed_repository`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `fsrs_predicted_retrievability`, `load_effective_replay_rows`, `rebuild_outcome_view`; statically calls `fsrs_predicted_retrievability`, `load_effective_replay_rows`, `rebuild_outcome_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `fsrs_rating_for_attempt`; calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `build_effective_observation`, `effective_observation_from_posterior`, `load_effective_observation_references`; calls `build_effective_observation`, `effective_observation_from_posterior`, `load_effective_observation_references`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `production_admissibility`; calls `production_admissibility`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_answer_summary`; calls `stuck_answer_summary`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `plan_served_origins`; calls `plan_served_origins`
- [[Reference/Modules/learnloop/db/stores/facet_identity|learnloop.db.stores.facet_identity]] — imports `settled_merge_rows`; calls `settled_merge_rows`
- [[Reference/Modules/learnloop/db/stores/families|learnloop.db.stores.families]] — imports `family_judge_models`; calls `family_judge_models`
- [[Reference/Modules/learnloop/db/stores/field|learnloop.db.stores.field]] — imports `replace_facet_outcomes`; calls `replace_facet_outcomes`
- [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] — imports `load_authoritative_observation_ledger`; calls `load_authoritative_observation_ledger`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `resolve_attempt_activity_policy`; calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `enrich_attempts`, `load_interaction_signals`; calls `enrich_attempts`, `load_interaction_signals`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`; calls `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`, `rubric_from_contract`; calls `compile_assessment_contract`, `rubric_from_contract`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `resolve_item_irt_params`; calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `derive_facet_outcomes`, `familiarity_discount_from_attempts`, `resolve_coverage`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`; calls `derive_facet_outcomes`, `familiarity_discount_from_attempts`, `resolve_coverage`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `predicted_retrievability_by_attempt`, `review_log_from_attempts`; calls `predicted_retrievability_by_attempt`, `review_log_from_attempts`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `UNVERIFIED_CRITERION_BLOCK`, `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `sqlite3`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/pfc_unassessed_readers_helpers.py](../../../../../../tests/pfc_unassessed_readers_helpers.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_historical_regrade_reads_its_current_epoch_not_a_surviving_obsolete_criterion`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_ad_reads_history_through_its_own_fallback_and_field_keeps_its_own`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_view_labels_the_pick_as_field_does_outside_ad`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_every_serving_branch_runs_with_zero_denials_and_fields_labels`
- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_the_loader_reads_the_tap_and_the_graders_tone_reading`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_an_empty_stuck_answer_on_a_plan_item_is_done_and_labelled_daily_plan`
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_plan_served_attempts_have_the_daily_plan_serving_kind`
- [tests/test_facet_outcome_view.py](../../../../../../tests/test_facet_outcome_view.py) — direct import
  - `test_changed_numeric_mapping_is_not_proven_by_same_targets`
  - `test_dont_know_and_priming_do_not_double_discount`
  - `test_edited_current_item_never_changes_exact_row`
  - `test_exact_debug_agreement_and_no_debug_authority`
  - `test_frozen_compiled_targets_must_match_selected_item`
  - `test_future_receipt_cannot_prove_revision`
  - `test_historical_subject_and_demand_ignore_current_lo`
  - `test_latest_epoch_and_canonical_merge`
  - `test_missing_revision_excluded_and_current_content_opt_in`
  - `test_multifacet_weight_is_not_multiplied`
  - `test_partial_fractional_criterion_uses_assessed_denominator`
  - `test_quarantine_has_zero_mass_even_without_assistance`
  - `test_rebuild_deterministic_and_never_writes_evidence`
  - `test_requested_text_is_not_a_machine_readable_request_receipt`
  - `test_selected_revision_must_match_attempt_receipts`
  - `test_serving_offer_join_is_not_a_propensity`
  - `test_zero_mass_attempt_does_not_change_later_valid_weight`
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
- [tests/test_field_split_outcomes.py](../../../../../../tests/test_field_split_outcomes.py) — direct import
  - `test_an_attempt_with_only_unverified_criteria_has_no_outcome_row`
  - `test_an_unverified_pfc_criterion_is_unassessed_in_the_field`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_an_attempts_rows_and_hint_outcome_are_unchanged_by_its_workbench_rows`
  - `test_the_rebuild_never_reads_the_workbench_tables`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_placement_and_the_field_read_a_held_attempt_as_unassessed`
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_adopted_reader_card_is_untested_on_the_map_with_no_outcome_row`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_field_projection_and_timeline_read_unverified_criteria_the_same_way`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains outcomes within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/outcomes.py](../../../../../../src/learnloop/field/outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
