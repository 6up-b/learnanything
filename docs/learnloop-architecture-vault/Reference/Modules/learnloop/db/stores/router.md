---
title: "learnloop.db.stores.router"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/router.py"
source_paths:
  - "src/learnloop/db/stores/router.py"
source_commit: "224700d26fdc3e8a31cb6a4fa481efff3ef1d939"
source_commit_timestamp: "2026-11-09T04:50:36-05:00"
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
  - "learnloop.db.stores.router module"
  - "src/learnloop/db/stores/router.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.router`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.router` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for router R1's tables (migration 181).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py) |
| Source lines | 393 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `224700d26fdc3e8a31cb6a4fa481efff3ef1d939` |
| Commit timestamp | `2026-11-09T04:50:36-05:00` |

## Public API

- `insert_router_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 110) — Append one decision; a repeated ``receipt_key`` is a no-op (returns False).
- `append_router_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 132) — Append one decision inside the caller's transaction, never failing it.
- `record_learner_pick(connection: sqlite3.Connection, *, scheduler_candidate_id: str, practice_item_id: str, session_id: str, entry_surface: str, submission_id: str | None, created_at: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 155) — Log a learner pick that overrides a logged Today offer's choice.
- `preferences_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 266) — The preference ledger exists (a vault below migration 251, or a historical copy, has none).
- `insert_learner_preference(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 274) — Append one preference (IH3); a repeated ``id`` is a no-op (returns False), so a retry of the same act writes once.
- `learner_preference(connection: sqlite3.Connection, preference_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 288)
- `learner_preference_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 293) — Every preference, oldest first (IH4's reader).
- `recent_learner_preferences(connection: sqlite3.Connection, *, at: str, limit: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 302) — The newest ``limit`` preferences known at ``at``, oldest first (the LLM card's read, IH4).
- `router_payloads_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 313)
- `append_router_payload(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 319) — Store one decision payload (router R2a: its learner-state card) inside the caller's transaction, never failing it: a refused row rolls back alone with a warning.
- `prune_router_payloads(connection: sqlite3.Connection, *, before: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 344) — Delete payloads stored before ``before`` (``router.payload_retention_days``).
- `router_payload(connection: sqlite3.Connection, decision_id: str, kind: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 355)
- `replace_router_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 364) — Replace the derived outcome cache whole (its one replayer only).
- `router_decision_rows(connection: sqlite3.Connection, *, limit: int | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 377) — Decisions oldest first (the newest ``limit`` when given).
- `router_outcome_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router.py), line 391)

### Module constants

- `ROUTER_LOG_VERSION` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 23)
- `ROUTER_DESIGNS` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 57)
- `DECISION_COLUMNS` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 71)
- `OUTCOME_COLUMNS` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 84)
- `PAYLOAD_COLUMNS` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 105)
- `OVERRIDE_KEY_PREFIX` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 257)
- `PREFERENCE_COLUMNS` ([src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py), line 260)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `router_decision_rows`, `router_payload`, `router_payloads_present`; statically calls `router_decision_rows`, `router_payload`, `router_payloads_present`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `module`; statically calls `insert_learner_preference`, `insert_router_decision`, `learner_preference`, `preferences_present`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `learner_preference_rows`; statically calls `learner_preference_rows`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `ROUTER_LOG_VERSION`, `insert_router_decision`; statically calls `insert_router_decision`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `module`; statically calls `recent_learner_preferences`
- [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] — imports `append_router_decision`, `record_learner_pick`; statically calls `append_router_decision`, `record_learner_pick`
- [[Reference/Modules/learnloop/router/decisions|learnloop.router.decisions]] — imports `ROUTER_LOG_VERSION`, `insert_router_decision`; statically calls `insert_router_decision`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `OVERRIDE_KEY_PREFIX`, `replace_router_outcomes`; statically calls `replace_router_outcomes`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `ROUTER_LOG_VERSION`, `append_router_decision`, `append_router_payload`, `prune_router_payloads`; statically calls `append_router_decision`, `append_router_payload`, `prune_router_payloads`
- [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] — imports `module`; statically calls `learner_preference_rows`, `preferences_present`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `module`; statically calls `learner_preference_rows`, `preferences_present`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `module`; statically calls `learner_preference`, `preferences_present`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a4_delayed_completion.py](../../../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
  - `test_the_lesson_suggestion_adapter_reads_the_same_definition`
- [tests/test_data_capture_codex_review.py](../../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_data_capture_successor.py](../../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_outcomes_cache_is_rebuilt_under_the_vaults_version`
- [tests/test_held_grade_composition.py](../../../../../../../tests/test_held_grade_composition.py) — direct import
- [tests/test_ih3_learner_preferences.py](../../../../../../../tests/test_ih3_learner_preferences.py) — direct import
- [tests/test_ih3_phone_host.py](../../../../../../../tests/test_ih3_phone_host.py) — direct import
  - `test_a_phone_choosing_the_drawn_lesson_is_told_it_waits_and_it_stays_an_agreement`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_staged_reads_nothing`
  - `test_w_itself_never_reads_a_preference_or_a_pick`
- [tests/test_ro0_codex_review.py](../../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_staged_decision_keeps_its_ad_numbers`
- [tests/test_router_coldness_covariates.py](../../../../../../../tests/test_router_coldness_covariates.py) — direct import
- [tests/test_router_offer_log.py](../../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_row_the_ledger_constraints_refuse_raises_instead_of_vanishing`
  - `test_an_unregistered_design_is_refused`
- [tests/test_router_outcomes.py](../../../../../../../tests/test_router_outcomes.py) — direct import
- [tests/test_router_r1_composition.py](../../../../../../../tests/test_router_r1_composition.py) — direct import
  - `test_a_refused_plan_row_never_blocks_the_plan`
- [tests/test_router_r2c_retrieval.py](../../../../../../../tests/test_router_r2c_retrieval.py) — direct import
- [tests/test_teacher_te1b_suggestions.py](../../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_decision_logs_the_draw_with_its_exact_propensity`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/router.py](../../../../../../../src/learnloop/db/stores/router.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
