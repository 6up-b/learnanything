---
title: "learnloop.experiments.contextual_embeddings.e1.decide"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/decide.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/decide.py"
source_commit: "5bcead897e0c117ad063e707611aacf640acddad"
source_commit_timestamp: "2026-10-24T00:11:39-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.decide module"
  - "src/learnloop/experiments/contextual_embeddings/e1/decide.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.decide`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.decide` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: E1's scoring and its prespecified decision (spec §8; fixed before any v2 result).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/decide.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py) |
| Source lines | 136 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5bcead897e0c117ad063e707611aacf640acddad` |
| Commit timestamp | `2026-10-24T00:11:39-04:00` |

## Public API

- `add_virtual_arms(rows: list[dict[str, Any]], finalists: Mapping[str, str | None], best: str | None, v2_best: str | None) -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 46) — Per-row columns for each copy's finalists, its best finalist and the chosen v2 arm.
- `decide_e1(plan: Mapping[str, Any], copies: Mapping[str, Mapping[str, Any]], pooled: list[dict[str, Any]], *, measured: Sequence[Mapping[str, Any]], gpu_meter: Mapping[str, Any], spend: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 57)

### Module constants

- `METRICS` ([src/learnloop/experiments/contextual_embeddings/e1/decide.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 31)
- `FINALIST_KEYS` ([src/learnloop/experiments/contextual_embeddings/e1/decide.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 32)

## Internal implementation anchors

- `_primary(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 35)
- `_best(summary: Mapping[str, Mapping[str, Any]], arms: Sequence[str]) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py), line 41)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `decide_e1`; statically calls `decide_e1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `arm_summary`, `completion`, `paired`; calls `arm_summary`, `completion`, `paired`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `primary_rows`; calls `primary_rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — imports consumer [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]]

## Modification guidance

- Make changes here when the responsibility remains decide within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/decide.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/decide.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
