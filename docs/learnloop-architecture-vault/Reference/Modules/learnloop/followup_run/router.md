---
title: "learnloop.followup_run.router"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/router.py"
source_paths:
  - "src/learnloop/followup_run/router.py"
source_commit: "274113bb8aa49f51cead7f122b00c9eb6fbf6a53"
source_commit_timestamp: "2026-11-04T09:25:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.router module"
  - "src/learnloop/followup_run/router.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.router`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.router` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: The router's decision for one workflow, before any item exists (spec §5, §5.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `274113bb8aa49f51cead7f122b00c9eb6fbf6a53` |
| Commit timestamp | `2026-11-04T09:25:40-05:00` |

## Public API

- `class FollowupDecision` ([source](../../../../../../src/learnloop/followup_run/router.py), line 42)
  - `refused(self) -> bool` (line 60; public)
  - `no_intervention(self) -> bool` (line 64; public)
  - `wait(self) -> bool` (line 68; public)
  - `for_author(self) -> dict[str, Any]` (line 71; public)
- `hard_refusal(vault: Any, repository: Repository, row: Mapping[str, Any], *, factor_id: str) -> str | None` ([source](../../../../../../src/learnloop/followup_run/router.py), line 76) — §5: what still refuses, in the orchestrator's own terms, before anything is spent.
- `observational(repository: Repository, factor_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_run/router.py), line 104) — §5 item 5: the checks that stopped deciding on this lane, still on the record.
- `decide(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any, clock: Clock | None) -> FollowupDecision` ([source](../../../../../../src/learnloop/followup_run/router.py), line 171)
- `decide_once(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any, clock: Clock | None) -> FollowupDecision` ([source](../../../../../../src/learnloop/followup_run/router.py), line 204) — The workflow's one decision (§5 item 2): the one it already recorded, else a new one.
- `record_decision(vault: Any, repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, *, clock: Clock | None) -> FollowupDecision` ([source](../../../../../../src/learnloop/followup_run/router.py), line 228) — Log it, with its objective frozen, and name it on the workflow, in one transaction, so a crash leaves both or neither.
- `record_outcome(repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, *, outcome: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/router.py), line 292) — Generation failure, skip and abandonment are distinct outcomes (§5 item 2).
- `append_outcome(repository: Repository, decision_id: str, workflow_id: str, *, outcome: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/router.py), line 300)
- `bind_item(repository: Repository, row: Mapping[str, Any], decision: FollowupDecision, admitted: Any, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/router.py), line 306) — The appended binding: decision -> generated item and its probe presentation.
- `bind_plan_presentation(repository: Repository, row: Mapping[str, Any], *, plan_presentation_id: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/router.py), line 320) — The second presentation: the plan's own, once Next served it.

### Module constants

- `LOG` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 28)
- `ASK_NOW` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 30)
- `WAIT` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 31)
- `NO_INTERVENTION` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 32)
- `DECLINE` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 33)
- `ARM_LABELS` ([src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py), line 36)

### Explicit exports

`__all__` declares:

- `ARM_LABELS`
- `ASK_NOW`
- `DECLINE`
- `FollowupDecision`
- `NO_INTERVENTION`
- `WAIT`
- `append_outcome`
- `bind_item`
- `bind_plan_presentation`
- `decide`
- `decide_once`
- `hard_refusal`
- `observational`
- `record_decision`
- `record_outcome`

## Internal implementation anchors

- `_card_facts(vault: Any, repository: Repository, choice: Any, seen: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/followup_run/router.py), line 132)
- `_plan_context(vault: Any, repository: Repository, row: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/followup_run/router.py), line 144) — The session's standing plan and its router gate, or None (no plan, no timing decision).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `append_outcome`, `bind_item`, `decide_once`, `hard_refusal`, `record_outcome`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `WAIT`, `module`; statically calls `append_outcome`, `bind_plan_presentation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `decision_state_fields`; calls `decision_state_fields`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `get_or_create_today`, `plan_active`; calls `PlanEnv`, `get_or_create_today`, `plan_active`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; calls `freeze_followup`, `record`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `mixture_active`, `policy_for`, `router_active`; calls `mixture_active`, `policy_for`, `router_active`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `FollowupGate`; calls `FollowupGate`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `append_binding`, `update_workflow`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `causal_origin`, `episode_conflict_reason`, `learner_preference`, `pending_machine_checks_for_factor`; calls `causal_origin`, `episode_conflict_reason`, `learner_preference`, `pending_machine_checks_for_factor`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `decide_probe`, `repair_class_need_for_factor`; calls `decide_probe`, `repair_class_need_for_factor`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `set_fields`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `existing_followup_decision`, `log_followup_decision`; calls `existing_followup_decision`, `log_followup_decision`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; calls `prepare`, `record`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]], [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f8_a_crash_after_the_decision_keeps_it_through_the_lease_recovery`
  - `test_f8_a_duplicate_receipt_resolves_to_the_decision_logged`
  - `test_f8_a_no_plan_decision_is_kept_too`
  - `test_f8_a_transport_failure_retries_under_the_decision_it_drew`
  - `test_f8_naming_the_decision_commits_with_it`
  - `test_f9_a_no_plan_retry_is_refused_too`
  - `test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw`
  - `test_f9_verify_a_retry_is_refused_by_a_check_on_the_whole_learning_object`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_wait_releases_now_labels_the_probe_exposed_and_its_answer_cant_close_the_factor`
  - `test_no_intervention_generates_nothing_and_releases_what_was_held`
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
  - `test_a_queue_miss_with_a_plan_open_opens_the_probe_and_the_plan_doesnt_serve_it_again`
  - `test_a_wait_outlasting_its_plan_is_served_by_a_later_plan_with_its_answer_labelled`
  - `test_r13_next_and_placement_read_one_predicate`
  - `test_the_matrix`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_a_cause_quoting_a_reserved_question_takes_the_practice_lane`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_no_intervention_declines_it_and_leaves_no_open_factor_behind`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_hard_refusal_needs_no_model_and_spends_nothing`
  - `test_data_captures_objective_is_frozen_for_every_arm`
  - `test_decide_runs_the_gate_against_the_standing_plan`
  - `test_no_plan_asks_now_with_no_draw`
  - `test_outcome_joins_follow_the_binding`
  - `test_the_binding_is_appended_and_the_row_stays_as_it_was`
  - `test_the_decision_line_says_what_the_screen_should`
  - `test_the_decision_row_is_itemless_and_names_the_workflow`
  - `test_the_value_checks_are_on_the_record_and_decide_nothing`
  - `test_with_no_binding_a_decision_has_no_action_to_follow`

## Modification guidance

- Make changes here when the responsibility remains router within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/router.py](../../../../../../src/learnloop/followup_run/router.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
