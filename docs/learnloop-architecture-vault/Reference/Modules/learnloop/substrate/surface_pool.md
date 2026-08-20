---
title: "learnloop.substrate.surface_pool"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/surface_pool.py"
source_paths:
  - "src/learnloop/substrate/surface_pool.py"
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
  - "learnloop.substrate.surface_pool module"
  - "src/learnloop/substrate/surface_pool.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.surface_pool`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.surface_pool` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P2 PRACTICE track -- the bounded, owner-admitted rotating practice pool (spec_p2_narrow_golden_path §7.3, U-028, §12.4; design B.7; migration 085).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/surface_pool.py](../../../../../../src/learnloop/substrate/surface_pool.py) |
| Source lines | 522 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InvalidPool(Exception)` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 53) — A pool surface cannot be admitted (out of blueprint bounds, or it collides with an assessment-reserved surface, §7.3).
- `class PoolSurface` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 59)
  - `as_dict(self) -> dict[str, Any]` (line 66; public)
- `class PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 71)
  - `as_dict(self) -> dict[str, Any]` (line 80; public)
- `class ServedSurface` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 87)
  - `as_dict(self) -> dict[str, Any]` (line 97; public)
- `class PoolSelection` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 102)
  - `as_dict(self) -> dict[str, Any]` (line 110; public)
- `pool_content_hash(*, pool_slug: str, blueprint_version_id: str, surfaces: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 139) — The timestamp/id-independent content identity of a pool (§12.8 determinism).
- `assemble_pool(repository: Repository, *, pool_slug: str, blueprint_version_id: str, surfaces: Sequence[Mapping[str, Any]], clock: Clock | None=None) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 154) — Assemble a practice pool from candidate surfaces for a reviewed blueprint version (§7.3).
- `admit_pool_surface(repository: Repository, *, pool_id: str, surface_slug: str, surface_id: str | None=None, assessment_surface_id: str | None=None, checks: Mapping[str, Any] | None=None, author: str='owner', clock: Clock | None=None) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 232) — Owner admits one reviewed surface into the pool (U-028).
- `reject_pool_surface(repository: Repository, *, pool_id: str, surface_slug: str, reason: str, author: str='owner', clock: Clock | None=None) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 263)
- `review_pool(repository: Repository, *, pool_id: str, checks: Mapping[str, Any] | None=None, author: str='owner', clock: Clock | None=None) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 284) — Owner marks the pool reviewed once every surface is admitted (§7.3).
- `activate_pool(repository: Repository, *, pool_id: str, author: str='owner', clock: Clock | None=None) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 304)
- `next_practice_surface(repository: Repository, *, pool_id: str, warmth_threshold: float | None=None, cadence: int | None=None, clock: Clock | None=None) -> PoolSelection` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 374) — Serve one current admitted surface + at most one cached spare (§7.3).
- `request_spare_mint(repository: Repository, *, card_version_id: str, anchor_surface_id: str | None=None, requested_angle: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 432) — Enqueue a durable, lease-fenced pre-mint request for a fresh spare surface (§7.3, design B.7 batch-and-rank).
- `open_practice(repository: Repository, *, resolved: ResolvedActivity, goal_id: str | None=None, assistance: Mapping[str, Any] | None=None, feedback_condition: str | None=None, algorithm_version: str | None=None, clock: Clock | None=None) -> Administration` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 459) — Administer a pool surface at the PRACTICE purpose through the landed atomic render/burn boundary (§7.3).
- `pool_status(repository: Repository, *, pool_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 492) — The current pool + its admission/rotation ledger (§7.3 audit).

### Module constants

- `POOL_SPEC_SCHEMA_VERSION` ([src/learnloop/substrate/surface_pool.py](../../../../../../src/learnloop/substrate/surface_pool.py), line 45)
- `POOL_SPARE_CACHE` ([src/learnloop/substrate/surface_pool.py](../../../../../../src/learnloop/substrate/surface_pool.py), line 50)

## Internal implementation anchors

- `_canonical_surfaces(surfaces: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 125)
- `_assert_no_assessment_collision(repository: Repository, *, surface_id: str, assessment_surface_id: str | None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 191) — Refuse a pool surface that collides with the run's assessment reserve (§7.3): an exact ``surface_hash`` or ``fingerprint`` match, or a hard-namespace collision.
- `_assert_practice_purpose(repository: Repository, surface_id: str) -> None` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 214) — A purpose-specific family can never transition roles (§12.4): the resolved surface's card family must be a practice family, not an assessment/diagnostic one.
- `_serve(repository: Repository, surface_row: Mapping[str, Any], *, warmth_threshold: float | None, cadence: int | None) -> ServedSurface` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 321)
- `_record_pool_selection(repository: Repository, pool_id: str, selection: PoolSelection, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 342) — Write the served/rotated pool ledger events (§7.3 audit).
- `_load_pool(repository: Repository, pool_id: str, *, minted: bool=True) -> PoolRecord` ([source](../../../../../../src/learnloop/substrate/surface_pool.py), line 500)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `module`; statically calls `admit_pool_surface`, `assemble_pool`, `next_practice_surface`, `pool_status`, `review_pool`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `admit_pool_surface`, `review_pool`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `familiarity_projection_v1`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `Administration`, `ResolvedActivity`, `canonical_hash`, `canonical_json`, `open_administration`, `reserve_surface`; calls `canonical_hash`, `canonical_json`, `open_administration`, `reserve_surface`
- [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] — imports `module`; calls `request_candidates`, `rotation_decision`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_golden_path_ten_step_fixture_journey`
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
  - `test_assessment_reserved_surface_is_refused_at_admission`
  - `test_current_plus_spare_cache_is_bounded`
  - `test_familiar_practice_is_never_reported_fresh`
  - `test_generator_outage_does_not_block_in_flight_practice`
  - `test_lazy_rotation_fires_after_warmth`
  - `test_next_practice_surface_writes_served_and_rotated_ledger_events`
  - `test_pool_assembly_deterministic`
  - `test_practice_exposure_invalidates_same_fingerprint_assessment_reserve`
  - `test_purpose_specific_family_cannot_transition_roles`
  - `test_surfaces_enter_candidate_and_review_requires_admission`
  - `test_unadmitted_candidate_is_never_served`

## Modification guidance

- Change surface pool policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/surface_pool.py](../../../../../../src/learnloop/substrate/surface_pool.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
