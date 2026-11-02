---
title: "learnloop.diagnosis.forecast_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/forecast_receipts.py"
source_paths:
  - "src/learnloop/diagnosis/forecast_receipts.py"
source_commit: "880aef2b33171c22d39b9dc1508490dde868a991"
source_commit_timestamp: "2026-10-15T18:13:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.diagnosis.forecast_receipts module"
  - "src/learnloop/diagnosis/forecast_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.forecast_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.forecast_receipts` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Saved diagnosis forecasts: what a diagnosis and a repair expect, frozen.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py) |
| Source lines | 610 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `880aef2b33171c22d39b9dc1508490dde868a991` |
| Commit timestamp | `2026-10-15T18:13:29-04:00` |

## Public API

- `next_observation_likelihood(vault: Any, *, facet_id: str, error_type: str) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 123) — The facet response model's prediction under each cause, item-agnostic.
- `diagnosis_receipts(vault: Any, *, diagnosis_id: str, attempt: Mapping[str, Any], values: Mapping[str, Any], record: Mapping[str, Any] | None, seen_attempt_ids: Sequence[str]=(), inputs_as_of: str | None=None) -> list[FR.ForecastReceipt]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 196) — The receipts one completed diagnosis states (pure; no database).
- `record_diagnosis_forecasts(vault: Any, repository: Repository, *, diagnosis_id: str, attempt: Mapping[str, Any], values: Mapping[str, Any], record: Mapping[str, Any] | None, inputs_as_of: str | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 338) — Write a persisted diagnosis's receipts in ITS transaction.
- `effective_cold_outcome(connection: Any, cold_attempt_id: str, *, threshold: float) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 419) — A measured cold verification's outcome as the cold attempt's grade stands NOW: ``(cold_success | cold_failure, "realized")``, or ``(None, why not)``: the grade is held for review (THE held predicate), assesses nothing, or there is no correctness.
- `repair_receipt(connection: Any, *, attempt: Mapping[str, Any], repair_class_id: str | None, hypothesis_ids: Sequence[str], episode: Mapping[str, Any] | None, task: Mapping[str, Any] | None, censor_reason: str | None, success_threshold: float) -> FR.ForecastReceipt` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 475) — The repair class's predicted cold outcome (reads the measured ledger).
- `record_repair_expectation(vault: Any, repository: Repository, *, attempt: Mapping[str, Any], repair_class_id: str | None, hypothesis_ids: Sequence[str]=(), episode: Mapping[str, Any] | None=None, task: Mapping[str, Any] | None=None, censor_reason: str | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 557) — Write a repair's predicted cold outcome in the primed attempt's transaction.

### Module constants

- `DIAGNOSER_FORECASTER` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 64)
- `DIAGNOSER_FORECASTER_VERSION` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 66)
- `NEXT_OBSERVATION_RULE` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 80)
- `NEXT_OBSERVATION_ALPHABET` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 81)
- `QUALIFYING_ATTEMPT_TYPES` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 84)
- `NON_LEARNER_VALIDITY` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 87)
- `LEARNER_STATE` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 89)
- `TRANSIENT` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 90)
- `CLASSED` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 91)
- `DEFAULT_CLASS_CONFIDENCE` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 93)
- `FORECAST_FLOOR` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 96)
- `MAX_RECEIPTS_PER_DIAGNOSIS` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 98)
- `REPAIR_FORECASTER` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 376)
- `REPAIR_FORECASTER_VERSION` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 383)
- `REPAIR_ALPHABET` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 384)
- `REPAIR_PSEUDO_COUNT` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 385)
- `REPAIR_OUTCOME_RULE` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 389)
- `MEASURED_COLD_DISPOSITIONS` ([src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 391)

### Explicit exports

`__all__` declares:

- `DIAGNOSER_FORECASTER`
- `DIAGNOSER_FORECASTER_VERSION`
- `MEASURED_COLD_DISPOSITIONS`
- `NEXT_OBSERVATION_ALPHABET`
- `NEXT_OBSERVATION_RULE`
- `QUALIFYING_ATTEMPT_TYPES`
- `REPAIR_ALPHABET`
- `REPAIR_FORECASTER`
- `REPAIR_FORECASTER_VERSION`
- `REPAIR_OUTCOME_RULE`
- `diagnosis_receipts`
- `effective_cold_outcome`
- `next_observation_likelihood`
- `record_diagnosis_forecasts`
- `record_repair_expectation`
- `repair_receipt`

## Internal implementation anchors

- `_class_posterior(causal_class: str, confidence: float | None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 101)
- `_coarse(distribution: Mapping[tuple[str, str | None], float], error_type: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 107) — (bucket, error) -> pass / same_error / other_error, floored.
- `_diagnoser_parameters(vault: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 137)
- `_attributions(record: Mapping[str, Any] | None) -> dict[int, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 152)
- `_canonical_facets(vault: Any, facets: Sequence[Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 165)
- `_candidate_causes(event: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 174) — The diagnoser's candidate causes with their verbalized weights normalized (a cause without a weight takes the mean of the others): recorded, not used.
- `_seen_attempts(connection: Any, attempt: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 328) — The attempts created at or after ``attempt`` (not it) visible now.
- `_has_table(connection: Any, table: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 394)
- `_assessed(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 400) — Does the attempt's current grade assess anything?
- `_measured_cold_outcomes(connection: Any, repair_class_id: str | None, *, threshold: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/forecast_receipts.py), line 442) — The measured cold outcomes as their grades stand now (Codex review F3): every measured disposition's cold attempt read through :func:`effective_cold_outcome`; the ones that no longer measure anything are counted by reason, never in the sample.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `record_repair_expectation`; statically calls `record_repair_expectation`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `record_diagnosis_forecasts`; statically calls `record_diagnosis_forecasts`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `MEASURED_COLD_DISPOSITIONS`, `NON_LEARNER_VALIDITY`, `effective_cold_outcome`; statically calls `effective_cold_outcome`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `resolve_causal_probe_parameters`; calls `resolve_causal_probe_parameters`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `facet_conditional_distribution`; calls `facet_conditional_distribution`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`, `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `module`; calls `ForecastReceipt`, `categorical_body`, `receipts_enabled`, `record_receipts`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; calls `parameter`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task`
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
  - `test_the_forecast_reads_the_diagnosis_class_and_confidence_once_per_facet_and_pattern`

## Modification guidance

- Change forecast receipts policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/forecast_receipts.py](../../../../../../src/learnloop/diagnosis/forecast_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
