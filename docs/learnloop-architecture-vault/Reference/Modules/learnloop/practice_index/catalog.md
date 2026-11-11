---
title: "learnloop.practice_index.catalog"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/catalog.py"
source_paths:
  - "src/learnloop/practice_index/catalog.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.catalog module"
  - "src/learnloop/practice_index/catalog.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.catalog`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.catalog` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: The vault's item-facet hypergraph as the practice index reads it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/catalog.py](../../../../../../src/learnloop/practice_index/catalog.py) |
| Source lines | 41 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `registered_facets(vault: LoadedVault) -> dict[str, EvidenceFacet]` ([source](../../../../../../src/learnloop/practice_index/catalog.py), line 14) — Registered, non-retired facets by canonical id.
- `item_facets(vault: LoadedVault, item: PracticeItem) -> set[str]` ([source](../../../../../../src/learnloop/practice_index/catalog.py), line 22) — Canonical facet ids an item declares (registered or not).
- `facet_items(vault: LoadedVault, items: Iterable[PracticeItem] | None=None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/practice_index/catalog.py), line 27) — Item ids per canonical facet id, sorted.
- `facet_label(facet: EvidenceFacet) -> str` ([source](../../../../../../src/learnloop/practice_index/catalog.py), line 37)

### Module constants

- `DIAGNOSTIC_MODES` ([src/learnloop/practice_index/catalog.py](../../../../../../src/learnloop/practice_index/catalog.py), line 11)

### Explicit exports

`__all__` declares:

- `DIAGNOSTIC_MODES`
- `facet_items`
- `facet_label`
- `item_facets`
- `registered_facets`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `facet_label`, `registered_facets`; statically calls `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `item_facets`; statically calls `item_facets`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `item_facets`; statically calls `item_facets`
- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `facet_items`, `facet_label`, `registered_facets`; statically calls `facet_items`, `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `DIAGNOSTIC_MODES`, `facet_items`, `facet_label`, `item_facets`, `registered_facets`; statically calls `facet_items`, `facet_label`, `item_facets`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `facet_items`, `facet_label`, `registered_facets`; statically calls `facet_items`, `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `facet_label`, `item_facets`, `registered_facets`; statically calls `facet_label`, `item_facets`, `registered_facets`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`, `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]], [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]], [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — imports consumer [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]]
- [tests/reader_followups_helpers.py](../../../../../../tests/reader_followups_helpers.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/reader_followups_round4_helpers.py](../../../../../../tests/reader_followups_round4_helpers.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/reader_followups_round7_helpers.py](../../../../../../tests/reader_followups_round7_helpers.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/test_curriculum_c1_landing.py](../../../../../../tests/test_curriculum_c1_landing.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/test_reader_followup_valuation.py](../../../../../../tests/test_reader_followup_valuation.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — imports consumer [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]]

## Modification guidance

- Make changes here when the responsibility remains catalog within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/catalog.py](../../../../../../src/learnloop/practice_index/catalog.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
