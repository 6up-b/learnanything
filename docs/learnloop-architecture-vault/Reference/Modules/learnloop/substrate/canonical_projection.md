---
title: "learnloop.substrate.canonical_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/canonical_projection.py"
source_paths:
  - "src/learnloop/substrate/canonical_projection.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.canonical_projection module"
  - "src/learnloop/substrate/canonical_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.canonical_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.canonical_projection` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: KM2 canonical belief projection (§5.3/§5.4/§6/§7.1).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py) |
| Source lines | 1152 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `p0_effective_evidence_mass(repository: Repository, *, interpretation: Mapping[str, Any] | None, attempt_type_mass: float, references: EffectiveObservationReferences | None=None) -> float` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 124) — THE mvp-0.8 response-level evidence-mass discount (P0.3 §4.3), shared by both evidence folds.
- `surface_group_id(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 167) — The correlation/surface group an item's evidence belongs to (§6).
- `class CanonicalProjectionSnapshot` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 228) — Bulk-loaded, immutable inputs for one canonical evidence replay.
- `load_canonical_projection_snapshot(repository: Repository, *, algorithm_version: str) -> CanonicalProjectionSnapshot` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 240) — Read replay inputs once, before the pure attempt fold begins.
- `attribution_weights(raw: object, targets: list[CriterionTarget]) -> dict[tuple[str, str], float]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 349) — Normalize persisted failure attribution over the criterion targets.
- `observed_unresolved_failure(observed_fraction: float, targets: Sequence[CriterionTarget], attribution: Mapping[tuple[str, str], float]) -> bool` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 379) — True when an OBSERVED failure has multiple candidate causes and no resolving attribution (§5.3) — the condition that opens an unresolved-cause factor.
- `configured_repeat_discount(vault: LoadedVault) -> float` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 544)
- `project_canonical_facet_state(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 552) — Recompute and persist the canonical belief cache.
- `project_capability_residuals(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 995) — Derive lazy capability-residual activation state (§4.2, KM5; DEFAULT OFF).

### Module constants

- `FAILURE_THRESHOLD` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 56)
- `DEFAULT_REPEAT_SURFACE_DISCOUNT` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 61)
- `ASSISTED_ATTEMPT_TYPES` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 69)
- `CANONICAL_PROJECTION_VERSION` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 121)

## Internal implementation anchors

- `class _RecallAcc` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 189)
- `class _CapAcc` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 201)
- `class _HistoricalCriterion` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 219)
- `_historical_contract(evidence: list[dict[str, Any]], *, contracts_by_source_version: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 287) — Resolve the immutable assessment contract attached to this grading.
- `_contract_criteria(contract: Mapping[str, Any]) -> list[_HistoricalCriterion]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 312)
- `_contract_surface_group(contract: Mapping[str, Any], practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 339)
- `_target_ref_key(target_ref: Any) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 398) — Identity of a candidate cause's declared target, for union de-duplication.
- `_facet_target_cause(target: CriterionTarget) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 414) — One synthesized open-world arm for a criterion target.
- `_open_candidate_causes(error_events: Sequence[Mapping[str, Any]], targets: Sequence[CriterionTarget]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 439) — Thin candidate set for an unresolved factor, always open-world.
- `_adjudicated_score_fraction(adjudication: Mapping[str, Any] | None, interpretation: Mapping[str, Any] | None, score_fraction: Mapping[str, float]) -> float | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 508) — Observed-outcome override when an adjudication heads the interpretation chain.
- `_sync_unresolved_cause_factors(repository: Repository, unresolved: list[dict[str, object]], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 1120) — Idempotently reconcile open unresolved-cause factors with the projection.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `FAILURE_THRESHOLD`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `CANONICAL_PROJECTION_VERSION`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `DEFAULT_REPEAT_SURFACE_DISCOUNT`, `FAILURE_THRESHOLD`, `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`; statically calls `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `FAILURE_THRESHOLD`, `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `EffectiveObservationReferences`, `build_effective_observation`, `load_effective_observation_references`; calls `build_effective_observation`, `load_effective_observation_references`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `COARSE_RESPONSE_SLUG`, `ensure_builtin_schemas`; calls `ensure_builtin_schemas`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `cap_embedded_credit`, `supporting_unexercised`; calls `cap_embedded_credit`, `supporting_unexercised`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `ASSISTED_ATTEMPT_TYPES`, `resolve_attempt_activity_policy`; calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/goals/receipt_contributions|learnloop.goals.receipt_contributions]] — imports `itemize_observation_contributions`; calls `itemize_observation_contributions`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CriterionTarget`, `LoadedVault`, `PracticeItem`; calls `CriterionTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] and 22 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
  - `test_anti_double_count_claim_seeds_prior_but_earns_no_mass`
  - `test_anti_double_count_observation_attaches_once`
  - `test_anti_double_count_projection_deterministic_and_idempotent`
  - `test_anti_double_count_projection_signal_earns_zero_certification`
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — direct import
  - `test_fresh_startup_stamps_a_silent_projection_baseline_once`
  - `test_projection_upgrade_stays_silent_while_vault_has_no_attempts`
  - `test_startup_records_one_recalibration_for_an_unstamped_practised_vault`
- [tests/test_causal_activity_policy.py](../../../../../../tests/test_causal_activity_policy.py) — direct import
  - `test_near_clone_is_a_fingerprint_comparison_not_provenance`
  - `test_rebuild_records_the_current_projection_version`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_projection_sync_does_not_resurrect_deferral_closed_factors`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_projection_bulk_loads_candidate_cause_error_events_once`
  - `test_projection_version_names_the_open_cause_union`
- [tests/test_characterization_certification_ledger.py](../../../../../../tests/test_characterization_certification_ledger.py) — direct import
  - `test_projection_mass_identical_across_grader_confidence`
  - `test_regrade_of_grading_evidence_changes_projection`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_merged_facet_does_not_desynchronise_the_two_folds`
  - `test_a_trace_row_for_a_different_facet_does_not_license_the_supporting_target`
  - `test_an_exercised_supporting_target_does_make_the_failure_ambiguous`
  - `test_an_unexercised_supporting_target_costs_its_criterion_no_measurement`
  - `test_an_unexercised_supporting_target_takes_no_blame_when_its_own_step_fails`
  - `test_failure_at_step_one_leaves_later_steps_unassessed_not_failed`
  - `test_failure_at_step_three_indicts_only_the_diverged_facet`
  - `test_full_pass_credits_every_primary_cell_and_banks_unexercised_supporting_mass`
  - `test_guard_1_holds_in_the_receipt_fold_as_well_as_the_projection`
  - `test_the_configured_share_is_the_ledgers_cap_and_one_point_zero_disables_it`
  - `test_the_projection_version_pins_the_current_replay_semantics`
  - `test_trace_evidence_report_surfaces_unexercised_cells_and_abstains_on_concentration`
  - `test_trace_evidence_turns_the_supporting_target_into_embedded_credit`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_clean_solution_false_positive_writes_a_candidate_not_a_facet_failure`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_retire_surface_from_cli_preserves_evidence_and_logs_reason`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_a_shared_stimulus_outranks_differing_authored_family_names`
  - `test_exam_practiced_surfaces_are_groups`
  - `test_genuinely_unrelated_items_stay_distinct`
- [tests/test_measurement_corrections.py](../../../../../../tests/test_measurement_corrections.py) — direct import
  - `test_attempted_item_correction_is_append_only_and_projection_versioned`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_canonical_projection_bulk_loads_historical_contracts_once`
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_primed_provenance_reaches_projection_and_blocks_certification`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_activation_records_derived_state_rebuild`
  - `test_adjudicating_up_raises_credit_and_unchanged_direction_skips`
  - `test_adjudication_reverses_projection_and_preserves_history`
  - `test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_creates_ordinary_copy_and_probe_stays_retired`
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_missing_evidence_rows_bank_nothing`
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
  - `test_partially_graded_attempt_credits_only_the_graded_criterion`
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — direct import
  - `test_per_observation_itemization_sums_to_banked_credit`
  - `test_ready_derivation_matches_canonical_recall_slices`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
  - `test_from_scratch_fold_equals_incremental_fold_on_real_history`
  - `test_timeline_final_credit_equals_banked_ledger_credit`
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import
  - `test_adjudicated_failure_to_success_retires_cause_factor`
  - `test_adjudicated_success_to_failure_opens_cause_factor`

## Modification guidance

- Change canonical projection policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
