---
title: "learnloop.learner.facet_evidence_timeline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/facet_evidence_timeline.py"
source_paths:
  - "src/learnloop/learner/facet_evidence_timeline.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.learner.facet_evidence_timeline module"
  - "src/learnloop/learner/facet_evidence_timeline.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.facet_evidence_timeline`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.facet_evidence_timeline` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Facet evidence timeline — the Demonstrated curve (KM §9.6 phase 1, §16).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/facet_evidence_timeline.py](../../../../../../src/learnloop/learner/facet_evidence_timeline.py) |
| Source lines | 1266 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ObservationDerivation` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 74) — Per-observation §5.1 receipt line for one (facet, capability) cell.
  - `as_dict(self) -> dict[str, object]` (line 88; public)
- `class ObservationEvent` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 99) — One grading epoch of one attempt, as it bears on a single facet.
  - `raw_positive(self) -> float` (line 129; public)
- `class TimelinePoint` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 134)
  - `as_dict(self) -> dict[str, object]` (line 166; public)
- `class FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 183) — Bulk-loaded immutable inputs for one evidence-ledger replay.
- `load_facet_timeline_snapshot(repository: Repository) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 214) — Load the complete timeline ledger with a bounded number of DB reads.
- `snapshot_as_of(snapshot: FacetTimelineSnapshot, cutoff: str, *, vault: LoadedVault | None=None) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 249) — The grading ledger as it stood at ``cutoff`` (RW6a review round 2 F1).
- `p0_evidence_mass_by_attempt(vault: LoadedVault, repository: Repository) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 375) — Per-attempt mvp-0.8 evidence mass, byte-matched to the projection.
- `vault_timeline_snapshot(vault: LoadedVault, repository: Repository) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 433) — The ledger snapshot :func:`facet_evidence_timelines` would load, P0 masses attached, so a caller replaying it several times (as of several moments) loads it once.
- `fold_demonstrated_timeline(events: list[ObservationEvent], *, repeat_surface_discount: float=DEFAULT_REPEAT_SURFACE_DISCOUNT, max_embedded_credit_share: float=1.0) -> list[TimelinePoint]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 441) — Fold ordered observation events into the Demonstrated curve (pure).
- `facet_evidence_timelines(vault: LoadedVault, repository: Repository, facet_ids: Iterable[str], *, snapshot: FacetTimelineSnapshot | None=None, as_of: str | None=None) -> dict[str, list[TimelinePoint]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1038) — Build multiple Demonstrated curves from one bulk ledger replay.
- `facet_evidence_timeline(vault: LoadedVault, repository: Repository, facet_id: str) -> list[TimelinePoint]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1080) — The Demonstrated curve for ``facet_id`` (canonicalized) — the §9.6 phase-1 surface.
- `class ReadyCapabilitySlice` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1094) — One capability slice pooled into the facet's shared recall belief.
  - `as_dict(self) -> dict[str, object]` (line 1103; public)
- `class ReadyDerivation` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1114) — The §5.1 Ready-sentence ingredients, template-rendered from ledger state.
  - `as_dict(self) -> dict[str, object]` (line 1138; public)
- `facet_ready_derivation(vault: LoadedVault, repository: Repository, facet_id: str, series: list[TimelinePoint], *, clock: Clock | None=None) -> ReadyDerivation | None` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1155) — §5.1 Ready-derivation ingredients for a canonical facet, or ``None``.

## Internal implementation anchors

- `_at_or_before(stamp: str | None, cutoff: str) -> bool` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 240)
- `_epoch_held_as_of(rows: tuple[GradingEvidenceRecord, ...], vault: LoadedVault | None, item_id: str | None) -> bool` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 305) — Replay's unrecorded-contract hold (mvp-0.26) for an attempt's rows as they stood at a cutoff: ``attempts.current_epoch_reading`` over them.
- `_contract_unrecorded(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 339)
- `_resolved_exercised_facets(observations: dict[str, list[dict[str, Any]]], merge_map: dict[str, str]) -> dict[str, frozenset[str]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 346) — A6 observations with their facet ids merge-resolved (Meas §3.A1 guard 1).
- `_with_p0_masses(vault: LoadedVault, repository: Repository, snapshot: FacetTimelineSnapshot) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 409) — Attach the P0 mass map to a snapshot when the vault runs the P0 projection.
- `_epoch_certification_credit(vault: LoadedVault, item, rubric, *, rows_by_criterion: dict[str, dict], attempt_type: str, surface_group: str, assisted: bool, certification_eligible: bool, seen_groups_by_cell: dict[tuple[str, str], set[str]], resolve, exercised_facets: frozenset[str]=frozenset(), evidence_mass_override: float | None=None) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], set[str]], list, dict[tuple[str, str], str], dict[tuple[str, str], float]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 610) — Final capped certification credit for every cell in one grading epoch.
- `_decoded_attribution(raw: str | None) -> object` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 797) — Decode a persisted failure-attribution payload (None on legacy rows).
- `_observation_events_by_facet(vault: LoadedVault, snapshot: FacetTimelineSnapshot, canonical_facets: Iterable[str]) -> dict[str, list[ObservationEvent]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 808) — Extract events for every requested facet in one grading-ledger walk.
- `_observation_events(vault: LoadedVault, repository: Repository, canonical_facet: str) -> list[ObservationEvent]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 1021) — Compatibility wrapper for callers that inspect one facet's events.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `facet_evidence_timelines`; statically calls `facet_evidence_timelines`
- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `facet_evidence_timelines`, `load_facet_timeline_snapshot`; statically calls `facet_evidence_timelines`, `load_facet_timeline_snapshot`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `facet_evidence_timelines`, `vault_timeline_snapshot`; statically calls `facet_evidence_timelines`, `vault_timeline_snapshot`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `epoch_held_as_of`; statically calls `epoch_held_as_of`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `facet_evidence_timelines`; statically calls `facet_evidence_timelines`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `facet_evidence_timeline`, `facet_ready_derivation`; statically calls `facet_evidence_timeline`, `facet_ready_derivation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `load_effective_observation_references`; calls `load_effective_observation_references`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `cap_embedded_credit`, `supporting_unexercised`; calls `cap_embedded_credit`, `supporting_unexercised`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GradingEvidenceRecord`, `Repository`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `resolve_attempt_activity_policy`; calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/goals/receipt_contributions|learnloop.goals.receipt_contributions]] — imports `itemize_observation_contributions`; calls `itemize_observation_contributions`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`, `only_grade`, `ordered_epochs`; calls `current_epoch`, `only_grade`, `ordered_epochs`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `contract_unrecorded_attempts`; calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `P0_PROJECTION_VERSIONS`, `rubric_from_contract`; calls `rubric_from_contract`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`, `resolve_canonical_facet`; calls `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `DEFAULT_REPEAT_SURFACE_DISCOUNT`, `FAILURE_THRESHOLD`, `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`, `transfer_tier_mass_scale`, `unassessed_evidence_row`; calls `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`, `transfer_tier_mass_scale`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]], [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]], [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_the_demonstrated_curve_banks_what_the_belief_banks`
- [tests/test_facet_evidence_timeline.py](../../../../../../tests/test_facet_evidence_timeline.py) — direct import
  - `test_assisted_observation_earns_zero_credit`
  - `test_bulk_timelines_read_grading_history_once`
  - `test_correction_that_retires_all_credit_steps_to_zero`
  - `test_fresh_unassisted_observations_rise_monotonically`
  - `test_hinted_attempt_contributes_flat_point`
  - `test_real_regrade_renders_as_correction_step`
  - `test_recompute_from_scratch_equals_incremental_render`
  - `test_regrade_correction_steps_the_curve_down`
  - `test_repeat_surface_group_is_discounted`
  - `test_timeline_rises_on_real_unassisted_demonstration`
- [tests/test_learner_read_model_pinning.py](../../../../../../tests/test_learner_read_model_pinning.py) — direct import
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_adjudication_reverses_projection_and_preserves_history`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_missing_evidence_rows_bank_nothing`
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
  - `test_partially_graded_attempt_credits_only_the_graded_criterion`
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
  - `test_f3_the_timeline_carries_each_attempts_effective_credit_and_capability_credit`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_a_later_regrade_does_not_rewrite_the_credit_banked_before_the_cutoff`
  - `test_f1_r2_the_as_of_curve_ignores_gradings_recorded_after_the_cutoff`
  - `test_f3_r2_embedded_only_credit_under_the_default_cap_leaves_the_claim_open`
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f1_r3_a_hold_released_after_the_cutoff_still_holds_at_the_cutoff`
  - `test_f1_r3_the_as_of_hold_agrees_with_the_upgrade_on_every_shape`
  - `test_f1_r3_the_as_of_hold_is_the_replay_predicate_on_the_ledger`
  - `test_f2_r3_embedded_credit_banking_beside_standing_direct_credit_answers_the_claim`
  - `test_f2_r3_embedded_credit_whose_direct_credit_was_regraded_away_leaves_the_claim_open`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — direct import
  - `test_per_observation_itemization_sums_to_banked_credit`
  - `test_ready_derivation_matches_canonical_recall_slices`
  - `test_ready_derivation_none_on_legacy_vault`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
  - `test_from_scratch_fold_equals_incremental_fold_on_real_history`
  - `test_timeline_final_credit_equals_banked_ledger_credit`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_historical_cutoff_ignores_a_later_unaided_success`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f4_the_learning_diff_names_the_attempts_whose_points_raised_a_demonstrated_facet`

## Modification guidance

- Change facet evidence timeline policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/facet_evidence_timeline.py](../../../../../../src/learnloop/learner/facet_evidence_timeline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
