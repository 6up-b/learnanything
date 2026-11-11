---
title: "learnloop.hints.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/report.py"
source_paths:
  - "src/learnloop/hints/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.report module"
  - "src/learnloop/hints/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.report` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: `learnloop hints report`: which hints are used and what follows (spec_adaptive_hints_v1 §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py) |
| Source lines | 826 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `item_caps(practice_items: Iterable[Any]) -> dict[str, tuple[str, int]]` ([source](../../../../../../src/learnloop/hints/report.py), line 136) — Each item's content hash and ``max_useful_hints`` (0: no cap), for the report's completeness check: a row's cap is known only when the item is unchanged since the hint (the row's ``practice_item_hash``).
- `build_hints_report(sqlite_path: Path | str, *, since: str | None=None, surface: str | None=None, now: datetime | None=None, item_caps: Mapping[str, tuple[str, int]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report.py), line 269) — Compute the descriptive rows from ``help_assists`` and the attempts (pure read).

### Module constants

- `REPORT_VERSION` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 102)
- `TOP_ITEMS` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 104)
- `INTERVAL_LEVEL` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 106)
- `_Z` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 107)
- `UNAIDED_UNKNOWN_REASONS` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 109)
- `_REACHED` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 115)
- `_NOT_REACHED` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 116)
- `_ROW_COLUMNS` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 119)
- `INTO_ATTEMPT_UNKNOWN_REASONS` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 129)
- `_SELF_GRADE_DISCLOSURE` ([src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py), line 133)

### Explicit exports

`__all__` declares:

- `INTO_ATTEMPT_UNKNOWN_REASONS`
- `REPORT_VERSION`
- `UNAIDED_UNKNOWN_REASONS`
- `build_hints_report`
- `item_caps`

## Internal implementation anchors

- `_own_disclosure(reveal: Mapping[str, Any], submission_id: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/report.py), line 146) — The submission's own plain self-grade disclosure (shown after its trace was frozen; a trace changed after it makes the attempt primed).
- `_hint_reveal(reveal: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/hints/report.py), line 162) — A shown hint's own key overlap (H2a's delivery: ``tutor_answer`` with basis ``hint:<kind>:L<level>``): the hint is one of the help rows already, so its reveal is not other assistance (H2b).
- `_wilson(count: int, of: int) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/report.py), line 171)
- `_binomial_pmf(n: int, q: float) -> list[float]` ([source](../../../../../../src/learnloop/hints/report.py), line 184) — P(B = i) for i = 0..n, B ~ Binomial(n, q), 0 < q < 1, in log space: the exact coefficient times ``q**i`` overflows a float from n = 1030 (review round 2, V1).
- `_quantile_interval(ordered: list[float], q: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report.py), line 198) — A distribution-free interval for the q-quantile: the order statistics [X(j), X(k)] (1-based) cover it with probability P(j <= B <= k - 1), B ~ Binomial(n, q).
- `_percentiles(values: Iterable[float | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report.py), line 227)
- `_share(count: int, of: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report.py), line 242)
- `_when(value: str | None) -> datetime | None` ([source](../../../../../../src/learnloop/hints/report.py), line 246)
- `_outcome(correctness: float | None) -> str` ([source](../../../../../../src/learnloop/hints/report.py), line 253)
- `_table_exists(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/hints/report.py), line 263)
- `_split_columns(members: list[dict[str, Any]], attempts: Mapping[str, Any], unaided: Any, replies: Mapping[str, list[str]], later_independent: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report.py), line 662) — The expertise-reversal split's columns for one group of hints (§6.3): unaided next progress, "too big a jump" and any "doesn't connect" reply, and later independent success on the item.
- `_second(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/hints/report.py), line 684) — A stored instant at whole-second resolution: attempts and tutor events are stamped to the second, so two stamps in the same second cannot be ordered by time.
- `_window_position(event: Mapping[str, Any], *, attempt_id: str, previous_id: str | None, since: datetime | None, until: datetime | None) -> str` ([source](../../../../../../src/learnloop/hints/report.py), line 693) — Where an event falls against the attempt's window (after the item's previous attempt, up to this one): ``inside``, ``outside`` or ``ambiguous``.
- `_other_assistance(connection: Any, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/hints/report.py), line 732) — Assistance the attempt recorded outside its help rows, read uncapped from the records themselves: ``"help"``, ``"ambiguous"`` (an event whose order against the window cannot be established), ``"workbench"`` (a workbench problem that could have been open in the window and bound t…
- `_never_this_item(problem: Mapping[str, Any], item_id: str) -> bool` ([source](../../../../../../src/learnloop/hints/report.py), line 787) — Whether a workbench problem could never have been bound to the item (round 5).
- `_could_overlap(problem: Mapping[str, Any], *, since: datetime | None, until: datetime | None) -> bool` ([source](../../../../../../src/learnloop/hints/report.py), line 808) — Whether a workbench problem could have been open during the window, from its timestamps alone (round 4): opened at or before the evaluated attempt and not closed before the window opened.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]] — imports `build_hints_report`, `item_caps`; statically calls `build_hints_report`, `item_caps`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/hints/report_adaptive|learnloop.hints.report_adaptive]] — imports `module`; calls `answered_id`, `expertise_reversal`, `help_seeking`, `ledger`, `loads`, `map_paths`, `progress_by_next_placement`, `routes`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `PROMPT_VERSION`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/hint_h2b_review_helpers.py](../../../../../../tests/hint_h2b_review_helpers.py) — direct import
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_a_report_with_no_figure_has_no_figure_block`
  - `test_the_hints_report_shows_the_figure_kind_with_its_sample_size`
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_a_served_hint_keeps_the_draft_it_answered_and_the_grader_never_sees_it`
- [tests/test_hint_report.py](../../../../../../tests/test_hint_report.py) — direct import
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_failed_attach_is_repaired_by_recovery_and_never_given_to_the_next_attempt`
  - `test_a_row_without_a_submit_time_is_timed_unknown_not_from_the_grade`
  - `test_an_ungraded_next_attempt_is_reported_ungraded_never_fail`
  - `test_order_statistic_intervals_hold_at_any_sample_size`
  - `test_reveal_to_submit_ends_at_the_submit_not_at_the_graded_attempt`
  - `test_shares_and_summaries_carry_intervals_with_explicit_small_sample_behaviour`
  - `test_the_report_describes_authored_reveals_and_what_followed`
  - `test_the_report_summarises_any_number_of_rows`
  - `test_the_stable_terms_reproduce_every_exact_interval_below_the_overflow`
  - `test_unaided_next_progress_is_settled_by_the_grade_where_it_can_be`
  - `test_unaided_progress_is_reached_only_when_the_uncapped_records_show_no_other_help`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/report.py](../../../../../../src/learnloop/hints/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
