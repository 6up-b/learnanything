---
title: "learnloop.learner.familiarity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/familiarity.py"
source_paths:
  - "src/learnloop/learner/familiarity.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.familiarity module"
  - "src/learnloop/learner/familiarity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.familiarity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.familiarity` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: P1 step 6 -- one familiarity namespace + soft-kinship + familiarity_projection_v1 (spec_p1_shared_substrate §4.1, §4.2, §4.3; standing rules 5 & 7; owner decision A.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py) |
| Source lines | 527 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `record_memberships(repository: Repository, *, surface_id: str, memberships: Iterable[Mapping[str, Any]], clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 104) — Record namespaced hard-group memberships for a surface (§4.1).
- `record_soft_features(repository: Repository, *, surface_id: str, features: Mapping[str, Any], clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 133) — Store the §4.2 soft-kinship feature vector for a surface (never a group id).
- `warmth_score(features: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 154) — Deterministic monotone warmth in ``[0, 1)`` over the §4.2 feature vector.
- `class HardCollision` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 171)
- `class Familiarity` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 179)
  - `as_dict(self) -> dict[str, Any]` (line 189; public)
- `familiarity_projection_v1(repository: Repository, *, surface_id: str, purpose: str | None=None) -> Familiarity` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 217) — The P1 named familiarity projection (§4.2).
- `propagate_tutor_exposure(repository: Repository, *, explanation_fingerprints: Sequence[Mapping[str, Any]], plausibly_touched_surface_ids: Sequence[str]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 305) — When an AI explanation is shown, the claims/proof ideas/representations/ examples it exposed append memberships against their fingerprint groups so a near-term surface reusing those cues reads as warm rather than cold (§4.1).
- `tight_kinship_clusters(repository: Repository, *, surface_ids: Sequence[str], threshold: float | None=None, stem_columns: Mapping[str, StemColumn] | None=None) -> list[list[str]]` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 403) — Single-linkage threshold clustering (A.4).
- `class EvidenceCapGrouping` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 488)
  - `as_dict(self) -> dict[str, Any]` (line 492; public)
- `evidence_cap_grouping(repository: Repository, *, surface_ids: Sequence[str], threshold: float | None=None, stem_columns: Mapping[str, StemColumn] | None=None) -> EvidenceCapGrouping` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 499) — Independent-group count for the family evidence cap (§4.3): one tight soft-kinship cluster contributes exactly ONE independent group, no matter how many variant surfaces it holds.

### Module constants

- `FEATURE_SCHEMA_VERSION` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 40)
- `NAMESPACES` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 43)
- `HARD_NAMESPACES` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 56)
- `_EXPOSURE_KINDS` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 61)
- `AFFECTS` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 67)
- `TIGHT_KINSHIP_THRESHOLD` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 77)
- `WARMTH_ROTATION_THRESHOLD` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 80)
- `V1_COEFFICIENTS` ([src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py), line 85)

## Internal implementation anchors

- `_surface_exposed(repository: Repository, surface_id: str) -> bool` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 210)
- `_pairwise_warmth(repository: Repository, surface_a: str, surface_b: str) -> float` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 359) — Symmetric pairwise warmth between two surfaces from their stored soft features.
- `_stem_edge(a: StemColumn | None, b: StemColumn | None) -> bool | None` ([source](../../../../../../src/learnloop/learner/familiarity.py), line 386) — Does A2's stem rule decide this edge, and how?

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `propagate_tutor_exposure`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `module`; statically calls `familiarity_projection_v1`, `warmth_score`
- [[Reference/Modules/learnloop/scheduling/progression|learnloop.scheduling.progression]] — imports `module`; statically calls `evidence_cap_grouping`
- [[Reference/Modules/learnloop/sim/kinship_admission|learnloop.sim.kinship_admission]] — imports `module`; statically calls `warmth_score`
- [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] — imports `module`; statically calls `familiarity_projection_v1`
- [[Reference/Modules/learnloop/substrate/surface_pool|learnloop.substrate.surface_pool]] — imports `module`; statically calls `familiarity_projection_v1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]], [[Reference/Modules/learnloop/scheduling/progression|learnloop.scheduling.progression]], [[Reference/Modules/learnloop/sim/kinship_admission|learnloop.sim.kinship_admission]], [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_familiarity.py](../../../../../../tests/test_familiarity.py) — direct import
  - `test_all_hard_memberships_considered_not_just_first`
  - `test_clustering_is_deterministic`
  - `test_distant_surfaces_stay_separate_groups`
  - `test_equal_values_in_different_namespaces_do_not_collide`
  - `test_exposure_under_one_purpose_warms_hard_sibling_under_another`
  - `test_familiarity_result_has_no_correctness_field`
  - `test_fingerprinted_but_unseen_is_novel`
  - `test_hard_collision_blocks_unseen_claim`
  - `test_missing_fingerprint_is_unknown_not_novel`
  - `test_tight_kinship_single_linkage_caps_independent_groups`
  - `test_tutor_exposure_propagation_warms_and_degrades`
  - `test_warmth_is_monotone_in_exposure_features`
- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — direct import
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_the_rule_is_inert_without_stem_identity`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_golden_path_ten_step_fixture_journey`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
- [tests/test_surface_mint.py](../../../../../../tests/test_surface_mint.py) — direct import
  - `test_purpose_leakage_blocks_assessment_hard_collision`
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
  - `test_familiar_practice_is_never_reported_fresh`
  - `test_lazy_rotation_fires_after_warmth`
  - `test_next_practice_surface_writes_served_and_rotated_ledger_events`

## Modification guidance

- Change familiarity policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/familiarity.py](../../../../../../src/learnloop/learner/familiarity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
