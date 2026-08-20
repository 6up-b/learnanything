---
title: "learnloop.scheduling.controller_cutover"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/controller_cutover.py"
source_paths:
  - "src/learnloop/scheduling/controller_cutover.py"
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
  - "learnloop.scheduling.controller_cutover module"
  - "src/learnloop/scheduling/controller_cutover.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.controller_cutover`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.controller_cutover` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 §14.2 dual-controller cutover -- step 3 coexistence window (design §C).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/controller_cutover.py](../../../../../../src/learnloop/scheduling/controller_cutover.py) |
| Source lines | 499 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class LiveNextAction` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 56) — The next action for a P2 run under the cutover.
  - `as_dict(self) -> dict[str, Any]` (line 71; public)
- `staged_next_action(repository: Repository, run_id: str, *, vault: Any, session: Any | None=None, live: bool | None=None, receipt_key: str | None=None, clock: Clock | None=None) -> LiveNextAction` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 134) — Consult the staged policy LIVE for a P2 run's next action (design §C step 3).
- `advance_live(repository: Repository, run_id: str, *, vault: Any, session: Any | None=None, idempotency_key: str, live: bool | None=None, clock: Clock | None=None, **extra: Any) -> tuple[GPR.AdvanceResult | None, LiveNextAction]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 196) — The LIVE P2 next-action path: consult the staged policy, then advance the run to the resolved successor.
- `rollback(repository: Repository, *, reason: str='cutover_rollback', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 252) — Return every staged-owned commitment to legacy atomically under one receipt.
- `cross_seam_exposure_probe(repo_factory: Callable[[], Repository], *, open_administration: Callable[[Repository], Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 271) — Drive two concurrent administrations at the SAME surface through two independent connections (the two controllers), and report the serialization outcome.
- `class GateOutcome` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 320)
  - `cleared(self) -> bool` (line 328; public)
  - `as_dict(self) -> dict[str, Any]` (line 331; public)
- `class CutoverGateReport` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 337)
  - `all_cleared(self) -> bool` (line 342; public)
  - `as_dict(self) -> dict[str, Any]` (line 345; public)
- `run_cutover_gates(repository: Repository, *, vault: Any, session: Any, run_id: str, commitment_id: str, exposure_probe: Callable[[], dict[str, Any]] | None=None, clock: Clock | None=None) -> CutoverGateReport` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 445) — Evaluate the six §14.2 step-3 gates (design §C) as a hard sequential barrier: a gate is evaluated only if every prior gate cleared.

### Module constants

- `STAGED_POLICY_LIVE_FOR_P2` ([src/learnloop/scheduling/controller_cutover.py](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 46)
- `_EVSI_VETO_REASONS` ([src/learnloop/scheduling/controller_cutover.py](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 52)

## Internal implementation anchors

- `_commitment_item_refs(vault: Any, repository: Repository, commitment_id: str) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 80) — The practice items a commitment owns (its head ``learning_object`` / ``legacy_practice_item`` targets, resolved down to vault item ids).
- `_constraint_or_evsi_veto(result: sp.DecisionResult) -> str | None` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 101) — Return the named constraint/EVSI reason iff the staged decision legitimately vetoes the canonical successor, else None.
- `_run_signal_hints(run: Mapping[str, Any], state: GPR.RunState) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 119) — Stage material the P2 run knows directly (§4.2 rungs the golden-path machine owns): mode, whether a terminal assessment has been shown, and goal satisfaction.
- `_gate_shadow_parity(repository: Repository, vault: Any, session: Any, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 350) — (a) Shadow parity baseline: a staged decision is logged alongside the legacy comparator with ZERO authority; assert the comparator log is complete.
- `_gate_ownership_assignment(repository: Repository, commitment_id: str, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 365) — (b) Ownership assignment for P2 runs: the P2 commitment is assigned to staged and a non-P2 commitment is refused.
- `_gate_staged_live(repository: Repository, run_id: str, vault: Any, session: Any, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 379) — (c) Staged policy LIVE for owned commitments: the bridge drives the run and is decision-equivalent to the canonical successor (no spurious veto), persisting a ``mode='live'`` decision.
- `_gate_affect_one_edge(repository: Repository, vault: Any, session: Any, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 406) — (e) Affect check + one-edge discipline preserved under live mode: the affect step precedes the (at most one) depth edge and U-018 stays inert (activates nothing).
- `_gate_rollback(repository: Repository, commitment_id: str, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/controller_cutover.py), line 431) — (f) Rollback: the single registered switch returns owned commitments to legacy atomically with a receipt; legacy ownership is restored exactly.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; calls `advance`, `project_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `assign_p2_run`, `is_staged_owned`, `ownership_events`, `resolve_owner`, `rollback_to_legacy`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; calls `build_snapshot`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `decision_row`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `StateSignals`, `decide`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`; calls `derive_signals`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_advance_live_veto_persists_typed_marker`
  - `test_all_six_cutover_gates_pass_in_order`
  - `test_bridge_goes_live_and_is_decision_equivalent_when_owned`
  - `test_bridge_returns_canonical_when_not_staged_owned`
  - `test_constraint_emptied_feasible_set_is_a_veto`
  - `test_evsi_abstain_is_a_veto`
  - `test_full_live_walk_reproduces_canonical_sequence`
  - `test_gate_off_forces_legacy_even_when_owned`
  - `test_ladder_stop_is_not_a_veto`
  - `test_ownership_only_emptying_is_not_a_veto`
  - `test_rollback_switch_returns_owned_to_legacy`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_same_surface_exactly_one_wins_via_shared_ledger`

## Modification guidance

- Change controller cutover policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/controller_cutover.py](../../../../../../src/learnloop/scheduling/controller_cutover.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
