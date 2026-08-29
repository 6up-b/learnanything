---
title: "learnloop.substrate.activity_patterns"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/activity_patterns.py"
source_paths:
  - "src/learnloop/substrate/activity_patterns.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.activity_patterns module"
  - "src/learnloop/substrate/activity_patterns.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.activity_patterns`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.activity_patterns` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P1 step 2 -- capability aliases, TaskFeatures, and the ActivityPattern registry (spec_p1_shared_substrate §3.3, §3.4, §3.5).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py) |
| Source lines | 659 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InvalidPattern(Exception)` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 108) — A pattern version declared a value outside a closed vocabulary (§3.5, §9.1).
- `class InvalidCoordinationUse(Exception)` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 112) — ``coordination`` used outside a blueprint integration component / whole-task criterion that cites one (§3.3, §9.1).
- `class UnknownPatternVersion(Exception)` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 117)
  - `__init__(self, pattern_version_id: str)` (line 118; internal)
- `class ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 128)
  - `as_dict(self) -> dict[str, Any]` (line 149; public)
- `ensure_capability_alias_registry(repository: Repository, *, registry_version: int=CAPABILITY_ALIAS_REGISTRY_VERSION, aliases: Mapping[str, str | None] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 157) — Seed the versioned capability-alias registry (idempotent).
- `map_capability(repository: Repository, legacy_value: str, *, registry_version: int=CAPABILITY_ALIAS_REGISTRY_VERSION) -> str` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 177) — Map a legacy capability value to the closed vocabulary (§3.3).
- `normalize_capabilities(repository: Repository, values: Iterable[str], *, registry_version: int=CAPABILITY_ALIAS_REGISTRY_VERSION) -> list[str]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 195) — Normalize a legacy capability list through the alias registry (§3.3).
- `ensure_builtin_task_feature_schema(repository: Repository, *, schema_slug: str='p1_launch', version: int=TASK_FEATURE_SCHEMA_VERSION, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 211)
- `validate_task_features(repository: Repository, schema_version_id: str, features: Mapping[str, Any]) -> tuple[bool, list[str]]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 228) — Validate a TaskFeature vector against a schema version (§3.4).
- `register_pattern_version(repository: Repository, *, pattern_slug: str, fields: Mapping[str, Any], status: str='draft', clock: Clock | None=None) -> ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 341) — Register an immutable, content-addressed pattern version (§3.5).
- `review_pattern_version(repository: Repository, *, pattern_version_id: str) -> None` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 376)
- `activate_pattern_version(repository: Repository, *, pattern_version_id: str) -> None` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 382)
- `list_compatible_patterns(repository: Repository, *, purpose: str, target_kind: str | None=None, capabilities: Sequence[str]=(), status: str='active') -> list[ActivityPatternVersion]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 388) — List reviewed/active patterns compatible with a (purpose, target kind, capability set).
- `candidate_within_bounds(version: ActivityPatternVersion, *, purpose: str | None=None, operation: str | None=None, capability: str | None=None, target_kind: str | None=None) -> bool` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 412) — Fail closed (§3.5): a candidate that invents an operation, capability, target kind, or purpose outside the pattern's declared bounds is rejected.
- `routing_metadata(version: ActivityPatternVersion) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 443) — The "why this activity?" routing DTO (§3.5).
- `evidence_semantics(version: ActivityPatternVersion) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 466) — The ONLY projection-facing DTO this module exposes.
- `ensure_builtin_patterns(repository: Repository, *, clock: Clock | None=None) -> dict[str, ActivityPatternVersion]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 553) — Seed the reviewed launch patterns (§3.5), idempotent + content-addressed (mirrors the P0.2 ``ensure_builtin_schemas`` precedent).
- `adapt_probe_template_to_pattern(repository: Repository, *, template_slug: str, likelihood_identity: str, status: str='active', clock: Clock | None=None) -> ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 575) — Mirror an admitted probe-family template into a ``diagnostic``-purpose pattern without touching the probe rows; the compiled likelihood identity + status remain intact on the diagnostic instrument side (§3.5, §7.3).
- `load_pattern_version(repository: Repository, pattern_version_id: str) -> ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 658)

### Module constants

- `CAPABILITIES` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 33)
- `OPERATIONS` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 38)
- `LEARNING_PROCESSES` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 43)
- `PURPOSES` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 58)
- `CALIBRATION_STATUSES` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 60)
- `LEGACY_UNMAPPED` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 64)
- `CAPABILITY_ALIAS_REGISTRY_VERSION` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 67)
- `TASK_FEATURE_SCHEMA_VERSION` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 68)
- `_TASK_FEATURE_DIMENSIONS` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 71)
- `_LEGACY_ALIASES` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 93)
- `_EVIDENCE_INPUT_KEYS` ([src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py), line 457)

## Internal implementation anchors

- `_validate_pattern_fields(fields: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 265)
- `_pattern_content_hash(pattern_slug: str, fields: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 288)
- `_fields_to_columns(fields: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 317)
- `_launch_pattern_defs() -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 485) — The reviewed launch patterns (§3.5).
- `_row_to_version(row: Mapping[str, Any], pattern_slug: str) -> ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 613)
- `_pattern_slug_for(repository: Repository, pattern_id: str) -> str` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 643)
- `_load_version(repository: Repository, pattern_version_id: str) -> ActivityPatternVersion` ([source](../../../../../../src/learnloop/substrate/activity_patterns.py), line 651)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; statically calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `LEGACY_UNMAPPED`, `ensure_capability_alias_registry`, `map_capability`; statically calls `ensure_capability_alias_registry`, `map_capability`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; statically calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; statically calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; statically calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]], [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]], [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_contract_extensions.py](../../../../../../tests/test_activity_contract_extensions.py) — direct import
- [tests/test_activity_patterns.py](../../../../../../tests/test_activity_patterns.py) — direct import
  - `test_candidate_out_of_bounds_fails_closed`
  - `test_coordination_requires_integration_component`
  - `test_ensure_builtin_patterns_idempotent`
  - `test_invalid_capability_fails_new_authoring`
  - `test_invalid_operation_and_learning_process_fail`
  - `test_learning_process_excluded_from_evidence_dto`
  - `test_list_compatible_patterns`
  - `test_map_capability_identity_alias_and_unmapped`
  - `test_normalize_capabilities_folds_synthesis_output`
  - `test_probe_template_adapter_is_diagnostic_only`
  - `test_task_feature_validation`

## Modification guidance

- Change activity patterns policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/activity_patterns.py](../../../../../../src/learnloop/substrate/activity_patterns.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
