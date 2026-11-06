---
title: "learnloop.followup_run.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/jobs.py"
source_paths:
  - "src/learnloop/followup_run/jobs.py"
source_commit: "dc5302d98cfcd397c2bb3678cdb2bf12f232164a"
source_commit_timestamp: "2026-11-06T04:43:14-05:00"
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
  - "learnloop.followup_run.jobs module"
  - "src/learnloop/followup_run/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.jobs` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: The follow-up generation worker (spec §5 item 1, §8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py) |
| Source lines | 496 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dc5302d98cfcd397c2bb3678cdb2bf12f232164a` |
| Commit timestamp | `2026-11-06T04:43:14-05:00` |

## Public API

- `class GenerationDeferred(RuntimeError)` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 47) — The route is not ready: nothing was spent, and the job may run again.
- `class QuestionEcho(RuntimeError)` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 51) — R10: a draft reproduced a reserved question and the job has its one retry left.
- `class JobOutcome` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 57)
- `process_next_job(vault: Any, repository: Repository, *, owner: str, clients: Any=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> JobOutcome | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 70) — Lease and run the next runnable job; None when none is.
- `fail_workflow(vault: Any, repository: Repository, workflow_id: str, *, reason: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 152) — §6.2: nothing passed.
- `recover_workflow(vault: Any, repository: Repository, row: Mapping[str, Any], *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 170) — §6.2's "Next never strands": a pending workflow whose diagnosis ended and whose job a crash lost gets that job; one whose job ended with the workflow still pending fails, with its failure line.
- `recover_pending_workflows(vault: Any, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 194) — At startup: what a previous process committed and never handed off.
- `reloaded(vault: Any) -> Any` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 477) — The vault with the item just written; its config stays the run's.

### Module constants

- `LOG` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 27)
- `RECEIPT_OWNER` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 31)
- `LEASE_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 34)
- `MAX_GENERATION_ATTEMPTS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 37)
- `RETRY_BACKOFF_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 40)
- `NEED_RETRY_DELAY_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 42)
- `ATTEMPTS_EXHAUSTED` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 44)

### Explicit exports

`__all__` declares:

- `ATTEMPTS_EXHAUSTED`
- `GenerationDeferred`
- `JobOutcome`
- `LEASE_SECONDS`
- `MAX_GENERATION_ATTEMPTS`
- `NEED_RETRY_DELAY_SECONDS`
- `RETRY_BACKOFF_SECONDS`
- `fail_workflow`
- `process_next_job`
- `recover_pending_workflows`
- `recover_workflow`
- `reloaded`

## Internal implementation anchors

- `_iso_after(clock: Clock | None, seconds: float) -> str` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 65)
- `_finish(repository: Repository, job: Mapping[str, Any], state: str, error: str | None, clock: Clock | None, *, not_before: str | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 125)
- `_retry_or_fail(vault: Any, repository: Repository, job: Mapping[str, Any], outcome: JobOutcome, error: str, clock: Clock | None) -> JobOutcome` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 133)
- `_run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 204)
- `_run_entry(vault: Any, repository: Repository, episode_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 229) — §4.3: the worker chooses the contract.
- `_causal_factor_of(episode: Any) -> str | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 253)
- `_author_for_factor(vault: Any, repository: Repository, *, factor_id: str, learning_object_id: str, attempt_id: str, episode_id: str | None, clients: Any, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 259) — §4.1's contract with no workflow: an active candidate on the factor, unreserved.
- `_run_factor_need(vault: Any, repository: Repository, factor_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 280) — §6.2: a failed probe lane's need, deduplicated by factor and cancelled if it closed.
- `_run_need(vault: Any, repository: Repository, need_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 292) — §4: a recorded need fills in the background, S2b's order kept: an existing item was the chooser's, then a textbook exercise, then a generated practice item.
- `_run_workflow(vault: Any, repository: Repository, workflow_id: str, *, clients: Any, clock: Clock | None, attempt: int=MAX_GENERATION_ATTEMPTS) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 325)
- `_author_client(vault: Any, clients: Any) -> Any` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 365) — The test seam's client, else the route's; never the Decider.
- `_run_probe_lane(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any, clock: Clock | None, attempt: int=MAX_GENERATION_ATTEMPTS) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 374) — §5: the decision first and the item after it.
- `_withdraw(repository: Repository, item_id: str | None, *, reason: str, workflow_id: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 487)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `GenerationDeferred`, `_author_client`; statically calls `GenerationDeferred`, `_author_client`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `recover_workflow`; statically calls `recover_workflow`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `recover_pending_workflows`; statically calls `recover_pending_workflows`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `process_next_job`; statically calls `process_next_job`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `generate_diagnostic_practice_proposal`; calls `generate_diagnostic_practice_proposal`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `FOLLOWUP_GENERATION_OWNER`, `default_runtime`; calls `default_runtime`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `finish_generation_job`, `generation_job`, `lease_next_generation_job`, `open_workflows`, `present`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `causal_origin_factor`; calls `causal_origin_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `mint_single_use_probe_surface`; calls `mint_single_use_probe_surface`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DONE`, `PENDING`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `module`; calls `OfferRefused`, `author_probe`, `commission_and_pin`, `commission_only`, `persist_item`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `QUESTION_MATCHES_RESERVED`, `RESERVED_MATCHES`, `module`, `resolve_author_client`; calls `causes_match_reserved`, `resolve_author_client`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `concrete_rivals`, `open_rival_factor`, `select_lane`, `settle_practice_lane`; calls `concrete_rivals`, `open_rival_factor`, `select_lane`, `settle_practice_lane`
- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `module`; calls `enabled`, `failure_reason`, `refuse`, `run`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; calls `append_outcome`, `bind_item`, `decide_once`, `hard_refusal`, `record_outcome`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `module`; calls `enqueue_factor`, `enqueue_workflow`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `close_probe`, `finish`, `get`, `move`, `note`, `noted`, `release_feedback`, `set_fields`, `superseded`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `fulfil_need_from_sources`, `pending_causal_decision`; calls `fulfil_need_from_sources`, `pending_causal_decision`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]], [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_failed_workflow_withdraws_what_its_last_run_left`
  - `test_f10_recovery_redoes_a_withdrawal_a_crash_cut_at_the_job_boundary`
  - `test_f1_a_failed_generation_keeps_its_reservation`
  - `test_f1_an_in_flight_generation_reserves_against_the_next`
  - `test_f1_generation_receipts_are_in_the_daily_total`
  - `test_f1_generation_spend_refuses_the_routers_own_next_request`
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
  - `test_f6_startup_recovery_needs_no_click`
  - `test_f7_verify_every_exit_closes_what_an_interrupted_run_prepared`
  - `test_f8_a_crash_after_the_decision_keeps_it_through_the_lease_recovery`
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_f20_a_crash_on_the_retry_after_a_match_makes_no_third_call`
  - `test_f20_a_need_job_has_the_same_limit`
  - `test_f20_a_transport_failure_then_a_crash_makes_no_third_call`
  - `test_f20_an_exit_that_spends_nothing_still_takes_its_own_way_out`
  - `test_f20_what_a_crashed_run_pinned_closes_with_the_exhausted_job`
  - `test_r10_the_retry_is_the_workflows_one_so_no_third_call`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains jobs within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
