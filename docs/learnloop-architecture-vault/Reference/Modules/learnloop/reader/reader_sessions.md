---
title: "learnloop.reader.reader_sessions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_sessions.py"
source_paths:
  - "src/learnloop/reader/reader_sessions.py"
source_commit: "90c261ba8578c8fcc343b5158d8f18a1d091a30a"
source_commit_timestamp: "2026-10-17T10:18:04-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_sessions module"
  - "src/learnloop/reader/reader_sessions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_sessions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_sessions` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW6a: the reader session (spec_reader_workbench_v1 §9.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_sessions.py](../../../../../../src/learnloop/reader/reader_sessions.py) |
| Source lines | 245 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `90c261ba8578c8fcc343b5158d8f18a1d091a30a` |
| Commit timestamp | `2026-10-17T10:18:04-04:00` |

## Public API

- `class Visit` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 40)
- `class ReaderSession` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 48) — One reader session on one source: its visits and its window.
  - `session_id(self) -> str` (line 57; public) — The session is named by its first visit (stable as later visits join).
  - `contains(self, when: str | None) -> bool` (line 62; public)
  - `as_dict(self) -> dict[str, Any]` (line 67; public)
- `iso_seconds(moment: datetime) -> str` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 87) — ``moment`` as the ledgers write times (UTC, whole seconds, ``Z``).
- `visits_from_events(events: Iterable[Mapping[str, Any]]) -> list[Visit]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 111) — Visits from envelope rows (``kind``, ``created_at``, ``payload``), oldest first.
- `group_sessions(visits: Sequence[Visit], *, gap: timedelta=SESSION_GAP) -> list[ReaderSession]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 142) — Group visits into sessions per source, oldest first (by start).
- `split_sessions(sessions: Sequence[ReaderSession], *, current_visit_id: str | None, now: datetime, extraction_id: str | None=None, gap: timedelta=SESSION_GAP) -> tuple[ReaderSession | None, ReaderSession]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 167) — ``(previous, current)`` for one source's sessions, as seen at ``now``.
- `envelope_events(repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 204) — Every reader-envelope row that can date a visit (one read).
- `load_visits(repository: Any) -> list[Visit]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 218)
- `all_sessions(repository: Any) -> list[ReaderSession]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 222) — Every reader session on every source, oldest first.
- `sessions_for_source(repository: Any, extraction_id: str) -> list[ReaderSession]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 228)

### Module constants

- `SESSION_GAP` ([src/learnloop/reader/reader_sessions.py](../../../../../../src/learnloop/reader/reader_sessions.py), line 30)
- `ENVELOPE_KINDS` ([src/learnloop/reader/reader_sessions.py](../../../../../../src/learnloop/reader/reader_sessions.py), line 32)
- `VISIT_EVENT_KINDS` ([src/learnloop/reader/reader_sessions.py](../../../../../../src/learnloop/reader/reader_sessions.py), line 34)

### Explicit exports

`__all__` declares:

- `ENVELOPE_KINDS`
- `ReaderSession`
- `SESSION_GAP`
- `Visit`
- `all_sessions`
- `envelope_events`
- `group_sessions`
- `iso_seconds`
- `load_visits`
- `sessions_for_source`
- `split_sessions`
- `visits_from_events`

## Internal implementation anchors

- `_when(value: str | None) -> datetime | None` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 80)
- `_payload(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_sessions.py), line 93)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `ReaderSession`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `all_sessions`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `all_sessions`
- [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]] — imports `ReaderSession`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; statically calls `ReaderSession`, `all_sessions`, `iso_seconds`, `sessions_for_source`, `split_sessions`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `SESSION_GAP`, `module`; statically calls `claims_from_judgments`, `on_demand_enabled`, `positive_filter_enabled`, `propose_roles`, `sessions_for_source`, `split_sessions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]], [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_predictions.py](../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_rw6a_lists_a_missed_prediction_as_worth_a_second_look`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_revealed_families_are_the_sessions_reveals_only`
  - `test_the_provenance_carries_the_way_back_and_dl2_renders_it`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
- [tests/test_reader_observation_records.py](../../../../../../tests/test_reader_observation_records.py) — direct import
  - `test_a_record_outside_its_session_is_not_its_sessions`
  - `test_building_the_records_writes_nothing`
  - `test_records_are_deterministic_and_only_of_the_spec_kinds`
  - `test_still_unclear_becomes_one_routing_only_record`
  - `test_the_formative_builders_for_later_phases_read_nothing_today`
- [tests/test_reader_recap.py](../../../../../../tests/test_reader_recap.py) — direct import
  - `test_claims_needing_an_independent_check_are_assisted_only_facets`
  - `test_sessions_are_per_source_and_a_visit_without_a_close_ends_at_its_last_event`
  - `test_sessions_are_read_from_the_reader_envelope`
  - `test_the_card_is_about_the_session_before_the_current_one`
  - `test_the_summary_keeps_to_its_session`
  - `test_the_typed_summary_is_deterministic_from_the_ledgers`
  - `test_visits_less_than_30_minutes_apart_are_one_session`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it`
  - `test_a_real_missed_prediction_reaches_the_section_through_its_figure`
  - `test_a_session_that_touched_the_lo_only_through_a_figure_is_kept_for_its_prediction`

## Modification guidance

- Change reader sessions policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_sessions.py](../../../../../../src/learnloop/reader/reader_sessions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
