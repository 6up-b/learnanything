---
title: "learnloop.diagnosis.probe_audit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_audit.py"
source_paths:
  - "src/learnloop/diagnosis/probe_audit.py"
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
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_audit module"
  - "src/learnloop/diagnosis/probe_audit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_audit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_audit` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Probe pilot audit and retirement telemetry (spec_probe_eig_redesign.md §13).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_audit.py](../../../../../../src/learnloop/diagnosis/probe_audit.py) |
| Source lines | 722 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `eig_calibration_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 63) — Expected vs realized information per family version.
- `time_calibration_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 127) — Expected instrument seconds vs observed served→submitted seconds.
- `cross_surface_replication_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 171) — Whether early diagnoses replicate on later observations from a different surface family within the same episode.
- `downstream_outcome_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 224) — Post-episode success proxy: attempt success on the LO before vs after completion.
- `replay_determinism_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 274) — Pilot integrity check: replay is deterministic and stored observation rows are internally consistent (entropies match their posterior JSON, the realized gain matches the entropy delta).
- `record_probe_regrade_check(repository: Repository, *, attempt_id: str, regrade_rubric_score: int | None, max_points: int=4, regrade_error_types: list[str] | None=None, attempt_type: str='diagnostic_probe', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 396) — Classify a regraded response through the observation's own persisted card snapshot and record the (original, regrade) outcome pair.
- `run_probe_regrade_checks(vault: LoadedVault, repository: Repository, client: Any, *, limit: int=10, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 445) — Re-grade a sample of probe observations and record agreement (§7.6).
- `grading_confusion_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 523) — Regrade agreement and the (original, regrade) confusion matrix per family version and grader version (§7.6).
- `calibration_evidence_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 556) — Family calibration rows grouped by evidence source.
- `shadow_policy_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 586) — Compare the executed selection against logged shadow rankings.
- `planner_shadow_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 632) — §5.9 routine-planner shadow comparison (§13.3, log-only).
- `shadow_intent_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 669) — §11.2 intent-first session-composition shadow comparison (log-only).
- `pilot_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 702) — The full fixture-vault pilot audit (Checkpoint 4).

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 31)
- `_round(value: float | None, digits: int=4) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 35)
- `_mean(values: list[float]) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 39)
- `_observation_rows(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 43) — Every presentation-backed observation with its episode context.
- `_family_key(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_audit.py), line 54)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `grading_confusion_report`, `pilot_report`, `run_probe_regrade_checks`; statically calls `grading_confusion_report`, `pilot_report`, `run_probe_regrade_checks`
- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `pilot_report`; statically calls `pilot_report`
- [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]] — imports `eig_calibration_report`, `grading_confusion_report`; statically calls `eig_calibration_report`, `grading_confusion_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`; calls `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`, `classify_outcome`; calls `classify_outcome`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]], [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_probe_regrade.py](../../../../../../tests/test_characterization_probe_regrade.py) — direct import
  - `test_regrade_records_original_vs_regrade_grader_outputs`
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
  - `test_intent_planner_is_shadow_only`
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
  - `test_eig_report_matches_stored_observations`
  - `test_evidence_sources_stay_separate`
  - `test_pilot_report_bundles_all_sections`
  - `test_regrade_checks_record_agreement_and_confusion`
  - `test_replay_audit_detects_a_self_consistent_but_wrong_posterior_transition`
  - `test_replay_determinism_holds_on_pilot_vault`
  - `test_run_probe_regrade_checks_samples_and_skips_checked`
  - `test_shadow_rankings_are_logged_and_reported`
  - `test_time_calibration_uses_served_to_submitted`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_planner_shadow_report_summarizes_logged_components`

## Modification guidance

- Change probe audit policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_audit.py](../../../../../../src/learnloop/diagnosis/probe_audit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
