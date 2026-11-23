---
title: "learnloop.figures.protection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/protection.py"
source_paths:
  - "src/learnloop/figures/protection.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.protection module"
  - "src/learnloop/figures/protection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.protection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.protection` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: May this figure be built, sent or shown now?

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py) |
| Source lines | 547 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `withheld_message(vault: Any, repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 107) — The refusal when any of the spans (or the whole reading) is exam or held-out material (``exam_material(...).withheld``), else None: the shared :func:`~learnloop.content.sources.exam_material.spans_withheld`, which learner-text gaps ask too (fix round 2, F1).
- `keys_withheld(vault: Any, repository: Repository, keys: Sequence[Sequence[str]]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 137) — RW5d: the refusal when any ``(extraction_id, span_id)`` (a retrieved passage in any source, or its neighbour) is held out now, else None: the one predicate, asked per source.
- `row_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 153) — A stored figure's held-out refusal now, else None: its home's spans and (RW5d) every retrieved passage it was built from, across sources.
- `learner_state_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 184) — Why a stored figure may not go out now because of the learner state an author of it was sent, or None (follow-ups Nov 2, ruling R1 of learner data-relax 2: exam-material protection, not privacy).
- `inherited_learner_inputs(repository: Repository, row: Mapping[str, Any]) -> list[Any]` ([source](../../../../../../src/learnloop/figures/protection.py), line 269) — What every learner state the authors of ``row`` and of the figures it was made from were sent was read from (Codex review F4): a revision's rich job carries it, so the job checks it at admission, before every request and before it stores, though the revision sends no learner sta…
- `figure_homes(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]] | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 294) — Where a figure with no passage lands (:func:`learnloop.figure_admission.figure_home_keys`): every recorded request's reading position; empty for an anchored figure.
- `show_me_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/protection.py), line 304) — A figure built from a goal or with no anchor (RW5d): absent while ``figures.enabled`` is off.
- `figure_withheld(vault: Any, repository: Repository, figure_id: str) -> bool` ([source](../../../../../../src/learnloop/figures/protection.py), line 310) — Whether a stored figure may not go out now (its row is gone, or any span it was built from is held out, or (RW5d) it is a show-me figure while figures are off).
- `stored_learner_state_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 368) — Why a stored rich figure whose author was sent the learner's state may not go out (be delivered, recovered or reused) now, or None: what that state was read from is checked again against the protection as it is now (``learner_state.inputs_withheld``; a missing record fails close…
- `intent_learner_state_withheld(vault: Any, repository: Repository, payload: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 382) — Why a saved rich job payload's learner state (a quick figure's durable rich intent) may not go out now, or None when its author was sent no learner state (follow-ups Nov 2: a fuller version stored with no record of its own is read from its quick figure's intent, the job's payloa…
- `stored_plan_open_items(repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/figures/protection.py), line 415) — The ids of the items today's latest stored plan holds open: planned, and not yet done, skipped or displaced.
- `item_passages(vault: Any, repository: Repository, *, clock: Clock | None=None) -> tuple[frozenset[tuple[str, str]], frozenset[str]] | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 435) — RW5d P5 (spec §10b.2, G-SM29): the passages no prebuild may send or show now: every passage (``corpus.item_exclusions``: its exercise, solution or worked answer, whatever the relation) of an item under a live administration (:data:`LIVE_ADMINISTRATION_REASONS`), reserved for a g…
- `rich_base_keys(base: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/protection.py), line 491) — Every ``(extraction_id, span_id)`` a rich job's saved context names: its passage, the paragraphs around it the author was sent, its region, its retrieved passages and its home (the spans ``rich._withheld`` checks).
- `rich_base_item_protected(vault: Any, repository: Repository, base: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 510) — :data:`ITEM_PASSAGE_PROTECTED` when a rich job's saved context touches a passage :func:`item_passages` protects now, or the protection can't be read (fail closed); else None.

### Module constants

- `_LOG` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 84)
- `ATTEMPT_HOST_REFS` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 89)
- `RICH_INTENT_KEY` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 92)
- `LEARNER_STATE_INPUTS_KEY` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 96)
- `INHERITED_LEARNER_INPUTS_KEY` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 100)
- `LEARNER_STATE_UNRECORDED` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 223)
- `LEARNER_STATE_PROTECTED` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 343)
- `LIVE_ADMINISTRATION_REASONS` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 412)
- `ITEM_PASSAGE_PROTECTED` ([src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py), line 487)

### Explicit exports

`__all__` declares:

- `ATTEMPT_HOST_REFS`
- `INHERITED_LEARNER_INPUTS_KEY`
- `ITEM_PASSAGE_PROTECTED`
- `LEARNER_STATE_INPUTS_KEY`
- `LEARNER_STATE_PROTECTED`
- `LEARNER_STATE_UNRECORDED`
- `LIVE_ADMINISTRATION_REASONS`
- `RICH_INTENT_KEY`
- `figure_homes`
- `figure_withheld`
- `inherited_learner_inputs`
- `intent_learner_state_withheld`
- `item_passages`
- `keys_withheld`
- `learner_state_withheld`
- `rich_base_item_protected`
- `rich_base_keys`
- `row_withheld`
- `show_me_row`
- `stored_learner_state_withheld`
- `stored_plan_open_items`
- `withheld_message`

## Internal implementation anchors

- `_figure_spans(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/protection.py), line 121) — Every span a figure was built from: the selection, the region's and the crop's block, and the complete manifest of what the author was sent (the paragraphs around it too: a figure may show a neighbour's quoted assumption; Codex review F1).
- `_rich_intent(row: Mapping[str, Any]) -> Any` ([source](../../../../../../src/learnloop/figures/protection.py), line 227)
- `_learner_inputs_unrecorded(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/protection.py), line 232) — Codex review F3: the row's author was sent a learner state (the prompt version's ``+learner-v1``) and neither its report nor its rich intent keeps what that state was read from.
- `_lineage(repository: Repository, row: Mapping[str, Any]) -> list[Mapping[str, Any]] | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 247) — The figure and every figure it was made from (``supersedes_id``, ``fuller_of_id``), read from the current rows; None without the tables.
- `_withheld(vault: Any, repository: Repository, base: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 328)
- `_carries_learner_state(payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/protection.py), line 347)
- `_inherits_learner_state(payload: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/protection.py), line 351)
- `_inherited_withheld(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 355) — Why a revision job's inherited learner states may not be built on now, or None (each against the protection as it is now; no record: fail closed).
- `_learner_state_withheld(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/figures/protection.py), line 393) — Why the saved learner state may not be sent now, or None (``learner_state.inputs_withheld``: its answers, items, questions and passages against the protection as it is now; no record: fail closed).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `row_withheld`; statically calls `row_withheld`
- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `INHERITED_LEARNER_INPUTS_KEY`, `LEARNER_STATE_INPUTS_KEY`, `RICH_INTENT_KEY`, `_learner_inputs_unrecorded`, `_withheld`, `inherited_learner_inputs`, `learner_state_withheld`; statically calls `_learner_inputs_unrecorded`, `_withheld`, `inherited_learner_inputs`, `learner_state_withheld`
- [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]] — imports `keys_withheld`; statically calls `keys_withheld`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `row_withheld`; statically calls `row_withheld`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `_withheld`, `figure_homes`, `item_passages`, `rich_base_keys`, `row_withheld`, `show_me_row`; statically calls `_withheld`, `figure_homes`, `item_passages`, `rich_base_keys`, `row_withheld`, `show_me_row`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `item_passages`, `keys_withheld`, `withheld_message`; statically calls `item_passages`, `keys_withheld`, `withheld_message`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `ATTEMPT_HOST_REFS`, `keys_withheld`, `row_withheld`, `withheld_message`; statically calls `keys_withheld`, `row_withheld`, `withheld_message`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `ATTEMPT_HOST_REFS`, `LEARNER_STATE_INPUTS_KEY`, `_carries_learner_state`, `_inherited_withheld`, `_inherits_learner_state`, `_learner_state_withheld`, `_withheld`, `rich_base_item_protected`, `stored_learner_state_withheld`; statically calls `_carries_learner_state`, `_inherited_withheld`, `_inherits_learner_state`, `_learner_state_withheld`, `_withheld`, `rich_base_item_protected`, `stored_learner_state_withheld`
- [[Reference/Modules/learnloop/figures/view|learnloop.figures.view]] — imports `RICH_INTENT_KEY`, `_withheld`, `learner_state_withheld`; statically calls `_withheld`, `learner_state_withheld`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `figure_withheld`; statically calls `figure_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `ATTEMPT_HOST_REFS`, `figure_withheld`; statically calls `figure_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `figure_withheld`; statically calls `figure_withheld`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `spans_withheld`; calls `spans_withheld`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `assemble`; calls `assemble`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `block_events_for`, `daily_plan_tables_present`, `plan_blocks`, `plans_for_date`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`, `has_tables`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `figure_home_keys`, `figures_enabled`; calls `figure_home_keys`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `inputs_withheld`; calls `inputs_withheld`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; calls `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `module`; calls `item_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/grounding|learnloop.figures.grounding]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_an_unreadable_stored_plan_fails_closed_everywhere`
  - `test_v1_only_todays_plan_holds_an_item`
  - `test_v1_the_open_items_are_the_plan_records_own`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_fresh_figure_for_a_marked_row_is_reused_under_another_setting`
  - `test_a_fuller_version_with_no_record_of_its_own_is_checked_by_its_jobs_payload`
  - `test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`
  - `test_a_marked_quick_figure_with_no_record_is_withheld`
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
  - `test_a_quick_figure_keeps_the_inputs_of_the_learner_state_it_was_written_from`
  - `test_a_quick_figure_whose_learner_inputs_became_protected_is_not_presented`
  - `test_a_quick_figure_with_no_learner_state_keeps_its_report_as_before`
  - `test_a_revision_inherits_its_bases_learner_state_protection`
  - `test_a_rich_revision_with_nothing_inherited_carries_no_record`
  - `test_an_unmarked_quick_figure_with_no_record_keeps_the_no_learner_state_reading`
- [tests/test_k1_source_sets_gate.py](../../../../../../tests/test_k1_source_sets_gate.py) — direct import
  - `test_the_tutor_figures_and_phone_withhold_when_source_sets_did_not_load`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_rich_figure_whose_learner_inputs_became_protected_is_not_delivered`
  - `test_a_rich_only_figure_whose_learner_inputs_became_protected_is_never_reused`
  - `test_a_stored_rich_figure_without_learner_state_is_checked_as_before`
- [tests/test_protection_surface_matrix.py](../../../../../../tests/test_protection_surface_matrix.py) — direct import
  - `test_figure_prebuilds_are_all_withheld_when_exam_reservations_cannot_be_read`
  - `test_releasing_an_exam_reservation_admits_its_items_passage_to_figure_prebuilds`

## Modification guidance

- Make changes here when the responsibility remains protection within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/protection.py](../../../../../../src/learnloop/figures/protection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
