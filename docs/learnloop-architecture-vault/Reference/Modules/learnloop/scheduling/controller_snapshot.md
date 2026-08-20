---
title: "learnloop.scheduling.controller_snapshot"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/controller_snapshot.py"
source_paths:
  - "src/learnloop/scheduling/controller_snapshot.py"
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
  - "learnloop.scheduling.controller_snapshot module"
  - "src/learnloop/scheduling/controller_snapshot.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.controller_snapshot`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.controller_snapshot` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 1 -- the ControllerSnapshot (spec §3.1, design B step 1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py) |
| Source lines | 414 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Candidate` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 63) — One selection candidate.
  - `hashable(self) -> dict[str, Any]` (line 95; public)
- `class CommitmentSummary` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 121)
  - `hashable(self) -> dict[str, Any]` (line 132; public)
- `class ControllerSnapshot` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 147)
  - `commitment(self, commitment_id: str) -> CommitmentSummary | None` (line 167; public)
- `build_snapshot(vault: LoadedVault, repository: Repository, session: Any | None=None, *, candidates: Sequence[Candidate] | None=None, clock: Clock | None=None) -> ControllerSnapshot` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 269) — Assemble one immutable, content-hashed ControllerSnapshot from bounded bulk reads (§3.1).
- `persist_snapshot(repository: Repository, snapshot: ControllerSnapshot, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 394) — Persist (dedupe on content hash).

### Module constants

- `SNAPSHOT_SCHEMA_VERSION` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 38)
- `CONSERVATIVE_DURATION_MINUTES` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 43)
- `_PURPOSE_DIAGNOSTIC` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 46)
- `_PURPOSE_INSTRUCTIONAL` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 47)
- `_PURPOSE_PRACTICE` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 48)
- `_PURPOSE_ASSESSMENT` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 49)
- `_DIAGNOSTIC_MODES` ([src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 51)

## Internal implementation anchors

- `_purpose_for_mode(practice_mode: str | None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 54)
- `_controller_param_manifest_hash() -> str` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 174) — Deterministic hash over the registered controller decision/structural params (owner in the controller modules).
- `_commitment_summary(repository: Repository, commitment_id: str) -> CommitmentSummary | None` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 190)
- `_candidates_from_vault(vault: LoadedVault, states: Mapping[str, Any]) -> list[Candidate]` ([source](../../../../../../src/learnloop/scheduling/controller_snapshot.py), line 229) — Every practice item as a staged-controller candidate.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `Candidate`, `ControllerSnapshot`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `build_snapshot`
- [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]] — imports `Candidate`, `ControllerSnapshot`
- [[Reference/Modules/learnloop/scheduling/interleaving|learnloop.scheduling.interleaving]] — imports `Candidate`, `ControllerSnapshot`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `module`; statically calls `build_snapshot`
- [[Reference/Modules/learnloop/scheduling/short_session|learnloop.scheduling.short_session]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `build_snapshot`, `persist_snapshot`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`, `resolve_head`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `module`; calls `manifest`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `bulk_commitment_rows`, `bulk_exposure_events`, `upsert_snapshot`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]], [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]], [[Reference/Modules/learnloop/scheduling/interleaving|learnloop.scheduling.interleaving]], [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] and 3 more.

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
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_constraint_emptied_feasible_set_is_a_veto`
  - `test_ownership_only_emptying_is_not_a_veto`
- [tests/test_controller_snapshot.py](../../../../../../tests/test_controller_snapshot.py) — direct import
  - `test_reserved_assessment_surfaces_load_into_snapshot`
  - `test_snapshot_construction_is_bounded_no_per_candidate_query`
  - `test_snapshot_contains_no_cold_answer_material`
  - `test_snapshot_is_deterministic_and_hash_stable`
  - `test_snapshot_persists_deduped_on_content_hash`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_assessment_reserve_not_poached_by_practice_at_plan_time`
- [tests/test_dispersion.py](../../../../../../tests/test_dispersion.py) — direct import
  - `test_acquisition_stays_coherent`
  - `test_assessment_follows_frozen_distribution`
  - `test_discrimination_allows_interleaving`
  - `test_dispersion_inert_when_enough_intervening_administrations`
  - `test_lapse_retry_is_exempt_but_earns_no_independent_evidence`
  - `test_near_kin_fingerprint_dispersion`
  - `test_practice_block_is_not_dispersed`
  - `test_same_facet_fresh_evidence_not_back_to_back`
  - `test_unstaged_block_leaves_interleaving_inert`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_staged_controller_admits_both_instruments`
- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
  - `test_short_session_prefers_admitted_short_p1_patterns`
  - `test_short_session_retry_after_commit_is_idempotent`
  - `test_short_session_stops_honestly_when_nothing_fits`
  - `test_three_minute_activity_completes_a_session`
- [tests/test_shadow_components.py](../../../../../../tests/test_shadow_components.py) — direct import
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
  - `test_high_shadow_score_cannot_resurrect_infeasible_candidate`
  - `test_no_feasible_activity_is_typed_stop`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
  - `test_evsi_selector_ranks_only_within_feasible_set`
  - `test_evsi_stop_is_a_typed_stop_not_no_feasible_activity`
- [tests/test_state_signals.py](../../../../../../tests/test_state_signals.py) — direct import
  - `test_derive_signals_composes_all_five`
  - `test_misspecification_false_when_alarm_resolved`
  - `test_misspecification_false_when_no_alarm`
  - `test_misspecification_scoped_to_commitment_head_targets`
  - `test_misspecification_true_with_pending_generation_need`
  - `test_pending_items_episode_is_not_measurement_value`
  - `test_retention_near_limit_when_overdue`
  - `test_retention_not_near_limit_when_future_due`
  - `test_robust_value_positive_with_in_progress_episode`
  - `test_robust_value_zero_without_open_episode`

## Modification guidance

- Change controller snapshot policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/controller_snapshot.py](../../../../../../src/learnloop/scheduling/controller_snapshot.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
