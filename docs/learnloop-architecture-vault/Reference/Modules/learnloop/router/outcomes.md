---
title: "learnloop.router.outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/outcomes.py"
source_paths:
  - "src/learnloop/router/outcomes.py"
source_commit: "2cfe5cce75c95910c18c0105c36d952e15ab11cc"
source_commit_timestamp: "2026-11-03T23:34:25-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.outcomes module"
  - "src/learnloop/router/outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.outcomes` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R1: ``router_outcomes`` (DERIVED, one replayer) per logged decision.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py) |
| Source lines | 1441 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2cfe5cce75c95910c18c0105c36d952e15ab11cc` |
| Commit timestamp | `2026-11-03T23:34:25-05:00` |

## Public API

- `outcome_version_for(config: Any) -> str` ([source](../../../../../../src/learnloop/router/outcomes.py), line 225) — The outcome version a vault's outcomes are derived under (module docstring).
- `servable_items_by_learning_object(vault: Any) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 639) — Each learning object's active, servable practice items (vault content).
- `fold_measurement(objective: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1052) — An objective's measurement as one plain record (this adapter's and the capture report's).
- `answer_completion(connection: sqlite3.Connection, attempt_id: str, *, decided_at: str, reader_exposures: Iterable[tuple[str, str]]) -> DC.Completion | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1081) — What the shared definition makes of one attempt as the delayed retrieval of a decision taken at ``decided_at``: a measurement's check asks this of its answer.
- `derive_router_outcomes(connection: sqlite3.Connection, *, reader_exposures: Iterable[tuple[str, str]] | None, pfc_states: Mapping[str, str] | None=None, servable_items_by_lo: Mapping[str, set[str]] | None=None, retrievability_by_attempt: Mapping[str, float] | None=None, held_attempt_ids: frozenset[str] | set[str]=frozenset(), outcome_version: str=OUTCOME_VERSION) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1195) — One outcome row per logged decision, from the ledgers alone (read-only).
- `rebuild_router_outcomes(connection: sqlite3.Connection, *, reader_exposures: Iterable[tuple[str, str]] | None, pfc_states: Mapping[str, str] | None=None, servable_items_by_lo: Mapping[str, set[str]] | None=None, retrievability_by_attempt: Mapping[str, float] | None=None, held_attempt_ids: frozenset[str] | set[str]=frozenset(), outcome_version: str=OUTCOME_VERSION) -> int` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1399) — Replace the derived cache; the caller owns the transaction.

### Module constants

- `OUTCOME_VERSION` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 152)
- `BINDING_PRESENTATION` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 155)
- `BINDING_CANDIDATE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 156)
- `BINDING_SESSION_RULE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 157)
- `S_ALPHA` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 160)
- `ARM_READING` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 164)
- `ACTIONLESS_ARMS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 165)
- `INDEPENDENT_ATTEMPT_TYPES` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 168)
- `_DELAY_REASONS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 173)
- `_ATTEMPT_COLUMNS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 175)
- `_OPTIONAL_ATTEMPT_COLUMNS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 182)
- `R_COLD_RULE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 185)
- `R_COLD_RULE_V3` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 187)
- `COLDNESS_CANDIDATE_CAP` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 189)
- `COVARIATE_NAMES` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 191)
- `_INTERRUPT_KIND` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 559)
- `_SUGGESTION_KIND` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 561)
- `R_COLD_ITT_RULE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 563)

### Explicit exports

`__all__` declares:

- `answer_completion`
- `COLDNESS_CANDIDATE_CAP`
- `COVARIATE_NAMES`
- `INDEPENDENT_ATTEMPT_TYPES`
- `R_COLD_ITT_RULE`
- `R_COLD_RULE`
- `OUTCOME_VERSION`
- `OUTCOME_VERSION_V3`
- `R_COLD_RULE_V3`
- `S_ALPHA`
- `derive_router_outcomes`
- `fold_measurement`
- `outcome_version_for`
- `rebuild_router_outcomes`
- `servable_items_by_learning_object`

## Internal implementation anchors

- `_facet_ids(raw: Any) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 205) — Facet ids from an ``evidence_facets_json`` / ``facets_json`` value.
- `_table_present(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../src/learnloop/router/outcomes.py), line 231)
- `_seconds(later: str, earlier: str) -> int | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 237)
- `_contract_row(attempt: Mapping[str, Any], *, elapsed_seconds: int | None, source_session_id: str | None, pfc_states: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 244) — The outcome contract's view of one attempt.
- `_exclusions(attempt: Mapping[str, Any], *, elapsed_seconds: int | None, source_session_id: str | None, pfc_states: Mapping[str, str]) -> list[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 268)
- `_reading_marks(reader_exposures: Iterable[tuple[str, str]]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 286) — ``(LO, time)`` of the Reader exposures, the time at the attempts' own precision (a receipt keeps microseconds, an attempt seconds: the ledger compares them as strings).
- `class _Ledger` ([source](../../../../../../src/learnloop/router/outcomes.py), line 301) — The attempt, reveal and exposure ledgers, indexed once for every decision.
- `_decision_block(decision: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 566) — The block of a ``plan_block`` or ``plan_interrupt`` decision (its receipt key names it).
- `_presentation_is_the_decisions(decision: Mapping[str, Any], presentation: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/router/outcomes.py), line 579) — Whether ``presentation`` (of the decision's block) served this decision's action.
- `_follow_binding(decision: Mapping[str, Any], bindings: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 593) — FG1: a decision comes before its item, and its row stays immutable, so its action is what the appended binding names.
- `_action_attempt(decision: Mapping[str, Any], ledger: _Ledger, presentations: Mapping[str, list[dict[str, Any]]] | None=None) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 603) — The action attempt and how it was bound (module docstring, rules 1-3).
- `_r_next(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], *, until_position: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 659) — The first fresh, unassisted, independent attempt after the action, at or before ``until_position`` (the R_cold attempt) when one is given.
- `_completion(row: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], *, source_session_id: str | None, not_before: str | None=None) -> DC.Completion` ([source](../../../../../../src/learnloop/router/outcomes.py), line 699) — Version 3: the shared definition over one attempt's frozen facts.
- `_completion_reasons(completion: DC.Completion) -> list[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 735) — A non-outcome's reasons under the skip counts (``pre_exposed`` and the rest stay apart).
- `_r_cold_v3(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 743) — The next delayed presentation on the action's LO under the shared definition (module docstring).
- `_r_cold(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 769)
- `_not_applicable(decision: Mapping[str, Any], status: str, observed_through: str | None, *, pending: bool, version: str=OUTCOME_VERSION) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 812)
- `_r_cold_rule(version: str) -> str` ([source](../../../../../../src/learnloop/router/outcomes.py), line 846)
- `_covariate_columns(prefix: str, covariates: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 850)
- `_coldness_candidates(action: Mapping[str, Any], considered: list[tuple[dict[str, Any], list[str]]], ledger: _Ledger, *, r_next_id: str | None, r_cold_id: str | None) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 854) — Every later attempt the R_cold rule considered, with its covariates.
- `_suggestion_responses(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 886) — Each suggestion decision's one response: its kind, the candidate taken and its LOs.
- `_r_cold_itt(learning_object_id: str, start: str, ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 904) — The first eligible cold retrieval on the LO at least a day after ``start`` and after its last exposure.
- `_suggestion_scope(detail: Mapping[str, Any], target: str, start: str, ledger: _Ledger, pfc_states: Mapping[str, str], taken: Mapping[str, Any] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 940) — R_cold on every LO of the decision's predeclared scope (codex review F4): the target and the candidates the card offered (or would have offered) beside it, fixed at the draw in both arms, so an accepted alternative's delayed check reaches its decision.
- `_suggestion_outcome(decision: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], responses: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 971) — A lesson suggestion's intention-to-treat outcome (module docstring).
- `_completion_detail(ledger: _Ledger, r_cold: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1026) — Version 3's fields on an outcome's detail (absent below it, whose detail stays byte-identical).
- `_event_instant(event: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1034)
- `_replacement_of(event: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1042) — The check an early answer's event arranged in its place (``daily_plan.measurement.settle``).
- `_objective_record(decision: Mapping[str, Any], objective: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1093) — A frozen objective's ITT record: its R_cold, its scope's, its measurement's states.
- `_objective_outcome(decision: Mapping[str, Any], objective: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], events: Sequence[Mapping[str, Any]], reading_started: frozenset[str] | set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1120) — A reading, wait or stop arm's outcome: the lesson suggestion's adapter over a frozen objective.
- `_with_objective_itt(row: dict[str, Any], decision: Mapping[str, Any], objective: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1155) — A practice arm keeps its own outcome and records the same objective, so every arm compares.
- `_reading_started(connection: sqlite3.Connection) -> set[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1171)
- `_ended_sessions(connection: sqlite3.Connection, session_ids: set[str]) -> set[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 1178)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`; statically calls `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `answer_completion`; statically calls `answer_completion`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`; statically calls `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `derive_router_outcomes`, `fold_measurement`, `outcome_version_for`, `servable_items_by_learning_object`; statically calls `derive_router_outcomes`, `fold_measurement`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]] — imports `OUTCOME_VERSION_V3`, `_Ledger`, `_completion`, `_decision_block`, `_table_present`; statically calls `_Ledger`, `_completion`, `_decision_block`, `_table_present`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `outcome_version_for`, `rebuild_router_outcomes`, `servable_items_by_learning_object`; statically calls `outcome_version_for`, `rebuild_router_outcomes`, `servable_items_by_learning_object`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `OUTCOME_VERSION_V3`, `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; calls `measurement_events`, `objectives`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `all_bindings`; calls `all_bindings`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `presentations_for_blocks`; calls `presentations_for_blocks`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `replace_router_outcomes`; calls `replace_router_outcomes`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `module`; calls `Presentation`, `classify`, `help_question`, `other_exclusions`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `RETENTION_MIN_DELAY_SECONDS`, `retention_exclusions`; calls `retention_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]], [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a2_measurement.py](../../../../../../tests/test_data_capture_a2_measurement.py) — direct import
  - `test_a_reading_arm_gets_a_real_outcome_instead_of_not_applicable`
  - `test_a_wait_arm_gets_a_real_outcome_and_a_measurement`
  - `test_the_routers_copy_of_the_actionless_arms_is_the_measurements`
- [tests/test_data_capture_a4_delayed_completion.py](../../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
  - `test_requested_help_on_a_delayed_unexposed_presentation_is_r_cold_zero`
  - `test_the_lesson_suggestion_adapter_reads_the_same_definition`
  - `test_v2_derivation_is_untouched_by_default`
  - `test_warm_performance_gets_no_cold_label_a_reading_is_an_exposure`
- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f1_a_section_read_does_not_change_the_predecessors_outcome`
  - `test_f2_a_warm_answer_consumes_the_check_but_keeps_the_measurement_duty`
  - `test_f2_the_replacement_answered_cold_completes_the_measurement`
  - `test_f6_every_arm_is_reported_on_its_frozen_objective_and_action_outcomes_apart`
  - `test_f6_the_text_report_names_both`
  - `test_f7_a_later_offer_restores_it_and_an_answer_is_terminal`
  - `test_f7_a_replaced_check_reads_unavailable_not_due`
  - `test_f7_times_of_different_precision_fold_in_time_order`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f11_an_answer_on_another_objective_never_records_answered_and_the_duty_stays`
  - `test_f1_a_rebuild_with_no_decisions_needs_no_read`
  - `test_f1_for_version_reads_only_at_version_3`
  - `test_f1_version_3_refuses_to_derive_without_the_read`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_released_hold_is_an_ordinary_outcome_again`
- [tests/test_reader_rw3a_landing.py](../../../../../../tests/test_reader_rw3a_landing.py) — direct import
  - `test_the_answer_to_a_check_binds_by_the_picks_presentation`
- [tests/test_router_coldness_covariates.py](../../../../../../tests/test_router_coldness_covariates.py) — direct import
  - `test_an_unobserved_outcome_has_no_covariates`
  - `test_each_outcome_records_its_coldness_covariates`
- [tests/test_router_g4_restraint.py](../../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation`
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_an_observed_cold_retrieval_finalizes_s_and_closes_r_next`
  - `test_r_cold_needs_a_day_since_the_last_exposure_including_reveals`
  - `test_r_next_is_not_applicable_on_a_single_item_learning_object_and_r_cold_finalizes_s`
  - `test_the_replayer_applies_the_vaults_servable_items`
- [tests/test_router_presentations.py](../../../../../../tests/test_router_presentations.py) — direct import
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_replay_never_asks_a_model_and_is_deterministic`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_replay_never_needs_a_vector`
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_not_now_on_a_pending_card_releases_the_reservation`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_outcome_is_r_cold_on_the_drawn_lo_shown_or_not`

## Modification guidance

- Make changes here when the responsibility remains outcomes within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
