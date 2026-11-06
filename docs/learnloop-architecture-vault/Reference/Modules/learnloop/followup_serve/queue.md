---
title: "learnloop.followup_serve.queue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/queue.py"
source_paths:
  - "src/learnloop/followup_serve/queue.py"
source_commit: "dc5302d98cfcd397c2bb3678cdb2bf12f232164a"
source_commit_timestamp: "2026-11-06T04:43:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_serve"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.followup_serve.queue module"
  - "src/learnloop/followup_serve/queue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.queue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.queue` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: FG1's durable generation queue: the writes domain packages may make (a leaf).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/queue.py](../../../../../../src/learnloop/followup_serve/queue.py) |
| Source lines | 86 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dc5302d98cfcd397c2bb3678cdb2bf12f232164a` |
| Commit timestamp | `2026-11-06T04:43:14-05:00` |

## Public API

- `enqueue_workflow(repository: Repository, workflow_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 14) — Queue the workflow's one job (the dedupe key is its identity).
- `enqueue_need(repository: Repository, need_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 24) — A recorded practice-lane need fills in the background, deduplicated (§4).
- `enqueue_factor(repository: Repository, factor_id: str, *, workflow_id: str | None, not_before: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 33) — A failed probe lane's need stays open for background generation, deduplicated by factor (§6.2).
- `enqueue_entry(repository: Repository, episode_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 44) — An episode entered: its generation is queued, so opening a vault can't stall or burst (§4.3).
- `lesson_dedupe_key(lesson_id: str, node_id: str) -> str` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 54) — Teacher TE2: one generation per (lesson, node); the key names the lesson (no column of its own).
- `enqueue_lesson(repository: Repository, lesson_id: str, node_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 60) — A lesson's ``serve_probe`` (teacher TE2, spec_teacher_v1 §11.3): its one generation job, deduplicated on (lesson, node); the worker writes it through FG1's authoring operation (``followup_run.lesson_probe``).
- `skip_lesson_job(repository: Repository, lesson_id: str, node_id: str, *, reason: str, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 70) — A lesson probe no one will answer ("Teach it anyway", the lesson's close): its queued job never runs.
- `pending_jobs(repository: Repository) -> int` ([source](../../../../../../src/learnloop/followup_serve/queue.py), line 80)

### Explicit exports

`__all__` declares:

- `enqueue_entry`
- `enqueue_factor`
- `enqueue_lesson`
- `enqueue_need`
- `enqueue_workflow`
- `lesson_dedupe_key`
- `pending_jobs`
- `skip_lesson_job`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `enqueue_workflow`; statically calls `enqueue_workflow`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `enqueue_entry`; statically calls `enqueue_entry`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `enqueue_entry`; statically calls `enqueue_entry`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `enqueue_factor`, `enqueue_workflow`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `enqueue_need`; statically calls `enqueue_need`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `enqueue_workflow`; statically calls `enqueue_workflow`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; statically calls `enqueue_lesson`, `skip_lesson_job`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `pending_jobs`; statically calls `pending_jobs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `enqueue_generation_job`, `present`, `runnable_generation_jobs`, `skip_generation_job`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]], [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_failed_lanes_need_is_deduplicated_and_cancelled_when_the_factor_closes`
  - `test_a_mint_under_fg1_is_model_written_single_use_and_needs_no_review`
  - `test_a_recorded_need_fills_textbook_first_without_a_click`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_f20_a_need_job_has_the_same_limit`
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_reserved_question_match_gives_no_probe`

## Modification guidance

- Make changes here when the responsibility remains queue within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/queue.py](../../../../../../src/learnloop/followup_serve/queue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
