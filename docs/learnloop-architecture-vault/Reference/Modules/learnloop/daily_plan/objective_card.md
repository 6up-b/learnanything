---
title: "learnloop.daily_plan.objective_card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_card.py"
source_paths:
  - "src/learnloop/daily_plan/objective_card.py"
source_commit: "1f9f56d046d309a903a4a45d868cff9b618bce30"
source_commit_timestamp: "2026-11-09T15:51:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_card module"
  - "src/learnloop/daily_plan/objective_card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_card` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec §8.3): the LLM policy's card, a decision-level variant of RO2's H3 card.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py) |
| Source lines | 283 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1f9f56d046d309a903a4a45d868cff9b618bce30` |
| Commit timestamp | `2026-11-09T15:51:40-05:00` |

## Public API

- `learner_statements(vault: Any, repository: Any, connection: Any, *, served_at: str) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 112) — The learner's statements known at ``served_at``, oldest first, and whether the read reached its limit.
- `miss_cause_entries(vault: Any, connection: Any, candidates: Sequence[Any], *, served_at: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 169) — SG1 (spec_slip_vs_gap_v1 §3 item 3): for the offer's topic and each repair candidate's, the latest miss's cause class probabilities, its surprise in words and its status (:func:`learnloop.router_objective.miss_cause.card_entry`), probe attempts included.
- `miss_cause_lines(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str, budget: int) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 192) — The same entries for the mid-block ``plan_interrupt`` request, whose state is text (the LLM's request only, never the Decider's), oldest dropped first to fit ``budget``.
- `statement_lines(vault: Any, repository: Any, *, served_at: str, budget: int) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 215) — The same statements for the mid-block ``plan_interrupt`` request, whose state is text: lines for the LLM's request only (never the Decider's), oldest dropped first to fit ``budget``.
- `decision_card(vault: Any, repository: Any, candidates: Sequence[Any], *, served_at: str, goals: Mapping[str, Any], session: Mapping[str, Any], budget: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 233) — The frozen card (the state), its evidence ids and what the budget left out.

### Module constants

- `CARD_VERSION` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 31)
- `CARD_VERSION_STATEMENTS` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 33)
- `CARD_VERSION_MISS_CAUSES` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 36)
- `MISS_CAUSES` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 38)
- `STATEMENTS` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 39)
- `STATEMENTS_NOTE` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 40)
- `_SECTION_ORDER` ([src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py), line 45)

### Explicit exports

`__all__` declares:

- `CARD_VERSION`
- `CARD_VERSION_MISS_CAUSES`
- `CARD_VERSION_STATEMENTS`
- `MISS_CAUSES`
- `STATEMENTS`
- `STATEMENTS_NOTE`
- `decision_card`
- `learner_statements`
- `miss_cause_entries`
- `miss_cause_lines`
- `statement_lines`

## Internal implementation anchors

- `_size(state: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 51)
- `_merged(built: Sequence[Mapping[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 55)
- `_trim(state: dict[str, Any], budget: int) -> dict[str, dict[str, int]]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 76) — Oldest first within each section, one entry per non-empty section per round, until it fits.
- `_goal_entry(goal: Mapping[str, Any], titles: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 98) — One goal as the policy sees it (Codex review F10): its date, its use weights and which topics it covers, with each topic's effective weight at the date (``dated``, unless ``topic_weights`` names the topic), the same weights the numeric policy's scoring reads.
- `_card_topics(candidates: Sequence[Any]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/objective_card.py), line 157) — SG1: the topics the card shows a miss's cause for: a lesson offer's and each repair candidate's.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `decision_card`, `miss_cause_lines`, `statement_lines`; statically calls `decision_card`, `miss_cause_lines`, `statement_lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `module`; calls `_Days`, `_excerpt`, `_topic`, `decision_sections_entry`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `LESSON_OFFER_SUBTYPE`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; calls `recent_learner_preferences`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PastWork`, `WITHHELD_UNREADABLE`; calls `PastWork`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `CARD_NOTE`, `module`; calls `card_entry`, `sensor`, `surprise_reference`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `WORDS`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `miss_cause_sensor_on`, `preferences_inform_router_on`; calls `miss_cause_sensor_on`, `preferences_inform_router_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_note_on_a_protected_attempt_shows_nothing_and_says_why`
  - `test_protection_unreadable_hides_every_note`
  - `test_the_budget_holds_oldest_first_and_says_what_it_left_out`
  - `test_the_card_carries_the_learners_own_statements`
  - `test_the_llm_reads_the_card_and_the_trace_names_it`
  - `test_the_mid_block_request_carries_them_for_the_llm_alone`
  - `test_the_read_is_bounded_by_the_card_questions_limit_and_says_so`
  - `test_with_the_switch_off_or_none_on_record_the_card_is_the_predecessors_bytes`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f10_the_policy_card_names_each_goals_topics_and_their_weights`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_protection_holds_on_the_llm_policys_card`
- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_every_build_card_and_fit_of_the_jobs_is_the_same_with_the_pool`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_a_regrade_or_hold_between_the_jobs_card_and_numeric_builds_reaches_the_numeric_policy`
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_nothing_protected_or_answer_restating_reaches_the_card_and_probe_attempts_gain_the_cause`
  - `test_off_and_below_the_tag_the_card_is_the_predecessors`
  - `test_the_card_shows_offer_and_repair_topics_only_and_names_v4_only_with_an_entry`
  - `test_the_interrupt_lines_fit_their_budget_heading_included`
  - `test_the_whole_card_off_and_below_the_tag_is_byte_identical_and_on_differs_by_the_section_alone`

## Modification guidance

- Make changes here when the responsibility remains objective card within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_card.py](../../../../../../src/learnloop/daily_plan/objective_card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
