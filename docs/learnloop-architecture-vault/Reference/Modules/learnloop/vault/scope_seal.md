---
title: "learnloop.vault.scope_seal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/scope_seal.py"
source_paths:
  - "src/learnloop/vault/scope_seal.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.scope_seal module"
  - "src/learnloop/vault/scope_seal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.scope_seal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.scope_seal` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: The seal binding a source-set member's scope to the reading it names (exam protection by extraction identity, docs/reviews/exam-protection-identity.md).

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/scope_seal.py](../../../../../../src/learnloop/vault/scope_seal.py) |
| Source lines | 42 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `scope_seal(member: Any) -> str | None` ([source](../../../../../../src/learnloop/vault/scope_seal.py), line 20) — A hash of the book, ``scope_extraction_id``, ``scope_revision_id`` and every scope entry's unit id and role override, in order (the pinned revision is left out: a refresh may advance it).

### Explicit exports

`__all__` declares:

- `scope_seal`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `scope_seal`; statically calls `scope_seal`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `scope_seal`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `scope_seal`; statically calls `scope_seal`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]], [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]], [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]
- [tests/test_curriculum_c3_codex_review.py](../../../../../../tests/test_curriculum_c3_codex_review.py) — imports consumer [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]]

## Modification guidance

- Make changes here when the responsibility remains scope seal within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/scope_seal.py](../../../../../../src/learnloop/vault/scope_seal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
