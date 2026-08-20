---
title: "learnloop.curriculum.depth_transition"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/depth_transition.py"
source_paths:
  - "src/learnloop/curriculum/depth_transition.py"
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
  - "learnloop.curriculum.depth_transition module"
  - "src/learnloop/curriculum/depth_transition.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.depth_transition`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.depth_transition` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P1 step 8 -- the deterministic one-edge depth-transition service (spec_p1_shared_substrate §5.7, §3.1.1, §10; invariant 12).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/depth_transition.py](../../../../../../src/learnloop/curriculum/depth_transition.py) |
| Source lines | 308 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TransitionProposal` ([source](../../../../../../src/learnloop/curriculum/depth_transition.py), line 40) — A non-activating outcome: the transition was refused, deferred to suggest_next, or requires authoring.
  - `committed(self) -> bool` (line 51; public)
  - `as_dict(self) -> dict[str, Any]` (line 54; public)
- `class TransitionReceipt` ([source](../../../../../../src/learnloop/curriculum/depth_transition.py), line 66) — A committed one-edge transition (§5.7 step 7).
  - `committed(self) -> bool` (line 79; public)
  - `as_dict(self) -> dict[str, Any]` (line 82; public)
- `commit_one_edge(repository: Repository, *, commitment_id: str, milestone: str, selected_edge_id: str, evidence_receipt: Mapping[str, Any], goal_id: str | None=None, proposed_contract_body: Mapping[str, Any] | None=None, progression_decision: Mapping[str, Any] | None=None, fork_edit: Mapping[str, Any] | None=None, scheduler_algorithm_version: str='fsrs6', live_activation_enabled: bool | None=None, author: str='controller', clock: Clock | None=None) -> TransitionReceipt | TransitionProposal` ([source](../../../../../../src/learnloop/curriculum/depth_transition.py), line 116) — Commit at most one reviewed inside-envelope depth edge (§5.7).

### Module constants

- `LIVE_ACTIVATION_ENABLED` ([src/learnloop/curriculum/depth_transition.py](../../../../../../src/learnloop/curriculum/depth_transition.py), line 36)

## Internal implementation anchors

- `_resolve_policy(repository: Repository, policy_version_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/curriculum/depth_transition.py), line 96)
- `_reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/depth_transition.py), line 105)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; statically calls `commit_one_edge`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; statically calls `commit_one_edge`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `commit_one_edge`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `module`; calls `append_authorized_depth_successor`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `module`; calls `classify_edit`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]], [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — direct import
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — direct import
  - `test_achieved_milestone_stays_when_a_deeper_one_activates`
  - `test_argument_alone_cannot_activate_while_constant_off`
  - `test_auto_within_envelope_activates_exactly_one_reviewed_edge`
  - `test_capability_change_forks_with_no_inherited_stability`
  - `test_commit_one_edge_retry_is_idempotent`
  - `test_fork_retry_does_not_duplicate_lineage`
  - `test_gate_off_stores_intent_and_behaves_as_suggest_next`
  - `test_hold_at_target_cannot_auto_activate`
  - `test_insufficient_evidence_is_refused`
  - `test_module_default_gate_is_off`
  - `test_outside_envelope_edge_needs_authoring`
  - `test_review_required_edit_parks_without_committing`
  - `test_suggest_next_policy_cannot_auto_activate`
  - `test_surface_only_change_does_not_fork`
  - `test_unreviewed_or_missing_edge_is_refused`
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_harness_activation_activates_exactly_one_edge`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`

## Modification guidance

- Change depth transition policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/depth_transition.py](../../../../../../src/learnloop/curriculum/depth_transition.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
