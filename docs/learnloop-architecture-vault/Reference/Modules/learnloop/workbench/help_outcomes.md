---
title: "learnloop.workbench.help_outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/help_outcomes.py"
source_paths:
  - "src/learnloop/workbench/help_outcomes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.help_outcomes module"
  - "src/learnloop/workbench/help_outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.help_outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.help_outcomes` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2c: what helps this learner, a replayable read (spec_reader_workbench_v1 §5.10, G39).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py) |
| Source lines | 795 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `safe_slug(value: Any) -> str | None` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 143) — A strategy slug the lines may carry, or None (free text never is).
- `class HelpKindOutcome` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 151) — One help kind on one facet (module docstring).
  - `as_dict(self) -> dict[str, Any]` (line 168; public)
- `class GoesOff` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 182) — Where the work tends to go off on one facet (module docstring).
  - `as_dict(self) -> dict[str, Any]` (line 191; public)
  - `empty(self) -> bool` (line 203; public)
- `class HelpOutcomesV1` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 208)
  - `as_dict(self) -> dict[str, Any]` (line 217; public)
- `help_outcomes(repository: Any, facet_ids: Iterable[str], as_of: str, *, item_facets: Mapping[str, Iterable[str]], vault: Any | None=None) -> HelpOutcomesV1` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 351) — The read (module docstring).
- `lines_for(outcomes: HelpOutcomesV1, *, limit: int=MAX_LINES, per_facet: int=MAX_LINES_PER_FACET) -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 709) — Typed lines (kinds, levels, counts, outcomes; never text): per facet, the help kinds shown most, then those with the most observed outcomes (a continuation or a later independent attempt), then the most recent; then where the work goes off.
- `item_facets_of(vault: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 761) — Each item's evidence facets, canonical (the vault's).
- `lines_for_item(vault: Any, repository: Any, item: Any, *, as_of: str) -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 772) — The lines for one item's facets at ``as_of`` (the workbench's hint context).

### Module constants

- `VERSION` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 84)
- `LABEL` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 85)
- `GUESSES_LABEL` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 86)
- `CAUSES_LABEL` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 87)
- `CORRECT` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 90)
- `S5_SUCCESS` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 92)
- `MAX_LINES` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 95)
- `MAX_LINES_PER_FACET` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 96)
- `_SLUG` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 98)
- `_HELP_KINDS` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 99)
- `FIGURE_KIND` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 104)
- `_S5_COLD_PASS` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 105)
- `_S5_COLD_FAIL` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 106)
- `_S5_COLD_PENDING` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 107)
- `_PASSAGE_KINDS` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 249)
- `UNJUDGED` ([src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py), line 607)

### Explicit exports

`__all__` declares:

- `CAUSES_LABEL`
- `GUESSES_LABEL`
- `GoesOff`
- `HelpKindOutcome`
- `HelpOutcomesV1`
- `LABEL`
- `VERSION`
- `help_outcomes`
- `item_facets_of`
- `lines_for`
- `lines_for_item`
- `safe_slug`

## Internal implementation anchors

- `_when(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 110)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 120)
- `_table(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 127)
- `_grade(correctness: Any) -> str` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 132)
- `_day(value: datetime | None) -> str | None` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 139)
- `_rows(connection: sqlite3.Connection, sql: str, params: Sequence[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 228)
- `_help_key(row: Mapping[str, Any]) -> tuple[str, str | None, str | None]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 233)
- `_passage_pick(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 252)
- `_after(value: Any, cutoff: datetime) -> bool` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 256) — Was this stamp written after the cutoff?
- `_grades_at(connection: sqlite3.Connection, attempts: Mapping[str, Mapping[str, Any]], cutoff: datetime, vault: Any | None) -> dict[str, tuple[Any, bool]]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 263) — ``(correctness, held)`` of each attempt as the grading ledger stood at the cutoff (review F6), with the shared grading-history machinery.
- `_grade_from_ledger(attempt: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]], cutoff: datetime, vault: Any | None, namespace: Any) -> tuple[Any, bool]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 319)
- `_s5_outcomes_at(connection: sqlite3.Connection, vault: Any | None, cutoff: datetime, graded: Mapping[str, tuple[Any, bool]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 589) — S5's outcomes at ``cutoff`` by intervention id (fix round 2, 5), from the sources spec's own historical read (:func:`learnloop.substrate.intervention_outcomes.outcomes_as_of`) over the grades as they stood then; None when S5's tables are absent.
- `class _Unjudged(Mapping[str, Any])` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 610) — Every intervention's outcome is :data:`UNJUDGED` (no vault given).
- `_s5_links(connection: sqlite3.Connection, assist_ids: set[str], cutoff: datetime, outcomes: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any] | None], set[str]]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 623) — The S5 records that name a workbench passage BY ITS ASSIST ID (the record's ``caller_ref``, or ``assets.help_assist_id``; never a match on time, item or spans), written by ``cutoff``: ``({assist id: its outcome row or None}, {those records' ids})``.
- `_s5_next(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 654)
- `_s5_cold(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 666)
- `_causes(proposal_json: Any) -> list[str]` ([source](../../../../../../src/learnloop/workbench/help_outcomes.py), line 684) — The diagnoser's typed causes: never a statement or a quote.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `lines_for_item`; statically calls `lines_for_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `help_kind_enabled`; calls `help_kind_enabled`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`; calls `current_epoch`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/hints/report_adaptive|learnloop.hints.report_adaptive]] — imports `module`; calls `map_paths`
- [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]] — imports `workbench_unaided_progress`; calls `workbench_unaided_progress`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `epoch_held_as_of`; calls `epoch_held_as_of`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`; calls `grade_held_for_review`, `grade_is_held`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `outcomes_as_of`; calls `outcomes_as_of`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `pathlib`, `re`, `sqlite3`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_help_outcomes_list_figure_deterministically_and_not_when_off`
- [tests/test_help_outcomes.py](../../../../../../tests/test_help_outcomes.py) — direct import
  - `test_a_facet_without_history_gives_no_lines`
  - `test_as_of_replays_the_past`
  - `test_continuation_reads_the_next_check_with_no_other_hint_between`
  - `test_f10_an_s5_record_naming_a_passage_is_its_outcome_and_is_not_counted_again`
  - `test_f3_hints_the_learner_picked_stay_in_the_history_passage_picks_do_not_count_twice`
  - `test_f4_a_step_already_on_the_page_that_a_later_check_validates_is_not_progress`
  - `test_f4_a_step_written_after_the_hint_that_the_check_validates_is_progress`
  - `test_f4_an_intervening_example_is_further_help_but_the_hints_own_bridge_is_not`
  - `test_f4_no_work_recorded_at_delivery_stays_unknown`
  - `test_f5_a_comparison_gets_no_credit_for_an_attempt_before_it_was_opened`
  - `test_f6_a_hold_released_after_as_of_still_held_then`
  - `test_f6_a_later_regrade_never_changes_what_as_of_said`
  - `test_help_outcomes_is_deterministic_and_reads_only_existing_rows`
  - `test_lines_are_typed_records_that_never_carry_the_answer`
  - `test_lines_for_ranks_every_requested_facet`
  - `test_s5_absent_reads_as_absent`
  - `test_s5_outcomes_are_read_not_rederived_and_pending_until_as_of`
  - `test_where_the_work_goes_off_keeps_guesses_and_the_diagnosers_typed_causes`
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_5_a_later_regrade_never_changes_s5s_outcome_at_as_of_linked_or_standalone`
  - `test_fr2_5_an_s5_record_read_before_its_censoring_horizon_is_pending_not_expired`
  - `test_fr2_6_an_unrelated_edit_to_an_earlier_valid_step_is_not_progress_after_a_waypoint`
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_m1_rewording_an_already_valid_step_is_progress_for_neither_the_hint_nor_its_example`

## Modification guidance

- Make changes here when the responsibility remains help outcomes within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/help_outcomes.py](../../../../../../src/learnloop/workbench/help_outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
