---
title: "learnloop.substrate.surface_mint"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/surface_mint.py"
source_paths:
  - "src/learnloop/substrate/surface_mint.py"
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
  - "learnloop.substrate.surface_mint module"
  - "src/learnloop/substrate/surface_mint.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.surface_mint`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.surface_mint` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P1 step 7 -- mint/gate infrastructure + durable pre-mint jobs (spec_p1_shared_substrate §5.2, §5.3, §5.6; §9.3, §9.7).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py) |
| Source lines | 560 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MintWorkerError(RuntimeError)` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 71) — A mint worker failure.
- `class GateOutcome` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 76)
- `class GateResult` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 83)
  - `admitted(self) -> bool` (line 89; public)
  - `first_failure(self) -> str | None` (line 93; public)
  - `as_dict(self) -> dict[str, Any]` (line 99; public)
- `request_candidates(repository: Repository, *, card_version_id: str, anchor_surface_id: str | None=None, requested_angle: Mapping[str, Any] | None=None, generator_version: str=MINT_GENERATOR_VERSION, gate_policy_version: str=MINT_GATE_POLICY_VERSION, token_cost: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 115) — Enqueue a durable, idempotent pre-mint job (§5.6).
- `claim_next_mint_job(repository: Repository, *, worker_id: str, lease_seconds: int=300, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 144) — Claim the next pending mint job under a lease (§5.6, 033 pattern).
- `run_all_gates(repository: Repository, *, request: Mapping[str, Any], candidate: Mapping[str, Any]) -> GateResult` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 216) — Run the §5.2 gates on a generated candidate.
- `process_mint_job(repository: Repository, *, request: Mapping[str, Any], candidate: Mapping[str, Any], reviewer: str='structural_gate', clock: Clock | None=None) -> GateResult` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 340) — Run the gates on a claimed job's candidate and transition the request: ``candidate_ready`` then ``admitted`` on pass, ``rejected`` on gate failure.
- `admit_candidate(repository: Repository, *, request_id: str, candidate_surface_id: str | None, gate_result: GateResult | None=None, lease_epoch: int | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 407) — Admit a gate-passing candidate into the pool (§5.2).
- `reject_candidate(repository: Repository, *, request_id: str, gate_result: GateResult | None=None, failure_reason: str | None=None, lease_epoch: int | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 457) — Reject a gate-failing candidate (§5.2).
- `fail_mint_job(repository: Repository, *, request_id: str, failure_reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 476) — Mark a job ``failed`` (generator error / interrupted lease).
- `obsolete_mint_work_for_card_versions(repository: Repository, card_version_ids: Sequence[str], *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 490) — Card/family retirement makes not-yet-terminal mint work ``obsolete`` (§5.6).
- `class RotationDecision` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 525)
- `rotation_decision(repository: Repository, *, surface_id: str, warmth_threshold: float | None=None, cadence: int | None=None) -> RotationDecision` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 533) — Decide whether a rotating surface needs rotation (§5.3): rotate once the warmth projection crosses the registered threshold OR the exposure cadence is reached.
- `needs_rotation(repository: Repository, *, surface_id: str) -> bool` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 555)

### Module constants

- `MINT_GATE_POLICY_VERSION` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 41)
- `MINT_GENERATOR_VERSION` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 42)
- `ROTATION_CADENCE_ADMINISTRATIONS` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 46)
- `SPARE_SURFACE_COUNT` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 49)
- `GATE_NAMES` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 54)
- `_UNSEEN_CREDIT_PURPOSES` ([src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py), line 68)

## Internal implementation anchors

- `_card_bounds(repository: Repository, card_version_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 171)
- `_within_task_feature_bounds(features: Mapping[str, Any], bounds: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 181) — Every declared task-feature bound must hold.
- `_within_difficulty_bounds(difficulty: Any, bounds: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 204)
- `_stale_lease_result(request: Mapping[str, Any], reason: str) -> GateResult` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 329) — A non-admitting result for a job that is no longer this worker's to process (B1 fencing).
- `_mark_surface_admitted(repository: Repository, *, surface_id: str, gate_result: GateResult, admitted: bool, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 391) — Raw authoring write -- private (B5).
- `_administration_count(repository: Repository, surface_id: str) -> int` ([source](../../../../../../src/learnloop/substrate/surface_mint.py), line 505) — Administrations of the CARD this surface belongs to (§5.3 cadence).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `obsolete_mint_work_for_card_versions`; statically calls `obsolete_mint_work_for_card_versions`
- [[Reference/Modules/learnloop/substrate/surface_pool|learnloop.substrate.surface_pool]] — imports `module`; statically calls `request_candidates`, `rotation_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `familiarity_projection_v1`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/substrate/surface_pool|learnloop.substrate.surface_pool]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
- [tests/test_surface_mint.py](../../../../../../tests/test_surface_mint.py) — direct import
  - `test_admit_candidate_without_passing_gate_raises`
  - `test_admit_marks_surface_admitted_and_rotation_eligible`
  - `test_anchored_candidate_passes_comparative_and_verbatim_rubric`
  - `test_cache_race_does_not_double_admit`
  - `test_candidate_identical_to_anchor_fails_comparative_gate`
  - `test_expired_lease_recovery_rejects_stale_worker_write`
  - `test_fixed_surface_never_auto_rotates`
  - `test_lease_lets_exactly_one_worker_drain`
  - `test_no_anchor_enqueue_is_idempotent_under_concurrency`
  - `test_novelty_gate_blocks_exposed_exact_hash`
  - `test_purpose_leakage_blocks_assessment_hard_collision`
  - `test_rejected_candidate_retained_but_not_admitted`
  - `test_reprocessing_admitted_job_never_double_admits`
  - `test_request_candidates_is_idempotent`
  - `test_retirement_obsoletes_queued_mint_work`
  - `test_rotation_triggers_after_exposure_cadence`
  - `test_submission_usable_when_mint_workers_down`

## Modification guidance

- Change surface mint policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/surface_mint.py](../../../../../../src/learnloop/substrate/surface_mint.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
