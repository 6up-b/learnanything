---
title: "learnloop.router_objective.trace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/trace.py"
source_paths:
  - "src/learnloop/router_objective/trace.py"
source_commit: "workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d"
source_commit_timestamp: "2026-11-07T01:13:16-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.trace module"
  - "src/learnloop/router_objective/trace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.trace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.trace` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.8: one decision's trace, each sensor, the objective and the output, and its plain-words reading.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/trace.py](../../../../../../src/learnloop/router_objective/trace.py) |
| Source lines | 195 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d` |
| Commit timestamp | `2026-11-07T01:13:16-05:00` |

## Public API

- `assemble(trace: Mapping[str, Any], *, decision_id: str, decision_kind: str, decision_state_id: str | None, algorithm_version: str, local_date: str, session_id: str | None, created_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 50) — The ``router_objective_traces`` row for one decision's trace dict.
- `explain(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 96) — The trace in plain words, for the learner who asks how a block was chosen (glass box on request).
- `record(connection: Any, *, decision_id: str, decision_kind: str, router_record: Mapping[str, Any] | None, config: Any, local_date: str, session_id: str | None, at: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 177) — Write the decision's trace beside it, in its transaction (its own savepoint).

### Module constants

- `TRACE_VERSION` ([src/learnloop/router_objective/trace.py](../../../../../../src/learnloop/router_objective/trace.py), line 33)

### Explicit exports

`__all__` declares:

- `TRACE_VERSION`
- `assemble`
- `explain`
- `record`

## Internal implementation anchors

- `_canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 36)
- `_round(value: Any, digits: int=6) -> Any` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 40)
- `_pct(value: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 80)
- `_split_sentence(mixing: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/trace.py), line 84) — Whether the split between the two suggestions has moved, in plain words (from the weight's own source).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `explain`; statically calls `explain`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `record`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `record`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `_round`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `explain`; statically calls `explain`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `decision_state`, `insert_trace`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]], [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]], [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_why_surface_offers_the_trace_in_plain_words`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols`
- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_at_the_tag_the_trace_carries_the_residual_and_its_terms_recompute`

## Modification guidance

- Make changes here when the responsibility remains trace within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/trace.py](../../../../../../src/learnloop/router_objective/trace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
