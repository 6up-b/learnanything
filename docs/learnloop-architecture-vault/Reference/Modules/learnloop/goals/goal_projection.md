---
title: "learnloop.goals.goal_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_projection.py"
source_paths:
  - "src/learnloop/goals/goal_projection.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_projection module"
  - "src/learnloop/goals/goal_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_projection` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Forward projection of facet recall against a goal's due date.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_projection.py](../../../../../../src/learnloop/goals/goal_projection.py) |
| Source lines | 904 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FacetProjection` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 107)
  - `ready(self) -> float` (line 149; public) — The Ready axis: predicted ability at the goal horizon (§9.6).
  - `at_risk(self) -> bool` (line 155; public) — Needs work for the goal: not attained OR not yet certified.
- `class GoalReport` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 162)
  - `on_track_count(self) -> int` (line 174; public)
  - `total(self) -> int` (line 178; public)
  - `certified_count(self) -> int` (line 182; public)
  - `examined_count(self) -> int` (line 186; public)
  - `at_risk_count(self) -> int` (line 190; public)
  - `attainment_fraction(self) -> float | None` (line 194; public) — Mean per-facet progress toward target (clamped ratio), the headline %.
  - `predicted_recall_mean(self) -> float | None` (line 204; public)
  - `ready_current_mean(self) -> float | None` (line 210; public)
  - `demonstrated_count(self) -> int` (line 216; public)
  - `decay_estimated_count(self) -> int` (line 220; public)
  - `held_flat_count(self) -> int` (line 224; public)
  - `attempts_remaining(self) -> int` (line 228; public)
  - `attempts_remaining_is_partial(self) -> bool` (line 236; public) — ``attempts_remaining`` is an under-count, not the whole job.
- `class FrontierEntry` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 253)
- `class GoalFrontier` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 259)
- `resolve_goal_scope(vault: LoadedVault, goal: Goal, repository: Repository) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 265) — ``lo_id -> set of canonical facet ids`` in the goal's scope.
- `goal_material_gaps(vault: LoadedVault, goal: Goal, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 306) — In-scope learning objects with no ACTIVE practice item to serve.
- `unserved_contract_facets(vault: LoadedVault) -> dict[str, frozenset[str]]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 433) — ``lo_id -> facets whose contract the instrument pool cannot close``.
- `project_lo_blueprint_readiness(vault: LoadedVault, learning_object_id: str, facet_states: list[FacetRecallState], mastery: MasteryState | None, *, blend_count: float) -> LoReadiness | None` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 657) — Blueprint expected-performance readiness for one LO (§9.2), or None.
- `goal_report(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None) -> GoalReport` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 734)
- `facet_projections_at(vault: LoadedVault, repository: Repository, goal: Goal, at: datetime, *, clock: Clock | None=None, include_demonstration: bool=False) -> list[FacetProjection]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 775) — Per-facet do-nothing projection to ``at`` (the horizon overridden).
- `projected_ready_mean_at(vault: LoadedVault, repository: Repository, goal: Goal, at: datetime, *, clock: Clock | None=None) -> tuple[float | None, int, int]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 806) — Do-nothing Ready mean at ``at`` using only facets with FSRS support.
- `build_goal_frontier(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, item_states: dict[str, PracticeItemState] | None=None, facet_states_by_lo: dict[str, list[FacetRecallState]] | None=None, mastery_states: dict[str, MasteryState] | None=None) -> GoalFrontier` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 844)

### Module constants

- `_ASSUMED_FRESH_DISCOUNT` ([src/learnloop/goals/goal_projection.py](../../../../../../src/learnloop/goals/goal_projection.py), line 85)
- `_UNSERVED_VERDICTS` ([src/learnloop/goals/goal_projection.py](../../../../../../src/learnloop/goals/goal_projection.py), line 101)

## Internal implementation anchors

- `_supporting_weight(vault: LoadedVault, item, facet_id: str) -> float` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 356) — The item's evidence weight for ``facet_id`` (0.0 when not a support).
- `_retention_ratio(vault: LoadedVault, learning_object_id: str, facet_id: str, *, now: datetime, horizon: datetime, item_states: dict[str, PracticeItemState], fsrs_weights: tuple[float, ...]) -> tuple[float, bool]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 369) — Evidence-weighted FSRS retention ratio (horizon vs now) for one facet.
- `_attempts_to_certify(facet_id: str, evidence_mass: float, mass_gain_by_facet: dict[str, list[float]], min_mass: float) -> int | None` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 413) — Invert the mass equation into a coarse fresh-attempt count (None = no items).
- `_outstanding_attempts(facet_id: str, evidence_mass: float, mass_gain_by_facet: dict[str, list[float]], min_mass: float, *, at_risk: bool, certification_reachable: bool) -> tuple[int | None, bool]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 461) — ``(attempts_to_certify, is_lower_bound)`` for one facet.
- `_lo_mass_gains(vault: LoadedVault, learning_object_id: str, item_states: dict[str, PracticeItemState]) -> dict[str, list[float]]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 499) — Per canonical facet id, the nominal mass gain of each active item covering it.
- `_facet_projections(vault: LoadedVault, repository: Repository, goal: Goal, *, now: datetime, horizon: datetime, item_states: dict[str, PracticeItemState], facet_states_by_lo: dict[str, list[FacetRecallState]], mastery_states: dict[str, MasteryState], fsrs_weights: tuple[float, ...], include_demonstration: bool=False, unserved_facets: Mapping[str, frozenset[str]] | None=None) -> list[FacetProjection]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 521)
- `_blueprint_readiness_by_lo(vault: LoadedVault, goal: Goal, repository: Repository, *, facet_states_by_lo: dict[str, list[FacetRecallState]], mastery_states: dict[str, MasteryState]) -> dict[str, LoReadiness]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 701)
- `_horizon(vault: LoadedVault, goal: Goal, now: datetime) -> tuple[datetime | None, datetime]` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 726)
- `_quota_floor_for_goal(goal: Goal, config, now: datetime) -> float` ([source](../../../../../../src/learnloop/goals/goal_projection.py), line 829)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `goal_report`, `resolve_goal_scope`; statically calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `goal_report`, `resolve_goal_scope`; statically calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `goal_report`, `resolve_goal_scope`; statically calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/goal_pace|learnloop.goals.goal_pace]] — imports `GoalReport`, `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `goal_report`, `projected_ready_mean_at`, `resolve_goal_scope`; statically calls `goal_report`, `projected_ready_mean_at`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `project_lo_blueprint_readiness`; statically calls `project_lo_blueprint_readiness`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `GoalReport`, `goal_report`; statically calls `goal_report`
- [[Reference/Modules/learnloop/scheduling/decay_pressure|learnloop.scheduling.decay_pressure]] — imports `facet_projections_at`; statically calls `facet_projections_at`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `facet_projections_at`, `goal_report`; statically calls `facet_projections_at`, `goal_report`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `facet_projections_at`, `goal_report`; statically calls `facet_projections_at`, `goal_report`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `build_goal_frontier`; statically calls `build_goal_frontier`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `goal_report`, `resolve_goal_scope`; statically calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `GoalReport`, `goal_material_gaps`, `goal_report`, `resolve_goal_scope`; statically calls `goal_material_gaps`, `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `resolve_goal_scope`; statically calls `resolve_goal_scope`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `FacetRecallState`, `MasteryState`, `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `facet_demonstration`; calls `facet_demonstration`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `LoReadiness`, `project_lo_readiness`; calls `project_lo_readiness`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `ReachabilityVerdict`, `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `facet_state_label`, `scope_facets`; calls `facet_state_label`, `scope_facets`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_states_by_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`; calls `facet_states_by_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`; calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/measurement_state|learnloop.learner.measurement_state]] — imports `UNKNOWN`, `classify_measurement_state`; calls `classify_measurement_state`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `expected_facet_mass_gain`; calls `expected_facet_mass_gain`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `predicted_facet_recall`; calls `predicted_facet_recall`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `math`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]], [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]], [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]], [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] and 15 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_decay_projection.py](../../../../../../tests/test_goal_decay_projection.py) — direct import
  - `test_do_nothing_projection_is_monotone_non_increasing_for_decay_facets`
  - `test_goal_with_zero_decay_estimated_facets_reports_suppressible_coverage`
  - `test_held_flat_facets_are_excluded_from_the_curve_but_counted`
  - `test_linear_algebra_fixture_golden_projection`
- [tests/test_goal_pace.py](../../../../../../tests/test_goal_pace.py) — direct import
  - `test_compute_goal_pace_open_ended`
  - `test_compute_goal_pace_with_due_date`
  - `test_pace_as_dict_shape`
  - `test_unknowable_remaining_surfaces_as_none`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_attainment_aggregates`
  - `test_attempts_to_certify_inversion_edge_cases`
  - `test_attempts_to_certify_inverts_the_mass_equation`
  - `test_decayed_certified_facet_reports_a_floor_not_zero`
  - `test_explicit_facet_scope_adds_facet_without_listing_concept`
  - `test_fully_reachable_contract_keeps_the_legacy_estimate`
  - `test_high_mastery_low_mass_is_on_track_but_uncertified_and_at_risk`
  - `test_known_gap_facet_is_never_on_track`
  - `test_legacy_lo_without_a_contract_is_untouched`
  - `test_legacy_v1_goal_converts_and_scope_resolves`
  - `test_mismatch_above_is_not_treated_as_unreachable`
  - `test_one_uncloseable_rung_abstains_for_the_whole_facet`
  - `test_projection_is_monotonically_non_increasing_with_horizon`
  - `test_quota_floor_interpolates_within_ramp_window`
  - `test_quota_floor_open_ended_goal_uses_floor_min`
  - `test_quota_floor_past_due_uses_floor_max`
  - `test_quota_floor_zero_when_no_active_frontier`
  - `test_solid_facet_above_target_no_decay_info_is_on_track`
  - `test_solid_facet_decays_below_target_lands_on_frontier`
  - `test_unexamined_facet_is_on_frontier_and_not_on_track`
  - `test_unreachable_contract_cell_makes_attempts_unknowable`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_a_concept_with_no_learning_objects_still_resolves_to_nothing`
  - `test_an_authored_learning_object_is_not_a_gap`
  - `test_fixture_vault_goal_over_unauthored_concepts_resolves`
  - `test_goal_scope_resolves_over_unauthored_material`
  - `test_material_gaps_report_the_fillable_learning_object`
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_goal_projection_reads_canonical_state`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
  - `test_blueprint_readiness_wired_into_goal_report`
  - `test_goal_report_exposes_dual_axis_fields`
- [tests/test_measurement_state_labels.py](../../../../../../tests/test_measurement_state_labels.py) — direct import
  - `test_claimed_label_when_only_a_learner_claim_covers_the_cell`
  - `test_label_does_not_move_a_threshold_a_number_or_a_certification`
  - `test_measured_label_on_a_facet_with_evidence_over_the_gate`
  - `test_pooled_prediction_that_rendered_unlabelled_now_carries_inferred`
  - `test_sub_threshold_direct_mass_is_inferred_not_measured`
  - `test_unknown_label_when_there_is_nothing_at_all`
- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_blueprint_weight_by_facet_sums_referencing_blueprints`

## Modification guidance

- Change goal projection policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_projection.py](../../../../../../src/learnloop/goals/goal_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
