---
title: "learnloop.curriculum.golden_path_run"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_run.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_run.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.golden_path_run module"
  - "src/learnloop/curriculum/golden_path_run.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_run`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_run` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 step 3 -- the golden-path run state machine + resume (spec_p2_narrow_golden_path §4.1, §4.2, §4.3, §12.6; migration 082).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py) |
| Source lines | 368 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class IllegalTransition(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 100) — A requested transition is not in the run's feasible set (§4.1 adjacency).
  - `__init__(self, run_id: str, *, from_state: str, to_state: str)` (line 103; internal)
- `class StaleRunHead(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 110) — The expected head event no longer matches the run's head (§4.3 optimistic fence).
  - `__init__(self, run_id: str, *, expected: str | None, actual: str | None)` (line 113; internal)
- `class NextAction` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 121)
  - `as_dict(self) -> dict[str, Any]` (line 126; public)
- `class RunState` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 131) — A projection of the append-only event log (§4.1).
  - `as_dict(self) -> dict[str, Any]` (line 145; public)
- `class AdvanceResult` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 150)
  - `as_dict(self) -> dict[str, Any]` (line 158; public)
- `project_run(repository: Repository, run_id: str) -> RunState` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 174) — Fold the event log into the current run state (§4.1).
- `advance(repository: Repository, run_id: str, *, to_state: str, reason: str, idempotency_key: str, expected_head_event_id: str | None=None, evidence_ids: Sequence[str] | None=None, selected_activity: Mapping[str, Any] | None=None, feasible_alternatives: Sequence[str] | None=None, predecessor_milestone: str | None=None, successor_milestone: str | None=None, policy_calibration: Mapping[str, Any] | None=None, burden: Mapping[str, Any] | None=None, clock: Clock | None=None) -> AdvanceResult` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 224) — Append exactly one transition (§4.1).
- `advance_canonical(repository: Repository, run_id: str, *, idempotency_key: str, clock: Clock | None=None, **extra: Any) -> AdvanceResult` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 344) — Convenience: advance along the canonical happy-path successor (§4.2).

### Module constants

- `STATES` ([src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 29)
- `TERMINAL_STATES` ([src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 38)
- `INSTRUCTION_STATES` ([src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 45)
- `ALLOWED_TRANSITIONS` ([src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 54)
- `_CANONICAL_NEXT` ([src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 82)

## Internal implementation anchors

- `_next_action_for(current_state: str, mode: str) -> NextAction` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 162)
- `_close_diagnostic_segment_on_instruction(repository: Repository, run_id: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 312) — Close the run's pinned baseline episode + snapshot its boundary view when instruction begins (invariant 7 / §5.3 / §8.4).
- `_existing_event(repository: Repository, run_id: str, idempotency_key: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/golden_path_run.py), line 364)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `module`; statically calls `advance`, `project_run`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; statically calls `advance`, `project_run`
- [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]] — imports `module`; statically calls `advance`, `project_run`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `module`; calls `snapshot_baseline_boundary`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `module`; calls `close_diagnostic_segment`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]], [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]], [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
- [tests/test_failure_triage.py](../../../../../../tests/test_failure_triage.py) — direct import
  - `test_concentrated_signature_distribution_stays_tier_one`
  - `test_decide_commits_the_aid_and_routes_the_run`
  - `test_diffuse_signature_distribution_downgrades_to_tier_two`
  - `test_dont_know_on_never_exposed_routes_unfamiliar_decisively`
  - `test_high_confidence_signature_takes_intended_route`
  - `test_low_confidence_yields_decision_aid_that_never_auto_commits`
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_triage_records_tier_one_basis_on_the_result_and_the_event`
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_accept_records_draft_intent_without_successor`
  - `test_burned_surface_refuses_and_run_degrades`
  - `test_decline_logs_decision_and_holds_milestone`
  - `test_harness_activation_activates_exactly_one_edge`
  - `test_kill_resume_across_assessment_boundary`
  - `test_milestone_event_only_and_one_suggest_next_never_activates`
  - `test_practice_only_run_mints_no_certification`
  - `test_restoration_after_measurement_cannot_change_the_observation`
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — direct import
  - `test_fixture_bootstrap_confirms_a_certifying_run`
- [tests/test_golden_path_run.py](../../../../../../tests/test_golden_path_run.py) — direct import
  - `test_confirmation_seeds_ready_state_and_run_started_event`
  - `test_every_transition_logs_current_goal_contract_head`
  - `test_full_canonical_walk_visits_every_stage_in_order`
  - `test_idempotent_replay_yields_exactly_one_transition`
  - `test_illegal_transition_refused`
  - `test_kill_resume_rebuilds_state_and_next_action_from_events`
  - `test_never_reopens_a_closed_diagnostic_segment`
  - `test_optimistic_head_fence_rejects_stale_expected_head`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
  - `test_fault_injection_diagnostic_baseline_boundary_yields_exactly_one`
  - `test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
  - `test_diagnostic_exposure_consumes_cold_eligibility`

## Modification guidance

- Change golden path run policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_run.py](../../../../../../src/learnloop/curriculum/golden_path_run.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
