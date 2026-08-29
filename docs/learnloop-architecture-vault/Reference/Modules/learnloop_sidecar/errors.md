---
title: "learnloop_sidecar.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/errors.py"
source_paths:
  - "src/learnloop_sidecar/errors.py"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.errors module"
  - "src/learnloop_sidecar/errors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.errors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps errors behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `SidecarError`, `json_rpc_error`, `sidecar_error`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py) |
| Source lines | 56 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Public API

- `class SidecarError(Exception)` ([source](../../../../../src/learnloop_sidecar/errors.py), line 11)
  - `__str__(self) -> str` (line 17; internal)
- `json_rpc_error(code: int, message: str, *, stable_code: str | None=None, retryable: bool=False, details: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/errors.py), line 21)
- `sidecar_error(exc: SidecarError) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/errors.py), line 38)

### Module constants

- `APPLICATION_ERROR_CODE` ([src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py), line 7)

## Internal implementation anchors

- `_stable_code_for_json_rpc(code: int) -> str` ([source](../../../../../src/learnloop_sidecar/errors.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `SidecarError`; statically calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `SidecarError`, `json_rpc_error`, `sidecar_error`; statically calls `json_rpc_error`, `sidecar_error`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] and 32 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../tests/test_build_study_map_routing.py) — direct import
  - `test_out_of_range_or_unknown_ceilings_are_refused`
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_submit_eliciting_response_sidecar_method`
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_a_facet_only_scope_that_resolves_to_nothing_is_refused`
  - `test_create_goal_refuses_a_concept_with_no_learning_objects`
  - `test_one_unmeasurable_concept_rejects_the_whole_selection`
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
  - `test_get_facet_detail_unknown_facet_raises`
  - `test_preview_blueprint_readiness_malformed_payload_raises`
  - `test_preview_blueprint_readiness_unknown_lo_raises`
  - `test_preview_knowledge_map_unknown_concept_raises`
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_a_stem_part_with_no_stimulus_is_still_refused`
  - `test_an_error_hunt_with_a_blank_worked_solution_is_still_refused`
  - `test_an_unknown_item_id_still_reports_not_found`
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
  - `test_queue_is_stratified_contests_first_then_abstentions`
  - `test_record_refuses_a_verdict_the_partition_forbids`
  - `test_scoreboard_keeps_enum_keys_and_refuses_a_flattering_rate`
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_invalid_pdf_page_expressions_are_rejected`
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
  - `test_create_goal_rejects_empty_scope`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_a_stem_part_with_no_stimulus_is_a_typed_refusal`
  - `test_an_error_hunt_with_no_worked_solution_is_a_typed_refusal`
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
  - `test_causal_probe_review_transition_returns_a_typed_sidecar_error`
  - `test_generate_commissioning_practice_rejects_unknown_learning_objects`
  - `test_integration_backfill_requires_explicit_confirmation`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
  - `test_an_empty_answer_is_refused_rather_than_burning_the_one_question`
  - `test_answering_a_question_that_was_never_asked_is_a_typed_refusal`
  - `test_answering_the_same_question_twice_is_a_typed_refusal`
  - `test_trace_evidence_read_rejects_an_unknown_attempt`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/errors.py](../../../../../src/learnloop_sidecar/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
