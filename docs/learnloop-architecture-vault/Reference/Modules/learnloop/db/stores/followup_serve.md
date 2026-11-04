---
title: "learnloop.db.stores.followup_serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/followup_serve.py"
source_paths:
  - "src/learnloop/db/stores/followup_serve.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
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
| Source lines | 349 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

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
- `lease_next_generation_job(connection: sqlite3.Connection, *, owner: str, now: str, lease_expires_at: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 181) — Lease the oldest runnable job, or reclaim one whose lease lapsed.
- `finish_generation_job(connection: sqlite3.Connection, job: Mapping[str, Any], *, state: str, at: str, error: str | None=None, not_before: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 203) — Settle or requeue a leased job, fenced on its lease epoch.
- `cancel_generation_jobs(connection: sqlite3.Connection, *, workflow_id: str | None=None, probe_episode_id: str | None=None, reason: str, at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 215) — Queued work whose reason has gone (its hypotheses closed, a skip): never run.
- `runnable_generation_jobs(connection: sqlite3.Connection) -> int` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 236)
- `generation_job(connection: sqlite3.Connection, dedupe_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 242)
- `insert_generated_probe(connection: sqlite3.Connection, *, practice_item_id: str, item_revision: str, source: str, at: str, workflow_id: str | None=None, probe_episode_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 250)
- `generated_probe(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 260)
- `unclosed_probes_of_workflow(connection: sqlite3.Connection, workflow_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 265) — A workflow's generated probes with no burn: what an interrupted run left behind.
- `administration_ended(connection: sqlite3.Connection, practice_item_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 276) — Some presentation of this item was answered or ended: its one administration is over.
- `generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 285)
- `insert_burn(connection: sqlite3.Connection, *, practice_item_id: str, kind: str, item_revision: str, reason: str, at: str, surface: str | None=None, presentation_id: str | None=None, workflow_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 289) — The atomic claim: the UNIQUE (item, kind) decides the one winner.
- `burns_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 303)
- `closed_generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 311) — Every generated probe with a burn or a retirement.
- `append_binding(connection: sqlite3.Connection, *, decision_id: str, workflow_id: str, binding_kind: str, at: str, practice_item_id: str | None=None, probe_presentation_id: str | None=None, plan_presentation_id: str | None=None, outcome: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 321)
- `bindings_for_decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 334)
- `all_bindings(connection: sqlite3.Connection) -> dict[str, dict[str, dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/followup_serve.py), line 341) — Every decision's bindings, keyed by decision id and then kind (the outcome join's one read).

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
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; statically calls `administration_ended`, `burns_for_item`, `closed_generated_probe_ids`, `generated_probe`, `generated_probe_ids`, `insert_burn`, `insert_generated_probe`, `present`, `unclosed_probes_of_workflow`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `module`; statically calls `enqueue_generation_job`, `present`, `runnable_generation_jobs`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; statically calls `append_binding`, `cancel_generation_jobs`, `insert_workflow`, `move_workflow`, `open_workflows`, `present`, `update_workflow`, `workflow`, `workflow_for_attempt`, `workflow_for_item`, `workflow_for_presentation`
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
  - `test_f8_a_transport_failure_retries_under_the_decision_it_drew`
  - `test_f8_naming_the_decision_commits_with_it`
- [tests/test_followup_generate_e2e.py](../../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_entry_enqueues_deduplicated_work_and_never_calls_a_model_inline`
- [tests/test_followup_router.py](../../../../../../../tests/test_followup_router.py) — direct import
  - `test_the_binding_is_appended_and_the_row_stays_as_it_was`
- [tests/test_followup_workflow.py](../../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_settled_workflow_takes_nothing_more`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/followup_serve.py](../../../../../../../src/learnloop/db/stores/followup_serve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
