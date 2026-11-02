---
title: "learnloop.attempts.grading_admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grading_admission.py"
source_paths:
  - "src/learnloop/attempts/grading_admission.py"
source_commit: "f2aa47537b5203f923088e33b88174f61c08d027"
source_commit_timestamp: "2026-10-13T13:46:55-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.grading_admission module"
  - "src/learnloop/attempts/grading_admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grading_admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grading_admission` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Optional spend admission around each practice grading call.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grading_admission.py](../../../../../../src/learnloop/attempts/grading_admission.py) |
| Source lines | 54 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f2aa47537b5203f923088e33b88174f61c08d027` |
| Commit timestamp | `2026-10-13T13:46:55-04:00` |

## Public API

- `grading_admission(guard: Guard | None) -> Iterator[None]` ([source](../../../../../../src/learnloop/attempts/grading_admission.py), line 26) — Admit every practice grading call made inside this block through ``guard``.
- `admit_grading_call(purpose: str, prompt: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/attempts/grading_admission.py), line 37) — Wrap ONE logical grading call (one sample); a no-op without a guard.
- `estimated_prompt_tokens(prompt: str) -> int` ([source](../../../../../../src/learnloop/attempts/grading_admission.py), line 48) — The same bytes/4 input estimate the diagnosis plans use.

### Module constants

- `_GUARD` ([src/learnloop/attempts/grading_admission.py](../../../../../../src/learnloop/attempts/grading_admission.py), line 22)

### Explicit exports

`__all__` declares:

- `Guard`
- `admit_grading_call`
- `estimated_prompt_tokens`
- `grading_admission`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `estimated_prompt_tokens`; statically calls `estimated_prompt_tokens`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `admit_grading_call`, `estimated_prompt_tokens`; statically calls `admit_grading_call`, `estimated_prompt_tokens`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `admit_grading_call`; statically calls `admit_grading_call`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `estimated_prompt_tokens`, `grading_admission`; statically calls `estimated_prompt_tokens`, `grading_admission`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `estimated_prompt_tokens`; statically calls `estimated_prompt_tokens`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_proof_item_is_graded_in_exactly_one_model_call`

## Modification guidance

- Change grading admission policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grading_admission.py](../../../../../../src/learnloop/attempts/grading_admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
