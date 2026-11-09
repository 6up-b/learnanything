---
title: "learnloop.db.stores.router_objective"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/router_objective.py"
source_paths:
  - "src/learnloop/db/stores/router_objective.py"
source_commit: "84b890f02cd674436ba3b9ce3ab22628680d0783"
source_commit_timestamp: "2026-11-05T07:25:07-05:00"
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
  - "learnloop.db.stores.router_objective module"
  - "src/learnloop/db/stores/router_objective.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.router_objective`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.router_objective` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: RO0's append-only records (migration 243; spec_router_objective_v1 §4).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py) |
| Source lines | 266 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `84b890f02cd674436ba3b9ce3ab22628680d0783` |
| Commit timestamp | `2026-11-05T07:25:07-05:00` |

## Public API

- `table_present(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 41)
- `column_present(connection: sqlite3.Connection, table: str, column: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 47) — Whether the database has the column (a vault below migration 243 has not).
- `split_receipt(table: str, row: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 94) — ``row`` as its predecessor wrote it (RO0's fields out), and RO0's fields on it that hold a value.
- `fill_receipt(connection: sqlite3.Connection, table: str, key: Any, values: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 102) — RO0's fields on a row just inserted without them, in their own savepoint, or False: nothing to write (a vault below migration 243 has no such column), or refused, with a warning, and the row stands with them null.
- `insert_session_receipt(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 127) — One session receipt, or False: refused (a warning), or that session already has one of this kind.
- `session_receipt(connection: sqlite3.Connection, session_id: str, kind: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 133)
- `insert_decision_state(connection: sqlite3.Connection, row: Mapping[str, Any], content: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 141) — One decision's state, compressed, or False (a warning) when refused.
- `decision_state(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 150) — One decision's receipt with its state decompressed (read-only), or None.
- `insert_trace(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 170) — RO4 §8.8: one decision's trace (migration 246), in its own savepoint; False (a warning) when refused.
- `trace(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 178) — One decision's trace with its JSON decoded (read-only), or None.
- `traces(connection: sqlite3.Connection, *, since: str | None=None, limit: int | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 192) — The traces' columns (not their JSON), oldest first.
- `insert_goal_event(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 210)
- `insert_assignment(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 223) — One RO5 assignment, in its own savepoint; False (a warning) when refused.
- `latest_goal_events(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 231) — Each goal's newest lifecycle row, what the next load compares its YAML against.

### Module constants

- `SESSION_RECEIPTS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 21)
- `DECISION_STATE` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 22)
- `GOAL_EVENTS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 23)
- `SESSION_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 25)
- `STATE_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 30)
- `GOAL_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 35)
- `RECEIPT_FIELDS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 73)
- `_RECEIPT_KEYS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 81)
- `_RECEIPT_WHAT` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 85)
- `TRACES` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 161)
- `TRACE_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 162)
- `ASSIGNMENTS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 216)
- `ASSIGNMENT_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 217)

### Explicit exports

`__all__` declares:

- `ASSIGNMENTS`
- `ASSIGNMENT_COLUMNS`
- `insert_assignment`
- `DECISION_STATE`
- `TRACES`
- `TRACE_COLUMNS`
- `insert_trace`
- `trace`
- `traces`
- `GOAL_COLUMNS`
- `GOAL_EVENTS`
- `SESSION_COLUMNS`
- `SESSION_RECEIPTS`
- `STATE_COLUMNS`
- `column_present`
- `decision_state`
- `insert_decision_state`
- `insert_goal_event`
- `insert_session_receipt`
- `latest_goal_events`
- `RECEIPT_FIELDS`
- `fill_receipt`
- `session_receipt`
- `split_receipt`
- `table_present`

## Internal implementation anchors

- `_append(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 53)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `table_present`, `trace`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `session_receipt`, `table_present`, `traces`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `module`; statically calls `append`, `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; statically calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `module`; statically calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] — imports `module`; statically calls `column_present`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; statically calls `insert_assignment`
- [[Reference/Modules/learnloop/router_objective/combiner_data|learnloop.router_objective.combiner_data]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; statically calls `insert_decision_state`, `table_present`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; statically calls `column_present`
- [[Reference/Modules/learnloop/router_objective/forecast_resolve|learnloop.router_objective.forecast_resolve]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/goal_lifecycle|learnloop.router_objective.goal_lifecycle]] — imports `module`; statically calls `insert_goal_event`, `latest_goal_events`, `table_present`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/question_state|learnloop.router_objective.question_state]] — imports `module`; statically calls `column_present`, `table_present`
- [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] — imports `module`; statically calls `insert_session_receipt`, `table_present`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] — imports `module`; statically calls `decision_state`, `insert_trace`, `table_present`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `module`; statically calls `table_present`, `trace`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`, `zlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]], [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih4_preferences_inform_router.py](../../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
- [tests/test_instruct_handoff_ih0.py](../../../../../../../tests/test_instruct_handoff_ih0.py) — direct import
- [tests/test_ro0_codex_review.py](../../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_rows7_8_sessions.py](../../../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
  - `test_a_refused_receipt_rolls_back_alone_and_the_session_stands`
  - `test_the_store_rolls_back_a_refused_row_alone`
- [tests/test_ro0_rows9_13_decision_state.py](../../../../../../../tests/test_ro0_rows9_13_decision_state.py) — direct import
  - `test_a_refused_state_rolls_back_alone_and_the_decision_stands`
- [tests/test_ro4_codex_review.py](../../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_ro4_objective_serving.py](../../../../../../../tests/test_ro4_objective_serving.py) — direct import
- [tests/test_ro4_trace_report.py](../../../../../../../tests/test_ro4_trace_report.py) — direct import
- [tests/test_ro5_landing.py](../../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_1_at_the_tag_fg1s_gate_is_the_two_policy_mix_with_its_trace`
  - `test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols`
- [tests/test_ro5_stop_coin.py](../../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_every_arm_off_at_the_tag_is_mvp_047_exactly`
  - `test_kappa_stays_the_seed_until_a_randomized_offer_has_a_response`
  - `test_serving_records_each_coin_with_its_exact_probability_and_availability`
- [tests/test_ro6_codex_rereview.py](../../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`
- [tests/test_ro6_codex_review.py](../../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
- [tests/test_ro6_landing.py](../../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r12_with_the_carried_evaluation_blocked_the_choosers_wait_returns`
  - `test_r2_a_served_decision_logs_its_objective_under_the_generator_it_served`
  - `test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup`
  - `test_r7_a_served_decision_freezes_its_support_and_the_measurable_tail`
- [tests/test_ro6_serving.py](../../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_the_features_frozen_at_serve_equal_the_rebuild_from_the_trace_and_ro0s_receipt`
- [tests/test_ro6_tail_data.py](../../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_a_few_weeks_on_a_copy_shaped_synthetic_vault`
  - `test_a_row_received_after_the_moment_never_enters_a_feature`
- [tests/test_rofu_ad_link.py](../../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_numeric_policy_reads_ads_own_predictive_only_at_the_tag_with_its_switch`
- [tests/test_rofu_carried.py](../../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
- [tests/test_rofu_generator_switches.py](../../../../../../../tests/test_rofu_generator_switches.py) — direct import
- [tests/test_rofu_learning.py](../../../../../../../tests/test_rofu_learning.py) — direct import
- [tests/test_rofu_monotone.py](../../../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_the_numeric_policy_reads_the_monotone_combiner_only_at_the_tag_with_its_switch`
- [tests/test_rofu_review_draw.py](../../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_the_numeric_policy_draws_consistently_only_at_the_tag_with_its_switch`
- [tests/test_rofu_weeks.py](../../../../../../../tests/test_rofu_weeks.py) — direct import
  - `test_two_weeks_before_and_after_the_batch`
- [tests/test_rospeed_join.py](../../../../../../../tests/test_rospeed_join.py) — direct import
- [tests/test_te3b_offers.py](../../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_drawn_offer_is_a_block_answered_on_its_own_decision`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
