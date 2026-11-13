---
title: "learnloop.db.stores.ad_serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/ad_serving.py"
source_paths:
  - "src/learnloop/db/stores/ad_serving.py"
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
  - "learnloop.db.stores.ad_serving module"
  - "src/learnloop/db/stores/ad_serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.ad_serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.ad_serving` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Adaptive difficulty AD2+AD3's tables: the only SQL writer of migration 214.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py) |
| Source lines | 516 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 38)
- `loads(value: Any, default: Any=None) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 42)
- `has_table(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 51)
- `insert_selection(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 76)
- `selection(connection: sqlite3.Connection, selection_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 88)
- `selection_by_key(connection: sqlite3.Connection, decision_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 93)
- `selections(connection: sqlite3.Connection, *, kind: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 98)
- `commissions_in_draw_order(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 105) — Every commission draw in its total draw order, ``(created_at, rowid)``: timestamps carry whole seconds, so two draws of one second are ordered by insertion (Codex verify F16).
- `commission_batch_id(selection_id: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 133)
- `open_commissions(connection: sqlite3.Connection, *, now: str | None=None, landed: Any=None, rows: Any=None, proposal_visible: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 137) — Commission draws still open at ``now`` (default: the current UTC time).
- `commission_expires_at(connection: sqlite3.Connection, row: Mapping[str, Any], *, proposal_visible: Any=None) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 199) — When an unlanded commission expires (an aware ``datetime``), or None while it cannot.
- `landed_after_expiry(connection: sqlite3.Connection, row: Mapping[str, Any], landed_at: Any, *, proposal_visible: Any=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 209) — Whether an item that landed at ``landed_at`` landed after its commission had expired.
- `instant(value: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 217) — An ISO timestamp as an aware ``datetime`` (naive reads as UTC), or None.
- `insert_commission_result(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 299)
- `commission_results(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 316)
- `insert_dose_row(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 327)
- `dose_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 338)
- `dose_draw_by_key(connection: sqlite3.Connection, draw_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 348)
- `insert_relatedness_run(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 357)
- `relatedness_runs(connection: sqlite3.Connection, *, subject_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 369)
- `insert_coupling_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 381)
- `coupling_versions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 390)
- `clear_derived(connection: sqlite3.Connection, tables: Iterable[str]) -> None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 401)
- `write_state(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 407)
- `write_trace(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 418)
- `write_scores(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 433)
- `read_state(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 449)
- `read_trace(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 459)
- `read_scores(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 470)

### Module constants

- `SELECTIONS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 28)
- `COMMISSION_RESULTS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 29)
- `DOSE_OFFERS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 30)
- `RELATEDNESS_RUNS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 31)
- `COUPLING_VERSIONS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 32)
- `STATE` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 33)
- `TRACE` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 34)
- `SCORES` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 35)
- `COMMISSION_EXPIRY_DAYS` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 126)
- `COMMISSION_BATCH_PREFIX` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 128)
- `MODELS_OFF_CODE` ([src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 130)

### Explicit exports

`__all__` declares:

- `COMMISSION_RESULTS`
- `COUPLING_VERSIONS`
- `DOSE_OFFERS`
- `RELATEDNESS_RUNS`
- `SCORES`
- `SELECTIONS`
- `STATE`
- `TRACE`
- `clear_derived`
- `commission_results`
- `coupling_versions`
- `dose_draw_by_key`
- `dose_rows`
- `dumps`
- `has_table`
- `insert_commission_result`
- `insert_coupling_version`
- `insert_dose_row`
- `insert_relatedness_run`
- `insert_selection`
- `loads`
- `open_commissions`
- `commission_batch_id`
- `COMMISSION_BATCH_PREFIX`
- `COMMISSION_EXPIRY_DAYS`
- `MODELS_OFF_CODE`
- `read_scores`
- `read_state`
- `read_trace`
- `relatedness_runs`
- `selection`
- `selection_by_key`
- `selections`
- `write_scores`
- `write_state`
- `write_trace`

## Internal implementation anchors

- `_row(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 57)
- `_select(connection: sqlite3.Connection, sql: str, args: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 61)
- `_insert(connection: sqlite3.Connection, table: str, values: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 66)
- `_decode_selection(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 115)
- `_instant(value: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 223)
- `_expiry_clock(connection: sqlite3.Connection, row: Mapping[str, Any], *, proposal_visible: Any=None) -> Any` ([source](../../../../../../../src/learnloop/db/stores/ad_serving.py), line 235) — When an unlanded commission's expiry clock started, or None while it cannot expire.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `module`; statically calls `dose_rows`, `has_table`, `insert_dose_row`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `module`; statically calls `has_table`, `insert_commission_result`, `instant`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`; statically calls `commission_results`, `dose_rows`, `landed_after_expiry`, `open_commissions`, `selections`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `module`; statically calls `has_table`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; statically calls `has_table`, `insert_coupling_version`, `insert_relatedness_run`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `clear_derived`, `has_table`, `write_state`, `write_trace`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `has_table`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `clear_derived`, `has_table`, `write_scores`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `has_table`, `insert_selection`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `module`; statically calls `relatedness_runs`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `commission_batch_id`; statically calls `commission_batch_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/ingest_queue|learnloop.db.stores.ingest_queue]] — imports `batch_outcome`, `job_outcome`; calls `batch_outcome`, `job_outcome`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — direct import
- [tests/ad3_dose_arm_helpers.py](../../../../../../../tests/ad3_dose_arm_helpers.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_late_uptake_callback_writes_nothing_when_ad_cannot_record_it`
  - `test_a_stale_run_never_answers_for_a_re_proposal`
  - `test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off`
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — direct import
- [tests/test_ad23_fix_r6.py](../../../../../../../tests/test_ad23_fix_r6.py) — direct import
  - `test_draws_of_one_second_are_ordered_by_insertion`
  - `test_one_owner_at_equal_timestamps_and_the_first_attribution_is_final`
- [tests/test_ad23_fix_r7.py](../../../../../../../tests/test_ad23_fix_r7.py) — direct import
- [tests/test_ad23_fix_r8.py](../../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_the_dose_arm_never_offers_or_returns_a_held_out_question`
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_repeated_reports_fire_the_readiness_flag_through_build`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
- [tests/test_ad2_serving.py](../../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_commission_result_appended_never_mutates_selection`
- [tests/test_ad3_relatedness.py](../../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_each_loading_and_coupling_is_one_ledger_row_and_invalid_outputs_drop`
  - `test_unchanged_input_makes_no_call_and_a_change_reproposes_only_what_it_touches`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/ad_serving.py](../../../../../../../src/learnloop/db/stores/ad_serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
