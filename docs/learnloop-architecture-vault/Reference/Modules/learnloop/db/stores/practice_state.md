---
title: "learnloop.db.stores.practice_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/practice_state.py"
source_paths:
  - "src/learnloop/db/stores/practice_state.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.practice_state module"
  - "src/learnloop/db/stores/practice_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.practice_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.practice_state` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Practice state, practice sessions and scheduler records.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/practice_state.py](../../../../../../../src/learnloop/db/stores/practice_state.py) |
| Source lines | 1327 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_mastery_seed_inputs(connection: Any, inputs: MasterySeedInputs, *, recorded_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 30) — Record ``inputs`` unless the learning object has a record already; whether it was written.
- `record_legacy_mastery_seeds(connection: Any, seeds_by_learning_object: Mapping[str, MasterySeedInputs], *, recorded_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 45) — Record the upgrade's reconstructed seeds for learning objects that have none, in id order; how many.
- `class PracticeItemQualityState` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 57)
- `class PracticeStateStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 133)
  - `practice_item_state(self, practice_item_id: str) -> PracticeItemState | None` (line 135; public)
  - `practice_item_states(self) -> dict[str, PracticeItemState]` (line 143; public)
  - `initialize_practice_item_state(self, practice_item_id: str, *, content_hash: str | None=None, active: bool=True, clock: Clock | None=None) -> bool` (line 148; public) — Insert a fresh scheduling row only when none exists.
  - `update_practice_item_content_state(self, practice_item_id: str, *, active: bool, content_hash: str | None, clock: Clock | None=None) -> bool` (line 178; public) — Set only ``active`` and ``content_hash`` on an existing row.
  - `upsert_practice_item_state(self, practice_item_id: str, *, difficulty: float | None=None, stability: float | None=None, retrievability: float | None=None, due_at: str | None=None, active: bool=True, content_hash: str | None=None, last_attempt_at: str | None=None, clock: Clock | None=None) -> None` (line 206; public)
  - `inactive_practice_item_ids(self, practice_item_ids: Iterable[str]) -> frozenset[str]` (line 252; public) — The given items whose scheduling row exists and is inactive.
  - `keep_practice_items_inactive(self, practice_item_ids: Iterable[str]) -> int` (line 267; public) — Close the given items' rows again after replay rewrote them active.
  - `set_practice_item_active(self, practice_item_id: str, *, active: bool, clock: Clock | None=None) -> None` (line 287; public) — Flip only the active flag, preserving scheduling state on the row.
  - `mastery_state(self, learning_object_id: str) -> MasteryState | None` (line 308; public)
  - `mastery_states(self) -> dict[str, MasteryState]` (line 316; public)
  - `upsert_mastery_state(self, mastery: MasteryState) -> None` (line 321; public)
  - `mastery_seed_inputs(self, learning_object_id: str) -> MasterySeedInputs | None` (line 353; public) — The claims the learning object's mastery was first seeded from (mvp-0.67), or None.
  - `record_mastery_seed_inputs(self, inputs: MasterySeedInputs, *, recorded_at: str) -> bool` (line 362; public) — Record the seed unless the learning object has one already (the first persistence wins); whether it did.
  - `answer_confidence_presence(self, *, exclude_attempt_ids: Iterable[str]=()) -> dict[str, int]` (line 370; public) — How often an ordinary graded attempt carries a pre-answer confidence tap.
  - `practice_item_quality_state(self, practice_item_id: str) -> PracticeItemQualityState | None` (line 400; public)
  - `practice_item_quality_states(self) -> dict[str, PracticeItemQualityState]` (line 408; public) — All item-quality projections keyed for a scheduler vault sweep.
  - `upsert_practice_item_quality_state(self, state: Mapping[str, Any]) -> None` (line 420; public)
  - `ability_transition_event(self, attempt_id: str) -> dict[str, Any] | None` (line 425; public)
  - `prediction_interval_rows(self) -> list[dict[str, Any]]` (line 433; public) — Per-attempt predicted score distribution joined to the realized outcome (`learnloop eval` coverage input), oldest first per LO.
  - `retention_label_rows(self) -> list[dict[str, Any]]` (line 462; public)
  - `item_attempt_history(self) -> list[dict[str, Any]]` (line 480; public) — Graded attempts ordered for per-item FSRS replay (`learnloop eval`).
  - `candidate_propensity_rows(self) -> list[dict[str, Any]]` (line 494; public)
  - `insert_fitted_parameters(self, *, scope: str, params: Mapping[str, Any], algorithm_version: str, training_rows_count: int, training_data_through: str | None=None, metrics: Mapping[str, Any] | None=None, activate: bool=True, clock: Clock | None=None) -> str` (line 506; public) — Insert a fitted parameter set; when ``activate``, atomically replace the currently active set for the scope (history rows are kept).
  - `active_fitted_parameters(self, scope: str) -> dict[str, Any] | None` (line 554; public)
  - `list_fitted_parameters(self, scope: str | None=None, limit: int=50) -> list[dict[str, Any]]` (line 567; public)
  - `deactivate_fitted_parameters(self, scope: str, *, fitted_id: str | None=None, clock: Clock | None=None) -> int` (line 579; public)
  - `item_parameter_state(self, practice_item_id: str) -> ItemParameterState | None` (line 593; public)
  - `item_parameter_states(self) -> dict[str, ItemParameterState]` (line 601; public)
  - `_upsert_item_parameter_state_record(self, connection: sqlite3.Connection, state: ItemParameterState) -> None` (line 606; internal)
  - `insert_elicitation_event(self, event: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 632; public)
  - `record_decision_features(self, *, decision_id: str, decision_type: str, ability_vector: Mapping[str, Any], item_demand_vector: Mapping[str, Any] | None=None, context: Mapping[str, Any] | None=None, algorithm_version: str, clock: Clock | None=None) -> str` (line 666; public)
  - `decision_features(self, *, decision_id: str, decision_type: str) -> dict[str, Any] | None` (line 712; public)
  - `elicitation_events(self, session_id: str | None=None) -> list[dict[str, Any]]` (line 723; public)
  - `insert_scheduler_explanations(self, explanations: Iterable[dict[str, Any]], *, session_id: str | None, algorithm_version: str, retention_limit: int | None=None, clock: Clock | None=None) -> None` (line 736; public)
  - `latest_scheduler_slate_by_session(self, session_id: str) -> dict[str, Any] | None` (line 788; public)
  - `scheduler_slate_candidates(self, slate_id: str) -> list[dict[str, Any]]` (line 801; public)
  - `latest_scheduler_explanation(self, practice_item_id: str) -> dict[str, Any] | None` (line 813; public)
  - `latest_scheduler_explanations_by_session(self, session_id: str) -> list[dict[str, Any]]` (line 838; public)
  - `create_session(self, *, energy: str | None=None, sleep_quality: float | None=None, available_minutes: int | None=None, notes_md_path: str | None=None, clock: Clock | None=None) -> str` (line 850; public)
  - `fetch_session(self, session_id: str) -> dict[str, Any] | None` (line 875; public)
  - `most_recent_open_session(self) -> dict[str, Any] | None` (line 883; public)
  - `latest_session_minutes(self) -> tuple[int, str] | None` (line 895; public) — ``(minutes, started_at)`` of the latest session begun with minutes, or None.
  - `session_day_streak(self, *, clock: Clock | None=None) -> dict[str, Any]` (line 917; public) — Consecutive-day study streak derived from session start timestamps.
  - `end_session(self, session_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` (line 958; public)
  - `session_learner_answers(self, session_id: str) -> list[str]` (line 976; public) — Every answer body recorded against this session, in submission order.
  - `update_session_checkpoint(self, session_id: str, *, current_practice_item_id: str | None=None, current_answer: str | None=None, focus_block_state: Mapping[str, Any] | None=None, pending_grading_proposal: Mapping[str, Any] | None=None, readiness: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` (line 999; public)
  - `fetch_session_checkpoint(self, session_id: str) -> dict[str, Any] | None` (line 1040; public)
  - `open_session_checkpoints_except(self, session_id: str) -> list[dict[str, Any]]` (line 1054; public) — The checkpoints of every OTHER open session (the ones :meth:`end_open_sessions_except` is about to end), decoded like :meth:`fetch_session_checkpoint`.
  - `clear_session_checkpoint(self, session_id: str) -> bool` (line 1073; public)
  - `clear_practice_checkpoint_for_item(self, session_id: str, practice_item_id: str) -> bool` (line 1082; public) — Clear this session's draft only while it still points at this card.
  - `acknowledge_practice_checkpoint(self, session_id: str, *, practice_item_id: str, submission_id: str) -> str` (line 1098; public) — Atomically clear only the practice checkpoint the client received.
  - `_record_attempt_practice_item_state(self, connection: sqlite3.Connection, state: PracticeItemState) -> None` (line 1142; internal) — A live attempt's write to its item's scheduling row.
  - `_upsert_practice_item_state_record(self, connection: sqlite3.Connection, state: PracticeItemState) -> None` (line 1195; internal)
  - `_upsert_mastery_state_record(self, connection: sqlite3.Connection, mastery: MasteryState) -> None` (line 1230; internal)
  - `_upsert_practice_item_quality_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None` (line 1261; internal)
  - `_upsert_ability_transition_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None` (line 1288; internal)

## Internal implementation anchors

- `_practice_item_state(row: sqlite3.Row) -> PracticeItemState` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 67)
- `_mastery_state(row: sqlite3.Row) -> MasteryState` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 81)
- `_practice_item_quality_state(row: sqlite3.Row) -> PracticeItemQualityState` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 93)
- `_decode_ability_transition_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 105)
- `_decode_fitted_parameters(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 114)
- `_decode_item_parameter_state(row: sqlite3.Row) -> ItemParameterState` ([source](../../../../../../../src/learnloop/db/stores/practice_state.py), line 122)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `PracticeItemQualityState`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `PracticeStateStoreMixin`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `insert_mastery_seed_inputs`; statically calls `insert_mastery_seed_inputs`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `record_legacy_mastery_seeds`; statically calls `record_legacy_mastery_seeds`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `PracticeItemQualityState`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `PracticeItemQualityState`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/mastery_seed_inputs|learnloop.db.mastery_seed_inputs]] — imports `MASTERY_SEED_TABLE`, `MasterySeedInputs`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_decision_features`, `_decode_elicitation_event`, `_decode_learning_outcome_label`, `_decode_scheduler_explanation`, `_decode_scheduler_slate`, `_decode_scheduler_slate_candidate`; calls `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_decision_features`, `_decode_elicitation_event`, `_decode_learning_outcome_label`, `_decode_scheduler_explanation`, `_decode_scheduler_slate`, `_decode_scheduler_slate_candidate`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_factor_deferral_helpers.py](../../../../../../../tests/causal_factor_deferral_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/causal_p2_acceptance_helpers.py](../../../../../../../tests/causal_p2_acceptance_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/certification_cold_probe_helpers.py](../../../../../../../tests/certification_cold_probe_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/cold_retry_reschedule_helpers.py](../../../../../../../tests/cold_retry_reschedule_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_journey_helpers.py](../../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnosis_split_helpers.py](../../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_augmentation_helpers.py](../../../../../../../tests/diagnostic_augmentation_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../../tests/diagnostic_probe_single_use_helpers.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/practice_state.py](../../../../../../../src/learnloop/db/stores/practice_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
