---
title: "learnloop.content.pipeline.exam_marking"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/exam_marking.py"
source_paths:
  - "src/learnloop/content/pipeline/exam_marking.py"
source_commit: "5d6393b58d63cb97cb969d1640726b7a545d7492"
source_commit_timestamp: "2026-10-15T08:06:10-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.content.pipeline.exam_marking module"
  - "src/learnloop/content/pipeline/exam_marking.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.exam_marking`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.exam_marking` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Marking exam material on a reading (protection redesign, 2026-10-15; extraction identity, the same day's fourth round).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py) |
| Source lines | 394 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5d6393b58d63cb97cb969d1640726b7a545d7492` |
| Commit timestamp | `2026-10-15T08:06:10-04:00` |

## Public API

- `class StaleMarkConfirmation(Exception)` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 100) — The confirmation the owner gave no longer matches the reading the Reader opens or the proposal for it; ``plan`` is the fresh confirmation (None when nothing is held back any more).
  - `__init__(self, plan: dict[str, Any] | None) -> None` (line 105; internal)
- `held_back_reading(vault: Any, repository: Any, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 110) — The reading the Reader opens for the book, when it is withheld whole until exam material is marked on it (``exam_material`` rule 4); else None.
- `held_back_details(vault: Any, repository: Any, source_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 121) — The card's details for a held-back reading: why, in plain words.
- `held_back_readings(vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 131) — Every book whose current reading is held back: ``{"source_id", "extraction_id", "older", "ambiguous"}`` (``older``: the book's other extractions also held back, which no Reader opens; ``ambiguous``: the kinds of legacy mark that name no reading).
- `class MarkSuggestion` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 149) — What :func:`mark_exam_material` would hold out on a reading.
- `suggest_marks(vault: Any, repository: Any, extraction_id: str) -> MarkSuggestion` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 161) — Every unit of ``extraction_id`` that may hold material any mark of its book protects: over-inclusive, a suggestion the owner checks before anything is written, never a carry of protection.
- `proposal_hash(source_id: str, extraction_id: str, revision_id: str | None, suggestion: MarkSuggestion, selection: Mapping[str, Any] | None, unplaced: tuple[str, ...]=()) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 230) — The identity of one shown proposal: the book, the reading and its revision, the units it holds out and where they were suggested from, the reading's own marks as they stood, and the book's unplaced marks it was made over (the ones the marking records it reviewed).
- `mark_plan(vault: Any, repository: Any, source_id: str, *, title: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 277) — The card's confirmation before marking, in plain words, bound to the reading it names and the proposal it shows (``proposal_hash``); None when the book's reading is not held back.
- `mark_exam_material(vault: Any, repository: Any, source_id: str, *, extraction_id: str | None, proposal_hash: str | None, title: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 286) — The owner's confirmed marking of the reading the Reader opens, exactly as the confirmation they confirmed showed it (``extraction_id`` and ``proposal_hash`` from :func:`mark_plan`): the units held out in its own unit selection, the owner's mark (``PROTECTION_MARK_KEY``) and the…

### Module constants

- `MARK_ACTION` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 68)
- `MARK_LABEL` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 69)
- `HELD_BACK_LINE` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 71)
- `HELD_BACK_DETAILS` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 72)
- `AMBIGUOUS_DETAILS` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 79)
- `FOUND_DETAILS` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 87)
- `MARK_JUDGMENT_TASK` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 93)
- `CHANGED_LINE` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 95)
- `_LISTED` ([src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 97)

### Explicit exports

`__all__` declares:

- `AMBIGUOUS_DETAILS`
- `CHANGED_LINE`
- `FOUND_DETAILS`
- `HELD_BACK_DETAILS`
- `HELD_BACK_LINE`
- `MARK_ACTION`
- `MARK_JUDGMENT_TASK`
- `MARK_LABEL`
- `MarkSuggestion`
- `StaleMarkConfirmation`
- `held_back_details`
- `held_back_reading`
- `held_back_readings`
- `mark_exam_material`
- `mark_plan`
- `proposal_hash`
- `suggest_marks`

## Internal implementation anchors

- `_listed(labels: tuple[str, ...]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 214)
- `_marks_state(selection: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 220) — What a reading's own selection says about protection (part of the proposal: a mark written meanwhile makes the confirmation stale).
- `_plan(vault: Any, repository: Any, source_id: str, title: str | None) -> tuple[dict[str, Any], MarkSuggestion, dict[str, Any] | None, SourceMarks] | None` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 244)
- `_record_verdict(repository: Any, source_id: str, plan: Mapping[str, Any], suggestion: MarkSuggestion, reviewed: list[str], now: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/exam_marking.py), line 352) — The owner's marking as an owner verdict in ``judgment_ledger``, in the caller's transaction, once per confirmed proposal (Codex review of extraction identity, F5: every owner verdict appends to the ledger).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; statically calls `held_back_details`, `held_back_reading`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `MARK_LABEL`, `held_back_readings`; statically calls `held_back_readings`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`; statically calls `mark_exam_material`, `mark_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `module`; calls `carry_owed`, `finish_carry_over`, `reread_reading`, `unit_map`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `AMBIGUOUS_SCOPE`, `AMBIGUOUS_SELECTION`, `HELD_OUT_EVALUATION`, `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `REVIEWED_UNPLACED`, `SourceMarks`, `marks_made_on`, `protected_spans_by_reading`, `source_marks`; calls `marks_made_on`, `protected_spans_by_reading`, `source_marks`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `module`; calls `alias_map`, `reading_source`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_a_legacy_held_out_mark_withholds_every_reading_until_marked_exactly`
  - `test_an_exact_held_out_mark_under_a_legacy_scope_waits_for_the_owners_marking`
  - `test_an_exact_mark_never_resolves_a_reading_a_legacy_mark_may_also_be_about`
  - `test_f13_a_changed_proposal_returns_a_fresh_confirmation`
  - `test_f13_the_confirmed_proposal_is_applied_exactly_and_bound_to_its_reading`
  - `test_identity_review_a_signal_of_unknown_reading_is_named_plainly`
  - `test_identity_review_f1_a_confirmation_never_covers_an_ambiguous_mark_made_after_it`
  - `test_identity_review_f5_the_owners_marking_is_an_owner_verdict_in_the_judgment_ledger`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_redesign_a_reading_of_a_new_revision_is_held_back_until_marked`
  - `test_redesign_a_study_map_save_keeps_the_owners_marks`
  - `test_redesign_an_unprotected_book_is_unaffected`
  - `test_redesign_marking_the_new_reading_makes_it_usable`

## Modification guidance

- Change exam marking policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/exam_marking.py](../../../../../../../src/learnloop/content/pipeline/exam_marking.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
