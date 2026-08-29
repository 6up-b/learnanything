---
title: "learnloop_sidecar.handlers.measurement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/measurement.py"
source_paths:
  - "src/learnloop_sidecar/handlers/measurement.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.measurement module"
  - "src/learnloop_sidecar/handlers/measurement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.measurement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps measurement behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `ScheduleCertificationColdProbesInput`, `GenerateCommissioningPracticeInput`, `TransitionCausalProbeCandidateInput`, `ApplyIntegrationBackfillInput`, `get_measurement_health`, `schedule_certification_cold_probes_handler`, `transition_causal_probe_candidate_handler`, `apply_integration_backfill_handler` and 1 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/measurement.py](../../../../../../src/learnloop_sidecar/handlers/measurement.py) |
| Source lines | 427 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ScheduleCertificationColdProbesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 38)
- `class GenerateCommissioningPracticeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 42)
- `class TransitionCausalProbeCandidateInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 53)
- `class ApplyIntegrationBackfillInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 60)
- `get_measurement_health(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 220) — Stage 0–6 plus the Stage 8.1 precheck for the Tauri Maintain view.
- `schedule_certification_cold_probes_handler(ctx: SidecarContext, params: ScheduleCertificationColdProbesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 272)
- `transition_causal_probe_candidate_handler(ctx: SidecarContext, params: TransitionCausalProbeCandidateInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 288)
- `apply_integration_backfill_handler(ctx: SidecarContext, params: ApplyIntegrationBackfillInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 306) — Apply reviewed D3 coordination edits and narrate the recalibration.
- `generate_commissioning_practice(ctx: SidecarContext, params: GenerateCommissioningPracticeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 341) — Author practice for the commissioning queue's authorable gaps.

## Internal implementation anchors

- `_integration_backfill(vault)` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 64)
- `_integration_backfill_payload(vault) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 71)
- `_causal_probe_review_queue(repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 86)
- `_instrument_audit_payload(vault, repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 133) — Every Meas §3 instrument class's REVERT criterion, plus A4 commissioning.
- `_facet_mint_gate_payload(vault) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/measurement.py), line 200)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `clarification_rate`; calls `clarification_rate`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `trace_evidence_report`; calls `trace_evidence_report`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `commission_plan`; calls `commission_plan`
- [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]] — imports `stem_independence_signal`, `stem_shapes`; calls `stem_independence_signal`, `stem_shapes`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `gate_precision`; calls `gate_precision`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `judge_facet_mints`; calls `judge_facet_mints`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `COORDINATION`, `apply_integration_backfill`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`; calls `apply_integration_backfill`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`
- [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]] — imports `causal_lane_health`; calls `causal_lane_health`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `candidate_has_current_blind_input_contract`, `transition_probe_candidate`; calls `candidate_has_current_blind_input_contract`, `transition_probe_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `causal_selection_readiness`; calls `causal_selection_readiness`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `commission_contrast_pairs`, `contrast_pair_order_effect`; calls `commission_contrast_pairs`, `contrast_pair_order_effect`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `profile_coverage`, `profile_match_fill_rate`; calls `profile_coverage`, `profile_match_fill_rate`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `error_hunt_outcome_summary`, `proofreading_signal`; calls `error_hunt_outcome_summary`, `proofreading_signal`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `missing_vocabulary_report`; calls `missing_vocabulary_report`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `scoreboard`; calls `scoreboard`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `certification_cold_probe_report`, `schedule_certification_cold_probes`; calls `certification_cold_probe_report`, `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/inference_precheck|learnloop.learner.inference_precheck]] — imports `analyze_inference_precheck`; calls `analyze_inference_precheck`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/measurement.py](../../../../../../src/learnloop_sidecar/handlers/measurement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
