---
title: "learnloop.params.fitted_params"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/params/fitted_params.py"
source_paths:
  - "src/learnloop/params/fitted_params.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.params"
layer: "domain"
concepts:
  - "Learning System"
  - "Configuration"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.params.fitted_params module"
  - "src/learnloop/params/fitted_params.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-params"
---

# `learnloop.params.fitted_params`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/params/_package|learnloop.params]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.params.fitted_params` exists within [[Reference/Modules/learnloop/params/_package|learnloop.params]] to own the behavior summarized by its module contract: Resolution of fitted parameter sets (architecture_pivot.md Stage 1).

The authoritative system-level explanation remains in [[Learning System]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py) |
| Source lines | 124 |
| Owning package | [[Reference/Modules/learnloop/params/_package|learnloop.params]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GraderChannelPrior` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 48)
- `resolve_grader_channel_prior(repository: Repository) -> GraderChannelPrior` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 53) — Active fitted grader-channel prior knobs, else the pinned defaults.
- `resolve_fsrs_weights(repository: Repository) -> tuple[float, ...]` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 90) — Active fitted FSRS weights, else the pinned FSRS-6 defaults.
- `fitted_fsrs_provenance(repository: Repository) -> str | None` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 106) — Fitted-set id when fitted weights are active and valid, else None.

### Module constants

- `FSRS_WEIGHTS_SCOPE` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 18)
- `FOLLOWUP_GATE_SCOPE` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 19)
- `GRADER_CHANNEL_SCOPE` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 20)
- `CAUSAL_PROBE_POLICY_SCOPE` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 25)
- `CERTIFICATION_COLD_PROBE_SCOPE` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 35)
- `GRADER_CHANNEL_RELIABILITY_FLOOR_DEFAULT` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 43)
- `CERTAINTY_LCB_QUANTILE_DEFAULT` ([src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py), line 44)

## Internal implementation anchors

- `_validated_float(raw: Any, *, low: float, high: float) -> float | None` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 81)
- `_validated_weights(params: dict[str, Any]) -> tuple[float, ...] | None` ([source](../../../../../../src/learnloop/params/fitted_params.py), line 115)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `resolve_fsrs_weights`; statically calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `CERTAINTY_LCB_QUANTILE_DEFAULT`, `resolve_grader_channel_prior`; statically calls `resolve_grader_channel_prior`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `resolve_grader_channel_prior`; statically calls `resolve_grader_channel_prior`
- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `resolve_grader_channel_prior`; statically calls `resolve_grader_channel_prior`
- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `FOLLOWUP_GATE_SCOPE`, `FSRS_WEIGHTS_SCOPE`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `CAUSAL_PROBE_POLICY_SCOPE`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `FOLLOWUP_GATE_SCOPE`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `CERTIFICATION_COLD_PROBE_SCOPE`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_fsrs_weights`; statically calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `resolve_fsrs_weights`; statically calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `resolve_fsrs_weights`; statically calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `resolve_fsrs_weights`; statically calls `resolve_fsrs_weights`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]], [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_fitted_parameters.py](../../../../../../tests/test_fitted_parameters.py) — direct import
  - `test_resolve_fsrs_weights_defaults_when_absent`
  - `test_resolve_fsrs_weights_falls_back_on_malformed_payload`
  - `test_resolve_fsrs_weights_uses_valid_fitted_set`
- [tests/test_grader_channel_prior_knobs.py](../../../../../../tests/test_grader_channel_prior_knobs.py) — direct import
  - `test_resolver_defaults_and_fitted_override`
  - `test_resolver_rejects_malformed_values`
  - `test_retuned_knob_reaches_an_already_seeded_vault`

## Modification guidance

- Make changes here when the responsibility remains fitted params within learnloop.params; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/params/fitted_params.py](../../../../../../src/learnloop/params/fitted_params.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
