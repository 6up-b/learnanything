---
title: "learnloop.ids"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ids.py"
source_paths:
  - "src/learnloop/ids.py"
source_commit: "4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7"
source_commit_timestamp: "2026-05-19T19:15:00-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "primitive"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.ids module"
  - "src/learnloop/ids.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/primitive"
  - "package/learnloop"
---

# `learnloop.ids`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps ids behavior inside its owning package, [[Reference/Modules/learnloop/_package|learnloop]]. Its public surface centers on `new_ulid`, `kebab_case`, `snake_case`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ids.py](../../../../../src/learnloop/ids.py) |
| Source lines | 39 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `primitive` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7` |
| Commit timestamp | `2026-05-19T19:15:00-04:00` |

## Public API

- `new_ulid() -> str` ([source](../../../../../src/learnloop/ids.py), line 17) — Generate a ULID-like sortable identifier without an external runtime dependency.
- `kebab_case(value: str) -> str` ([source](../../../../../src/learnloop/ids.py), line 25)
- `snake_case(value: str) -> str` ([source](../../../../../src/learnloop/ids.py), line 38)

### Module constants

- `_CROCKFORD` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 6)

## Internal implementation anchors

- `_encode_crockford(value: int, length: int) -> str` ([source](../../../../../src/learnloop/ids.py), line 9)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `kebab_case`; statically calls `kebab_case`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `kebab_case`, `new_ulid`, `snake_case`; statically calls `kebab_case`, `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `snake_case`; statically calls `snake_case`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/prequential|learnloop.scheduling.prequential]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `kebab_case`, `snake_case`; statically calls `kebab_case`, `snake_case`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `new_ulid`; statically calls `new_ulid`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `secrets`, `time`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]], [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] and 47 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
- [tests/test_characterization_probe_regrade.py](../../../../../tests/test_characterization_probe_regrade.py) — direct import
  - `test_deferred_regrade_rewrites_summary_but_posterior_does_not_follow`
- [tests/test_characterization_probe_replay.py](../../../../../tests/test_characterization_probe_replay.py) — direct import
- [tests/test_goal_contracts.py](../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_misconception_registry.py](../../../../../tests/test_misconception_registry.py) — direct import
  - `test_discriminating_item_has_higher_eig`
- [tests/test_p2_acceptance.py](../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_probe_audit.py](../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_probe_block_end.py](../../../../../tests/test_probe_block_end.py) — direct import
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_probe_dialogue.py](../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_episodes.py](../../../../../tests/test_probe_episodes.py) — direct import
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
- [tests/test_probe_longform_families.py](../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_orchestration_remainder.py](../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_out_of_range_is_rejected`
- [tests/test_probe_policy.py](../../../../../tests/test_probe_policy.py) — direct import
- [tests/test_probe_robust_cutover.py](../../../../../tests/test_probe_robust_cutover.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains ids within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ids.py](../../../../../src/learnloop/ids.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
