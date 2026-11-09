---
title: "learnloop.db.stores.router_suggestions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/router_suggestions.py"
source_paths:
  - "src/learnloop/db/stores/router_suggestions.py"
source_commit: "workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
source_worktree_state: "modified"
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
  - "learnloop.db.stores.router_suggestions module"
  - "src/learnloop/db/stores/router_suggestions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.router_suggestions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.router_suggestions` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL for teacher TE1b's lesson suggestions (migration 236; spec_teacher_v1 §15.1, §18.1).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py) |
| Source lines | 298 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65` |
| Commit timestamp | `2026-11-09T12:16:08-05:00` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 35)
- `receipt_key(day: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 41)
- `decision_for_day(connection: sqlite3.Connection, day: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 53)
- `decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 61)
- `decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 68) — Every lesson-suggestion decision, oldest first.
- `offer_decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 99) — Every drawn lesson offer (a ``plan_block`` or, from IH2, ``plan_interrupt`` decision naming one), oldest first; none below TE3b's tag.
- `offer_decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 108)
- `offer_drawn_since(connection: sqlite3.Connection, decision_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 115) — A lesson offer was drawn after this decision.
- `all_decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 125) — TE1b's daily decisions and TE3b's drawn offers together, oldest first (identical to :func:`decisions` while no offer was ever drawn).
- `responses(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 136) — Every learner response (never a release), in response order.
- `releases(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 145) — Every reservation let go (``released`` or ``expired``), in order.
- `response_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 154) — The decision's one learner response (never its release).
- `release_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 164) — The row that let the decision's reservation go, if one did.
- `response_for_lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 174)
- `insert_response(connection: sqlite3.Connection, *, decision_id: str, response: str, candidate_ref: str, learning_object_ids: Sequence[str], responded_at: str, lesson_id: str | None=None, session_id: str | None=None, detail: Mapping[str, Any] | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 181) — Append the decision's one response (or its one release); a second of either is a no-op (False).
- `lesson_exists(connection: sqlite3.Connection, lesson_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 209)
- `open_lesson_learning_objects(connection: sqlite3.Connection) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 213) — The LOs of every lesson still open.
- `last_lesson_opened_by_learning_object(connection: sqlite3.Connection) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 224) — Per LO, when the latest lesson on it opened.
- `last_lesson_ended_by_learning_object(connection: sqlite3.Connection) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 236) — Per LO, when the last lesson on it ended: the latest ``closed_at`` (``opened_at`` for one still open, which the candidates leave out anyway).
- `attempts_classified_by(connection: sqlite3.Connection, source: str) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 250) — The attempts with an activity classification written by ``source`` (e.g.
- `attempts_by_learning_object(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 261) — Each LO's attempts, oldest first (what the candidate reasons read).

### Module constants

- `RECEIPT_PREFIX` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 19)
- `RESPONSE_KINDS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 22)
- `RELEASE_KINDS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 25)
- `_RESPONSE_SQL` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 26)
- `_RELEASE_SQL` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 27)
- `RESPONSE_COLUMNS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 29)
- `OFFER_REF_PREFIX` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 79)
- `OFFER_DECISION_KINDS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 80)

### Explicit exports

`__all__` declares:

- `OFFER_REF_PREFIX`
- `RECEIPT_PREFIX`
- `RELEASE_KINDS`
- `RESPONSE_KINDS`
- `all_decisions`
- `attempts_by_learning_object`
- `attempts_classified_by`
- `decision`
- `decision_for_day`
- `decisions`
- `offer_decision`
- `offer_decisions`
- `insert_response`
- `last_lesson_ended_by_learning_object`
- `last_lesson_opened_by_learning_object`
- `lesson_exists`
- `open_lesson_learning_objects`
- `receipt_key`
- `release_for`
- `releases`
- `response_for`
- `response_for_lesson`
- `responses`
- `tables_present`

## Internal implementation anchors

- `_decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 45)
- `_offer_decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 83) — A drawn lesson offer in the shape of a shown TE1b decision (its context, its card, its day), so the acceptance model, the decline recovery, the ceiling and a pending Start read both alike.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `decisions`, `releases`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `offer_decision`, `offer_drawn_since`, `response_for`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; statically calls `all_decisions`, `insert_response`, `offer_decision`, `offer_decisions`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `all_decisions`, `attempts_by_learning_object`, `attempts_classified_by`, `decision`, `decision_for_day`, `decisions`, `insert_response`, `last_lesson_ended_by_learning_object`, `last_lesson_opened_by_learning_object`, `lesson_exists`, `offer_decision`, `open_lesson_learning_objects`, `receipt_key`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `module`; statically calls `tables_present`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `all_decisions`, `releases`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `lesson_exists`, `release_for`, `response_for`, `tables_present`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_review_fixes.py](../../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_on_a_database_before_lesson_suggestions_is_refused`
- [tests/test_ih2_lessons_compete.py](../../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_phone_follow_up_stays_forced_beside_an_open_desktop_offer`
  - `test_a_probe_arriving_during_an_open_offer_gets_a_new_decision_holding_both`
  - `test_the_acceptance_model_never_reads_a_superseded_offer`
- [tests/test_ih2_offer_ceiling_and_unseen.py](../../../../../../../tests/test_ih2_offer_ceiling_and_unseen.py) — direct import
  - `test_a_followups_draw_stands_only_while_no_offer_has_been_drawn_since`
  - `test_an_offer_drawn_after_a_miss_and_never_rendered_is_no_decline`
  - `test_an_offer_seen_and_left_is_still_ignored`
  - `test_off_or_below_the_tag_every_drawn_offer_counts_and_an_unseen_one_is_ignored`
  - `test_offers_nobody_saw_use_up_nothing_and_a_lesson_keeps_competing_past_the_ceiling`
  - `test_the_todays_card_sweep_agrees`
- [tests/test_ih2_one_open_offer.py](../../../../../../../tests/test_ih2_one_open_offer.py) — direct import
  - `test_a_boundary_drawing_an_offer_replaces_the_jobs_offer_placed_under_it`
  - `test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
- [tests/test_ih6_workbench_open_item.py](../../../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_a_drawn_offer_stays_as_it_is_when_a_workbench_opens`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_the_candidacy_condition_reads_no_score_magnitude_count_or_error_type`
- [tests/test_te3b_codex_review.py](../../../../../../../tests/test_te3b_codex_review.py) — direct import
- [tests/test_te3b_offers.py](../../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_drawn_offer_is_a_block_answered_on_its_own_decision`
  - `test_a_phone_step_holds_a_drawn_offer_for_the_desktop`
  - `test_moving_on_without_an_answer_is_ignored_at_the_next_boundary`
  - `test_te1bs_daily_card_is_drawn_only_where_the_objective_does_not_serve`
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_not_now_on_a_pending_card_releases_the_reservation`
  - `test_the_store_keeps_one_response_and_one_release_per_decision`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
