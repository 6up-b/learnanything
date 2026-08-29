---
title: "learnloop.content.authoring.practice_generation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/practice_generation.py"
source_paths:
  - "src/learnloop/content/authoring/practice_generation.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.practice_generation module"
  - "src/learnloop/content/authoring/practice_generation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.practice_generation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps practice generation behavior inside its owning package, [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]]. Its public surface centers on `PracticeExpansionTarget`, `PracticeExpansionPlan`, `PracticeExpansionResult`, `PracticeExpansionError`, `DiagnosticPracticeTarget`, `DiagnosticPracticePlan`, `DiagnosticPracticeResult`, `build_practice_expansion_plan` and 10 more public symbols.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py) |
| Source lines | 2202 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PracticeExpansionTarget` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 46)
  - `as_dict(self) -> dict[str, Any]` (line 93; public)
- `class PracticeExpansionPlan` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 129)
  - `requested_new_items(self) -> int` (line 133; public)
  - `as_dict(self) -> dict[str, Any]` (line 136; public)
- `class PracticeExpansionResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 156)
  - `as_dict(self) -> dict[str, Any]` (line 169; public)
- `class PracticeExpansionError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 180)
- `class DiagnosticPracticeTarget` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 185)
  - `as_dict(self) -> dict[str, Any]` (line 205; public)
- `class DiagnosticPracticePlan` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 229)
  - `requested_new_items(self) -> int` (line 233; public)
  - `as_dict(self) -> dict[str, Any]` (line 236; public)
- `class DiagnosticPracticeResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 244)
  - `as_dict(self) -> dict[str, Any]` (line 256; public)
- `build_practice_expansion_plan(vault: LoadedVault, repository: Repository, *, subjects: list[str] | None=None, target_items_per_lo: int=5, max_new_per_lo: int=3, max_los: int | None=None, focus_concepts: list[str] | None=None, learning_object_ids: list[str] | None=None, mode_mix: dict[str, int] | None=None, require_completed_probe: bool=True, exclude_item_ids: set[str] | None=None, force_named_targets: bool=True) -> PracticeExpansionPlan` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 271)
- `build_diagnostic_practice_plan(vault: LoadedVault, repository: Repository, *, learning_object_id: str | None=None, max_needs: int=3, clock: Clock | None=None) -> DiagnosticPracticePlan` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 441)
- `generate_diagnostic_practice_proposal(root: Path, codex_client: AIProviderClient, *, learning_object_id: str | None=None, max_needs: int=3, extra_instructions: str | None=None, codex_revision: str | None=None) -> DiagnosticPracticeResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 646)
- `generate_post_probe_practice_proposal(root: Path, codex_client: AIProviderClient, *, subjects: list[str] | None=None, target_items_per_lo: int=5, max_new_per_lo: int=3, max_los: int | None=None, focus_concepts: list[str] | None=None, focus_facets: list[str] | None=None, extra_instructions: str | None=None, codex_revision: str | None=None, learning_object_ids: list[str] | None=None, mode_mix: dict[str, int] | None=None, require_completed_probe: bool=True, source_refs: list[dict[str, Any]] | None=None) -> PracticeExpansionResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 755)
- `build_goal_practice_plan(vault: LoadedVault, repository: Repository, goal, *, target_items_per_lo: int=5, max_new_per_lo: int=3) -> tuple[PracticeExpansionPlan, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 848) — Expansion plan covering a goal's scope, sized by *practicable* supply.
- `generate_goal_practice_proposal(root: Path, codex_client: AIProviderClient, *, goal_id: str, target_items_per_lo: int=5, max_new_per_lo: int=3, extra_instructions: str | None=None, codex_revision: str | None=None) -> PracticeExpansionResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 887) — Generate Practice Items that populate an active goal's scope.
- `class LeakageBlock` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 979) — One generated practice item blocked by the held-out leakage gate (§8.5).
  - `as_dict(self) -> dict[str, Any]` (line 986; public)
- `class CrossSourcePracticeResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 995)
  - `as_dict(self) -> dict[str, Any]` (line 1002; public)
- `generate_cross_source_practice_proposal(root: Path, codex_client: AIProviderClient, *, subjects: list[str] | None=None, target_items_per_lo: int=5, max_new_per_lo: int=3, max_los: int | None=None, focus_concepts: list[str] | None=None, focus_facets: list[str] | None=None, learning_object_ids: list[str] | None=None, max_spans_per_item: int=4, extra_instructions: str | None=None, codex_revision: str | None=None) -> CrossSourcePracticeResult` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1100) — Assessment-blueprint-driven, multi-source practice generation with HARD leakage controls (spec §8.5, ING M8).
- `ability_logit(ability: float | None) -> float` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2120)
- `success_band_difficulty(ability_logit: float, success_band: tuple[float, float], *, discrimination: float, difficulty_scale: float, difficulty_floor: float=0.0, min_band_width: float=0.0) -> tuple[float, float]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2148) — ``(easier, harder)`` authored-difficulty band spanning a target success interval.

### Module constants

- `_CONSTRUCTED_RESPONSE_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1688)
- `_BLUEPRINT_SPREAD_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1704)
- `_CONJUNCTIVE_ITEM_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1731)
- `_DISCRIMINATION_PROFILE_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1759)
- `_LADDERED_STEM_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1780)
- `_ERROR_HUNT_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1799)
- `_CONTRAST_PAIR_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1819)
- `_CONTRACT_CELL_RULE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1848)
- `_TEACH_BACK_GENERATION_GUIDANCE` ([src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1864)

## Internal implementation anchors

- `_stale_repeat_failure_need(vault: LoadedVault, repository: Repository, need: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 530) — Lazily retire repeat-failure needs whose streak has since resolved.
- `_stale_tutor_gap_need(vault: LoadedVault, repository: Repository, need: dict[str, Any], *, now: datetime) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 577) — Lazily retire tutor_gap_declaration needs (spec §3 G3).
- `_attempt_failed(attempt: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 632) — Failure predicate mirroring ``question_signal._attempt_failed`` (§3 G3).
- `_blueprint_shaping(vault: LoadedVault, learning_object) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1011) — Task-family / capability distribution from the LO's assessment blueprints.
- `_cross_source_instructions(plan: PracticeExpansionPlan, context_by_lo: dict[str, list[dict[str, Any]]], shaping_by_lo: dict[str, list[dict[str, Any]]], *, extra_instructions: str | None, focus_facets: list[str] | None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1038)
- `_validate_mode_mix(mode_mix: dict[str, int] | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1229)
- `_validate_named_learning_objects(vault: LoadedVault, repository: Repository, learning_object_ids: list[str], *, require_completed_probe: bool=True, contract_backed: set[str] | None=None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1239) — Named --los targets must exist, be active, and have a completed probe.
- `_contrast_pair_requests_by_facet(vault: LoadedVault, repository: Repository) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1281) — Canonical facet id -> the A4 authoring requests that name it (Meas §3.A4).
- `_contrast_pair_requests_for(by_facet: Mapping[str, list[dict[str, Any]]], learning_object: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1318) — The requests this LO can discharge: those naming a facet its blueprints use.
- `class _RungGate` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1340) — Deterministic rung admission over persisted proposal rows (row_transform seam): a generated item that overshoots or contradicts its target waypoint is forced off the auto-apply route; the diagnostics surface on the result.
- `_mode_mix_compliance(plan: PracticeExpansionPlan, mode_mix: dict[str, int], proposal_items: list[dict[str, Any]]) -> tuple[list[str], list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1537) — Check the persisted proposal against the requested per-LO mode counts.
- `_active_practice_item_counts(vault: LoadedVault, repository: Repository, *, exclude_item_ids: set[str] | None=None) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1577)
- `_blueprint_components(learning_object) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1596) — The distinct (facet, capability, role) requirements of an LO's blueprints.
- `_active_surface_families(vault: LoadedVault, repository: Repository) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1636) — Surface families already in use per LO, so a batch cannot re-run them.
- `_active_evidence_facet_unions(vault: LoadedVault, repository: Repository) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1652) — Canonical facet vocabulary available to each Learning Object.
- `_target_subjects(plan: PracticeExpansionPlan, subjects: list[str] | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1680)
- `_ladder_capabilities(target: 'PracticeExpansionTarget') -> int` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1880) — How many distinct capabilities this target's contract spans (Meas §3.A2).
- `_practice_expansion_instructions(plan: PracticeExpansionPlan, *, extra_instructions: str | None, focus_facets: list[str] | None=None, mode_mix: dict[str, int] | None=None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1901)
- `_diagnostic_practice_instructions(plan: DiagnosticPracticePlan, *, extra_instructions: str | None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1965)
- `_diagnostic_item_ids_by_need(plan: DiagnosticPracticePlan, proposal_items: list[dict[str, Any]]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 1993)
- `_is_diagnostic_practice_item_row(item: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2019)
- `_repair_rationales_from_focus(diagnostic_focus: dict[str, Any] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2031)
- `_repair_rationales(repository: Repository, attempt_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2055) — Pull the grader's repair-suggestion rationales for the source attempt.
- `_diagnostic_source_refs(plan: DiagnosticPracticePlan) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2087)
- `_ability_estimate(facet_means: dict[str, float], mastery_mean: float | None) -> float` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2107) — Best available ability estimate (probability scale) for difficulty targeting.
- `_logit(probability: float) -> float` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2124)
- `_difficulty_for_success(ability_logit: float, target_success: float, *, discrimination: float, difficulty_scale: float) -> float` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2129) — Authored difficulty in [0,1] whose IRT ``b`` yields ``target_success`` at ``ability_logit``.
- `_guard_degenerate_band(band: tuple[float, float], *, min_band_width: float) -> tuple[float, float]` ([source](../../../../../../../src/learnloop/content/authoring/practice_generation.py), line 2181) — Restore width to a band that clamped to ``[x, x]``; never re-centre it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]] — imports `DiagnosticPracticePlan`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `DiagnosticPracticePlan`, `PracticeExpansionError`, `build_diagnostic_practice_plan`, `build_goal_practice_plan`, `build_practice_expansion_plan`, `generate_diagnostic_practice_proposal`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `PracticeExpansionError`, `PracticeExpansionPlan`, `_RungGate`, `build_practice_expansion_plan`; statically calls `PracticeExpansionPlan`, `_RungGate`, `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `PracticeExpansionError`, `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`; statically calls `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `PracticeExpansionError`, `build_practice_expansion_plan`; statically calls `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PracticeExpansionError`, `ability_logit`, `generate_diagnostic_practice_proposal`, `success_band_difficulty`; statically calls `ability_logit`, `generate_diagnostic_practice_proposal`, `success_band_difficulty`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `PracticeExpansionError`, `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`; statically calls `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `SELECTED_RESPONSE_PATTERNS`, `SelectedResponseGate`, `build_instrument_gates`, `chain_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `commission_plan`; calls `commission_plan`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`; calls `build_cross_source_spans`, `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `PRACTICE_GENERATION_PROMPT_VERSION`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `generate_authoring_proposal`; calls `generate_authoring_proposal`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `GateDiagnostic`; calls `GateDiagnostic`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `RungTarget`, `TASK_FEATURE_SCHEMA_SLUG`, `capability_rung`, `rung_float_proxies`, `select_rung`, `validate_item_against_rung`; calls `capability_rung`, `rung_float_proxies`, `select_rung`, `validate_item_against_rung`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `commission_contrast_pairs`; calls `commission_contrast_pairs`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `current_same_facet_failure_streak`, `current_same_item_failure_streak`; calls `current_same_facet_failure_streak`, `current_same_item_failure_streak`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`, `resolve_goal_scope`; calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_states_for_lo`; calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`, `display_mastery`; calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `LEGACY_UNMAPPED`, `ensure_capability_alias_registry`, `map_capability`; calls `ensure_capability_alias_registry`, `map_capability`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contract_commissioning.py](../../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_contract_backed_lo_waives_the_completed_probe_gate`
  - `test_deferred_cells_ride_on_the_plan_not_the_prompt`
  - `test_deferred_only_lo_keeps_the_completed_probe_gate`
  - `test_gate_keeps_single_rung_behaviour_on_a_legacy_learning_object`
  - `test_legacy_learning_object_keeps_the_mastery_band_rung`
  - `test_lo_without_contract_cells_keeps_the_completed_probe_gate`
  - `test_max_los_truncates_by_queue_priority`
  - `test_plan_rung_follows_the_contract_not_the_mastery_band`
- [tests/test_difficulty_band_guards.py](../../../../../../../tests/test_difficulty_band_guards.py) — direct import
  - `test_diagnostic_plan_band_is_never_degenerate`
  - `test_guard_is_inert_at_zero_min_width`
  - `test_guard_never_touches_a_band_with_width`
  - `test_guard_widens_a_ceiling_collapsed_band_downward`
  - `test_guard_widens_a_floor_collapsed_band_away_from_the_clamp`
  - `test_probe_band_collapses_unguarded_and_stays_boundary_centred_guarded`
  - `test_promotion_band_unchanged_at_ordinary_mastery`
- [tests/test_facet_diagnostics_v03.py](../../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_diagnostic_plan_carries_grader_repair_rationales`
  - `test_need_target_builder_freezes_structured_repair_focus`
  - `test_subthreshold_noisy_item_creates_single_facet_generation_need_and_logs_slate`
- [tests/test_goal_scope_material.py](../../../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_goal_population_never_authors_for_an_unmeasurable_concept`
  - `test_goal_population_targets_only_the_measurable_concepts`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_goal_population_handler_generates_and_applies_practice`
- [tests/test_persona_gate.py](../../../../../../../tests/test_persona_gate.py) — direct import
  - `test_b2_license_from_another_generator_family_stays_advisory`
  - `test_b2_license_promotes_plain_practice_advisory_failure_to_hard`
  - `test_b2_lookup_fault_is_not_reported_as_an_unvalidated_pass`
  - `test_b2_never_run_is_recorded_as_no_run`
  - `test_gate_precision_becomes_available_once_labels_are_supplied`
  - `test_gate_precision_reports_no_producer_without_blinded_ground_truth`
  - `test_live_generate_diagnostics_blocks_an_undiscriminating_diagnostic`
  - `test_live_generate_diagnostics_ships_a_discriminating_diagnostic`
  - `test_live_plain_practice_item_is_flagged_but_shipped`
  - `test_live_route_abstains_when_there_is_nothing_to_plant`
- [tests/test_practice_item_quality_gates.py](../../../../../../../tests/test_practice_item_quality_gates.py) — direct import
  - `test_constructed_response_surfaces_pass`
  - `test_gate_leaves_other_row_types_alone`
  - `test_selected_response_surfaces_are_blocked`
- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
  - `test_generated_practice_never_reproduces_held_out_wording`
- [tests/test_reader_progression.py](../../../../../../../tests/test_reader_progression.py) — direct import
  - `test_post_probe_generation_passes_and_persists_reader_source_refs`
  - `test_practice_plan_uses_blueprint_facets_before_first_item`
- [tests/test_recall_coverage_interventions.py](../../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_diagnostic_generation_stales_resolved_repeat_failure_need`
- [tests/test_tutor_promotion_w2.py](../../../../../../../tests/test_tutor_promotion_w2.py) — direct import
  - `test_gap_need_goes_stale_after_ttl`
  - `test_gap_need_goes_stale_when_facets_succeed`
  - `test_gap_need_survives_before_ttl_without_success`
  - `test_non_gap_need_unaffected_by_gap_staleness`

## Modification guidance

- Change practice generation policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/practice_generation.py](../../../../../../../src/learnloop/content/authoring/practice_generation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
