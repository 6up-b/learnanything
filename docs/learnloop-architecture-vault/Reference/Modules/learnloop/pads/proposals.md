---
title: "learnloop.pads.proposals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/proposals.py"
source_paths:
  - "src/learnloop/pads/proposals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.pads.proposals module"
  - "src/learnloop/pads/proposals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.proposals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.proposals` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: LearnLoop's suggested connections for a pad block, and what the learner did with them (spec §10.6, §14).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/proposals.py](../../../../../../src/learnloop/pads/proposals.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProposalRefused(Exception)` ([source](../../../../../../src/learnloop/pads/proposals.py), line 36)
  - `__init__(self, code: str, message: str) -> None` (line 37; internal)
- `propose_for_blocks(repository: Any, block_ids: Iterable[str], *, vault: Any=None, clock: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 74) — After a pad batch: one proposal for each block whose newly committed words have none yet and a candidate (:func:`_findings`).
- `pad_proposals(repository: Any, pad_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 112) — ``pad.proposals``: each standing block's proposal for its current words, with its labels (``shown`` false once dismissed or marked "not this").
- `label(repository: Any, *, label_id: str, proposal_kind: str, proposal_id: str, label_value: str, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 134) — Record one label, idempotent by the client-minted ``label_id``.

### Module constants

- `LABELS` ([src/learnloop/pads/proposals.py](../../../../../../src/learnloop/pads/proposals.py), line 29)
- `PASSAGE_LINK` ([src/learnloop/pads/proposals.py](../../../../../../src/learnloop/pads/proposals.py), line 30)
- `REASONS` ([src/learnloop/pads/proposals.py](../../../../../../src/learnloop/pads/proposals.py), line 33)

### Explicit exports

`__all__` declares:

- `LABELS`
- `PAD_PROPOSAL`
- `PASSAGE_LINK`
- `PROMOTED_ROW`
- `ProposalRefused`
- `REASONS`
- `label`
- `pad_proposals`
- `propose_for_blocks`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/pads/proposals.py), line 42)
- `_block_places(connection: Any, head: dict[str, Any]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 47)
- `_findings(vault: Any, repository: Any, connection: Any, head: dict[str, Any]) -> list[Any]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 51) — The candidates for one block, best first: a passage the cue judge tied to the same learner problem (ranked for this learner), else another book's section the coverage judge says treats the same topic, else a passage found for the block's words by keyword ("found by search, not c…
- `_out(row: dict[str, Any], labels: list[dict[str, Any]], current: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/proposals.py), line 104)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `module`; statically calls `label`, `pad_proposals`, `propose_for_blocks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `reading_source`; calls `reading_source`
- [[Reference/Modules/learnloop/db/stores/pad_ledgers|learnloop.db.stores.pad_ledgers]] — imports `module`; calls `insert_label`, `insert_proposal`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`, `heads`, `label`, `labels_for`, `pad`, `proposal`, `proposal_for_version`, `proposals_for_versions`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `emittable`, `lineage`, `passages_of`, `words_version`; calls `emittable`, `lineage`, `passages_of`, `words_version`
- [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]] — imports `RELATION_REASONS`, `as_proposal`, `module`; calls `as_proposal`, `by_correspondents`, `by_passage_links`, `by_search`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_menu_elsewhere_and_proposals.py](../../../../../../tests/test_menu_elsewhere_and_proposals.py) — direct import
  - `test_a_pad_block_with_no_passage_link_gets_a_correspondent_then_a_search_proposal`
- [tests/test_reader_rd4_carried_and_proposals.py](../../../../../../tests/test_reader_rd4_carried_and_proposals.py) — direct import
  - `test_a_committed_note_under_a_linked_quote_gets_one_proposal_from_the_passage_links`

## Modification guidance

- Make changes here when the responsibility remains proposals within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/proposals.py](../../../../../../src/learnloop/pads/proposals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
