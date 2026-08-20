---
title: "learnloop.vault.hashes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/hashes.py"
source_paths:
  - "src/learnloop/vault/hashes.py"
source_commit: "4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7"
source_commit_timestamp: "2026-05-19T19:15:00-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.hashes module"
  - "src/learnloop/vault/hashes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.hashes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps hashes behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `content_hash`, `learning_object_hash`, `practice_item_hash`, `concept_hash`, `concept_edge_hash`, `rubric_hash`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/hashes.py](../../../../../../src/learnloop/vault/hashes.py) |
| Source lines | 93 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7` |
| Commit timestamp | `2026-05-19T19:15:00-04:00` |

## Public API

- `content_hash(fields: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 22)
- `learning_object_hash(learning_object: LearningObject) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 27)
- `practice_item_hash(practice_item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 45)
- `concept_hash(concept_id: str, concept: Concept) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 63)
- `concept_edge_hash(edge: ConceptEdge) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 75)
- `rubric_hash(rubric: Rubric) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 92)

## Internal implementation anchors

- `_plain(value: Any) -> Any` ([source](../../../../../../src/learnloop/vault/hashes.py), line 12)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `practice_item_hash`; statically calls `practice_item_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Concept`, `ConceptEdge`, `LearningObject`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]], [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_difficulty_source_is_excluded_from_content_hash`

## Modification guidance

- Make changes here when the responsibility remains hashes within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/hashes.py](../../../../../../src/learnloop/vault/hashes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
