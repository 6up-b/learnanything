---
title: "learnloop.ops.doctor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/doctor.py"
source_paths:
  - "src/learnloop/ops/doctor.py"
source_commit: "9350e078139bf2a4b0d5ad67af60af1042d924f6"
source_commit_timestamp: "2026-09-23T18:50:00-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.doctor module"
  - "src/learnloop/ops/doctor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.doctor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps doctor behavior inside its owning package, [[Reference/Modules/learnloop/ops/_package|learnloop.ops]]. Its public surface centers on `HealthIssue`, `DoctorReport`, `run_doctor`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py) |
| Source lines | 2251 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9350e078139bf2a4b0d5ad67af60af1042d924f6` |
| Commit timestamp | `2026-09-23T18:50:00-04:00` |

## Public API

- `class HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 59)
  - `as_dict(self) -> dict[str, object]` (line 67; public)
- `class DoctorReport` ([source](../../../../../../src/learnloop/ops/doctor.py), line 81)
  - `clean(self) -> bool` (line 98; public)
  - `error_count(self) -> int` (line 102; public)
  - `warning_count(self) -> int` (line 106; public)
  - `as_dict(self) -> dict[str, object]` (line 109; public)
- `run_doctor(root: Path, *, fix_state: bool=False, ai: bool=False, ai_provider: str | None=None) -> DoctorReport` ([source](../../../../../../src/learnloop/ops/doctor.py), line 126)

### Module constants

- `WAL_SIZE_WARNING_BYTES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 687)
- `_DEPRECATED_STATE_TABLES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 767)
- `_REACHABILITY_CODES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2101)
- `_REACHABILITY_HEADLINE` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2108)
- `_REACHABILITY_ACTION` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2115)

## Internal implementation anchors

- `_requested_ai_runtimes(vault_root: Path, config: LearnLoopConfig, *, ai: bool, ai_provider: str | None) -> tuple[AIRuntimeReport | None, AIRuntimeReport | None]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 212) — ``(codex_runtime, ai_runtime)`` for ``doctor --ai``; both None otherwise.
- `_attach_state_database(paths: VaultPaths, issues: list[HealthIssue], *, fix_state: bool) -> tuple[Repository | None, set[str]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 238) — The state database (read-only unless fixing) and its table names, or ``(None, set())``.
- `_merge_mvp06_facet_recall_aliases(vault: LoadedVault, repository: Repository, database_tables: set[str], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 266) — Under ``--fix``, fold aliased per-LO facet recall rows on mvp-0.6 vaults.
- `_check_database_state(vault: LoadedVault, repository: Repository, database_tables: set[str], issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 292) — Checks of derived learner state; each runs only when its tables exist.
- `_check_database_contracts(vault: LoadedVault, repository: Repository, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 317) — Checks of diagnostic proposals, goal-contract drift, canonical facet state and pre-practice identifiability; each runs only when its tables exist.
- `_load_config_for_doctor(root: Path, issues: list[HealthIssue]) -> LearnLoopConfig | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 347)
- `_check_retired_config(root: Path, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 359) — Migration warning for retired config blocks (knowledge-model §8.3/§15).
- `_check_layout(paths: VaultPaths, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 484)
- `class _ParsedYamlFiles` ([source](../../../../../../src/learnloop/ops/doctor.py), line 499) — Each vault YAML file parsed once per doctor run.
- `_check_schema_versions(paths: VaultPaths, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 525)
- `_check_yaml_schema(path: Path, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles, supported: set[int]=frozenset({1})) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 540)
- `_check_unknown_yaml_keys(paths: VaultPaths, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 565)
- `_check_unknown_yaml_keys_for_file(path: Path, model: type[BaseModel], issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 593)
- `_check_unknown_mapping_keys(data: dict[str, Any], model: type[BaseModel], issues: list[HealthIssue], *, path: Path, location: str) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 609)
- `_iter_model_children(value: Any, annotation: Any, location: str) -> list[tuple[str, type[BaseModel], dict[str, Any]]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 636)
- `_model_from_annotation(annotation: Any) -> type[BaseModel] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 671)
- `_check_storage(paths: VaultPaths, issues: list[HealthIssue]) -> DatabaseStorage | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 690) — Warn about filesystems WAL cannot share memory on, and an oversized WAL.
- `_check_sqlite(paths: VaultPaths, issues: list[HealthIssue]) -> bool` ([source](../../../../../../src/learnloop/ops/doctor.py), line 727)
- `_database_tables(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 757)
- `_check_deprecated_tables(repository: Repository, database_tables: set[str], issues: list[HealthIssue]) -> dict[str, int]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 774) — Report read-only telemetry before deprecated state is detached.
- `_has_tables(available: set[str], *required: str) -> bool` ([source](../../../../../../src/learnloop/ops/doctor.py), line 825)
- `_recover_apply_intents(paths: VaultPaths, repository: Repository | None, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 829) — Complete any write-ahead apply intent left mid-flight (§10.2 recovery).
- `_from_loader_issue(issue: DoctorIssue) -> HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 882)
- `_check_references(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 891)
- `_check_source_sets(vault: LoadedVault, repository: Repository | None, database_tables: set[str], issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 928) — Validate source-set membership (spec_source_ingestion_v2 §4.3).
- `_check_sql_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 978)
- `_check_derived_state_rebuild_marker(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1026)
- `_check_invalid_proposals(repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1052)
- `_check_difficulty_calibration(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1066) — Surface items whose IRT difficulty ``b`` looks miscalibrated (spec §7.4).
- `_check_bad_item_suspicion(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1077)
- `_check_criterion_facet_maps(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1101)
- `_check_mvp07_canonical_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1187) — Guard against mixed/inconsistent keying on an mvp-0.7 vault (KM §15).
- `_mvp07_facet_severity(vault: LoadedVault) -> Severity` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1222) — Facet-registry issues are errors on mvp-0.7 vaults, warnings on legacy.
- `_check_registered_facets(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1234)
- `_check_facet_contract_completeness(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1285) — Facet semantic-contract completeness (knowledge-model §3.2).
- `_check_blueprints_and_criteria(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1326) — Validate LO blueprints and rubric criterion targets (§5.1/§7.2).
- `_check_instrument_contracts(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1387) — Meas §3.A2-§3.A5 contracts, checked on the VAULT (plan item 6.4).
- `_check_laddered_stems(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1577) — Meas §3.A2: a stem's parts must actually span the capability ladder.
- `_instrument_normalizer()` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1634)
- `_instrument_expected_text(item: Any) -> str` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1640)
- `_check_criterion_target_dags(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1647)
- `_first_dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1709) — Return one cycle as an id path, or None if the graph is a DAG.
- `_check_facet_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1738)
- `_check_registry_near_duplicate_facets(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1790) — Post-append near-duplicate facet pass over the whole registry (§14).
- `_check_concept_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1813)
- `_concept_similarity(left_id: str, left: Any, right_id: str, right: Any) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1844)
- `_concept_surfaces(concept_id: str, concept: Any) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1854)
- `_normalized_surface(value: str) -> str` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1859)
- `_concept_merge_affected_refs(vault: LoadedVault, canonical_id: str, duplicate_id: str) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1863)
- `_facet_merge_details(learning_object_id: str, left: str, right: str, score: float, *, item_ids_by_lo_facet: dict[tuple[str, str], list[str]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1890)
- `_check_learning_object_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1917)
- `_check_duplicate_diagnostic_proposals(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1947)
- `_facet_similarity(left: str, right: str) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1997)
- `_text_similarity(left: str | None, right: str | None) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2014)
- `_text_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2022)
- `_facet_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2028)
- `_check_pre_first_practice_identifiability(vault: LoadedVault, repository: Repository, issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2034) — Pre-first-practice identifiability doctor check (knowledge-model §11.3).
- `_check_contract_cell_reachability(vault: LoadedVault, issues: list[HealthIssue]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2136) — Contract-cell reachability as a standing check (§5.8.2, plan item 3.1).
- `_check_contract_drift(vault, repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2198) — Surface goal terminal-contract drift (P0.4 §3): a confirmed goal whose live YAML draft fields diverge from the confirmed head.
- `_issue(severity: Severity, code: str, message: str, path: Path | None=None, *, entity_id: str | None=None, details: dict[str, Any] | None=None) -> HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2223)
- `_dedupe(issues: list[HealthIssue]) -> list[HealthIssue]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2242)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `run_doctor`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `runtime_for_provider`; calls `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `declares_error_count`; calls `declares_error_count`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `recover_apply_intents`; calls `recover_apply_intents`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`; calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `checkpoint_wal`; calls `checkpoint_wal`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`, `discover_migrations`; calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/storage|learnloop.db.storage]] — imports `DatabaseStorage`, `inspect_database_storage`; calls `inspect_database_storage`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `detect_contract_drift`; calls `detect_contract_drift`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/calibration|learnloop.learner.calibration]] — imports `difficulty_miscalibration_flags`; calls `difficulty_miscalibration_flags`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `is_valid_capability`; calls `is_valid_capability`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`; calls `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `migrate_vault`; calls `migrate_vault`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `UNSERVABLE_REMEDIES`, `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `StateSyncResult`, `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RelationsFile`, `learning_object_facet_union`, `recipe_components`; calls `learning_object_facet_union`, `recipe_components`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml_data`; calls `read_yaml_data`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `difflib`, `os`, `pathlib`, `sqlite3`, `tomllib`, `types`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_apply_write_ahead.py](../../../../../../tests/test_apply_write_ahead.py) — direct import
  - `test_doctor_fix_recovers_mid_flight_intent`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_detect_contract_drift_and_doctor_surface`
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
  - `test_doctor_does_not_flag_a_well_calibrated_item`
  - `test_doctor_surfaces_miscalibration_warning`
- [tests/test_codex_runtime.py](../../../../../../tests/test_codex_runtime.py) — direct import
  - `test_doctor_only_checks_provider_health_when_explicitly_requested`
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_doctor_reports_concept_merge_candidates`
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_doctor_groups_cells_by_learning_object_and_verdict`
  - `test_doctor_reports_unreachable_cells_as_review_warnings`
  - `test_legacy_vault_without_contracts_reports_empty_not_perfect`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_doctor_catches_a_one_sided_pair_binding`
  - `test_the_doctor_is_silent_on_a_well_formed_pair`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_the_doctor_catches_a_blind_profile_on_a_hand_authored_item`
  - `test_the_doctor_is_silent_on_a_well_formed_profile`
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_clean_fresh_vault`
  - `test_doctor_does_not_merge_opposite_registered_facet_contracts`
  - `test_doctor_does_not_merge_unrelated_equal_length_facet_ids`
  - `test_doctor_escalates_nonempty_deprecated_tables_without_mutating_them`
  - `test_doctor_fix_state_merges_registered_facet_alias_state`
  - `test_doctor_flags_bad_item_suspicion_after_evidence_gate`
  - `test_doctor_parses_each_yaml_file_once`
  - `test_doctor_report_is_the_same_with_and_without_the_parse_cache`
  - `test_doctor_reports_and_fixes_missing_derived_state`
  - `test_doctor_resolves_legacy_error_event_through_causal_taxonomy`
  - `test_doctor_surfaces_likely_facet_merge_candidates`
  - `test_doctor_validates_criterion_facet_maps`
  - `test_doctor_warns_for_legacy_codex_and_retired_settings`
  - `test_doctor_warns_on_duplicate_diagnostic_practice_proposals`
  - `test_doctor_warns_on_duplicate_learning_objects`
  - `test_doctor_warns_on_unaligned_error_event_type`
  - `test_doctor_warns_on_unknown_yaml_key_that_looks_like_typo`
  - `test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker`
  - `test_plain_doctor_does_not_create_a_missing_database`
  - `test_plain_doctor_reports_an_unreadable_database_without_rewriting_it`
  - `test_plain_doctor_reports_pre_044_migrations_without_touching_database`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_the_doctor_catches_a_hand_authored_error_hunt_the_gates_never_saw`
  - `test_the_doctor_is_silent_on_a_well_formed_error_hunt`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
  - `test_fresh_vault_has_no_retired_config_warning`
  - `test_retired_cross_lo_propagation_config_warns`
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
  - `test_pre_first_practice_doctor_watermark`
- [tests/test_km1_doctor.py](../../../../../../tests/test_km1_doctor.py) — direct import
  - `test_valid_blueprint_and_criterion_targets_pass`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_the_doctor_is_silent_on_a_real_ladder`
  - `test_the_doctor_warns_when_a_stem_fills_only_one_column`
- [tests/test_source_sets.py](../../../../../../tests/test_source_sets.py) — direct import
  - `test_doctor_flags_source_set_issues`
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_read_only_reports_work_in_a_read_only_vault`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_doctor_reports_wal_size_and_warns_when_it_is_large`
  - `test_doctor_warns_when_the_vault_is_on_a_network_mount`

## Modification guidance

- Make changes here when the responsibility remains doctor within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
