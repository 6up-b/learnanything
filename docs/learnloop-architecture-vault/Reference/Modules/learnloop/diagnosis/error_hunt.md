---
title: "learnloop.diagnosis.error_hunt"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/error_hunt.py"
source_paths:
  - "src/learnloop/diagnosis/error_hunt.py"
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
  - "learnloop.diagnosis.error_hunt module"
  - "src/learnloop/diagnosis/error_hunt.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.error_hunt`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.error_hunt` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: A3 — error-hunt items (spec_measurement_efficiency_v1 §3.A3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py) |
| Source lines | 699 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PlantOutcome(StrEnum)` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 85) — What became of one planted error on one attempt.
- `class PlantResult` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 106) — One plant's outcome, with the report that decided it.
  - `as_dict(self) -> dict[str, Any]` (line 116; public)
- `class FalsePositiveReport` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 127) — An error the learner reported that corresponds to no plant.
  - `as_dict(self) -> dict[str, Any]` (line 139; public)
- `class ValidatedErrorHunt` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 149) — One attempt's A3 outcome, as the grading validator resolved it.
  - `planted_total(self) -> int` (line 164; public)
  - `count(self, outcome: PlantOutcome) -> int` (line 167; public)
  - `reported_error_on_clean_solution(self) -> bool` (line 171; public) — The §10 case: correct work, and the learner says something is wrong.
  - `as_dict(self) -> dict[str, Any]` (line 176; public)
- `validate_error_hunt_report(item: PracticeItem, proposal: Any) -> ValidatedErrorHunt | None` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 263) — Resolve the grader's A3 report against the item's plants.
- `suppress_facet_failures_on_clean_solution(hunt: ValidatedErrorHunt | None, error_attributions: list[Any], repair_suggestions: list[dict[str, Any]]) -> tuple[list[Any], list[dict[str, Any]], ValidatedErrorHunt | None]` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 339) — Strip facet targets from a clean-solution error hunt's attributions.
- `record_error_hunt_outcome(repository: Repository, hunt: ValidatedErrorHunt, *, attempt_id: str, learning_object_id: str, grading_prompt_version: str | None=None, vault: Any=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 432) — Persist the outcome and, on the §10 path, mint the misconception candidate.
- `proofreading_signal(vault: LoadedVault, repository: Repository, *, since: str | None=None) -> Metric` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 552) — ``error_hunt_constructed_response_agreement``: A3's revert producer.
- `error_hunt_outcome_summary(repository: Repository, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 667) — Descriptive counts over recorded A3 outcomes, including the clean rotation.

### Module constants

- `ERROR_HUNT_VERSION` ([src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 82)
- `CLEAN_SOLUTION_FALSE_POSITIVE` ([src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 336)
- `PROOFREADING_SIGNAL_METRIC` ([src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 540)
- `MIN_PAIRED_FACETS` ([src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 544)
- `AGREEMENT_FLOOR` ([src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 549)

## Internal implementation anchors

- `_mentions(haystack: str, needle: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 197) — Normalized containment under the shared answer normalizer.
- `_match_plant(report: Any, plants: Sequence[PlantedError], claimed: set[str]) -> PlantedError | None` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 211) — Which plant, if any, this report is about.
- `_plant_outcome(report: Any, plant: PlantedError) -> PlantOutcome` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 249) — Repaired, or merely found.
- `_candidate_statement(report: FalsePositiveReport) -> str` ([source](../../../../../../src/learnloop/diagnosis/error_hunt.py), line 519) — The belief, phrased as a belief, from a false-positive report.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`; statically calls `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `suppress_facet_failures_on_clean_solution`, `validate_error_hunt_report`; statically calls `suppress_facet_failures_on_clean_solution`, `validate_error_hunt_report`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `error_hunt_outcome_summary`, `proofreading_signal`; statically calls `error_hunt_outcome_summary`, `proofreading_signal`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `error_hunt_outcome_summary`, `proofreading_signal`; statically calls `error_hunt_outcome_summary`, `proofreading_signal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`; calls `normalize_answer`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `promote_candidate_if_independent`; calls `promote_candidate_if_independent`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `Metric`; calls `Metric`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PlantedError`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_a_wrong_repair_is_not_credited_as_a_repair`
  - `test_an_item_that_is_not_an_error_hunt_produces_no_outcome`
  - `test_outcome_summary_reports_the_clean_rotation_share`
  - `test_proofreading_signal_abstains_without_both_populations`
  - `test_the_repair_is_required_not_the_flag`

## Modification guidance

- Change error hunt policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/error_hunt.py](../../../../../../src/learnloop/diagnosis/error_hunt.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
