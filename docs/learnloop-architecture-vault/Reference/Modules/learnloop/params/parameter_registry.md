---
title: "learnloop.params.parameter_registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/params/parameter_registry.py"
source_paths:
  - "src/learnloop/params/parameter_registry.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.params"
layer: "domain"
concepts:
  - "Learning System"
  - "Configuration"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.params.parameter_registry module"
  - "src/learnloop/params/parameter_registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-params"
---

# `learnloop.params.parameter_registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/params/_package|learnloop.params]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.params.parameter_registry` exists within [[Reference/Modules/learnloop/params/_package|learnloop.params]] to own the behavior summarized by its module contract: P0.5 calibration-status parameter registry (spec_p0_measurement_correctness §6).

The authoritative system-level explanation remains in [[Learning System]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py) |
| Source lines | 3571 |
| Owning package | [[Reference/Modules/learnloop/params/_package|learnloop.params]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ParameterSpec` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 75)
- `register(spec: ParameterSpec) -> ParameterSpec` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 97)
- `classify_config_path(path: str) -> _ConfigRule | None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 2959)
- `config_numeric_leaves(config: LearnLoopConfig | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 2974) — Every numeric leaf of the ``LearnLoopConfig`` pydantic tree, keyed by dotted path.
- `module_numeric_constants() -> list[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3024) — Module-level UPPERCASE numeric constants across the §2.1 module inventory, as ``module:CONSTANT`` paths.
- `tagged_decision_constants() -> list[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3048) — Module constants carrying the ``# decision parameter`` breadcrumb comment, as ``module:CONSTANT`` paths (the drift cross-check surface of §2.3).
- `class ResolutionContext` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3072)
- `resolve_effective(spec: ParameterSpec, ctx: ResolutionContext) -> tuple[Any, str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3115) — Return (effective_value, source).
- `decision_specs() -> list[ParameterSpec]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3233)
- `refresh(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3237) — Rebuild the per-vault ``parameter_registry`` projection from the code definition + resolved effective values.
- `set_promotion_evidence_id(repository: Repository, path: str, evidence_id: str | None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3316) — Persist the ``promotion_evidence_id`` column for a registry row.
- `freeze_manifest(vault: LoadedVault, repository: Repository, *, algorithm_version: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3341) — Freeze the immutable per-algorithm-version manifest of all decision parameters' effective value-hash/status/lifecycle/source.
- `record_bind(repository: Repository, path: str, context: dict[str, Any], *, observation_ref: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3390) — Log that a dormant guardrail actually fired (§6).
- `class AuditReport` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3411)
  - `failures(self) -> list[str]` (line 3426; public) — The failure categories (name) that are non-empty.
  - `clean(self) -> bool` (line 3445; public) — Ordinary audit cleanliness: no failures.
  - `release_clean(self) -> bool` (line 3452; public) — Strict release-gate cleanliness: clean AND zero pending coverage certificates.
  - `as_dict(self) -> dict[str, Any]` (line 3458; public)
- `audit(vault: LoadedVault | None=None, repository: Repository | None=None) -> AuditReport` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3473) — Run the decision-parameter audit.

### Module constants

- `PLANTED_LEARNER_GATE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 70)
- `PLANTED_MISGRADE_GATE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 71)
- `REGISTRY` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 94)
- `MODULE_INVENTORY` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 106)
- `MODULE_IMPORTS` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 296)
- `_CONFIG_RULES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 1562)
- `_CATCHALL_RULE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 2956)
- `_MODULE_ATTR_CACHE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 3092)
- `CATCHALL_SNAPSHOT` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 3155)
- `BOOLEAN_DECISION_LEAVES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 3189)
- `BOOLEAN_STRUCTURAL_LEAVES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 3194)
- `ENUM_DECISION_LEAVES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 3201)

## Internal implementation anchors

- `_reg_const(path: str, param_class: ParamClass, *, kind: Kind='decision', owner: str, rationale: str, lifecycle: Lifecycle='active', status: Status='heuristic', bind_site: str | None=None, gate: str | None=PLANTED_LEARNER_GATE) -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 302)
- `class _ConfigRule` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1537)
- `_exact(*paths: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1548)
- `_prefix(*prefixes: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1553)
- `_suffix(*suffixes: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1557)
- `_is_number(value: Any) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 2970)
- `_module_path(rel: str) -> Path` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3008)
- `_numeric_ast(node: ast.AST) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3012)
- `_resolve_config_value(path: str, config: LearnLoopConfig) -> Any` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3078)
- `_resolve_module_constant(path: str) -> Any` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3095)
- `_freeze_catchall_rule() -> frozenset[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3135) — Snapshot the config leaves the broad decision-namespace catch-all currently owns, then rebind the rule to match only that explicit set (F6).
- `_register_config_path(path: str) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3158) — Register one config leaf from its classification rule.
- `_build_config_specs() -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 3206)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `module`; statically calls `_resolve_config_value`, `audit`, `refresh`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `module`; statically calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `module`; statically calls `set_promotion_evidence_id`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `module`; statically calls `record_bind`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `module`; statically calls `record_bind`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`; calls `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `ast`, `dataclasses`, `importlib`, `json`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]], [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]], [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_configured_ad_price_is_a_classified_config_leaf`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_the_owner_defaults_of_2026_10_19`
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_every_new_key_is_a_classified_config_leaf`
- [tests/test_architecture.py](../../../../../../tests/test_architecture.py) — direct import
  - `test_runtime_constructed_module_references_resolve`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_mvp037_is_one_constant_after_mvp036`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_mvp038_is_one_constant_after_mvp037`
- [tests/test_constraint_engine.py](../../../../../../tests/test_constraint_engine.py) — direct import
  - `test_fatigue_slack_param_is_registered_dormant_and_monitored`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_switch_is_on_by_default_classified_and_needs_the_curriculum_and_rw7b`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f13_the_check_dates_follow_the_vaults_dl2_parameters`
- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_figure_wait_successor.py](../../../../../../tests/test_figure_wait_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f9_the_grounding_cap_is_registered_and_audited`
- [tests/test_followups_batch6_power_probe_cache.py](../../../../../../tests/test_followups_batch6_power_probe_cache.py) — direct import
  - `test_the_window_is_a_registered_keep_bound`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_reviews_lists_quarantined_then_adjudicate_clears_and_receipt`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_mvp042_is_one_constant_after_mvp041_and_the_latest`
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key`
- [tests/test_ih3_learner_preferences.py](../../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_the_switch_is_in_the_registry_and_the_default_is_on`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_ih6_workbench_open_item.py](../../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_switch_is_registered_as_an_operational_kill_switch`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_the_switch_needs_the_tag_defaults_on_and_is_registered`
- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — direct import
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_the_rw4b_switches_are_classified_in_the_parameter_registry`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_one_switch_on_by_default_classified_and_gating`
- [tests/test_open_world_gate.py](../../../../../../tests/test_open_world_gate.py) — direct import
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_switch_is_on_by_default_classified_and_acts_only_at_the_tag_with_the_guide_on`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_max_perspectives_is_a_keep_config_key`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_mvp039_is_one_constant_after_mvp038_and_the_latest`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f11_every_key_rw2b_added_is_classified`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_on_by_default_classified_and_the_contract_and_palette_gain_only_rw7a_keys`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_registry_audit.py](../../../../../../tests/test_registry_audit.py) — direct import
  - `test_a_stored_row_for_a_removed_spec_stays_readable`
  - `test_a_stored_row_of_a_removed_parameter_still_loads`
  - `test_abstention_budget_is_registered_and_monitored`
  - `test_active_heuristic_without_coverage_is_pending_warning_not_failure`
  - `test_audit_clean_with_vault`
  - `test_audit_falls_back_to_rules_for_vault_added_dict_keys`
  - `test_audit_flags_future_field_under_decision_namespace`
  - `test_bind_event_logging_records_and_reads`
  - `test_catchall_rule_is_frozen_to_snapshot`
  - `test_decision_specs_carry_promotion_gate_and_rationale`
  - `test_demotion_clears_evidence_and_redundancy_proofs`
  - `test_dormant_parameter_needs_no_coverage_certificate`
  - `test_every_config_numeric_leaf_is_classified`
  - `test_every_module_constant_is_registered`
  - `test_migration_069_idempotent_on_copy`
  - `test_no_unclassified_parameters_static`
  - `test_refresh_is_idempotent_projection`
  - `test_status_above_heuristic_without_promotion_evidence_is_failure`
  - `test_tagged_decision_comments_have_registered_specs`
  - `test_value_change_without_evidence_demotes_to_heuristic`
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_each_switch_is_classified_and_reads_off_or_below_the_tag`
- [tests/test_ro4_successor.py](../../../../../../tests/test_ro4_successor.py) — direct import
  - `test_each_new_key_is_classified`
- [tests/test_ro5_successor.py](../../../../../../tests/test_ro5_successor.py) — direct import
  - `test_each_new_key_is_classified`
- [tests/test_ro6_successor.py](../../../../../../tests/test_ro6_successor.py) — direct import
  - `test_each_new_key_is_classified`
- [tests/test_rofu_successor.py](../../../../../../tests/test_rofu_successor.py) — direct import
  - `test_each_new_key_is_classified`
- [tests/test_router_objective_migration.py](../../../../../../tests/test_router_objective_migration.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_rw2c_switch_off.py](../../../../../../tests/test_rw2c_switch_off.py) — direct import
  - `test_every_new_key_is_classified_in_the_parameter_registry`
- [tests/test_sensitivity_certificates.py](../../../../../../tests/test_sensitivity_certificates.py) — direct import
  - `test_coverage_certificate_with_flip_points_is_valid_coverage`
  - `test_link_coverage_certificate_never_changes_status`
  - `test_promote_refuses_decision_unstable_evidence`
  - `test_promote_requires_covering_evidence`
  - `test_stale_coverage_certificate_does_not_link`
- [tests/test_sg_successor.py](../../../../../../tests/test_sg_successor.py) — direct import
  - `test_the_switches_default_on_and_are_classified`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_every_roles_key_and_the_route_are_classified_as_operational_switches_and_bounds`
- [tests/test_te3a_successor.py](../../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_te3b_successor.py](../../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_the_switch_is_on_by_default_and_registered`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_each_new_key_is_classified`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_teacher_episode_log_is_classified_and_on_by_default`
- [tests/test_ux_phase2_shell.py](../../../../../../tests/test_ux_phase2_shell.py) — direct import
  - `test_the_shell_switch_is_classified_as_a_structural_display_key`

## Modification guidance

- Make changes here when the responsibility remains parameter registry within learnloop.params; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
