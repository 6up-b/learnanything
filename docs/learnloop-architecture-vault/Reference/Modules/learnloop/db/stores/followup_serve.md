---
title: "learnloop.db.stores.followup_serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/followup_serve.py"
source_paths:
  - "src/learnloop/db/stores/followup_serve.py"
source_commit: "867897f2287300fc9267644fd4cb983021f5e273"
source_commit_timestamp: "2026-11-08T21:16:02-05:00"
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
  - "learnloop.db.stores.followup_serve module"
  - "src/learnloop/db/stores/followup_serve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.followup_serve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.followup_serve` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: FG1's records (migration 241).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py) |
| Source lines | 390 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `867897f2287300fc9267644fd4cb983021f5e273` |
| Commit timestamp | `2026-11-08T21:16:02-05:00` |

## Public API

- `present(connection: sqlite3.Connection, table: str=WORKFLOW_TABLE) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 29)
- `insert_workflow(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 45) — The workflow's row; a repeat of its attempt and revision is a no-op (retry and crash recovery reuse the identity).
- `workflow(connection: sqlite3.Connection, workflow_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 64)
- `workflow_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 68) — The attempt's newest workflow (a regrade's revision is the newest).
- `workflow_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 77)
- `any_feedback_held(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 84) — A miss's causes are still held from the learner, somewhere.
- `workflow_for_presentation(connection: sqlite3.Connection, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 92)
- `open_workflows(connection: sqlite3.Connection, *, session_id: str | None=None, states: Iterable[str]=OPEN_STATES) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 99)
- `update_workflow(connection: sqlite3.Connection, workflow_id: str, *, at: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 112)
- `move_workflow(connection: sqlite3.Connection, workflow_id: str, *, from_states: Iterable[str], to_state: str, reason: str, at: str, detail: Mapping[str, Any] | None=None, **fields: Any) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 125) — Move a workflow from one of ``from_states``: a compare-and-set, so a late generator or diagnosis cannot move a workflow a fallback or a skip has settled.
- `insert_event(connection: sqlite3.Connection, workflow_id: str, from_state: str | None, to_state: str, reason: str, detail: Mapping[str, Any], at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 149)
- `workflow_events(connection: sqlite3.Connection, workflow_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 158)
- `enqueue_generation_job(connection: sqlite3.Connection, *, kind: str, dedupe_key: str, at: str, workflow_id: str | None=None, probe_episode_id: str | None=None, need_id: str | None=None, not_before: str | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 166) — One row per deduplicated key; returns the new id, None for a repeat.
- `requeue_generation_job(connection: sqlite3.Connection, dedupe_key: str, *, at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 181) — IH2 (spec_instruct_handoff_v1 §5): the workflow's one job runs again for a new decision, with a new attempt count; the row stays one per key.
- `lease_next_generation_job(connection: sqlite3.Connection, *, owner: str, now: str, lease_expires_at: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 193) — Lease the oldest runnable job, or reclaim one whose lease lapsed.
- `finish_generation_job(connection: sqlite3.Connection, job: Mapping[str, Any], *, state: str, at: str, error: str | None=None, not_before: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 215) — Settle or requeue a leased job, fenced on its lease epoch.
- `cancel_generation_jobs(connection: sqlite3.Connection, *, workflow_id: str | None=None, probe_episode_id: str | None=None, reason: str, at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 227) — Queued work whose reason has gone (its hypotheses closed, a skip): never run.
- `skip_generation_job(connection: sqlite3.Connection, dedupe_key: str, *, reason: str, at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 248) — A queued job whose reason has gone, by its key (teacher TE2's lesson probes): never run.
- `runnable_generation_jobs(connection: sqlite3.Connection) -> int` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 257)
- `generation_job(connection: sqlite3.Connection, dedupe_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 263)
- `insert_generated_probe(connection: sqlite3.Connection, *, practice_item_id: str, item_revision: str, source: str, at: str, workflow_id: str | None=None, probe_episode_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 271)
- `generated_probe(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 281)
- `unclosed_probes_of_workflow(connection: sqlite3.Connection, workflow_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 286) — A workflow's generated probes with no burn: what an interrupted run left behind.
- `episodes_pinned_by_workflow(connection: sqlite3.Connection, workflow_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 297) — The episodes holding a presentation of this workflow's generated probes, bound or not.
- `live_candidates_of_item(connection: sqlite3.Connection, practice_item_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 308) — The item's causal probe candidates not yet rejected.
- `administration_ended(connection: sqlite3.Connection, practice_item_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 317) — Some presentation of this item was answered or ended: its one administration is over.
- `generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 326)
- `insert_burn(connection: sqlite3.Connection, *, practice_item_id: str, kind: str, item_revision: str, reason: str, at: str, surface: str | None=None, presentation_id: str | None=None, workflow_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 330) — The atomic claim: the UNIQUE (item, kind) decides the one winner.
- `burns_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 344)
- `closed_generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 352) — Every generated probe with a burn or a retirement.
- `append_binding(connection: sqlite3.Connection, *, decision_id: str, workflow_id: str, binding_kind: str, at: str, practice_item_id: str | None=None, probe_presentation_id: str | None=None, plan_presentation_id: str | None=None, outcome: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 362)
- `bindings_for_decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 375)
- `all_bindings(connection: sqlite3.Connection) -> dict[str, dict[str, dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 382) — Every decision's bindings, keyed by decision id and then kind (the outcome join's one read).

### Module constants

- `WORKFLOW_TABLE` ([src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 17)
- `TERMINAL_STATES` ([src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 19)
- `OPEN_STATES` ([src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 20)
- `WORKFLOW_FIELDS` ([src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 22)

## Internal implementation anchors

- `_row(row: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 34)
- `_rows(cursor: Iterable[Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 38)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]] — imports `module`; statically calls `any_feedback_held`, `present`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `finish_generation_job`, `generation_job`, `lease_next_generation_job`, `open_workflows`, `present`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `append_binding`, `update_workflow`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; statically calls `administration_ended`, `burns_for_item`, `closed_generated_probe_ids`, `generated_probe`, `generated_probe_ids`, `insert_burn`, `insert_generated_probe`, `live_candidates_of_item`, `present`, `unclosed_probes_of_workflow`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `module`; statically calls `enqueue_generation_job`, `present`, `requeue_generation_job`, `runnable_generation_jobs`, `skip_generation_job`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; statically calls `append_binding`, `cancel_generation_jobs`, `episodes_pinned_by_workflow`, `insert_event`, `insert_workflow`, `move_workflow`, `open_workflows`, `present`, `update_workflow`, `workflow`, `workflow_events`, `workflow_for_attempt`, `workflow_for_item`, `workflow_for_presentation`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `all_bindings`; statically calls `all_bindings`

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

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]], [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]], [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f2_another_decisions_card_is_held_too_since_cards_list_open_problems`
  - `test_f4_the_burn_binds_to_the_open_presentation_and_ends_with_it`
  - `test_f7_a_served_probe_keeps_its_burn_after_the_rollback`
  - `test_f7_rereview_continue_without_commits_its_preference_and_outcome_with_the_move`
  - `test_f7_verify_a_crash_in_the_exit_leaves_all_of_it_open_for_the_next_run`
  - `test_f7_verify_move_refuses_a_terminal_state_and_finish_refuses_any_other`
  - `test_f7_verify_no_other_writer_of_a_terminal_state`
  - `test_f8_a_transport_failure_retries_under_the_decision_it_drew`
  - `test_f8_naming_the_decision_commits_with_it`
  - `test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw`
- [tests/test_followup_generate_e2e.py](../../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_entry_enqueues_deduplicated_work_and_never_calls_a_model_inline`
- [tests/test_followup_live_shape.py](../../../../../../../tests/test_followup_live_shape.py) — direct import
- [tests/test_followup_rival_factor.py](../../../../../../../tests/test_followup_rival_factor.py) — direct import
- [tests/test_followup_router.py](../../../../../../../tests/test_followup_router.py) — direct import
  - `test_the_binding_is_appended_and_the_row_stays_as_it_was`
- [tests/test_followup_workflow.py](../../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_settled_workflow_takes_nothing_more`
- [tests/test_ih2_lessons_compete.py](../../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_lesson_win_after_a_miss_generates_nothing_and_the_offer_page_opens_from_next`
  - `test_a_probe_win_after_a_miss_generates_and_serves_as_before`
  - `test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes`
  - `test_taking_the_lesson_settles_the_followup_honestly`
  - `test_the_workflows_one_job_runs_again_for_a_new_decision`
- [tests/test_ih2_offer_ceiling_and_unseen.py](../../../../../../../tests/test_ih2_offer_ceiling_and_unseen.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
