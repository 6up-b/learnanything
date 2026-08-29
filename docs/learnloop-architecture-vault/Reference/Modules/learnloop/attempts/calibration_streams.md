---
title: "learnloop.attempts.calibration_streams"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/calibration_streams.py"
source_paths:
  - "src/learnloop/attempts/calibration_streams.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.calibration_streams module"
  - "src/learnloop/attempts/calibration_streams.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.calibration_streams`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.calibration_streams` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The three calibration streams + retrospective bootstrap (§4.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py) |
| Source lines | 215 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `stratum_for(*, confidence_bucket: str, influence_flag: bool, partial_boundary: bool, domain: str | None, length_bucket: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 46)
- `inclusion_probability_for(stratum: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 63) — The stratified inclusion probability (§4.7).
- `should_sample(stratum: Mapping[str, Any], *, key: str, frame_id: str) -> tuple[bool, float]` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 77) — Deterministic stratified draw keyed on (frame_id, key) so the frame is reproducible (§4.7 'the sampling frame and probabilities are logged').
- `class BootstrapFrame` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 89)
  - `as_dict(self) -> dict[str, Any]` (line 96; public)
- `build_bootstrap_frame(repository: Repository, *, frame_id: str | None=None, clock: Clock | None=None) -> BootstrapFrame` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 106) — Draw a stratified sample over existing attempt history (§4.7 bootstrap).
- `record_error_intake_sample(repository: Repository, *, observation_id: str | None, administration_id: str | None, raw_grade_event_id: str | None, stratum: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 166) — Tap a misgraded/ambiguous affect signal into the error-intake stream (§4.7).
- `record_adjudicated_anchor_sample(repository: Repository, *, observation_id: str | None, administration_id: str | None, raw_grade_event_id: str | None, stratum: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 192) — Log an adjudicated anchor (§4.7): authority-grade single datapoint, inclusion_probability = 1.0.

### Module constants

- `CALIBRATION_BASE_INCLUSION_PROBABILITY` ([src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py), line 26)
- `OVERSAMPLE_LOW_CONFIDENCE` ([src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py), line 27)
- `OVERSAMPLE_HIGH_INFLUENCE` ([src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py), line 28)
- `OVERSAMPLE_PARTIAL_BOUNDARY` ([src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py), line 29)
- `ERROR_INTAKE_NOMINAL_INCLUSION` ([src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py), line 34)

## Internal implementation anchors

- `_partial_credit_boundary(correctness: float | None) -> bool` ([source](../../../../../../src/learnloop/attempts/calibration_streams.py), line 37) — A partial-credit-boundary attempt for stratification (§4.7, §10 param 8): an outcome strictly between full and zero credit.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `build_bootstrap_frame`; statically calls `build_bootstrap_frame`
- [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]] — imports `module`; statically calls `record_adjudicated_anchor_sample`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_classifier|learnloop.attempts.grade_classifier]] — imports `bucket_confidence`, `length_bucket_for_text`; calls `bucket_confidence`, `length_bucket_for_text`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]], [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_bootstrap_frame_logs_inclusion_probabilities_and_is_deterministic`
  - `test_confusion_updates_only_from_denominator_bearing_sources`

## Modification guidance

- Change calibration streams policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/calibration_streams.py](../../../../../../src/learnloop/attempts/calibration_streams.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
