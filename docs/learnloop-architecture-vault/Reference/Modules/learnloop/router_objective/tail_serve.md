---
title: "learnloop.router_objective.tail_serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/tail_serve.py"
source_paths:
  - "src/learnloop/router_objective/tail_serve.py"
source_commit: "017c3ed22ddf583d5cddfe612d4e1ac32dc70950"
source_commit_timestamp: "2026-11-05T12:03:53-05:00"
source_worktree_state: "clean"
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
  - "learnloop.router_objective.tail_serve module"
  - "src/learnloop/router_objective/tail_serve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.tail_serve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.tail_serve` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO6 (spec_router_objective_v1 §10): the learned tail at a decision.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py) |
| Source lines | 138 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `017c3ed22ddf583d5cddfe612d4e1ac32dc70950` |
| Commit timestamp | `2026-11-05T12:03:53-05:00` |

## Public API

- `features(connection: Any, inputs: Any, actions: Sequence[Any], *, now_iso: str) -> tuple[dict[str, tuple[float, ...]], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 37) — Each candidate's features at serve time (the module docstring's step 1).
- `residual(repository: Any, config: Any, *, inputs: Any, actions: Sequence[Any], now_iso: str, generator_now: str, clock: Any=time.monotonic) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 67) — The decision's residual record (module docstring), or its failure: ``{"status": ...}``.
- `applied(record: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 112)
- `shifted(evaluation: Any, record: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 116) — The evaluation the numeric policy's argmax reads: each candidate's draws moved by ``ŵ·V_residual`` (a constant per candidate, so the paired precision is the tail's).
- `candidate_terms(record: Mapping[str, Any], ref: str, v_tail: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 129) — §10's per-candidate trace terms: ``ŵ``, ``V_tail``, ``V_residual`` and ``Ṽ``.

### Module constants

- `LOG` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 32)
- `VERSION` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 34)

### Explicit exports

`__all__` declares:

- `VERSION`
- `applied`
- `candidate_terms`
- `features`
- `residual`
- `shifted`

## Internal implementation anchors

- `_exact(value: float) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 105) — A number the trace keeps exactly (its ``repr``): the trace rounds every float to six places, and the fit's standardized coefficients and the features must recompute ``V_residual`` to float precision.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `candidate_terms`, `residual`, `shifted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; calls `_lo_rows`, `_pending_reports`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `ActionView`, `TopicNumbers`, `belief`, `prior_fit`, `residual_weight`, `vector`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `contrasts`, `fits`, `logged`, `snapshot_mastery`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_at_the_tag_the_trace_carries_the_residual_and_its_terms_recompute`

## Modification guidance

- Make changes here when the responsibility remains tail serve within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
