---
title: "learnloop.params.parameter_registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/params/parameter_registry.py"
source_paths:
  - "src/learnloop/params/parameter_registry.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/params/_package|learnloop.params]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.params.parameter_registry` exists within [[Reference/Modules/learnloop/params/_package|learnloop.params]] to own the behavior summarized by its module contract: P0.5 calibration-status parameter registry (spec_p0_measurement_correctness §6).

The authoritative system-level explanation remains in [[Learning System]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py) |
| Source lines | 1594 |
| Owning package | [[Reference/Modules/learnloop/params/_package|learnloop.params]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ParameterSpec` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 76)
- `register(spec: ParameterSpec) -> ParameterSpec` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 98)
- `classify_config_path(path: str) -> _ConfigRule | None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1004)
- `config_numeric_leaves(config: LearnLoopConfig | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1019) — Every numeric leaf of the ``LearnLoopConfig`` pydantic tree, keyed by dotted path.
- `module_numeric_constants() -> list[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1069) — Module-level UPPERCASE numeric constants across the §2.1 module inventory, as ``module:CONSTANT`` paths.
- `tagged_decision_constants() -> list[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1093) — Module constants carrying the ``# decision parameter`` breadcrumb comment, as ``module:CONSTANT`` paths (the drift cross-check surface of §2.3).
- `class ResolutionContext` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1117)
- `resolve_effective(spec: ParameterSpec, ctx: ResolutionContext) -> tuple[Any, str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1160) — Return (effective_value, source).
- `decision_specs() -> list[ParameterSpec]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1256)
- `refresh(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1260) — Rebuild the per-vault ``parameter_registry`` projection from the code definition + resolved effective values.
- `set_promotion_evidence_id(repository: Repository, path: str, evidence_id: str | None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1339) — Persist the ``promotion_evidence_id`` column for a registry row.
- `freeze_manifest(vault: LoadedVault, repository: Repository, *, algorithm_version: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1364) — Freeze the immutable per-algorithm-version manifest of all decision parameters' effective value-hash/status/lifecycle/source.
- `record_bind(repository: Repository, path: str, context: dict[str, Any], *, observation_ref: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1413) — Log that a dormant guardrail actually fired (§6).
- `class AuditReport` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1434)
  - `failures(self) -> list[str]` (line 1449; public) — The failure categories (name) that are non-empty.
  - `clean(self) -> bool` (line 1468; public) — Ordinary audit cleanliness: no failures.
  - `release_clean(self) -> bool` (line 1475; public) — Strict release-gate cleanliness: clean AND zero pending coverage certificates.
  - `as_dict(self) -> dict[str, Any]` (line 1481; public)
- `audit(vault: LoadedVault | None=None, repository: Repository | None=None) -> AuditReport` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1496) — Run the decision-parameter audit.

### Module constants

- `PLANTED_LEARNER_GATE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 71)
- `PLANTED_MISGRADE_GATE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 72)
- `REGISTRY` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 95)
- `MODULE_INVENTORY` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 107)
- `MODULE_IMPORTS` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 199)
- `_CONFIG_RULES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 828)
- `_CATCHALL_RULE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 1001)
- `_MODULE_ATTR_CACHE` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 1137)
- `CATCHALL_SNAPSHOT` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 1200)
- `BOOLEAN_DECISION_LEAVES` ([src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py), line 1234)

## Internal implementation anchors

- `_reg_const(path: str, param_class: ParamClass, *, kind: Kind='decision', owner: str, rationale: str, lifecycle: Lifecycle='active', status: Status='heuristic', bind_site: str | None=None, gate: str | None=PLANTED_LEARNER_GATE) -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 205)
- `class _ConfigRule` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 803)
- `_exact(*paths: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 814)
- `_prefix(*prefixes: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 819)
- `_suffix(*suffixes: str) -> Callable[[str], bool]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 823)
- `_is_number(value: Any) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1015)
- `_module_path(rel: str) -> Path` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1053)
- `_numeric_ast(node: ast.AST) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1057)
- `_resolve_config_value(path: str, config: LearnLoopConfig) -> Any` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1123)
- `_resolve_module_constant(path: str) -> Any` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1140)
- `_freeze_catchall_rule() -> frozenset[str]` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1180) — Snapshot the config leaves the broad decision-namespace catch-all currently owns, then rebind the rule to match only that explicit set (F6).
- `_register_config_path(path: str) -> bool` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1203) — Register one config leaf from its classification rule.
- `_build_config_specs() -> None` ([source](../../../../../../src/learnloop/params/parameter_registry.py), line 1239)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `module`; statically calls `_resolve_config_value`, `audit`, `refresh`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `module`; statically calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `REGISTRY`, `module`; statically calls `set_promotion_evidence_id`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]], [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]], [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]], [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]], [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_architecture.py](../../../../../../tests/test_architecture.py) — direct import
  - `test_runtime_constructed_module_references_resolve`
- [tests/test_constraint_engine.py](../../../../../../tests/test_constraint_engine.py) — direct import
  - `test_fatigue_slack_param_is_registered_dormant_and_monitored`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_reviews_lists_quarantined_then_adjudicate_clears_and_receipt`
- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — direct import
- [tests/test_open_world_gate.py](../../../../../../tests/test_open_world_gate.py) — direct import
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
  - `test_upgrade_freezes_legacy_manifests_immutably`
- [tests/test_registry_audit.py](../../../../../../tests/test_registry_audit.py) — direct import
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
- [tests/test_sensitivity_certificates.py](../../../../../../tests/test_sensitivity_certificates.py) — direct import
  - `test_coverage_certificate_with_flip_points_is_valid_coverage`
  - `test_link_coverage_certificate_never_changes_status`
  - `test_promote_refuses_decision_unstable_evidence`
  - `test_promote_requires_covering_evidence`
  - `test_stale_coverage_certificate_does_not_link`

## Modification guidance

- Make changes here when the responsibility remains parameter registry within learnloop.params; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/params/parameter_registry.py](../../../../../../src/learnloop/params/parameter_registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
