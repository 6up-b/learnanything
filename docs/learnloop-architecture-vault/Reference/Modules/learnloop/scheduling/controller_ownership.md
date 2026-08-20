---
title: "learnloop.scheduling.controller_ownership"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/controller_ownership.py"
source_paths:
  - "src/learnloop/scheduling/controller_ownership.py"
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
  - "learnloop.scheduling.controller_ownership module"
  - "src/learnloop/scheduling/controller_ownership.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.controller_ownership`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.controller_ownership` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 §14.2 step 3 -- commitment-scoped controller ownership (design §A.2 / §C step 3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py) |
| Source lines | 425 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class NotAP2GoldenPathCommitment(Exception)` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 48) — Refused a staged-ownership assignment for a commitment that is not a P2 golden-path commitment (design §A.2 rule 1: staged owns only commitments with a confirmed goal contract + depth policy + depth envelope).
- `class StagedOwnedAdministrationRefused(Exception)` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 54) — An administration surface (legacy queue, probe episode, held-out exam) refused to serve a learning object / practice item that a staged-owned P2 commitment owns (design §A.2 rule 3, the dual-authority exclusion).
- `class ExamReservationOwnershipConflict(Exception)` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 61) — A staged-ownership assignment and a held-out exam reservation would cover the same practice item(s).
- `is_p2_golden_path_commitment(repository: Repository, commitment_id: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 73) — A P2 golden-path commitment has a confirmed goal contract AND a depth policy AND a depth envelope (the three things ``golden_path_confirm`` mints atomically).
- `ownership_head(repository: Repository, commitment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 94)
- `rebuild_ownership_head(repository: Repository, *, commitment_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 102) — Rebuild the current-owner head projection by folding ``controller_ownership_events`` (design §A.2: the head is a REBUILDABLE projection of the append-only event log, not a source of truth).
- `resolve_owner(repository: Repository, commitment_id: str) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 159) — The current owner of a commitment.
- `is_staged_owned(repository: Repository, commitment_id: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 166)
- `ownership_events(repository: Repository, commitment_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 170)
- `assign(repository: Repository, *, commitment_id: str, owner: str, reason: str, receipt_id: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 234) — Record a durable ownership transition (append-only + head upsert), atomically.
- `assign_p2_run(repository: Repository, *, commitment_id: str, reason: str='p2_golden_path_run', detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 271) — Assign a P2 golden-path commitment to the staged controller (design §A.2 rule 1).
- `staged_owned_commitment_ids(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 306) — Every commitment whose current head is owned by the staged controller.
- `staged_owned_refs(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 316) — The atomic dual-authority exclusion input shared by every administration surface (design §A.2 rule 3): the union of every staged-owned commitment's head targets of kind ``learning_object`` / ``legacy_practice_item`` (raw refs, not resolved against a vault).
- `is_learning_object_staged_owned(repository: Repository, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 356) — True when the WHOLE learning object is a head target of a staged-owned commitment (an ``learning_object``-kind ref).
- `staged_owned_practice_item_ids(vault: Any, repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 364) — The legacy-scheduler EXCLUSION set (design §A.2 rule 3, the coexistence seam): every practice item that belongs to a staged-owned commitment, resolved down from the commitment's head targets (``learning_object`` / ``legacy_practice_item`` kinds).
- `rollback_to_legacy(repository: Repository, *, reason: str='cutover_rollback', commitment_ids: Sequence[str] | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 388) — Return owned commitments to the legacy controller atomically under ONE shared receipt (design §C step-3 gate f).

### Module constants

- `OWNERSHIP_POLICY_VERSION` ([src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 39)
- `STAGED` ([src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 41)
- `LEGACY` ([src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 42)
- `DEFAULT_OWNER` ([src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 45)

## Internal implementation anchors

- `_append_transition(connection: Any, *, commitment_id: str, to_owner: str, reason: str, receipt_id: str, detail: Mapping[str, Any] | None, now: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 180) — Append one ownership transition + upsert the head, INSIDE an open transaction.
- `_commitment_refs(repository: Repository, commitment_id: str) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/controller_ownership.py), line 342) — The head-target refs (learning_object / legacy_practice_item) of ONE commitment.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `module`; statically calls `StagedOwnedAdministrationRefused`, `is_learning_object_staged_owned`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `ExamReservationOwnershipConflict`, `module`, `staged_owned_practice_item_ids`; statically calls `ExamReservationOwnershipConflict`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `assign_p2_run`, `is_staged_owned`, `ownership_events`, `resolve_owner`, `rollback_to_legacy`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `module`; statically calls `staged_owned_practice_item_ids`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]], [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_all_six_cutover_gates_pass_in_order`
  - `test_bridge_goes_live_and_is_decision_equivalent_when_owned`
  - `test_full_live_walk_reproduces_canonical_sequence`
  - `test_gate_off_forces_legacy_even_when_owned`
  - `test_rollback_switch_returns_owned_to_legacy`
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
  - `test_assign_is_idempotent_and_append_only`
  - `test_default_owner_is_legacy`
  - `test_empty_ownership_is_a_noop_exclusion`
  - `test_legacy_scheduler_excludes_staged_owned_items`
  - `test_non_p2_commitment_refused_staged_ownership`
  - `test_p2_commitment_assigned_to_staged_with_receipt`
  - `test_rebuild_ownership_head_reconstructs_from_events`
  - `test_rollback_is_all_or_nothing_on_mid_failure`
  - `test_rollback_returns_to_legacy_and_restores_queue`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_stale_ownership_still_prevents_double_administration`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
  - `test_assign_refused_when_item_already_exam_reserved`
  - `test_staged_owned_item_never_surfaces_in_probe_slate`
  - `test_staged_owned_item_not_reservable_into_exam_pool`
  - `test_unowned_probe_slate_is_byte_identical`
  - `test_wholly_staged_owned_lo_refuses_probe_administration`

## Modification guidance

- Change controller ownership policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/controller_ownership.py](../../../../../../src/learnloop/scheduling/controller_ownership.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
