---
title: "learnloop.sim.diagnostic_validation"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/diagnostic_validation.py"
source_paths:
  - "src/learnloop/sim/diagnostic_validation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.diagnostic_validation module"
  - "src/learnloop/sim/diagnostic_validation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.diagnostic_validation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.diagnostic_validation` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Checkpoint-3 sim validation: planted latent hypothesis types end to end.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py) |
| Source lines | 498 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class PlantedResponse` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 96)
- `planted_response(planted: str, instrument: CompiledInstrument, rng: random.Random) -> PlantedResponse` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 120) — Behavioral response of one planted student to one instrument.
- `class EpisodeValidationResult` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 181)
  - `as_dict(self) -> dict[str, Any]` (line 196; public)
- `class ValidationReport` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 215)
  - `by_planted(self) -> dict[str, dict[str, Any]]` (line 218; public)
  - `as_dict(self) -> dict[str, Any]` (line 234; public)
  - `passes(self, *, label_accuracy_threshold: float, action_accuracy_threshold: float) -> bool` (line 246; public) — Checkpoint 4 entry gate: every planted type classified at or above threshold within the budget, with matching instructional actions.
- `run_probe_validation(source_vault: Path, workdir: Path, *, planted_types: tuple[str, ...]=PLANTED_TYPES, seeds: tuple[int, ...]=(11, 12, 13), learning_object_id: str | None=None, claim_level: float=0.7, config_overrides: Mapping[str, Any] | None=None) -> ValidationReport` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 276) — Run the planted-type episode validation against copies of one vault.

### Module constants

- `VALIDATION_START` ([src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 60)
- `PLANTED_TYPES` ([src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 62)
- `_CORRECT_OUTCOMES` ([src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 70)
- `_WEAK_OUTCOMES` ([src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 82)

## Internal implementation anchors

- `_effective_slot(planted: str, instrument: CompiledInstrument) -> str` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 102)
- `_expected_label(planted: str, diagnosed: str | None) -> bool` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 258)
- `_action_for_label(label: str | None) -> str | None` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 266)
- `_run_one_episode(vault_root: Path, *, planted: str, seed: int, learning_object_id: str | None, claim_level: float, config_overrides: Mapping[str, Any] | None) -> EpisodeValidationResult | None` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 313)
- `_submit_response(vault, repository: Repository, practice_item_id: str, presentation_id: str, response: PlantedResponse, *, clock: FrozenClock) -> None` ([source](../../../../../../src/learnloop/sim/diagnostic_validation.py), line 437)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `PLANTED_TYPES`, `run_probe_validation`; statically calls `run_probe_validation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `FrozenClock`; calls `FrozenClock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `RoutineDisplayCovered`, `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`; calls `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`, `DEFAULT_INSTRUCTIONAL_ACTIONS`, `builtin_family_templates`; calls `builtin_family_templates`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `CONFUSES_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `generate_instances_for_episode`; calls `generate_instances_for_episode`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `apply_config_overrides`, `prepare_run_vault`; calls `apply_config_overrides`, `prepare_run_vault`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `pathlib`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sim_probe_validation.py](../../../../../../tests/test_sim_probe_validation.py) — direct import
  - `test_planted_confuses_with_is_diagnosed_within_budget`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run`

## Modification guidance

- Make changes here when the responsibility remains diagnostic validation within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/diagnostic_validation.py](../../../../../../src/learnloop/sim/diagnostic_validation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
