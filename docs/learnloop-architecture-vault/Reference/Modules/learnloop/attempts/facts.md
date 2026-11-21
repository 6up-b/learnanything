---
title: "learnloop.attempts.facts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/facts.py"
source_paths:
  - "src/learnloop/attempts/facts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.facts module"
  - "src/learnloop/attempts/facts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.facts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.facts` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Attempt facts: what happened around one answer, each fact with where it came from and how well it was captured.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py) |
| Source lines | 572 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FieldCoverage` ([source](../../../../../../src/learnloop/attempts/facts.py), line 71) — How one fact was captured: its coverage, the stored source it was read from, the source rows, and why.
  - `__post_init__(self) -> None` (line 80; internal)
- `class HelpFact` ([source](../../../../../../src/learnloop/attempts/facts.py), line 86) — One ``help_assists`` row: an assist requested on the attempt's item under its submission, shown or not, attached to the attempt or not.
- `class QuestionFact` ([source](../../../../../../src/learnloop/attempts/facts.py), line 107) — One ``question_events`` row bound to the attempt: a question to the tutor during it.
- `class RevealFact` ([source](../../../../../../src/learnloop/attempts/facts.py), line 120) — One ``reveal_events`` row on the attempt's item between the item's previous attempt and this one: how much of the answer a surface displayed, and when.
- `class AttemptFacts` ([source](../../../../../../src/learnloop/attempts/facts.py), line 136) — What happened around one attempt, as stored (module docstring).
  - `bound_presentation(self) -> bool` (line 173; public) — The attempt answers a recorded plan presentation (adaptive difficulty's ``bound_presentation``).
  - `coverage_of(self, field_name: str) -> FieldCoverage | None` (line 178; public)
  - `assists(self, kind: str, *, shown: bool | None=None) -> tuple[HelpFact, ...]` (line 184; public) — The help rows of one ``assist_kind`` (``check``, ``figure``, ``hint``...), optionally only the shown ones.
  - `shown_before(self) -> tuple[RevealFact, ...]` (line 189; public)
  - `shown_during(self) -> tuple[RevealFact, ...]` (line 192; public)
- `submitted_facts(*, attempt_type: Any, hints_used: Any=0, primed: Any=False, correctness: Any=None, first_hint_progress: str | None=None, declared_dont_know: Any=False, declared_stuck: Any=False, attempt_id: str | None=None, practice_item_id: str | None=None, learning_object_id: str | None=None) -> AttemptFacts` ([source](../../../../../../src/learnloop/attempts/facts.py), line 214) — The submitted values alone, verbatim, with every detail source ``not_read``: what a reader holding an attempt row (or a draft) knows.
- `facts_from_draft(draft: Any) -> AttemptFacts` ([source](../../../../../../src/learnloop/attempts/facts.py), line 237) — The facts of a submission before it has an attempt id: the draft's own fields (an ``attempts.attempts.AttemptDraft`` or anything with its field names), no database read, every stored detail ``not_read``.
- `class FactReader(Protocol)` ([source](../../../../../../src/learnloop/attempts/facts.py), line 272) — Where :func:`collect_facts` reads: a connection, and the caller's visibility over the rows it reads.
  - `connection(self) -> Any` (line 276; public)
  - `visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]` (line 278; public)
- `class ConnectionReader` ([source](../../../../../../src/learnloop/attempts/facts.py), line 282) — Every row is visible: the caller's own connection, as the readers outside adaptive difficulty read.
  - `visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]` (line 287; public)
- `class FilteredReader` ([source](../../../../../../src/learnloop/attempts/facts.py), line 292) — Rows filtered by a view with adaptive difficulty's material view's shape (``filter(connection, table, rows)``): what it withholds (an item held out for an exam, a revision cut from held-out material, and every attempt, help row, question and reveal that names one) is never read…
  - `visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]` (line 300; public)
- `collect_facts(reader: FactReader, attempt_ids: Iterable[str], cutoff: Cutoff) -> dict[str, AttemptFacts]` ([source](../../../../../../src/learnloop/attempts/facts.py), line 343) — The facts of each stored attempt the reader shows and the cutoff admits, by attempt id, in the order asked.

### Module constants

- `PRESENT` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 42)
- `COUNT_ONLY` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 45)
- `PARTIAL` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 48)
- `ABSENT` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 50)
- `NOT_READ` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 52)
- `COVERAGES` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 53)
- `DETAIL_FULL` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 56)
- `DETAIL_COUNTS_ONLY` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 57)
- `BEFORE_SERVE` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 61)
- `DURING` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 62)
- `POSITION_UNKNOWN` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 63)
- `_COUNTED_KINDS` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 67)
- `_SUBMITTED_SOURCES` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 198)
- `_DETAIL_SOURCES` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 203)
- `_SUBMITTED_COVERAGE` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 210)
- `_CHUNK` ([src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py), line 304)

### Explicit exports

`__all__` declares:

- `ABSENT`
- `AttemptFacts`
- `BEFORE_SERVE`
- `COUNT_ONLY`
- `COVERAGES`
- `ConnectionReader`
- `DETAIL_COUNTS_ONLY`
- `DETAIL_FULL`
- `DURING`
- `FactReader`
- `FieldCoverage`
- `FilteredReader`
- `HelpFact`
- `NOT_READ`
- `PARTIAL`
- `POSITION_UNKNOWN`
- `PRESENT`
- `QuestionFact`
- `RevealFact`
- `collect_facts`
- `facts_from_draft`
- `submitted_facts`

## Internal implementation anchors

- `_replace(facts: AttemptFacts, **changes: Any) -> AttemptFacts` ([source](../../../../../../src/learnloop/attempts/facts.py), line 263)
- `_tables(connection: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/attempts/facts.py), line 307)
- `_select(reader: FactReader, table: str, where: str, values: Sequence[Any], order: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/facts.py), line 312) — ``SELECT *`` (every column, so the reader's visibility rule sees every reference) in chunks of ids.
- `_instant(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/attempts/facts.py), line 326)
- `_known_by(value: Any, known_at: datetime | None) -> bool` ([source](../../../../../../src/learnloop/attempts/facts.py), line 335) — Under historical corrections, a time at or before the cutoff's known time; an unreadable one is not (fails closed, as the cutoff's own ``as_known_at`` rule).
- `_facts(row: Mapping[str, Any], *, tables: frozenset[str], help_rows: list[dict[str, Any]], question_rows: list[dict[str, Any]], reveal_rows: list[dict[str, Any]], previous_at: str | None, served: Mapping[str, Any], then: bool, known_at: datetime | None) -> AttemptFacts` ([source](../../../../../../src/learnloop/attempts/facts.py), line 424)
- `_help_fact(row: Mapping[str, Any], attempt_id: str, *, then: bool, known_at: datetime | None) -> HelpFact` ([source](../../../../../../src/learnloop/attempts/facts.py), line 499)
- `_help_coverage(row: Mapping[str, Any], hints: tuple[HelpFact, ...], tables: frozenset[str], *, then: bool) -> FieldCoverage` ([source](../../../../../../src/learnloop/attempts/facts.py), line 515)
- `_question_fact(row: Mapping[str, Any]) -> QuestionFact` ([source](../../../../../../src/learnloop/attempts/facts.py), line 538)
- `_reveal_facts(row: Mapping[str, Any], reveal_rows: list[dict[str, Any]], previous_at: str | None, presented_at: Any, *, then: bool, known_at: datetime | None) -> tuple[RevealFact, ...]` ([source](../../../../../../src/learnloop/attempts/facts.py), line 546)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/fact_predicates|learnloop.attempts.fact_predicates]] — imports `AttemptFacts`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `submitted_facts`; statically calls `submitted_facts`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `submitted_facts`; statically calls `submitted_facts`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `submitted_facts`; statically calls `submitted_facts`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `submitted_facts`; statically calls `submitted_facts`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `AttemptFacts`, `submitted_facts`; statically calls `submitted_facts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/evidence_cutoff|learnloop.db.evidence_cutoff]] — imports `CORRECTIONS_THEN`, `Cutoff`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/fact_predicates|learnloop.attempts.fact_predicates]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]], [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/attempt_facts_helpers.py](../../../../../../tests/attempt_facts_helpers.py) — direct import
- [tests/test_attempt_fact_predicates.py](../../../../../../tests/test_attempt_fact_predicates.py) — direct import
  - `test_the_fsrs_cap_lookup_keeps_key_coercion_and_fallback`
- [tests/test_attempt_facts.py](../../../../../../tests/test_attempt_facts.py) — direct import
  - `test_a_count_that_disagrees_with_its_rows_keeps_both`
  - `test_a_hint_requested_and_never_shown_is_kept_as_not_shown`
  - `test_a_hint_under_the_submission_key_is_found_before_and_after_its_late_attachment`
  - `test_a_reveal_under_the_priming_threshold_leaves_primed_as_submitted`
  - `test_a_withheld_item_behind_the_material_view_reads_as_if_it_were_never_stored`
  - `test_adaptive_difficultys_categories_over_the_facts_match_its_own_on_the_full_matrix`
  - `test_an_old_attempt_keeps_its_counts_and_says_it_has_nothing_more`
  - `test_as_known_at_a_cutoff_a_later_showing_reads_not_shown_and_the_attachment_partial`
  - `test_draft_facts_need_no_attempt_id_and_no_database`
  - `test_each_reveal_kind_is_kept_with_its_amount_and_its_side_of_the_serve`
  - `test_partial_modern_capture_keeps_the_count_and_the_rows_apart`
  - `test_the_collector_reads_a_fixed_handful_whatever_the_number_of_attempts`
  - `test_without_the_help_table_the_source_is_absent_not_no_help`

## Modification guidance

- Change facts policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/facts.py](../../../../../../src/learnloop/attempts/facts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
