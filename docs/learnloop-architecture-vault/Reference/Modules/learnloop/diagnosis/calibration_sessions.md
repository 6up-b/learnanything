---
title: "learnloop.diagnosis.calibration_sessions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/calibration_sessions.py"
source_paths:
  - "src/learnloop/diagnosis/calibration_sessions.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.diagnosis.calibration_sessions module"
  - "src/learnloop/diagnosis/calibration_sessions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.calibration_sessions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.calibration_sessions` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Learner-initiated calibration sessions (spec_probe_eig_redesign.md §5.9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/calibration_sessions.py](../../../../../../src/learnloop/diagnosis/calibration_sessions.py) |
| Source lines | 374 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CalibrationSessionError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 25)
- `graph_propagated_prior(vault: LoadedVault, repository: Repository, learning_object_id: str) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 29) — Prerequisite-only, direction-respecting graph mastery prior (§8.3).
- `episode_priority_disagreement(vault: LoadedVault, repository: Repository, learning_object_id: str) -> float` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 81) — §5.9/§6.4 planner priority signal: disagreement among the graph-propagated prior, the learner's covering claim, and observed evidence — the spread of whichever of the three signals exist, in [0, 1].
- `routine_planner_shadow(vault: LoadedVault, repository: Repository, episode_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 107) — §5.9 routine-session diagnostic planner, run in SHADOW mode (§13.3).
- `start_calibration_session(vault: LoadedVault, repository: Repository, *, session_id: str, goal_id: str | None=None, learning_object_ids: list[str] | None=None, time_budget_minutes: int | None=None, generate_missing: bool=True, clock: Clock | None=None, ai_client: object | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 156) — Open a calibration session over a goal scope or an explicit LO list.
- `calibration_session_progress(vault: LoadedVault, repository: Repository, calibration_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 257) — Progress payload for the calibration UI: per-episode status, blocks completed, elapsed versus budget, and the next target item.
- `stop_calibration_session(repository: Repository, calibration_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 332)
- `calibration_cap_lifted(repository: Repository, session_id: str | None, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 338) — Whether the per-session qualifying-observation cap is lifted for this client session (§5.9) — true only inside an active, in-budget calibration session.

## Internal implementation anchors

- `_elapsed_minutes(record: ProbeCalibrationSessionRecord, *, clock: Clock | None) -> float` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 354)
- `_expire_if_over_budget(repository: Repository, record: ProbeCalibrationSessionRecord, *, clock: Clock | None) -> ProbeCalibrationSessionRecord` ([source](../../../../../../src/learnloop/diagnosis/calibration_sessions.py), line 362)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; statically calls `calibration_cap_lifted`, `routine_planner_shadow`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `CalibrationSessionError`, `calibration_session_progress`, `start_calibration_session`, `stop_calibration_session`; statically calls `calibration_session_progress`, `start_calibration_session`, `stop_calibration_session`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; statically calls `calibration_cap_lifted`, `routine_planner_shadow`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeCalibrationSessionRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`, `enter_episode`, `episode_posterior`; calls `eligible_instruments`, `enter_episode`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `generate_instances_for_episode`; calls `generate_instances_for_episode`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`, `display_mastery`; calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
  - `test_anti_double_count_direct_evidence_not_refed_via_graph_prior`
- [tests/test_calibration_sessions.py](../../../../../../tests/test_calibration_sessions.py) — direct import
  - `test_calibration_session_plans_episodes_and_reports_progress`
  - `test_calibration_session_requires_scope`
  - `test_calibration_session_stop_and_budget_expiry`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
  - `test_calibration_ordering_reverts_to_plain_rate`
  - `test_non_prerequisite_edges_produce_zero_belief_change`
  - `test_prerequisite_prior_respects_direction`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_disagreement_between_claim_and_observed_evidence`
  - `test_graph_prior_absent_without_evidence_bearing_neighbors`
  - `test_routine_planner_shadow_ranks_open_episodes`

## Modification guidance

- Change calibration sessions policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/calibration_sessions.py](../../../../../../src/learnloop/diagnosis/calibration_sessions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
