---
title: "learnloop.daily_plan.router_reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_reader.py"
source_paths:
  - "src/learnloop/daily_plan/router_reader.py"
source_commit: "2a4e97de6521c1c263a64c836230cc95534fcb92"
source_commit_timestamp: "2026-11-01T03:20:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.daily_plan.router_reader module"
  - "src/learnloop/daily_plan/router_reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_reader` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Reader workbench RW6b part 2: reader activity for the router's learner-state card (spec_reader_workbench_v1 §9.2; router spec §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py) |
| Source lines | 724 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2a4e97de6521c1c263a64c836230cc95534fcb92` |
| Commit timestamp | `2026-11-01T03:20:44-05:00` |

## Public API

- `reader_activity_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 103) — The section's switches: ``digest.enabled`` (RW6b part 2) and ``reader_inquiry.enabled`` (the sessions and inquiries are RW1a's).
- `narrative_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 112) — ``digest.narrative_enabled`` (under ``digest.enabled``): off, no saved narrative reaches the section (Codex review F4).
- `reader_activity_for_card(vault: Any, repository: Any, learning_object_ids: Sequence[str], as_of: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 636) — ``ReaderActivityV1`` for these LOs, read strictly before ``as_of`` (a pure read; None when switched off).
- `for_card(activity: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 695) — The card's copy (``evidence_sections.reader_activity``), or None when there is nothing to say (the card is then the predecessor's, byte for byte).

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 72)
- `ACTIVITY_VERSION` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 74)
- `AUTHORITY` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 76)
- `EXCERPT_CHARS` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 78)
- `NARRATIVE_LEDGER_TASK` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 81)
- `NARRATIVE_LEDGER_LEFT` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 82)
- `SECTIONS` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 84)
- `CARD_SECTION` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 89)
- `CARD_LIST_LIMIT` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 94)
- `_LIST_SECTIONS` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 95)
- `_NEWEST_LAST` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 97)
- `_EPISODE_OPEN` ([src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py), line 100)

### Explicit exports

`__all__` declares:

- `ACTIVITY_VERSION`
- `AUTHORITY`
- `CARD_LIST_LIMIT`
- `CARD_SECTION`
- `SECTIONS`
- `for_card`
- `narrative_enabled`
- `reader_activity_enabled`
- `reader_activity_for_card`

## Internal implementation anchors

- `_ids(values: Iterable[Any]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 121)
- `_before(value: Any, cutoff: datetime | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 125)
- `_excerpt(text: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 130)
- `_facets_of(vault: Any, lo_ids: Sequence[str]) -> set[str]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 135) — The LOs' facets (canonical): their own facet union and the evidence facets of their practice items (an item's facets are what a claim or a formative record names).
- `_item_lo(vault: Any, item_id: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 157)
- `_touches(summary: Mapping[str, Any], lo_ids: set[str], facets: set[str]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 162)
- `_record_in_scope(record: Mapping[str, Any], scope: set[str]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 167)
- `_days(start: Any, cutoff: datetime | None) -> int | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 171)
- `_inquiry_tree(history: Sequence[Mapping[str, Any]], cutoff: datetime | None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 181) — Per root exchange: the root's event, its exchange count and depth (exchanges strictly before ``cutoff``).
- `_status_events(repository: Any) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 201) — Each inquiry root's ``inquiry_status_set`` events, oldest first.
- `_resolution_as_of(root: Mapping[str, Any], events: Sequence[Mapping[str, Any]], cutoff: datetime | None) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 219) — The inquiry's status as it stood at ``cutoff`` (Codex review F5): the last status event before it; before its first event, that event's previous status.
- `_open_inquiries(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str], cutoff: datetime | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 234)
- `_assisted_only(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]], facets: set[str], lo_ids: set[str], cutoff: datetime | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 288)
- `_due_hint(repository: Any, commitment_id: str, cutoff: datetime | None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 331)
- `_line_los(line: Mapping[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 337)
- `_pending_followups(repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str], cutoff: datetime | None, as_of: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 345)
- `_gap_reversals(repository: Any, gap_ids: Sequence[str], cutoff: datetime | None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 381) — The learner's reversals of these named gaps made before ``cutoff``.
- `_episode_open(repository: Any, episode_id: str, cutoff: datetime | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 400) — A probe episode open at ``cutoff``: created before it and not closed before it (its ``completed_at``, else its last update, is the close).
- `_open_hypotheses(repository: Any, rows: Sequence[Mapping[str, Any]], lo_ids: set[str], cutoff: datetime | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 415) — Open hypotheses as they stood at ``cutoff`` (Codex review F8): a named gap the learner reversed is left out (it is kept, with its reversal, in the card's own open problems); a rival explanation lists only its targets still open (a probe episode closed by then, or a reversed gap,…
- `_prediction_los(vault: Any, repository: Any, rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 481) — Each missed figure prediction's LOs, through its figure's passages (Codex review F6: a prediction record names no facet or span of its own).
- `_prediction_events(summary: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 519) — The source events of the summary's missed figure predictions (both lists that carry one: missed predictions and formative records).
- `_predicts_on(summary: Mapping[str, Any], prediction_los: Mapping[str, set[str]], lo_ids: set[str]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 529) — Whether a missed prediction of the session resolves, through its figure's passages, to one of these LOs (final verify F6).
- `_records(rows: Sequence[Mapping[str, Any]], scope: set[str], key: str, prediction_los: Mapping[str, set[str]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 536)
- `_kept_comparisons(vault: Any, repository: Any, lo_ids: Sequence[str], as_of: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 553)
- `_candidate_actions(repository: Any, rows: Sequence[Mapping[str, Any]], pending: Sequence[Mapping[str, Any]], lo_ids: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 563)
- `_narrated_at(repository: Any, digest_ids: Sequence[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 603) — When each digest's narrative was kept: its ``judgment_ledger`` verdict (the narrative columns carry no time of their own).
- `_narrative(repository: Any, rows: Sequence[Mapping[str, Any]], cutoff: datetime | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/router_reader.py), line 618)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `for_card`, `reader_activity_enabled`, `reader_activity_for_card`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_withheld`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`
- [[Reference/Modules/learnloop/db/stores/reader_digests|learnloop.db.stores.reader_digests]] — imports `module`; calls `digests`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `facet_evidence_timelines`; calls `facet_evidence_timelines`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask_history`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `module`; calls `ReaderSession`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; calls `_action_events`, `_continue_at`, `_effective_success_since`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `kept_comparisons_for_card`; calls `kept_comparisons_for_card`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_historical_cutoff_ignores_a_later_unaided_success`
  - `test_a_historical_cutoff_reads_the_same_after_a_later_resolution`
  - `test_a_historical_cutoff_reads_the_same_after_a_later_undo`
  - `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it`
  - `test_a_real_missed_prediction_reaches_the_section_through_its_figure`
  - `test_a_resolved_inquiry_is_no_longer_open`
  - `test_a_reversed_gap_and_a_closed_episode_are_not_open_hypotheses`
  - `test_a_session_that_touched_the_lo_only_through_a_figure_is_kept_for_its_prediction`
  - `test_an_exam_anchored_inquiry_keeps_its_entry_and_never_its_words`
  - `test_an_unreadable_section_is_named_in_the_unknowns`
  - `test_it_is_a_pure_read`
  - `test_it_reads_strictly_before_as_of_and_only_these_los`
  - `test_narration_switched_off_after_a_narrative_was_saved_shows_it_nowhere`
  - `test_nothing_to_say_leaves_the_predecessor_card_byte_for_byte`
  - `test_the_budget_trims_reader_entries_deterministically_and_says_so`
  - `test_the_card_copy_is_bounded_and_says_what_it_left_out`
  - `test_the_plan_stores_the_card_with_its_reader_section`
  - `test_the_reader_activity_carries_what_the_spec_lists`
  - `test_the_router_reads_the_section_and_the_kill_switch_restores_the_predecessor`
  - `test_the_section_is_absent_with_its_switches_off`

## Modification guidance

- Make changes here when the responsibility remains router reader within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_reader.py](../../../../../../src/learnloop/daily_plan/router_reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
