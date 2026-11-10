---
title: "learnloop.diagnosis.chain_records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/chain_records.py"
source_paths:
  - "src/learnloop/diagnosis/chain_records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.chain_records module"
  - "src/learnloop/diagnosis/chain_records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.chain_records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.chain_records` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: The attempt chain's decision records after the grade (refactor B7, ADR-017).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py) |
| Source lines | 296 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `diagnosis_record(*, diagnosis_id: str, job_id: str | None, values: Mapping[str, Any]) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 93) — One persisted diagnosis (pure).
- `record_diagnosis(repository: Any, *, diagnosis_id: str, job_id: str | None, values: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 139)
- `step_failed_record(*, step: str, exc: BaseException, attempt_id: str | None=None, subject: tuple[str, str] | None=None, facts: Mapping[str, Any] | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 145) — A diagnosis step that failed and was skipped (pure): the step as ``rule``, the exception's class and where it was raised; the message stays in the log (at the caller's WARNING, with the trace).
- `record_step_failed(repository: Any, *, step: str, exc: BaseException, attempt_id: str | None=None, subject: tuple[str, str] | None=None, facts: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 163)
- `followup_value_record(*, receipt_id: str, attempt_id: str, learning_object_id: str | None, session_id: str | None, outcome: str, decision: Mapping[str, Any] | None, manual_override: bool, need_id: str | None, algorithm_version: str | None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 195) — One follow-up value decision (pure), beside its receipt row.
- `record_followup_value(repository: Any, **values: Any) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 218)
- `forecast_failed_record(*, site: str, exc: BaseException, decision_ref: str | None=None, receipt_key: str | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 222) — A value-of-information forecast that could not be logged (pure): the decision it describes stands.
- `record_forecast_failed(repository: Any, *, site: str, exc: BaseException, decision_ref: str | None=None, receipt_key: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 235)
- `probe_value_record(*, practice_item_id: str, episode_id: str | None, reason: str, decision: Mapping[str, Any] | None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 241) — An opened item rejected as its episode's next observation (pure): its value did not pay for its minutes, so it is ordinary practice.
- `record_probe_value(repository: Any, *, practice_item_id: str, episode_id: str | None, reason: str, decision: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 261)
- `probe_offer_record(*, offer: Any, decision_receipt_id: str | None, router_decision_id: str | None, followup_workflow_id: str | None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 270) — One acceptance of a causal probe offer (pure): accepted (pinned, or already pinned) or refused with its code.
- `record_probe_offer(repository: Any, *, offer: Any, decision_receipt_id: str | None, router_decision_id: str | None, followup_workflow_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 292)

### Module constants

- `LOG` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 36)
- `DIAGNOSIS` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 38)
- `DIAGNOSIS_STEP` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 39)
- `FOLLOWUP_VALUE` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 40)
- `VOI_FORECAST` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 41)
- `PROBE_VALUE` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 42)
- `PROBE_OFFER` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 43)
- `ALTERNATIVES_KEPT` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 46)
- `_DIAGNOSIS_STATUS` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 49)
- `_SKIP_STATUS` ([src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py), line 51)

## Internal implementation anchors

- `_code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 54)
- `_number(value: Any) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 61)
- `_get(value: Any, key: str, default: Any=None) -> Any` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 67)
- `_ids(values: Iterable[Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 73)
- `_write(repository: Any, kind: str, build: Any) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 78) — Build and write one record through the repository's connection (joining its transaction); never raises.
- `_candidate_alternatives(body: Mapping[str, Any] | None, chosen: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 172)
- `_value_facts(body: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/chain_records.py), line 183)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `record_probe_offer`, `record_step_failed`; statically calls `record_probe_offer`, `record_step_failed`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `module`; statically calls `record_followup_value`, `record_step_failed`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `module`; statically calls `record_diagnosis`, `record_step_failed`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `module`; statically calls `record_forecast_failed`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `record_probe_value`; statically calls `record_probe_value`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; calls `write_decision`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `current_cause`, `current_trace`, `is_code`, `where`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_chain_records.py](../../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_failed_forecast_and_a_failed_post_diagnosis_step_leave_records`
  - `test_a_rejected_probe_value_and_a_learner_lane_offer_are_recorded`
  - `test_forecast_failure_is_recorded_when_the_forecast_runs`
  - `test_the_grades_trace_carries_through_the_diagnosis_to_the_follow_up`
  - `test_the_sidecar_records_a_rejected_probe_value`
- [tests/test_provenance.py](../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`

## Modification guidance

- Change chain records policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/chain_records.py](../../../../../../src/learnloop/diagnosis/chain_records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
