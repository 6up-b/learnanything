---
title: "learnloop.diagnosis.causal_probe_commissioning"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_probe_commissioning.py"
source_paths:
  - "src/learnloop/diagnosis/causal_probe_commissioning.py"
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
  - "learnloop.diagnosis.causal_probe_commissioning module"
  - "src/learnloop/diagnosis/causal_probe_commissioning.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_probe_commissioning`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_probe_commissioning` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Commission a discriminating probe instrument for a divergent factor.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py) |
| Source lines | 777 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `targeted_criteria(hypothesis: Mapping[str, Any], rubric: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 143) — Candidate-item criterion ids that structurally exercise a hypothesis.
- `make_target_generator(frame_criterion_ids: Sequence[str]) -> BlindGenerator` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 202) — Blind structural predictions over the rivals' fresh-item target frame.
- `probe_instrument_class(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 284) — The instrument CLASS an item would serve as, for the multiplicity cap.
- `candidate_probe_items(vault: LoadedVault, *, learning_object_id: str, exclude_item_ids: Sequence[str]=()) -> list[PracticeItem]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 303) — Items that could serve as this factor's instrument, best first.
- `measurement_contract_for_item(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 328) — The item's OWN measurement targets, never the parent's.
- `commission_probe_instrument(vault: LoadedVault, repository: Repository, *, factor_id: str, candidate_practice_item_id: str | None=None, blind_generator: BlindGenerator | None=None, model_revision: str | None=None, outcome_schema_version: str='deterministic_criterion_features_v1', adversarial_review: Mapping[str, Any] | None=None, generation_agent_run_id: str | None=None, reviewer_agent_run_id: str | None=None, require_adversarial: bool=True, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 383) — Commission one discriminating instrument for ``factor_id``.
- `sweep_probe_commissioning(vault: LoadedVault, repository: Repository, *, learning_object_id: str, limit: int=4, clock: Clock | None=None, **kwargs: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 745) — Commission instruments for this learning object's divergent factors.

### Module constants

- `COMMISSIONING_POLICY_VERSION` ([src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 62)
- `MAX_CANDIDATES_PER_FACTOR` ([src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 67)
- `PREDICTION_BASES` ([src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 75)
- `COMMISSIONING_OUTCOMES` ([src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 84)
- `_ALGORITHM_VERSION` ([src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 118)

## Internal implementation anchors

- `_criterion_ids(payload: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 128)
- `_is_diagnostic_item(item: PracticeItem) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 277)
- `_result(outcome: str, **extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 374)
- `_support_scores(repository: Repository, factor: Mapping[str, Any]) -> dict[str, float | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py), line 716) — Support scores from the factor's diagnosis receipt, when it owns any.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `COMMISSIONING_POLICY_VERSION`, `commission_probe_instrument`; statically calls `commission_probe_instrument`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `audit_manipulation_contract`, `blind_bundle_discrimination`, `build_causal_hypothesis_set`, `candidate_has_current_blind_input_contract`, `create_probe_candidate`, `generate_blind_prediction_bundle`, `lock_causal_hypothesis_set`, `repair_class_need_for_factor`, `transition_probe_candidate`; calls `audit_manipulation_contract`, `blind_bundle_discrimination`, `build_causal_hypothesis_set`, `candidate_has_current_blind_input_contract`, `create_probe_candidate`, `generate_blind_prediction_bundle`, `lock_causal_hypothesis_set`, `repair_class_need_for_factor`, `transition_probe_candidate`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
  - `test_action_equivalent_causes_buy_nothing`
  - `test_causes_predicting_the_same_observation_do_not_discriminate`
  - `test_claims_the_item_cannot_observe_yield_no_derivable_predictions`
  - `test_commissioning_lights_the_lane_end_to_end`
  - `test_commissioning_makes_the_orchestrator_see_an_instrument`
  - `test_frame_generator_declares_targets_and_marks_the_complement`
  - `test_measurement_contract_is_the_items_own`
  - `test_no_candidate_item_is_an_authoring_obligation`
  - `test_obsolete_observation_exposed_candidate_cannot_advance`
  - `test_pending_adversarial_review_is_a_state_not_a_failure`
  - `test_self_reviewed_manipulation_is_rejected`
  - `test_sweep_commissions_open_factors_and_reports_each_outcome`
  - `test_sweep_machine_checks_queues_the_instrument_debt`
  - `test_target_mapping_never_falls_back_to_postdictive_claims`
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_commissioned_v2_bundles_reach_arm_b_and_the_prior_refusal_passes_through`
  - `test_readiness_report_counts_multiplicity_and_regimes`
  - `test_stripping_the_h_other_disposition_demotes_arm_b`
  - `test_v1_style_bundles_stay_arm_c_and_never_license_measure`

## Modification guidance

- Change causal probe commissioning policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_probe_commissioning.py](../../../../../../src/learnloop/diagnosis/causal_probe_commissioning.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
