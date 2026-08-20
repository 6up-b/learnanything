---
title: "learnloop.curriculum.integration_backfill"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/integration_backfill.py"
source_paths:
  - "src/learnloop/curriculum/integration_backfill.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.integration_backfill module"
  - "src/learnloop/curriculum/integration_backfill.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.integration_backfill`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.integration_backfill` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: D3's integration gate applied to blueprints already persisted (plan item 5.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/integration_backfill.py](../../../../../../src/learnloop/curriculum/integration_backfill.py) |
| Source lines | 623 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class IntegrationDisposition(StrEnum)` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 104) — What to do with one persisted integration component.
- `class IntegrationReason(StrEnum)` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 126) — Typed reason per disposition — closed, and never a free-text rationale.
- `class IntegrationVerdict` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 156) — One persisted integration component, judged under D3, with its evidence.
  - `changes_content(self) -> bool` (line 177; public)
  - `as_dict(self) -> dict[str, Any]` (line 180; public)
- `class IntegrationBackfillReport` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 198)
  - `changed(self) -> tuple[IntegrationVerdict, ...]` (line 205; public)
  - `owed_capstones(self) -> tuple[IntegrationVerdict, ...]` (line 209; public)
  - `counts(self) -> dict[str, int]` (line 212; public)
  - `reason_counts(self) -> dict[str, int]` (line 218; public)
  - `by_learning_object(self) -> dict[str, list[IntegrationVerdict]]` (line 224; public)
  - `summary(self) -> dict[str, Any]` (line 230; public)
  - `as_dict(self) -> dict[str, Any]` (line 240; public)
- `coordination_is_observable(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 248) — Does any active instrument observe some facet at ``coordination``?
- `plan_integration_backfill(vault: LoadedVault, *, learning_object_ids: Iterable[str] | None=None, capabilities: Iterable[str] | None=None) -> IntegrationBackfillReport` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 364) — Judge every persisted integration component under D3.
- `class BackfillFileEdit` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 412) — One learning-object file's rewrite, with a unified diff for review.
  - `as_dict(self) -> dict[str, Any]` (line 420; public)
- `apply_integration_backfill(vault: LoadedVault, verdicts: Sequence[IntegrationVerdict], *, dry_run: bool=True, clock: Clock | None=None) -> tuple[BackfillFileEdit, ...]` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 444) — Rewrite the authored blueprints for ``verdicts``, or just diff them.
- `class BackfillApplyResult` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 524) — A landed backfill: the file edits plus the single recalibration boundary.
  - `as_dict(self) -> dict[str, Any]` (line 532; public)
- `apply_integration_backfill_and_recalibrate(vault: LoadedVault, repository: Repository, verdicts: Sequence[IntegrationVerdict], *, dry_run: bool=True, clock: Clock | None=None) -> BackfillApplyResult` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 541) — Land the backfill and narrate the mastery move it causes (§5.2 / A6).

### Module constants

- `DEEPEST_AUTHORABLE_CAPABILITY` ([src/learnloop/curriculum/integration_backfill.py](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 94)
- `COORDINATION` ([src/learnloop/curriculum/integration_backfill.py](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 98)
- `_CAPABILITY_BY_RANK` ([src/learnloop/curriculum/integration_backfill.py](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 101)

## Internal implementation anchors

- `_binding(components: Iterable[Any]) -> list[Any]` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 262) — Components that actually gate — ``hard`` / ``path_specific`` only (§8.2).
- `_judge(vault: LoadedVault, *, learning_object_id: str, blueprint_id: str, recipe, coordination_observed: bool) -> IntegrationVerdict` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 272)
- `_learning_object_path(vault: LoadedVault, learning_object_id: str) -> Path` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 429) — Resolve the authored YAML for an LO.
- `_find_recipe(data: dict[str, Any], verdict: IntegrationVerdict) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/integration_backfill.py), line 614) — The raw recipe mapping this verdict judged, matched by blueprint+recipe id.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `COORDINATION`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`; statically calls `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `COORDINATION`, `apply_integration_backfill`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`; statically calls `apply_integration_backfill`, `apply_integration_backfill_and_recalibrate`, `plan_integration_backfill`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `DEFAULT_TRAJECTORY`, `waypoint_slug_for_capability`; calls `waypoint_slug_for_capability`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CAPABILITY_RANK`, `CONTRACT_MODALITIES`, `build_instrument_pool`; calls `build_instrument_pool`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `replay_learning_object`; calls `replay_learning_object`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`, `yaml_to_string`; calls `read_yaml`, `write_yaml`, `yaml_to_string`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `difflib`, `enum`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_apply_writes_one_boundary_and_a_rerun_writes_none`
  - `test_dry_run_writes_no_boundary`
- [tests/test_integration_backfill.py](../../../../../../tests/test_integration_backfill.py) — direct import
  - `test_apply_is_diff_only_by_default`
  - `test_apply_lowers_the_capability_in_place`
  - `test_apply_writes_a_drop_as_an_explicit_null`
  - `test_capability_scope_keeps_the_plans_stated_batch_honest`
  - `test_coordination_becomes_keepable_once_an_instrument_observes_it`
  - `test_criterion_one_is_capability_independent`
  - `test_drop_removes_the_cell_without_moving_the_reachable_count`
  - `test_drop_when_fewer_than_two_binding_components`
  - `test_drop_when_the_integration_facet_duplicates_a_component`
  - `test_keep_and_flag_when_no_observable_rung_is_deeper_than_the_parts`
  - `test_keep_when_the_capability_is_already_observable`
  - `test_learning_object_scope_is_the_pilot_seam`
  - `test_lower_when_coordination_is_unobservable_and_a_deeper_authorable_rung_exists`
  - `test_out_of_vocabulary_capability_abstains`

## Modification guidance

- Change integration backfill policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/integration_backfill.py](../../../../../../src/learnloop/curriculum/integration_backfill.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
