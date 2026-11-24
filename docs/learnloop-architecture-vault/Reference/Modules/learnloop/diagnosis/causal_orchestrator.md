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

`learnloop.diagnosis.causal_orchestrator` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 causal repair decisions (spec_causal_attribution_v1 §6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) |
| Source lines | 1468 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 251) — Resolved orchestrator knobs plus their provenance.
  - `__getitem__(self, key: str) -> float` (line 259; internal)
  - `manifest(self) -> dict[str, Any]` (line 262; public)
- `resolve_orchestrator_parameters(repository: Repository | None) -> OrchestratorParameters` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 272)
- `class RepairAction` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 289)
  - `as_dict(self) -> dict[str, str]` (line 293; public)
- `class RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 298) — The typed union returned by :func:`causal_repair_status` (§6).
  - `__post_init__(self) -> None` (line 346; internal)
  - `repair_permitted(self) -> bool` (line 350; public) — True when the causal state allows the targeted repair to run.
  - `as_dict(self) -> dict[str, Any]` (line 360; public)
- `causal_repair_status(vault: LoadedVault | None, repository: Repository, *, misconception_id: str, session_id: str | None=None, session_budget_minutes: float | None=None, start_repair: bool=True, clock: Clock | None=None, record_receipt: bool=True, factor_id: str | None=None, attempt_id: str | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 472) — Resolve — and where safe, START — the repair for one cause.
- `repair_classes_for_factor(repository: Repository, factor_id: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 674) — Each hypothesis's repair class on the factor's classified cause set, as the repair status reads it (empty for a factor that is not open or names no repair class).
- `gather_probe_reads(repository: Repository, *, factor_id: str, attempt_id: str | None, learning_object_id: str | None, session_id: str | None, targeting: Any, repair_class_by_hypothesis: Mapping[str, str], parameters: OrchestratorParameters) -> ProbeProposalReads` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 686) — What the repair status reads about the factor's possible probe, after its mapping checks are settled.
- `candidate_unservable(vault: Any, repository: Repository, candidate: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1287) — Why the quick check on ``candidate`` could not be administered now, or None: the executability read the router draws on and the status reads back.

### Module constants

- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 162)
- `REPAIR_STATUSES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 164)
- `EVSI_PROVENANCE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 181)
- `LOSS_TABLE_REGIME_P2_PROXY` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 192)
- `NEEDS_DISAMBIGUATION_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 198)
- `DEFERRED_OFFER_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 202)
- `DEFERRED_MACHINE_CHECKS_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 206)
- `SAFE_COMMON_REPAIR_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 210)
- `BLOCKED_PENDING_REVIEW_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 214)
- `STARTED_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 218)
- `ROUTER_PENDING_MESSAGE` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 220)
- `TAKE_QUICK_CHECK` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 224)
- `TEACH_ME_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 225)
- `NOT_NOW` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 226)
- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 232)
- `_ORCHESTRATOR_POLICY_BOUNDS` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 243)
- `_UNCOMMITTED_REPAIR_STATES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 424)
- `ROUTER_DECIDES` ([src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1284)

### Explicit exports

`__all__` declares:

- `CAUSAL_ORCHESTRATOR_POLICY_DEFAULTS`
- `CAUSAL_ORCHESTRATOR_POLICY_SCOPE`
- `ROUTER_DECIDES`
- `candidate_unservable`
- `EVSI_PROVENANCE`
- `NEEDS_DISAMBIGUATION_MESSAGE`
- `REPAIR_STATUSES`
- `RepairAction`
- `RepairStatus`
- `causal_repair_status`
- `gather_probe_reads`
- `repair_classes_for_factor`
- `resolve_orchestrator_parameters`

## Internal implementation anchors

- `_with_reveal_spend(repository: Repository, status: RepairStatus) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 393) — Stamp the episode's reveal spend and the budget it is measured against.
- `_episode_for(repository: Repository, *, case_kind: str, case_ref: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 427) — The repair episode for this case — reused, not re-minted.
- `_actions(status: str, *, offered: bool) -> tuple[RepairAction, ...]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 458)
- `_requested_factor(factors: Sequence[Mapping[str, Any]], *, factor_id: str | None, attempt_id: str | None) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 651) — The open factor the caller shows.
- `_status_for_factor(repository: Repository, *, misconception_id: str, factor: Mapping[str, Any], session_id: str | None, session_budget_minutes: float | None, start_repair: bool, clock: Clock | None, vault: LoadedVault | None=None, record_receipt: bool=True) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 847) — Map a factor to repair status after machine checks and probe valuation.
- `_routed(repository: Repository, *, vault: Any, finish: Any, reads: ProbeProposalReads, base_inputs: Mapping[str, Any], session_budget_minutes: float | None, start_repair: bool, proposal: Mapping[str, Any]) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py), line 1307) — The probe router's tag: the facts settle what they settle, and whether the quick check is offered is the router's decision, read back here (``plan_log.learner_probe_decision``), never formed here.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `ROUTER_DECIDES`, `causal_repair_status`; statically calls `causal_repair_status`
- [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]] — imports `repair_classes_for_factor`, `resolve_orchestrator_parameters`; statically calls `repair_classes_for_factor`, `resolve_orchestrator_parameters`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `SAFE_COMMON_REPAIR_MESSAGE`, `causal_repair_status`; statically calls `causal_repair_status`
- [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]] — imports `RepairStatus`, `causal_repair_status`; statically calls `causal_repair_status`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `causal_repair_status`; statically calls `causal_repair_status`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `causal_repair_status`; statically calls `causal_repair_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `probe_router_on`; calls `probe_router_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `ProbeDecision`, `candidate_has_current_blind_input_contract`, `decide_probe`, `order_probe_candidates`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`; calls `candidate_has_current_blind_input_contract`, `decide_probe`, `order_probe_candidates`, `repair_class_need_for_factor`, `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`; calls `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`
- [[Reference/Modules/learnloop/diagnosis/learner_probe_proposal|learnloop.diagnosis.learner_probe_proposal]] — imports `Proposal`; calls `Proposal`
- [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]] — imports `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`; calls `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `module`; calls `administered_surface_exclusions`, `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/probe_facts|learnloop.diagnosis.probe_facts]] — imports `ProbeProposalReads`, `REFUSING_PREFERENCES`, `channel_status`, `settled_by_repair_classes`; calls `ProbeProposalReads`, `channel_status`, `settled_by_repair_classes`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `EPISODE_CONFLICT_MESSAGE`, `learner_preference`, `probe_episode_conflict`; calls `learner_preference`, `probe_episode_conflict`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `CAUSE_SET_INCOMPLETE_MAPPING`, `MAPPING_BASIS_LEGACY_FACET`, `classify_cause_set`; calls `classify_cause_set`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `EPISODE_REVEAL_BUDGET`, `episode_reveal_spend`; calls `episode_reveal_spend`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_bounded_knobs`; calls `resolve_bounded_knobs`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `INSERT_REF`, `PROBE_REF`, `automatic_probe_decision`, `learner_probe_decision`; calls `automatic_probe_decision`, `learner_probe_decision`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/probe_router_owned_helpers.py](../../../../../../tests/probe_router_owned_helpers.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_common_repair_cover_serves_the_repair_and_records_the_skip`
  - `test_a_stale_backfill_check_cannot_wedge_a_now_mapped_factor`
  - `test_a_status_read_records_the_decision_without_minting_an_episode`
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_divergent_causes_without_a_reviewed_instrument_block_pending_review`
  - `test_evsi_inputs_are_computed_and_carry_their_provenance`
  - `test_inseparable_bundles_yield_a_computed_zero_information_gain`
  - `test_not_now_persists_and_the_next_call_does_not_reoffer`
  - `test_reviewed_active_candidate_produces_the_disambiguation_offer`
  - `test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_self_report_keeps_the_repair_mapping_and_returns_a_live_id`
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_causal_probe_decision_writes_no_retired_shadow_receipts`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_durable_case_records_receipt_readable_by_feedback_attach`
  - `test_failed_diagnostic_attempt_opens_the_repair_lane`
  - `test_learner_derived_hypothesis_defaults_learner_state_and_offer_survives`
  - `test_mapped_factorless_diagnosis_case_still_starts`
  - `test_unmapped_diagnosis_case_defers_machine_checks`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
- [tests/test_probe_proposal_reads.py](../../../../../../tests/test_probe_proposal_reads.py) — direct import
  - `test_gathering_writes_nothing_and_the_verdict_on_its_facts_is_the_statuss`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
- [tests/test_probe_router_decision_integrity.py](../../../../../../tests/test_probe_router_decision_integrity.py) — direct import
  - `test_r6_a_machine_check_queued_after_the_selection_refuses_the_stale_click`
- [tests/test_probe_router_learner_lane.py](../../../../../../tests/test_probe_router_learner_lane.py) — direct import
  - `test_a_status_read_decides_once_and_a_reread_draws_nothing_and_writes_no_receipt`
  - `test_one_repair_for_both_causes_settles_the_status_with_no_probe_to_decide`
- [tests/test_probe_router_replay.py](../../../../../../tests/test_probe_router_replay.py) — direct import
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_repair_status_reports_episode_reveal_spend_against_the_budget`

## Modification guidance

- Change causal orchestrator policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_orchestrator.py](../../../../../../src/learnloop/diagnosis/causal_orchestrator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
