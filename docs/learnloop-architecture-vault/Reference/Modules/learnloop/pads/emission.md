---
title: "learnloop.pads.emission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/emission.py"
source_paths:
  - "src/learnloop/pads/emission.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.emission module"
  - "src/learnloop/pads/emission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.emission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.emission` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: A scratchpad's words as learner text (spec §10.11, the contract per review F4; mvp-0.68).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py) |
| Source lines | 258 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `emittable(version: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/pads/emission.py), line 55) — A version of the learner's own, standing words (spec §10.11 "What is emitted").
- `lineage(connection: Any, block_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/emission.py), line 78) — The versions whose words this block carries, oldest first: its own versions since its last lift-out stub (earlier ones went to the lifted block), after the versions of the block it was lifted from, if it was.
- `words_version(versions: list[dict[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/pads/emission.py), line 85) — The version where the head's words were written: the earliest of the run of versions, ending at the head, with the head's kind and words.
- `context_blocks(connection: Any, head: Mapping[str, Any]) -> tuple[list[str], list[str]]` ([source](../../../../../../src/learnloop/pads/emission.py), line 100) — The blocks and pads whose links and quotes a block's words carry: the block itself, every block of its lift lineage (a lifted block's words came from there, and a lift made before anchors moved with the words left its links on the stub), and the block each of them is a note unde…
- `passages_of(connection: Any, head: Mapping[str, Any]) -> list[list[str]]` ([source](../../../../../../src/learnloop/pads/emission.py), line 122) — The passages a block's words are linked to, through :func:`context_blocks`, in written order.
- `quotes_of(connection: Any, repository: Any, head: Mapping[str, Any], passages: list[list[str]] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/pads/emission.py), line 134) — Someone else's words a block of the learner's might carry: the quote blocks of every pad its words passed through (:func:`context_blocks`) and the text of the passages it is linked to.
- `snapshot(connection: Any, repository: Any, head: Mapping[str, Any], words: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/emission.py), line 156) — What the gap pipeline is handed for one wording: the learner's words and the facts about them, frozen.
- `class Settled` ([source](../../../../../../src/learnloop/pads/emission.py), line 173) — What one pass did: jobs queued, readings set aside before they ran, gaps reversed.
  - `merge(self, other: 'Settled') -> None` (line 180; public)
- `settle_blocks(vault: Any, repository: Any, block_ids: Iterable[str], *, clock: Any=None) -> Settled` ([source](../../../../../../src/learnloop/pads/emission.py), line 242) — After a pad batch: emit the blocks' new words, supersede what they replaced, retract what was removed.
- `reconcile(vault: Any, repository: Any, *, clock: Any=None) -> Settled` ([source](../../../../../../src/learnloop/pads/emission.py), line 248) — Every block, the same way (a vault's open, after the gap worker drains): words committed while emission could not run are queued, and a reading that finished after its words were replaced is set aside.

### Module constants

- `LOG` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 37)
- `PAD_TEXT` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 39)
- `SNAPSHOT_KEY` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 41)
- `EMITTED` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 43)
- `QUOTE_KINDS` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 49)
- `_MAX_LIFTS` ([src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py), line 52)

### Explicit exports

`__all__` declares:

- `EMITTED`
- `PAD_TEXT`
- `QUOTE_KINDS`
- `RETRACTED`
- `SNAPSHOT_KEY`
- `SUPERSEDED`
- `Settled`
- `context_blocks`
- `emittable`
- `lineage`
- `passages_of`
- `quotes_of`
- `reconcile`
- `settle_blocks`
- `snapshot`
- `words_version`

## Internal implementation anchors

- `_lineage_until(connection: Any, block_id: str, stop: int | None, depth: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/emission.py), line 62)
- `_settle_block(connection: Any, repository: Any, block_id: str, *, emit: bool, gaps: Mapping[str, Mapping[str, Any]], reversed_ids: set[str], now: str) -> Settled` ([source](../../../../../../src/learnloop/pads/emission.py), line 186)
- `_settle(vault: Any, repository: Any, block_ids: Iterable[str] | None, clock: Any) -> Settled` ([source](../../../../../../src/learnloop/pads/emission.py), line 221)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `context_blocks`; statically calls `context_blocks`
- [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] — imports `emittable`, `lineage`, `passages_of`, `words_version`; statically calls `emittable`, `lineage`, `passages_of`, `words_version`
- [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] — imports `lineage`, `quotes_of`, `words_version`; statically calls `lineage`, `quotes_of`, `words_version`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `reconcile`; statically calls `reconcile`
- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `module`; statically calls `settle_blocks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `pad_text_on`; calls `pad_text_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `enqueue_job`, `gap_tables_present`, `gaps`, `insert_reversal`, `job_for_source`, `reversals`, `skip_queued_job`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `block_ids`, `chain`, `head`, `heads`, `lift_stub_for`, `pad`, `standing_anchors_for_blocks`
- [[Reference/Modules/learnloop/pads/quoting|learnloop.pads.quoting]] — imports `includes_quote`; calls `includes_quote`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]], [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_rd4_helpers.py](../../../../../../tests/reader_rd4_helpers.py) — direct import
- [tests/test_reader_rd4_emission.py](../../../../../../tests/test_reader_rd4_emission.py) — direct import
  - `test_a_committed_text_block_is_queued_once_with_its_snapshot`
  - `test_a_reading_that_finished_after_its_words_were_replaced_is_set_aside_by_the_reconcile`
  - `test_below_the_tag_a_pad_emits_nothing_and_the_upgrade_queues_its_standing_words`
  - `test_switched_off_nothing_is_queued_and_switched_on_the_reconcile_queues_it`
  - `test_the_tag_and_the_kind`

## Modification guidance

- Make changes here when the responsibility remains emission within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/emission.py](../../../../../../src/learnloop/pads/emission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
