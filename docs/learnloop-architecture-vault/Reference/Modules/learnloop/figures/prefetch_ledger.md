---
title: "learnloop.figures.prefetch_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/prefetch_ledger.py"
source_paths:
  - "src/learnloop/figures/prefetch_ledger.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.prefetch_ledger module"
  - "src/learnloop/figures/prefetch_ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.prefetch_ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.prefetch_ledger` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the prefetch ledger's reads (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §10b.6, §13.2b).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py) |
| Source lines | 616 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `plan_providers(vault: Any) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 55) — The vault's plan profiles (subscription billing): whose receipts are the plan's load.
- `pressed_waits_on(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 64) — The figure wait estimate's successor (``FIGURE_WAIT_VERSIONS``) with its switch ``figures.prefetch.pressed_waits`` on: decisions read ``prefetch_decision_v2`` (:func:`load_model`).
- `has_tables(connection: Any) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 75)
- `decisions(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 108)
- `observations(rows: Iterable[Mapping[str, Any]]) -> list[PM.Observation]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 114) — The opening model's data: built rows closed ``opened`` or ``neither`` (time order).
- `plan_receipts(connection: Any, plan_providers: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 131)
- `call_build_modes(connection: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 150) — ``owner_id`` -> the build mode (``pressed`` or ``prefetch``) of the build whose figure calls carry it, read from what the ledger records (no receipt says it: a pre-build's calls have the same owner kind as a press's).
- `background_call(row: Mapping[str, Any], modes: Mapping[str, str]) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 196) — Whether a receipt is the pre-builder's own background call (``prefetch_decision_v2``): the judge's, or a figure author's or rich author's call whose build was a pre-build (:func:`call_build_modes`).
- `day_load(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta=timedelta(0)) -> tuple[int, int]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 215) — ``(requests, known tokens)`` on a plan provider during one local day.
- `plan_day(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta=timedelta(0), paused: bool=False) -> PM.PlanDay` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 223) — One local day's plan load: its requests, its known tokens and how many requests reported them.
- `pauses(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 237)
- `plan_days(connection: Any, plan_providers: Iterable[str], *, today: str, offset: timedelta=timedelta(0)) -> list[PM.PlanDay]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 243) — Each past local day with plan activity (today excluded: it is still open).
- `blocked_minutes(connection: Any, plan_providers: Iterable[str], *, pressed_only: bool=False) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 263) — Measured foreground minutes a pause blocked, per pause: the pressed (non-background) plan calls that failed inside a pause's window, times the mean measured plan call latency.
- `blocked_basis(connection: Any, plan_providers: Iterable[str], *, pressed_only: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 272) — :func:`blocked_minutes` and what it counted: ``minutes`` (None: no pause or no measured latency), ``refused`` (failed calls inside a pause window it counted), ``background_left_out`` (the pre-builder's own failed calls inside one, :func:`background_call`), ``latency_calls`` and…
- `waits(connection: Any, *, pressed_only: bool=False) -> PM.Waits` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 340) — W_tier's measurements.
- `incremental(connection: Any) -> PM.Incremental` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 390) — The measured calls a build makes (Codex review F14): the figure author's calls per authored request (its receipts per ``figure:<request>`` owner) and the rich author's per rich job (per ``figure_rich:<request>`` owner).
- `load_model(connection: Any, plan_providers: Iterable[str], *, now: datetime, offset: timedelta=timedelta(0), pressed_waits: bool=True) -> PM.Model` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 407) — The decision model from the ledger.
- `started_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 433) — The decisions whose build started today (Codex review F6: the cap counts work when it starts, a resumed decision of an earlier day included): their prefetch requests stored today.
- `builds_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> int` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 445)
- `render_minutes_left(vault: Any, sqlite_path: Any, *, now: datetime | None=None) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 449) — ``figures.prefetch.max_daily_render_minutes`` less today's background render minutes (Codex review F6: the rich worker checks it when a prebuild's rich job starts and before each of its requests).
- `capacity_left(vault: Any, sqlite_path: Any, *, now: datetime | None=None) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 466) — Today's ``figures.prefetch`` caps both have room (the durable count of started builds): what a pass would admit before it reserves a build.
- `render_minutes_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 483) — Wall-clock minutes of today's background rich builds (a prebuild's rich figure: its request to its row).
- `report_block(connection: Any, *, since: datetime | None=None, plan_providers: Iterable[str]=(), now: datetime | None=None, pressed_waits: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 507) — ``learnloop reader report``'s ``prefetch`` block (spec §10b.6), read as the decisions read the ledger now (``pressed_waits``, :func:`load_model`).
- `add_report_block(report: dict[str, Any], sqlite_path: Any, *, since: str | None=None, plan_providers: Iterable[str]=(), now: datetime | None=None, pressed_waits: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 558) — Put :func:`report_block` under the reader report's ``figures`` (``learnloop reader report`` calls it only with ``figures.prefetch_enabled`` on, so off the report is P2b's).
- `anchor_of(row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 575)

### Module constants

- `DECISIONS_TABLE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 44)
- `PAUSES_TABLE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 45)
- `BUILD_DECISIONS` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 50)
- `DEFERRALS` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 52)
- `AUTHOR_PURPOSE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 144)
- `RICH_AUTHOR_PURPOSE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 145)
- `JUDGE_PURPOSE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 147)

### Explicit exports

`__all__` declares:

- `AUTHOR_PURPOSE`
- `BUILD_DECISIONS`
- `DECISIONS_TABLE`
- `DEFERRALS`
- `JUDGE_PURPOSE`
- `RICH_AUTHOR_PURPOSE`
- `add_report_block`
- `PAUSES_TABLE`
- `anchor_of`
- `background_call`
- `blocked_basis`
- `blocked_minutes`
- `builds_today`
- `call_build_modes`
- `capacity_left`
- `day_load`
- `decisions`
- `has_tables`
- `incremental`
- `load_model`
- `observations`
- `pauses`
- `plan_day`
- `plan_days`
- `plan_providers`
- `plan_receipts`
- `pressed_waits_on`
- `render_minutes_left`
- `render_minutes_today`
- `report_block`
- `started_today`
- `waits`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 81)
- `_when(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 86)
- `_minutes(start: Any, end: Any) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 96)
- `_dicts(cursor: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 103)
- `_local_day(value: Any, offset: timedelta) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 126)
- `_tokens(row: Mapping[str, Any]) -> int | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 207) — A receipt's reported tokens, or None when the provider reported none (missing, not zero).
- `_figures_by_request(connection: Any) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 317)
- `_waited_tier(rows: list[dict[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 330) — The tier a request's learner waited for: its rich figure's when one followed, else its own.
- `_built_at(connection: Any, row: Mapping[str, Any]) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 498) — When a decision's build started (its request row), a resumed decision's later than its own row; the decision's time when that request can't be read.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `add_report_block`, `plan_providers`, `pressed_waits_on`; statically calls `add_report_block`, `plan_providers`, `pressed_waits_on`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `_when`, `anchor_of`, `day_load`, `decisions`, `has_tables`, `load_model`, `render_minutes_left`, `render_minutes_today`, `started_today`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `render_minutes_left`; statically calls `render_minutes_left`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `capacity_left`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FIGURE_WAIT_VERSIONS`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `module`; calls `Incremental`, `Model`, `Observation`, `PlanDay`, `open_posterior`, `pause_posterior`, `wait_estimate`, `waits`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `ALL_SPEC_VERSIONS`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `billing_for`; calls `billing_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_the_recorded_seed_redraws_the_pass_exactly`
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import
  - `test_a_rich_figures_calls_are_named_by_the_rich_jobs_own_key_and_a_reuse_never_relabels_a_build`
  - `test_at_the_tag_the_rows_say_v2_and_the_records_carry_ws_basis`
  - `test_each_author_call_is_named_by_its_builds_mode_from_the_ledger`
  - `test_switched_off_or_below_the_tag_the_rows_say_v1_and_the_records_are_as_before`
  - `test_the_reader_report_reads_the_ledger_as_the_decisions_do`
- [tests/test_figure_wait_successor.py](../../../../../../tests/test_figure_wait_successor.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_and_with_the_switch_off`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_the_ledger_reads_nothing_before_migration_236`
  - `test_the_report_block_appears_only_with_the_switch`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f14_a_builds_expected_requests_are_measured`
  - `test_f5_a_deferred_decision_is_built_once_the_condition_clears`
  - `test_f6_a_resumed_build_spends_todays_cap`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_capped_decision_is_built_the_next_day_with_no_new_draw_and_its_row_stays_the_record`
  - `test_a_capped_decision_that_never_built_is_no_observation`
  - `test_a_figure_the_learner_pressed_for_meanwhile_is_not_counted_as_the_prebuilds`
  - `test_a_stored_request_is_linked_whatever_holds_new_builds_and_its_opening_is_observed`
  - `test_close_horizons_itself_links_first`
  - `test_the_report_and_the_model_count_a_resumed_build`
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../../tests/test_followups_batch7_prefetch_link_served.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains prefetch ledger within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
