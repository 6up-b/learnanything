---
title: "learnloop.diagnosis.causal_probe_coherence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_probe_coherence.py"
source_paths:
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_probe_coherence module"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_probe_coherence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_probe_coherence` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 causal probe coherence.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py) |
| Source lines | 1998 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CausalProbeParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 121) — Resolved probe-policy knobs plus their provenance.
  - `__getitem__(self, key: str) -> float` (line 134; internal)
  - `recent_diagnostic_limit(self) -> int` (line 138; public)
  - `manifest(self) -> dict[str, Any]` (line 141; public)
- `resolve_causal_probe_parameters(repository: Repository | None) -> CausalProbeParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 151) — Active fitted probe-policy knobs, else the pinned heuristic defaults.
- `class BundleFeatureRow` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 216) — One declared prediction row.
  - `matches(self, observed_features: Mapping[str, Any]) -> bool` (line 228; public)
  - `as_record(self) -> dict[str, Any]` (line 238; public)
- `class BundleFeatureRowReport` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 243)
  - `usable(self) -> bool` (line 248; public)
- `bundle_feature_row_report(predictions: Mapping[str, Any] | None) -> BundleFeatureRowReport` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 280) — Parse every declared feature row plus the typed reasons for the rest.
- `parse_bundle_feature_rows(predictions: Mapping[str, Any]) -> list[BundleFeatureRow]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 337) — The single parser used by generation, discrimination, and classification.
- `rows_are_separable(left: Sequence[BundleFeatureRow], right: Sequence[BundleFeatureRow]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 370) — True iff some observation can match exactly one of the two row sets.
- `class ProbeDecision` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 391)
  - `as_dict(self) -> dict[str, Any]` (line 406; public)
- `decide_probe(*, repair_class_ids: Sequence[str | None], common_repair_covers: bool, expected_information_gain: float, probability_information_changes_repair: float, probe_burden_minutes: float, avoided_overteaching_minutes: float, pending_machine_checks: Sequence[str]=(), session_budget_minutes: float | None=None, learner_preference: str='allow', recent_diagnostic_burden: int=0, repository: Repository | None=None, parameters: CausalProbeParameters | None=None) -> ProbeDecision` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 413) — Apply §7's EVSI-flavoured, action-relative probe rule.
- `repair_class_need_for_factor(repository: Repository, factor_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 527)
- `rung_divergence_gate(repository: Repository, hypotheses: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 571) — Golden-path cause → repair-rung gate, tri-state (§3.7).
- `class CausalHypothesisSetPlan` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 665) — An unlocked set plus the provenance of its prior.
  - `as_hypothesis_set(self, set_id: str | None=None) -> HypothesisSet` (line 679; public)
- `build_causal_hypothesis_set(repository: Repository, factor_id: str, *, support_scores: Mapping[str, float | None] | None=None) -> CausalHypothesisSetPlan` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 705) — Build the hypothesis-set plan from P1 ids, always with H_OTHER.
- `lock_causal_hypothesis_set(repository: Repository, factor_id: str, *, probe_phase_id: str | None, algorithm_version: str, support_scores: Mapping[str, float | None] | None=None, clock: Clock | None=None) -> HypothesisSet` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 814)
- `class BlindGenerationInput` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 863) — The ONLY thing a blind prediction generator ever sees.
  - `as_payload(self) -> dict[str, Any]` (line 884; public)
- `generate_blind_prediction_bundle(repository: Repository, *, hypothesis_id: str, item: PracticeItem | Mapping[str, Any], rubric: Any, trace_contract: Any, generator: Callable[[dict[str, Any]], Mapping[str, Any]], model_revision: str, outcome_schema_version: str, generation_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 928) — Generate and persist a bundle from a typed, allowlisted blind input.
- `blind_bundle_discrimination(repository: Repository, *, hypothesis_ids: Sequence[str], practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1040) — Assess discrimination using only stamped blind bundles.
- `classify_against_blind_bundles(repository: Repository, *, hypothesis_set_id: str, practice_item_id: str, blind_bundle_ids: Sequence[str], observed_features: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1144) — Classify an administered probe against the bundles PINNED to the probe.
- `audit_manipulation_contract(repository: Repository, *, source_item: PracticeItem | Mapping[str, Any], candidate_item: PracticeItem | Mapping[str, Any], source_kind: str, adversarial_review: Mapping[str, Any] | None, generation_agent_run_id: str | None=None, reviewer_agent_run_id: str | None=None, require_adversarial: bool=True, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1400) — Run the shared probe/rung structural diff plus independent review.
- `validate_independent_measurement_contract(measurement_contract: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1492) — Reject parent-weight inheritance and require recompilation or abstention.
- `create_probe_candidate(repository: Repository, *, factor_id: str, practice_item_id: str, hypothesis_set_id: str, manipulation_audit_id: str, measurement_contract: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1515) — Mint a candidate only after blind discrimination and the diff audit.
- `candidate_has_current_blind_input_contract(candidate: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1575) — Whether a candidate was minted from the observation-free v2 input.
- `order_probe_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1605) — THE deterministic candidate order, shared by every consumer.
- `transition_probe_candidate(repository: Repository, candidate_id: str, *, to_status: str, reviewer: str | None=None, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1631) — Enforce candidate → registered → reviewed → active.
- `classify_causal_activity(repository: Repository, *, attempt_id: str, contamination_class: str, near_clone: bool=False, near_clone_basis: str | None=None, source: str='causal_probe_coherence', detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1705) — Persist the contamination classification for one attempt.
- `class ColdVerificationPrecondition(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1758) — A §6.2 precondition failed, with the §4.3 disposition it maps to.
  - `__init__(self, reason: str, message: str, *, detail: Mapping[str, Any] | None=None)` (line 1765; internal)
- `record_causal_cold_outcome(repository: Repository, *, outcome: str, followup_task_id: str | None=None, remediation_episode_id: str | None=None, case_kind: str | None=None, case_ref: str | None=None, source_attempt_id: str | None=None, cold_attempt_id: str | None=None, repair_class_id: str | None=None, hypothesis_ids: Sequence[str]=(), cold_verification_id: str | None=None, servable_opportunity: bool, detail: Mapping[str, Any] | None=None, scheduled_not_before: str | None=None, scheduled_expires_at: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1771) — Write one typed terminal disposition (spec §4.3).
- `record_delayed_cold_verification(vault: LoadedVault, repository: Repository, *, source_attempt_id: str, cold_attempt_id: str, repair_class_id: str, hypothesis_ids: Sequence[str], avoided_affordances: Sequence[str], diagnosis_support_update: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1833) — Record three separate cold-outcome channels.

### Module constants

- `PROBE_REVIEW_TRANSITIONS` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 47)
- `BLIND_INPUT_CONTRACT_VERSION` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 60)
- `FEATURE_ROW_SKIP_REASONS` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 65)
- `CLASSIFICATION_OUTCOMES` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 75)
- `RUNG_GATE_STATES` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 84)
- `CAUSAL_PROBE_POLICY_DEFAULTS` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 95)
- `_CAUSAL_PROBE_POLICY_BOUNDS` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 109)
- `_RUBRIC_CRITERION_FIELDS` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 851)
- `CANDIDATE_STATUS_RANK` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1588)
- `CAUSAL_COLD_OUTCOME_STORE_VERSION` ([src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1755)

## Internal implementation anchors

- `_content_id(prefix: str, value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 189)
- `_jsonable(value: Any) -> Any` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 196)
- `_canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 206)
- `_feature_row_from_mapping(source: str, raw: Any) -> tuple[BundleFeatureRow | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 252) — Build one row, or a typed skip record.
- `_rows_conflict(left: BundleFeatureRow, right: BundleFeatureRow) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 348) — True iff the rows disagree on a key they BOTH declare.
- `_discriminating_row(row: BundleFeatureRow, others: Sequence[BundleFeatureRow]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 364)
- `_hypothesis_prior_weight(hypothesis: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 688) — The grader's normalized verbalized prior for one hypothesis, or 0.0.
- `_rubric_criteria(rubric: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 901)
- `_optional_mapping(value: Any) -> dict | None` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 923)
- `_cohort_of(bundle: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1017)
- `_cohort_record(cohort: tuple[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1024)
- `_single_cohort(bundles: Iterable[Mapping[str, Any]]) -> tuple[tuple[str, str] | None, list[dict[str, str]]]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1031)
- `_item_diff(source: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1329)
- `_candidate_separable_pairs(candidate: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py), line 1597)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `transition_probe_candidate`; statically calls `transition_probe_candidate`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `audit_manipulation_contract`; statically calls `audit_manipulation_contract`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `BLIND_INPUT_CONTRACT_VERSION`, `bundle_feature_row_report`; statically calls `bundle_feature_row_report`
- [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]] — imports `BLIND_INPUT_CONTRACT_VERSION`, `bundle_feature_row_report`; statically calls `bundle_feature_row_report`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `ColdVerificationPrecondition`, `ProbeDecision`, `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `record_causal_cold_outcome`, `record_delayed_cold_verification`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`; statically calls `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `record_causal_cold_outcome`, `record_delayed_cold_verification`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning|learnloop.diagnosis.causal_probe_commissioning]] — imports `audit_manipulation_contract`, `blind_bundle_discrimination`, `build_causal_hypothesis_set`, `candidate_has_current_blind_input_contract`, `create_probe_candidate`, `generate_blind_prediction_bundle`, `lock_causal_hypothesis_set`, `repair_class_need_for_factor`, `transition_probe_candidate`; statically calls `audit_manipulation_contract`, `blind_bundle_discrimination`, `build_causal_hypothesis_set`, `candidate_has_current_blind_input_contract`, `create_probe_candidate`, `generate_blind_prediction_bundle`, `lock_causal_hypothesis_set`, `repair_class_need_for_factor`, `transition_probe_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `candidate_has_current_blind_input_contract`, `order_probe_candidates`; statically calls `candidate_has_current_blind_input_contract`, `order_probe_candidates`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `lock_causal_hypothesis_set`; statically calls `lock_causal_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `record_causal_cold_outcome`; statically calls `record_causal_cold_outcome`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `resolve_causal_probe_parameters`; statically calls `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `candidate_has_current_blind_input_contract`, `transition_probe_candidate`; statically calls `candidate_has_current_blind_input_contract`, `transition_probe_candidate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `NEAR_CLONE_BASES`, `assess_near_clone`, `policy_for_class`; calls `assess_near_clone`, `policy_for_class`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `OPEN_SET_CAUSE_ID`, `SUPPORT_BASIS_AUTHORITY`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `apply_cold_verification_to_factors`; calls `apply_cold_verification_to_factors`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `Hypothesis`, `HypothesisSet`; calls `Hypothesis`, `HypothesisSet`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `CAUSAL_PROBE_POLICY_SCOPE`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p2.py](../../../../../../tests/test_causal_attribution_p2.py) — direct import
  - `test_all_bundles_matched_is_not_open_set_evidence`
  - `test_blind_bundles_diff_audit_and_review_ladder`
  - `test_bundles_from_different_cohorts_never_compare`
  - `test_classification_is_pinned_and_survives_a_newer_bundle`
  - `test_cold_success_updates_repair_effect_not_diagnosis`
  - `test_empty_feature_row_is_rejected_at_generation_and_skipped_at_read`
  - `test_evsi_rule_is_action_relative_and_budgeted`
  - `test_repair_class_divergence_locks_existing_hypothesis_set_with_other`
  - `test_rung_divergence_gate_defers_instead_of_buying_learner_effort`
  - `test_subset_rows_without_a_conflicting_shared_key_are_inseparable`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_a_primed_attempt_can_never_resolve_a_factor`
  - `test_an_auto_primed_attempt_can_never_resolve_a_factor`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_diagnosis_support_moves_only_on_independent_discriminating_evidence`
  - `test_one_authored_cause_is_unioned_with_the_synthesized_arms`
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
  - `test_commissioning_lights_the_lane_end_to_end`
  - `test_commissioning_makes_the_orchestrator_see_an_instrument`
  - `test_obsolete_observation_exposed_candidate_cannot_advance`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
  - `test_cold_verification_records_its_near_clone_basis`
  - `test_open_set_cause_id_and_probe_label_are_distinct_namespaces`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_evpi_skip_bound_licenses_stop_under_a_skewed_supported_prior`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_hypothesis_set_prior_seeds_from_verbalized_weights`
  - `test_hypothesis_set_prior_stays_uniform_without_weights`
- [tests/test_evsi_fail_closed.py](../../../../../../tests/test_evsi_fail_closed.py) — direct import
  - `test_order_probe_candidates_is_status_first_then_discrimination_then_age`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_open_set_arm_survives_apply_attempt_into_the_probe_path`

## Modification guidance

- Change causal probe coherence policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_probe_coherence.py](../../../../../../src/learnloop/diagnosis/causal_probe_coherence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
