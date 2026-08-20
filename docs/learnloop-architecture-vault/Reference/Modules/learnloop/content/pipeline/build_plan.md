---
title: "learnloop.content.pipeline.build_plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/build_plan.py"
source_paths:
  - "src/learnloop/content/pipeline/build_plan.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.build_plan module"
  - "src/learnloop/content/pipeline/build_plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.build_plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.build_plan` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Deterministic build plan (spec_source_ingestion_v2 §8.6.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/build_plan.py](../../../../../../../src/learnloop/content/pipeline/build_plan.py) |
| Source lines | 375 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class StageEstimate` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 27)
  - `as_dict(self) -> dict` (line 36; public)
- `class PlannedSource` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 49)
  - `as_dict(self) -> dict` (line 62; public)
- `class BuildPlan` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 79)
  - `selected_unit_count(self) -> int` (line 90; public)
  - `total_input_tokens(self) -> int` (line 94; public)
  - `total_max_output_tokens(self) -> int` (line 98; public)
  - `total_calls(self) -> int` (line 102; public)
  - `cache_savings_tokens(self) -> int` (line 106; public)
  - `as_dict(self) -> dict` (line 109; public)
  - `snapshot_payload(self) -> dict` (line 134; public) — The estimate snapshot stored in a batch/job payload when it starts.
- `subject_has_study_map(vault, subject_id: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 140) — True when the subject already has an applied study map (any learning object).
- `route_create_or_update(vault, subject_id: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 154)
- `build_build_plan(repo: Repository, config: LearnLoopConfig, vault, *, subject_id: str | None, selections: list[Mapping[str, object]], budget_overrides: Mapping[str, int] | None=None) -> BuildPlan` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 158) — Assemble the deterministic build plan for a set of selected extractions.

## Internal implementation anchors

- `_selected_units(units: list[OutlineUnit], requested: list[str]) -> list[OutlineUnit]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 242)
- `_source_warnings(outline, units: list[OutlineUnit]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 249)
- `_stage_estimates(*, unit_tokens: list[int], cached_token_pool: int, budgets, routing: str, provider_context: int | None) -> list[StageEstimate]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 259)
- `_shard(unit_tokens: list[int], ceiling: int) -> list[list[int]]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 318)
- `_exceeds(unit_tokens: list[int], ceiling: int, provider_context: int | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 334)
- `_over_context(inputs: list[int], provider_context: int | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 343)
- `_provider_warnings(stages: list[StageEstimate], provider: str, provider_context: int | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 349)
- `_dedupe(values: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/build_plan.py), line 368)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `build_build_plan`; statically calls `build_build_plan`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `build_build_plan`; statically calls `build_build_plan`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `build_build_plan`; statically calls `build_build_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `OutlineUnit`, `build_source_outline`; calls `build_source_outline`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_build_plan_charts_per_run_budget_overrides`
  - `test_build_plan_routes_create_vs_update`
  - `test_build_plan_warns_when_provider_has_no_configured_context_limit`
  - `test_build_plan_warns_when_stage_exceeds_provider_context`
  - `test_token_budgets_preflight_emits_per_stage_estimates`

## Modification guidance

- Change build plan policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/build_plan.py](../../../../../../../src/learnloop/content/pipeline/build_plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
