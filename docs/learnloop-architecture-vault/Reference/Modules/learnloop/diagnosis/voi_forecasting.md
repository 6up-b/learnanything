---
title: "learnloop.diagnosis.voi_forecasting"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/voi_forecasting.py"
source_paths:
  - "src/learnloop/diagnosis/voi_forecasting.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.diagnosis.voi_forecasting module"
  - "src/learnloop/diagnosis/voi_forecasting.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.voi_forecasting`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.voi_forecasting` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: EVSI calibration Part B: forecasts of the diagnosis-side VOI decisions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/voi_forecasting.py](../../../../../../src/learnloop/diagnosis/voi_forecasting.py) |
| Source lines | 602 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_probe_presentation_forecast(vault: Any, repository: Repository, presentation: Any, *, learning_object_id: str | None=None, candidate_count: int | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 95) — Forecast of one committed probe presentation (site ``probe_selection``).
- `record_robust_selection_forecast(vault: Any, repository: Repository, *, episode: Any, decision: rc.RobustDecision, candidates: Sequence[Any], ensembles: Mapping[str, rc.Ensemble] | None, posterior: Mapping[str, float], observations: int, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 178) — Forecast of the robust stop/abstain gate (site ``probe_robust_selection``).
- `facet_contract_criteria_hash(criteria: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 281) — Identity of an assessment contract's ``criteria`` (with their targets).
- `target_facet_contract(vault: Any, item: Any, rubric: Any, facet: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 294) — How the chosen item's answer measures ``facet``, frozen at selection time.
- `record_followup_forecast(vault: Any, repository: Repository, *, attempt_id: str, learning_object_id: str, selection: Any, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 350) — Forecast of a queued follow-up (site ``followup_selection``).
- `value_decision_is_forecast(body: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 456) — Whether a ``voi_stopping`` receipt is a valued decision (it carries the valuation of the check it is about), so a forecast.
- `record_value_decision_forecast(vault: Any, repository: Repository, body: Mapping[str, Any] | None, *, receipt_key: str, scheduler_exploration: Mapping[str, Any] | None=None, extra: Mapping[str, Any] | None=None, clock: Clock | None=None, **columns: Any) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 482) — One value-of-information stop/continue decision (``SiteDecision.as_dict`` or a per-check receipt) as a ``voi_forecasts`` row.

### Module constants

- `FACET_OUTCOME_CONTRACT_VERSION` ([src/learnloop/diagnosis/voi_forecasting.py](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 278)
- `VALUE_DECISION_SITES` ([src/learnloop/diagnosis/voi_forecasting.py](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 443)
- `_NOT_VALUED_REASONS` ([src/learnloop/diagnosis/voi_forecasting.py](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 453)

### Explicit exports

`__all__` declares:

- `VALUE_DECISION_SITES`
- `record_value_decision_forecast`
- `value_decision_is_forecast`
- `record_followup_forecast`
- `record_probe_presentation_forecast`
- `record_robust_selection_forecast`

## Internal implementation anchors

- `_route_action_of(repository: Repository, labels: Sequence[str]) -> tuple[Callable[[Mapping[str, float]], str | None], str]` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 56)
- `_vocabulary_parameters(instrument: CompiledInstrument) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 78)
- `_coarse_parameters(parameters: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_forecasting.py), line 465) — The decision's own parameter list on ``voi_forecasts``' coarse provenance vocabulary: a provenance outside it (the multi-family study's ``evsi_multisim`` recommendations, set by simulation, never measured on this learner) reads ``heuristic`` and keeps its own as ``fine_provenanc…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `record_followup_forecast`, `record_value_decision_forecast`; statically calls `record_followup_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `record_probe_presentation_forecast`, `record_robust_selection_forecast`, `record_value_decision_forecast`; statically calls `record_probe_presentation_forecast`, `record_robust_selection_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `record_value_decision_forecast`; statically calls `record_value_decision_forecast`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `facet_contract_criteria_hash`; statically calls `facet_contract_criteria_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`, `GRADER_CHANNEL_RELIABILITY`, `ORDINAL_VOCABULARY`, `SELECTION_POLICY_VERSION`, `instrument_conditionals`; calls `instrument_conditionals`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `triage_reason_for_label`; calls `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `facet_conditional_distribution`, `resolve_item_irt`; calls `facet_conditional_distribution`, `resolve_item_irt`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `expected_information_gain`, `robust_quantile`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`; calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `ROLE_WEIGHTS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `candidate_facet_support`; calls `candidate_facet_support`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; calls `forecast_block`, `parameter`, `provenance_of`, `record_forecast`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]], [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_followup_forecast_uses_the_facet_model`
  - `test_robust_gate_forecast_records_the_eig_paths_minutes`

## Modification guidance

- Change voi forecasting policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/voi_forecasting.py](../../../../../../src/learnloop/diagnosis/voi_forecasting.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
