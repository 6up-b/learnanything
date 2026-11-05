---
title: "learnloop.router_objective.tail_serve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/tail_serve.py"
source_paths:
  - "src/learnloop/router_objective/tail_serve.py"
source_commit: "5d726bbc21eefbd05b0b3cc0f068ec4272ae4ee8"
source_commit_timestamp: "2026-11-05T15:04:13-05:00"
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
| Source lines | 238 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5d726bbc21eefbd05b0b3cc0f068ec4272ae4ee8` |
| Commit timestamp | `2026-11-05T15:04:13-05:00` |

## Public API

- `snapshot(repository: Any, *, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 45) — The decision's own reads of the residual's mutable inputs, taken **at the decision's moment** (Codex review of RO6, F4): the pending reports (``decision_state``'s reader) and every LO's mastery numbers (RO0 row 9's), so a diagnosis queued or a projection moved after ``now_iso``…
- `features(inputs: Any, actions: Sequence[Any], *, frozen: Mapping[str, Any], cutoff_days: float | None=None) -> tuple[dict[str, tuple[float, ...]], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 65) — Each candidate's features at serve time (the module docstring's step 1), from the decision's ``frozen`` :func:`snapshot` and its frozen inputs only: nothing here reads the vault.
- `residual(repository: Any, config: Any, *, inputs: Any, actions: Sequence[Any], now_iso: str, generator_now: str, frozen: Mapping[str, Any] | None, clock: Any=time.monotonic) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 96) — The decision's residual record (module docstring), or its failure: ``{"status": ...}``.
- `previous_cutoff(rows: Sequence[Any], inputs: Any, *, now_iso: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 151) — §3.2 for the backup (Codex re-review F3): the latest earlier logged decision (``tail_data.Logged``) and its cutoff ``C_prev`` in days from now.
- `carried_cutoff(record: Mapping[str, Any] | None) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 176) — The cutoff (days from now) the candidates are valued at a second time, for an applied record whose previous decision's cutoff is ``carried`` (:func:`previous_cutoff`); else None (no second valuation).
- `with_carried_values(record: Mapping[str, Any], evaluation: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 188) — The record with each candidate's ``Q̄`` at the carried cutoff (``previous.q``, from the evaluation run at it, with its draws and time), or with why there is none (``previous.q_status``): a transition into this decision then has no value at the earlier cutoff and is censored ``cu…
- `applied(record: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 211)
- `shifted(evaluation: Any, record: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 215) — The evaluation the numeric policy's argmax reads: each candidate's draws moved by ``ŵ·V_residual`` (a constant per candidate, so the paired precision is the tail's).
- `candidate_terms(record: Mapping[str, Any], ref: str, v_tail: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 228) — §10's per-candidate trace terms: ``ŵ``, ``V_tail``, ``V_residual`` and ``Ṽ``.

### Module constants

- `LOG` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 37)
- `VERSION` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 39)
- `SNAPSHOT_VERSION` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 42)
- `CARRIED` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 146)
- `SAME_CUTOFF` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 147)
- `PAST_CUTOFF` ([src/learnloop/router_objective/tail_serve.py](../../../../../../src/learnloop/router_objective/tail_serve.py), line 148)

### Explicit exports

`__all__` declares:

- `CARRIED`
- `PAST_CUTOFF`
- `SAME_CUTOFF`
- `SNAPSHOT_VERSION`
- `VERSION`
- `applied`
- `candidate_terms`
- `carried_cutoff`
- `features`
- `previous_cutoff`
- `residual`
- `shifted`
- `snapshot`
- `with_carried_values`

## Internal implementation anchors

- `_exact(value: float) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_serve.py), line 204) — A number the trace keeps exactly (its ``repr``): the trace rounds every float to six places, and the fit's standardized coefficients and the features must recompute ``V_residual`` to float precision.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `candidate_terms`, `carried_cutoff`, `residual`, `shifted`, `snapshot`, `with_carried_values`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; calls `_pending_reports`, `_round`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `ActionView`, `TopicNumbers`, `belief`, `prior_fit`, `residual_weight`, `vector`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `_parse`, `contrasts`, `fits`, `logged`, `snapshot_mastery`

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

- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_no_snapshot_leaves_the_residual_out`
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
