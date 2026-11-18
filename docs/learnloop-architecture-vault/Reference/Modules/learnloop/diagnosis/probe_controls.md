---
title: "learnloop.diagnosis.probe_controls"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_controls.py"
source_paths:
  - "src/learnloop/diagnosis/probe_controls.py"
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
  - "learnloop.diagnosis.probe_controls module"
  - "src/learnloop/diagnosis/probe_controls.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_controls`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_controls` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Learner controls and the shared diagnostic client contract.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_controls.py](../../../../../../src/learnloop/diagnosis/probe_controls.py) |
| Source lines | 185 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class StoppedCheck` ([source](../../../../../../src/learnloop/diagnosis/probe_controls.py), line 47) — What `Stop diagnosing and teach me` did: the typed transition decision it persisted, and the block's committed answers' feedback it released.
- `stop_diagnosing_and_teach(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> StoppedCheck | None` ([source](../../../../../../src/learnloop/diagnosis/probe_controls.py), line 55) — `Stop diagnosing and teach me`: settle the block's committed answers, end measurement, open a post-intervention state segment, and persist a typed transition decision (§12.1).
- `episode_contract(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_controls.py), line 106) — The probe UX contract for one LO, or None when no episode is active.
- `next_probe_item(vault: LoadedVault, repository: Repository, learning_object_id: str) -> EligibleInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_controls.py), line 141) — The item that would be served next for this LO's open episode, or None.

### Module constants

- `PROBE_ASSISTANCE_RESTRICTIONS` ([src/learnloop/diagnosis/probe_controls.py](../../../../../../src/learnloop/diagnosis/probe_controls.py), line 37)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `episode_contract`, `stop_diagnosing_and_teach`; statically calls `episode_contract`, `stop_diagnosing_and_teach`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `episode_contract`, `next_probe_item`, `stop_diagnosing_and_teach`; statically calls `episode_contract`, `next_probe_item`, `stop_diagnosing_and_teach`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `block_observation_rows`, `build_typed_transition_decision`, `first_error_from_block`, `settle_block_answers`; calls `block_observation_rows`, `build_typed_transition_decision`, `first_error_from_block`, `settle_block_answers`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `set_target_decision`, `voi_probe_site_active`; calls `set_target_decision`, `voi_probe_site_active`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `open_cause_sets_for_learning_object`, `select_discriminating_instrument`; calls `open_cause_sets_for_learning_object`, `select_discriminating_instrument`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
  - `test_probe_pool_is_empty_for_an_inactive_lo`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
  - `test_staged_owned_item_never_surfaces_in_probe_slate`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_probe_selection_offers_both_instruments`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_next_probe_item_peeks_the_unused_surface_without_committing`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
- [tests/test_teach_handoff_stop_settles.py](../../../../../../tests/test_teach_handoff_stop_settles.py) — direct import
  - `test_a_mid_check_stop_normalizes_joint_answers_and_releases_their_feedback`
  - `test_a_mid_check_stop_queues_the_blind_answers_diagnosis`
  - `test_a_stop_with_nothing_committed_settles_nothing`
  - `test_the_calibration_dialogue_s_stop_settles_its_committed_turns`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_the_probe_contract_says_value_decides_only_with_the_switch_on`

## Modification guidance

- Change probe controls policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_controls.py](../../../../../../src/learnloop/diagnosis/probe_controls.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
