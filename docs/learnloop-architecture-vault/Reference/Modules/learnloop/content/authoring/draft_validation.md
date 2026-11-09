---
title: "learnloop.content.authoring.draft_validation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/draft_validation.py"
source_paths:
  - "src/learnloop/content/authoring/draft_validation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.draft_validation module"
  - "src/learnloop/content/authoring/draft_validation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.draft_validation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.draft_validation` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Post-import validation of an authored exercise against its request (spec §8.1).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/draft_validation.py](../../../../../../../src/learnloop/content/authoring/draft_validation.py) |
| Source lines | 113 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `draft_validator(vault: LoadedVault, constraints: Any, *, intent: str='practice', estimator: Callable[..., Any] | None=None, independent: bool=False) -> Callable[[Any], Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/draft_validation.py), line 37) — ``constraints``: ``PracticeConstraints`` or its stored mapping (a proposal's receipt).
- `duration_estimator(duration_by_mode: Mapping[str, Mapping[str, Any]]) -> Callable[..., float | None]` ([source](../../../../../../../src/learnloop/content/authoring/draft_validation.py), line 89) — The plan estimator's carried response per practice mode (``instructional.practice.duration_response``), evaluated on the authored draft: ``(item_id, practice_mode, expected_minutes) -> minutes``, or None for a mode it has no estimate for (Codex third pass F7).

### Explicit exports

`__all__` declares:

- `draft_validator`
- `duration_estimator`

## Internal implementation anchors

- `_field(constraints: Any, name: str, default: Any=None) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/draft_validation.py), line 31)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `draft_validator`, `duration_estimator`; statically calls `draft_validator`, `duration_estimator`
- [[Reference/Modules/learnloop/instructional/validation|learnloop.instructional.validation]] — imports `draft_validator`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/instructional/validation|learnloop.instructional.validation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_the_carried_duration_response_is_the_plan_estimate_of_the_authored_draft`

## Modification guidance

- Change draft validation policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/draft_validation.py](../../../../../../../src/learnloop/content/authoring/draft_validation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
