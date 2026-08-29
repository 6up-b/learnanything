---
title: "learnloop.learner.facet_evidence_timeline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/facet_evidence_timeline.py"
source_paths:
  - "src/learnloop/learner/facet_evidence_timeline.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.facet_evidence_timeline` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Facet evidence timeline — the Demonstrated curve (KM §9.6 phase 1, §16).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/facet_evidence_timeline.py](../../../../../../src/learnloop/learner/facet_evidence_timeline.py) |
| Source lines | 1047 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ObservationDerivation` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 69) — Per-observation §5.1 receipt line for one (facet, capability) cell.
  - `as_dict(self) -> dict[str, object]` (line 83; public)
- `class ObservationEvent` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 94) — One grading epoch of one attempt, as it bears on a single facet.
  - `raw_positive(self) -> float` (line 124; public)
- `class TimelinePoint` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 129)
  - `as_dict(self) -> dict[str, object]` (line 144; public)
- `class FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 161) — Bulk-loaded immutable inputs for one evidence-ledger replay.
- `load_facet_timeline_snapshot(repository: Repository) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 188) — Load the complete timeline ledger with a bounded number of DB reads.
- `p0_evidence_mass_by_attempt(vault: LoadedVault, repository: Repository) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 242) — Per-attempt mvp-0.8 evidence mass, byte-matched to the projection.
- `fold_demonstrated_timeline(events: list[ObservationEvent], *, repeat_surface_discount: float=DEFAULT_REPEAT_SURFACE_DISCOUNT, max_embedded_credit_share: float=1.0) -> list[TimelinePoint]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 300) — Fold ordered observation events into the Demonstrated curve (pure).
- `facet_evidence_timelines(vault: LoadedVault, repository: Repository, facet_ids: Iterable[str], *, snapshot: FacetTimelineSnapshot | None=None) -> dict[str, list[TimelinePoint]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 826) — Build multiple Demonstrated curves from one bulk ledger replay.
- `facet_evidence_timeline(vault: LoadedVault, repository: Repository, facet_id: str) -> list[TimelinePoint]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 861) — The Demonstrated curve for ``facet_id`` (canonicalized) — the §9.6 phase-1 surface.
- `class ReadyCapabilitySlice` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 875) — One capability slice pooled into the facet's shared recall belief.
  - `as_dict(self) -> dict[str, object]` (line 884; public)
- `class ReadyDerivation` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 895) — The §5.1 Ready-sentence ingredients, template-rendered from ledger state.
  - `as_dict(self) -> dict[str, object]` (line 919; public)
- `facet_ready_derivation(vault: LoadedVault, repository: Repository, facet_id: str, series: list[TimelinePoint], *, clock: Clock | None=None) -> ReadyDerivation | None` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 936) — §5.1 Ready-derivation ingredients for a canonical facet, or ``None``.

## Internal implementation anchors

- `_resolved_exercised_facets(observations: dict[str, list[dict[str, Any]]], merge_map: dict[str, str]) -> dict[str, frozenset[str]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 213) — A6 observations with their facet ids merge-resolved (Meas §3.A1 guard 1).
- `_with_p0_masses(vault: LoadedVault, repository: Repository, snapshot: FacetTimelineSnapshot) -> FacetTimelineSnapshot` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 276) — Attach the P0 mass map to a snapshot when the vault runs the P0 projection.
- `_epoch_certification_credit(vault: LoadedVault, item, rubric, *, rows_by_criterion: dict[str, dict], attempt_type: str, surface_group: str, assisted: bool, certification_eligible: bool, seen_groups_by_cell: dict[tuple[str, str], set[str]], resolve, exercised_facets: frozenset[str]=frozenset(), evidence_mass_override: float | None=None) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], set[str]], list, dict[tuple[str, str], str], dict[tuple[str, str], float]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 422) — Final capped certification credit for every cell in one grading epoch.
- `_decoded_attribution(raw: str | None) -> object` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 604) — Decode a persisted failure-attribution payload (None on legacy rows).
- `_observation_events_by_facet(vault: LoadedVault, snapshot: FacetTimelineSnapshot, canonical_facets: Iterable[str]) -> dict[str, list[ObservationEvent]]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 615) — Extract events for every requested facet in one grading-ledger walk.
- `_observation_events(vault: LoadedVault, repository: Repository, canonical_facet: str) -> list[FacetEvidenceEvent]` ([source](../../../../../../src/learnloop/learner/facet_evidence_timeline.py), line 810) — Compatibility wrapper for callers that inspect one facet's events.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `facet_evidence_timelines`, `load_facet_timeline_snapshot`; statically calls `facet_evidence_timelines`, `load_facet_timeline_snapshot`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `facet_evidence_timelines`; statically calls `facet_evidence_timelines`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `facet_evidence_timeline`, `facet_ready_derivation`; statically calls `facet_evidence_timeline`, `facet_ready_derivation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `load_effective_observation_references`; calls `load_effective_observation_references`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `cap_embedded_credit`, `supporting_unexercised`; calls `cap_embedded_credit`, `supporting_unexercised`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GradingEvidenceRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `resolve_attempt_activity_policy`; calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/goals/receipt_contributions|learnloop.goals.receipt_contributions]] — imports `itemize_observation_contributions`; calls `itemize_observation_contributions`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `P0_PROJECTION_VERSIONS`, `rubric_from_contract`; calls `rubric_from_contract`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`, `resolve_canonical_facet`; calls `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `DEFAULT_REPEAT_SURFACE_DISCOUNT`, `FAILURE_THRESHOLD`, `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`; calls `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
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
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_adjudication_reverses_projection_and_preserves_history`
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_missing_evidence_rows_bank_nothing`
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
  - `test_partially_graded_attempt_credits_only_the_graded_criterion`
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — direct import
  - `test_per_observation_itemization_sums_to_banked_credit`
  - `test_ready_derivation_matches_canonical_recall_slices`
  - `test_ready_derivation_none_on_legacy_vault`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
  - `test_from_scratch_fold_equals_incremental_fold_on_real_history`
  - `test_timeline_final_credit_equals_banked_ledger_credit`

## Modification guidance

- Change facet evidence timeline policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/facet_evidence_timeline.py](../../../../../../src/learnloop/learner/facet_evidence_timeline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
