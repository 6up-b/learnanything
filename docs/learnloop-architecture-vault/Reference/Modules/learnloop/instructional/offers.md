---
title: "learnloop.instructional.offers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/offers.py"
source_paths:
  - "src/learnloop/instructional/offers.py"
source_commit: "801326152516add59dcfa4016352f0be987aca83"
source_commit_timestamp: "2026-10-13T01:05:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.offers module"
  - "src/learnloop/instructional/offers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.offers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.offers` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: The tutor's "Practice this" offer (spec_source_practice_and_probes_v1 §6.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/offers.py](../../../../../../src/learnloop/instructional/offers.py) |
| Source lines | 58 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `801326152516add59dcfa4016352f0be987aca83` |
| Commit timestamp | `2026-10-13T01:05:29-04:00` |

## Public API

- `practice_request_for_answer(vault: LoadedVault, event: Mapping[str, Any], *, exercise_arm: bool=False) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/offers.py), line 25) — The practice request for one answered tutor question, or None.

### Module constants

- `PRACTICE_REQUEST_VERSION` ([src/learnloop/instructional/offers.py](../../../../../../src/learnloop/instructional/offers.py), line 22)

### Explicit exports

`__all__` declares:

- `PRACTICE_REQUEST_VERSION`
- `practice_request_for_answer`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `practice_request_for_answer`; statically calls `practice_request_for_answer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `learning_objects_for_event`; calls `learning_objects_for_event`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `ITEM_BOUND_CONTEXTS`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_no_request_for_an_unanswered_question`
  - `test_the_request_is_deterministic_and_excludes_the_current_item`

## Modification guidance

- Make changes here when the responsibility remains offers within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/offers.py](../../../../../../src/learnloop/instructional/offers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
