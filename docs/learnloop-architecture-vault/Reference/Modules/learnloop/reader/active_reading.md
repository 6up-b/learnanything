---
title: "learnloop.reader.active_reading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/active_reading.py"
source_paths:
  - "src/learnloop/reader/active_reading.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.active_reading module"
  - "src/learnloop/reader/active_reading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.active_reading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.active_reading` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW1b: active reading's acts that write more than the question row (spec_reader_workbench_v1 §4.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/active_reading.py](../../../../../../src/learnloop/reader/active_reading.py) |
| Source lines | 156 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ActiveReadingError(ValueError)` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 45) — Domain error for RW1b's active-reading acts.
- `class ReconstructUndone(ActiveReadingError)` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 49) — The learner undid this reconstruction: it is not made again.
- `queue_formative(vault: Any, repository: Any, row: dict[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 53) — Queue a missed formative answer for learner-text gaps (or nothing).
- `record_action(vault: Any, repository: Any, *, question_id: str, action: str, response_md: str | None=None, self_check: str | None=None, clock: Clock | None=None) -> tuple[dict[str, Any], str | None]` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 61) — The learner's act on an active-reading question and, for a missed self-check, its learner-text job, in one transaction (F7).
- `reconstruct_commit(root: Path, repository: Any, *, question_id: str, learning_object_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 89) — Escalate a reconstruct question into one practice item and add one ``test_me_later`` commitment on it.
- `reconstruct_undo(root: Path, repository: Any, *, question_id: str, vault: Any=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 123) — Undo "reconstruct this later": retire its commitment and its item.

### Module constants

- `RECONSTRUCT_DAYS` ([src/learnloop/reader/active_reading.py](../../../../../../src/learnloop/reader/active_reading.py), line 41)
- `RECONSTRUCT_REASON` ([src/learnloop/reader/active_reading.py](../../../../../../src/learnloop/reader/active_reading.py), line 42)

### Explicit exports

`__all__` declares:

- `ActiveReadingError`
- `RECONSTRUCT_DAYS`
- `ReconstructUndone`
- `queue_formative`
- `record_action`
- `reconstruct_commit`
- `reconstruct_undo`

## Internal implementation anchors

- `_key(question_id: str) -> str` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 76)
- `_commitment_for(repository: Any, question_id: str) -> str | None` ([source](../../../../../../src/learnloop/reader/active_reading.py), line 80)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `_commitment_for`, `reconstruct_commit`, `reconstruct_undo`, `record_action`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `retire_item`; calls `retire_item`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`, `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_reader_formative`; calls `enqueue_reader_formative`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `escalate`, `is_missed`, `record_selection_action`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_reconstruct.py](../../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_reconstruct_makes_one_item_and_one_test_me_later_commitment`
  - `test_reconstruct_needs_a_reconstruct_question`
  - `test_undo_retires_the_commitment_and_the_item`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f5_a_crash_after_the_item_is_written_leaves_one_item`
  - `test_f5_a_crash_before_the_commitment_leaves_one_item_and_one_commitment`
  - `test_f6_an_undone_reconstruction_is_never_reported_as_scheduled_again`

## Modification guidance

- Change active reading policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/active_reading.py](../../../../../../src/learnloop/reader/active_reading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
