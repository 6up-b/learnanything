---
title: "learnloop.db.evidence_cutoff"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/evidence_cutoff.py"
source_paths:
  - "src/learnloop/db/evidence_cutoff.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.evidence_cutoff module"
  - "src/learnloop/db/evidence_cutoff.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.evidence_cutoff`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.evidence_cutoff` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Evidence cutoffs: which evidence a read admits, as of when, and which corrections it applies.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py) |
| Source lines | 637 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class Boundary` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 115) — One test a read applies: ``<subject>.<time> <op> <anchor time>`` under ``comparison``.
  - `to_dict(self) -> dict[str, str]` (line 130; public)
  - `from_dict(cls, raw: Mapping[str, Any]) -> 'Boundary'` (line 135; public)
  - `inclusive(self) -> bool` (line 145; public)
- `class FieldApproximation` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 150) — A field a read showed although it could not reconstruct its value at the cutoff.
  - `to_dict(self) -> dict[str, str]` (line 157; public)
- `class MutableField` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 173) — One column (or derived value) the evidence reads change in place, and whether its past is recoverable.
  - `name(self) -> str` (line 183; public)
- `recoverability(field_name: str) -> MutableField | None` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 255) — The inventory's entry for ``table.column``, or None for a field the evidence reads never overwrite.
- `approximate_fields(field_names: tuple[str, ...] | list[str]) -> tuple[FieldApproximation, ...]` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 261) — The fields of ``field_names`` a read as of then cannot reconstruct exactly, sorted by name.
- `closure_through_limit(local_date: str) -> tuple[datetime, bool]` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 276) — ``(limit, inclusive)`` for the end of ``local_date`` in the machine's local time: the next local midnight, exclusive; a date with no next day (``9999-12-31``) admits every event, inclusive at the largest instant.
- `closure_at_limit(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 287) — The instant ``stamp`` names (a window's ``window_closes_at``): events at or before it.
- `closure_admits(limit: datetime, inclusive: bool, occurred: Any, received: Any=None) -> bool` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 295) — Whether an event that happened at ``occurred`` (and, for an answer, became known at ``received``, None where the two are one) is in the read: both at or before the closure.
- `history_v1_written_before(written: datetime | None, cutoff: datetime | None) -> bool` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 311) — A record written strictly before the cutoff instant.
- `history_v1_known_by(known: datetime | None, cutoff: datetime | None) -> bool` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 318) — True unless the attempt became known after the cutoff (always True where no known time was read).
- `ad_replay_excludes(at: float, limit: float) -> bool` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 324) — An event at ``at`` days is after the replay's ``limit`` days (``math.inf`` with no ``as_of``).
- `completed_by_excludes(created_at: Any, as_of: Any) -> bool` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 330) — An attempt whose stored ``created_at`` text sorts after ``as_of``: the field's completion cutoff, a text comparison (a ``None`` time raises, an empty one is admitted).
- `class Cutoff` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 357) — Which evidence a read admits, as of when, and which corrections it applies (module docstring).
  - `__post_init__(self) -> None` (line 376; internal)
  - `current(cls) -> 'Cutoff'` (line 391; public) — Everything LearnLoop holds, every correction as it stands now.
  - `corrected_before(cls, attempt_id: str, occurred_at: str) -> 'Cutoff'` (line 397; public) — Events before an attempt in ``(created_at, id)`` text order (two in one second order by id), every correction as it stands now: a regrade reaches the read.
  - `as_known_at(cls, known_at: str, *, attempt_id: str | None=None, fields: tuple[str, ...] | list[str]=()) -> 'Cutoff'` (line 411; public) — Events known by ``known_at`` (an attempt's known time, or a moment), corrections as they stood then.
  - `closure_through(cls, local_date: str) -> 'Cutoff'` (line 427; public) — The end of a local date: events before the next local midnight (the instant is computed in the machine's local time when the cutoff is made and stored, so it does not move with a later time zone).
  - `closure_at(cls, stamp: str) -> 'Cutoff'` (line 435; public) — A stamp itself (a window's closing moment): events at or before it.
  - `_closure(cls, anchor_kind: str, anchor_id: str, limit: datetime, inclusive: bool) -> 'Cutoff'` (line 441; internal)
  - `history_v1(cls, attempt_id: str, completed_at: str, *, known_at: str | None=None, available_at_reads: bool=False) -> 'Cutoff'` (line 451; public) — The diagnoser's history as it is read today (``diagnosis.split.history.VaultHistoryStore``).
  - `ad_replay(cls, as_of: str | None) -> 'Cutoff'` (line 480; public) — Adaptive difficulty's replay (``replay.load_events``): attempts, reading opportunities and claims at or before ``as_of`` in float days of their parsed time (an unreadable time is skipped; no ``as_of`` admits every readable one); grades, holds, claims' supersession and protection…
  - `completed_by(cls, as_of: str | None) -> 'Cutoff'` (line 494; public) — The learner field's attempt rows (``field.outcomes.load_attempt_rows``): ``created_at`` text at or before ``as_of`` text (a ``None`` time raises, an empty one is admitted; no ``as_of`` admits all); the latest surviving grading epoch and the field's revision policy now, not a poi…
  - `time(self, name: str) -> str | None` (line 508; public)
  - `is_approximate(self) -> bool` (line 512; public)
  - `identity_scalar(self) -> str | None` (line 515; public) — The scalar each reader keyed its caches and identities by before this type existed (an ``as_of``, a closure's date or stamp, an attempt id; None for the current read).
  - `admits(self, occurred: Any, received: Any=None, *, attempt_id: str | None=None) -> bool` (line 524; public) — Whether an attempt (or event) that happened at ``occurred``, known at ``received`` (None where the two are one), with id ``attempt_id`` (for a tie), is admitted, by exactly the rule of the preset's reader.
  - `history_known_cutoff(self) -> datetime | None` (line 561; public) — ``history_v1``: when the decision at the target was made, its known time, else its completion.
  - `written_before(self, written: Any) -> bool` (line 567; public) — ``history_v1``: a record written strictly before the target's completion instant.
  - `mark_before(self, created_at: Any) -> bool` (line 574; public) — ``history_v1``: a learner mark whose ``created_at`` text sorts strictly before the target's.
  - `_require(self, preset: str) -> None` (line 580; internal)
  - `to_dict(self) -> dict[str, Any]` (line 586; public)
  - `to_json(self) -> str` (line 601; public) — Canonical JSON: sorted keys, compact separators, UTF-8 text kept as is.
  - `from_dict(cls, raw: Mapping[str, Any]) -> 'Cutoff'` (line 607; public)
  - `from_json(cls, text: str) -> 'Cutoff'` (line 628; public)

### Module constants

- `SCHEMA` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 49)
- `CURRENT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 53)
- `CORRECTED_BEFORE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 54)
- `AS_KNOWN_AT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 55)
- `CLOSURE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 56)
- `HISTORY_V1` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 57)
- `AD_REPLAY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 58)
- `COMPLETED_BY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 59)
- `PRESETS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 60)
- `ADMIT_ALL` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 64)
- `ADMIT_OCCURRED_BEFORE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 65)
- `ADMIT_KNOWN_BY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 66)
- `ADMIT_OCCURRED_AND_RECEIVED_BY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 68)
- `ADMIT_HISTORY_V1` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 70)
- `ADMIT_OCCURRED_BY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 71)
- `ADMISSIONS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 72)
- `CORRECTIONS_NOW` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 75)
- `CORRECTIONS_THEN` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 76)
- `CORRECTIONS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 77)
- `ANCHOR_NONE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 79)
- `ANCHOR_ATTEMPT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 80)
- `ANCHOR_MOMENT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 81)
- `ANCHOR_LOCAL_DATE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 82)
- `ANCHORS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 83)
- `COMPARE_INSTANT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 88)
- `COMPARE_TEXT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 90)
- `COMPARE_TEXT_KEY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 92)
- `COMPARE_DAYS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 94)
- `COMPARISONS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 95)
- `TIME_EXCLUDED` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 98)
- `TIME_ADMITTED` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 99)
- `TIME_RAISES` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 100)
- `TIME_IGNORED` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 101)
- `TIME_RULES` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 102)
- `AVAILABILITY_CREATED` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 105)
- `AVAILABILITY_RECEIVED_OR_CREATED` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 107)
- `AVAILABILITY_BOTH` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 109)
- `AVAILABILITY_NONE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 110)
- `AVAILABILITIES` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 111)
- `RECOVERABLE_EXACT` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 165)
- `RECOVERABLE_BY_TIMESTAMP` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 166)
- `RECOVERABLE_PARTIAL` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 167)
- `RECOVERABLE_NONE` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 168)
- `RECOVERABILITY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 169)
- `MUTABLE_FIELDS` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 195)
- `_INVENTORY` ([src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py), line 252)

### Explicit exports

`__all__` declares:

- `AD_REPLAY`
- `AS_KNOWN_AT`
- `Boundary`
- `CLOSURE`
- `COMPLETED_BY`
- `CORRECTED_BEFORE`
- `CURRENT`
- `Cutoff`
- `FieldApproximation`
- `HISTORY_V1`
- `MUTABLE_FIELDS`
- `MutableField`
- `PRESETS`
- `SCHEMA`
- `ad_replay_excludes`
- `approximate_fields`
- `closure_admits`
- `closure_at_limit`
- `closure_through_limit`
- `completed_by_excludes`
- `history_v1_known_by`
- `history_v1_written_before`
- `recoverability`

## Internal implementation anchors

- `_fields(table: str, columns: str, recoverable: str, how: str, writer: str) -> tuple[MutableField, ...]` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 187)
- `_instant_or_none(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 337)
- `_days(value: Any) -> float` ([source](../../../../../../src/learnloop/db/evidence_cutoff.py), line 346)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/grade_forecast|learnloop.adaptive_difficulty.grade_forecast]] — imports `Cutoff`
- [[Reference/Modules/learnloop/adaptive_difficulty/repeat_receipts|learnloop.adaptive_difficulty.repeat_receipts]] — imports `Cutoff`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `ad_replay_excludes`; statically calls `ad_replay_excludes`
- [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]] — imports `Cutoff`
- [[Reference/Modules/learnloop/attempts/facts|learnloop.attempts.facts]] — imports `CORRECTIONS_THEN`, `Cutoff`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `Cutoff`, `history_v1_known_by`, `history_v1_written_before`; statically calls `history_v1_known_by`, `history_v1_written_before`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `completed_by_excludes`; statically calls `completed_by_excludes`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `Cutoff`, `closure_admits`, `closure_at_limit`, `closure_through_limit`; statically calls `closure_admits`, `closure_at_limit`, `closure_through_limit`
- [[Reference/Modules/learnloop/scheduling/prediction_snapshots|learnloop.scheduling.prediction_snapshots]] — imports `Cutoff`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/grade_forecast|learnloop.adaptive_difficulty.grade_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/repeat_receipts|learnloop.adaptive_difficulty.repeat_receipts]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/adaptive_difficulty/snapshot_parts|learnloop.adaptive_difficulty.snapshot_parts]], [[Reference/Modules/learnloop/attempts/facts|learnloop.attempts.facts]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_attempt_facts.py](../../../../../../tests/test_attempt_facts.py) — direct import
  - `test_a_withheld_item_behind_the_material_view_reads_as_if_it_were_never_stored`
  - `test_as_known_at_a_cutoff_a_later_showing_reads_not_shown_and_the_attachment_partial`
  - `test_the_collector_reads_a_fixed_handful_whatever_the_number_of_attempts`
  - `test_the_cutoff_admits_attempts_by_its_own_rule`
  - `test_without_the_help_table_the_source_is_absent_not_no_help`
- [tests/test_epp_prediction_snapshots.py](../../../../../../tests/test_epp_prediction_snapshots.py) — direct import
  - `test_a_receipt_round_trips_its_cutoff_target_distribution_and_provenance`
  - `test_threshold_and_in_process_receipts_state_their_cutoff_target_and_provenance`
  - `test_writes_are_idempotent_and_roll_back_with_their_transaction`
- [tests/test_evidence_cutoff.py](../../../../../../tests/test_evidence_cutoff.py) — direct import
  - `test_a_cutoff_refuses_an_unknown_schema_or_policy`
  - `test_ad_replay_matrix_equals_the_predecessor`
  - `test_ad_replay_with_an_unreadable_as_of_raises_like_the_predecessor`
  - `test_as_known_at_is_known_by_inclusive_and_fails_closed`
  - `test_as_known_at_reports_unreconstructable_fields_as_approximate`
  - `test_closure_admits_matrix_equals_the_predecessor`
  - `test_closure_at_the_same_instant_is_inclusive`
  - `test_closure_far_future_admits_everything_inclusively`
  - `test_closure_through_is_the_next_local_midnight_across_a_transition`
  - `test_completed_by_matrix_equals_the_field_predecessor`
  - `test_corrected_before_is_the_attempt_order_without_a_known_gate`
  - `test_current_admits_everything`
  - `test_cutoff_round_trips_through_canonical_json`
  - `test_equal_time_inclusion_ad_and_field`
  - `test_history_kernels_equal_the_predecessor`
  - `test_history_v1_attempt_rule_and_equal_second_ties`
  - `test_history_v1_records_are_written_strictly_before_the_completion`
  - `test_identity_scalars_are_the_readers_old_keys`
  - `test_the_inventory_names_real_columns`
  - `test_the_module_imports_nothing_of_learnloop_but_the_clock`
  - `test_the_serialized_form_names_preset_policies_anchor_boundaries_and_approximation`
- [tests/test_evidence_cutoff_census.py](../../../../../../tests/test_evidence_cutoff_census.py) — direct import
  - `test_every_row_is_well_formed_and_its_caller_makes_the_call`
  - `test_the_census_names_every_preset_but_the_unread_ones`
- [tests/test_evidence_cutoff_readers.py](../../../../../../tests/test_evidence_cutoff_readers.py) — direct import
  - `test_a_hint_shown_then_attached_after_the_cutoff_is_partly_reconstructable`
  - `test_a_mutable_status_is_read_now`
  - `test_a_record_written_at_exactly_the_targets_completion_is_not_shown`
  - `test_a_regrade_is_read_now_by_an_earlier_target`
  - `test_ad_replay_and_field_rows_admit_an_attempt_at_exactly_as_of`
  - `test_the_planted_history_store_is_corrected_before`
  - `test_the_sql_form_reads_an_empty_receipt_as_text`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/evidence_cutoff.py](../../../../../../src/learnloop/db/evidence_cutoff.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
