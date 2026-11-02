---
title: "learnloop.projects.ai_runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/ai_runtime.py"
source_paths:
  - "src/learnloop/projects/ai_runtime.py"
source_commit: "12b1ea122b444bc01cf2157f39f945a1d5bf84b5"
source_commit_timestamp: "2026-10-13T02:13:17-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.projects.ai_runtime module"
  - "src/learnloop/projects/ai_runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.ai_runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.ai_runtime` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: Routes, spend admission and receipts for project model calls (spec §4, §7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py) |
| Source lines | 506 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `12b1ea122b444bc01cf2157f39f945a1d5bf84b5` |
| Commit timestamp | `2026-10-13T02:13:17-04:00` |

## Public API

- `class ProjectRoute` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 60)
  - `describe(self) -> dict[str, Any]` (line 79; public)
- `config_for_role(config: LearnLoopConfig, role: str) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 110) — The configuration a role's client is built from.
- `describe_routes(config: LearnLoopConfig) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 140) — Which provider each role would use, without building any client.
- `resolve_route(workdir: Path, config: LearnLoopConfig, role: str) -> ProjectRoute` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 165)
- `set_route_resolver(resolver: ClientResolver | None) -> None` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 189)
- `project_routes(vault_root: Path, config: LearnLoopConfig, roles: tuple[str, ...], *, hidden: Iterable[Path]=()) -> Iterator[dict[str, ProjectRoute]]` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 213) — Resolve the requested roles around an empty working directory.
- `class PlannedCall` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 243)
- `class PaidCalls` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 255) — One command's admission, accounting and receipts for model calls.
  - `__init__(self, store: ProjectStore, *, caps: SpendCaps, run_id: str, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, require_tool_isolation: bool=True) -> None` (line 258; internal)
  - `rate(self, route: ProjectRoute | dict[str, Any]) -> float | None` (line 289; public)
  - `usd(self, route: ProjectRoute | dict[str, Any], tokens: int) -> float | None` (line 295; public)
  - `plan(self, planned: list[PlannedCall], routes: dict[str, Any]) -> dict[str, Any]` (line 299; public) — Aggregate a dry-run estimate and check it against the caps.
  - `call(self, route: ProjectRoute, *, purpose: str, prompt: str, result_model: type, output_tokens: int, candidates: int=0, diff_id: str | None=None, disclosure: dict[str, Any] | None=None) -> Any` (line 345; public)
  - `summary(self) -> dict[str, Any]` (line 457; public)
- `caps_from_options(*, max_candidates: int, max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float) -> SpendCaps` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 474)

### Module constants

- `SUBSCRIPTION_PROVIDER_TYPES` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 48)
- `SUBSCRIPTION_REFERENCE_USD_PER_MILLION` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 52)
- `_UNBOUNDED_COUNT` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 53)
- `_UNBOUNDED_USD` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 54)
- `ROLE_TASK` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 56)
- `ISOLATION_KILL_SWITCH_HINT` ([src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py), line 194)

### Explicit exports

`__all__` declares:

- `ISOLATION_KILL_SWITCH_HINT`
- `PaidCalls`
- `PlannedCall`
- `ProjectRoute`
- `ROLE_TASK`
- `SUBSCRIPTION_PROVIDER_TYPES`
- `SUBSCRIPTION_REFERENCE_USD_PER_MILLION`
- `caps_from_options`
- `config_for_role`
- `describe_routes`
- `project_routes`
- `resolve_route`
- `set_route_resolver`

## Internal implementation anchors

- `_provider_type(config: LearnLoopConfig, provider_name: str) -> str | None` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 94)
- `_config_for_workdir(config: LearnLoopConfig, vault_root: Path) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 99) — Pin relative Codex checkout paths to the vault before moving the cwd.
- `_with_isolation(route: ProjectRoute, isolation: ToolIsolation, *, required: bool) -> ProjectRoute` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 197) — Attach the isolation a route's calls run under, or mark the route not ready.
- `_physical_start(event: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/projects/ai_runtime.py), line 250)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `PaidCalls`, `PlannedCall`, `caps_from_options`, `describe_routes`, `project_routes`; statically calls `PaidCalls`, `PlannedCall`, `caps_from_options`, `describe_routes`, `project_routes`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `PaidCalls`, `PlannedCall`, `ProjectRoute`, `ROLE_TASK`; statically calls `PlannedCall`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `declared_budgets`, `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`; calls `declared_budgets`, `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/ai/isolation|learnloop.ai.isolation]] — imports `ToolIsolation`, `isolation_mode`, `tool_isolation`; calls `ToolIsolation`, `isolation_mode`, `tool_isolation`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `estimate_tokens`; calls `estimate_tokens`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `pathlib`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]], [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/project_support.py](../../../../../../tests/project_support.py) — direct import
- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_a_confinable_agent_runs_inside_the_isolation`
  - `test_an_unconfinable_agent_is_refused_before_any_request`
  - `test_project_routes_give_a_confinable_agent_the_vault_and_repos_as_hidden`
  - `test_project_routes_mark_an_unconfinable_agent_not_ready`
  - `test_the_kill_switch_runs_unconfined_and_says_so`
- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — direct import
  - `test_a_grade_never_persists_without_its_judgment`
  - `test_a_second_grader_waits_its_turn_instead_of_paying`
  - `test_an_adjudication_never_persists_without_its_judgment`
  - `test_interleaved_graders_leave_one_outcome_and_report_it`
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_grading_effort_leaves_chat_profiles_without_an_effort_alone`
  - `test_hidden_retries_are_admitted_only_against_max_retries`
  - `test_metered_calls_carry_their_admitted_output_limit`
  - `test_metered_output_limit_reaches_the_provider_request_and_its_repair`
  - `test_metered_routes_fail_closed_without_a_price`
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_replay_and_rebuild_make_no_git_model_or_subprocess_calls`
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
  - `test_answers_grades_and_contest`
  - `test_grade_failures_stay_pending_then_fail`
- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance`

## Modification guidance

- Make changes here when the responsibility remains ai runtime within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/ai_runtime.py](../../../../../../src/learnloop/projects/ai_runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
