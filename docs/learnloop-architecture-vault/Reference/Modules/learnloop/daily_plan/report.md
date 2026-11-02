---
title: "learnloop.daily_plan.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/report.py"
source_paths:
  - "src/learnloop/daily_plan/report.py"
source_commit: "ba2f22d7ca35c034630110d75966b34cc0b5a31c"
source_commit_timestamp: "2026-10-12T17:49:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.report module"
  - "src/learnloop/daily_plan/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.report` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: ``learnloop plan show | report`` (``spec_daily_loop_v1.md`` §12, the DL1 checkpoint).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/report.py](../../../../../../src/learnloop/daily_plan/report.py) |
| Source lines | 182 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ba2f22d7ca35c034630110d75966b34cc0b5a31c` |
| Commit timestamp | `2026-10-12T17:49:16-04:00` |

## Public API

- `plan_report(records: list[PlanRecord]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/report.py), line 27)
- `plan_show(record: PlanRecord, vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/report.py), line 120) — One persisted plan, as stored (no queue build, no projection).

### Explicit exports

`__all__` declares:

- `plan_report`
- `plan_show`

## Internal implementation anchors

- `_quantile(values: list[float], q: float) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/report.py), line 19)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]] — imports `plan_report`, `plan_show`; statically calls `plan_report`, `plan_show`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `PlanRecord`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/report.py](../../../../../../src/learnloop/daily_plan/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
