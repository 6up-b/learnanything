---
title: "learnloop.content.synthesis.source_set_synthesis"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_set_synthesis.py"
source_paths:
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_set_synthesis module"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_set_synthesis`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_set_synthesis` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Bootstrap synthesis: brief -> sharded synthesis -> dependency-closed proposal -> applied study map (source-ingestion v2 §8, ING M6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py) |
| Source lines | 2668 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class StudyMapError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 90) — A typed bootstrap-synthesis failure (lock refusal / gate hard-fail).
  - `__init__(self, code: str, message: str, *, diagnostics: list[dict[str, Any]] | None=None, lock_reasons: list[dict[str, Any]] | None=None, synthesis_run_id: str | None=None, candidate_preserved: bool=False)` (line 93; internal)
- `request_source_set_synthesis(client: StructuredTransport, context: SourceSetSynthesisContext) -> SourceSetSynthesis` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 105) — Synthesize one source-set shard through the shared transport.
- `request_concept_graph_structuring(client: StructuredTransport, context: ConceptGraphContext) -> ConceptGraphStructuring` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 118) — Structure a merged candidate graph through the shared transport.
- `class StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 132)
  - `as_dict(self) -> dict[str, Any]` (line 149; public)
- `resolve_subject_id(source_set: Any, vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1360) — The subject a synthesized study map belongs to: the source set's own subject_id (§4.3 — sets are subject-scoped), never "first subject in the vault", which misfires on multi-subject vaults and crashes on fresh ones.
- `create_study_map(root: Path, source_set_id: str, *, client: Any, brief: dict[str, Any] | None=None, mode: str='auto', apply: bool=False, create_goal: bool=False, repository: Repository | None=None, clock: Clock | None=None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1427)
- `derive_candidate_repairs(candidate: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1790) — Mechanically-safe repair ops for a preserved synthesis candidate.
- `apply_candidate_repairs(candidate: dict[str, Any], ops: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1839) — Apply typed repair ops to a candidate dict; returns (repaired, log).
- `revalidate_synthesis_candidate(root: Path, synthesis_run_id: str, *, apply: bool=False, create_goal: bool=False, repair: bool=False, repair_ops: list[dict[str, Any]] | None=None, repository: Repository | None=None, clock: Clock | None=None, progress: ProgressFn | None=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1889) — Re-run normalization, gates, and persistence over a preserved candidate with ZERO model calls.

### Module constants

- `SYNTHESIS_AGENT_PURPOSE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 81)
- `BOOTSTRAP_PROPOSAL_PURPOSE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 82)
- `_SEMANTIC_ROLES` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 85)
- `_SHARD_PREFIX_RE` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1784)
- `_CANDIDATE_ITEM_FIELDS` ([src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1787)

## Internal implementation anchors

- `class _SynthesisInputs` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 173)
- `_best_inventory(rows: list[dict[str, Any]], unit_id: str, requested_profile: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 186)
- `_assessment_signal_spans(inventory: dict[str, Any], *, held_out_only: bool) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 200)
- `_collect_inputs(repo: Repository, vault: LoadedVault, source_set: SourceSet) -> _SynthesisInputs` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 210)
- `_registry_index(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 363) — A compact existing-registry index for the prompt (never full contracts).
- `_notify(progress: ProgressFn | None, stage: str, message: str, *, current: int | None=None, total: int | None=None) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 380)
- `_shards(unit_inventories: list[dict[str, Any]], shard_input_tokens: int) -> list[list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 392)
- `_resolve_span_requests(repo: Repository, requests: list[dict[str, Any]], inputs: _SynthesisInputs, *, max_count: int, char_cap: int) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 414) — One bounded span-request round (§8.5).
- `_slug(prefix: str, text: str, fallback: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 465)
- `class _Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 471)
- `_span_refs(refs: list[Any], inputs: _SynthesisInputs, *, default_relation: str) -> tuple[list[ProvenanceRef], list[dict[str, Any]], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 484) — Build gate ProvenanceRefs + YAML source_refs from synth span refs.
- `_normalize(synth: Any, inputs: _SynthesisInputs, vault: LoadedVault, now: str, *, subject_id: str, items_off: bool=False) -> _Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 539)
- `_row(item_type: str, entity_id: str, payload: dict[str, Any], depends_on: list[str], *, client_id: str, now: str, target_entity_id: str | None=None, target_entity_type: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1377)
- `_bootstrap_lock_refusal(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1403) — §8.2 enforcement 1: bootstrap is legal only where nothing is identity-locked.
- `_create_study_map(vault: LoadedVault, repository: Repository, root: Path, source_set_id: str, *, client: Any, brief: dict[str, Any], mode: str, apply: bool, create_goal: bool, clock: Clock | None, budget_overrides: dict[str, int] | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None) -> StudyMapResult` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1455)
- `_gate_and_persist(vault: LoadedVault, repository: Repository, source_set: SourceSet, merged: Any, inputs: _SynthesisInputs, *, subject_id: str, agent_run_id: str | None, synthesis_run_id: str, now: str, usage: dict[str, Any] | None, resolved_hashes: list[str], clock: Clock | None, progress: ProgressFn | None=None, items_off: bool=False, token_usage: TokenUsage | None=None, grading_client: Any=None) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], _Normalized]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 1654) — Normalize -> §8.7 gates -> persist proposal, over a merged candidate.
- `_run_synthesis(transport, repository, inputs, vault, source_set, brief, budgets, *, clock, client: Any=None, provider: str | None=None, model: str | None=None, manifest_hash: str | None=None, unlimited_token_budget: bool=False, progress: ProgressFn | None=None)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2002)
- `_result_tokens(result: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2159)
- `_merge_synthesis(base: Any, extra: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2169)
- `_namespace_synthesis_shard(result: Any, ordinal: int) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2175) — Make model-authored client ids local to one synthesis shard.
- `_shard_checkpoint_key(*, source_set: Any, brief: dict[str, Any], registry: dict[str, Any], exam_profile: dict[str, Any] | None, shard: list[dict[str, Any]], ordinal: int, count: int, provider: str | None, model: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2213) — Durable checkpoint identity for one synthesis shard.
- `_consolidate_same_title_concepts(result: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2260) — Deterministic pass: fold concepts whose normalized titles are identical.
- `_source_skeletons(repository: Repository, inputs: _SynthesisInputs) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2285) — Compact per-source big-picture views from already-paid-for artifacts.
- `_model_graph_structuring(merged: Any, client: Any, source_set: Any, inputs: _SynthesisInputs, repository: Repository, vault: LoadedVault, *, shard_count: int, input_tokens_estimate: int, total_input_ceiling: int | None, progress: ProgressFn | None=None) -> tuple[Any, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2342) — One bounded model pass over the WHOLE merged candidate (§8.5): folds semantic duplicate concepts AND authors the big-picture concept relations (part_of hierarchy, prerequisites, confusables) across every shard and source, using the compact source skeletons as whole-span context.
- `_validated_merge_mapping(consolidation: Any, result: Any) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2440) — duplicate client id -> canonical client id, from validated merge groups.
- `_apply_concept_merges(result: Any, mapping: dict[str, str]) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2466) — Fold duplicate concepts into their canonical and rewrite all references.
- `_duplicate_client_id_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2539)
- `_gate_context(vault, repository, inputs, findings) -> GateContext` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2554)
- `_findings_to_diagnostics(findings) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2575)
- `_persist_generation_needs(repository, subject_id, source_set_id, synthesis_run_id, findings, *, clock)` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2590)
- `_count_items(rows: list[dict[str, Any]]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2616)
- `_is_exam_prep(brief: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2623)
- `_create_goal_from_brief(root: Path, brief: dict[str, Any], facet_ids: list[str], *, clock: Clock | None) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py), line 2628) — Create a Goal wired to the freshly minted facets (§5.1), after acceptance.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `StudyMapError`, `create_study_map`, `derive_candidate_repairs`, `revalidate_synthesis_candidate`; statically calls `create_study_map`, `derive_candidate_repairs`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `StudyMapError`, `create_study_map`, `revalidate_synthesis_candidate`; statically calls `create_study_map`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `StudyMapError`, `_collect_inputs`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`; statically calls `StudyMapError`, `_collect_inputs`, `_gate_context`, `_normalize`, `_resolve_span_requests`, `_row`, `_span_refs`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `StudyMapError`, `create_study_map`; statically calls `create_study_map`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsage`, `consume_client_usage`; calls `TokenUsage`, `consume_client_usage`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `apply_accepted_items`; calls `apply_accepted_items`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `role_authority`; calls `role_authority`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `ConceptGraphContext`, `ConceptGraphStructuring`, `SOURCE_SET_SYNTHESIS_PROMPT_VERSION`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`; calls `ConceptGraphContext`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `validate_brief`; calls `validate_brief`
- [[Reference/Modules/learnloop/content/synthesis/exam_profile|learnloop.content.synthesis.exam_profile]] — imports `ExamUnitEntry`, `aggregate_exam_profile`; calls `ExamUnitEntry`, `aggregate_exam_profile`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `MintDisposition`, `judge_facet_mints`, `mint_diagnostic`; calls `judge_facet_mints`, `mint_diagnostic`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `profile_satisfies`; calls `profile_satisfies`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `compute_effective_units`, `effective_scope_groups`; calls `compute_effective_units`, `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; calls `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`; calls `agent_run_input_context_hash`, `build_manifest`, `persist_manifest`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `identity_locks`; calls `identity_locks`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CAPABILITY_VOCABULARY`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_proposal_view`; calls `analyze_identifiability`, `build_proposal_view`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `read_learner_profile`; calls `read_learner_profile`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_readiness_and_conflict.py](../../../../../../../tests/test_exam_readiness_and_conflict.py) — direct import
  - `test_conflict_resolution_notation_mapping_materializes_mapping`
  - `test_conflict_resolution_preserves_locators_and_audit`
  - `test_exam_readiness_predicted_score_distribution_is_analytic`
  - `test_exam_readiness_report_is_deterministic_and_labels_ready_vs_demonstrated`
- [tests/test_facet_mint_gate.py](../../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_apply_stamps_coverage_boundary_and_later_rebuilds_add_nothing`
  - `test_explicit_capabilities_produce_no_capability_diagnostics`
  - `test_omitted_component_capability_defaults_with_diagnostic`
  - `test_omitted_criterion_target_capability_defaults_with_diagnostic`
  - `test_reachability_summary_reports_minted_cells`
  - `test_single_alternative_any_of_gets_review_diagnostic`
  - `test_synthesis_lane_blocks_selected_response_items`
  - `test_synthesis_lane_records_persona_gate_outcome`
  - `test_vacuous_recipe_hard_fails_at_the_gate`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_maintenance_feed.py](../../../../../../../tests/test_maintenance_feed.py) — direct import
  - `test_dismiss_and_snooze_do_not_change_curriculum`
  - `test_maintenance_notice_aging_policies`
  - `test_maintenance_notice_deterministic_generation`
- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
- [tests/test_revision_refresh.py](../../../../../../../tests/test_revision_refresh.py) — direct import
  - `test_new_revision_pinned_membership_requires_confirmation`
  - `test_unchanged_spans_keep_links_changed_spans_go_stale`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_context_bounded_by_neighborhood`
  - `test_n_sources_append_linear_inventory_and_bounded_context`
  - `test_planted_full_map_resend_fails_scaling_gate`
- [tests/test_source_outcome_analytics.py](../../../../../../../tests/test_source_outcome_analytics.py) — direct import
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_apply_candidate_repairs_vocabulary`
  - `test_auto_repair_drops_criterion_id_dependencies`
  - `test_bootstrap_canonicalizes_prerequisite_and_confusable_concepts`
  - `test_bootstrap_end_to_end_applies_learnable_map`
  - `test_bootstrap_mints_concept_for_unanchored_learning_object`
  - `test_bootstrap_tolerates_unresolved_concept_relationships`
  - `test_cross_shard_same_title_concepts_consolidate_deterministically`
  - `test_derive_candidate_repairs_only_targets_criterion_refs`
  - `test_exam_shifts_blueprint_distribution`
  - `test_facets_cite_textbook_not_exam_and_held_out_wording_absent`
  - `test_graph_structuring_merges_near_duplicates_and_authors_relations`
  - `test_graph_structuring_relations_become_concept_edges`
  - `test_integration_at_coordination_is_kept_but_flagged`
  - `test_integration_below_coordination_is_kept_silently`
  - `test_integration_without_capability_is_dropped_not_defaulted`
  - `test_invalid_structuring_nomination_is_a_noop`
  - `test_legacy_vault_acceptance_refused`
  - `test_lo_prerequisites_derive_concept_edges_without_model_relations`
  - `test_locked_subject_bootstrap_refusal`
  - `test_manifest_idempotency_cache_zero_new_calls`
  - `test_replay_identical_after_apply`
  - `test_resolve_subject_id_prefers_source_set_over_vault`
  - `test_revalidate_requires_a_preserved_candidate`
  - `test_revalidate_saved_candidate_completes_without_model`
  - `test_shard_checkpoints_survive_post_generation_failure`
  - `test_synthesis_can_disable_local_token_ceilings`
  - `test_synthesis_progress_reports_shard_and_stage_messages`
  - `test_synthesis_shards_namespace_declarations_and_references`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_subject_registry.py](../../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_synthesis_eval.py](../../../../../../../tests/test_synthesis_eval.py) — direct import
  - `test_canned_synthesis_scores_perfect_against_matching_gold`
- [tests/test_synthesis_identifiability.py](../../../../../../../tests/test_synthesis_identifiability.py) — direct import
  - `test_non_identifiable_bootstrap_persists_generation_need`
- [tests/test_tutor_citations.py](../../../../../../../tests/test_tutor_citations.py) — direct import

## Modification guidance

- Change source set synthesis policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_set_synthesis.py](../../../../../../../src/learnloop/content/synthesis/source_set_synthesis.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
