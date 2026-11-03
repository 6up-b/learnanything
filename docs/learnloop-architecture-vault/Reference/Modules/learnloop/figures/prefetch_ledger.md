---
title: "learnloop.figures.prefetch_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/prefetch_ledger.py"
source_paths:
  - "src/learnloop/figures/prefetch_ledger.py"
source_commit: "workspace/uncommitted @ HEAD 9a4aaf6a01c0a130282a4d2315921cb166ba3f3a"
source_commit_timestamp: "2026-11-02T20:59:20-05:00"
source_worktree_state: "modified"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.prefetch_ledger` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: the prefetch ledger's reads (spec_reader_show_me_figures_v1 §10b.3, §10b.5, §10b.6, §13.2b).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py) |
| Source lines | 465 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 9a4aaf6a01c0a130282a4d2315921cb166ba3f3a` |
| Commit timestamp | `2026-11-02T20:59:20-05:00` |

## Public API

- `plan_providers(vault: Any) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 46) — The vault's plan profiles (subscription billing): whose receipts are the plan's load.
- `has_tables(connection: Any) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 55)
- `decisions(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 88)
- `observations(rows: Iterable[Mapping[str, Any]]) -> list[PM.Observation]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 94) — The opening model's data: built rows closed ``opened`` or ``neither`` (time order).
- `plan_receipts(connection: Any, plan_providers: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 111)
- `day_load(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta=timedelta(0)) -> tuple[int, int]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 129) — ``(requests, known tokens)`` on a plan provider during one local day.
- `plan_day(connection: Any, plan_providers: Iterable[str], day: str, *, offset: timedelta=timedelta(0), paused: bool=False) -> PM.PlanDay` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 137) — One local day's plan load: its requests, its known tokens and how many requests reported them.
- `pauses(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 151)
- `plan_days(connection: Any, plan_providers: Iterable[str], *, today: str, offset: timedelta=timedelta(0)) -> list[PM.PlanDay]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 157) — Each past local day with plan activity (today excluded: it is still open).
- `blocked_minutes(connection: Any, plan_providers: Iterable[str]) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 177) — Measured foreground minutes a pause blocked, per pause: the pressed (non-background) plan calls that failed inside a pause's window, times the mean measured plan call latency.
- `waits(connection: Any) -> PM.Waits` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 227)
- `incremental(connection: Any) -> PM.Incremental` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 258) — The measured calls a build makes (Codex review F14): the figure author's calls per authored request (its receipts per ``figure:<request>`` owner) and the rich author's per rich job (per ``figure_rich:<request>`` owner).
- `load_model(connection: Any, plan_providers: Iterable[str], *, now: datetime, offset: timedelta=timedelta(0)) -> PM.Model` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 275)
- `started_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> set[str]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 293) — The decisions whose build started today (Codex review F6: the cap counts work when it starts, a resumed decision of an earlier day included): their prefetch requests stored today.
- `builds_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> int` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 305)
- `render_minutes_left(vault: Any, sqlite_path: Any, *, now: datetime | None=None) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 309) — ``figures.prefetch.max_daily_render_minutes`` less today's background render minutes (Codex review F6: the rich worker checks it when a prebuild's rich job starts and before each of its requests).
- `capacity_left(vault: Any, sqlite_path: Any, *, now: datetime | None=None) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 326) — Today's ``figures.prefetch`` caps both have room (the durable count of started builds): what a pass would admit before it reserves a build.
- `render_minutes_today(connection: Any, *, today: str, offset: timedelta=timedelta(0)) -> float` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 343) — Wall-clock minutes of today's background rich builds (a prebuild's rich figure: its request to its row).
- `report_block(connection: Any, *, since: datetime | None=None, plan_providers: Iterable[str]=(), now: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 367) — ``learnloop reader report``'s ``prefetch`` block (spec §10b.6).
- `add_report_block(report: dict[str, Any], sqlite_path: Any, *, since: str | None=None, plan_providers: Iterable[str]=(), now: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 415) — Put :func:`report_block` under the reader report's ``figures`` (``learnloop reader report`` calls it only with ``figures.prefetch_enabled`` on, so off the report is P2b's).
- `anchor_of(row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 431)

### Module constants

- `DECISIONS_TABLE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 35)
- `PAUSES_TABLE` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 36)
- `BUILD_DECISIONS` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 41)
- `DEFERRALS` ([src/learnloop/figures/prefetch_ledger.py](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 43)

### Explicit exports

`__all__` declares:

- `BUILD_DECISIONS`
- `DECISIONS_TABLE`
- `DEFERRALS`
- `add_report_block`
- `PAUSES_TABLE`
- `anchor_of`
- `blocked_minutes`
- `builds_today`
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
- `render_minutes_left`
- `render_minutes_today`
- `report_block`
- `started_today`
- `waits`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 61)
- `_when(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 66)
- `_minutes(start: Any, end: Any) -> float | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 76)
- `_dicts(cursor: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 83)
- `_local_day(value: Any, offset: timedelta) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 106)
- `_tokens(row: Mapping[str, Any]) -> int | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 121) — A receipt's reported tokens, or None when the provider reported none (missing, not zero).
- `_figures_by_request(connection: Any) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 204)
- `_waited_tier(rows: list[dict[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 217) — The tier a request's learner waited for: its rich figure's when one followed, else its own.
- `_built_at(connection: Any, row: Mapping[str, Any]) -> datetime | None` ([source](../../../../../../src/learnloop/figures/prefetch_ledger.py), line 358) — When a decision's build started (its request row), a resumed decision's later than its own row; the decision's time when that request can't be read.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `add_report_block`, `plan_providers`; statically calls `add_report_block`, `plan_providers`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `_when`, `anchor_of`, `day_load`, `decisions`, `has_tables`, `load_model`, `render_minutes_left`, `render_minutes_today`, `started_today`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `render_minutes_left`; statically calls `render_minutes_left`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `capacity_left`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `module`; calls `Incremental`, `Model`, `Observation`, `PlanDay`, `open_posterior`, `pause_posterior`, `waits`
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
