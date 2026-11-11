---
title: "learnloop.db.stores.help_assists"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/help_assists.py"
source_paths:
  - "src/learnloop/db/stores/help_assists.py"
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
  - "learnloop.db.stores.help_assists module"
  - "src/learnloop/db/stores/help_assists.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.help_assists`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.help_assists` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Adaptive hints H0: ``help_assists`` (migration 210; ``work_md``: migration 230; RW5d P3's ``figure`` rows, ``explore_figure``, ``take_step`` and ``figure_id``: migration 232).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py) |
| Source lines | 758 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `kept_draft(work_md: str | None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 49) — The draft a row keeps (``work_md``): bounded by :data:`WORK_MD_CHARS`, None when empty.
- `insert_assist(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 56) — Insert one assist row; columns left out are NULL (or their default).
- `stamp_submitted(connection: sqlite3.Connection, *, submission_id: str, practice_item_id: str, submitted_at: str, latency_seconds: float | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 69) — Record when a submission reached the sidecar, before grading, and the open-to-submit latency it sent, together, on its still-unattached rows.
- `attach_submission(connection: sqlite3.Connection, *, submission_id: str, practice_item_id: str, attempt_id: str, submitted_at: str | None=None, latency_seconds: float | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 92) — Fill ``attempt_id`` on the rows recorded under ``submission_id`` for the item (and ``submitted_at`` with ``latency_seconds``, together, where no stamp was made); returns how many it attached.
- `assist(connection: sqlite3.Connection, assist_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 121) — One row as a dict, or None.
- `submission_assists(connection: sqlite3.Connection, *, submission_id: str, practice_item_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 130) — Every row recorded under a submission key for the item, in the order requested (shown or not, attached or not): this attempt's hints.
- `mark_shown(connection: sqlite3.Connection, assist_id: str, *, shown_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 177) — A prepared server hint (``shown = 0``) delivered to the learner: shown once, with its time.
- `count_closed(connection: sqlite3.Connection, assist_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 195) — Whether a row's count is closed by a committed attempt (:data:`_CLOSED`).
- `submission_committed(connection: sqlite3.Connection, submission_id: str | None, *, practice_item_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 202) — Whether a submission key already committed its attempt (of ``practice_item_id`` when given: another item's key is not this one's).
- `keyless_window_start(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 220) — Where a keyless submit's window starts: the item's last attempt in this session (round 3, W1), or None.
- `authored_reveals_in_window(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, since: str | None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 231) — How many distinct authored hints the practice screen revealed (H0's client-counted rows, any key, still unattached) on the item in this session after ``since`` (:func:`keyless_window_start`).
- `server_fold(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, submission_id: str | None, since: str | None=None, any_session: bool=False) -> tuple[int, bool]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 250) — The server-counted hints a submission folds (hints spec §5): how many shown rows at levels 1-3, and whether any shown row is at level 4-5 (``primed``).
- `attach_keyless_fold(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, since: str | None, attempt_id: str, submitted_at: str | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 322) — A keyless attempt takes the server hint rows its fold counted (round 3b): ``attempt_id`` set once (NULL to a value, as H0's attach writes and its identity trigger allows), in the attempt's own write transaction, so no later fold, keyed or keyless, counts them again.
- `attach_keyed_fold(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, submission_id: str, attempt_id: str, submitted_at: str | None=None, latency_seconds: float | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 343) — A keyed attempt takes the rows its fold counted (follow-ups Nov 2; the successor's fold, ``any_session``, only), in its own write transaction, as a keyless one does (:func:`attach_keyless_fold`): the fold's own rows (:func:`_fold_rows`, so every help kind it counts), and no othe…
- `fold_row_count(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, submission_id: str | None, since: str | None=None, any_session: bool=False) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 367) — How many rows a fold counts (:func:`_fold_rows`), every level: what a workbench problem's record line names as "shown on the answer box" before Submit (H2b fix round 3, ruling R1; read-only).
- `stamp_window_submitted(connection: sqlite3.Connection, *, practice_item_id: str, session_id: str, since: str | None, submitted_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 379) — When a workbench submission reached the sidecar, before grading, on the window's rows it folds (H2b re-review F9, under fix round 3's ruling R1: :func:`_fold_rows` with no key) that are still unstamped: the first stamp stays, as :func:`stamp_submitted`'s.
- `class WorkbenchFold` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 402) — What a workbench problem's shown, server-counted, still-unattached rows add to its attempt (Reader §5.4): one per check and per level 1-3 hint, and ``primed`` when any shown hint was at level 4 or 5.
  - `hints(self) -> int` (line 415; public) — The hint-equivalents: every check, every level 1-3 hint and (RW5d P3) every figure opened.
  - `primed(self) -> bool` (line 421; public)
  - `empty(self) -> bool` (line 425; public)
- `workbench_fold(connection: sqlite3.Connection, *, workbench_session_id: str, practice_item_id: str | None=None) -> WorkbenchFold` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 429) — The one count the workbench's record line and its submit read (Reader §5.4, G5, G62): the session's ``surface = 'workbench'`` rows that are shown, counted by the server and attached to no attempt.
- `workbench_assist_ids(connection: sqlite3.Connection, *, workbench_session_id: str, practice_item_id: str | None=None) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 461) — The ids of the rows :func:`workbench_fold` counts as hint-equivalents (shown, server-counted, unattached checks and level 1-3 hints), so a submit can count each distinct row once across problems (RW2b fix round 5, items 4-5).
- `workbench_window(connection: sqlite3.Connection, *, practice_item_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 499) — The item's workbench server assists in the window (:data:`_WINDOW`): ``(counted, worked)``: the checks and level 1-3 hints an attempt of the item counts, and the level 4-5 hints that prime it (fix round 14, item 1: never counted); the attempt attaches both.
- `workbench_window_ids(connection: sqlite3.Connection, *, practice_item_id: str) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 516) — The ids an attempt of the item counts (:func:`workbench_window`).
- `unattached_ids(connection: sqlite3.Connection, ids: Sequence[str]) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 522) — Which of ``ids`` no attempt has taken yet.
- `attach_workbench_rows(connection: sqlite3.Connection, ids: Sequence[str], attempt_id: str, submitted_at: str | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 537) — The attempt takes the workbench server assists it counted, in its own write transaction (NULL to a value, as H0's attach writes), so no later attempt counts them again (fix round 13).
- `workbench_rows(connection: sqlite3.Connection, workbench_session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 554) — Every row of a workbench problem, in the order requested.
- `bind_workbench_rows(connection: sqlite3.Connection, *, workbench_session_id: str, practice_session_id: str, attempt_id: str, submission_id: str, practice_item_id: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 568) — At a workbench submit, after its attempt committed: the practice session the problem was submitted in (NULL until then, set once, as the schema says) on every row of the problem, and the attempt on its rows under the submission's key (H0's attach rule: by key alone, idempotent,…
- `settle_bridge(connection: sqlite3.Connection, assist_id: str, fields: Mapping[str, Any], *, kind: str='bridge') -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 593) — A bridge (or, RW2c, a worked-example) search's outcome on the row written before it ran (its place among the problem's calls): only its result columns and its draw's log, only while unshown.
- `settle_compare(connection: sqlite3.Connection, assist_id: str, fields: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 616) — A ``compare_methods`` row's AI-written lines, after the reference was shown (its row and reveal were written first): only its result columns.
- `compare_rows_for(connection: sqlite3.Connection, workbench_session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 631) — A problem's ``compare_methods`` rows, oldest first.
- `mark_bridge_shown(connection: sqlite3.Connection, assist_id: str, *, shown_at: str, kind: str='bridge') -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 637) — A bridge (or, RW2c, a worked example; counted by neither) delivered to the workbench: shown once, and only one that found a passage (a search's row is written before it runs, RW2b fix round 1, F9).
- `open_figure_rows(connection: sqlite3.Connection, *, practice_item_id: str, submission_ids: Sequence[str]=(), workbench_session_ids: Sequence[str]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 656) — An open attempt's figure rows (``assist_kind = 'figure'``, attached to no attempt) under any of its identities: the answer box's submission keys and the workbench problems (Codex review F3: the caller passes CA2's aliases, so the same figure is never counted twice across the hos…
- `submission_session_conflict(connection: sqlite3.Connection, *, practice_item_id: str, submission_id: str, session_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 685) — Codex review F1: whether an unattached server row of this item and submission key names another practice session (the key is the attach's, the session the fold's: one key in two sessions would attach a row its attempt's fold never counted).
- `take_step(connection: sqlite3.Connection, token: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 699) — A cold take step's row by its token (its id), or None.
- `bind_figure(connection: sqlite3.Connection, assist_id: str, figure_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 708) — A take step's row names the figure it was taken for (set once: the identity trigger fixes it).
- `figure_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 718) — Every figure row, oldest first (the help outcomes and the report).

### Module constants

- `TABLE` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 20)
- `COLUMNS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 24)
- `_COLUMN_SET` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 41)
- `WORK_MD_CHARS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 46)
- `HINT_EQUIVALENT_KINDS_SQL` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 150)
- `_CLOSED` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 159)
- `_WINDOW` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 488)
- `_BRIDGE_RESULT_COLUMNS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 586)
- `_DRAW_COLUMNS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 588)
- `PASSAGE_KINDS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 590)
- `_COMPARE_RESULT_COLUMNS` ([src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py), line 613)

### Explicit exports

`__all__` declares:

- `attach_workbench_rows`
- `unattached_ids`
- `workbench_assist_ids`
- `workbench_window`
- `workbench_window_ids`
- `COLUMNS`
- `TABLE`
- `assist`
- `attach_keyed_fold`
- `attach_keyless_fold`
- `attach_submission`
- `authored_reveals_in_window`
- `count_closed`
- `fold_row_count`
- `insert_assist`
- `keyless_window_start`
- `mark_shown`
- `server_fold`
- `stamp_submitted`
- `stamp_window_submitted`
- `submission_assists`
- `submission_committed`
- `PASSAGE_KINDS`
- `WorkbenchFold`
- `bind_workbench_rows`
- `compare_rows_for`
- `mark_bridge_shown`
- `settle_bridge`
- `settle_compare`
- `workbench_fold`
- `workbench_rows`
- `WORK_MD_CHARS`
- `kept_draft`
- `HINT_EQUIVALENT_KINDS_SQL`
- `bind_figure`
- `figure_rows`
- `open_figure_rows`
- `submission_session_conflict`
- `take_step`

## Internal implementation anchors

- `_fold_rows(*, practice_item_id: str, session_id: str, submission_id: str | None, since: str | None, any_session: bool=False) -> tuple[str, tuple[Any, ...]]` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 282) — The rows a fold counts (:func:`server_fold`) and its attempt attaches (:func:`attach_keyless_fold`, :func:`attach_keyed_fold`): one definition, so the rows attached are exactly the rows counted, whatever help kinds it counts.
- `_latency(value: float | None) -> float | None` ([source](../../../../../../../src/learnloop/db/stores/help_assists.py), line 733) — A latency the client sent, or None (a negative one is not believed).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `attach_keyed_fold`, `attach_keyless_fold`, `attach_workbench_rows`, `keyless_window_start`, `server_fold`, `unattached_ids`; statically calls `attach_keyed_fold`, `attach_keyless_fold`, `attach_workbench_rows`, `keyless_window_start`, `server_fold`, `unattached_ids`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `module`; statically calls `assist`, `count_closed`, `insert_assist`, `kept_draft`, `mark_shown`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `module`; statically calls `submission_assists`
- [[Reference/Modules/learnloop/hints/telemetry|learnloop.hints.telemetry]] — imports `module`; statically calls `attach_submission`, `insert_assist`, `kept_draft`, `stamp_submitted`, `stamp_window_submitted`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; statically calls `assist`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `WorkbenchFold`, `module`; statically calls `WorkbenchFold`, `workbench_assist_ids`, `workbench_fold`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `insert_assist`; statically calls `insert_assist`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `module`; statically calls `assist`, `insert_assist`, `settle_bridge`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; statically calls `insert_assist`, `workbench_rows`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `module`; statically calls `assist`, `compare_rows_for`, `insert_assist`, `settle_compare`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `assist`, `module`; statically calls `assist`, `workbench_rows`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `module`; statically calls `assist`, `insert_assist`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`; statically calls `assist`, `insert_assist`, `settle_bridge`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `bind_figure`, `insert_assist`, `open_figure_rows`, `submission_committed`, `submission_session_conflict`, `take_step`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`; statically calls `assist`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `authored_reveals_in_window`, `keyless_window_start`, `workbench_window`; statically calls `authored_reveals_in_window`, `keyless_window_start`, `workbench_window`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `bind_workbench_rows`, `fold_row_count`, `keyless_window_start`, `stamp_submitted`; statically calls `bind_workbench_rows`, `fold_row_count`, `keyless_window_start`, `stamp_submitted`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `assist`, `mark_bridge_shown`, `workbench_rows`; statically calls `assist`, `mark_bridge_shown`, `workbench_rows`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `assist`; statically calls `assist`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]], [[Reference/Modules/learnloop/hints/telemetry|learnloop.hints.telemetry]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/help_outcomes_helpers.py](../../../../../../../tests/help_outcomes_helpers.py) — direct import
- [tests/test_compare_methods.py](../../../../../../../tests/test_compare_methods.py) — direct import
  - `test_f7_only_the_claims_holder_settles_and_a_stale_claim_can_be_taken_over`
- [tests/test_figures_help.py](../../../../../../../tests/test_figures_help.py) — direct import
  - `test_the_workbench_fold_counts_a_figure_once`
- [tests/test_followups_nov2_help_fold.py](../../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
  - `test_every_help_kind_the_keyed_fold_counts_is_exactly_what_the_attempt_attaches`
- [tests/test_help_assist_figures_migration.py](../../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_232_on_the_durability_lane`
  - `test_232_widens_three_checks_adds_figure_id_and_keeps_every_row`
- [tests/test_help_assist_work_md_migration.py](../../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_230_adds_only_the_nullable_column_and_keeps_every_row`
  - `test_230_on_the_durability_lane`
  - `test_the_kept_draft_is_bounded_and_empty_is_none`
- [tests/test_help_assists_schema.py](../../../../../../../tests/test_help_assists_schema.py) — direct import
  - `test_210_adds_help_assists_and_nothing_else`
  - `test_every_column_both_specs_write_is_created_once`
  - `test_the_ledger_keeps_rows_and_an_attached_attempt`
  - `test_the_store_attach_matches_the_submission_key_only`
  - `test_the_store_refuses_unknown_columns`
  - `test_the_workbench_lifecycle_binds_each_deferred_column_once`
- [tests/test_hint_h2a_review_round3.py](../../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
  - `test_w1_the_fence_and_the_keyless_fold_share_one_window`
- [tests/test_hint_h2b_rereview.py](../../../../../../../tests/test_hint_h2b_rereview.py) — direct import
  - `test_f9_the_first_submit_time_stays`
- [tests/test_hint_telemetry.py](../../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_failed_write_never_fails_the_reveal_or_the_submit`
  - `test_submit_never_attaches_another_sessions_or_items_rows`
  - `test_the_report_summarises_any_number_of_rows`
- [tests/test_ro0_question_state.py](../../../../../../../tests/test_ro0_question_state.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/help_assists.py](../../../../../../../src/learnloop/db/stores/help_assists.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
