---
title: "learnloop.curriculum.depth_rungs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/depth_rungs.py"
source_paths:
  - "src/learnloop/curriculum/depth_rungs.py"
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
  - "learnloop.curriculum.depth_rungs module"
  - "src/learnloop/curriculum/depth_rungs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.depth_rungs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.depth_rungs` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Depth rungs: waypoint targeting for practice-item generation (spec v2 §4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py) |
| Source lines | 659 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RungTarget` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 47)
  - `as_dict(self) -> dict[str, Any]` (line 62; public)
- `class Waypoint` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 79)
- `resolve_waypoint_slug(slug: str) -> str` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 138) — Canonical slug for ``slug``, mapping retired waypoints forward.
- `trajectory_slugs() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 144) — Ordered waypoint slugs of the built-in trajectory (easiest first).
- `adjacent_slug(slug: str, direction: str) -> str | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 150) — The waypoint one step easier/harder on the default trajectory, or None at the trajectory bounds (deeper than select_method needs an envelope).
- `waypoint_rung(repository: Repository, slug: str) -> RungTarget` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 164) — A RungTarget for one default-trajectory waypoint (public seam for rung_variants and other callers; keeps them off module-private names).
- `waypoint_slug_for_capability(capability: str) -> str | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 174) — The default-trajectory waypoint that authors AT ``capability``, or ``None``.
- `capability_rung(repository: Repository, capability: str) -> RungTarget | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 189) — A RungTarget authoring AT ``capability``, or ``None`` when none exists.
- `select_rung(vault, repository: Repository, *, learning_object_id: str, mastery_mean: float | None, evidence_count: int=0, claimed_level: float | None=None, commitment_id: str | None=None) -> RungTarget` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 229) — Pick the generation waypoint for one learning object.
- `project_task_contract(repository: Repository, contract: Mapping[str, Any], schema_version_id: str) -> tuple[str, dict[str, Any], dict[str, dict[str, Any]]] | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 437) — Project a milestone ``task_contract_json`` into (capability, point vector, bounds), or None when any piece is malformed (no partial rungs).
- `rung_float_proxies(rung: RungTarget) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 498) — Legacy float bands consistent with the rung, so the two vocabularies (task features vs retrieval_demand/transfer_distance/scaffold_level) cannot silently drift.
- `validate_item_against_rung(repository: Repository, *, payload: Mapping[str, Any], rung: RungTarget) -> list[GateDiagnostic]` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 539) — Deterministic admission check of one generated-item payload against its rung.

### Module constants

- `RUNG_TRAJECTORY_VERSION` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 37)
- `TASK_FEATURE_SCHEMA_SLUG` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 39)
- `_SCAFFOLDING_ORDER` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 41)
- `_TRANSFER_ORDER` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 42)
- `_SPAN_ORDER` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 43)
- `DEFAULT_TRAJECTORY` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 101)
- `_WAYPOINT_BY_SLUG` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 124)
- `_WAYPOINT_SLUG_BY_CAPABILITY` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 130)
- `_RETIRED_WAYPOINT_SLUGS` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 135)
- `UNCERTAIN_EVIDENCE_COUNT` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 314)
- `UNCERTAIN_OPTIMISM_STEPS` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 315)
- `_RUNG_BY_HYPOTHESIS` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 327)
- `_HYPOTHESIS_COMPLETION_REASONS` ([src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 336)

## Internal implementation anchors

- `_default_bounds(features: Mapping[str, Any]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 205) — Point-target bounds: max equals the target on every declared dimension — the generated item may not exceed the waypoint's hardness anywhere.
- `_waypoint_target(waypoint: Waypoint, schema_version_id: str, *, fallback_reason: str | None=None) -> RungTarget` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 212)
- `_uncertainty_optimism(evidence_count: int) -> int` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 318) — Waypoints to climb past the point estimate when evidence is thin.
- `_rung_from_episode_hypothesis(repository: Repository, learning_object_id: str) -> str | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 339) — Entry slug from the LO's latest trusted completed probe episode, or None.
- `_milestone_rung(repository: Repository, commitment_id: str, schema_version_id: str) -> RungTarget | None` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 354) — Project the commitment's NEXT milestone into a RungTarget, or None.
- `_reached_milestones(repository: Repository, commitment_id: str) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/depth_rungs.py), line 415)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `RungTarget`, `capability_rung`; statically calls `capability_rung`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `TASK_FEATURE_SCHEMA_SLUG`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `RungTarget`, `TASK_FEATURE_SCHEMA_SLUG`, `capability_rung`, `rung_float_proxies`, `select_rung`, `validate_item_against_rung`; statically calls `capability_rung`, `rung_float_proxies`, `select_rung`, `validate_item_against_rung`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `RungTarget`, `adjacent_slug`, `rung_float_proxies`, `select_rung`, `trajectory_slugs`, `waypoint_rung`; statically calls `RungTarget`, `adjacent_slug`, `rung_float_proxies`, `select_rung`, `trajectory_slugs`, `waypoint_rung`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `project_task_contract`; statically calls `project_task_contract`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `DEFAULT_TRAJECTORY`, `waypoint_slug_for_capability`; statically calls `waypoint_slug_for_capability`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `TASK_FEATURE_SCHEMA_SLUG`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `GateDiagnostic`; calls `GateDiagnostic`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contract_commissioning.py](../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_capability_rung_refuses_to_guess`
  - `test_coordination_cell_is_deferred_with_a_typed_reason`
  - `test_plan_rung_follows_the_contract_not_the_mastery_band`
- [tests/test_practice_item_quality_gates.py](../../../../../../tests/test_practice_item_quality_gates.py) — direct import
  - `test_cold_entry_waypoint_is_a_cued_constructed_response`
  - `test_default_trajectory_has_no_selected_response_waypoint`
  - `test_retired_recognize_slug_still_resolves`
  - `test_trajectory_is_monotone_and_escalates`

## Modification guidance

- Change depth rungs policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/depth_rungs.py](../../../../../../src/learnloop/curriculum/depth_rungs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
