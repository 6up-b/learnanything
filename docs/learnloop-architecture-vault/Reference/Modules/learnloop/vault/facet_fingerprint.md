---
title: "learnloop.vault.facet_fingerprint"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/facet_fingerprint.py"
source_paths:
  - "src/learnloop/vault/facet_fingerprint.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.facet_fingerprint module"
  - "src/learnloop/vault/facet_fingerprint.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.facet_fingerprint`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.facet_fingerprint` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Deterministic semantic fingerprint for content facets (knowledge-model §3.2).

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py) |
| Source lines | 88 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `normalize_text(value: Any) -> str` ([source](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 38) — Lowercase, strip, and collapse internal whitespace.
- `normalized_contract(facet: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 61) — Extract and normalize the semantic contract from a facet-like object.
- `semantic_fingerprint(facet: Any) -> str` ([source](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 82) — Deterministic ``sf_...`` fingerprint of a facet's normalized contract.

### Module constants

- `_CONTRACT_SCALAR_FIELDS` ([src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 21)
- `_CONTRACT_LIST_FIELDS` ([src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 22)
- `_WHITESPACE` ([src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 33)
- `FINGERPRINT_PREFIX` ([src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 35)

## Internal implementation anchors

- `_normalize_list(values: Any) -> list[str]` ([source](../../../../../../src/learnloop/vault/facet_fingerprint.py), line 46) — Normalize each entry, drop empties, and sort so order is not identity.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `semantic_fingerprint`; statically calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `semantic_fingerprint`; statically calls `semantic_fingerprint`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `semantic_fingerprint`; statically calls `semantic_fingerprint`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]], [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]], [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_fingerprint_normalization_collapses_whitespace_and_case`
  - `test_semantic_fingerprint_deterministic_and_ignores_naming`

## Modification guidance

- Make changes here when the responsibility remains facet fingerprint within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/facet_fingerprint.py](../../../../../../src/learnloop/vault/facet_fingerprint.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
