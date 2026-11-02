---
title: "learnloop.local_embeddings.identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/identity.py"
source_paths:
  - "src/learnloop/local_embeddings/identity.py"
source_commit: "986e7227906adc3349ee514cbba0eb6a4d5c7a0e"
source_commit_timestamp: "2026-10-24T14:49:56-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.identity module"
  - "src/learnloop/local_embeddings/identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.identity` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: Embedding space identity (spec_local_contextual_retrieval_v1 §4.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/identity.py](../../../../../../src/learnloop/local_embeddings/identity.py) |
| Source lines | 57 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `986e7227906adc3349ee514cbba0eb6a4d5c7a0e` |
| Commit timestamp | `2026-10-24T14:49:56-04:00` |

## Public API

- `local_space_pins(*, variant: str, software_epoch: Mapping[str, str], window_rule: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/identity.py), line 29)
- `hosted_space_pins(*, provider: str, model: str, dims: int, variant: str, window_rule: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/identity.py), line 38)
- `space_id(space_pins: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/local_embeddings/identity.py), line 44)
- `query_encoder_id(space: str, *, encoder: str, precision: str=pins.PRECISION, device_class: str='gpu', method: str=pins.QUERY_METHOD) -> str` ([source](../../../../../../src/learnloop/local_embeddings/identity.py), line 49) — ``encoder`` is ``teacher``, ``student:<checkpoint sha256>`` or a hosted model name.

### Module constants

- `RECIPE` ([src/learnloop/local_embeddings/identity.py](../../../../../../src/learnloop/local_embeddings/identity.py), line 22)

### Explicit exports

`__all__` declares:

- `RECIPE`
- `hosted_space_pins`
- `local_space_pins`
- `query_encoder_id`
- `space_id`

## Internal implementation anchors

- `_digest(value: Any) -> str` ([source](../../../../../../src/learnloop/local_embeddings/identity.py), line 25)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `hosted_space_pins`, `space_id`; statically calls `hosted_space_pins`, `space_id`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `local_space_pins`, `space_id`; statically calls `local_space_pins`, `space_id`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `query_encoder_id`; statically calls `query_encoder_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]]
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]]
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]]
- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]]
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]]
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]]
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — imports consumer [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]]

## Modification guidance

- Make changes here when the responsibility remains identity within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/identity.py](../../../../../../src/learnloop/local_embeddings/identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
