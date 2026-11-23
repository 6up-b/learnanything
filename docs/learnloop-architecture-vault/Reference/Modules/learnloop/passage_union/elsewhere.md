---
title: "learnloop.passage_union.elsewhere"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/passage_union/elsewhere.py"
source_paths:
  - "src/learnloop/passage_union/elsewhere.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.passage_union"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.passage_union.elsewhere module"
  - "src/learnloop/passage_union/elsewhere.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-passage-union"
---

# `learnloop.passage_union.elsewhere`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.passage_union.elsewhere` exists within [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] to own the behavior summarized by its module contract: Where else the library says something about a passage or a learner's words (spec §9.1, §10.6): the one machinery behind the menus' promoted rows and the scratchpads' proposals.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/passage_union/elsewhere.py](../../../../../../src/learnloop/passage_union/elsewhere.py) |
| Source lines | 156 |
| Owning package | [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Finding` ([source](../../../../../../src/learnloop/passage_union/elsewhere.py), line 42) — One place elsewhere: its content reference and target, what found it, whether that was checked, and its rank within its finder (lower first).
  - `target(self) -> dict[str, Any]` (line 57; public)
- `by_passage_links(repository: Any, connection: Any, places: Iterable[tuple[str, str]]) -> list[Finding]` ([source](../../../../../../src/learnloop/passage_union/elsewhere.py), line 63)
- `by_correspondents(vault: Any, repository: Any, places: Iterable[tuple[str, str]], *, search_fallback: bool, embedder: Any | None=None, cache: Any | None=None) -> list[Finding]` ([source](../../../../../../src/learnloop/passage_union/elsewhere.py), line 77) — Each passage's section's correspondents in the other books, judged first; the search fallback's hits (keyword, no model) only when asked and when no judged one exists.
- `by_search(vault: Any, repository: Any, text: str, *, exclude_sources: Iterable[str]=(), exclude_places: Iterable[tuple[str, str]]=(), deep: bool, verify: bool, embedder: Any | None=None, verify_client: Any | None=None, owner_id: str='', pick_at_most: int) -> list[Finding]` ([source](../../../../../../src/learnloop/passage_union/elsewhere.py), line 111) — Passages found for ``text`` in the other sources; with ``verify``, the judge's picks are checked and the rest dropped (a judge that looked at a hit and did not pick it said it does not say this); without a judgment, every hit is unchecked.
- `as_proposal(finding: Finding) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/passage_union/elsewhere.py), line 148) — A finding as a ``pad_proposals`` row's content (the caller adds the ids and the time).

### Module constants

- `UNCHECKED` ([src/learnloop/passage_union/elsewhere.py](../../../../../../src/learnloop/passage_union/elsewhere.py), line 31)
- `RELATION_REASONS` ([src/learnloop/passage_union/elsewhere.py](../../../../../../src/learnloop/passage_union/elsewhere.py), line 33)

### Explicit exports

`__all__` declares:

- `Finding`
- `RELATION_REASONS`
- `UNCHECKED`
- `as_proposal`
- `by_correspondents`
- `by_passage_links`
- `by_search`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] — imports `RELATION_REASONS`, `as_proposal`, `module`; statically calls `as_proposal`, `by_correspondents`, `by_passage_links`, `by_search`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `module`; statically calls `by_correspondents`, `by_passage_links`, `by_search`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `reading_source`; calls `reading_source`
- [[Reference/Modules/learnloop/db/stores/passage_link_reads|learnloop.db.stores.passage_link_reads]] — imports `links_elsewhere`; calls `links_elsewhere`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `section_id_in_ir`; calls `section_id_in_ir`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `library_scope`; calls `Scope`, `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `correspondents`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `verify_spans`; calls `verify_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]], [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_menu_elsewhere_and_proposals.py](../../../../../../tests/test_menu_elsewhere_and_proposals.py) — direct import
  - `test_a_pad_block_with_no_passage_link_gets_a_correspondent_then_a_search_proposal`
  - `test_correspondents_judged_first_and_the_keyword_fallback_only_without_them`
  - `test_search_findings_are_the_judges_picks_checked_or_every_hit_unchecked_without_a_judgment`
- [tests/test_menu_promoted_rows.py](../../../../../../tests/test_menu_promoted_rows.py) — direct import
  - `test_judged_rows_arrive_through_the_job_checked_before_unchecked`

## Modification guidance

- Make changes here when the responsibility remains elsewhere within learnloop.passage_union; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/passage_union/elsewhere.py](../../../../../../src/learnloop/passage_union/elsewhere.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
