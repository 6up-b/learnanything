---
title: "learnloop.followup_serve.identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/identity.py"
source_paths:
  - "src/learnloop/followup_serve/identity.py"
source_commit: "workspace/uncommitted @ HEAD 3a57cdc863da69ad6a23e47a006c6932863322ee"
source_commit_timestamp: "2026-11-04T01:43:28-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_serve"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_serve.identity module"
  - "src/learnloop/followup_serve/identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.identity` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: The one durable single-use identity of a generated probe (spec §4.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py) |
| Source lines | 294 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 3a57cdc863da69ad6a23e47a006c6932863322ee` |
| Commit timestamp | `2026-11-04T01:43:28-05:00` |

## Public API

- `item_revision(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 45) — The content revision a claim is keyed to: the question as authored.
- `register(repository: Repository, *, practice_item_id: str, revision: str, source: str, workflow_id: str | None=None, probe_episode_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 59) — Give an item the identity, once, committed before its file exists (no crash publishes a question without it).
- `is_generated_probe(repository: Repository, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 79)
- `generated_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 86)
- `closed_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 91) — Every generated probe with a burn or a retirement.
- `retired_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 98)
- `class Claim` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 109) — A first-serve claim's verdict.
- `claim_serve(repository: Repository, practice_item_id: str, *, surface: str, presentation_id: str | None, workflow_id: str | None=None, reason: str='first_serve', clock: Clock | None=None) -> Claim` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 119) — The atomic first-serve burn; an item with no identity needs no claim.
- `retire(repository: Repository, practice_item_id: str, *, reason: str, workflow_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 168) — Close a generated probe for any further administration, and keep it for history.
- `withdraw(repository: Repository, practice_item_id: str, *, reason: str, workflow_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 196) — Everything that could still serve a generated probe, closed in one commit: it retires, its open presentations end, and its candidate stops being one, since serving accepts any ``active`` candidate and a live one blocks its factor's next question (``duplicate_instrument_class``).
- `retire_unbound(repository: Repository, workflow_id: str, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 225) — What an interrupted run of this workflow published and never bound is withdrawn, unused, before the retry writes its own question.
- `door_refusal(repository: Repository, practice_item_id: str, *, workflow_id: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 238) — Why a door may not open this generated probe now, or None.
- `door_sets(repository: Repository) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 260) — (closed, reserved): what every selector leaves out, read once.
- `exclude_ids(repository: Repository, item_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 277) — The ones in ``item_ids`` that carry the identity.
- `replay_inactive_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 284) — Rebuild replay: an item the ledger closed stays closed, attempt or no attempt.

### Module constants

- `GENERATED_PROBE_CLOSED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 35)
- `GENERATED_PROBE_RESERVED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 36)
- `SERVED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 38)
- `RETIRED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 39)
- `MACHINE_REVIEWER` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 42)

### Explicit exports

`__all__` declares:

- `Claim`
- `GENERATED_PROBE_CLOSED`
- `GENERATED_PROBE_RESERVED`
- `MACHINE_REVIEWER`
- `RETIRED`
- `SERVED`
- `claim_serve`
- `closed_probe_ids`
- `door_refusal`
- `door_sets`
- `exclude_ids`
- `generated_probe_ids`
- `is_generated_probe`
- `item_revision`
- `register`
- `replay_inactive_ids`
- `retire`
- `retire_unbound`
- `retired_probe_ids`
- `withdraw`

## Internal implementation anchors

- `_present(connection: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `closed_probe_ids`, `generated_probe_ids`, `retired_probe_ids`; statically calls `closed_probe_ids`, `generated_probe_ids`, `retired_probe_ids`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `door_sets`; statically calls `door_sets`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `item_revision`, `register`; statically calls `item_revision`, `register`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `is_generated_probe`; statically calls `is_generated_probe`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `module`; statically calls `item_revision`, `register`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `closed_probe_ids`, `is_generated_probe`, `withdraw`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; statically calls `is_generated_probe`, `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `door_sets`, `generated_probe_ids`; statically calls `door_sets`, `generated_probe_ids`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `closed_probe_ids`; statically calls `closed_probe_ids`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `closed_probe_ids`; statically calls `closed_probe_ids`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `module`; statically calls `claim_serve`, `closed_probe_ids`, `door_refusal`, `is_generated_probe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `administration_ended`, `burns_for_item`, `closed_generated_probe_ids`, `generated_probe`, `generated_probe_ids`, `insert_burn`, `insert_generated_probe`, `live_candidates_of_item`, `present`, `unclosed_probes_of_workflow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]], [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]], [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_failed_workflow_withdraws_what_its_last_run_left`
  - `test_f10_an_interrupted_withdrawal_is_redone_whole`
  - `test_f10_recovery_redoes_a_withdrawal_a_crash_cut_at_the_job_boundary`
  - `test_f3_a_crash_after_the_file_leaves_an_identified_parked_item`
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
  - `test_f3_the_mint_and_the_batch_write_the_identity_before_the_file`
  - `test_f3_the_retry_retires_the_orphan_and_serves_its_own_question`
  - `test_f4_a_burn_before_any_presentation_ends_when_one_has_ended`
  - `test_f4_a_workflowless_probe_skipped_is_never_served_again`
  - `test_f4_skipping_one_the_plan_listed_abandons_it_unserved_too`
  - `test_f4_the_burn_binds_to_the_open_presentation_and_ends_with_it`
  - `test_f4_the_claim_has_no_wildcard_for_a_missing_presentation`
  - `test_f5_a_cause_written_from_exam_work_reaches_neither_request`
  - `test_f7_a_prepared_probe_closes_with_the_switch`
  - `test_f7_a_standing_plan_doesnt_strand_next_on_a_switched_off_probe`
  - `test_f7_next_through_the_sidecar_after_the_switch`
  - `test_f7_rereview_a_crash_in_cleanup_leaves_the_workflow_open_for_recovery`
  - `test_f7_rereview_a_startup_crash_doesnt_leave_a_standing_plan_holding_the_item`
  - `test_f7_rereview_skipping_a_workflows_probe_through_the_sidecar_closes_it`
  - `test_f9_a_refusal_that_arrives_during_authoring_stops_the_offer`
  - `test_f9_a_refused_retry_doesnt_leave_what_the_crash_pinned`
  - `test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_late_generator_adds_nothing_after_a_skip`
  - `test_a_mint_under_fg1_is_model_written_single_use_and_needs_no_review`
  - `test_a_miss_with_two_rivals_generates_one_pinned_probe`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_probe_whose_hypotheses_closed_first_is_retired_unused`
  - `test_a_reserved_probe_refuses_every_door_until_its_workflow_is_ready`
  - `test_a_wait_releases_now_labels_the_probe_exposed_and_its_answer_cant_close_the_factor`
  - `test_continue_without_it_retires_the_probe_and_next_goes_on`
  - `test_no_intervention_generates_nothing_and_releases_what_was_held`
  - `test_the_whole_journey_and_never_again`
  - `test_with_no_plan_a_ready_probe_heads_todays_queue`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_closed_factor_retires_a_waiting_probe_at_the_boundary`
- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — direct import
  - `test_an_exam_never_reserves_one`
  - `test_an_item_with_no_identity_needs_no_claim`
  - `test_remint_refuses_the_identity`
  - `test_reserved_until_served_then_closed_for_every_selector`
  - `test_retired_while_unused_stays_retired_after_sync_and_rebuild`
  - `test_the_first_serve_is_one_atomic_claim`
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_generated_probe_attempt_opens_no_workflow`

## Modification guidance

- Make changes here when the responsibility remains identity within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
