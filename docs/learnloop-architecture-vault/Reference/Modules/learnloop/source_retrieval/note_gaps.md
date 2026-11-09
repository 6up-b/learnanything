---
title: "learnloop.source_retrieval.note_gaps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/note_gaps.py"
source_paths:
  - "src/learnloop/source_retrieval/note_gaps.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.note_gaps module"
  - "src/learnloop/source_retrieval/note_gaps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.note_gaps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.note_gaps` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Deliverable curriculum C5: notes as learner text (spec_deliverable_curriculum_v1 §10.2, §10.4, §12 C5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py) |
| Source lines | 329 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NoteWithheld(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 54) — The note is linked to protected material (an exam unit, a held-back reading): it is not read for gaps.
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 59) — The opt-in, the notes and the gap pipeline all on.
- `class LinkedNote` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 72) — One linked note's current snapshot and everything it is linked to now.
- `linked_notes(vault: Any, repository: Repository) -> list[LinkedNote]` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 84) — Every note linked now, by the snapshot its links show, oldest link first.
- `linked_note_ids(vault: Any, repository: Repository) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 111) — The snapshots the gap queue may read now (:func:`linked_notes`).
- `note_text(vault: Any, repository: Repository, note_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 171) — What the gap pipeline reads for one linked snapshot, or None: switched off, the note is no longer linked (hidden, unlinked, or a newer snapshot shows), or it is gone.
- `payload(*, text: str, learning_object_ids: Sequence[str], subject_id: str | None, context: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 251) — What a note's reading sends (its text, topics, subject and context), in one canonical form: the request gate compares the prepared request's with what the note's links build now (Codex re-review F3).
- `refusal(vault: Any, repository: Repository, note_id: str, *, prepared: str | None=None, passages: Sequence[tuple[str, str | None, str | None]]=(), sources: Sequence[tuple[str, Sequence[str]]]=()) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 285) — Why the snapshot ``note_id`` may not be read for gaps now, or None when it may (Codex review F3: the note reading's request gate asks before every request and before the gap row is written).

### Module constants

- `SOURCE_KIND` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 46)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 49)
- `LEAD_CHARS` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 51)
- `OFF` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 278)
- `PROTECTED` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 279)
- `UNLINKED` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 280)
- `CHANGED` ([src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 281)

### Explicit exports

`__all__` declares:

- `LinkedNote`
- `NoteWithheld`
- `SOURCE_KIND`
- `enabled`
- `linked_note_ids`
- `linked_notes`
- `note_text`
- `payload`
- `refusal`

## Internal implementation anchors

- `_one_line(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 117)
- `_section_lead(vault: Any, repository: Repository, library: SC.Library, passage: tuple[str, str | None, str | None]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 121) — A linked passage's section, its title and first blocks, protection read now.
- `_section_spans(library: SC.Library, passage: tuple[str, str | None, str | None]) -> tuple[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 148) — Every span a linked passage's lead may carry text from (Codex review C2b round 5 F2): the passage's own span and every span of its section (its title's header and every block :func:`SC.peek` may supply; a ref keeps no section id).
- `_sources_out(library: SC.Library, sources: Sequence[tuple[str, Sequence[str]]]) -> None` ([source](../../../../../../src/learnloop/source_retrieval/note_gaps.py), line 261) — Raise :class:`NoteWithheld` when any of ``sources`` is protected material now (a reading named with no spans: when any part of it is).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `module`; statically calls `enabled`, `linked_note_ids`, `note_text`, `payload`, `refusal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_notes|learnloop.db.stores.learner_notes]] — imports `module`; calls `links`, `tables_present`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; calls `available`, `effective_rows`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `Library`, `peek`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `module`; calls `anchor_sources`, `beside_protected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_c2b_a_reader_note_written_beside_material_protected_since_is_never_read`
  - `test_f3_rereview_a_payload_changed_after_preparation_is_not_sent`
  - `test_f3_rereview_the_gate_is_bound_to_the_prepared_passages`
  - `test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing`
- [tests/test_notes_c2b_review5.py](../../../../../../tests/test_notes_c2b_review5.py) — direct import
  - `test_c2b_r5_f2_the_note_gate_refuses_once_a_bound_source_is_protected`
  - `test_c2b_r5_rereview_f1_a_notes_reading_refuses_a_snapshot_from_a_now_protected_older_anchor`

## Modification guidance

- Make changes here when the responsibility remains note gaps within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/note_gaps.py](../../../../../../src/learnloop/source_retrieval/note_gaps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
