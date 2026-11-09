---
title: "learnloop.content.pipeline.reread"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/reread.py"
source_paths:
  - "src/learnloop/content/pipeline/reread.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.reread module"
  - "src/learnloop/content/pipeline/reread.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.reread`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.reread` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Reading a book again, safely (re-read safety, 2026-10-14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py) |
| Source lines | 665 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `current_revision(repository: Any, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 76)
- `original_bytes(repository: Any, vault_root: Path, source_id: str, *, fetch_url=None, clock: Clock | None=None) -> Any | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 89) — The current revision's own bytes for an import that names an existing book, as ``FetchedBytes``; ``None`` when the book (or its revision) does not exist yet, so the import fetches as before (:func:`revision_bytes`).
- `revision_bytes(vault_root: Path, revision: Mapping[str, Any], artifact: Mapping[str, Any] | None, *, fetch_url=None, clock: Clock | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 102) — One revision's own bytes, as ``FetchedBytes``.
- `has_completed_reading(repository: Any, source_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 146)
- `adopt_revision(repository: Any, source_id: str, revision_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 151) — Make ``revision_id`` current once it has a completed reading: when the current one has none, or ``revision_id`` is newer.
- `unread_current_revision(repository: Any, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 174) — The E1 state: the current revision has no completed reading while an older one has.
- `restore_readable_revision(repository: Any, source_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 189) — The one-tap repair: the book's newest revision with a completed reading becomes current again (nothing is deleted).
- `unread_current_revisions(repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 200)
- `unit_map(old_ir: Any, new_ir: Any, aliases: Mapping[str, tuple[str, str, float | None]]) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 216) — Each old unit's unit in the new reading (``None``: unresolved).
- `carry_progress(repository: Any, old_extraction_id: str, new_extraction_id: str, old_ir: Any, new_ir: Any, units: Mapping[str, str | None], *, clock: Clock | None=None) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 270) — Section progress onto the new reading's sections.
- `carry_selection(repository: Any, old_extraction_id: str, new_extraction_id: str, units: Mapping[str, str | None], *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 319) — The study-map unit selection onto the new reading: its chapters and boundary overrides (a unit that does not resolve is flagged ``needs_review``) and the paper's metadata.
- `carry_annotations(repository: Any, source_id: str, new_extraction_id: str, *, clock: Clock | None=None) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 371) — Re-anchor onto the new reading every annotation of the book anchored on an EARLIER reading of its revision.
- `carry_over(repository: Any, new_extraction_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 401) — After a completed top-level reading on a revision that already had one: record the aliases from every earlier reading of the revision, then carry section progress, the unit selection and annotations onto it.
- `owes_carry(repository: Any, revision_id: str, extraction_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 460) — Whether a reading of ``revision_id`` would owe a carry-over: the revision has another completed top-level reading.
- `carry_owed(repository: Any, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 467) — The carry-over a book still owes its current reading, or None: ``{"job_id", "extraction_id"}`` of the import that did not finish it.
- `mark_carried(repository: Any, job_id: str, extraction_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 483)
- `finish_carry_over(repository: Any, source_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 490) — The card's "Finish moving them" and ``doctor --fix-state``: run the owed carry-over again (idempotent) and record it done.
- `page_label(pages: Sequence[int]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 510) — 0-based page indices as the learner counts them: "pages 14–39".
- `cost_phrase(usd: float | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 524)
- `study_state(repository: Any, source_id: str, extraction_id: str | None) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 534) — What the learner has on this book that a re-read must carry.
- `reread_reading(repository: Any, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 571) — The completed top-level reading the Reader opens for a book (the one a re-read replaces): never a page repair's child run, whose one page would become the whole next reading (Codex review F4).
- `reread_plan(vault: Any, repository: Any, source_id: str, *, backend: str | None, upload_ok: bool, title: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 599) — What reading this book again will read, cost and carry, in plain words.

### Module constants

- `ORIGINAL_CHANGED_CODE` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 58)
- `ORIGINAL_CHANGED_MESSAGE` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 59)
- `CARRY_OWED_KEY` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 450)
- `CARRY_DONE_KEY` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 451)
- `CARRY_INCOMPLETE_LINE` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 452)
- `CARRY_INCOMPLETE_ACTION` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 453)
- `CARRY_INCOMPLETE_DETAILS` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 454)
- `HELD_BACK_PLAN_LINE` ([src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py), line 506)

## Internal implementation anchors

- `_local_path(uri: str | None) -> Path | None` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 68)
- `_label(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 212)
- `_newest_with(readings: Sequence[str], has: Any) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 395) — The newest of ``readings`` (newest first) that has the state, else the newest.
- `_plural(count: int, noun: str, plural: str | None=None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 567)
- `_engine_line(backend: str | None, settings: Mapping[str, Any], usd: float | None) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/pipeline/reread.py), line 583) — ``(engine, who reads it)`` for the confirmation: hosted GLM-OCR (z.ai), the owner's own GLM-OCR server (on this computer or another), or text recognition on this computer (Codex review F9).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `cost_phrase`, `module`, `unread_current_revision`; statically calls `carry_owed`, `cost_phrase`, `unread_current_revision`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `module`; statically calls `carry_owed`, `finish_carry_over`, `reread_reading`, `unit_map`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `CARRY_DONE_KEY`, `CARRY_OWED_KEY`, `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`; statically calls `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `carry_owed`, `finish_carry_over`, `restore_readable_revision`, `unread_current_revisions`; statically calls `carry_owed`, `finish_carry_over`, `restore_readable_revision`, `unread_current_revisions`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`, `restore_readable_revision`; statically calls `carry_owed`, `finish_carry_over`, `original_bytes`, `reread_plan`, `restore_readable_revision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `_pdf_page_count`; calls `_pdf_page_count`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `FetchedBytes`, `IngestRunnerError`; calls `FetchedBytes`, `IngestRunnerError`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `source_marks`; calls `source_marks`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `module`; calls `alias_map`, `completed_readings`, `current_reading`, `previous_readings`, `reading_source`, `record_aliases`, `source_readings`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `reanchor_units`; calls `reanchor_units`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `LOCAL_URL`, `estimate`, `is_loopback_url`; calls `estimate`, `is_loopback_url`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `stored_original_path`; calls `stored_original_path`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `AnnotationError`, `reanchor_annotation`; calls `reanchor_annotation`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_f5_a_legacy_saved_place_after_a_reread_with_no_alias_falls_back_to_the_history`
  - `test_f7_a_carry_over_that_fails_is_finished_later_never_lost`
  - `test_f7_doctor_fix_state_finishes_a_carry_over_left_owed`
  - `test_progress_on_a_coarser_reading_is_read_through_only_where_every_part_was`
  - `test_rereview_f1_a_held_out_mark_follows_its_question_not_its_label`
  - `test_rereview_f2_a_held_out_unit_split_across_units_protects_both_halves`
  - `test_the_reread_keeps_the_page_scope_and_carries_the_selection`
  - `test_unit_map_falls_back_to_the_pages_a_coarser_reading_puts_them_on`
  - `test_unit_map_keeps_outline_unit_ids_that_name_the_same_sections`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`

## Modification guidance

- Change reread policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/reread.py](../../../../../../../src/learnloop/content/pipeline/reread.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
