---
title: "learnloop.db.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/records.py"
source_paths:
  - "src/learnloop/db/records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.records module"
  - "src/learnloop/db/records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.records` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Database records and row helpers shared by the repository and its stores.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py) |
| Source lines | 498 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class PracticeItemState` ([source](../../../../../../src/learnloop/db/records.py), line 78)
- `class MasteryState` ([source](../../../../../../src/learnloop/db/records.py), line 91)
- `class ItemParameterState` ([source](../../../../../../src/learnloop/db/records.py), line 102) — Per-item empirical-Bayes difficulty posterior (b in the 2PL link).
- `class ProbeStateRecord` ([source](../../../../../../src/learnloop/db/records.py), line 114)
- `class ProbePresentationRecord` ([source](../../../../../../src/learnloop/db/records.py), line 129) — A durable committed probe assignment (probe redesign spec §5.1).
- `class ProbeObservationRecord` ([source](../../../../../../src/learnloop/db/records.py), line 160) — The grading result + posterior transition for one consumed presentation (§5.1).
- `class FacetUncertaintyState` ([source](../../../../../../src/learnloop/db/records.py), line 414)

### Module constants

- `_UNSET` ([src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py), line 14)
- `_FACET_RECALL_PROJECTION` ([src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py), line 383)
- `_FACET_CAPABILITY_PROJECTION` ([src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py), line 392)
- `_CAPABILITY_RESIDUAL_PROJECTION` ([src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py), line 402)

## Internal implementation anchors

- `_projection_id(prefix: str, *identity: object) -> str` ([source](../../../../../../src/learnloop/db/records.py), line 17) — Content-addressed identity for a row recreated by deterministic replay.
- `_insert_probe_presentation_row(connection: sqlite3.Connection, *, presentation_id: str, now: str, values: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/db/records.py), line 24) — Insert one frozen diagnostic assignment using the caller's transaction.
- `_decode_learning_outcome_label(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 181)
- `_probe_state_record(row: sqlite3.Row) -> ProbeStateRecord` ([source](../../../../../../src/learnloop/db/records.py), line 187)
- `_probe_presentation_record(row: sqlite3.Row) -> ProbePresentationRecord` ([source](../../../../../../src/learnloop/db/records.py), line 203)
- `_probe_observation_record(row: sqlite3.Row) -> ProbeObservationRecord` ([source](../../../../../../src/learnloop/db/records.py), line 235)
- `_decode_observation_template(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 254)
- `_decode_observation_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 261)
- `_decode_hypothesis_set(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 267)
- `_decode_intervention_need(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 274)
- `_decode_attempt(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 283)
- `_decode_followup_task(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 294)
- `_decode_error_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 302)
- `_decode_causal_hypothesis(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 309)
- `_decode_misconception_candidate(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 321)
- `_decode_surprise(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 347)
- `_decode_scheduler_slate(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 359)
- `class _ProjectionTable` ([source](../../../../../../src/learnloop/db/records.py), line 370) — A derived table a projection persists whole.
- `_facet_uncertainty_state(row: sqlite3.Row) -> FacetUncertaintyState` ([source](../../../../../../src/learnloop/db/records.py), line 429)
- `_decode_elicitation_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 449)
- `_decode_decision_features(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 457)
- `_decode_scheduler_explanation(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 465)
- `_decode_scheduler_slate_candidate(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 473)
- `_decode_proposal_batch(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 483)
- `_decode_proposal_item(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../src/learnloop/db/records.py), line 489)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `FacetUncertaintyState`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ItemParameterState`, `MasteryState`, `PracticeItemState`, `ProbePresentationRecord`, `_CAPABILITY_RESIDUAL_PROJECTION`, `_FACET_CAPABILITY_PROJECTION`, `_FACET_RECALL_PROJECTION`, `_decode_attempt`, `_decode_causal_hypothesis`, `_decode_decision_features`, `_decode_elicitation_event`, `_decode_error_event`, `_decode_followup_task`, `_decode_hypothesis_set`, `_decode_intervention_need`, `_decode_learning_outcome_label`, `_decode_misconception_candidate`, `_decode_observation_event`, `_decode_observation_template`, `_decode_proposal_batch`, `_decode_proposal_item`, `_decode_scheduler_explanation`, `_decode_scheduler_slate`, `_decode_scheduler_slate_candidate`, `_decode_surprise`, `_facet_uncertainty_state`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`, `_probe_state_record`; statically calls `_decode_causal_hypothesis`, `_decode_followup_task`, `_decode_misconception_candidate`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_attempt`, `_decode_learning_outcome_label`, `_decode_surprise`, `_projection_id`; statically calls `_decode_attempt`, `_decode_learning_outcome_label`, `_decode_surprise`, `_projection_id`
- [[Reference/Modules/learnloop/db/stores/causal|learnloop.db.stores.causal]] — imports `_decode_causal_hypothesis`; statically calls `_decode_causal_hypothesis`
- [[Reference/Modules/learnloop/db/stores/content|learnloop.db.stores.content]] — imports `_decode_proposal_batch`, `_decode_proposal_item`; statically calls `_decode_proposal_batch`, `_decode_proposal_item`
- [[Reference/Modules/learnloop/db/stores/facet_projection|learnloop.db.stores.facet_projection]] — imports `FacetUncertaintyState`, `_CAPABILITY_RESIDUAL_PROJECTION`, `_FACET_CAPABILITY_PROJECTION`, `_FACET_RECALL_PROJECTION`, `_ProjectionTable`, `_facet_uncertainty_state`, `_projection_id`; statically calls `_facet_uncertainty_state`, `_projection_id`
- [[Reference/Modules/learnloop/db/stores/grading|learnloop.db.stores.grading]] — imports `_UNSET`, `_decode_observation_event`, `_decode_observation_template`; statically calls `_decode_observation_event`, `_decode_observation_template`
- [[Reference/Modules/learnloop/db/stores/learner_model|learnloop.db.stores.learner_model]] — imports `_decode_error_event`, `_decode_intervention_need`, `_decode_misconception_candidate`, `_decode_scheduler_slate`; statically calls `_decode_error_event`, `_decode_intervention_need`, `_decode_misconception_candidate`, `_decode_scheduler_slate`
- [[Reference/Modules/learnloop/db/stores/practice_state|learnloop.db.stores.practice_state]] — imports `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_decision_features`, `_decode_elicitation_event`, `_decode_learning_outcome_label`, `_decode_scheduler_explanation`, `_decode_scheduler_slate`, `_decode_scheduler_slate_candidate`; statically calls `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_decision_features`, `_decode_elicitation_event`, `_decode_learning_outcome_label`, `_decode_scheduler_explanation`, `_decode_scheduler_slate`, `_decode_scheduler_slate_candidate`
- [[Reference/Modules/learnloop/db/stores/probes|learnloop.db.stores.probes]] — imports `ProbeObservationRecord`, `ProbePresentationRecord`, `ProbeStateRecord`, `_decode_hypothesis_set`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`, `_probe_state_record`; statically calls `_decode_hypothesis_set`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`, `_probe_state_record`
- [[Reference/Modules/learnloop/db/stores/questions|learnloop.db.stores.questions]] — imports `_UNSET`
- [[Reference/Modules/learnloop/db/stores/remediation|learnloop.db.stores.remediation]] — imports `_decode_followup_task`; statically calls `_decode_followup_task`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `ProbeStateRecord`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `FacetUncertaintyState`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `FacetUncertaintyState`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `FacetUncertaintyState`; statically calls `FacetUncertaintyState`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]], [[Reference/Modules/learnloop/db/stores/causal|learnloop.db.stores.causal]], [[Reference/Modules/learnloop/db/stores/content|learnloop.db.stores.content]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/assumed_known_helpers.py](../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/certification_cold_probe_helpers.py](../../../../../../tests/certification_cold_probe_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/cold_retry_reschedule_helpers.py](../../../../../../tests/cold_retry_reschedule_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_augmentation_helpers.py](../../../../../../tests/diagnostic_augmentation_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../tests/diagnostic_probe_single_use_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/records.py](../../../../../../src/learnloop/db/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
