---
title: "learnloop.scheduling.constraint_engine"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/constraint_engine.py"
source_paths:
  - "src/learnloop/scheduling/constraint_engine.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.constraint_engine module"
  - "src/learnloop/scheduling/constraint_engine.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.constraint_engine`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.constraint_engine` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 1 -- the versioned feasible-set constraint engine (spec §5, design B step 1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py) |
| Source lines | 362 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ExclusionReason` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 53) — One typed reason a candidate is infeasible or deferred (§5).
  - `as_dict(self) -> dict[str, Any]` (line 62; public)
- `class Feasibility` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 73) — The engine output for one candidate: eligible, or a list of exclusions.
  - `eligible(self) -> bool` (line 80; public)
  - `as_dict(self) -> dict[str, Any]` (line 83; public)
- `class Constraint` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 92) — A versioned constraint definition.
  - `definition(self) -> dict[str, Any]` (line 103; public)
- `manifest() -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 292) — The frozen, content-hashed manifest of active constraint definitions (§5).
- `evaluate(candidate: 'Candidate', snapshot: 'ControllerSnapshot', block: 'AttentionBlock | None'=None) -> Feasibility` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 301) — Evaluate every constraint against one candidate.
- `class FeasibilityReport` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 319)
- `feasible_set(candidates: Sequence['Candidate'], snapshot: 'ControllerSnapshot', block: 'AttentionBlock | None'=None, *, repository: Repository | None=None, clock: Clock | None=None) -> FeasibilityReport` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 326) — Partition candidates into the feasible set + per-candidate exclusion reasons (§5).

### Module constants

- `CONSTRAINT_MANIFEST_VERSION` ([src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 44)
- `FATIGUE_BUDGET_SLACK_MINUTES` ([src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 49)
- `_FRESH_EVIDENCE_ACTIONS` ([src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 111)
- `CONSTRAINTS` ([src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 270)

## Internal implementation anchors

- `_requires_unseen(block: 'AttentionBlock | None') -> bool` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 114) — Fresh-evidence blocks (diagnosis, terminal assessment) require an unseen surface; instruction/practice/maintenance do not (§5, §3.6).
- `_c_active(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 121)
- `_c_stimulus_renderable(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 129) — Meas §3.A2/§3.A3: the administration surface cannot render this stimulus.
- `_c_purpose(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 155)
- `_c_hard_exposure(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 167) — Global exact/hard exposure collision (invariant 11): P1's deterministic authority.
- `_c_assessment_reservation(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 196) — A surface holding a live assessment reservation may only be served for assessment (P0 leakage/burn rules, §5).
- `_c_fatigue_budget(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 211) — Remaining minutes + expected duration bound (§5).
- `_c_same_facet_dispersion(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 230) — Same-facet/near-kin dispersion (§9.1): two fresh-evidence administrations on the same facet/capability/lineage/hard-group/near-kin cannot be back-to-back.
- `_c_stage_interleaving(candidate, snapshot, block)` ([source](../../../../../../src/learnloop/scheduling/constraint_engine.py), line 254) — Stage-aware interleaving (§9.2): acquisition stays coherent, assessment follows the frozen distribution, discrimination/transfer interleave.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; statically calls `manifest`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `ExclusionReason`, `Feasibility`, `FeasibilityReport`, `feasible_set`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `record_bind`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `Candidate`, `ControllerSnapshot`
- [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]] — imports `module`; calls `same_facet_violation`
- [[Reference/Modules/learnloop/scheduling/interleaving|learnloop.scheduling.interleaving]] — imports `module`; calls `stage_violation`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `AttentionBlock`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_constraint_engine.py](../../../../../../tests/test_constraint_engine.py) — direct import
  - `test_assessment_reservation_blocks_non_assessment_use`
  - `test_dormant_fatigue_slack_guardrail_bind_logged_when_it_fires`
  - `test_exclusion_reasons_are_complete_all_violations_reported`
  - `test_fatigue_budget_excludes_over_budget_candidate`
  - `test_feasible_set_partitions_and_reports_manifest_hash`
  - `test_freshness_unknown_blocks_unseen_claim_only_for_fresh_block`
  - `test_hard_exposure_collision_excludes_fresh_evidence_candidate`
  - `test_inactive_and_quarantined_are_excluded`
  - `test_manifest_is_content_hashed_and_stable`
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_constraint_emptied_feasible_set_is_a_veto`
  - `test_ownership_only_emptying_is_not_a_veto`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_assessment_reserve_not_poached_by_practice_at_plan_time`
- [tests/test_dispersion.py](../../../../../../tests/test_dispersion.py) — direct import
  - `test_acquisition_stays_coherent`
  - `test_assessment_follows_frozen_distribution`
  - `test_discrimination_allows_interleaving`
  - `test_dispersion_inert_when_enough_intervening_administrations`
  - `test_near_kin_fingerprint_dispersion`
  - `test_practice_block_is_not_dispersed`
  - `test_same_facet_fresh_evidence_not_back_to_back`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_staged_controller_admits_both_instruments`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import

## Modification guidance

- Change constraint engine policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/constraint_engine.py](../../../../../../src/learnloop/scheduling/constraint_engine.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
