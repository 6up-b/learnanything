---
title: "learnloop.followup_run.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/jobs.py"
source_paths:
  - "src/learnloop/followup_run/jobs.py"
source_commit: "c11b6179c76d77eb4ef639d03f4fb112e12a75a7"
source_commit_timestamp: "2026-11-03T22:03:31-05:00"
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
| Source lines | 370 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c11b6179c76d77eb4ef639d03f4fb112e12a75a7` |
| Commit timestamp | `2026-11-03T22:03:31-05:00` |

## Public API

- `class GenerationDeferred(RuntimeError)` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 42) — The route is not ready: nothing was spent, and the job may run again.
- `class JobOutcome` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 47)
- `process_next_job(vault: Any, repository: Repository, *, owner: str, clients: Any=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> JobOutcome | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 60) — Lease and run the next runnable job; None when none is.
- `fail_workflow(vault: Any, repository: Repository, workflow_id: str, *, reason: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 119) — §6.2: nothing passed.
- `reloaded(vault: Any) -> Any` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 348) — The vault with the item just written; its config stays the run's.

### Module constants

- `LOG` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 25)
- `RECEIPT_OWNER` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 28)
- `LEASE_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 31)
- `MAX_GENERATION_ATTEMPTS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 34)
- `RETRY_BACKOFF_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 37)
- `NEED_RETRY_DELAY_SECONDS` ([src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py), line 39)

### Explicit exports

`__all__` declares:

- `GenerationDeferred`
- `JobOutcome`
- `LEASE_SECONDS`
- `MAX_GENERATION_ATTEMPTS`
- `NEED_RETRY_DELAY_SECONDS`
- `RETRY_BACKOFF_SECONDS`
- `fail_workflow`
- `process_next_job`
- `reloaded`

## Internal implementation anchors

- `_iso_after(clock: Clock | None, seconds: float) -> str` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 55)
- `_finish(repository: Repository, job: Mapping[str, Any], state: str, error: str | None, clock: Clock | None, *, not_before: str | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 97)
- `_retry_or_fail(vault: Any, repository: Repository, job: Mapping[str, Any], outcome: JobOutcome, error: str, clock: Clock | None) -> JobOutcome` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 105)
- `_run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 132)
- `_run_entry(vault: Any, repository: Repository, episode_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 151) — §4.3: the worker chooses the contract.
- `_causal_factor_of(episode: Any) -> str | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 175)
- `_author_for_factor(vault: Any, repository: Repository, *, factor_id: str, learning_object_id: str, attempt_id: str, episode_id: str | None, clients: Any, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 181) — §4.1's contract with no workflow: an active candidate on the factor, unreserved.
- `_run_factor_need(vault: Any, repository: Repository, factor_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 202) — §6.2: a failed probe lane's need, deduplicated by factor and cancelled if it closed.
- `_run_need(vault: Any, repository: Repository, need_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 214) — §4: a recorded need fills in the background, S2b's order kept: an existing item was the chooser's, then a textbook exercise, then a generated practice item.
- `_run_workflow(vault: Any, repository: Repository, workflow_id: str, *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 247)
- `_author_client(vault: Any, clients: Any) -> Any` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 273) — The test seam's client, else the route's; never the Decider.
- `_run_probe_lane(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 282) — §5: the decision first and the item after it.
- `_retire(repository: Repository, item_id: str | None, *, reason: str, workflow_id: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/jobs.py), line 358)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `process_next_job`; statically calls `process_next_job`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `generate_diagnostic_practice_proposal`; calls `generate_diagnostic_practice_proposal`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `default_runtime`; calls `default_runtime`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `finish_generation_job`, `lease_next_generation_job`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `causal_origin_factor`; calls `causal_origin_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `mint_single_use_probe_surface`; calls `mint_single_use_probe_surface`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DONE`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `module`; calls `author_probe`, `commission_and_pin`, `commission_only`, `persist_item`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `resolve_author_client`; calls `resolve_author_client`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `concrete_rivals`, `select_lane`, `settle_practice_lane`; calls `concrete_rivals`, `select_lane`, `settle_practice_lane`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; calls `bind_item`, `decide`, `record_decision`, `record_outcome`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `retire`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `module`; calls `enqueue_factor`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `get`, `move`, `release_feedback`, `set_fields`, `superseded`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `fulfil_need_from_sources`, `pending_causal_decision`; calls `fulfil_need_from_sources`, `pending_causal_decision`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains jobs within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/jobs.py](../../../../../../src/learnloop/followup_run/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
