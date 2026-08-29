---
title: "learnloop.curriculum.commitments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/commitments.py"
source_paths:
  - "src/learnloop/curriculum/commitments.py"
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
  - "learnloop.curriculum.commitments module"
  - "src/learnloop/curriculum/commitments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.commitments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.commitments` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P1 step 1 -- durable learner commitments (spec_p1_shared_substrate §3.1, §3.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py) |
| Source lines | 920 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PassiveActionCannotCommit(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 72) — A non-commit-class action tried to create a commitment (invariant 4, §9.1).
  - `__init__(self, action: str)` (line 75; internal)
- `class InvalidTarget(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 83) — A commitment target used an unknown target kind or role.
- `class UnknownCommitment(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 87)
  - `__init__(self, commitment_id: str)` (line 88; internal)
- `class EnvelopeWideningRejected(Exception)` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 93) — A shrink/change tried to WIDEN the depth envelope (§10.2, F4).
  - `__init__(self, dimension: str)` (line 101; internal)
- `envelope_widening_dimension(new_bounds: Mapping[str, Any], current_bounds: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 148) — Return the first bounds dimension on which ``new_bounds`` widens ``current_bounds``, or ``None`` if ``new_bounds`` is a subset (a shrink).
- `class CommitmentTarget` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 165)
  - `normalized(self) -> dict[str, Any]` (line 172; public)
- `class CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 179)
  - `as_dict(self) -> dict[str, Any]` (line 196; public)
- `class Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 201)
  - `as_dict(self) -> dict[str, Any]` (line 210; public)
- `target_set_hash(targets: Sequence[CommitmentTarget]) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 246) — Order-independent identity of the target set (§3.1 idempotency key).
- `create_commitment(repository: Repository, *, action: str, intent_text: str, targets: Sequence[Mapping[str, Any] | CommitmentTarget], depth_preset: str, interpretation_text: str | None=None, client_idempotency_key: str | None=None, goal_id: str | None=None, author: str='learner', learner_id: str='local', attention_bounds: Mapping[str, Any] | None=None, due_hint: str | None=None, hiatus_hint: str | None=None, reason: str | None=None, provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 300) — Create a durable commitment from an explicit commit-class action (§3.1).
- `append_commitment_version(repository: Repository, *, commitment_id: str, targets: Sequence[Mapping[str, Any] | CommitmentTarget] | None=None, intent_text: str | None=None, interpretation_text: str | None=None, goal_id: str | None=None, depth_preset: str | None=None, change_reason: str, author: str='learner', extra_events: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 414) — Append an immutable successor version.
- `add_target(repository: Repository, *, commitment_id: str, target: Mapping[str, Any] | CommitmentTarget, change_reason: str='target_added', author: str='learner', clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 473)
- `remove_target(repository: Repository, *, commitment_id: str, target_ref: str, change_reason: str='target_removed', author: str='learner', clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 496) — Remove a target: appends a commitment successor and stops future generation for it.
- `change_depth_policy(repository: Repository, *, commitment_id: str, policy: str, body: Mapping[str, Any] | None=None, change_reason: str='depth_policy_changed', author: str='learner', clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 528)
- `change_depth_envelope(repository: Repository, *, commitment_id: str, bounds: Mapping[str, Any], reviewed_edges: Sequence[Mapping[str, Any]]=(), change_reason: str='depth_envelope_changed', author: str='learner', allow_widen: bool=False, clock: Clock | None=None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 568)
- `change_disposition(repository: Repository, *, commitment_id: str, disposition: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 667) — Append a ``disposition_changed`` event only; disposition is a projection over events (§3.1), so no version bump.
- `pause(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 690)
- `resume(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 699)
- `retire(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 708)
- `satisfy_single_check(repository: Repository, *, commitment_id: str, administration_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 717) — One eligible delayed cold administration satisfies a ``test_me_later`` commitment (§3.1): ``one_check_pending`` -> ``satisfied``, never an open-ended review obligation.
- `record_milestone_reached(repository: Repository, *, commitment_id: str, milestone_slug: str, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 738) — Append ``depth_milestone_reached``: an achievement fact over the existing authored envelope.
- `record_depth_transition_committed(repository: Repository, *, commitment_id: str, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 763) — Append ``depth_transition_committed``: an activation fact over the existing authored envelope (A.3).
- `attach_family(repository: Repository, *, commitment_id: str, family_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 785)
- `detach_family(repository: Repository, *, commitment_id: str, family_id: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 795)
- `resolve_disposition(repository: Repository, commitment_id: str) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 809) — Fold ``commitment_events`` to one disposition (§3.1).
- `resolve_head(repository: Repository, commitment_id: str) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 836)
- `load_commitment(repository: Repository, commitment_id: str) -> Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 840)

### Module constants

- `COMMIT_ACTIONS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 35)
- `DEPTH_PRESETS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 39)
- `TARGET_KINDS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 43)
- `DISPOSITIONS` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 53)
- `_ACTION_DEFAULT_POLICY` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 61)
- `DEPTH_ENVELOPE_SCHEMA_VERSION` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 68)
- `DEPTH_POLICY_SCHEMA_VERSION` ([src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py), line 69)

## Internal implementation anchors

- `_bounds_value_is_subset(new_val: Any, old_val: Any) -> bool` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 109) — Is ``new_val`` provably contained in ``old_val`` for one bounds dimension?
- `_coerce_targets(targets: Sequence[Mapping[str, Any] | CommitmentTarget]) -> list[CommitmentTarget]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 218)
- `_version_hash(fields: Mapping[str, Any], targets: Sequence[CommitmentTarget], *, predecessor_version_id: str | None, version: int) -> str` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 252) — Chain-aware content hash: identity of this version's content plus its position in the append-only chain.
- `_default_depth_body(action: str, preset: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 274)
- `_default_envelope_body(preset: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 284)
- `_target_row(t: CommitmentTarget) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 400)
- `_append_depth_version(repository: Repository, *, head: CommitmentVersion, depth_policy_version_id: str | None, depth_envelope_version_id: str | None, event_kind: str, detail: Mapping[str, Any], change_reason: str, author: str, clock: Clock | None) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 616)
- `_loads(value: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 848)
- `_current_envelope_bounds(repository: Repository, envelope_version_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 856) — Bounds of the head's active depth envelope (empty when unset).
- `_version_from_row(row: Mapping[str, Any], targets: Sequence[Mapping[str, Any]]) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 868)
- `_require_head(repository: Repository, commitment_id: str) -> CommitmentVersion` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 897)
- `_load_commitment(repository: Repository, commitment_id: str, *, created: bool, merge_candidate: bool=False) -> Commitment` ([source](../../../../../../src/learnloop/curriculum/commitments.py), line 905)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; statically calls `change_depth_envelope`, `change_depth_policy`, `pause`, `record_milestone_reached`, `resolve_disposition`, `resolve_head`, `resume`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `module`; statically calls `change_depth_envelope`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `module`; statically calls `_coerce_targets`, `_default_depth_body`, `_default_envelope_body`, `_target_row`, `_version_hash`, `target_set_hash`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; statically calls `record_milestone_reached`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `module`; statically calls `change_depth_envelope`, `change_depth_policy`, `create_commitment`, `retire`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `create_commitment`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `create_commitment`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; statically calls `resolve_disposition`, `resolve_head`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`; statically calls `resolve_head`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`

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

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]], [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]], [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]], [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — direct import
  - `test_arc_pins_depth_and_maps_stages`
  - `test_shrink_envelope_rejects_widening`
- [tests/test_commitments.py](../../../../../../tests/test_commitments.py) — direct import
  - `test_depth_envelope_change_forces_version_bump`
  - `test_depth_policy_change_forces_version_bump_and_typed_event`
  - `test_different_target_set_creates_distinct_commitment`
  - `test_milestone_reached_does_not_bump_version`
  - `test_missing_key_returns_merge_candidate_not_silent_merge`
  - `test_noop_depth_envelope_change_short_circuits`
  - `test_noop_depth_policy_change_short_circuits`
  - `test_passive_action_cannot_create_commitment`
  - `test_pause_resume_retire_disposition`
  - `test_reference_only_disposition_change`
  - `test_target_removal_appends_successor`
  - `test_test_me_later_starts_pending_then_satisfied`
  - `test_version_append_preserves_prior_bytes`
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
  - `test_rollback_is_all_or_nothing_on_mid_failure`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_stale_ownership_still_prevents_double_administration`
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_harness_activation_activates_exactly_one_edge`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
  - `test_journey6_passive_action_cannot_create_commitment`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_retirement_preserves_commitment_and_evidence`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
- [tests/test_state_signals.py](../../../../../../tests/test_state_signals.py) — direct import
  - `test_misspecification_scoped_to_commitment_head_targets`

## Modification guidance

- Change commitments policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/commitments.py](../../../../../../src/learnloop/curriculum/commitments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
