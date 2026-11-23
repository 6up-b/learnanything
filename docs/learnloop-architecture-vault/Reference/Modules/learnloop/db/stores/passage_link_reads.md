---
title: "learnloop.db.stores.passage_link_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/passage_link_reads.py"
source_paths:
  - "src/learnloop/db/stores/passage_link_reads.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.passage_link_reads module"
  - "src/learnloop/db/stores/passage_link_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.passage_link_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.passage_link_reads` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: A read of the cue judge's ``passage_links`` (migration 215) shared by the scratchpads' proposals and the menus' promoted rows (spec §9.1, §10.6: "from the same machinery"): the other passages a link ties to the same learner problem as these passages.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/passage_link_reads.py](../../../../../../../src/learnloop/db/stores/passage_link_reads.py) |
| Source lines | 43 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `links_elsewhere(connection: sqlite3.Connection, places: Iterable[tuple[str, str]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/passage_link_reads.py), line 17) — Every passage link to a passage other than ``places`` tied to a problem (a misconception, a hypothesis, a named gap, a recurrence group, a demonstrated facet, an unchecked claim) a link on ``places`` names, best first: by the link's own ``pick_rank`` (the cue judge's rank for th…

### Explicit exports

`__all__` declares:

- `links_elsewhere`

## Internal implementation anchors

- `_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/passage_link_reads.py), line 12)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]] — imports `links_elsewhere`; statically calls `links_elsewhere`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_menu_elsewhere_and_proposals.py](../../../../../../../tests/test_menu_elsewhere_and_proposals.py) — imports consumer [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]]
- [tests/test_menu_promoted_rows.py](../../../../../../../tests/test_menu_promoted_rows.py) — imports consumer [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/passage_link_reads.py](../../../../../../../src/learnloop/db/stores/passage_link_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
