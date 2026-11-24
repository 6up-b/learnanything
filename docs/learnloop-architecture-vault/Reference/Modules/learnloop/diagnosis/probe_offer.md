---
title: "learnloop.diagnosis.probe_offer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_offer.py"
source_paths:
  - "src/learnloop/diagnosis/probe_offer.py"
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
  - "learnloop.diagnosis.probe_offer module"
  - "src/learnloop/diagnosis/probe_offer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_offer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_offer` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Record learner actions on a causal quick-check offer.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_offer.py](../../../../../../src/learnloop/diagnosis/probe_offer.py) |
| Source lines | 481 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 35) — Result of accepting the quick check.
  - `as_dict(self) -> dict[str, Any]` (line 48; public)
- `accept_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, candidate_id: str | None=None, followup_workflow_id: str | None=None, router_decision_id: str | None=None) -> ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 86) — "Take the quick check" (:func:`_accept_probe_offer`), and its ``probe_offer`` decision record (refactor B7).
- `router_disposition(repository: Repository, factor_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 122) — The router's decision on the factor's learner-lane probe as the offer reads it: ``router_state`` (``pending`` with no decision, ``selected`` or ``not_selected``) and ``router_decision_id``.
- `accept_routed_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> tuple[ProbeOffer, dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 143) — "Take the quick check" at the probe router's tag: only the router's selection of this factor's probe is accepted, and only its own candidate.
- `defer_probe_offer(repository: Repository, *, factor_id: str, learning_object_id: str | None=None, session_id: str | None=None, preference: str='decline', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 429) — "Not now": persist the decline so the next attempt does not re-offer.
- `request_teaching_now(vault: LoadedVault, repository: Repository, *, misconception_id: str, factor_id: str, session_id: str | None=None, clock: Clock | None=None) -> RepairStatus` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 452) — "Teach me now": an explicit learner authorisation to skip the check.

### Module constants

- `ROUTER_DECISION_REQUIRED` ([src/learnloop/diagnosis/probe_offer.py](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 119)

## Internal implementation anchors

- `_answer_shown(repository: Repository, practice_item_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 62) — Was the item's answer shown, so no probe of it may be offered (UX Phase 4 round 7; the one eligibility decision's question)?
- `class _OfferRefusedAtCommit(Exception)` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 77) — The commit refused the probe after the episode was retargeted: rolls the retarget back with it (UX Phase 4 round 7).
- `_accept_probe_offer(vault: LoadedVault, repository: Repository, *, factor_id: str, decision_receipt_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, candidate_id: str | None=None, followup_workflow_id: str | None=None, router_decision_id: str | None=None) -> ProbeOffer` ([source](../../../../../../src/learnloop/diagnosis/probe_offer.py), line 180) — "Take the quick check": enter a factor-aware episode and pin the probe.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `accept_probe_offer`; statically calls `accept_probe_offer`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `accept_probe_offer`, `accept_routed_probe_offer`, `defer_probe_offer`, `request_teaching_now`; statically calls `accept_probe_offer`, `accept_routed_probe_offer`, `defer_probe_offer`, `request_teaching_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`
- [[Reference/Modules/learnloop/diagnosis/causal_discrimination|learnloop.diagnosis.causal_discrimination]] — imports `pinned_causal_probe`; calls `pinned_causal_probe`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `RepairStatus`, `causal_repair_status`; calls `causal_repair_status`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `candidate_has_current_blind_input_contract`, `order_probe_candidates`; calls `candidate_has_current_blind_input_contract`, `order_probe_candidates`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`
- [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] — imports `record_probe_offer`; calls `record_probe_offer`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`; calls `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `EPISODE_CONFLICT_REASON`, `_causal_origin`, `episode_conflict_reason`, `record_learner_preference`; calls `_causal_origin`, `episode_conflict_reason`, `record_learner_preference`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `RoutineDisplayCovered`, `commit_presentation`, `routine_display_covers_item`; calls `commit_presentation`, `routine_display_covers_item`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `PROBE_REF`, `automatic_probe_decision`, `learner_probe_decision`; calls `automatic_probe_decision`, `learner_probe_decision`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]], [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_router_decided_pin_names_its_router_decision_not_a_causal_receipt`
  - `test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles`
  - `test_not_now_persists_and_the_next_call_does_not_reoffer`
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
  - `test_teach_me_now_starts_the_repair_under_recorded_authorisation`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_closed_probes_candidate_leaves_the_factors_active_set`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_hard_refusal_needs_no_model_and_spends_nothing`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_the_causal_quick_check_stops_the_episode_being_ignored`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_b_an_existing_pin_is_reused_and_acceptance_asks_no_gate`
  - `test_b_not_now_withdraws_the_offer_and_the_divergence_stays`
  - `test_c_a_manual_teach_me_now_starts_the_repair_without_the_probe`
  - `test_d_a_not_now_while_the_question_is_written_refuses_after_authoring`
  - `test_d_a_retry_keeps_the_first_draw_and_asks_only_the_hard_refusals_again`
  - `test_d_not_now_refuses_before_the_router_and_no_question_is_written`
  - `test_d_the_refusals_ask_preference_then_machine_checks_then_the_shared_episode_check`
- [tests/test_probe_router_decision_integrity.py](../../../../../../tests/test_probe_router_decision_integrity.py) — direct import
- [tests/test_probe_router_learner_lane.py](../../../../../../tests/test_probe_router_learner_lane.py) — direct import
  - `test_an_offer_request_without_the_routers_selection_is_a_typed_refusal`
  - `test_teach_me_now_starts_the_repair_without_the_probe`
  - `test_the_selected_probe_is_accepted_once_and_its_pin_names_the_router_decision`
- [tests/test_probe_router_replay.py](../../../../../../tests/test_probe_router_replay.py) — direct import
- [tests/test_refusal_records.py](../../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_hard_refusal_and_no_plan_each_leave_the_gates_record`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged`

## Modification guidance

- Change probe offer policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_offer.py](../../../../../../src/learnloop/diagnosis/probe_offer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
