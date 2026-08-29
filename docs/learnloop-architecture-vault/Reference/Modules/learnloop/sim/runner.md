---
title: "learnloop.sim.runner"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/runner.py"
source_paths:
  - "src/learnloop/sim/runner.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.runner module"
  - "src/learnloop/sim/runner.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.runner`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.runner` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Simulation runner: drive a synthetic student through the real pipeline.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py) |
| Source lines | 1052 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class SimulationError(ValueError)` ([source](../../../../../../src/learnloop/sim/runner.py), line 84)
- `class SimAttemptRecord` ([source](../../../../../../src/learnloop/sim/runner.py), line 89)
  - `as_dict(self) -> dict[str, Any]` (line 109; public)
- `class SimDayRecord` ([source](../../../../../../src/learnloop/sim/runner.py), line 133)
  - `as_dict(self) -> dict[str, Any]` (line 142; public)
- `class SimReport` ([source](../../../../../../src/learnloop/sim/runner.py), line 153)
  - `as_dict(self) -> dict[str, Any]` (line 165; public)
  - `deterministic_dict(self) -> dict[str, Any]` (line 180; public) — Report content that must be identical for identical (seed, args).
- `coerce_override_value(raw: str) -> Any` ([source](../../../../../../src/learnloop/sim/runner.py), line 191)
- `apply_config_overrides(config: LearnLoopConfig, overrides: Mapping[str, Any] | None) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/sim/runner.py), line 207) — Return a new config with dotted-path overrides merged in-memory.
- `prepare_run_vault(source: Path, dest: Path, *, reset_state: bool=True) -> Path` ([source](../../../../../../src/learnloop/sim/runner.py), line 240) — Copy a vault into a run directory; by default drop derived SQLite state.
- `run_simulation(vault_root: Path, profile: StudentProfile, *, days: int=60, items_per_day: int=6, seed: int=42, config_overrides: Mapping[str, Any] | None=None, start: datetime | None=None, primed_retries: bool=False, goal_due_day: int | None=None, grader_confusion: 'Any | None'=None) -> SimReport` ([source](../../../../../../src/learnloop/sim/runner.py), line 266) — Run one synthetic student against the vault at ``vault_root``.

### Module constants

- `SIM_START` ([src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py), line 69)
- `_ATTEMPT_SPACING_SECONDS` ([src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py), line 70)
- `_PRIMED_RETRY_DELAY_SECONDS` ([src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py), line 72)
- `_PREFERRED_ATTEMPT_TYPES` ([src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py), line 75)
- `_ULID_RE` ([src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py), line 906)

## Internal implementation anchors

- `_goal_snapshot_days(vault: LoadedVault, *, start: datetime, days: int) -> dict[str, int]` ([source](../../../../../../src/learnloop/sim/runner.py), line 460) — Sim day (end of day) at which each active goal's attainment is measured.
- `_track_goals_end_of_day(vault: LoadedVault, repository: Repository, student: SyntheticStudent, *, day: int, day_base: datetime, snapshot_days: dict[str, int], tracking: dict[str, dict[str, Any]]) -> dict[str, int]` ([source](../../../../../../src/learnloop/sim/runner.py), line 480) — Belief-side at-risk counts per goal; truth snapshot on each goal's due day.
- `_simulate_one_attempt(vault: LoadedVault, repository: Repository, student: SyntheticStudent, item: PracticeItem, *, day: int, day_f: float, clock: FrozenClock, session_id: str, source: str, primed: bool=False, grader_confusion: 'Any | None'=None, confusion_rng: 'random.Random | None'=None) -> SimAttemptRecord` ([source](../../../../../../src/learnloop/sim/runner.py), line 539)
- `_primed_retry_sibling(vault: LoadedVault, item: PracticeItem) -> PracticeItem | None` ([source](../../../../../../src/learnloop/sim/runner.py), line 693) — First (deterministic) other non-teach-back item on the same LO.
- `class _SimTeachBackClient` ([source](../../../../../../src/learnloop/sim/runner.py), line 710) — No-op question generator + synthesized grader for simulated teach-backs.
- `_simulate_teach_back_attempt(vault: LoadedVault, repository: Repository, student: SyntheticStudent, item: PracticeItem, *, day: int, day_f: float, clock: FrozenClock, session_id: str, source: str) -> SimAttemptRecord` ([source](../../../../../../src/learnloop/sim/runner.py), line 799) — Run one simulated teach-back conversation as ONE recorded attempt.
- `_strip_ulids(text: str) -> str` ([source](../../../../../../src/learnloop/sim/runner.py), line 909) — Replace random ULIDs in free text so reports are seed-deterministic.
- `_attempt_type_for_item(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/sim/runner.py), line 915)
- `_item_facet_weights(item: PracticeItem) -> dict[str, float]` ([source](../../../../../../src/learnloop/sim/runner.py), line 925)
- `_lo_facet_weights(vault: LoadedVault) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/sim/runner.py), line 931)
- `_los_for_facets(vault: LoadedVault, facets: list[str]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/sim/runner.py), line 940)
- `_resolve_auto_misconceptions(vault: LoadedVault, profile: StudentProfile) -> StudentProfile` ([source](../../../../../../src/learnloop/sim/runner.py), line 950)
- `_retrievability_prior(repository: Repository, item_id: str, clock: FrozenClock) -> float | None` ([source](../../../../../../src/learnloop/sim/runner.py), line 972)
- `_belief_mae(vault: LoadedVault, repository: Repository, student: SyntheticStudent, lo_facet_weights: dict[str, dict[str, float]], *, day_f: float) -> float | None` ([source](../../../../../../src/learnloop/sim/runner.py), line 983)
- `_update_detection_days(vault: LoadedVault, repository: Repository, profile: StudentProfile, planted_facet_los: dict[str, list[str]], detection_days: dict[str, dict[str, Any]], day: int) -> None` ([source](../../../../../../src/learnloop/sim/runner.py), line 1007)
- `_error_event_types(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/sim/runner.py), line 1039)
- `_taxonomy_severity(vault: LoadedVault, error_type: str) -> float` ([source](../../../../../../src/learnloop/sim/runner.py), line 1045)
- `_taxonomy_is_misconception(vault: LoadedVault, error_type: str) -> bool` ([source](../../../../../../src/learnloop/sim/runner.py), line 1050)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `coerce_override_value`, `prepare_run_vault`; statically calls `coerce_override_value`, `prepare_run_vault`
- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `SimulationError`, `run_simulation`; statically calls `run_simulation`
- [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]] — imports `SimReport`, `run_simulation`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `apply_config_overrides`, `prepare_run_vault`; statically calls `apply_config_overrides`, `prepare_run_vault`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `SimAttemptRecord`, `SimDayRecord`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `SimReport`, `SimulationError`, `prepare_run_vault`, `run_simulation`; statically calls `prepare_run_vault`, `run_simulation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `CriterionEvidence`, `GradingContext`, `GradingProposal`; calls `CriterionEvidence`, `GradingContext`, `GradingProposal`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `FrozenClock`, `parse_utc`; calls `FrozenClock`, `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `evaluate_attempt_intervention_followup`; calls `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`, `resolve_goal_scope`; calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `mastery_diagnostic_view`; calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `criterion_facet_weights_for_item`; calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`, `build_due_queue`; calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/sim/grader_confusion|learnloop.sim.grader_confusion]] — imports `apply_confusion`; calls `apply_confusion`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `module`; calls `build_metrics`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `AUTO_FACET`
- [[Reference/Modules/learnloop/sim/student|learnloop.sim.student]] — imports `StudentProfile`, `SyntheticStudent`, `_normalize`; calls `SyntheticStudent`, `_normalize`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TeachBackQuestion`, `TeachBackQuestionContext`; calls `TeachBackQuestion`, `TeachBackQuestionContext`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_ATTEMPT_TYPE`, `TEACH_BACK_PRACTICE_MODE`, `begin_teach_back`, `finish_teach_back`, `next_question`, `record_answer`; calls `begin_teach_back`, `finish_teach_back`, `next_question`, `record_answer`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `pathlib`, `random`, `re`, `shutil`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]], [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]], [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]], [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
  - `test_runner_confusion_is_byte_identical_when_none_vs_omitted`
  - `test_runner_planted_confusion_no_silent_diagnosis_flip_through_robust_path`
- [tests/test_sim_goals.py](../../../../../../tests/test_sim_goals.py) — direct import
  - `test_goal_metrics_deterministic_across_same_seed`
  - `test_goal_metrics_reported_with_due_day`
  - `test_goal_metrics_without_due_day_snapshot_at_run_end`
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_runner_completes_session_with_teach_back_item`
  - `test_teach_back_config_overrides_round_trip`
  - `test_teach_back_runs_are_seed_deterministic`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
  - `test_config_overrides_apply_in_memory_only`
  - `test_planted_misconception_is_identified`
  - `test_same_seed_produces_identical_reports`

## Modification guidance

- Make changes here when the responsibility remains runner within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/runner.py](../../../../../../src/learnloop/sim/runner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
