---
title: "learnloop.remote.views"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/views.py"
source_paths:
  - "src/learnloop/remote/views.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.remote.views module"
  - "src/learnloop/remote/views.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.views`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.views` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: Read-only views for remote frontends: status, today, progress, library (spec_mcp_frontend_c1 §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py) |
| Source lines | 391 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `ai_readiness(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 58) — Per serving route: which profile it uses and whether it can run.
- `status(runtime: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 100) — The vault, its algorithm version, AI readiness and waiting work.
- `today(runtime: Any, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 141) — Today's plan as the app built it: blocks, minutes and why.
- `progress(runtime: Any, *, goal_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 240) — Per goal and topic: demonstrated vs assumed, certification, retention risks.
- `library(runtime: Any, *, query: str | None=None, limit: int=30) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 330) — Sources and their state (titles searchable).

### Module constants

- `READINESS_TASKS` ([src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py), line 37)
- `_KEY_TYPES` ([src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py), line 39)
- `PHASE` ([src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py), line 41)
- `FRONTEND_NOTE` ([src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py), line 42)

### Explicit exports

`__all__` declares:

- `READINESS_TASKS`
- `ai_readiness`
- `library`
- `progress`
- `status`
- `today`

## Internal implementation anchors

- `_now(clock: Clock | None) -> datetime` ([source](../../../../../../src/learnloop/remote/views.py), line 46)
- `_alias_key(runtime: Any) -> bytes | None` ([source](../../../../../../src/learnloop/remote/views.py), line 50)
- `_plan_projection(plan: dict[str, Any], record: Any, guard: TextGuard) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 189) — The stored plan without any question text: topics, minutes, why.
- `_due_now(vault: Any, repository: Any, now: datetime) -> int` ([source](../../../../../../src/learnloop/remote/views.py), line 223)
- `_progress(vault: Any, repository: Any, guard: TextGuard, *, goal_id: str | None, clock: Clock | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/views.py), line 253)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `learner_title`, `source_kind_noun`, `source_status_line`; calls `learner_title`, `source_kind_noun`, `source_status_line`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `load_records`, `plan_active`; calls `PlanEnv`, `load_records`, `plan_active`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `HEADLINE_CLASSES`, `classify_learning_objects`, `today_headline`; calls `classify_learning_objects`, `today_headline`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `plan_view`; calls `plan_view`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`, `discover_migrations`; calls `applied_versions`, `discover_migrations`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`; calls `goal_report`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `HELD_BACK`, `TextGuard`, `protection_issues`, `retention_risks`; calls `TextGuard`, `protection_issues`, `retention_risks`
- [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]] — imports `NotFound`; calls `NotFound`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `os`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_attach_and_every_view_write_nothing`
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_today_shows_the_stored_plan_and_writes_nothing`

## Modification guidance

- Make changes here when the responsibility remains views within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/views.py](../../../../../../src/learnloop/remote/views.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
