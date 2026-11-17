---
title: "learnloop.diagnosis.causal_orchestrator"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_orchestrator.py"
source_paths:
  - "src/learnloop/diagnosis/causal_orchestrator.py"
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
  - "learnloop.diagnosis.causal_orchestrator module"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_orchestrator`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_orchestrator` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 causal repair orchestration (spec_causal_attribution_v1 §6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) |
| Source lines | 2218 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 283) — Resolved orchestrator knobs plus their provenance.
  - `__getitem__(self, key: str) -> float` (line 291; internal)
  - `manifest(self) -> dict[str, Any]` (line 294; public)
- `resolve_orchestrator_parameters(repository: Repository | None) -> OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 304)
- `class RepairAction` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 342)
  - `as_dict(self) -> dict[str, str]` (line 346; public)
- `class RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 351) — The typed union returned by :func:`causal_repair_status` (§6).
  - `__post_init__(self) -> None` (line 388; internal)
  - `repair_permitted(self) -> bool` (line 392; public) — True when the causal state allows the targeted repair to run.
  - `as_dict(self) -> dict[str, Any]` (line 402; public)
- `causal_repair_status(vault: LoadedVault | None, repository: Repository, *, misconception_id: str, session_id: str | None=None, session_budget_minutes: float | None=None, start_repair: bool=True, clock: Clock | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 512) — Resolve — and where safe, START — the repair for one cause.
- `class ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1175) — Result of accepting the quick check.
  - `as_dict(self) -> dict[str, Any]` (line 1188; public)
- `accept_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, candidate_id: str | None=None, followup_workflow_id: str | None=None, router_decision_id: str | None=None) -> ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1226) — "Take the quick check" (:func:`_accept_probe_offer`), and its ``probe_offer`` decision record (refactor B7).
- `defer_probe_offer(repository: Repository, *, factor_id: str, learning_object_id: str | None=None, session_id: str | None=None, preference: str='decline', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1507) — "Not now": persist the decline so the next attempt does not re-offer.
- `request_teaching_now(vault: LoadedVault, repository: Repository, *, misconception_id: str, factor_id: str, session_id: str | None=None, clock: Clock | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1530) — "Teach me now": an explicit learner authorisation to skip the check.
- `pinned_causal_probe(repository: Repository, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1562)
- `classify_probe_response(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1573) — Classify an administered causal probe against its PINNED bundles.
- `class DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1633) — One classification, judged: what it may close and what it may not.
  - `outcome(self) -> str` (line 1645; public)
  - `observation_id(self) -> str | None` (line 1649; public)
  - `as_dict(self) -> dict[str, Any]` (line 1652; public)
- `record_learner_embedded_prediction(repository: Repository, *, factor_id: str, prediction: str, question_event_id: str, attempt_id: str | None=None, practice_item_id: str | None=None, remediation_episode_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1796) — Record a falsifiable expectation the learner's OWN question asserted.
- `record_probe_classification(repository: Repository, *, presentation_id: str, observed_features: Mapping[str, Any], feature_source: str, probe_attempt_id: str | None=None, clock: Clock | None=None) -> DiscriminatingObservation` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1875) — Classify an administered probe AND act on the verdict (§6, §7).
- `deterministic_probe_features(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2067) — The graded probe attempt's own criterion outcomes, as a feature vector.
- `auto_classify_pinned_probe(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> DiscriminatingObservation | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 2124) — Close the loop automatically when a probe answer can be read by machine.

### Module constants

- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 176)
- `REPAIR_STATUSES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 178)
- `EVSI_PROVENANCE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 195)
- `LOSS_TABLE_REGIME_P2_PROXY` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 206)
- `BLIND_PROBE_BASIS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 213)
- `OBSERVATION_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 219)
- `VALIDATOR_OWNED_FEATURE_SOURCES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 226)
- `DETERMINISTIC_FEATURE_PREFIX` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 229)
- `NEEDS_DISAMBIGUATION_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 234)
- `DEFERRED_OFFER_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 238)
- `DEFERRED_MACHINE_CHECKS_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 242)
- `SAFE_COMMON_REPAIR_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 246)
- `BLOCKED_PENDING_REVIEW_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 250)
- `STARTED_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 254)
- `TAKE_QUICK_CHECK` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 256)
- `TEACH_ME_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 257)
- `NOT_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 258)
- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 264)
- `_ORCHESTRATOR_POLICY_BOUNDS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 275)
- `_UNCOMMITTED_REPAIR_STATES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 464)
- `_EMBEDDED_PREDICTION_OUTCOME` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1793)

### Explicit exports

`__all__` declares:

- `BLIND_PROBE_BASIS`
- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS`
- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE`
- `DETERMINISTIC_FEATURE_PREFIX`
- `DISCRIMINATING_OUTCOMES`
- `EVSI_PROVENANCE`
- `OBSERVATION_FEATURE_SOURCES`
- `VALIDATOR_OWNED_FEATURE_SOURCES`
- `DiscriminatingObservation`
- `NEEDS_DISAMBIGUATION_MESSAGE`
- `ProbeOffer`
- `REPAIR_STATUSES`
- `RepairAction`
- `RepairStatus`
- `accept_probe_offer`
- `auto_classify_pinned_probe`
- `causal_repair_status`
- `classify_probe_response`
- `deterministic_probe_features`
- `defer_probe_offer`
- `record_probe_classification`
- `pinned_causal_probe`
- `request_teaching_now`
- `resolve_orchestrator_parameters`

## Internal implementation anchors

- `_with_reveal_spend(repository: Repository, status: RepairStatus) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 433) — Stamp the episode's reveal spend and the budget it is measured against.
- `_episode_for(repository: Repository, *, case_kind: str, case_ref: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 467) — The repair episode for this case — reused, not re-minted.
- `_actions(status: str, *, offered: bool) -> tuple[RepairAction, ...]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 498)
- `_status_for_factor(repository: Repository, *, misconception_id: str, factor: Mapping[str, Any], session_id: str | None, session_budget_minutes: float | None, start_repair: bool, clock: Clock | None, vault: LoadedVault | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 684)
- `_answer_shown(repository: Repository, practice_item_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1202) — Was the item's answer shown, so no probe of it may be offered (UX Phase 4 round 7; the one eligibility decision's question)?
- `class _OfferRefusedAtCommit(Exception)` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1217) — The commit refused the probe after the episode was retargeted: rolls the retarget back with it (UX Phase 4 round 7).
- `_accept_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, candidate_id: str | None=None, followup_workflow_id: str | None=None, router_decision_id: str | None=None) -> ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1258) — "Take the quick check": enter a factor-aware episode and pin the probe.
- `_measured_hypotheses(repository: Repository, classification: Mapping[str, Any], observed_features: Mapping[str, Any]) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1665) — Which of the locked set's concrete hypotheses the observation MEASURED.
- `_observation_support_scores(classification: Mapping[str, Any], measured: set[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1721) — Support mass a discriminating observation licenses, and nothing more.
- `_probe_production_admissibility(repository: Repository, *, probe_attempt_id: str | None) -> 'ProductionAdmissibility | None'` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1748) — Was the probe answer produced before anything was revealed to it?

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `SAFE_COMMON_REPAIR_MESSAGE`, `auto_classify_pinned_probe`, `causal_repair_status`; statically calls `auto_classify_pinned_probe`, `causal_repair_status`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `causal_repair_status`; statically calls `causal_repair_status`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `accept_probe_offer`; statically calls `accept_probe_offer`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `record_learner_embedded_prediction`; statically calls `record_learner_embedded_prediction`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`; statically calls `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `ProductionAdmissibility`, `production_admissibility`; calls `ProductionAdmissibility`, `production_admissibility`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `DISCRIMINATING_OUTCOMES`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `OBSERVATION_CHANNEL_BLIND_PROBE`, `OBSERVATION_CHANNEL_LEARNER_QUESTION`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `SUPPORT_BASIS_AUTHORITY`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `ProbeDecision`, `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`; calls `bundle_feature_row_report`, `candidate_has_current_blind_input_contract`, `classify_against_blind_bundles`, `decide_probe`, `order_probe_candidates`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`; calls `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `record_probe_offer`; calls `record_probe_offer`
- [[Reference/Modules/learnloop/diagnosis/content_ids|learnloop.diagnosis.content_ids]] — imports `content_id`; calls `content_id`
- [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]] — imports `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`; calls `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`; calls `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `EPISODE_CONFLICT_MESSAGE`, `EPISODE_CONFLICT_REASON`, `_causal_origin`, `episode_conflict_reason`, `learner_preference`, `probe_episode_conflict`, `record_learner_preference`; calls `_causal_origin`, `episode_conflict_reason`, `learner_preference`, `probe_episode_conflict`, `record_learner_preference`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `RoutineDisplayCovered`, `commit_presentation`, `routine_display_covers_item`; calls `commit_presentation`, `routine_display_covers_item`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `CAUSE_SET_INCOMPLETE_MAPPING`, `MAPPING_BASIS_LEGACY_FACET`, `classify_cause_set`; calls `classify_cause_set`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `EPISODE_REVEAL_BUDGET`, `episode_reveal_spend`; calls `episode_reveal_spend`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `probe_answer_exposed`; calls `probe_answer_exposed`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/diagnosis_identity_helpers.py](../../../../../../tests/diagnosis_identity_helpers.py) — direct import
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_common_repair_cover_serves_the_repair_and_records_the_skip`
  - `test_a_router_decided_pin_names_its_router_decision_not_a_causal_receipt`
  - `test_a_stale_backfill_check_cannot_wedge_a_now_mapped_factor`
  - `test_a_status_read_records_the_decision_without_minting_an_episode`
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_divergent_causes_without_a_reviewed_instrument_block_pending_review`
  - `test_evsi_inputs_are_computed_and_carry_their_provenance`
  - `test_inseparable_bundles_yield_a_computed_zero_information_gain`
  - `test_not_now_persists_and_the_next_call_does_not_reoffer`
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
  - `test_reviewed_active_candidate_produces_the_disambiguation_offer`
  - `test_teach_me_now_starts_the_repair_under_recorded_authorisation`
  - `test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_probe_answered_after_a_reveal_is_not_independent_evidence`
  - `test_a_probe_answered_with_no_reveal_is_marked_independent`
  - `test_a_verdict_over_unmeasured_features_is_inadmissible`
  - `test_an_instrument_that_did_not_discriminate_resolves_nothing`
  - `test_auto_classification_declines_a_sensor_it_cannot_read`
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_no_bundle_matched_supports_the_open_set_but_closes_nothing`
  - `test_self_report_keeps_the_repair_mapping_and_returns_a_live_id`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_causal_probe_decision_writes_no_retired_shadow_receipts`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_durable_case_records_receipt_readable_by_feedback_attach`
  - `test_failed_diagnostic_attempt_opens_the_repair_lane`
  - `test_learner_derived_hypothesis_defaults_learner_state_and_offer_survives`
  - `test_mapped_factorless_diagnosis_case_still_starts`
  - `test_unmapped_diagnosis_case_defers_machine_checks`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_an_embedded_prediction_stays_admissible_after_a_reveal`
  - `test_embedded_prediction_is_idempotent_per_question`
  - `test_question_join_never_fails_the_learners_answer`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_closed_probes_candidate_leaves_the_factors_active_set`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f3_the_report_and_the_orchestrator_share_one_contract`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_miss_with_two_rivals_generates_one_pinned_probe`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_hard_refusal_needs_no_model_and_spends_nothing`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
  - `test_a_pinned_probe_declines_to_classify_an_unassessed_criterion`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_the_causal_quick_check_stops_the_episode_being_ignored`
- [tests/test_refusal_records.py](../../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_hard_refusal_and_no_plan_each_leave_the_gates_record`
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_repair_status_reports_episode_reveal_spend_against_the_budget`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged`

## Modification guidance

- Change causal orchestrator policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
