---
title: "learnloop.learner.facet_state_reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/facet_state_reader.py"
source_paths:
  - "src/learnloop/learner/facet_state_reader.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.learner.facet_state_reader module"
  - "src/learnloop/learner/facet_state_reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.facet_state_reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.facet_state_reader` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: KM2b consumer re-key: canonical shared facet state read adapter (§7.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py) |
| Source lines | 507 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `facet_belief_fixes_on(config) -> bool` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 46) — The facet-belief successor (mvp-0.59, ``FACET_BELIEF_FIX_VERSIONS``) with its switch ``facet_diagnostic.canonical_belief_fixes`` on.
- `facet_belief_corrections_on(config) -> bool` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 71) — The corrections to the successor's derivation: the uncertainty layer reads the frozen contract's criterion targets, the stored rows are read only through this module and relabelled when rekeyed, a success on a massless repeat surface still ends the failure streak, the timeline l…
- `canonical_facet_uncertainty_on(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 87) — A vault that writes and reads per-LO facet uncertainty (the facet-belief successor).
- `canonical_uncertainty_rows(vault: LoadedVault, repository: Repository, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 96) — The successor's uncertainty updates keyed by canonical facet id (aliases, then merges).
- `relabelled_marginal(marginal: Mapping[str, float], old_facet: str, new_facet: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 131) — A facet's hypothesis marginal under another id of the same facet.
- `current_facet_uncertainty(state: FacetUncertaintyState | None) -> FacetUncertaintyState | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 149) — A row the facet-belief successor wrote, or None.
- `resolve_canonical_facet(vault: LoadedVault, merge_map: dict[str, str], facet_id: str) -> str` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 160) — Resolve a facet id to its terminal canonical survivor (§7.1).
- `class CanonicalFacetStateReader` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 250) — Serves legacy-shaped per-LO facet states from canonical mvp-0.7 rows.
  - `__init__(self, vault: LoadedVault, repository: Repository) -> None` (line 258; internal)
  - `_resolve(self, facet_id: str) -> str` (line 283; internal)
  - `states_for_lo(self, learning_object_id: str) -> list[FacetRecallState]` (line 291; public)
  - `state_for_facet(self, learning_object_id: str, facet_id: str, practice_item_id: str | None=None) -> FacetRecallState | None` (line 319; public)
- `facet_states_by_lo(vault: LoadedVault, repository: Repository) -> dict[str, list[FacetRecallState]]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 343) — ``{learning_object_id: [FacetRecallState, ...]}`` for every LO in the vault.
- `facet_recall_states_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, *, reader: CanonicalFacetStateReader | None=None) -> list[FacetRecallState]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 352)
- `facet_recall_state_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, facet_id: str, practice_item_id: str | None=None, *, reader: CanonicalFacetStateReader | None=None) -> FacetRecallState | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 363)
- `facet_uncertainty_states_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, *, statuses: tuple[str, ...] | None=None) -> list[FacetUncertaintyState]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 376) — Per-LO facet uncertainty states (KM §7.1).
- `stored_facet_uncertainty_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, *, statuses: tuple[str, ...] | None=None) -> list[FacetUncertaintyState]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 422) — One LO's stored uncertainty rows as the readers outside the diagnostic layer see them: the instructional valuation, the Reader's open questions, tutor promotions and an attempt's prior.
- `attempt_uncertainty_priors(vault: LoadedVault, repository: Repository, learning_object_id: str, facets: Iterable[str]) -> dict[str, FacetUncertaintyState | None]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 445) — The stored row each of an attempt's facets updates from, keyed by the facet id the item names.
- `stored_facet_uncertainty_state(vault: LoadedVault, repository: Repository, learning_object_id: str, facet_id: str) -> FacetUncertaintyState | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 484) — One LO's stored uncertainty row on ``facet_id`` (its canonical survivor when the successor reads it), by the rules of :func:`stored_facet_uncertainty_for_lo`.

### Module constants

- `FACET_BELIEF_CORRECTION_VERSIONS` ([src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py), line 63)
- `DERIVED_WITH_BELIEF_FIXES_KEY` ([src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py), line 68)

## Internal implementation anchors

- `_max_iso(a: str | None, b: str | None) -> str | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 178)
- `_min_iso(a: str | None, b: str | None) -> str | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 186)
- `_capability_scope(rows: Iterable[CanonicalFacetRecallState]) -> str` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 194)
- `_fold(rows: list[CanonicalFacetRecallState], *, learning_object_id: str, facet_id: str, practice_item_id: str | None) -> FacetRecallState` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 199) — Fold capability-sliced canonical rows into one legacy-shaped state.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CanonicalFacetStateReader`, `DERIVED_WITH_BELIEF_FIXES_KEY`, `attempt_uncertainty_priors`, `canonical_facet_uncertainty_on`, `canonical_uncertainty_rows`, `facet_belief_corrections_on`; statically calls `CanonicalFacetStateReader`, `attempt_uncertainty_priors`, `canonical_facet_uncertainty_on`, `canonical_uncertainty_rows`, `facet_belief_corrections_on`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `facet_recall_states_for_lo`; statically calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `facet_recall_states_for_lo`; statically calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_states_by_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_states_by_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `stored_facet_uncertainty_state`; statically calls `stored_facet_uncertainty_state`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `stored_facet_uncertainty_state`; statically calls `stored_facet_uncertainty_state`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `facet_recall_states_for_lo`; statically calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `facet_belief_corrections_on`, `resolve_canonical_facet`; statically calls `facet_belief_corrections_on`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `facet_recall_state_for_lo`; statically calls `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `CanonicalFacetStateReader`, `facet_recall_state_for_lo`; statically calls `CanonicalFacetStateReader`, `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `DERIVED_WITH_BELIEF_FIXES_KEY`, `FACET_BELIEF_CORRECTION_VERSIONS`, `facet_belief_corrections_on`; statically calls `facet_belief_corrections_on`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `facet_states_by_lo`; statically calls `facet_states_by_lo`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `facet_belief_corrections_on`, `facet_belief_fixes_on`; statically calls `facet_belief_corrections_on`, `facet_belief_fixes_on`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `stored_facet_uncertainty_for_lo`; statically calls `stored_facet_uncertainty_for_lo`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `resolve_canonical_facet`; statically calls `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `resolve_canonical_facet`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FACET_BELIEF_FIX_VERSIONS`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CanonicalFacetRecallState`, `FacetRecallState`, `FacetUncertaintyState`, `Repository`; calls `FacetRecallState`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `_facet_uncertainty_id`; calls `_facet_uncertainty_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_replays_attempt_derived_state`
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_seed_creates_backdated_discounted_attempts`
- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_a_legacy_era_uncertainty_row_is_never_the_successors_prior_or_read`
  - `test_at_the_tag_the_three_fixes_and_the_uncertainty_show`
  - `test_the_gate_reads_off_below_the_tag_and_with_the_switch_off`
  - `test_the_upgrade_derives_the_successors_state_from_the_history`
  - `test_uncertainty_is_written_under_the_merged_facets_survivor`
  - `test_with_the_switch_off_the_belief_is_the_predecessors_exactly`
- [tests/test_facet_belief_successor_derivation.py](../../../../../../tests/test_facet_belief_successor_derivation.py) — direct import
  - `test_s3_a_row_read_under_its_facets_new_id_keeps_its_solid_reading`
  - `test_s3_after_an_alias_the_next_answer_updates_the_row_it_had_and_a_rebuild_agrees`
  - `test_s5_an_attempt_records_the_fixes_only_when_derived_with_them`
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_exam_attempt_moves_shared_parent_across_los`
  - `test_two_los_share_one_facet_parent_in_scheduler_view`
- [tests/test_learner_read_model_pinning.py](../../../../../../tests/test_learner_read_model_pinning.py) — direct import
- [tests/test_projection_timeline_agreement.py](../../../../../../tests/test_projection_timeline_agreement.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_facet_aliases_are_canonicalized_before_recall_updates`
  - `test_with_the_belief_fixes_off_a_success_keeps_the_facet_streak`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_finish_and_rebuild_replay_reproduce_derived_state`
  - `test_finish_partial_grading_only_asked_criteria_produce_evidence`
  - `test_regrade_teach_back_attempt_restricts_to_graded_criteria`

## Modification guidance

- Change facet state reader policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
