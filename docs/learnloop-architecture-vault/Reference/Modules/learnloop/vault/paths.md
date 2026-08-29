---
title: "learnloop.vault.paths"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/paths.py"
source_paths:
  - "src/learnloop/vault/paths.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.paths module"
  - "src/learnloop/vault/paths.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.paths`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps paths behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultPaths`, `animation_video_path`, `find_vault_root`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/paths.py](../../../../../../src/learnloop/vault/paths.py) |
| Source lines | 123 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class VaultPaths` ([source](../../../../../../src/learnloop/vault/paths.py), line 11)
  - `config_path(self) -> Path` (line 16; public)
  - `sqlite_path(self) -> Path` (line 20; public)
  - `concepts_path(self) -> Path` (line 24; public)
  - `relations_path(self) -> Path` (line 28; public)
  - `goals_path(self) -> Path` (line 32; public)
  - `learner_path(self) -> Path` (line 36; public)
  - `error_types_path(self) -> Path` (line 40; public)
  - `facets_path(self) -> Path` (line 44; public)
  - `subject_dir(self, subject_id: str) -> Path` (line 47; public)
  - `subject_markdown_path(self, subject_id: str) -> Path` (line 50; public)
  - `subject_graph_path(self, subject_id: str) -> Path` (line 53; public)
  - `learning_object_path(self, subject_id: str, learning_object_id: str) -> Path` (line 56; public)
  - `practice_item_path(self, subject_id: str, practice_item_id: str) -> Path` (line 59; public)
  - `note_path(self, subject_id: str, note_id: str) -> Path` (line 62; public)
  - `sources_dir(self) -> Path` (line 70; public)
  - `source_sets_path(self) -> Path` (line 74; public)
  - `source_dir(self, source_id: str) -> Path` (line 79; public)
  - `source_markdown_path(self, source_id: str) -> Path` (line 82; public)
  - `source_revision_path(self, source_id: str, revision_id: str) -> Path` (line 86; public)
  - `canonical_source_raw_path(self, asset_hash: str) -> Path` (line 90; public)
  - `source_extraction_cache_dir(self, extraction_id: str) -> Path` (line 94; public)
  - `animations_dir(self) -> Path` (line 99; public)
- `animation_video_path(root: Path, video_hash: str) -> Path` ([source](../../../../../../src/learnloop/vault/paths.py), line 104) — Content-addressed animation mp4 path; config-free like the raw store.
- `find_vault_root(start: Path) -> Path` ([source](../../../../../../src/learnloop/vault/paths.py), line 116)

## Internal implementation anchors

- `_sanitize_hash(asset_hash: str) -> str` ([source](../../../../../../src/learnloop/vault/paths.py), line 110)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `VaultPaths`, `find_vault_root`; statically calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `VaultPaths`, `animation_video_path`; statically calls `VaultPaths`, `animation_video_path`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/sources/source_deletion|learnloop.content.sources.source_deletion]] — imports `canonical_source_raw_path`; statically calls `canonical_source_raw_path`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/debug_time|learnloop.ops.debug_time]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `VaultPaths`, `find_vault_root`; statically calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `VaultPaths`; statically calls `VaultPaths`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `VaultPaths`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `canonical_source_raw_path`; calls `canonical_source_raw_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] and 30 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_apply_write_ahead.py](../../../../../../tests/test_apply_write_ahead.py) — direct import
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — direct import
  - `test_cli_show_attempt_includes_evidence_and_surprise`
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_proposals_json_contract`
- [tests/test_concept_animation_service.py](../../../../../../tests/test_concept_animation_service.py) — direct import
- [tests/test_concept_animation_store.py](../../../../../../tests/test_concept_animation_store.py) — direct import
  - `test_animation_video_path_is_content_addressed`
- [tests/test_diagnostic_generation.py](../../../../../../tests/test_diagnostic_generation.py) — direct import
- [tests/test_diagnostic_pack.py](../../../../../../tests/test_diagnostic_pack.py) — direct import
- [tests/test_facet_mint_gate.py](../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
- [tests/test_failure_triage.py](../../../../../../tests/test_failure_triage.py) — direct import
  - `test_high_confidence_signature_takes_intended_route`
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_triage_records_tier_one_basis_on_the_result_and_the_event`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — direct import
  - `test_fixture_blueprint_is_active_after_confirmation`
  - `test_fixture_bootstrap_confirms_a_certifying_run`
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_originals_store.py](../../../../../../tests/test_originals_store.py) — direct import
  - `test_resolve_prefers_store_then_original_uri`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_pattern_ladder.py](../../../../../../tests/test_pattern_ladder.py) — direct import
- [tests/test_persona_gate.py](../../../../../../tests/test_persona_gate.py) — direct import
  - `test_gate_precision_reports_no_data_before_any_prediction`
- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
- [tests/test_quick_add.py](../../../../../../tests/test_quick_add.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_golden_path_completes_with_reader_never_invoked`
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_scheduler_scores_due_goal_item`
- [tests/test_sidecar_append.py](../../../../../../tests/test_sidecar_append.py) — direct import
  - `test_list_source_conflicts_enriches_extraction_ids`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_get_facet_mastery_shape_on_fixture_vault`
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — direct import
  - `test_reader_ask_history_rpc_returns_durable_exchanges`
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_runner_completes_session_with_teach_back_item`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — direct import
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
  - `test_delete_keeps_stored_bytes_another_source_still_shares`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_locked_subject_bootstrap_refusal`
- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`

## Modification guidance

- Make changes here when the responsibility remains paths within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/paths.py](../../../../../../src/learnloop/vault/paths.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
