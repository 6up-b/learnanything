---
title: "learnloop.substrate.compat.substrate_cutover"
type: "module-reference"
status: "current"
refactor_status: "COMPAT"
version: "1.0.0"
source_path: "src/learnloop/substrate/compat/substrate_cutover.py"
source_paths:
  - "src/learnloop/substrate/compat/substrate_cutover.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate.compat"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.compat.substrate_cutover module"
  - "src/learnloop/substrate/compat/substrate_cutover.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/compat"
  - "layer/domain"
  - "package/learnloop-substrate-compat"
---

# `learnloop.substrate.compat.substrate_cutover`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.compat.substrate_cutover` exists within [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] to own the behavior summarized by its module contract: P1 step 9 -- dual-write cutover, narrowed by the 2026-07-19 owner decision.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py) |
| Source lines | 721 |
| Owning package | [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] |
| Architecture layer | `domain` |
| Refactor status | `COMPAT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Frozen compatibility boundary
> This live module is retained for old vaults. It is green but not a target for new feature growth.

## Public API

- `purpose_adapters_live(algorithm_version: str | None) -> bool` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 66) — Whether the purpose-adapter path is the LIVE scheduling authority for a vault.
- `scheduling_write_authority(algorithm_version: str | None) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 84) — ``'purpose_adapter'`` for a live mvp-0.8 vault, else ``'legacy_fsrs'`` (§7.4 gate 6: new-administration scheduling can only be written through the adapter on a live vault; a direct legacy write for a new administration is rejected).
- `class LegacyWriteRejected(Exception)` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 92) — §7.4 gate 6: a direct legacy scheduling write was attempted for a new administration on a live mvp-0.8 vault.
- `reject_legacy_scheduling_write(algorithm_version: str | None, *, administration_id: str) -> None` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 98) — Guard the new-substrate write path (§7.4 gate 6).
- `guarded_legacy_scheduling_write(repository: Repository, *, algorithm_version: str | None, administration_id: str, card_lineage_id: str, scheduler_algorithm_version: str=P1_SCHEDULER_ALGORITHM_VERSION, difficulty: float | None=None, stability: float | None=None, retrievability: float | None=None, due_at: str | None=None, model_label: str='fsrs', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 109) — The service-layer CHOKEPOINT that gate 6 enforces (§7.4 gate 6).
- `class InjectedFault(Exception)` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 154) — A fault injected by the fault-injection test after a named write boundary.
- `class SubstrateWriteReceipt` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 166)
  - `complete(self) -> bool` (line 177; public)
  - `as_dict(self) -> dict[str, Any]` (line 180; public)
- `submit_administration_response(repository: Repository, *, surface: Mapping[str, Any], card_version_id: str, family_id: str, purpose: str, card_lineage_id: str, algorithm_version: str, scheduler_algorithm_version: str=P1_SCHEDULER_ALGORITHM_VERSION, review_event: Mapping[str, Any] | None, eligible: bool, failed: bool, attempt_id: str | None=None, response_ref: str | None=None, feedback_condition: str | None=None, admin_context: Mapping[str, Any] | None=None, reading_phase: str | None=None, snapshot_hash: str | None=None, snapshot_json: str='{}', prior_reviews: Sequence[Mapping[str, Any]]=(), fault_after: Sequence[str]=(), clock: Clock | None=None) -> SubstrateWriteReceipt` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 198) — Write the complete new-substrate lineage for one administration as ONE fail-safe unit (§7.4): administration (+ once-only rendered exposure) -> submitted exposure -> observation -> adapter-specific scheduling/evidence projection.
- `class NoObservationToRebuild(Exception)` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 392) — A deferred-projection rebuild was requested for an administration that has no durable observation in the ledger.
- `rebuild_deferred_projection(repository: Repository, *, administration_id: str, card_lineage_id: str, scheduler_algorithm_version: str=P1_SCHEDULER_ALGORITHM_VERSION, prior_reviews: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 398) — Deterministically reapply the scheduling/evidence projection for a deferred administration by RE-DERIVING its inputs from the durable ledger (§7.5) -- never from caller-supplied evidence: - eligibility comes from the observation's recorded ``evidence_eligibility``; - the FSRS re…
- `class GateOutcome` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 458)
  - `cleared(self) -> bool` (line 466; public)
  - `as_dict(self) -> dict[str, Any]` (line 469; public)
- `class CutoverGateReport` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 480)
  - `all_cleared(self) -> bool` (line 486; public)
  - `as_dict(self) -> dict[str, Any]` (line 489; public)
- `run_cutover_gates(repository: Repository, *, algorithm_version: str, clock: Clock | None=None) -> CutoverGateReport` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 621) — Evaluate the six §7.4 cutover gates as a hard sequential barrier, narrowed by the 2026-07-19 owner decision (no old-vault migration): legacy-row *equivalence* gates are N/A; new-substrate write-completeness / atomicity / failure / rollback gates stay fully live.

### Module constants

- `P1_SCHEDULER_ALGORITHM_VERSION` ([src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 45)
- `PURPOSE_ADAPTERS_LIVE_FROM` ([src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 52)
- `PURPOSE_ADAPTERS_LIVE_SUCCESSORS` ([src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 59)
- `WRITE_BOUNDARIES` ([src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 162)
- `_PURPOSE_MATRIX` ([src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 500)

### Explicit exports

`__all__` declares:

- `P1_SCHEDULER_ALGORITHM_VERSION`
- `PURPOSE_ADAPTERS_LIVE_FROM`
- `PURPOSE_ADAPTERS_LIVE_SUCCESSORS`
- `P0_ALGORITHM_VERSION`
- `KM_ALGORITHM_VERSION`
- `CANONICAL_STATE_VERSIONS`
- `purpose_adapters_live`
- `scheduling_write_authority`
- `reject_legacy_scheduling_write`
- `guarded_legacy_scheduling_write`
- `LegacyWriteRejected`
- `InjectedFault`
- `WRITE_BOUNDARIES`
- `SubstrateWriteReceipt`
- `submit_administration_response`
- `rebuild_deferred_projection`
- `NoObservationToRebuild`
- `GateOutcome`
- `CutoverGateReport`
- `run_cutover_gates`

## Internal implementation anchors

- `_existing_observation(repository: Repository, administration_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 193)
- `_enqueue_rebuild(repository: Repository, administration_id: str, scheduler_algorithm_version: str, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 379)
- `_gate_purpose_side_effects() -> tuple[str, str]` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 508) — Gate 4 (LIVE): the §9.4 purpose matrix -- the same synthetic response under each purpose produces the exact §3.10 scheduling delta.
- `_gate3_probe_lineage(repository: Repository, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 522) — A throwaway practice card + lineage the gate 3 drive can project onto.
- `_gate_new_scheduling_projection(repository: Repository, algorithm_version: str, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 546) — Gate 3 (LIVE, reframed): the NARROWED scope drops legacy-row equivalence.
- `_gate_legacy_writes_rejected(repository: Repository, algorithm_version: str, clock: Clock | None) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py), line 585) — Gate 6 (LIVE): enforced at the service-layer CHOKEPOINT (:func:`guarded_legacy_scheduling_write`).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `Rating`, `apply_review`; calls `apply_review`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `module`; calls `canonical_hash`, `canonical_json`, `evidence_eligibility_for`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `OpportunisticDiagnosisRejected`, `module`; calls `PracticeAdapter`, `project_administration`, `resolve_adapter`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `module`; calls `start_lineage`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_event_sufficiency.py](../../../../../../../tests/test_event_sufficiency.py) — direct import
- [tests/test_journey6.py](../../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
- [tests/test_substrate_cutover.py](../../../../../../../tests/test_substrate_cutover.py) — direct import
  - `test_barrier_blocks_every_later_gate_when_an_early_gate_fails`
  - `test_deferred_projection_rebuild_is_deterministic_and_idempotent`
  - `test_diagnostic_and_assessment_write_no_practice_schedule`
  - `test_dual_write_retry_does_not_duplicate_events`
  - `test_fault_after_each_boundary_recovers_to_the_no_fault_state`
  - `test_gate3_drives_adapter_and_matches_independent_fsrs`
  - `test_gate6_chokepoint_actually_blocks_the_write`
  - `test_gate6_legacy_write_rejected_only_on_live_vault`
  - `test_gates_are_ordinal_and_ordered`
  - `test_module_override_forces_live_regardless_of_version`
  - `test_projection_failure_defers_without_half_update`
  - `test_purpose_adapters_live_from_registry_entry_is_bound_to_code`
  - `test_purpose_adapters_live_only_for_mvp08`
  - `test_rebuild_refuses_when_no_observation_exists`
  - `test_six_gates_barrier_all_cleared_on_mvp08`
  - `test_submit_writes_full_lineage_in_one_unit`

## Modification guidance

- Change substrate cutover policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/compat/substrate_cutover.py](../../../../../../../src/learnloop/substrate/compat/substrate_cutover.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
