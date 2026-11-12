---
title: "learnloop.ops.doctor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/doctor.py"
source_paths:
  - "src/learnloop/ops/doctor.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps doctor behavior inside its owning package, [[Reference/Modules/learnloop/ops/_package|learnloop.ops]]. Its public surface centers on `HealthIssue`, `DoctorReport`, `run_doctor`, `review_nominator`, `concept_merge_candidate_pairs`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py) |
| Source lines | 2956 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 77)
  - `as_dict(self) -> dict[str, object]` (line 85; public)
- `class DoctorReport` ([source](../../../../../../src/learnloop/ops/doctor.py), line 99)
  - `clean(self) -> bool` (line 119; public)
  - `error_count(self) -> int` (line 123; public)
  - `warning_count(self) -> int` (line 127; public)
  - `as_dict(self) -> dict[str, object]` (line 130; public)
- `run_doctor(root: Path, *, fix_state: bool=False, ai: bool=False, ai_provider: str | None=None) -> DoctorReport` ([source](../../../../../../src/learnloop/ops/doctor.py), line 148)
- `review_nominator(vault: LoadedVault) -> Any` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2408) — Slice 2 T5 stored-vector nominator for the doctor's cosine columns, or None.
- `concept_merge_candidate_pairs(vault: LoadedVault) -> list[tuple[str, str, float, bool]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2507) — Doctor's lexical concept-duplicate pairs: (left, right, similarity, strong_alias).

### Module constants

- `STALE_POST_ATTEMPT_JOB_HOURS` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 666)
- `WAL_SIZE_WARNING_BYTES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 1131)
- `_DEPRECATED_STATE_TABLES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 1247)
- `_REACHABILITY_CODES` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2806)
- `_REACHABILITY_HEADLINE` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2813)
- `_REACHABILITY_ACTION` ([src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py), line 2820)

## Internal implementation anchors

- `_check_model_routes(config: LearnLoopConfig, repository: Repository, issues: list[HealthIssue]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 256) — Each model route's last completed call and failures since, from receipts.
- `_check_codex_pins(root: Path, config: LearnLoopConfig, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 277) — Plan-first transport T1: every learnloop.toml setting that still names a Codex profile.
- `_check_chatgpt_plan_routes(root: Path, config: LearnLoopConfig, issues: list[HealthIssue], *, machine_state: bool=False) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 302) — Warn when a route uses a ``chatgpt_plan`` profile that cannot serve it.
- `_requested_ai_runtimes(vault_root: Path, config: LearnLoopConfig, *, ai: bool, ai_provider: str | None) -> tuple[AIRuntimeReport | None, AIRuntimeReport | None]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 364) — ``(codex_runtime, ai_runtime)`` for ``doctor --ai``; both None otherwise.
- `_attach_state_database(paths: VaultPaths, issues: list[HealthIssue], *, fix_state: bool) -> tuple[Repository | None, set[str]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 390) — The state database (read-only unless fixing) and its table names, or ``(None, set())``.
- `_merge_mvp06_facet_recall_aliases(vault: LoadedVault, repository: Repository, database_tables: set[str], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 418) — Under ``--fix``, fold aliased per-LO facet recall rows on mvp-0.6 vaults.
- `_check_database_state(vault: LoadedVault, repository: Repository, database_tables: set[str], issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 444) — Checks of derived learner state; each runs only when its tables exist.
- `_book_title(repository: Repository, source_id: str) -> str` ([source](../../../../../../src/learnloop/ops/doctor.py), line 474)
- `_check_reread_state(vault: LoadedVault, repository: Repository, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 479) — Re-read safety (docs/reviews/reread-safety.md): what reading a book again can leave behind.
- `_check_source_block_fts(repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 639) — Slice 2 T6: the DERIVED keyword index matches the source blocks.
- `_check_post_attempt_jobs(repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 669) — Slice 1 §11: failed and stale diagnosis/embedding jobs.
- `_check_database_contracts(vault: LoadedVault, repository: Repository, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 711) — Checks of diagnostic proposals, goal-contract drift, canonical facet state and pre-practice identifiability; each runs only when its tables exist.
- `_load_config_for_doctor(root: Path, issues: list[HealthIssue]) -> LearnLoopConfig | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 741)
- `_check_retired_config(root: Path, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 753) — Migration warning for retired config blocks (knowledge-model §8.3/§15).
- `_check_retired_keep_local(repository: Repository, database_tables: set[str], issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 899) — The per-book "Keep this book on this computer" (spec ux_learnloop_v1 §6.6, migration 198's ``source_artifacts.keep_local``) is retired (owner, 2026-10-13: sending books to an AI is fine; the opt-out was not asked for).
- `_check_layout(paths: VaultPaths, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 928)
- `class _ParsedYamlFiles` ([source](../../../../../../src/learnloop/ops/doctor.py), line 943) — Each vault YAML file parsed once per doctor run.
- `_check_schema_versions(paths: VaultPaths, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 969)
- `_check_yaml_schema(path: Path, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles, supported: set[int]=frozenset({1})) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 984)
- `_check_unknown_yaml_keys(paths: VaultPaths, issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1009)
- `_check_unknown_yaml_keys_for_file(path: Path, model: type[BaseModel], issues: list[HealthIssue], parsed_yaml: _ParsedYamlFiles) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1037)
- `_check_unknown_mapping_keys(data: dict[str, Any], model: type[BaseModel], issues: list[HealthIssue], *, path: Path, location: str) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1053)
- `_iter_model_children(value: Any, annotation: Any, location: str) -> list[tuple[str, type[BaseModel], dict[str, Any]]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1080)
- `_model_from_annotation(annotation: Any) -> type[BaseModel] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1115)
- `_check_storage(paths: VaultPaths, issues: list[HealthIssue]) -> DatabaseStorage | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1134) — Warn about a SQLite without the WAL-reset fix, filesystems WAL cannot share memory on, and an oversized WAL.
- `_check_wal_runtime(paths: VaultPaths, storage: DatabaseStorage | None, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1174)
- `_check_sqlite(paths: VaultPaths, issues: list[HealthIssue]) -> bool` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1207)
- `_database_tables(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1237)
- `_check_deprecated_tables(repository: Repository, database_tables: set[str], issues: list[HealthIssue]) -> dict[str, int]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1254) — Report read-only telemetry before deprecated state is detached.
- `_has_tables(available: set[str], *required: str) -> bool` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1305)
- `_recover_apply_intents(paths: VaultPaths, repository: Repository | None, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1309) — Complete any write-ahead apply intent left mid-flight (§10.2 recovery), and report conflicted ones.
- `_recover_facet_identity_actions(paths: VaultPaths, repository: Repository | None, database_tables: set[str], issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1381) — Finish a facet merge, undo or Library save left mid-flight (facet identity, review F4).
- `_from_loader_issue(issue: DoctorIssue) -> HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1447)
- `_check_references(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1456)
- `_check_source_sets(vault: LoadedVault, repository: Repository | None, database_tables: set[str], issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1493) — Validate source-set membership (spec_source_ingestion_v2 §4.3).
- `_check_sql_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1543)
- `_check_derived_state_rebuild_marker(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1591)
- `_check_projection_switches(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1617) — Router objective RO1 (spec §5.5): persisted due dates were derived under a switch the config no longer says.
- `_check_invalid_proposals(repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1652)
- `_check_difficulty_calibration(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1666) — Surface items whose IRT difficulty ``b`` looks miscalibrated (spec §7.4).
- `_check_bad_item_suspicion(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1677)
- `_check_criterion_facet_maps(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1701)
- `_check_mvp07_canonical_state(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1787) — Guard against mixed/inconsistent keying on an mvp-0.7 vault (KM §15).
- `_mvp07_facet_severity(vault: LoadedVault) -> Severity` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1822) — Facet-registry issues are errors on mvp-0.7 vaults, warnings on legacy.
- `_check_registered_facets(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1834)
- `_check_facet_contract_completeness(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1885) — Facet semantic-contract completeness (knowledge-model §3.2).
- `_check_blueprints_and_criteria(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1926) — Validate LO blueprints and rubric criterion targets (§5.1/§7.2).
- `_check_instrument_contracts(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 1987) — Meas §3.A2-§3.A5 contracts, checked on the VAULT (plan item 6.4).
- `_check_laddered_stems(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2177) — Meas §3.A2: a stem's parts must actually span the capability ladder.
- `_instrument_normalizer()` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2234)
- `_instrument_expected_text(item: Any) -> str` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2240)
- `_check_required_methods(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2247) — Method-explicit items (owner rule 2026-10-13).
- `_check_criterion_target_dags(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2317)
- `_first_dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2379) — Return one cycle as an id path, or None if the graph is a DAG.
- `_cosine_column(nominator: Any, recipe: str, left: str, right: str) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2416) — (details fields, message suffix) for the T5 cosine column; empty when off.
- `_check_facet_merge_candidates(vault: LoadedVault, issues: list[HealthIssue], nominator: Any=None) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2426)
- `_check_registry_near_duplicate_facets(vault: LoadedVault, issues: list[HealthIssue], nominator: Any=None) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2482) — Post-append near-duplicate facet pass over the whole registry (§14).
- `_check_concept_merge_candidates(vault: LoadedVault, issues: list[HealthIssue], nominator: Any=None) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2522)
- `_concept_similarity(left_id: str, left: Any, right_id: str, right: Any) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2549)
- `_concept_surfaces(concept_id: str, concept: Any) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2559)
- `_normalized_surface(value: str) -> str` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2564)
- `_concept_merge_affected_refs(vault: LoadedVault, canonical_id: str, duplicate_id: str) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2568)
- `_facet_merge_details(learning_object_id: str, left: str, right: str, score: float, *, item_ids_by_lo_facet: dict[tuple[str, str], list[str]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2595)
- `_check_learning_object_merge_candidates(vault: LoadedVault, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2622)
- `_check_duplicate_diagnostic_proposals(vault: LoadedVault, repository: Repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2652)
- `_facet_similarity(left: str, right: str) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2702)
- `_text_similarity(left: str | None, right: str | None) -> float` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2719)
- `_text_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2727)
- `_facet_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2733)
- `_check_pre_first_practice_identifiability(vault: LoadedVault, repository: Repository, issues: list[HealthIssue], *, fix_state: bool) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2739) — Pre-first-practice identifiability doctor check (knowledge-model §11.3).
- `_check_contract_cell_reachability(vault: LoadedVault, issues: list[HealthIssue]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2841) — Contract-cell reachability as a standing check (§5.8.2, plan item 3.1).
- `_check_contract_drift(vault, repository, issues: list[HealthIssue]) -> None` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2903) — Surface goal terminal-contract drift (P0.4 §3): a confirmed goal whose live YAML draft fields diverge from the confirmed head.
- `_issue(severity: Severity, code: str, message: str, path: Path | None=None, *, entity_id: str | None=None, details: dict[str, Any] | None=None) -> HealthIssue` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2928)
- `_dedupe(issues: list[HealthIssue]) -> list[HealthIssue]` ([source](../../../../../../src/learnloop/ops/doctor.py), line 2947)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `run_doctor`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `concept_merge_candidate_pairs`; statically calls `concept_merge_candidate_pairs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `plan_profiles`; calls `plan_profiles`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `runtime_for_provider`; calls `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `RETIRED_ROUTES`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `declares_error_count`; calls `declares_error_count`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `interrupted_actions`, `interrupted_registry_saves`, `recover_interrupted_actions`; calls `interrupted_actions`, `interrupted_registry_saves`, `recover_interrupted_actions`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `MARK_LABEL`, `held_back_readings`; calls `held_back_readings`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `carry_owed`, `finish_carry_over`, `restore_readable_revision`, `unread_current_revisions`; calls `carry_owed`, `finish_carry_over`, `restore_readable_revision`, `unread_current_revisions`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `recover_apply_intents`; calls `recover_apply_intents`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`, `CurrentKeys`, `reading_source`; calls `CitationResolver`, `CurrentKeys`, `reading_source`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`, `review_nominator`; calls `near_duplicate_facet_review`, `review_nominator`
- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `checkpoint_wal`; calls `checkpoint_wal`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `WAL_RESET_ADVISORY_URL`, `WAL_RESET_FIXED_VERSIONS_TEXT`, `linked_sqlite_version`, `wal_unavailable_reason`; calls `linked_sqlite_version`, `wal_unavailable_reason`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`, `discover_migrations`; calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/storage|learnloop.db.storage]] — imports `DatabaseStorage`, `inspect_database_storage`; calls `inspect_database_storage`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `fts_drift`; calls `fts_drift`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `detect_contract_drift`; calls `detect_contract_drift`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/calibration|learnloop.learner.calibration]] — imports `difficulty_miscalibration_flags`; calls `difficulty_miscalibration_flags`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `is_valid_capability`; calls `is_valid_capability`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`; calls `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `migrate_vault`; calls `migrate_vault`
- [[Reference/Modules/learnloop/ops/model_routes|learnloop.ops.model_routes]] — imports `FINDING_CODE`, `check_model_routes`; calls `check_model_routes`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `FINDING_CODE`, `METERED_FALLBACK_CODE`, `codex_pins`, `finding_message`, `metered_fallback_message`; calls `codex_pins`, `finding_message`, `metered_fallback_message`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches`; calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `UNSERVABLE_REMEDIES`, `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `StateSyncResult`, `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RelationsFile`, `learning_object_facet_union`, `recipe_components`; calls `learning_object_facet_union`, `recipe_components`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `method_phrase`, `method_targets`, `required_method_problems`; calls `method_phrase`, `method_targets`, `required_method_problems`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml_data`; calls `read_yaml_data`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `difflib`, `os`, `pathlib`, `sqlite3`, `tomllib`, `types`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_apply_recovery.py](../../../../../../tests/test_apply_recovery.py) — direct import
  - `test_doctor_and_the_feed_surface_a_conflicted_intent`
- [tests/test_apply_write_ahead.py](../../../../../../tests/test_apply_write_ahead.py) — direct import
  - `test_doctor_fix_recovers_mid_flight_intent`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_detect_contract_drift_and_doctor_surface`
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
  - `test_doctor_does_not_flag_a_well_calibrated_item`
  - `test_doctor_surfaces_miscalibration_warning`
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
  - `test_doctor_ignores_an_unrouted_plan_profile`
  - `test_doctor_warns_when_a_route_uses_a_plan_this_machine_cannot_serve`
- [tests/test_codex_transport_retired.py](../../../../../../tests/test_codex_transport_retired.py) — direct import
  - `test_an_old_config_naming_codex_loads_and_every_entry_refuses_it_clearly`
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_doctor_reports_concept_merge_candidates`
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_doctor_groups_cells_by_learning_object_and_verdict`
  - `test_doctor_reports_unreachable_cells_as_review_warnings`
  - `test_legacy_vault_without_contracts_reports_empty_not_perfect`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_doctor_catches_a_one_sided_pair_binding`
  - `test_the_doctor_is_silent_on_a_well_formed_pair`
- [tests/test_diagnosis_pipeline.py](../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_failed_diagnosis_backs_off_then_fails_and_leaves_the_grade`
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
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_doctor_names_a_legacy_mark_plainly`
  - `test_identity_review_a_signal_of_unknown_reading_is_named_plainly`
- [tests/test_facet_authority_rereview.py](../../../../../../tests/test_facet_authority_rereview.py) — direct import
  - `test_doctor_reports_and_settles_an_interrupted_save_with_no_reword`
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_a_facet_that_used_to_be_locked_merges_and_undoes_exactly`
  - `test_a_merge_leaves_the_vault_doctor_clean`
  - `test_doctor_reports_an_interrupted_merge_and_fix_state_finishes_it`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_retired_numeric_probability_route_loads_with_a_deprecation_note`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
  - `test_fresh_vault_has_no_retired_config_warning`
  - `test_retired_cross_lo_propagation_config_warns`
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_review_passes_gain_a_cosine_column`
  - `test_switches_return_no_nominator`
  - `test_synthesis_gate_and_facet_candidates_show_cosine_beside_jaccard`
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
  - `test_pre_first_practice_doctor_watermark`
- [tests/test_keep_local_retired.py](../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_doctor_names_books_that_still_carry_the_retired_choice`
- [tests/test_km1_doctor.py](../../../../../../tests/test_km1_doctor.py) — direct import
  - `test_valid_blueprint_and_criterion_targets_pass`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_the_doctor_is_silent_on_a_real_ladder`
  - `test_the_doctor_warns_when_a_stem_fills_only_one_column`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_model_route_health.py](../../../../../../tests/test_model_route_health.py) — direct import
  - `test_doctor_flags_a_route_whose_current_model_never_completed`
  - `test_doctor_reports_routes_in_json_and_text_and_flags_the_dead_one`
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_doctor_names_a_configured_slug_the_account_does_not_list`
  - `test_doctor_only_checks_provider_health_when_explicitly_requested`
  - `test_doctor_reports_each_pinned_codex_setting_and_fix_rewrites_it`
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_head_fixture_predecessor_to_successor_path`
- [tests/test_registry_audit.py](../../../../../../tests/test_registry_audit.py) — direct import
  - `test_a_stored_row_for_a_removed_spec_stays_readable`
  - `test_a_stored_row_of_a_removed_parameter_still_loads`
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_an_upgrade_interrupted_after_publication_is_resumed`
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_doctor_is_quiet_on_a_vault_with_fact_phrased_criteria`
  - `test_doctor_reports_method_phrased_criteria_and_malformed_required_methods`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_doctor_reports_the_e1_state_with_its_fix`
  - `test_f7_a_carry_over_that_fails_is_finished_later_never_lost`
  - `test_f7_doctor_fix_state_finishes_a_carry_over_left_owed`
- [tests/test_retired_config_keys_load.py](../../../../../../tests/test_retired_config_keys_load.py) — direct import
  - `test_doctor_still_names_the_retired_lock_settings`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_retired_proof_check_route_is_ignored_and_reported`
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_a_delete_never_removes_another_blocks_index_row`
- [tests/test_source_sets.py](../../../../../../tests/test_source_sets.py) — direct import
  - `test_doctor_flags_source_set_issues`
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_affected_sqlite_leaves_databases_in_rollback_mode_and_doctor_says_why`
  - `test_fixed_sqlite_switches_to_wal_and_doctor_is_quiet`
  - `test_read_only_reports_explain_a_read_only_vault_without_wal_files`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_doctor_reports_wal_size_and_warns_when_it_is_large`
  - `test_doctor_warns_when_the_vault_is_on_a_network_mount`
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_fix_content_dry_run_lists_the_edits_and_writes_nothing`
  - `test_fix_content_keeps_a_self_dependency_because_removing_it_changes_failure_attribution`
  - `test_fix_content_removes_invalid_entries_and_keeps_the_rest_of_the_file`
  - `test_normalize_keeps_only_sibling_criterion_dependencies`

## Modification guidance

- Make changes here when the responsibility remains doctor within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/doctor.py](../../../../../../src/learnloop/ops/doctor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
