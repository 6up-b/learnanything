---
title: "learnloop_sidecar.handlers.passage_union"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/passage_union.py"
source_paths:
  - "src/learnloop_sidecar/handlers/passage_union.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.passage_union module"
  - "src/learnloop_sidecar/handlers/passage_union.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.passage_union`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.passage_union` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPC: ``passage.union_range`` (spec §3.4, §7.6), everything tied to each passage of one visible range.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py) |
| Source lines | 441 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class UnionRangeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 36)
  - `_one_range(self) -> UnionRangeInput` (line 44; internal)
- `passage_union_range_handler(ctx: SidecarContext, params: UnionRangeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 54) — ``{extraction_id, spans: [{span_id, …everything tied to it}], sections}``.
- `class PassageContentInput(UnionRangeInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 71)
- `passage_content_handler(ctx: SidecarContext, params: PassageContentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 78) — One range of a reading as the source has it: ``{extraction_id, source_id, title, withheld, spans: [{span_id, text, page, t0, t1, section_id, section_label, withheld}]}`` (a ``source_piece``'s words, location and time).
- `class MenuObjectInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 100) — The object a menu was opened on (§9.1 "invocation"): a passage, a transcript cue (its span or a time), a highlight or margin note (its annotation and the passage it sits on), a window header (the passage in view), or a pad line (its block).
  - `_names_its_object(self) -> MenuObjectInput` (line 120; internal)
- `class PromotedInput(MenuObjectInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 131) — The menu's object and, from a client that may retry, its request id: a repeat answers with the job the first request started (its work runs once); the same id for another object is refused.
- `passage_knows_handler(ctx: SidecarContext, params: MenuObjectInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 254) — What this knows (§9.1 ``i``), as one read: the object's passages, each with everything the union read ties to it (each row with its anchor quality and alias).
- `passage_promoted_handler(ctx: SidecarContext, params: PromotedInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 277) — The menu's promoted rows at once (the cheap ones, ranked, at most four) and the job finding the judged ones: ``{object_key, rows, cap, withheld, pending_job: {job_id} | null, paid: {searched_by_meaning, verified, reason}}``.
- `class PromotedJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 349)
- `passage_promoted_job_handler(ctx: SidecarContext, params: PromotedJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 424) — The judged rows' job at once (never a wait): when done, every row ranked again, cheap and judged, at most four.
- `passage_promoted_cancel_handler(ctx: SidecarContext, params: PromotedJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 433) — Cancel the judged rows' job (the menu closed): its next paid request is refused; a finished job keeps its outcome.

### Module constants

- `PASSAGE_UNION_RPCS` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 22)
- `PASSAGE_CONTENT_RPCS` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 24)
- `MENU_RPCS` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 95)
- `PROMOTED_KIND` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 96)
- `_PROMOTED_REGISTRY` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 97)
- `_WORD_FIELDS` ([src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 220)

## Internal implementation anchors

- `_notes_by_span(vault: Any, repository: Any, extraction_id: str) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 27) — The notes linked beside each passage of a reading (curriculum C2's marks, while notes.enabled): the sidecar reads the notes' code, so the union read below it never does.
- `_menu_places(vault: Any, repository: Any, params: MenuObjectInput) -> tuple[str, list[tuple[str, str]], str, list[str], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 138) — The object's key, its passages, the words to search by, the sources it sits in, and whether any of its passages is exam or held-out material.
- `_union_entries(vault: Any, repository: Any, places: list[tuple[str, str]], row_origins: dict[str, set[tuple[str, str]]] | None=None) -> list[tuple[str, str, dict]]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 202)
- `_withhold_rows(vault: Any, repository: Any, entries: list[dict[str, Any]], row_origins: dict[str, set[tuple[str, str]]] | None=None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 223) — Drop every row whose words came from exam or held-out material, in place, and the rows' origins with them (``row_origins`` collects a kept learner row's origins for a later recheck).
- `_dismissed(repository: Any, rows: list[Any]) -> set[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 245)
- `_deliver_rows(ctx: SidecarContext, result: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 353)
- `_verbs_now(ctx: SidecarContext, result: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 382) — The per-verb verdict at a delivery, read again from the object's origins (a mark made since counts); a pad line that cannot be read withholds every verb.
- `_promoted_job_payload(ctx: SidecarContext, job_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/passage_union.py), line 394)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `module`; calls `waiting`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_job_offer`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `reading_source`; calls `reading_source`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`, `labels_for`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/passage_union/content|learnloop.passage_union.content]] — imports `passage_content`; calls `passage_content`
- [[Reference/Modules/learnloop/passage_union/elsewhere|learnloop.passage_union.elsewhere]] — imports `module`, `withheld_places`; calls `by_correspondents`, `by_passage_links`, `by_search`, `withheld_places`
- [[Reference/Modules/learnloop/passage_union/promoted|learnloop.passage_union.promoted]] — imports `module`; calls `cheap_rows`, `dismissed_rows`, `finding_rows`, `object_key`, `rank`
- [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] — imports `UnionError`, `span_range`, `union_range`; calls `span_range`, `union_range`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `annotation_placements`; calls `annotation_placements`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `block_roles`; calls `block_roles`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; calls `enabled`, `marks`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/workbench_protection|learnloop_sidecar.workbench_protection]] — imports `VERB_SURFACES`, `block_places`, `withheld_verbs`; calls `block_places`, `withheld_verbs`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_menu_promoted_rows.py](../../../../../../tests/test_menu_promoted_rows.py) — direct import
  - `test_what_this_knows_carries_the_notes_linked_beside_the_passage`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd0_rpcs_are_all_of_them`
  - `test_the_pinned_rd4_fix_rpcs_are_all_of_them`
  - `test_the_pinned_rd5a_rpcs_are_all_of_them`
- [tests/test_reader_rd0_rpcs.py](../../../../../../tests/test_reader_rd0_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_reader_rd4_rpcs.py](../../../../../../tests/test_reader_rd4_rpcs.py) — direct import
  - `test_the_fix_rounds_read_is_desktop_only_refuses_an_extra_field_and_is_versioned`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/passage_union.py](../../../../../../src/learnloop_sidecar/handlers/passage_union.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
