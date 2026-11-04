---
title: "learnloop.db.stores.recurrence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/recurrence.py"
source_paths:
  - "src/learnloop/db/stores/recurrence.py"
source_commit: "c5ae36a289cdc1d3e99b3005be768f6ec07032c2"
source_commit_timestamp: "2026-10-12T14:54:46-04:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.recurrence module"
  - "src/learnloop/db/stores/recurrence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.recurrence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.recurrence` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Slice 2 T1 persistence: recurrence groups (DERIVED) and escalation receipts.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/recurrence.py](../../../../../../../src/learnloop/db/stores/recurrence.py) |
| Source lines | 543 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c5ae36a289cdc1d3e99b3005be768f6ec07032c2` |
| Commit timestamp | `2026-10-12T14:54:46-04:00` |

## Public API

- `replace_recurrence_projection(connection: sqlite3.Connection, *, members: Sequence[Mapping[str, Any]], reviews: Sequence[Mapping[str, Any]], state: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 56) — Replace the whole projection inside the caller's transaction.
- `clear_recurrence_projection(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 104) — Empty the projection (the successor is off); True when rows were removed.
- `recurrence_state(connection: sqlite3.Connection) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 114)
- `recurrence_group_map(connection: sqlite3.Connection) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 127) — normalized statement -> group key, for merged classes only.
- `projection_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 150) — Whether any projection row (active or prepared) exists.
- `activate_prepared_projection(connection: sqlite3.Connection, *, prepared_fingerprint: str, active_fingerprint: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 159) — Flip PREPARED groups to active when their inputs are unchanged since preparation.
- `recurrence_group_rows(connection: sqlite3.Connection, group_key: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 172)
- `recurrence_review_rows(connection: sqlite3.Connection, case_kind: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 185)
- `input_fingerprint_parts(connection: sqlite3.Connection) -> list[Any]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 204) — Cheap counters over every ledger the builder reads (no JSON parsing).
- `hypothesis_episode_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 224) — One row per concrete episode: its FIRST version's identity fields.
- `diagnoses_in_force(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 273) — Each attempt's live diagnosis in force, with its proposal and citations.
- `diagnosis_with_citations(connection: sqlite3.Connection, diagnosis_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 323)
- `not_same_mistake_taps(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 343)
- `same_cause_judgments(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 354)
- `insert_escalation(connection: sqlite3.Connection, *, attempt_id: str, diagnosis_id: str, group_key: str, recurrence_count: int, earlier_attempt_ids: Iterable[str], repair_suggestion_id: str | None, repair_operator: str | None, prior_operators: Iterable[str], different_approach: bool, algorithm_version: str, repair_source: str='diagnosis', repair: Mapping[str, Any] | None=None, generation: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 367) — Append once per (attempt, diagnosis); returns the id, or None if present.
- `escalation_for_diagnosis(connection: sqlite3.Connection, diagnosis_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 426)
- `escalation_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 438)
- `register_guard_cases(connection: sqlite3.Connection, cases: Iterable[Mapping[str, Any]], *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 455) — Register planted cases once (by case id); returns how many were new.
- `guard_case_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 480)
- `class RecurrenceStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 488) — Repository conveniences over the module functions above.
  - `recurrence_group_map(self) -> dict[str, str]` (line 491; public)
  - `recurrence_groups(self, group_key: str | None=None) -> list[dict[str, Any]]` (line 495; public)
  - `recurrence_review(self, case_kind: str | None=None) -> list[dict[str, Any]]` (line 499; public)
  - `recurrence_state(self) -> dict[str, Any] | None` (line 503; public)
  - `recurrence_escalation(self, diagnosis_id: str) -> dict[str, Any] | None` (line 507; public)
  - `recurrence_escalations(self) -> list[dict[str, Any]]` (line 511; public)
  - `recurrence_guard_cases(self) -> list[dict[str, Any]]` (line 515; public)

### Module constants

- `DERIVED_TABLES` ([src/learnloop/db/stores/recurrence.py](../../../../../../../src/learnloop/db/stores/recurrence.py), line 24)
- `ESCALATION_RESPONSES` ([src/learnloop/db/stores/recurrence.py](../../../../../../../src/learnloop/db/stores/recurrence.py), line 29)
- `GUARD_CASE_COLUMNS` ([src/learnloop/db/stores/recurrence.py](../../../../../../../src/learnloop/db/stores/recurrence.py), line 449)

### Explicit exports

`__all__` declares:

- `DERIVED_TABLES`
- `activate_prepared_projection`
- `projection_present`
- `clear_recurrence_projection`
- `ESCALATION_RESPONSES`
- `RecurrenceStoreMixin`
- `diagnoses_in_force`
- `diagnosis_with_citations`
- `escalation_for_diagnosis`
- `escalation_rows`
- `guard_case_rows`
- `hypothesis_episode_rows`
- `input_fingerprint_parts`
- `insert_escalation`
- `not_same_mistake_taps`
- `recurrence_group_map`
- `recurrence_group_rows`
- `recurrence_review_rows`
- `recurrence_state`
- `register_guard_cases`
- `replace_recurrence_projection`
- `same_cause_judgments`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 32)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 36)
- `_has_table(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 47)
- `_decode_escalation(names: Sequence[str], raw: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/recurrence.py), line 416)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `RecurrenceStoreMixin`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `register_guard_cases`; statically calls `register_guard_cases`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `insert_escalation`; statically calls `insert_escalation`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `module`; statically calls `activate_prepared_projection`, `clear_recurrence_projection`, `diagnoses_in_force`, `diagnosis_with_citations`, `hypothesis_episode_rows`, `input_fingerprint_parts`, `not_same_mistake_taps`, `projection_present`, `recurrence_state`, `replace_recurrence_projection`, `same_cause_judgments`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]], [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/daily_plan_fakes.py](../../../../../../../tests/daily_plan_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/deliverable_fixtures.py](../../../../../../../tests/deliverable_fixtures.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/diagnosis_split_helpers.py](../../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/e0_fakes.py](../../../../../../../tests/e0_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/exam_scope_fixtures.py](../../../../../../../tests/exam_scope_fixtures.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/followup_serve_helpers.py](../../../../../../../tests/followup_serve_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/helpers.py](../../../../../../../tests/helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/hint_fakes.py](../../../../../../../tests/hint_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/intent_fakes.py](../../../../../../../tests/intent_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/recurrence.py](../../../../../../../src/learnloop/db/stores/recurrence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
